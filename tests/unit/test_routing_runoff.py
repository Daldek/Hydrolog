"""Tests of the curve-number runoff model: ``HydrographGenerator`` with a document.

The reference is the generator itself: for every unit hydrograph model the hydrograph of
the model is the one that ``HydrographGenerator(...).generate(rain)`` gives, to the last
ordinate, and the time of concentration of a formula is the one of the watershed. What
the model refuses is refused before anything is computed, with the reasons of the
options of ``hydrograph generate``; a document says what the object says.
"""

import warnings

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import WatershedParameters
from hydrolog.precipitation import BetaHietogram, HietogramResult
from hydrolog.routing import RUNOFF_MODELS, CurveNumberRunoff, Hydrograph, RunoffModel
from hydrolog.routing.runoff import runoff_from_document, watershed_from_document
from hydrolog.runoff import AMC, HydrographGenerator

from ._routing_extensions import Share

WATERSHED = WatershedParameters(
    area_km2=12.0,
    perimeter_km=18.0,
    length_km=6.0,
    elevation_min_m=210.0,
    elevation_max_m=330.0,
    cn=75,
    channel_length_km=5.0,
    channel_slope_m_per_m=0.012,
    mean_slope_m_per_m=0.03,
)
RAIN = BetaHietogram().generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)
KIRPICH = WATERSHED.calculate_tc("kirpich")


def refused(build) -> InvalidParameterError:
    with pytest.raises(InvalidParameterError) as caught:
        build()
    return caught.value


CASES = {
    "scs, tc given": (
        {"tc_min": 90.0},
        {"tc_min": 90.0},
        AMC.II,
    ),
    "scs, tc by the default formula": (
        {},
        {"tc_min": KIRPICH},
        AMC.II,
    ),
    "scs, tc by nrcs": (
        {"tc_method": "nrcs"},
        {"tc_min": WATERSHED.calculate_tc("nrcs")},
        AMC.II,
    ),
    "scs, dry, a low initial abstraction": (
        {"tc_min": 90.0, "amc": "I", "ia_coefficient": 0.05},
        {"tc_min": 90.0, "ia_coefficient": 0.05},
        AMC.I,
    ),
    "scs, wet": ({"tc_min": 40.0, "amc": "III"}, {"tc_min": 40.0}, AMC.III),
    "nash": (
        {"uh_model": "nash", "nash_n": 3.0, "nash_k_min": 48.0},
        {"uh_model": "nash", "uh_params": {"n": 3.0, "k": 48.0, "k_unit": "min"}},
        AMC.II,
    ),
    "clark, R given": (
        {"uh_model": "clark", "tc_min": 60.0, "clark_r_min": 40.0},
        {"uh_model": "clark", "tc_min": 60.0, "uh_params": {"r": 40.0}},
        AMC.II,
    ),
    "clark, R from the ratio to tc": (
        {"uh_model": "clark", "tc_min": 60.0, "clark_r_tc_ratio": 0.5},
        {"uh_model": "clark", "tc_min": 60.0, "uh_params": {"r": 30.0}},
        AMC.II,
    ),
    "clark, tc by a formula": (
        {"uh_model": "clark", "clark_r_tc_ratio": 0.5},
        {"uh_model": "clark", "tc_min": KIRPICH, "uh_params": {"r": 0.5 * KIRPICH}},
        AMC.II,
    ),
    "snyder": (
        {
            "uh_model": "snyder",
            "snyder_length_km": 15.0,
            "snyder_centroid_length_km": 8.0,
        },
        {
            "uh_model": "snyder",
            "uh_params": {"L_km": 15.0, "Lc_km": 8.0, "ct": 1.5, "cp": 0.6},
        },
        AMC.II,
    ),
    "snyder, its coefficients": (
        {
            "uh_model": "snyder",
            "snyder_length_km": 15.0,
            "snyder_centroid_length_km": 8.0,
            "snyder_ct": 1.8,
            "snyder_cp": 0.7,
        },
        {
            "uh_model": "snyder",
            "uh_params": {"L_km": 15.0, "Lc_km": 8.0, "ct": 1.8, "cp": 0.7},
        },
        AMC.II,
    ),
}


class TestItIsTheGenerator:
    @pytest.mark.parametrize("case", CASES)
    def test_the_hydrograph_is_the_one_of_the_generator_to_the_last_ordinate(
        self, case
    ):
        fields, generated, moisture = CASES[case]

        flood = CurveNumberRunoff(**fields).hydrograph(RAIN, WATERSHED, 5.0)

        expected = HydrographGenerator(area_km2=12.0, cn=75, **generated).generate(
            RAIN, amc=moisture
        )
        assert isinstance(flood, Hydrograph)
        np.testing.assert_array_equal(
            flood.discharge_m3s, expected.hydrograph.discharge_m3s
        )
        np.testing.assert_array_equal(flood.times_min, expected.hydrograph.times_min)
        assert flood.start_min == 0.0 and flood.timestep_min == 5.0

    def test_the_rain_must_be_at_the_step_of_the_network(self):
        error = refused(
            lambda: CurveNumberRunoff(tc_min=90.0).hydrograph(RAIN, WATERSHED, 10.0)
        )

        assert error.details["reason"] == "timestep_mismatch"
        assert error.details["expected"] == 10.0 and error.details["value"] == 5.0

    def test_a_model_has_the_protocol_and_a_name(self):
        model = CurveNumberRunoff(tc_min=90.0)

        assert isinstance(model, RunoffModel) and model.model == "curve-number"
        assert RUNOFF_MODELS["curve-number"] is CurveNumberRunoff
        assert not isinstance(object(), RunoffModel)


class TestWhatItRefuses:
    @pytest.mark.parametrize(
        ("fields", "option", "reason"),
        [
            ({"uh_model": "gamma"}, "uh_model", "choice"),
            ({"amc": "IV"}, "amc", "choice"),
            ({"tc_method": "rule-of-thumb"}, "tc_method", "choice"),
            ({"tc_min": 0.0}, "tc_min", "exclusive_minimum"),
            ({"tc_min": "long"}, "tc_min", "type"),
            ({"ia_coefficient": 0.0}, "ia_coefficient", "exclusive_minimum"),
            ({"ia_coefficient": 1.5}, "ia_coefficient", "maximum"),
            ({"tc_min": 10.0, "tc_method": "kirpich"}, "tc_method", "conflict"),
            (
                {"uh_model": "nash", "nash_n": 3.0},
                "nash_k_min",
                "required",
            ),
            (
                {"uh_model": "nash", "nash_n": 3.0, "nash_k_min": -1.0},
                "nash_k_min",
                "exclusive_minimum",
            ),
            (
                {"uh_model": "nash", "nash_n": 3.0, "nash_k_min": 50.0, "tc_min": 60.0},
                "tc_min",
                "not_applicable",
            ),
            (
                {"uh_model": "snyder", "snyder_length_km": 9.0},
                "snyder_centroid_length_km",
                "required",
            ),
            ({"tc_min": 60.0, "nash_n": 3.0}, "nash_n", "not_applicable"),
            ({"tc_min": 60.0, "snyder_ct": 1.5}, "snyder_ct", "not_applicable"),
            (
                {"uh_model": "clark", "tc_min": 60.0},
                "clark_r_min",
                "one_of",
            ),
            (
                {
                    "uh_model": "clark",
                    "tc_min": 60.0,
                    "clark_r_min": 20.0,
                    "clark_r_tc_ratio": 0.5,
                },
                "clark_r_tc_ratio",
                "one_of",
            ),
        ],
    )
    def test_an_option_that_is_not_valid_is_refused_with_the_reason_of_the_command(
        self, fields, option, reason
    ):
        error = refused(lambda: CurveNumberRunoff(**fields))

        assert (error.details["option"], error.details["reason"]) == (option, reason)

    def test_a_watershed_without_a_curve_number_is_refused(self):
        bare = WatershedParameters(
            area_km2=12.0,
            perimeter_km=18.0,
            length_km=6.0,
            elevation_min_m=210.0,
            elevation_max_m=330.0,
        )

        error = refused(lambda: CurveNumberRunoff(tc_min=90.0).validate(bare))

        assert (error.details["reason"], error.details["field"]) == (
            "missing_field",
            "cn",
        )
        assert "cn" in str(error.hint)

    def test_a_curve_number_below_one_is_refused_before_the_run(self):
        wet = WatershedParameters(
            area_km2=12.0,
            perimeter_km=18.0,
            length_km=6.0,
            elevation_min_m=210.0,
            elevation_max_m=330.0,
            cn=0,
        )

        error = refused(lambda: CurveNumberRunoff(tc_min=90.0).validate(wet))

        assert (error.details["reason"], error.details["field"]) == ("minimum", "cn")

    def test_a_formula_that_the_watershed_cannot_feed_is_refused_naming_what_it_lacks(
        self,
    ):
        error = refused(
            lambda: CurveNumberRunoff(tc_method="kerby").validate(WATERSHED)
        )

        assert error.details["reason"] == "missing_field"
        assert error.details["missing"] == [
            "retardance",
            "overland_length_km",
            "overland_slope_m_per_m",
        ]

    def test_a_given_time_of_concentration_needs_no_formula_data(self):
        CurveNumberRunoff(tc_min=90.0).validate(WATERSHED)
        CurveNumberRunoff(uh_model="nash", nash_n=3.0, nash_k_min=48.0).validate(
            WATERSHED
        )

    def test_something_that_is_not_a_watershed_is_refused(self):
        error = refused(
            lambda: CurveNumberRunoff(tc_min=90.0).validate({"area_km2": 1})
        )

        assert (error.details["option"], error.details["reason"]) == (
            "watershed",
            "type",
        )


class TestWhatItUses:
    @staticmethod
    def listed(model, *arguments):
        return {p.name: p for p in model.describe(*arguments)}

    def test_the_options_are_given_or_default_before_anything_is_known(self):
        listed = self.listed(CurveNumberRunoff(tc_min=90.0, amc="III"))

        assert {name: (p.value, p.source) for name, p in listed.items()} == {
            "ia_coefficient": (0.2, "default"),
            "amc": ("III", "given"),
            "uh_model": ("scs", "default"),
            "tc_min": (90.0, "given"),
        }

    def test_what_the_watershed_gives_is_listed_with_units(self):
        listed = self.listed(CurveNumberRunoff(tc_min=90.0), WATERSHED)

        assert (listed["area_km2"].value, listed["area_km2"].unit) == (12.0, "km2")
        assert (listed["cn"].value, listed["cn"].source) == (75, "given")
        assert listed["retention_mm"].source == "computed"
        assert listed["retention_mm"].unit == "mm"
        assert listed["retention_mm"].value == pytest.approx(25400.0 / 75 - 254.0)
        assert listed["initial_abstraction_mm"].value == pytest.approx(
            0.2 * (25400.0 / 75 - 254.0)
        )
        assert "cn_adjusted" not in listed and "total_effective_mm" not in listed

    def test_a_time_of_concentration_from_a_formula_is_computed_and_its_formula_named(
        self,
    ):
        listed = self.listed(CurveNumberRunoff(), WATERSHED)
        chosen = self.listed(CurveNumberRunoff(tc_method="nrcs"), WATERSHED)

        assert (listed["tc_method"].value, listed["tc_method"].source) == (
            "kirpich",
            "default",
        )
        assert (listed["tc_min"].value, listed["tc_min"].source) == (
            KIRPICH,
            "computed",
        )
        assert listed["tc_min"].unit == "min"
        assert chosen["tc_method"].source == "given"
        assert chosen["tc_min"].value == WATERSHED.calculate_tc("nrcs")

    def test_a_model_that_has_no_time_of_concentration_lists_none(self):
        listed = self.listed(
            CurveNumberRunoff(uh_model="nash", nash_n=3.0, nash_k_min=48.0), WATERSHED
        )

        assert "tc_min" not in listed and "tc_method" not in listed
        assert (listed["nash_k_min"].value, listed["nash_k_min"].unit) == (48.0, "min")

    def test_the_coefficients_of_snyder_are_default_and_the_ratio_of_clark_has_its_r(
        self,
    ):
        snyder = self.listed(
            CurveNumberRunoff(
                uh_model="snyder",
                snyder_length_km=15.0,
                snyder_centroid_length_km=8.0,
                snyder_cp=0.7,
            )
        )
        clark = self.listed(
            CurveNumberRunoff(uh_model="clark", clark_r_tc_ratio=0.5), WATERSHED
        )

        assert (snyder["snyder_ct"].value, snyder["snyder_ct"].source) == (
            1.5,
            "default",
        )
        assert (snyder["snyder_cp"].value, snyder["snyder_cp"].source) == (0.7, "given")
        assert (clark["clark_r_min"].value, clark["clark_r_min"].source) == (
            0.5 * KIRPICH,
            "computed",
        )

    def test_what_the_rain_gave_is_what_the_generator_reports(self):
        model = CurveNumberRunoff(tc_min=90.0, amc="III")
        listed = self.listed(model, WATERSHED, RAIN)

        reference = HydrographGenerator(area_km2=12.0, cn=75, tc_min=90.0).generate(
            RAIN, amc=AMC.III
        )
        assert listed["cn_adjusted"].value == reference.cn_used
        assert listed["retention_mm"].value == reference.retention_mm
        assert listed["initial_abstraction_mm"].value == (
            reference.initial_abstraction_mm
        )
        assert listed["total_effective_mm"].value == reference.total_effective_mm
        assert listed["runoff_coefficient"].value == reference.runoff_coefficient
        assert listed["runoff_coefficient"].unit is None

    def test_a_dry_spell_has_no_runoff_coefficient_to_divide(self):
        none = HietogramResult(
            times_min=np.array([5.0, 10.0]),
            intensities_mm=np.zeros(2),
            total_mm=0.0,
            duration_min=10.0,
            timestep_min=5.0,
        )

        listed = self.listed(CurveNumberRunoff(tc_min=90.0), WATERSHED, none)

        assert listed["total_effective_mm"].value == 0.0
        assert "runoff_coefficient" not in listed

    def test_describing_does_not_issue_the_warnings_of_the_formula_again(self):
        flat = WatershedParameters(
            area_km2=12.0,
            perimeter_km=18.0,
            length_km=12.0,
            elevation_min_m=210.0,
            elevation_max_m=220.0,
            cn=75,
        )
        model = CurveNumberRunoff()

        with pytest.warns(UserWarning, match="outside typical range"):
            model.hydrograph(RAIN, flat, 5.0)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            model.describe(flat, RAIN)


FIELDS = {"model": "curve-number", "tc_min": 90.0}


class TestTheDocument:
    def test_a_canonical_document_is_read_and_written_back_as_it_is(self):
        document = {
            "model": "curve-number",
            "tc_method": "nrcs",
            "ia_coefficient": 0.05,
            "amc": "III",
            "uh_model": "clark",
            "clark_r_tc_ratio": 0.5,
        }

        model = runoff_from_document(document)

        assert isinstance(model, CurveNumberRunoff)
        assert model.to_document() == document

    def test_a_default_is_left_out_and_an_object_equals_its_document(self):
        explicit = runoff_from_document(
            {
                "model": "curve-number",
                "tc_min": 90.0,
                "ia_coefficient": 0.2,
                "amc": "II",
                "uh_model": "scs",
            }
        )

        assert explicit.to_document() == FIELDS
        assert explicit == CurveNumberRunoff(tc_min=90.0)
        assert explicit != CurveNumberRunoff(tc_min=60.0)
        assert "tc_min=90.0" in repr(explicit)

    def test_the_hydrograph_of_a_document_is_the_one_of_the_generator(self):
        model = runoff_from_document(
            {
                "model": "curve-number",
                "uh_model": "nash",
                "nash_n": 3,
                "nash_k_min": 48,
                "amc": "III",
            }
        )

        flood = model.hydrograph(RAIN, WATERSHED, 5.0)

        expected = HydrographGenerator(
            area_km2=12.0,
            cn=75,
            uh_model="nash",
            uh_params={"n": 3.0, "k": 48.0, "k_unit": "min"},
        ).generate(RAIN, amc=AMC.III)
        np.testing.assert_array_equal(
            flood.discharge_m3s, expected.hydrograph.discharge_m3s
        )

    @pytest.mark.parametrize(
        ("document", "reason", "facts"),
        [
            ([FIELDS], "type", {}),
            ({}, "missing_field", {"field": "model"}),
            (
                {"model": "gr4j"},
                "unknown_model",
                {"field": "model", "value": "gr4j", "allowed": ["curve-number"]},
            ),
            ({**FIELDS, "color": 1}, "unknown_field", {"field": "color"}),
            ({**FIELDS, "tc_min": "long"}, "type", {"option": "tc_min"}),
            ({**FIELDS, "amc": "IV"}, "choice", {"option": "amc"}),
            ({**FIELDS, "nash_n": 3.0}, "not_applicable", {"option": "nash_n"}),
        ],
    )
    def test_a_document_that_is_wrong_says_what_and_where(
        self, document, reason, facts
    ):
        error = refused(lambda: runoff_from_document(document))

        assert error.details["reason"] == reason
        assert {key: error.details.get(key) for key in facts} == facts


COMPLETE = {
    "area_km2": 12.0,
    "perimeter_km": 18.0,
    "length_km": 6.0,
    "elevation_min_m": 210.0,
    "elevation_max_m": 330.0,
}


class TestTheWatershedDocument:
    def test_it_is_the_object_of_the_class(self):
        document = {**COMPLETE, "cn": 75, "name": "Upper", "channel_length_km": 5.0}

        watershed = watershed_from_document(document)

        assert watershed == WatershedParameters.from_dict(document)
        assert watershed.to_dict() == document

    @pytest.mark.parametrize(
        ("document", "reason", "facts"),
        [
            ("area", "type", {}),
            (
                {"area_km2": 12.0},
                "missing_field",
                {
                    "field": "perimeter_km",
                    "missing": [
                        "perimeter_km",
                        "length_km",
                        "elevation_min_m",
                        "elevation_max_m",
                    ],
                },
            ),
            ({**COMPLETE, "colour": "green"}, "unknown_field", {"field": "colour"}),
            ({**COMPLETE, "area_km2": "12"}, "type", {"field": "area_km2"}),
            ({**COMPLETE, "area_km2": True}, "type", {"field": "area_km2"}),
            ({**COMPLETE, "area_km2": float("inf")}, "type", {"field": "area_km2"}),
            ({**COMPLETE, "name": 12}, "type", {"field": "name"}),
        ],
    )
    def test_a_document_that_is_wrong_says_what_and_where(
        self, document, reason, facts
    ):
        error = refused(lambda: watershed_from_document(document))

        assert error.details["reason"] == reason
        assert {key: error.details.get(key) for key in facts} == facts

    def test_a_value_that_the_class_refuses_is_its_own_message(self):
        error = refused(
            lambda: watershed_from_document({**COMPLETE, "elevation_max_m": 100.0})
        )

        assert "must be greater than" in str(error)


class TestExtending:
    def test_a_new_model_is_a_registry_entry_and_nothing_else(self, monkeypatch):
        monkeypatch.setitem(RUNOFF_MODELS._classes, "share-of-rain", Share)

        model = runoff_from_document({"model": "share-of-rain", "share": 0.25})

        assert isinstance(model, Share) and isinstance(model, RunoffModel)
        assert runoff_from_document(model.to_document()).share == 0.25
        flood = model.hydrograph(RAIN, WATERSHED, 5.0)
        assert flood.volume_m3 == pytest.approx(
            0.25 * RAIN.total_mm / 1000.0 * 12.0e6, rel=0.05
        )

    def test_a_class_that_cannot_be_read_and_written_is_not_registered(self):
        class Unreadable:
            model = "unreadable"

        with pytest.raises(TypeError, match="no from_document, to_document"):
            RUNOFF_MODELS.register(Unreadable)
