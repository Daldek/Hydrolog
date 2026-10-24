"""Tests for the operations of the groups tc, cn, scs, precip, uh and hydrograph.

Every operation is compared with the library class it wraps (same inputs, same
numbers); the error cases check the machine-readable ``details`` of the
``InvalidParameterError`` / ``InputDataError`` they raise; a few commands run end to
end through :func:`hydrolog.catalog.run_command`.
"""

import inspect
import json
import warnings

import numpy as np
import pytest

from hydrolog import operations as ops
from hydrolog.catalog import OperationOutput, data_commands, get_command, run_command
from hydrolog.catalog.groups.hydrograph import GENERATE_ONE_OF, GENERATE_OPTIONS
from hydrolog.exceptions import InputDataError, InvalidParameterError, NotFoundError
from hydrolog.morphometry import WatershedParameters
from hydrolog.operations._common import check_choice, select_group
from hydrolog.operations.cn import (
    CONDITIONS,
    HSG_GROUPS,
    LAND_COVERS,
)
from hydrolog.operations.hydrograph import UH_MODELS, compute_hydrograph
from hydrolog.operations.precip import AREAL_METHODS, HIETOGRAM_TYPES
from hydrolog.operations.scs import AMC_CLASSES
from hydrolog.operations.tc import TC_METHODS, watershed_concentration_time
from hydrolog.precipitation import (
    BetaHietogram,
    BlockHietogram,
    EulerIIHietogram,
    HietogramResult,
    Station,
    TriangularHietogram,
    areal_precipitation_idw,
    arithmetic_mean,
    inverse_distance_weighting,
    isohyet_method,
    thiessen_polygons,
)
from hydrolog.runoff import (
    AMC,
    SCSCN,
    ClarkIUH,
    HydrographGenerator,
    HydrologicCondition,
    LandCover,
    NashIUH,
    SCSUnitHydrograph,
    SnyderUH,
    calculate_weighted_cn,
    get_cn,
    get_cn_range,
    lookup_cn,
)
from hydrolog.runoff import cn_lookup as cn_tables
from hydrolog.time import ConcentrationTime

RUNOFF_GROUPS = ("tc", "cn", "scs", "precip", "uh", "hydrograph")

FULL_WATERSHED = {
    "name": "Potok Młynówka",
    "area_km2": 45.3,
    "perimeter_km": 32.1,
    "length_km": 12.5,
    "elevation_min_m": 150.0,
    "elevation_max_m": 520.0,
    "elevation_mean_m": 330.0,
    "mean_slope_m_per_m": 0.025,
    "channel_length_km": 10.8,
    "channel_slope_m_per_m": 0.018,
    "cn": 72,
    "runoff_coeff": 0.45,
    "retardance": 0.4,
    "overland_length_km": 0.25,
    "overland_slope_m_per_m": 0.008,
}

# What each method of ``WatershedParameters.calculate_tc`` cannot do without, in the
# order the library reports it (besides the always present watershed fields). FAA and
# Kerby time the overland flow, so they need the overland flow length and slope.
REQUIRED_FIELDS = {
    "nrcs": ("cn",),
    "faa": ("runoff_coeff", "overland_length_km", "overland_slope_m_per_m"),
    "kerby": ("retardance", "overland_length_km", "overland_slope_m_per_m"),
    "kerby_kirpich": (
        "retardance",
        "overland_length_km",
        "overland_slope_m_per_m",
        "channel_length_km",
        "channel_slope_m_per_m",
    ),
}

STATIONS = [
    {"name": "Balice", "x": 555500.0, "y": 244300.0, "precipitation_mm": 31.2},
    {"name": "Krzeszowice", "x": 545900.0, "y": 249700.0, "precipitation_mm": 36.8},
    {"name": "Skawina", "x": 562900.0, "y": 229400.0, "precipitation_mm": 28.4},
]
GAUGES = [Station(s["name"], s["x"], s["y"], s["precipitation_mm"]) for s in STATIONS]


def unwrap(output):
    """Split what an operation returns into ``(result, notices)``."""
    if isinstance(output, OperationOutput):
        return output.result, list(output.notices)
    return output, []


def quietly(function, *args, **kwargs):
    """Call library code whose range warnings are not under test."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return function(*args, **kwargs)


def without(data, *keys):
    return {key: value for key, value in data.items() if key not in keys}


def assert_arrays(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=0)


# --- tc -------------------------------------------------------------------------------

TC_CASES = [
    ("tc_kirpich", "kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023}),
    ("tc_nrcs", "nrcs", {"length_km": 8.2, "slope_m_per_m": 0.023, "cn": 72}),
    (
        "tc_giandotti",
        "giandotti",
        {"area_km2": 145.0, "length_km": 21.5, "elevation_diff_m": 320.0},
    ),
    (
        "tc_faa",
        "faa",
        {"length_km": 0.15, "slope_m_per_m": 0.02, "runoff_coeff": 0.6},
    ),
    (
        "tc_kerby",
        "kerby",
        {"length_km": 0.10, "slope_m_per_m": 0.008, "retardance": 0.4},
    ),
    (
        "tc_kerby_kirpich",
        "kerby_kirpich",
        {
            "overland_length_km": 0.25,
            "overland_slope_m_per_m": 0.008,
            "retardance": 0.4,
            "channel_length_km": 5.0,
            "channel_slope_m_per_m": 0.005,
        },
    ),
]


class TestTimeOfConcentration:
    """``tc <method>`` and ``tc watershed``."""

    @pytest.mark.parametrize("function, method, arguments", TC_CASES)
    def test_method_matches_concentration_time(self, function, method, arguments):
        """The result is the library value, in minutes and hours."""
        result, notices = unwrap(getattr(ops, function)(**arguments))
        expected = getattr(ConcentrationTime, method)(**arguments)
        assert result.method == method
        assert result.tc_min == pytest.approx(expected, rel=1e-12)
        assert result.tc_h == pytest.approx(expected / 60.0, rel=1e-12)
        assert result.parameters == {k: float(v) for k, v in arguments.items()}
        assert notices == []

    def test_kirpich_documented_value(self):
        """Kirpich, L = 8.2 km, S = 0.023: 85.97 min (library docstring)."""
        result, _ = unwrap(ops.tc_kirpich(length_km=8.2, slope_m_per_m=0.023))
        assert result.tc_min == pytest.approx(85.9733, abs=1e-4)

    def test_nrcs_accepts_fractional_cn(self):
        """A weighted (fractional) CN is used as it is, not rounded."""
        low, _ = unwrap(ops.tc_nrcs(length_km=8.2, slope_m_per_m=0.023, cn=72.0))
        mid, _ = unwrap(ops.tc_nrcs(length_km=8.2, slope_m_per_m=0.023, cn=72.5))
        high, _ = unwrap(ops.tc_nrcs(length_km=8.2, slope_m_per_m=0.023, cn=73.0))
        assert high.tc_min < mid.tc_min < low.tc_min
        assert mid.parameters["cn"] == 72.5

    def test_out_of_range_parameters_become_notices(self):
        """Library range warnings are reported as notices, not printed."""
        with warnings.catch_warnings(record=True) as leaked:
            warnings.simplefilter("always")
            _, notices = unwrap(ops.tc_kirpich(length_km=120.0, slope_m_per_m=0.0001))
        assert leaked == []
        assert [n.level for n in notices] == ["warning", "warning"]
        assert "length_km=120.0" in notices[0].text
        assert "slope_m_per_m=0.0001" in notices[1].text

    @pytest.mark.parametrize("method", TC_METHODS)
    def test_watershed_matches_calculate_tc(self, method):
        """``tc watershed`` equals ``WatershedParameters.calculate_tc``."""
        watershed = WatershedParameters.from_dict(FULL_WATERSHED)
        expected = quietly(watershed.calculate_tc, method=method)
        result, _ = unwrap(ops.tc_watershed(watershed=FULL_WATERSHED, method=method))
        assert result.method == method
        assert result.tc_min == pytest.approx(expected, rel=1e-12)
        assert result.watershed_name == "Potok Młynówka"

    @pytest.mark.parametrize(
        "dropped",
        [
            (),
            ("channel_length_km", "channel_slope_m_per_m"),
            ("channel_length_km", "channel_slope_m_per_m", "mean_slope_m_per_m"),
            ("elevation_mean_m",),
        ],
        ids=["full", "no-channel", "relief-slope", "no-mean-elevation"],
    )
    @pytest.mark.parametrize("method", ["kirpich", "nrcs", "giandotti", "faa", "kerby"])
    def test_reported_parameters_reproduce_the_result(self, method, dropped):
        """The parameters shown are the ones the library derived from the watershed."""
        data = without(FULL_WATERSHED, *dropped)
        expected = quietly(WatershedParameters.from_dict(data).calculate_tc, method)
        result, _ = unwrap(ops.tc_watershed(watershed=data, method=method))
        assert result.tc_min == pytest.approx(expected, rel=1e-12)
        again = quietly(getattr(ConcentrationTime, method), **result.parameters)
        assert again == pytest.approx(expected, rel=1e-12)

    def test_kerby_kirpich_parameters_reproduce_the_result(self):
        """Composite method: the five derived arguments give the same tc."""
        result, _ = unwrap(
            ops.tc_watershed(watershed=FULL_WATERSHED, method="kerby_kirpich")
        )
        again = quietly(ConcentrationTime.kerby_kirpich, **result.parameters)
        assert again == pytest.approx(result.tc_min, rel=1e-12)

    @pytest.mark.parametrize(
        "method, extra",
        [("faa", {"runoff_coeff": 0.45}), ("kerby", {"retardance": 0.4})],
    )
    def test_overland_flow_methods_report_the_overland_path_not_the_channel(
        self, method, extra
    ):
        """FAA and Kerby time the overland flow (0.25 km at 0.008), not the 10.8 km
        channel: the result is inside the range of the formulas, so no notices."""
        result, notices = unwrap(
            ops.tc_watershed(watershed=FULL_WATERSHED, method=method)
        )
        assert result.parameters == {
            "length_km": 0.25,
            "slope_m_per_m": 0.008,
            **extra,
        }
        assert notices == []

    def test_nrcs_reports_the_land_slope_of_the_watershed(self):
        """TR-55: Y is the average land slope (0.025), not the channel slope (0.018)."""
        result, _ = unwrap(ops.tc_watershed(watershed=FULL_WATERSHED, method="nrcs"))
        assert result.parameters == {
            "length_km": 10.8,
            "slope_m_per_m": 0.025,
            "cn": 72.0,
        }

    def test_a_watershed_with_a_channel_only_has_no_faa_or_kerby(self):
        """No silent substitution of the channel: the error names the fields and the
        alternative."""
        data = without(FULL_WATERSHED, "overland_length_km", "overland_slope_m_per_m")
        with pytest.raises(InvalidParameterError) as caught:
            ops.tc_watershed(watershed=data, method="kerby")
        assert caught.value.code == "validation_error"
        assert caught.value.details == {
            "option": "watershed",
            "reason": "missing_field",
            "method": "kerby",
            "missing": ["overland_length_km", "overland_slope_m_per_m"],
        }
        assert "kerby_kirpich" in caught.value.hint

    def test_a_mean_elevation_of_zero_is_a_value_not_a_missing_one(self):
        """Giandotti: H = 0 - (-30) = 30 m; the middle of the range would give 65 m."""
        data = {
            **FULL_WATERSHED,
            "elevation_min_m": -30.0,
            "elevation_max_m": 100.0,
            "elevation_mean_m": 0.0,
        }
        expected = quietly(
            WatershedParameters.from_dict(data).calculate_tc, "giandotti"
        )
        result, _ = unwrap(ops.tc_watershed(watershed=data, method="giandotti"))
        assert result.parameters["elevation_diff_m"] == pytest.approx(30.0)
        assert result.tc_min == pytest.approx(expected, rel=1e-12)
        again = quietly(ConcentrationTime.giandotti, **result.parameters)
        assert again == pytest.approx(result.tc_min, rel=1e-12)

    @pytest.mark.parametrize(
        "method, field",
        [(m, f) for m, fields in REQUIRED_FIELDS.items() for f in fields],
    )
    def test_missing_field_is_named_and_the_library_agrees(self, method, field):
        """Each field of the table is really needed: the library names it."""
        data = without(FULL_WATERSHED, field)
        with pytest.raises(InvalidParameterError) as library:
            WatershedParameters.from_dict(data).calculate_tc(method=method)
        assert library.value.details["missing"] == [field]
        with pytest.raises(InvalidParameterError) as caught:
            ops.tc_watershed(watershed=data, method=method)
        assert caught.value.code == "validation_error"
        assert caught.value.details == {
            "option": "watershed",
            "reason": "missing_field",
            "method": method,
            "missing": [field],
        }

    def test_all_missing_fields_are_listed_in_order(self):
        """A bare watershed lacks everything the composite method needs."""
        bare = without(
            FULL_WATERSHED,
            *REQUIRED_FIELDS["kerby_kirpich"],
        )
        with pytest.raises(InvalidParameterError) as caught:
            ops.tc_watershed(watershed=bare, method="kerby_kirpich")
        assert caught.value.details["missing"] == list(REQUIRED_FIELDS["kerby_kirpich"])
        assert "retardance" in str(caught.value)

    def test_watershed_file_error_names_the_file_option(self, tmp_path):
        """The option reported is the one the watershed came from."""
        path = tmp_path / "zlewnia.json"
        path.write_text(json.dumps(without(FULL_WATERSHED, "cn")), encoding="utf-8")
        with pytest.raises(InvalidParameterError) as caught:
            ops.tc_watershed(watershed_file=str(path), method="nrcs")
        assert caught.value.details["option"] == "watershed_file"

    def test_watershed_file_gives_the_same_result(self, tmp_path):
        """A ``WatershedParameters.to_json()`` file works like the inline object."""
        path = tmp_path / "zlewnia.json"
        path.write_text(
            WatershedParameters.from_dict(FULL_WATERSHED).to_json(), encoding="utf-8"
        )
        from_file, _ = unwrap(ops.tc_watershed(watershed_file=str(path)))
        inline, _ = unwrap(ops.tc_watershed(watershed=FULL_WATERSHED))
        assert from_file.tc_min == inline.tc_min

    def test_watershed_source_errors(self, tmp_path):
        """Both, neither and a missing file are reported by the input loader."""
        with pytest.raises(InvalidParameterError) as neither:
            ops.tc_watershed()
        assert neither.value.details["reason"] == "one_of"
        with pytest.raises(NotFoundError):
            ops.tc_watershed(watershed_file=str(tmp_path / "brak.json"))

    def test_unknown_method_is_a_choice_error(self):
        """A method outside the six is a validation error with the allowed list."""
        watershed = WatershedParameters.from_dict(FULL_WATERSHED)
        with pytest.raises(InvalidParameterError) as caught:
            watershed_concentration_time(watershed, "bogus")
        assert caught.value.details["reason"] == "choice"
        assert caught.value.details["allowed"] == list(TC_METHODS)

    def test_formula_rejection_is_a_validation_error(self):
        """A zero channel slope passes the watershed checks but not Kirpich."""
        data = {**FULL_WATERSHED, "channel_slope_m_per_m": 0.0}
        with pytest.raises(InvalidParameterError) as caught:
            ops.tc_watershed(watershed=data, method="kirpich")
        assert caught.value.details["reason"] == "invalid_value"
        assert "slope_m_per_m must be positive" in str(caught.value)

    def test_catalog_validates_before_the_formula(self):
        """A non-positive length never reaches the library."""
        with pytest.raises(InvalidParameterError) as caught:
            run_command("tc kirpich", {"length_km": -1, "slope_m_per_m": 0.01})
        assert caught.value.details["reason"] == "exclusive_minimum"

    def test_run_command_envelope(self):
        """End to end: inputs, result, notices and strict JSON."""
        envelope = run_command("tc kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023})
        document = json.loads(envelope.to_json())
        assert document["command"] == "tc kirpich"
        assert document["inputs"] == {"length_km": 8.2, "slope_m_per_m": 0.023}
        assert document["result"]["tc_min"] == pytest.approx(85.9733, abs=1e-4)
        assert document["notices"] == []

    def test_run_command_notice(self):
        """Range warnings reach the envelope as notices with a stable code."""
        envelope = run_command("tc kirpich", {"length_km": 120, "slope_m_per_m": 0.023})
        assert [(n.level, n.code) for n in envelope.notices] == [
            ("warning", "user_warning")
        ]


# --- cn -------------------------------------------------------------------------------


class TestCurveNumberTables:
    """``cn lookup``, ``cn list``, ``cn range``."""

    def test_lookup_matches_the_table_for_every_row(self):
        """Every (cover, condition, group) of TR-55 gives the library CN."""
        checked = 0
        for (cover, condition), row in cn_tables._CN_TABLE.items():
            for hsg, expected in row.items():
                result, _ = unwrap(
                    ops.cn_lookup(
                        hsg=hsg,
                        land_cover=cover.value,
                        condition=condition.value if condition else None,
                    )
                )
                assert result.cn == expected == get_cn(hsg, cover, condition)
                checked += 1
        assert checked == 33 * 4

    def test_lookup_equals_lookup_cn(self):
        """The operation and ``lookup_cn`` agree on the documented example."""
        result, notices = unwrap(
            ops.cn_lookup(hsg="B", land_cover="forest", condition="good")
        )
        library = lookup_cn("B", "forest", "good")
        assert (result.cn, result.hsg) == (library.cn, library.hsg) == (55, "B")
        assert result.land_cover == "forest"
        assert result.condition == result.condition_applied == "good"
        assert notices == []

    def test_missing_condition_defaults_to_fair_and_says_so(self):
        """Without a condition the library uses ``fair``; the result states it."""
        result, notices = unwrap(ops.cn_lookup(hsg="C", land_cover="pasture"))
        assert result.cn == get_cn("C", "pasture", HydrologicCondition.FAIR) == 79
        assert result.condition is None
        assert result.condition_applied == "fair"
        assert [n.code for n in notices] == ["condition_defaulted"]

    def test_condition_is_ignored_for_single_value_covers(self):
        """A single-row cover ignores a given condition, and says so."""
        result, notices = unwrap(
            ops.cn_lookup(hsg="A", land_cover="paved", condition="good")
        )
        assert result.cn == 98
        assert result.condition == "good"
        assert result.condition_applied is None
        assert [n.code for n in notices] == ["condition_ignored"]

    @pytest.mark.parametrize(
        "arguments, option",
        [
            ({"hsg": "E", "land_cover": "forest"}, "hsg"),
            ({"hsg": "A", "land_cover": "tundra"}, "land_cover"),
            ({"hsg": "A", "land_cover": "forest", "condition": "bad"}, "condition"),
        ],
    )
    def test_unknown_choice_is_a_choice_error(self, arguments, option):
        """Values outside the tables never reach the library's KeyError paths."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.cn_lookup(**arguments)
        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == "choice"

    def test_list_is_the_whole_table(self):
        """``cn list`` has one entry per table row with all four groups."""
        listing = ops.cn_list()
        expected = {
            (cover.value, condition.value if condition else None): row
            for (cover, condition), row in cn_tables._CN_TABLE.items()
        }
        assert {(e.land_cover, e.condition): e.cn for e in listing.entries} == expected
        assert listing.hsg == ["A", "B", "C", "D"]
        assert len(listing.entries) == len(cn_tables._CN_TABLE)

    @pytest.mark.parametrize("cover", LAND_COVERS)
    def test_range_matches_get_cn_range(self, cover):
        """Bounds per group are the library's; conditions say what they span."""
        result = ops.cn_range(land_cover=cover)
        expected = get_cn_range(cover)
        assert {h: (b.minimum, b.maximum) for h, b in result.by_hsg.items()} == expected
        rows = [c for (lc, c) in cn_tables._CN_TABLE if lc.value == cover and c]
        assert result.conditions == [c.value for c in rows]

    def test_range_of_forest_group_a(self):
        """Forest, group A spans CN 30 (good) to 45 (poor)."""
        result = ops.cn_range(land_cover="forest")
        assert (result.by_hsg["A"].minimum, result.by_hsg["A"].maximum) == (30, 45)
        assert result.conditions == ["poor", "fair", "good"]


class TestWeightedCurveNumber:
    """``cn weighted``."""

    def test_documented_example(self):
        """60% CN 55 and 40% CN 69 give 60.6 (library docstring)."""
        result = ops.cn_weighted(cn_values=[55, 69], areas=[60.0, 40.0])
        assert result.cn == pytest.approx(60.6)
        assert result.total_area == pytest.approx(100.0)
        assert result.shares == pytest.approx([0.6, 0.4])
        assert result.n_parts == 2

    def test_three_input_styles_agree_with_the_library(self):
        """Objects, parallel areas and parallel fractions give the same CN."""
        cns, areas = [55.0, 69.0, 98.0], [27.2, 13.6, 4.5]
        total = sum(areas)
        expected = calculate_weighted_cn(list(zip(cns, areas, strict=False)))
        by_parts = ops.cn_weighted(
            parts=[{"cn": c, "area": a} for c, a in zip(cns, areas, strict=False)]
        )
        by_areas = ops.cn_weighted(cn_values=cns, areas=areas)
        by_fractions = ops.cn_weighted(
            cn_values=cns, fractions=[a / total for a in areas]
        )
        by_shares = ops.cn_weighted(
            parts=[
                {"cn": c, "fraction": a / total}
                for c, a in zip(cns, areas, strict=False)
            ]
        )
        for result in (by_parts, by_areas, by_fractions, by_shares):
            assert result.cn == pytest.approx(expected, rel=1e-12)
            assert sum(result.shares) == pytest.approx(1.0)
        assert by_areas.total_area == pytest.approx(total)
        assert by_fractions.total_area is None
        assert by_shares.total_area is None

    def test_zero_area_parts_do_not_contribute(self):
        """A part with zero area has zero share."""
        result = ops.cn_weighted(cn_values=[55, 98], areas=[10.0, 0.0])
        assert result.cn == pytest.approx(55.0)
        assert result.shares == [1.0, 0.0]

    def test_fractions_within_tolerance_pass(self):
        """The tolerance on the sum of shares is 0.001."""
        result = ops.cn_weighted(cn_values=[60, 80], fractions=[0.4004, 0.6])
        assert result.cn == pytest.approx((60 * 0.4004 + 80 * 0.6) / 1.0004)

    def test_fractions_must_sum_to_one(self):
        """Shares that do not sum to 1 are rejected, with the sum reported."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.cn_weighted(cn_values=[60, 80], fractions=[0.5, 0.6])
        assert caught.value.details["reason"] == "fraction_sum"
        assert caught.value.details["sum"] == pytest.approx(1.1)
        assert "areas" in caught.value.hint

    @pytest.mark.parametrize(
        "arguments, option, reason",
        [
            ({}, "parts", "one_of"),
            ({"cn_values": [60, 80]}, "cn_values", "one_of"),
            (
                {"cn_values": [60], "areas": [1.0], "fractions": [1.0]},
                "cn_values",
                "one_of",
            ),
            (
                {"parts": [{"cn": 60, "area": 1}], "areas": [1.0]},
                "areas",
                "not_applicable",
            ),
            ({"cn_values": [60, 80], "areas": [1.0]}, "areas", "length_mismatch"),
            ({"cn_values": [160], "areas": [1.0]}, "cn_values", "maximum"),
            ({"cn_values": [0.5], "areas": [1.0]}, "cn_values", "minimum"),
            ({"cn_values": [60], "areas": [-1.0]}, "areas", "minimum"),
            ({"cn_values": [60, 70], "fractions": [-0.2, 1.2]}, "fractions", "minimum"),
            ({"cn_values": [60, 70], "areas": [0.0, 0.0]}, "areas", "zero_total"),
            ({"parts": [{"cn": 60}]}, "parts", "one_of"),
            ({"parts": [{"cn": 60, "area": 1, "fraction": 0.5}]}, "parts", "one_of"),
            ({"parts": [{"area": 1}]}, "parts", "required"),
            ({"parts": [{"cn": 60, "area": 1, "pct": 5}]}, "parts", "unknown_key"),
            (
                {"parts": [{"cn": 60, "area": 1}, {"cn": 70, "fraction": 0.5}]},
                "parts",
                "conflict",
            ),
            ({"parts": [{"cn": "60", "area": 1}]}, "parts", "type"),
            ({"parts": [{"cn": True, "area": 1}]}, "parts", "type"),
        ],
    )
    def test_invalid_inputs(self, arguments, option, reason):
        """Each malformed input names the option and a machine-readable reason."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.cn_weighted(**arguments)
        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason

    def test_run_command_documented_example(self):
        """The catalog example: three parts of a 45.3 km2 catchment."""
        envelope = run_command(
            "cn weighted",
            {"parts": [{"cn": 55, "area": 27.2}, {"cn": 69, "area": 13.6}]},
        )
        expected = calculate_weighted_cn([(55, 27.2), (69, 13.6)])
        assert envelope.result.cn == pytest.approx(expected)
        assert json.loads(envelope.to_json())["result"]["n_parts"] == 2

    def test_run_command_rejects_two_complete_groups(self):
        """The catalog ``one_of`` refuses areas and fractions together."""
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "cn weighted",
                {"cn_values": [60], "areas": [1], "fractions": [1]},
            )
        assert caught.value.details["reason"] == "one_of"


# --- scs ------------------------------------------------------------------------------

HYETOGRAPH = [2.5, 5.0, 12.5, 15.0, 8.0, 4.0, 3.0]


class TestScsEffective:
    """``scs effective``."""

    @pytest.mark.parametrize("amc", ["I", "II", "III"])
    def test_total_matches_scscn(self, amc):
        """A total depth gives the library's balance for each AMC."""
        result, notices = unwrap(
            ops.scs_effective(cn=72, precipitation_mm=50.0, amc=amc)
        )
        calculator = SCSCN(cn=72)
        expected = calculator.effective_precipitation(50.0, AMC[amc])
        assert result.cn == 72.0
        assert result.cn_adjusted == expected.cn_adjusted
        assert result.retention_mm == pytest.approx(expected.retention_mm)
        assert result.initial_abstraction_mm == pytest.approx(
            expected.initial_abstraction_mm
        )
        assert result.total_effective_mm == pytest.approx(expected.total_effective_mm)
        assert result.total_precipitation_mm == 50.0
        assert result.runoff_coefficient == pytest.approx(
            calculator.runoff_coefficient(50.0, AMC[amc])
        )
        assert result.effective_mm is None
        assert notices == []

    def test_documented_value(self):
        """CN 72, P = 50 mm, AMC II: Pe = 7.09 mm (library docstring)."""
        result, _ = unwrap(ops.scs_effective(cn=72, precipitation_mm=50.0))
        assert result.total_effective_mm == pytest.approx(7.0897, abs=1e-4)
        assert result.runoff_coefficient == pytest.approx(0.1418, abs=1e-4)

    def test_amc_changes_runoff_in_the_expected_order(self):
        """Dry < normal < wet conditions for the same storm."""
        pe = {
            amc: unwrap(ops.scs_effective(cn=72, precipitation_mm=50.0, amc=amc))[
                0
            ].total_effective_mm
            for amc in AMC_CLASSES
        }
        assert pe["I"] < pe["II"] < pe["III"]

    def test_series_matches_scscn_per_step(self):
        """A hyetograph gives the library's incremental effective precipitation."""
        result, _ = unwrap(ops.scs_effective(cn=72, values=HYETOGRAPH))
        expected = SCSCN(cn=72).effective_precipitation(HYETOGRAPH)
        assert_arrays(result.effective_mm, expected.effective_mm)
        assert result.total_effective_mm == pytest.approx(expected.total_effective_mm)
        assert result.total_precipitation_mm == pytest.approx(sum(HYETOGRAPH))

    def test_series_total_equals_the_total_depth_result(self):
        """SCS-CN works on cumulative depth: steps add up to the one-shot total."""
        series, _ = unwrap(ops.scs_effective(cn=72, values=HYETOGRAPH))
        total, _ = unwrap(ops.scs_effective(cn=72, precipitation_mm=sum(HYETOGRAPH)))
        assert series.effective_mm.sum() == pytest.approx(total.total_effective_mm)
        assert series.total_effective_mm == pytest.approx(total.total_effective_mm)

    def test_series_from_a_semicolon_csv_with_decimal_commas(self, tmp_path):
        """File input: header row, ``;`` delimiter, ``12,5`` decimals, unit suffix."""
        path = tmp_path / "opad.csv"
        rows = [
            f"{10 * i};{str(v).replace('.', ',')}" for i, v in enumerate(HYETOGRAPH)
        ]
        path.write_text("czas;P [mm]\n" + "\n".join(rows) + "\n", encoding="utf-8")
        from_file, _ = unwrap(
            ops.scs_effective(cn=72, input_file=str(path), value_column="P")
        )
        inline, _ = unwrap(ops.scs_effective(cn=72, values=HYETOGRAPH))
        assert_arrays(from_file.effective_mm, inline.effective_mm)

    def test_fractional_cn(self):
        """A weighted CN is used as it is."""
        result, _ = unwrap(ops.scs_effective(cn=72.5, precipitation_mm=50.0))
        expected = SCSCN(cn=72.5).effective_precipitation(50.0)
        assert result.total_effective_mm == pytest.approx(expected.total_effective_mm)
        assert result.cn_adjusted == 72.5

    def test_no_precipitation_gives_zero_runoff(self):
        """P = 0 gives zero effective precipitation and coefficient."""
        result, _ = unwrap(ops.scs_effective(cn=72, precipitation_mm=0.0))
        assert result.total_effective_mm == 0.0
        assert result.runoff_coefficient == 0.0

    def test_nonstandard_ia_coefficient_is_reported(self):
        """λ other than 0.2 changes the result and gives an info notice."""
        standard, none = unwrap(ops.scs_effective(cn=72, precipitation_mm=50.0))
        alternative, notices = unwrap(
            ops.scs_effective(cn=72, precipitation_mm=50.0, ia_coefficient=0.05)
        )
        expected = SCSCN(cn=72, ia_coefficient=0.05).effective_precipitation(50.0)
        assert alternative.total_effective_mm == pytest.approx(
            expected.total_effective_mm
        )
        assert alternative.total_effective_mm > standard.total_effective_mm
        assert none == []
        assert [(n.level, n.code) for n in notices] == [
            ("info", "ia_coefficient_nonstandard")
        ]

    @pytest.mark.parametrize(
        "arguments, option, reason",
        [
            ({}, "precipitation_mm", "one_of"),
            ({"precipitation_mm": 5.0, "values": [1.0]}, "precipitation_mm", "one_of"),
            (
                {"precipitation_mm": 5.0, "value_column": "P"},
                "value_column",
                "not_applicable",
            ),
            ({"values": [1.0], "value_column": "P"}, "value_column", "not_applicable"),
            ({"values": [1.0, -2.0]}, "values", "negative_value"),
            ({"values": [1.0], "amc": "IV"}, "amc", "choice"),
        ],
    )
    def test_invalid_inputs(self, arguments, option, reason):
        """Wrong combinations and values name the option and the reason."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.scs_effective(cn=72, **arguments)
        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason

    def test_cn_outside_the_range_is_rejected(self):
        """The library check is reported as a validation error."""
        with pytest.raises(InvalidParameterError):
            ops.scs_effective(cn=0.5, precipitation_mm=10.0)

    def test_missing_value_in_a_file_is_a_data_error(self, tmp_path):
        """An empty cell in the file is an ``InputDataError`` with row and path."""
        path = tmp_path / "opad.csv"
        path.write_text("P,Q\n1.0,1\n,2\n", encoding="utf-8")
        with pytest.raises(InputDataError) as caught:
            ops.scs_effective(cn=72, input_file=str(path), value_column="P")
        assert caught.value.details["reason"] == "missing_value"
        assert caught.value.details["row"] == 2
        assert caught.value.details["path"].endswith("opad.csv")

    def test_negative_value_in_a_file_is_a_data_error(self, tmp_path):
        """A negative depth in a file names the row."""
        path = tmp_path / "opad.csv"
        path.write_text("P\n1.0\n-3.0\n", encoding="utf-8")
        with pytest.raises(InputDataError) as caught:
            ops.scs_effective(cn=72, input_file=str(path))
        assert caught.value.details["reason"] == "negative_value"
        assert caught.value.details["row"] == 2

    def test_missing_file_is_not_found(self, tmp_path):
        """A file that does not exist is ``not_found``."""
        with pytest.raises(NotFoundError):
            ops.scs_effective(cn=72, input_file=str(tmp_path / "brak.csv"))

    def test_run_command_series(self):
        """End to end with the catalog defaults recorded in the inputs."""
        envelope = run_command("scs effective", {"cn": 72, "values": HYETOGRAPH})
        assert envelope.inputs["amc"] == "II"
        assert envelope.inputs["ia_coefficient"] == 0.2
        document = json.loads(envelope.to_json())
        assert len(document["result"]["effective_mm"]) == len(HYETOGRAPH)
        assert document["result"]["total_effective_mm"] == pytest.approx(
            7.0897, abs=1e-4
        )


# --- precip hietogram -----------------------------------------------------------------


class TestHietogram:
    """``precip hietogram``."""

    @pytest.mark.parametrize(
        "kind, generator",
        [
            ("block", BlockHietogram()),
            ("triangular", TriangularHietogram()),
            ("beta", BetaHietogram()),
            ("euler_ii", EulerIIHietogram()),
        ],
    )
    def test_matches_the_generator(self, kind, generator):
        """Depths, times and intensities are the generator's; blocks add up."""
        expected = generator.generate(
            total_mm=42.0, duration_min=90.0, timestep_min=5.0
        )
        result, notices = unwrap(
            ops.precip_hietogram(
                hietogram_type=kind, total_mm=42.0, duration_min=90.0, timestep_min=5.0
            )
        )
        assert result.hietogram_type == kind
        assert result.n_steps == expected.n_steps == 18
        assert_arrays(result.depths_mm, expected.intensities_mm)
        assert_arrays(result.times_min, expected.times_min)
        assert_arrays(result.intensities_mm_per_h, expected.intensity_mm_per_h)
        assert result.peak_intensity_mm_per_h == pytest.approx(
            expected.intensity_mm_per_h.max()
        )
        assert result.depths_mm.sum() == pytest.approx(42.0)
        assert (result.total_mm, result.duration_min, result.timestep_min) == (
            42.0,
            90.0,
            5.0,
        )
        assert notices == []

    @pytest.mark.parametrize(
        "kind, given, generator, reported",
        [
            ("beta", {}, BetaHietogram(), {"alpha": 2.0, "beta": 5.0}),
            (
                "beta",
                {"alpha": 3.0, "beta": 3.0},
                BetaHietogram(3.0, 3.0),
                {"alpha": 3.0, "beta": 3.0},
            ),
            (
                "beta",
                {"alpha": 4.0},
                BetaHietogram(alpha=4.0),
                {"alpha": 4.0, "beta": 5.0},
            ),
            ("triangular", {}, TriangularHietogram(), {"peak_position": 0.5}),
            (
                "triangular",
                {"peak_position": 0.4},
                TriangularHietogram(0.4),
                {"peak_position": 0.4},
            ),
            ("euler_ii", {}, EulerIIHietogram(), {"peak_position": 0.33}),
            (
                "euler_ii",
                {"peak_position": 0.5},
                EulerIIHietogram(0.5),
                {"peak_position": 0.5},
            ),
            ("block", {}, BlockHietogram(), {}),
        ],
    )
    def test_shape_parameters_and_their_defaults(
        self, kind, given, generator, reported
    ):
        """Given parameters reach the generator; the defaults used are reported."""
        expected = generator.generate(
            total_mm=30.0, duration_min=60.0, timestep_min=10.0
        )
        result, _ = unwrap(
            ops.precip_hietogram(
                hietogram_type=kind,
                total_mm=30.0,
                duration_min=60.0,
                timestep_min=10.0,
                **given,
            )
        )
        assert_arrays(result.depths_mm, expected.intensities_mm)
        assert result.parameters == reported

    def test_euler_ii_peak_is_early(self):
        """Euler type II puts its highest block near a third of the duration."""
        result, _ = unwrap(
            ops.precip_hietogram(
                hietogram_type="euler_ii", total_mm=50.0, duration_min=60.0
            )
        )
        assert (
            int(np.argmax(result.depths_mm)) + 1 == 4
        )  # library docstring: interval 4 of 12

    @pytest.mark.parametrize(
        "kind, given",
        [
            ("block", {"alpha": 2.0}),
            ("block", {"beta": 2.0}),
            ("block", {"peak_position": 0.4}),
            ("beta", {"peak_position": 0.4}),
            ("triangular", {"alpha": 2.0}),
            ("euler_ii", {"beta": 5.0}),
        ],
    )
    def test_parameter_of_another_type_is_rejected(self, kind, given):
        """A parameter that the chosen type does not have is not ignored."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.precip_hietogram(
                hietogram_type=kind, total_mm=30.0, duration_min=60.0, **given
            )
        assert caught.value.details == {
            "option": next(iter(given)),
            "reason": "not_applicable",
        }
        assert caught.value.hint

    def test_duration_not_a_multiple_of_the_step_is_reported(self):
        """The library truncates to whole steps; the notice says what is covered."""
        result, notices = unwrap(
            ops.precip_hietogram(
                hietogram_type="block",
                total_mm=30.0,
                duration_min=100.0,
                timestep_min=30.0,
            )
        )
        assert result.n_steps == 3
        assert result.duration_min == 100.0
        assert [(n.level, n.code) for n in notices] == [
            ("warning", "duration_not_covered")
        ]
        assert "covers 90 min" in notices[0].text

    def test_values_outside_the_library_ranges_are_validation_errors(self):
        """Step longer than the duration and a peak outside (0, 1)."""
        with pytest.raises(InvalidParameterError):
            ops.precip_hietogram(
                hietogram_type="block",
                total_mm=30.0,
                duration_min=10.0,
                timestep_min=30.0,
            )
        with pytest.raises(InvalidParameterError):
            ops.precip_hietogram(
                hietogram_type="triangular",
                total_mm=30.0,
                duration_min=60.0,
                peak_position=1.0,
            )

    def test_unknown_type_is_a_choice_error(self):
        """A type outside the four is a validation error with the allowed list."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.precip_hietogram(
                hietogram_type="gauss", total_mm=30.0, duration_min=60.0
            )
        assert caught.value.details["reason"] == "choice"
        assert caught.value.details["allowed"] == list(HIETOGRAM_TYPES)

    def test_run_command_strict_json(self):
        """The catalog example runs and every array is plain JSON numbers."""
        example = get_command("precip hietogram").examples[0]
        document = json.loads(run_command("precip hietogram", example).to_json())
        result = document["result"]
        assert result["hietogram_type"] == "beta"
        assert sum(result["depths_mm"]) == pytest.approx(50.0)
        assert len(result["times_min"]) == result["n_steps"] == 12


# --- precip areal ---------------------------------------------------------------------

POLYGONS = {"Balice": 18.5, "Krzeszowice": 14.2, "Skawina": 12.6}


class TestArealPrecipitation:
    """``precip areal``."""

    def test_arithmetic_mean(self):
        """The mean of the gauges."""
        result, notices = unwrap(
            ops.precip_areal(method="arithmetic", stations=STATIONS)
        )
        assert result.areal_precipitation_mm == pytest.approx(arithmetic_mean(GAUGES))
        assert result.areal_precipitation_mm == pytest.approx((31.2 + 36.8 + 28.4) / 3)
        assert result.n_stations == 3
        assert result.station_weights is None
        assert notices == []

    def test_thiessen_matches_the_library(self):
        """Weights and contributions are the library's."""
        result, notices = unwrap(
            ops.precip_areal(
                method="thiessen", stations=STATIONS, polygon_areas_km2=POLYGONS
            )
        )
        expected = thiessen_polygons(GAUGES, POLYGONS)
        assert result.areal_precipitation_mm == pytest.approx(
            expected.areal_precipitation_mm
        )
        assert result.station_weights == pytest.approx(expected.station_weights)
        assert result.station_contributions_mm == pytest.approx(
            expected.station_contributions_mm
        )
        assert sum(result.station_weights.values()) == pytest.approx(1.0)
        assert notices == []

    def test_thiessen_names_the_gauges_without_an_area(self):
        """A gauge without a polygon is skipped by the library; a notice lists it."""
        result, notices = unwrap(
            ops.precip_areal(
                method="thiessen",
                stations=STATIONS,
                polygon_areas_km2={"Balice": 18.5, "Skawina": 12.6},
            )
        )
        assert sorted(result.station_weights) == ["Balice", "Skawina"]
        assert [n.code for n in notices] == ["stations_without_polygon"]
        assert "Krzeszowice" in notices[0].text

    def test_idw_at_a_point_matches_the_library(self):
        """Point interpolation with the default and a given exponent."""
        for power in (None, 3.0):
            result, _ = unwrap(
                ops.precip_areal(
                    method="idw",
                    stations=STATIONS,
                    target_x=553000.0,
                    target_y=240000.0,
                    power=power,
                )
            )
            expected = inverse_distance_weighting(
                GAUGES, 553000.0, 240000.0, power=2.0 if power is None else power
            )
            assert result.areal_precipitation_mm == pytest.approx(
                expected.areal_precipitation_mm
            )
            assert result.station_weights == pytest.approx(expected.station_weights)
            assert result.power == (2.0 if power is None else power)
            assert result.n_grid_points is None

    def test_idw_max_distance_drops_far_gauges(self):
        """Only gauges within ``max_distance`` get a weight."""
        result, _ = unwrap(
            ops.precip_areal(
                method="idw",
                stations=STATIONS,
                target_x=553000.0,
                target_y=240000.0,
                max_distance=12000.0,
            )
        )
        expected = inverse_distance_weighting(
            GAUGES, 553000.0, 240000.0, max_distance=12000.0
        )
        assert set(result.station_weights) == set(expected.station_weights)
        assert 0 < len(result.station_weights) < 3

    def test_idw_over_a_grid_matches_the_library(self):
        """The grid variant returns the mean of the point values."""
        grid_x = [551000.0, 553000.0, 555000.0]
        grid_y = [238000.0, 240000.0, 242000.0]
        result, _ = unwrap(
            ops.precip_areal(
                method="idw", stations=STATIONS, grid_x=grid_x, grid_y=grid_y
            )
        )
        expected = areal_precipitation_idw(
            GAUGES, np.array(grid_x), np.array(grid_y), 2.0
        )
        assert result.areal_precipitation_mm == pytest.approx(expected)
        assert result.n_grid_points == 3
        assert result.station_weights is None

    def test_isohyets_match_the_library(self):
        """Zone means weighted by area fractions."""
        values, fractions = [20.0, 30.0, 40.0, 50.0], [0.3, 0.5, 0.2]
        result, _ = unwrap(
            ops.precip_areal(
                method="isohyet", isohyet_values_mm=values, area_fractions=fractions
            )
        )
        expected = isohyet_method(np.array(values), np.array(fractions))
        assert result.areal_precipitation_mm == pytest.approx(
            expected.areal_precipitation_mm
        )
        assert result.areal_precipitation_mm == pytest.approx(34.0)
        assert result.n_stations is None
        assert_arrays(result.area_fractions, fractions)

    def test_stations_from_a_csv_file(self, tmp_path):
        """``stations_file`` gives the same result as the inline records."""
        path = tmp_path / "posterunki.csv"
        lines = ["name,x,y,precipitation_mm"] + [
            f"{s['name']},{s['x']},{s['y']},{s['precipitation_mm']}" for s in STATIONS
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        from_file, _ = unwrap(
            ops.precip_areal(
                method="thiessen", stations_file=str(path), polygon_areas_km2=POLYGONS
            )
        )
        inline, _ = unwrap(
            ops.precip_areal(
                method="thiessen", stations=STATIONS, polygon_areas_km2=POLYGONS
            )
        )
        assert from_file.areal_precipitation_mm == pytest.approx(
            inline.areal_precipitation_mm
        )

    @pytest.mark.parametrize(
        "arguments, option, reason",
        [
            ({"method": "arithmetic"}, "stations", "one_of"),
            (
                {"method": "thiessen", "stations": STATIONS},
                "polygon_areas_km2",
                "required",
            ),
            (
                {
                    "method": "thiessen",
                    "stations": STATIONS,
                    "polygon_areas_km2": {"Balice": -1},
                },
                "polygon_areas_km2",
                "minimum",
            ),
            (
                {
                    "method": "thiessen",
                    "stations": STATIONS,
                    "polygon_areas_km2": {"Balice": "x"},
                },
                "polygon_areas_km2",
                "type",
            ),
            (
                {
                    "method": "arithmetic",
                    "stations": STATIONS,
                    "polygon_areas_km2": POLYGONS,
                },
                "polygon_areas_km2",
                "not_applicable",
            ),
            (
                {"method": "arithmetic", "stations": STATIONS, "power": 2.0},
                "power",
                "not_applicable",
            ),
            (
                {"method": "idw", "stations": STATIONS},
                "target_x",
                "one_of",
            ),
            (
                {"method": "idw", "stations": STATIONS, "target_x": 1.0},
                "target_x",
                "one_of",
            ),
            (
                {
                    "method": "idw",
                    "stations": STATIONS,
                    "target_x": 1.0,
                    "target_y": 1.0,
                    "grid_x": [1.0],
                    "grid_y": [1.0],
                },
                "target_x",
                "one_of",
            ),
            (
                {
                    "method": "idw",
                    "stations": STATIONS,
                    "grid_x": [1.0],
                    "grid_y": [1.0],
                    "max_distance": 5.0,
                },
                "max_distance",
                "not_applicable",
            ),
            (
                {
                    "method": "idw",
                    "stations": STATIONS,
                    "target_x": 1.0,
                    "target_y": 1.0,
                    "polygon_areas_km2": POLYGONS,
                },
                "polygon_areas_km2",
                "not_applicable",
            ),
            (
                {"method": "isohyet", "isohyet_values_mm": [10.0, 20.0]},
                "area_fractions",
                "required",
            ),
            (
                {
                    "method": "isohyet",
                    "isohyet_values_mm": [10.0, 20.0],
                    "area_fractions": [1.0],
                    "stations": STATIONS,
                },
                "stations",
                "not_applicable",
            ),
            (
                {
                    "method": "arithmetic",
                    "stations": STATIONS,
                    "isohyet_values_mm": [1.0, 2.0],
                },
                "isohyet_values_mm",
                "not_applicable",
            ),
            ({"method": "kriging", "stations": STATIONS}, "method", "choice"),
        ],
    )
    def test_invalid_inputs(self, arguments, option, reason):
        """Missing, foreign and malformed options name the option and the reason."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.precip_areal(**arguments)
        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason

    def test_library_errors_pass_through(self):
        """Fractions that do not sum to one are the library's validation error."""
        with pytest.raises(InvalidParameterError):
            ops.precip_areal(
                method="isohyet", isohyet_values_mm=[10.0, 20.0], area_fractions=[0.4]
            )
        with pytest.raises(InvalidParameterError):
            ops.precip_areal(
                method="thiessen",
                stations=STATIONS,
                polygon_areas_km2={"Nieznany": 5.0},
            )

    def test_run_command_idw_example(self):
        """End to end through the catalog; JSON keeps the station weights."""
        example = get_command("precip areal").examples[2]
        document = json.loads(run_command("precip areal", example).to_json())
        assert document["result"]["method"] == "idw"
        assert sum(document["result"]["station_weights"].values()) == pytest.approx(1.0)


# --- uh -------------------------------------------------------------------------------


def volume_in_mm(result):
    """Depth under the unit hydrograph: should be 1 mm over the catchment."""
    seconds = result.timestep_min * 60.0
    return result.ordinates_m3s_per_mm.sum() * seconds / (result.area_km2 * 1000.0)


class TestUnitHydrographs:
    """``uh scs|nash|clark|snyder``."""

    def test_scs_matches_the_class(self):
        """Summary values and ordinates are SCSUnitHydrograph's."""
        result = ops.uh_scs(area_km2=45.3, tc_min=90.0, timestep_min=5.0)
        expected = SCSUnitHydrograph(area_km2=45.3, tc_min=90.0).generate(
            timestep_min=5.0
        )
        assert (result.model, result.estimation) == ("scs", "direct")
        assert_arrays(result.times_min, expected.times_min)
        assert_arrays(result.ordinates_m3s_per_mm, expected.ordinates_m3s)
        assert (
            result.time_to_peak_min == expected.time_to_peak_min == pytest.approx(56.5)
        )
        assert result.peak_discharge_m3s_per_mm == pytest.approx(
            expected.peak_discharge_m3s
        )
        assert result.lag_time_min == pytest.approx(54.0)  # 0.6 * tc
        assert result.time_base_min == pytest.approx(expected.time_base_min)
        assert result.duration_min == result.timestep_min == 5.0
        assert result.parameters == {"tc_min": 90.0}
        assert volume_in_mm(result) == pytest.approx(1.0, abs=2e-3)

    def test_nash_direct_matches_the_class(self):
        """Direct n and K: the D = step unit hydrograph of ``NashIUH.generate``."""
        result = ops.uh_nash(area_km2=45.3, n=3.0, k_min=30.0, timestep_min=5.0)
        expected = NashIUH(n=3.0, k_min=30.0, area_km2=45.3).generate(timestep_min=5.0)
        assert (result.model, result.estimation) == ("nash", "direct")
        assert_arrays(result.times_min, expected.times_min)
        assert_arrays(result.ordinates_m3s_per_mm, expected.ordinates_m3s)
        assert result.time_to_peak_min == expected.time_to_peak_min
        assert result.peak_discharge_m3s_per_mm == pytest.approx(
            expected.peak_discharge_m3s
        )
        assert result.lag_time_min == pytest.approx(90.0)  # n * K
        assert result.parameters == {"n": 3.0, "k_min": 30.0}
        assert result.lutz is None and result.time_base_min is None
        assert volume_in_mm(result) == pytest.approx(1.0, abs=1e-3)

    def test_nash_rainfall_duration_and_total_length(self):
        """D and the length of the result are passed to ``to_unit_hydrograph``."""
        result = ops.uh_nash(
            area_km2=45.3,
            n=3.0,
            k_min=30.0,
            timestep_min=5.0,
            rainfall_duration_min=20.0,
            total_duration_min=300.0,
        )
        expected = NashIUH(n=3.0, k_min=30.0).to_unit_hydrograph(
            area_km2=45.3, duration_min=20.0, timestep_min=5.0, total_duration_min=300.0
        )
        assert_arrays(result.ordinates_m3s_per_mm, expected.ordinates_m3s)
        assert result.duration_min == 20.0
        assert result.times_min[-1] == 300.0

    def test_nash_lutz_matches_from_lutz(self):
        """Lutz estimation: n, K and the intermediate results are the library's."""
        result = ops.uh_nash(
            area_km2=45.0,
            lutz_length_km=8.2,
            lutz_centroid_length_km=4.5,
            lutz_slope_m_per_m=0.023,
            lutz_manning_n=0.035,
            lutz_urban_pct=5.0,
            lutz_forest_pct=30.0,
        )
        cascade = NashIUH.from_lutz(
            L_km=8.2,
            Lc_km=4.5,
            slope=0.023,
            manning_n=0.035,
            urban_pct=5.0,
            forest_pct=30.0,
            area_km2=45.0,
        )
        expected = cascade.generate(timestep_min=5.0)
        assert result.estimation == "lutz"
        assert result.parameters == {"n": cascade.n, "k_min": cascade.k_min}
        assert result.lutz == cascade.lutz_params
        assert result.lutz.tp_hours == pytest.approx(cascade.lutz_params.tp_hours)
        assert_arrays(result.ordinates_m3s_per_mm, expected.ordinates_m3s)

    def test_nash_lutz_defaults_urban_and_forest_to_zero(self):
        """Optional shares default to the library's 0 %."""
        result = ops.uh_nash(
            area_km2=45.0,
            lutz_length_km=15.0,
            lutz_centroid_length_km=8.0,
            lutz_slope_m_per_m=0.02,
            lutz_manning_n=0.035,
        )
        cascade = NashIUH.from_lutz(L_km=15.0, Lc_km=8.0, slope=0.02, manning_n=0.035)
        assert result.parameters["n"] == pytest.approx(cascade.n)
        assert (result.lutz.urban_pct, result.lutz.forest_pct) == (0.0, 0.0)

    def test_nash_urban_regression_matches_the_class(self):
        """Regression estimation gives the library's N and K (docstring: N=1.621)."""
        result = ops.uh_nash(
            area_km2=1.3,
            urban_effective_precip_mm=1.305,
            urban_duration_h=0.167,
            urban_fraction=0.05,
            timestep_min=2.0,
        )
        cascade = NashIUH.from_urban_regression(
            area_km2=1.3,
            effective_precip_mm=1.305,
            duration_h=0.167,
            urban_fraction=0.05,
        )
        expected = cascade.generate(timestep_min=2.0)
        assert result.estimation == "urban_regression"
        assert result.parameters["n"] == pytest.approx(1.621, abs=1e-3)
        assert result.parameters == {"n": cascade.n, "k_min": cascade.k_min}
        assert_arrays(result.ordinates_m3s_per_mm, expected.ordinates_m3s)

    @pytest.mark.parametrize(
        "arguments, option, reason",
        [
            ({}, "n", "one_of"),
            ({"n": 3.0}, "n", "one_of"),
            (
                {"n": 3.0, "k_min": 30.0, "lutz_length_km": 8.0},
                "lutz_length_km",
                "not_applicable",
            ),
            (
                {"n": 3.0, "k_min": 30.0, "lutz_urban_pct": 5.0},
                "lutz_urban_pct",
                "not_applicable",
            ),
            (
                {"n": 3.0, "k_min": 30.0, "urban_fraction": 0.1},
                "urban_fraction",
                "not_applicable",
            ),
            (
                {
                    "n": 3.0,
                    "k_min": 30.0,
                    "urban_effective_precip_mm": 5.0,
                    "urban_duration_h": 1.0,
                },
                "n",
                "one_of",
            ),
            (
                {
                    "lutz_length_km": 8.0,
                    "lutz_centroid_length_km": 4.0,
                    "lutz_slope_m_per_m": 0.02,
                    "lutz_manning_n": 0.035,
                    "urban_fraction": 0.1,
                },
                "urban_fraction",
                "not_applicable",
            ),
        ],
    )
    def test_nash_group_selection_errors(self, arguments, option, reason):
        """Exactly one parameter group; options of another group are rejected."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.uh_nash(area_km2=45.0, **arguments)
        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason

    def test_nash_lutz_impossible_input_is_a_validation_error(self):
        """Lc longer than L is rejected by the library, not computed."""
        with pytest.raises(InvalidParameterError, match="cannot exceed"):
            ops.uh_nash(
                area_km2=45.0,
                lutz_length_km=4.0,
                lutz_centroid_length_km=8.0,
                lutz_slope_m_per_m=0.02,
                lutz_manning_n=0.035,
            )

    @pytest.mark.parametrize("given", [{"r_min": 60.0}, {"r_tc_ratio": 0.5}])
    def test_clark_matches_the_class(self, given):
        """R directly or from R/tc: the unit hydrograph of ``ClarkIUH.generate``."""
        result = ops.uh_clark(area_km2=45.3, tc_min=120.0, timestep_min=10.0, **given)
        if "r_min" in given:
            reservoir = ClarkIUH(tc_min=120.0, r_min=60.0, area_km2=45.3)
        else:
            reservoir = ClarkIUH.from_tc_r_ratio(tc_min=120.0, r_tc_ratio=0.5)
            reservoir.area_km2 = 45.3
        expected = reservoir.generate(timestep_min=10.0)
        assert result.model == "clark"
        assert result.estimation == ("direct" if "r_min" in given else "r_tc_ratio")
        assert_arrays(result.times_min, expected.times_min)
        assert_arrays(result.ordinates_m3s_per_mm, expected.ordinates_m3s)
        assert result.time_to_peak_min == expected.time_to_peak_min
        assert result.lag_time_min == pytest.approx(120.0 / 2 + 60.0)
        assert result.parameters["r_min"] == pytest.approx(60.0)
        assert result.time_base_min is None
        assert volume_in_mm(result) == pytest.approx(1.0, abs=1e-3)

    @pytest.mark.parametrize("duration", [10.0, 7.0, 2.0, 12.5])
    def test_clark_rainfall_duration_is_any_positive_value(self, duration):
        """D, a multiple of the step or not, gives the class's hydrograph of 1 mm."""
        result = ops.uh_clark(
            area_km2=45.3,
            tc_min=120.0,
            r_min=60.0,
            timestep_min=5.0,
            rainfall_duration_min=duration,
            total_duration_min=1200.0,
        )
        expected = ClarkIUH(tc_min=120.0, r_min=60.0).to_unit_hydrograph(
            area_km2=45.3,
            duration_min=duration,
            timestep_min=5.0,
            total_duration_min=1200.0,
        )
        assert_arrays(result.ordinates_m3s_per_mm, expected.ordinates_m3s)
        assert result.duration_min == duration
        assert volume_in_mm(result) == pytest.approx(1.0, abs=1e-6)

    def test_clark_needs_exactly_one_of_r_and_ratio(self):
        """Both or neither of ``r_min`` / ``r_tc_ratio`` is a one_of error."""
        for given in ({}, {"r_min": 60.0, "r_tc_ratio": 0.5}):
            with pytest.raises(InvalidParameterError) as caught:
                ops.uh_clark(area_km2=45.3, tc_min=120.0, **given)
            assert caught.value.details["reason"] == "one_of"

    def test_snyder_matches_the_class(self):
        """The Snyder unit hydrograph with its own lag, no external tc."""
        result = ops.uh_snyder(area_km2=100.0, length_km=15.0, centroid_length_km=8.0)
        model = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        expected = model.generate(timestep_min=30.0)
        assert (result.model, result.estimation) == ("snyder", "direct")
        assert_arrays(result.times_min, expected.times_min)
        assert_arrays(result.ordinates_m3s_per_mm, expected.ordinates_m3s)
        assert result.time_to_peak_min == pytest.approx(expected.time_to_peak_min)
        assert result.time_base_min == pytest.approx(expected.time_base_min)
        assert result.lag_time_min == pytest.approx(model.lag_time_min)
        assert result.derived == {
            "standard_duration_min": pytest.approx(model.standard_duration_min),
            "adjusted_lag_time_min": pytest.approx(expected.adjusted_lag_time_min),
        }
        assert result.parameters == {
            "length_km": 15.0,
            "centroid_length_km": 8.0,
            "ct": 1.5,
            "cp": 0.6,
        }
        assert volume_in_mm(result) == pytest.approx(1.0, abs=1e-3)

    def test_snyder_coefficients_duration_and_total_length(self):
        """Ct, Cp, D and the length of the result reach the class."""
        result = ops.uh_snyder(
            area_km2=45.3,
            length_km=12.5,
            centroid_length_km=6.0,
            ct=1.65,
            cp=0.565,
            timestep_min=10.0,
            rainfall_duration_min=60.0,
            total_duration_min=900.0,
        )
        expected = SnyderUH(
            area_km2=45.3, L_km=12.5, Lc_km=6.0, ct=1.65, cp=0.565
        ).generate(timestep_min=10.0, duration_min=60.0, total_duration_min=900.0)
        assert_arrays(result.ordinates_m3s_per_mm, expected.ordinates_m3s)
        assert result.duration_min == 60.0
        assert result.times_min[-1] == 900.0

    def test_invalid_parameters_are_validation_errors(self):
        """Library range checks surface as ``validation_error``."""
        with pytest.raises(InvalidParameterError):
            ops.uh_scs(area_km2=45.3, tc_min=-1.0)
        with pytest.raises(InvalidParameterError):
            ops.uh_snyder(area_km2=45.3, length_km=0.0, centroid_length_km=1.0)

    def test_run_command_nash_lutz_envelope(self):
        """The Lutz example end to end: intermediate results survive the JSON."""
        example = get_command("uh nash").examples[1]
        document = json.loads(run_command("uh nash", example).to_json())
        result = document["result"]
        assert result["estimation"] == "lutz"
        assert result["lutz"]["P1"] == pytest.approx(3.989 * 0.035 + 0.028)
        assert len(result["times_min"]) == len(result["ordinates_m3s_per_mm"])
        assert document["inputs"]["timestep_min"] == 5.0


# --- hydrograph -----------------------------------------------------------------------

WATERSHED = without(
    FULL_WATERSHED,
    "runoff_coeff",
    "retardance",
    "overland_length_km",
    "overland_slope_m_per_m",
)
STORM = {
    "hietogram_type": "beta",
    "total_mm": 50.0,
    "duration_min": 60.0,
    "timestep_min": 5.0,
}
SERIES = [5.0, 10.0, 15.0, 10.0, 5.0, 3.0]
# A watershed without CN (L = 12 km, land slope 2.5 %) and a 50 mm / 120 min beta
# storm: the case of the review of the CN override (tc by NRCS).
OVERRIDE_WATERSHED = {
    "name": "Zlewnia CN",
    "area_km2": 45.0,
    "perimeter_km": 32.0,
    "length_km": 12.0,
    "elevation_min_m": 150.0,
    "elevation_max_m": 520.0,
    "mean_slope_m_per_m": 0.025,
}
OVERRIDE_STORM = {"hietogram_type": "beta", "total_mm": 50.0, "duration_min": 120.0}


def library_run(
    *,
    area=45.3,
    cn=72,
    tc=90.0,
    model="scs",
    params=None,
    ia=0.2,
    amc=AMC.II,
    rain=None,
):
    """The same computation written directly with the library classes."""
    generator = HydrographGenerator(
        area_km2=area,
        cn=cn,
        tc_min=tc,
        ia_coefficient=ia,
        uh_model=model,
        uh_params=params,
    )
    if rain is None:
        rain = BetaHietogram().generate(
            total_mm=50.0, duration_min=60.0, timestep_min=5.0
        )
    return generator.generate(rain, amc=amc)


class TestHydrographGenerate:
    """``hydrograph generate`` and ``compute_hydrograph``."""

    @pytest.mark.parametrize(
        "model, tc, extra, params",
        [
            ("scs", 90.0, {}, {}),
            ("nash", None, {"nash_n": 3.0, "nash_k_min": 48.0}, {"n": 3.0, "k": 0.8}),
            ("clark", 120.0, {"clark_r_min": 60.0}, {"r": 60.0}),
            (
                "snyder",
                None,
                {"snyder_length_km": 15.0, "snyder_centroid_length_km": 8.0},
                {"L_km": 15.0, "Lc_km": 8.0},
            ),
            (
                "snyder",
                None,
                {
                    "snyder_length_km": 15.0,
                    "snyder_centroid_length_km": 8.0,
                    "snyder_ct": 1.65,
                    "snyder_cp": 0.565,
                },
                {"L_km": 15.0, "Lc_km": 8.0, "ct": 1.65, "cp": 0.565},
            ),
        ],
    )
    def test_matches_the_generator_for_every_model(self, model, tc, extra, params):
        """Design storm + unit hydrograph model equals ``HydrographGenerator``."""
        result, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.3, cn=72, tc_min=tc, uh_model=model, **extra, **STORM
            )
        )
        expected = library_run(tc=tc, model=model, params=params or None)
        assert result.uh_model == model
        assert result.peak_discharge_m3s == pytest.approx(expected.peak_discharge_m3s)
        assert result.time_to_peak_min == expected.time_to_peak_min
        assert result.total_volume_m3 == pytest.approx(expected.total_volume_m3)
        assert result.runoff_coefficient == pytest.approx(expected.runoff_coefficient)
        assert result.total_effective_mm == pytest.approx(expected.total_effective_mm)
        assert_arrays(result.discharge_m3s, expected.hydrograph.discharge_m3s)
        assert_arrays(result.times_min, expected.hydrograph.times_min)
        assert_arrays(result.effective_precipitation_mm, expected.effective_precip_mm)
        assert result.duration_min == expected.hydrograph.duration_min

    def test_nash_k_is_in_minutes(self):
        """``nash_k_min`` is minutes: 48 min equals the generator's 0.8 hours."""
        by_minutes, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.0,
                cn=72,
                uh_model="nash",
                nash_n=3.0,
                nash_k_min=48.0,
                **STORM,
            )
        )
        by_hours = library_run(
            area=45.0,
            tc=None,
            model="nash",
            params={"n": 3.0, "k": 0.8, "k_unit": "hours"},
        )
        assert by_minutes.peak_discharge_m3s == pytest.approx(
            by_hours.peak_discharge_m3s
        )

    def test_clark_ratio_matches_r_computed_from_tc(self):
        """``clark_r_tc_ratio`` is R = ratio * tc."""
        by_ratio, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.3,
                cn=72,
                tc_min=120.0,
                uh_model="clark",
                clark_r_tc_ratio=0.5,
                **STORM,
            )
        )
        by_value, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.3,
                cn=72,
                tc_min=120.0,
                uh_model="clark",
                clark_r_min=60.0,
                **STORM,
            )
        )
        assert_arrays(by_ratio.discharge_m3s, by_value.discharge_m3s)
        assert by_ratio.uh_parameters == {"tc_min": 120.0, "r_min": 60.0}

    @pytest.mark.parametrize("kind", ["block", "triangular", "euler_ii"])
    def test_other_hyetograph_types(self, kind):
        """The hyetograph comes from the generator of the chosen type."""
        generated = {
            "block": BlockHietogram(),
            "triangular": TriangularHietogram(),
            "euler_ii": EulerIIHietogram(),
        }[kind].generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)
        result, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.3,
                cn=72,
                tc_min=90.0,
                hietogram_type=kind,
                total_mm=50.0,
                duration_min=60.0,
            )
        )
        expected = library_run(rain=generated)
        assert_arrays(result.precipitation_mm, generated.intensities_mm)
        assert result.peak_discharge_m3s == pytest.approx(expected.peak_discharge_m3s)
        assert result.hietogram_type == kind

    def test_hyetograph_parameters_are_forwarded(self):
        """``alpha``/``beta`` shape the Beta storm; ``peak_position`` the triangle."""
        beta, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.3,
                cn=72,
                tc_min=90.0,
                **{**STORM, "timestep_min": 5.0},
                alpha=5.0,
                beta=2.0,
            )
        )
        expected = BetaHietogram(alpha=5.0, beta=2.0).generate(50.0, 60.0, 5.0)
        assert_arrays(beta.precipitation_mm, expected.intensities_mm)
        triangle, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.3,
                cn=72,
                tc_min=90.0,
                hietogram_type="triangular",
                total_mm=50.0,
                duration_min=60.0,
                peak_position=0.25,
            )
        )
        expected = TriangularHietogram(0.25).generate(50.0, 60.0, 5.0)
        assert_arrays(triangle.precipitation_mm, expected.intensities_mm)

    def test_precipitation_series_matches_the_generator(self):
        """A series of depths is used as the hyetograph, step ``timestep_min``."""
        result, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.0,
                cn=72,
                values=SERIES,
                timestep_min=10.0,
                uh_model="nash",
                nash_n=3.0,
                nash_k_min=48.0,
            )
        )
        expected = HydrographGenerator(
            area_km2=45.0, cn=72, uh_model="nash", uh_params={"n": 3.0, "k": 0.8}
        ).generate(SERIES, timestep_min=10.0)
        assert result.hietogram_type is None
        assert result.total_precipitation_mm == pytest.approx(sum(SERIES))
        assert_arrays(result.precipitation_mm, SERIES)
        assert_arrays(result.discharge_m3s, expected.hydrograph.discharge_m3s)
        assert result.peak_discharge_m3s == pytest.approx(expected.peak_discharge_m3s)

    def test_precipitation_series_from_a_file(self, tmp_path):
        """``input_file`` + ``value_column`` give the same hydrograph as ``values``."""
        path = tmp_path / "opad.csv"
        rows = "\n".join(f"{10 * i},{v}" for i, v in enumerate(SERIES))
        path.write_text("minuta,opad [mm]\n" + rows + "\n", encoding="utf-8")
        common = {"area_km2": 45.0, "cn": 72, "tc_min": 90.0, "timestep_min": 10.0}
        from_file, _ = unwrap(
            ops.hydrograph_generate(**common, input_file=str(path), value_column="opad")
        )
        inline, _ = unwrap(ops.hydrograph_generate(**common, values=SERIES))
        assert_arrays(from_file.discharge_m3s, inline.discharge_m3s)

    def test_water_balance_of_the_volume_conserving_clark_model(self):
        """Runoff volume = effective depth x area (Clark conserves volume)."""
        result, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.3,
                cn=72,
                tc_min=120.0,
                uh_model="clark",
                clark_r_min=60.0,
                **STORM,
            )
        )
        assert result.total_volume_m3 == pytest.approx(
            result.total_effective_mm * result.area_km2 * 1000.0, rel=1e-3
        )
        assert result.discharge_m3s.max() == pytest.approx(result.peak_discharge_m3s)
        assert (
            result.times_min[int(np.argmax(result.discharge_m3s))]
            == result.time_to_peak_min
        )
        assert result.runoff_coefficient == pytest.approx(
            result.total_effective_mm / result.total_precipitation_mm
        )

    @pytest.mark.parametrize("amc", ["I", "II", "III"])
    def test_amc_and_ia_coefficient_reach_the_generator(self, amc):
        """AMC adjustment and initial abstraction ratio act as in the library."""
        result, notices = unwrap(
            ops.hydrograph_generate(
                area_km2=45.3, cn=72, tc_min=90.0, amc=amc, ia_coefficient=0.1, **STORM
            )
        )
        expected = library_run(amc=AMC[amc], ia=0.1)
        assert result.cn == 72.0 and result.amc == amc
        assert result.cn_adjusted == expected.cn_used
        assert result.peak_discharge_m3s == pytest.approx(expected.peak_discharge_m3s)
        assert [n.code for n in notices] == ["ia_coefficient_nonstandard"]

    def test_watershed_supplies_area_cn_and_kirpich_tc(self):
        """Default tc of a watershed: Kirpich from its channel/slope data."""
        result, _ = unwrap(ops.hydrograph_generate(watershed=WATERSHED, **STORM))
        tc = WatershedParameters.from_dict(WATERSHED).calculate_tc(method="kirpich")
        expected = library_run(area=45.3, cn=72, tc=tc)
        assert result.tc_min == pytest.approx(tc)
        assert result.tc_method == "kirpich"
        assert result.area_km2 == 45.3 and result.cn == 72.0
        assert result.watershed_name == "Potok Młynówka"
        assert result.peak_discharge_m3s == pytest.approx(expected.peak_discharge_m3s)

    @pytest.mark.parametrize("method", ["nrcs", "giandotti"])
    def test_tc_method_is_applied_to_the_watershed(self, method):
        """``tc_method`` selects the formula used on the watershed."""
        result, _ = unwrap(
            ops.hydrograph_generate(watershed=WATERSHED, tc_method=method, **STORM)
        )
        tc = quietly(WatershedParameters.from_dict(WATERSHED).calculate_tc, method)
        assert result.tc_min == pytest.approx(tc)
        assert result.tc_method == method

    def test_cn_next_to_a_watershed_overrides_its_cn(self):
        """A given ``cn`` wins over the watershed value."""
        result, _ = unwrap(
            ops.hydrograph_generate(watershed=WATERSHED, cn=85, tc_min=90.0, **STORM)
        )
        expected = library_run(area=45.3, cn=85, tc=90.0)
        assert result.cn == 85.0
        assert result.peak_discharge_m3s == pytest.approx(expected.peak_discharge_m3s)

    def test_cn_override_reaches_the_nrcs_time_of_concentration(self):
        """The CN next to a watershed is the CN of the whole computation.

        Watershed with CN 60 in the file (L = 12 km, S = 0.025), ``cn=85`` given,
        beta storm of 50 mm in 120 min. The NRCS lag equation took the retention of
        the CN of the file (S = 169.3 mm) while the runoff used CN 85: tc = 657.7 min,
        Qmax = 27.64 m3/s at 440 min. With the CN of the computation (S = 44.8 mm)
        tc = 322.1 min, Qmax = 55.62 m3/s at 240 min (twice the peak).
        """
        data = {**OVERRIDE_WATERSHED, "cn": 60}
        result, _ = unwrap(
            ops.hydrograph_generate(
                watershed=data, cn=85, tc_method="nrcs", **OVERRIDE_STORM
            )
        )
        assert result.cn == 85.0
        assert result.tc_min == pytest.approx(322.09, abs=0.01)
        assert result.peak_discharge_m3s == pytest.approx(55.625, abs=0.005)
        assert result.time_to_peak_min == 240.0

        # what the computation did before: tc of the CN of the file, runoff of CN 85
        tc_of_the_file = WatershedParameters.from_dict(data).calculate_tc("nrcs")
        before, _ = unwrap(
            ops.hydrograph_generate(
                watershed=data, cn=85, tc_min=tc_of_the_file, **OVERRIDE_STORM
            )
        )
        assert before.tc_min == pytest.approx(657.73, abs=0.01)
        assert before.peak_discharge_m3s == pytest.approx(27.637, abs=0.005)
        assert before.time_to_peak_min == 440.0

        # the override acts as if the CN were written into the watershed
        written, _ = unwrap(
            ops.hydrograph_generate(
                watershed={**data, "cn": 85}, tc_method="nrcs", **OVERRIDE_STORM
            )
        )
        assert result.tc_min == pytest.approx(written.tc_min, rel=1e-12)
        assert_arrays(result.discharge_m3s, written.discharge_m3s)

    def test_cn_override_is_what_the_run_and_its_tc_inputs_report(self):
        """``tc_parameters`` and the watershed of the run carry the CN used."""
        run = compute_hydrograph(
            watershed={**OVERRIDE_WATERSHED, "cn": 60},
            cn=85,
            tc_method="nrcs",
            **OVERRIDE_STORM,
        )
        assert run.cn == 85.0
        assert run.tc_parameters["cn"] == 85.0
        assert run.watershed.cn == 85

    def test_cn_override_gives_nrcs_the_cn_a_watershed_lacks(self):
        """No ``cn`` in the file and ``cn`` given: NRCS works (it was "missing: cn")."""
        result, _ = unwrap(
            ops.hydrograph_generate(
                watershed=OVERRIDE_WATERSHED, cn=85, tc_method="nrcs", **OVERRIDE_STORM
            )
        )
        assert result.tc_min == pytest.approx(322.09, abs=0.01)
        assert result.peak_discharge_m3s == pytest.approx(55.625, abs=0.005)
        with pytest.raises(InvalidParameterError) as caught:
            ops.hydrograph_generate(
                watershed=OVERRIDE_WATERSHED, tc_method="nrcs", **OVERRIDE_STORM
            )
        assert caught.value.details["option"] == "cn"
        assert caught.value.details["reason"] == "required"

    def test_a_watershed_cn_is_used_without_an_override(self):
        """Without ``cn`` the watershed value is the CN of runoff and of tc."""
        data = {**OVERRIDE_WATERSHED, "cn": 72}
        run = compute_hydrograph(watershed=data, tc_method="nrcs", **OVERRIDE_STORM)
        assert run.cn == 72.0 and run.tc_parameters["cn"] == 72.0
        assert run.tc_min == pytest.approx(
            WatershedParameters.from_dict(data).calculate_tc("nrcs")
        )

    def test_snyder_hydrograph_uses_the_unit_hydrograph_of_the_time_step(self):
        """Snyder (1938): the unit hydrograph of D = the 5-minute step, not of tD.

        Review case (45 km2, L = 12 km, Lc = 6 km, CN 72, beta 50 mm / 120 min): the
        unit hydrograph had tp = 354.2 min and qp = 1.379 m3/s/mm and the hydrograph
        Qmax = 9.76 m3/s at 405 min (the values for the standard duration tD = 59 min).
        For D = 5 min: tp = 313.7 min, qp = 1.542 m3/s/mm, Qmax = 10.90 m3/s at 365 min.
        """
        result, _ = unwrap(
            ops.hydrograph_generate(
                area_km2=45.0,
                cn=72,
                hietogram_type="beta",
                total_mm=50.0,
                duration_min=120.0,
                timestep_min=5.0,
                uh_model="snyder",
                snyder_length_km=12.0,
                snyder_centroid_length_km=6.0,
            )
        )
        assert result.uh_time_to_peak_min == pytest.approx(313.66, abs=0.01)
        assert result.uh_peak_discharge_m3s_per_mm == pytest.approx(1.5424, abs=1e-4)
        assert result.peak_discharge_m3s == pytest.approx(10.9023, abs=1e-4)
        assert result.time_to_peak_min == 365.0

    def test_watershed_file(self, tmp_path):
        """A ``WatershedParameters`` JSON file works like the inline object."""
        path = tmp_path / "zlewnia.json"
        path.write_text(
            WatershedParameters.from_dict(WATERSHED).to_json(), encoding="utf-8"
        )
        from_file, _ = unwrap(
            ops.hydrograph_generate(watershed_file=str(path), **STORM)
        )
        inline, _ = unwrap(ops.hydrograph_generate(watershed=WATERSHED, **STORM))
        assert_arrays(from_file.discharge_m3s, inline.discharge_m3s)
        with pytest.raises(NotFoundError):
            ops.hydrograph_generate(watershed_file=str(tmp_path / "brak.json"), **STORM)

    def test_library_range_warnings_become_notices(self):
        """A tc formula outside its range warns; the hydrograph is still computed."""
        long_river = {
            **WATERSHED,
            "channel_length_km": 120.0,
            "channel_slope_m_per_m": 0.0005,
        }
        result, notices = unwrap(ops.hydrograph_generate(watershed=long_river, **STORM))
        assert result.tc_method == "kirpich"
        assert [(n.level, n.code) for n in notices] == [
            ("warning", "user_warning"),
            ("warning", "user_warning"),
        ]
        assert "kirpich: length_km=120.0" in notices[0].text

    def test_duration_not_covered_is_reported(self):
        """The truncated hyetograph is flagged exactly like ``precip hietogram``."""
        _, notices = unwrap(
            ops.hydrograph_generate(
                area_km2=45.3,
                cn=72,
                tc_min=90.0,
                hietogram_type="block",
                total_mm=30.0,
                duration_min=100.0,
                timestep_min=30.0,
            )
        )
        assert [n.code for n in notices] == ["duration_not_covered"]

    def test_tc_that_the_model_does_not_use_is_reported(self):
        """Nash and Snyder ignore tc; the notice says so instead of hiding it."""
        result, notices = unwrap(
            ops.hydrograph_generate(
                area_km2=45.0,
                cn=72,
                tc_min=100.0,
                uh_model="nash",
                nash_n=3.0,
                nash_k_min=40.0,
                **STORM,
            )
        )
        assert result.tc_min == 100.0
        assert [n.code for n in notices] == ["tc_not_used"]
        expected = library_run(
            area=45.0,
            tc=None,
            model="nash",
            params={"n": 3.0, "k": 40.0, "k_unit": "min"},
        )
        assert result.peak_discharge_m3s == pytest.approx(expected.peak_discharge_m3s)

    @pytest.mark.parametrize(
        "arguments, option, reason",
        [
            # catchment source
            ({"area_km2": 45.3, **STORM}, "area_km2", "one_of"),
            ({"cn": 72, **STORM}, "cn", "one_of"),
            ({}, "watershed", "one_of"),
            (
                {"watershed": WATERSHED, "watershed_file": "x.json", **STORM},
                "watershed",
                "one_of",
            ),
            (
                {"watershed": WATERSHED, "area_km2": 10.0, **STORM},
                "area_km2",
                "not_applicable",
            ),
            (
                {"watershed": without(WATERSHED, "cn"), "tc_min": 90.0, **STORM},
                "cn",
                "required",
            ),
            # time of concentration
            ({"area_km2": 45.3, "cn": 72, **STORM}, "tc_min", "required"),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    "tc_method": "nrcs",
                    **STORM,
                },
                "tc_method",
                "not_applicable",
            ),
            (
                {"watershed": WATERSHED, "tc_min": 90.0, "tc_method": "nrcs", **STORM},
                "tc_method",
                "conflict",
            ),
            (
                {"watershed": WATERSHED, "tc_method": "faa", **STORM},
                "watershed",
                "missing_field",
            ),
            (
                {"watershed": WATERSHED, "tc_method": "bogus", **STORM},
                "tc_method",
                "choice",
            ),
            # precipitation source
            ({"area_km2": 45.3, "cn": 72, "tc_min": 90.0}, "hietogram_type", "one_of"),
            (
                {"area_km2": 45.3, "cn": 72, "tc_min": 90.0, "total_mm": 50.0},
                "total_mm",
                "one_of",
            ),
            (
                {"area_km2": 45.3, "cn": 72, "tc_min": 90.0, "values": SERIES, **STORM},
                "hietogram_type",
                "one_of",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    "values": SERIES,
                    "alpha": 2.0,
                },
                "alpha",
                "not_applicable",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    "values": SERIES,
                    "value_column": "P",
                },
                "value_column",
                "not_applicable",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    **STORM,
                    "peak_position": 0.4,
                },
                "peak_position",
                "not_applicable",
            ),
            (
                {"area_km2": 45.3, "cn": 72, "tc_min": 90.0, "values": [1.0, -1.0]},
                "values",
                "negative_value",
            ),
            # unit hydrograph model
            (
                {"area_km2": 45.3, "cn": 72, "tc_min": 90.0, "nash_n": 3.0, **STORM},
                "nash_n",
                "not_applicable",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    "uh_model": "nash",
                    **STORM,
                },
                "nash_n",
                "required",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    "uh_model": "nash",
                    "nash_n": 3.0,
                    **STORM,
                },
                "nash_k_min",
                "required",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    "uh_model": "nash",
                    "nash_n": 3.0,
                    "nash_k_min": 40.0,
                    "snyder_cp": 0.6,
                    **STORM,
                },
                "snyder_cp",
                "not_applicable",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    "uh_model": "clark",
                    **STORM,
                },
                "clark_r_min",
                "one_of",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    "uh_model": "clark",
                    "clark_r_min": 60.0,
                    "clark_r_tc_ratio": 0.5,
                    **STORM,
                },
                "clark_r_min",
                "one_of",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "uh_model": "snyder",
                    "snyder_length_km": 15.0,
                    **STORM,
                },
                "snyder_centroid_length_km",
                "required",
            ),
            (
                {
                    "area_km2": 45.3,
                    "cn": 72,
                    "tc_min": 90.0,
                    "uh_model": "huff",
                    **STORM,
                },
                "uh_model",
                "choice",
            ),
            (
                {"area_km2": 45.3, "cn": 72, "tc_min": 90.0, "amc": "IV", **STORM},
                "amc",
                "choice",
            ),
        ],
    )
    def test_invalid_inputs(self, arguments, option, reason):
        """Each wrong combination names the offending option and the reason."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.hydrograph_generate(**arguments)
        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason

    def test_missing_tc_fields_are_listed(self):
        """A watershed with a channel only cannot use the FAA method: it needs the
        overland flow path and the runoff coefficient."""
        with pytest.raises(InvalidParameterError) as caught:
            ops.hydrograph_generate(watershed=WATERSHED, tc_method="faa", **STORM)
        assert caught.value.details["missing"] == [
            "runoff_coeff",
            "overland_length_km",
            "overland_slope_m_per_m",
        ]

    def test_model_parameter_ranges_are_validated_by_the_library(self):
        """A non-positive Nash ``n`` is the library's validation error."""
        with pytest.raises(InvalidParameterError):
            ops.hydrograph_generate(
                area_km2=45.0,
                cn=72,
                uh_model="nash",
                nash_n=-1.0,
                nash_k_min=40.0,
                **STORM,
            )

    def test_compute_hydrograph_returns_the_whole_run(self):
        """The run keeps the library objects and everything it was built from."""
        run = compute_hydrograph(
            watershed=WATERSHED, tc_method="nrcs", amc="III", **STORM
        )
        tc = WatershedParameters.from_dict(WATERSHED).calculate_tc(method="nrcs")
        assert run.tc_min == pytest.approx(tc) and run.tc_method == "nrcs"
        # NRCS takes the average land slope of the watershed (0.025), not the slope
        # of the channel (0.018)
        assert run.tc_parameters == pytest.approx(
            {"length_km": 10.8, "slope_m_per_m": 0.025, "cn": 72.0}
        )
        assert (run.area_km2, run.cn, run.amc, run.ia_coefficient) == (
            45.3,
            72.0,
            "III",
            0.2,
        )
        assert run.uh_model == "scs" and run.uh_params == {}
        assert run.hietogram_type == "beta"
        assert run.watershed.name == "Potok Młynówka"
        assert isinstance(run.hietogram, HietogramResult)
        assert run.hietogram.total_mm == 50.0
        expected = library_run(area=45.3, cn=72, tc=tc, amc=AMC.III)
        assert run.result.peak_discharge_m3s == pytest.approx(
            expected.peak_discharge_m3s
        )
        assert run.notices == []

    def test_compute_hydrograph_builds_a_hietogram_from_a_series(self):
        """For a series the run carries an equivalent ``HietogramResult``."""
        run = compute_hydrograph(
            area_km2=45.0,
            cn=72,
            values=SERIES,
            timestep_min=10.0,
            uh_model="nash",
            nash_n=3.0,
            nash_k_min=48.0,
        )
        assert (
            run.hietogram_type is None and run.tc_min is None and run.watershed is None
        )
        assert run.tc_parameters is None
        assert run.uh_params == {"n": 3.0, "k": 48.0, "k_unit": "min"}
        assert_arrays(run.hietogram.intensities_mm, SERIES)
        assert_arrays(run.hietogram.times_min, [10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
        assert (run.hietogram.timestep_min, run.hietogram.duration_min) == (10.0, 60.0)
        assert run.hietogram.total_mm == pytest.approx(sum(SERIES))

    def test_run_command_envelope(self):
        """End to end: strict JSON with the series and the catalog defaults."""
        example = get_command("hydrograph generate").examples[0]
        envelope = run_command("hydrograph generate", example)
        document = json.loads(envelope.to_json())
        result = document["result"]
        assert document["inputs"]["amc"] == "II"
        assert document["inputs"]["uh_model"] == "scs"
        assert result["tc_method"] == "kirpich"
        assert len(result["times_min"]) == len(result["discharge_m3s"])
        assert max(result["discharge_m3s"]) == pytest.approx(
            result["peak_discharge_m3s"]
        )
        assert envelope.notices == ()

    def test_run_command_rejects_a_watershed_and_area_together(self):
        """The catalog ``one_of`` refuses two complete catchment sources."""
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "hydrograph generate",
                {
                    "watershed": WATERSHED,
                    "area_km2": 10,
                    "cn": 70,
                    "tc_min": 60,
                    **STORM,
                },
            )
        assert caught.value.details["reason"] == "one_of"


# --- declarations ---------------------------------------------------------------------


def _my_commands():
    return [c for c in data_commands() if c.group in RUNOFF_GROUPS]


class TestDeclarations:
    """The catalog declarations agree with the library and with the operations."""

    def test_the_six_groups_are_in_the_catalog(self):
        names = {c.name for c in _my_commands()}
        assert names == {
            "tc kirpich",
            "tc nrcs",
            "tc giandotti",
            "tc faa",
            "tc kerby",
            "tc kerby-kirpich",
            "tc watershed",
            "cn lookup",
            "cn list",
            "cn range",
            "cn weighted",
            "scs effective",
            "precip hietogram",
            "precip areal",
            "uh scs",
            "uh nash",
            "uh clark",
            "uh snyder",
            "hydrograph generate",
        }

    @pytest.mark.parametrize("command", _my_commands(), ids=lambda c: c.name)
    def test_every_example_runs_and_serializes(self, command):
        """Examples are not just valid: they run and give strict JSON."""
        for example in command.examples:
            envelope = run_command(command, example)
            document = json.loads(envelope.to_json())
            assert document["status"] == "ok"
            assert document["command"] == command.name
            for key in example:
                assert key in document["inputs"]

    @pytest.mark.parametrize("command", _my_commands(), ids=lambda c: c.name)
    def test_python_defaults_equal_catalog_defaults(self, command):
        """An option default is the default of the operation parameter."""
        function = getattr(ops, command.function.split(":")[1])
        parameters = inspect.signature(function).parameters
        for option in command.options:
            default = parameters[option.name].default
            if option.default is not None:
                assert default == option.default, option.name
            elif not option.required:
                assert default is None, option.name

    def test_declared_choices_equal_the_library(self):
        """Choices typed into the declarations match the enums they mirror."""
        assert tuple(cover.value for cover in LandCover) == LAND_COVERS
        assert tuple(c.value for c in HydrologicCondition) == CONDITIONS
        assert HSG_GROUPS == ("A", "B", "C", "D")
        assert tuple(a.name for a in AMC) == AMC_CLASSES
        assert set(UH_MODELS) == set(HydrographGenerator.SUPPORTED_MODELS)
        lookup = get_command("cn lookup")
        assert lookup.option("land_cover").choices == LAND_COVERS
        assert lookup.option("condition").choices == CONDITIONS
        assert lookup.option("hsg").choices == HSG_GROUPS
        assert get_command("cn range").option("land_cover").choices == LAND_COVERS
        assert get_command("scs effective").option("amc").choices == AMC_CLASSES
        generate = get_command("hydrograph generate")
        assert generate.option("amc").choices == AMC_CLASSES
        assert generate.option("uh_model").choices == UH_MODELS
        assert generate.option("tc_method").choices == TC_METHODS
        assert generate.option("hietogram_type").choices == HIETOGRAM_TYPES
        assert get_command("tc watershed").option("method").choices == TC_METHODS
        assert get_command("precip areal").option("method").choices == AREAL_METHODS

    def test_every_tc_method_is_accepted_by_the_library(self):
        """The choice list is exactly what ``calculate_tc`` supports."""
        watershed = WatershedParameters.from_dict(FULL_WATERSHED)
        for method in TC_METHODS:
            assert quietly(watershed.calculate_tc, method=method) > 0
        with pytest.raises(ValueError):
            watershed.calculate_tc(method="bogus")

    def test_generate_options_are_the_signature_of_both_functions(self):
        """``report generate`` builds on these options and on ``compute_hydrograph``."""
        names = [option.name for option in GENERATE_OPTIONS]
        assert list(inspect.signature(ops.hydrograph_generate).parameters) == names
        assert list(inspect.signature(compute_hydrograph).parameters) == names
        command = get_command("hydrograph generate")
        assert command.options == GENERATE_OPTIONS
        assert command.one_of == GENERATE_ONE_OF
        assert not command.writes


# --- shared helpers -------------------------------------------------------------------


class TestSelectGroup:
    """``select_group``: the operation-level counterpart of the catalog ``one_of``."""

    GROUPS = {"a": ("x", "y"), "b": ("z",)}

    def test_complete_group_is_chosen(self):
        assert select_group({"x": 1, "y": 2, "z": None}, self.GROUPS) == "a"
        assert select_group({"x": None, "y": None, "z": 0}, self.GROUPS) == "b"

    def test_partial_group_is_not_complete(self):
        with pytest.raises(InvalidParameterError) as caught:
            select_group({"x": 1, "y": None, "z": None}, self.GROUPS)
        assert caught.value.details["reason"] == "one_of"
        assert caught.value.details["given"] == ["x"]

    def test_two_complete_groups_are_ambiguous(self):
        with pytest.raises(InvalidParameterError) as caught:
            select_group({"x": 1, "y": 2, "z": 3}, self.GROUPS)
        assert caught.value.details["reason"] == "one_of"

    def test_extra_option_may_accompany_its_group_only(self):
        values = {"x": 1, "y": 2, "z": None, "w": 5}
        assert select_group(values, self.GROUPS, extra={"w": "a"}) == "a"
        with pytest.raises(InvalidParameterError) as caught:
            select_group(
                {"x": None, "y": None, "z": 1, "w": 5}, self.GROUPS, extra={"w": "a"}
            )
        assert caught.value.details == {
            "option": "w",
            "reason": "not_applicable",
        }

    def test_extra_option_for_several_groups(self):
        for given in ({"x": 1, "y": 2, "z": None}, {"x": None, "y": None, "z": 1}):
            assert (
                select_group({**given, "w": 5}, self.GROUPS, extra={"w": ("a", "b")})
                in "ab"
            )

    def test_check_choice_reports_the_allowed_values(self):
        assert check_choice("amc", "II", AMC_CLASSES) == "II"
        with pytest.raises(InvalidParameterError) as caught:
            check_choice("amc", 2, AMC_CLASSES)
        assert caught.value.details == {
            "option": "amc",
            "reason": "choice",
            "allowed": ["I", "II", "III"],
            "value": 2,
        }
