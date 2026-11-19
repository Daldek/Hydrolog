"""Tests of the notice codes: the library warnings, the registry and the capture.

Every notice has a stable code of ``NOTICES`` (plan D16): a library warning
(``hydrolog._warnings``) gives the code, message and details of its class, an operation
builds its notices with ``notice``, and a warning of another library gets the code of
the category it was captured as, never its own class name.
"""

from __future__ import annotations

import copy
import math
import pickle
import string
import warnings

import numpy as np
import pytest

from hydrolog._formulas import checked_inputs, constraint_range, constraint_ranges
from hydrolog._warnings import (
    LIBRARY_WARNINGS,
    DistributionLeftOut,
    HydrologWarning,
    IncompleteYears,
    KsTestApproximate,
    NegativeQuantiles,
    OutsideSupport,
    OutsideTypicalRange,
    OutsideUnverifiedRange,
    PositionsIgnored,
    ShortRecord,
    SmallSample,
    UhModelMismatch,
    UhSubsteps,
    UnknownHietogramType,
    UnreferencedFormula,
    render,
    warn_outside_typical_range,
)
from hydrolog.catalog.envelope import NOTICE_LEVELS, Notice, capture_warnings
from hydrolog.catalog.notices import NOTICES, notice
from hydrolog.nogat_formulas import (
    Constraint,
    FormulaSpec,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    Tolerance,
    Variable,
)
from hydrolog.operations import route_lag, route_network
from hydrolog.routing import RUNOFF_MODELS
from hydrolog.routing.network import _observed

from ._network_documents import document, outlet
from ._routing_extensions import Share

SAMPLES = {
    OutsideTypicalRange: {
        "method": "kirpich",
        "parameter": "length_km",
        "field": "channel_length_km",
        "value": 120.0,
        "minimum": 0.001,
        "maximum": 80.0,
        "constraint": None,
        "condition": None,
        "source": None,
    },
    OutsideUnverifiedRange: {
        "method": "nash",
        "parameter": "n",
        "field": "nash_n",
        "value": 12.0,
        "minimum": 1.0,
        "maximum": 10.0,
        "constraint": None,
        "condition": None,
        "source": None,
    },
    SmallSample: {"years": 6, "minimum": 10},
    ShortRecord: {"years": 20, "minimum": 30},
    KsTestApproximate: {},
    DistributionLeftOut: {
        "distribution": "weibull",
        "fit_method": "moments",
        "reason": "out_of_range",
        "cause": "The method of moments cannot fit the Weibull distribution",
    },
    OutsideSupport: {
        "distribution": "pearson3",
        "fit_method": "l_moments",
        "values": [81.6, 87.2],
    },
    NegativeQuantiles: {"return_periods": [500.0, 1000.0], "zero_return_period": 312.5},
    IncompleteYears: {
        "skipped": 2,
        "total": 31,
        "years": [1991, 2021],
        "days_with_data": [304, 61],
        "days_in_year": [365, 365],
    },
    UnknownHietogramType: {
        "hietogram_type": "gamma",
        "allowed": ["beta", "block", "euler_ii", "triangular"],
    },
    UhModelMismatch: {"uh_model": "scs", "result_uh_model": "nash"},
    UhSubsteps: {
        "timestep_min": 1440.0,
        "maximum_min": 193.605,
        "substeps": 93,
        "substep_min": 15.4839,
    },
    PositionsIgnored: {"reason": "partial", "node_id": "R3"},
    UnreferencedFormula: {
        "formula": "rybczynski_zones",
        "title": "Rybczyński's zones",
        "formula_version": 1,
    },
}


def _fields(template: str) -> set[str]:
    """The names of the fields of a ``str.format`` template."""
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


class TestRender:
    def test_a_list_or_a_tuple_is_written_as_its_items(self):
        listed = render("Gauges: {stations}.", {"stations": ["A", "B"]})
        assert listed == "Gauges: A, B."
        assert render("Years {years}", {"years": (1991, 2021)}) == "Years 1991, 2021"

    def test_more_than_ten_items_are_cut_and_counted(self):
        ten = render("{x}", {"x": list(range(1, 11))})
        twelve = render("{x}", {"x": list(range(1, 13))})
        assert ten == "1, 2, 3, 4, 5, 6, 7, 8, 9, 10"
        assert twelve == "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, and 2 more"

    def test_format_specs_and_conversions_apply_to_the_values(self):
        details = {"tc_min": 90.0, "size": 123456, "cover": "forest"}
        assert render("{tc_min:g} min", details) == "90 min"
        assert render("{size:,} characters", details) == "123,456 characters"
        assert render("{cover!r}", details) == "'forest'"

    def test_a_field_without_a_value_is_an_error(self):
        with pytest.raises(KeyError):
            render("{missing} of {total}", {"missing": 1})


class TestLibraryWarnings:
    def test_the_codes_of_the_classes(self):
        assert [kind.code() for kind in LIBRARY_WARNINGS] == [
            "outside_typical_range",
            "outside_unverified_range",
            "small_sample",
            "short_record",
            "ks_test_approximate",
            "distribution_left_out",
            "outside_support",
            "negative_quantiles",
            "incomplete_years",
            "unknown_hietogram_type",
            "uh_model_mismatch",
            "uh_substeps",
            "positions_ignored",
            "unreferenced_formula",
        ]

    def test_every_subclass_is_listed(self):
        found: set[type[HydrologWarning]] = set()
        pending = [HydrologWarning]
        while pending:
            for kind in pending.pop().__subclasses__():
                found.add(kind)
                pending.append(kind)
        assert found == set(LIBRARY_WARNINGS)

    def test_an_unverified_range_is_caught_as_a_typical_range(self):
        warning = OutsideUnverifiedRange(**SAMPLES[OutsideUnverifiedRange])
        with pytest.warns(OutsideTypicalRange) as caught:
            warnings.warn(warning, stacklevel=2)
        assert caught[0].message is warning
        assert OutsideUnverifiedRange.keys == OutsideTypicalRange.keys

    @pytest.mark.parametrize("kind", LIBRARY_WARNINGS, ids=lambda k: k.__name__)
    def test_the_registry_has_the_level_template_and_keys_of_the_class(self, kind):
        spec = NOTICES[kind.code()]
        assert (spec.level, spec.template, spec.details) == (
            kind.level,
            kind.template,
            kind.keys,
        )
        assert not spec.own_text

    @pytest.mark.parametrize("kind", LIBRARY_WARNINGS, ids=lambda k: k.__name__)
    def test_a_warning_is_a_user_warning_with_its_details_and_message(self, kind):
        warning = kind(**SAMPLES[kind])
        assert isinstance(warning, UserWarning)
        assert warning.details == SAMPLES[kind]
        assert str(warning) == render(kind.template, SAMPLES[kind])

    @pytest.mark.parametrize("kind", LIBRARY_WARNINGS, ids=lambda k: k.__name__)
    @pytest.mark.parametrize(
        "clone", [copy.copy, copy.deepcopy, lambda w: pickle.loads(pickle.dumps(w))]
    )
    def test_a_warning_pickles_and_copies(self, kind, clone):
        warning = kind(**SAMPLES[kind])
        again = clone(warning)
        assert type(again) is kind
        assert again.details == warning.details
        assert str(again) == str(warning)

    def test_the_details_must_be_exactly_the_keys(self):
        with pytest.raises(TypeError, match="years, minimum"):
            SmallSample(years=6)
        with pytest.raises(TypeError, match="years, minimum"):
            SmallSample(years=6, minimum=10, extra=1)
        with pytest.raises(TypeError, match="message alone"):
            SmallSample("only 6 years", years=6, minimum=10)
        with pytest.raises(TypeError, match="message alone"):
            SmallSample("only 6 years", "and more")

    @pytest.mark.parametrize("kind", LIBRARY_WARNINGS, ids=lambda k: k.__name__)
    def test_a_warning_issued_again_by_its_text_and_class_is_made_again(self, kind):
        """Code that records warnings and issues them again by their text and class
        (numba's WarningsFixer: warn_explicit(str(message), category, ...)) made
        warn_explicit raise TypeError: __init__ took the details only (E5b-08)."""
        first = kind(**SAMPLES[kind])
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            warnings.warn(first, stacklevel=1)
        with capture_warnings() as notices:
            for item in recorded:
                warnings.warn_explicit(
                    str(item.message), item.category, item.filename, item.lineno
                )
        assert [(n.code, n.message, n.details) for n in notices] == [
            (kind.code(), str(first), None)
        ]

    @pytest.mark.parametrize(
        "clone", [copy.copy, copy.deepcopy, lambda w: pickle.loads(pickle.dumps(w))]
    )
    def test_a_warning_made_from_its_message_pickles_copies_and_raises(self, clone):
        text = str(SmallSample(**SAMPLES[SmallSample]))
        again = clone(SmallSample(text))
        assert (type(again), str(again), again.details) == (SmallSample, text, {})
        with warnings.catch_warnings():
            warnings.simplefilter("error", SmallSample)
            with pytest.raises(SmallSample, match="Only 6 year"):
                warnings.warn(text, SmallSample, stacklevel=1)

    def test_the_base_class_has_no_code_to_warn_with(self):
        with pytest.raises(TypeError, match="subclasses"):
            HydrologWarning()

    def test_inside_a_routing_network_each_class_keeps_its_code_and_level(self):
        """The network names a caught warning after its class (routing/network.py),
        at the level of its class: uh_substeps is info, as in an operation."""
        with _observed() as caught:
            for kind in LIBRARY_WARNINGS:
                warnings.warn(kind(**SAMPLES[kind]), stacklevel=2)
        assert [item.code for item in caught] == [k.code() for k in LIBRARY_WARNINGS]
        assert [item.level for item in caught] == [k.level for k in LIBRARY_WARNINGS]
        assert all(item.code in NOTICES for item in caught)


class TestRegistry:
    def test_it_is_read_only(self):
        with pytest.raises(TypeError):
            NOTICES["new_code"] = NOTICES["empty_area"]  # type: ignore[index]

    @pytest.mark.parametrize("code", list(NOTICES))
    def test_a_spec_is_a_valid_notice_and_names_only_its_details(self, code):
        spec = NOTICES[code]
        assert spec.code == code
        assert spec.level in NOTICE_LEVELS
        Notice(spec.level, spec.code, spec.template)  # snake_case, a message
        assert _fields(spec.template) <= set(spec.details)
        assert len(set(spec.details)) == len(spec.details)
        if spec.own_text:
            assert spec.details == () and _fields(spec.template) == set()

    def test_the_captured_and_routing_codes_carry_their_own_text(self):
        own = {code for code, spec in NOTICES.items() if spec.own_text}
        assert own == {
            "user_warning",
            "runtime_warning",
            "tail_extended",
            "lag_interpolated",
            "timestep_refined",
            "substeps_added",
            "subreaches_adjusted",
            "accuracy_limit",
            "diffusion_dominated",
            "tail_truncated",
        }


class TestNotice:
    def test_the_message_is_the_template_and_the_details_follow_the_registry(self):
        made = notice("condition_ignored", condition="good", land_cover="water")
        assert (made.level, made.code) == ("info", "condition_ignored")
        assert made.message == "'water' has a single CN: condition 'good' was ignored."
        assert list(made.details) == ["land_cover", "condition"]

    def test_a_code_without_details_has_none(self):
        assert notice("empty_area").details is None
        assert "details" not in notice("empty_area").to_dict()

    def test_an_unknown_code_is_refused(self):
        with pytest.raises(ValueError, match="Unknown notice code"):
            notice("short_series")

    @pytest.mark.parametrize("code", ["user_warning", "tail_extended"])
    def test_a_code_with_the_text_of_its_emitter_is_refused(self, code):
        with pytest.raises(ValueError, match="text of its emitter"):
            notice(code)

    @pytest.mark.parametrize(
        "details",
        [{"missing": 2}, {"missing": 2, "total": 14, "first_date": None, "n": 1}],
    )
    def test_the_details_must_be_exactly_the_keys_of_the_code(self, details):
        with pytest.raises(ValueError, match="missing, total, first_date"):
            notice("missing_values_removed", **details)


class TestNoticeObject:
    def test_to_dict_adds_details_only_when_there_are_some(self):
        plain = Notice("info", "superseded", "replaced")
        assert plain.to_dict() == {
            "level": "info",
            "code": "superseded",
            "message": "replaced",
        }
        assert "details" not in Notice("info", "superseded", "replaced", {}).to_dict()

    def test_details_are_json_native(self):
        made = Notice(
            "warning",
            "small_sample",
            "Only 6 year(s)",
            {"years": np.int64(6), "values": (np.float64(1.5), np.nan)},
        )
        assert made.to_dict()["details"] == {"years": 6, "values": [1.5, None]}

    def test_details_take_no_part_in_equality(self):
        first = Notice("info", "superseded", "replaced", {"run": 1})
        second = Notice("info", "superseded", "replaced", {"run": 2})
        assert first == second
        assert len({first, second}) == 1


class TestCaptureWarnings:
    def test_a_library_warning_gives_its_code_level_message_and_details(self):
        with capture_warnings() as notices:
            warnings.warn(SmallSample(years=6, minimum=10), stacklevel=2)
            warnings.warn(SmallSample(years=6, minimum=10), stacklevel=2)
            warnings.warn(KsTestApproximate(), stacklevel=2)
        assert [(n.level, n.code, n.details) for n in notices] == [
            ("warning", "small_sample", {"years": 6, "minimum": 10}),
            ("warning", "ks_test_approximate", None),
        ]
        assert notices[0].message == str(SmallSample(years=6, minimum=10))

    def test_a_warning_of_another_library_gets_the_code_of_its_category(self):
        class OptimizeWarning(UserWarning):
            """Like the warning of SciPy's curve fitting."""

        class ComplexWarning(RuntimeWarning):
            """Like NumPy's warning about a discarded imaginary part."""

        with capture_warnings((UserWarning, RuntimeWarning)) as notices:
            warnings.warn("covariance not estimated", OptimizeWarning, stacklevel=2)
            warnings.warn("imaginary part discarded", ComplexWarning, stacklevel=2)
        assert [(n.code, n.message, n.details) for n in notices] == [
            ("user_warning", "covariance not estimated", None),
            ("runtime_warning", "imaginary part discarded", None),
        ]

    def test_a_library_warning_outside_the_categories_is_issued_again(self):
        with (
            pytest.warns(SmallSample) as outer,
            capture_warnings((RuntimeWarning,)) as notices,
        ):
            warnings.warn(SmallSample(years=6, minimum=10), stacklevel=2)
        assert notices == []
        assert [w.message.details for w in outer] == [{"years": 6, "minimum": 10}]


class LooseParameters(UserWarning):
    """A warning of another library, a class that the registry does not know."""


class _Noisy(Share):
    """A runoff model that warns the way another library does, and the library."""

    model = "noisy-share"

    def hydrograph(self, rainfall, watershed, timestep_min):
        warnings.warn("loose parameters", LooseParameters, stacklevel=2)
        warnings.warn(SmallSample(years=3, minimum=10), stacklevel=2)
        return super().hydrograph(rainfall, watershed, timestep_min)


class TestRouting:
    def test_the_notices_of_a_routing_model_keep_its_text_without_details(self):
        output = route_lag(
            lag_min=12.0, times_min=[0, 10, 20, 30], discharge_m3s=[0, 5, 2, 0]
        )
        assert [n.code for n in output.notices] == ["lag_interpolated", "tail_extended"]
        assert all(n.details is None for n in output.notices)

    def test_a_code_outside_the_registry_becomes_user_warning_of_its_node(
        self, monkeypatch
    ):
        monkeypatch.setitem(RUNOFF_MODELS._classes, _Noisy.model, _Noisy)
        made = {
            "id": "A",
            "type": "subcatchment",
            "watershed": {
                "area_km2": 12.0,
                "perimeter_km": 18.0,
                "length_km": 6.0,
                "elevation_min_m": 210.0,
                "elevation_max_m": 330.0,
            },
            "runoff": {"model": _Noisy.model, "share": 0.5},
            "rainfall": {
                "kind": "design",
                "hietogram_type": "block",
                "total_mm": 45,
                "duration_min": 60,
            },
        }

        notices = route_network(network=document(made, outlet("A"))).notices

        assert [(n.code, n.message, n.details) for n in notices] == [
            ("user_warning", "A: loose parameters", {"node_id": "A"}),
            (
                "small_sample",
                f"A: {SmallSample(years=3, minimum=10)}",
                {"node_id": "A"},
            ),
        ]


_TOY_SOURCE = Source(citation="A source of the tests", locator="p. 1")


def _toy(
    name: str,
    applicability: Range | str = "unstated",
    constraints: tuple[Constraint, ...] = (),
    status: str = "oracle only",
) -> FormulaSpec:
    """A spec of y = x with the applicability and constraints of a test."""
    return FormulaSpec(
        name=name,
        title="A formula of the tests",
        function="tests.toy.formula",
        family="index",
        equation="y = x",
        latex="y = x",
        variables=(
            Variable(
                name="x",
                symbol="x",
                unit="-",
                physical=Range(test_low=-100.0, test_high=100.0, test_reason="a test"),
                applicability=applicability,  # type: ignore[arg-type]
                typical=Range(low=0.0, high=10.0, source=_TOY_SOURCE),
            ),
        ),
        outputs=(Output(name="y", unit="-", physical=Range()),),
        sources=(_TOY_SOURCE,),
        properties=Properties(
            units="homogeneous",
            scalings=(
                Scaling(
                    name="x",
                    inputs={"x": 1},
                    outputs={"y": 1},
                    tolerance=Tolerance(abs=0.0, reason="a test"),
                ),
            ),
        ),
        validation="none",
        formula_version=3,
        status=status,  # type: ignore[arg-type]
        constraints=constraints,
        no_traps_reason="a test",
    )


_AT_LEAST_TWO = Constraint(
    name="x_at_least_two",
    cls="applicability",
    check=lambda values: values.real("x") >= 2.0,
    text="x >= 2",
    source=_TOY_SOURCE,
    satisfied={"x": 5.0},
    violated={"x": 1.0},
)


class TestFormulaNotices:
    """``hydrolog._formulas`` issues the standard's notices as library warnings."""

    def test_a_range_with_one_end_words_that_end(self):
        with pytest.warns(OutsideTypicalRange) as caught:
            warn_outside_typical_range("m", "n", 6, 12, None, stacklevel=1)
            warn_outside_typical_range("m", "n", 9.5, None, 8.0, stacklevel=1)
        assert [str(w.message) for w in caught] == [
            "m: n=6 is below its typical minimum 12. Results may be unreliable.",
            "m: n=9.5 is above its typical maximum 8.0. Results may be unreliable.",
        ]
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            warn_outside_typical_range("m", "n", 12, 12, None, stacklevel=1)

    def test_an_input_outside_a_half_open_range_has_a_null_end(self):
        spec = _toy(
            "toy_half_open",
            Range(low=2.0, high=math.inf, source=_TOY_SOURCE),
        )
        with pytest.warns(OutsideTypicalRange) as caught:
            checked_inputs(spec, x=1.0)
        assert caught[0].message.details == {
            "method": "toy_half_open",
            "parameter": "x",
            "field": "x",
            "value": 1.0,
            "minimum": 2.0,
            "maximum": None,
            "constraint": None,
            "condition": None,
            "source": None,
        }

    def test_an_open_end_has_no_warning(self):
        spec = _toy(
            "toy_open_end",
            Range(low=2.0, high=8.0, low_inclusive=False, source=_TOY_SOURCE),
        )
        with pytest.raises(TypeError, match="open"):
            checked_inputs(spec, x=1.0)

    def test_a_violated_constraint_warns_with_its_quantity(self):
        spec = _toy("toy_constraint", constraints=(_AT_LEAST_TWO,))
        declared = constraint_range(
            spec,
            "x_at_least_two",
            parameter="twice_x",
            value=lambda values: 2.0 * values.real("x"),
            minimum=4.0,
        )
        with pytest.warns(OutsideTypicalRange) as caught:
            checked_inputs(spec, x=1.5)
        assert constraint_ranges()[("toy_constraint", "x_at_least_two")] is declared
        assert caught[0].message.details == {
            "method": "toy_constraint",
            "parameter": "twice_x",
            "field": "twice_x",
            "value": 3.0,
            "minimum": 4.0,
            "maximum": None,
            "constraint": "x_at_least_two",
            "condition": "x >= 2",
            "source": "A source of the tests, p. 1",
        }
        assert str(caught[0].message) == (
            "toy_constraint: twice_x=3.0 is below its typical minimum 4.0: x >= 2 (A "
            "source of the tests, p. 1). Results may be unreliable."
        )

    def test_an_undeclared_constraint_has_no_warning(self):
        spec = _toy("toy_undeclared", constraints=(_AT_LEAST_TWO,))
        with pytest.raises(TypeError, match="no warning of the library"):
            checked_inputs(spec, x=1.0)

    def test_a_constraint_range_is_declared_once_for_an_applicability_constraint(self):
        spec = _toy("toy_declared", constraints=(_AT_LEAST_TWO,))
        with pytest.raises(ValueError, match="no applicability constraint"):
            constraint_range(spec, "x", parameter="x", value=float, minimum=2.0)
        with pytest.raises(ValueError, match="minimum, maximum or both"):
            constraint_range(spec, "x_at_least_two", parameter="x", value=float)
        constraint_range(spec, "x_at_least_two", parameter="x", value=float, minimum=2)
        with pytest.raises(ValueError, match="declared already"):
            constraint_range(
                spec, "x_at_least_two", parameter="x", value=float, maximum=9
            )

    def test_an_unreferenced_formula_warns_on_every_result(self):
        spec = _toy("toy_unreferenced", status="unreferenced")
        with capture_warnings() as notices:
            checked_inputs(spec, x=5.0)
            checked_inputs(spec, x=6.0)
        assert [(n.level, n.code, n.details) for n in notices] == [
            (
                "info",
                "unreferenced_formula",
                {
                    "formula": "toy_unreferenced",
                    "title": "A formula of the tests",
                    "formula_version": 3,
                },
            )
        ]
