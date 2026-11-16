"""Tests of Nash's n and K estimated by Lutz from the watershed (ADR-0024).

The reference is what the estimate replaces: ``uh nash`` by Lutz with the inputs the
method defines (L and J of the main stream from the divide: the longest flow path),
then ``hydrograph generate`` with the n and K it gave. ``hydrograph generate`` and
``report generate`` with ``nash_estimation`` do it in one run, and a subcatchment of
``hydrolog-network/1`` whose runoff says ``nash_estimation`` gives the command's
hydrograph. What the estimation cannot work with is refused with the reasons of
``tc_method``: the option where it is misplaced, the fields that the watershed lacks.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from hydrolog import command_schema, run_command
from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import WatershedParameters
from hydrolog.operations import compute_hydrograph, hydrograph_generate
from hydrolog.routing import CurveNumberRunoff, RoutingNetwork
from hydrolog.routing.runoff import runoff_from_document
from hydrolog.runoff import NashIUH

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
KAMIENNIK: dict[str, Any] = json.loads(
    (FIXTURES / "kamiennik.json").read_text(encoding="utf-8")
)
STORM = {"hietogram_type": "beta", "total_mm": 101.82, "duration_min": 720.0}
LUTZ = {"uh_model": "nash", "nash_estimation": "lutz"}
RUNOFF = {"model": "curve-number", **LUTZ}
# Lutz's inputs that the watershed lacks, in the order they are reported
NEEDED = ["flow_path_length_km", "Lc_km", "flow_path_slope_m_per_m", "manning_n"]


def refused(build) -> InvalidParameterError:
    with pytest.raises(InvalidParameterError) as caught:
        build()
    return caught.value


def generated(watershed: dict[str, Any], **options: Any) -> dict[str, Any]:
    """The envelope of ``hydrograph generate`` at a step of 10 min, as JSON."""
    return run_command(
        "hydrograph generate",
        watershed=watershed,
        timestep_min=10.0,
        **STORM,
        **options,
    ).to_dict()


def by_uh_nash(watershed: dict[str, Any], timestep_min: float) -> dict[str, float]:
    """n and K of ``uh nash`` by Lutz from the main stream from the divide."""
    options = {
        "area_km2": watershed["area_km2"],
        "lutz_length_km": watershed["flow_path_length_km"],
        "lutz_centroid_length_km": watershed["Lc_km"],
        "lutz_slope_m_per_m": watershed["flow_path_slope_m_per_m"],
        "lutz_manning_n": watershed["manning_n"],
        "timestep_min": timestep_min,
    }
    for share in ("urban_pct", "forest_pct"):
        if share in watershed:
            options[f"lutz_{share}"] = watershed[share]
    parameters: dict[str, float] = run_command("uh nash", **options).to_dict()[
        "result"
    ]["parameters"]
    return parameters


def network(watershed: dict[str, Any], runoff: dict[str, Any]) -> dict[str, Any]:
    """One subcatchment under the storm of the network, at 10 min, and the outlet."""
    return {
        "schema": "hydrolog-network/1",
        "timestep_min": 10.0,
        "rainfall": {"kind": "design", **STORM},
        "nodes": [
            {
                "id": "Z1",
                "type": "subcatchment",
                "watershed": watershed,
                "runoff": runoff,
            },
            {"id": "OUT", "type": "outlet", "from": ["Z1"]},
        ],
    }


class TestTheFieldsOfTheWatershed:
    def test_l_and_j_are_those_of_the_main_stream_from_the_divide(self):
        parameters = WatershedParameters.from_dict(KAMIENNIK).nash_parameters("lutz")

        # the channel (14.78 km at 0.0142) ends at the channel head: not Lutz's L, J
        assert parameters == {
            "L_km": 15.88,
            "Lc_km": 6.76,
            "slope": 0.0114,
            "manning_n": 0.035,
            "urban_pct": 1.0,
            "forest_pct": 57.4,
            "area_km2": 37.22,
        }

    def test_the_urban_and_forest_shares_are_zero_when_the_watershed_has_none(self):
        bare = {
            key: value
            for key, value in KAMIENNIK.items()
            if key not in ("urban_pct", "forest_pct")
        }

        parameters = WatershedParameters.from_dict(bare).nash_parameters()

        assert (parameters["urban_pct"], parameters["forest_pct"]) == (0.0, 0.0)

    @pytest.mark.parametrize(
        "lacking",
        [
            NEEDED,
            ["Lc_km", "manning_n"],
            ["flow_path_slope_m_per_m"],
        ],
    )
    def test_a_field_that_lutz_needs_is_named_with_the_others_missing(self, lacking):
        # the channel's length and slope do not stand in for the flow path's
        watershed = WatershedParameters.from_dict(
            {key: value for key, value in KAMIENNIK.items() if key not in lacking}
        )

        error = refused(lambda: watershed.nash_parameters("lutz"))

        assert error.details["reason"] == "missing_field"
        assert error.details["option"] == lacking[0]
        assert error.details["missing"] == lacking
        assert error.details["method"] == "lutz"

    def test_a_centroid_beyond_the_main_stream_is_refused_on_lc(self):
        watershed = WatershedParameters.from_dict({**KAMIENNIK, "Lc_km": 16.0})

        error = refused(watershed.nash_parameters)

        assert {key: error.details[key] for key in ("option", "reason")} == {
            "option": "Lc_km",
            "reason": "maximum",
        }
        assert (error.details["maximum"], error.details["value"]) == (15.88, 16.0)

    def test_a_flat_main_stream_is_refused_on_its_slope(self):
        watershed = WatershedParameters.from_dict(
            {**KAMIENNIK, "flow_path_slope_m_per_m": 0.0}
        )

        error = refused(watershed.nash_parameters)

        assert (error.details["option"], error.details["reason"]) == (
            "flow_path_slope_m_per_m",
            "exclusive_minimum",
        )

    def test_an_unknown_estimation_is_a_choice(self):
        watershed = WatershedParameters.from_dict(KAMIENNIK)

        error = refused(lambda: watershed.nash_parameters("urban_regression"))

        assert (error.details["reason"], error.details["allowed"]) == (
            "choice",
            ["lutz"],
        )


class TestTheCommand:
    def test_one_run_gives_what_uh_nash_and_the_hydrograph_of_its_n_and_k_gave(self):
        parameters = by_uh_nash(KAMIENNIK, 10.0)

        one = generated(KAMIENNIK, **LUTZ)
        two = generated(
            KAMIENNIK,
            uh_model="nash",
            nash_n=parameters["n"],
            nash_k_min=parameters["k_min"],
        )

        result, reference = one["result"], two["result"]
        assert result["nash_estimation"] == "lutz"
        assert reference["nash_estimation"] is None
        assert result["uh_parameters"] == pytest.approx(parameters, rel=1e-12)
        np.testing.assert_allclose(
            result["discharge_m3s"], reference["discharge_m3s"], rtol=1e-9, atol=0
        )
        np.testing.assert_allclose(
            result["uh_discharge_m3s_per_mm"],
            reference["uh_discharge_m3s_per_mm"],
            rtol=1e-9,
            atol=0,
        )
        assert result["peak_discharge_m3s"] == pytest.approx(
            reference["peak_discharge_m3s"], rel=1e-9
        )
        assert result["time_to_peak_min"] == reference["time_to_peak_min"]

    def test_an_estimate_is_not_checked_against_the_ranges_of_given_n_and_k(self):
        # a small steep watershed: Lutz's K is below the range of a given K (10 min)
        small = {
            "area_km2": 1.0,
            "cn": 75,
            "flow_path_length_km": 1.0,
            "flow_path_slope_m_per_m": 0.1,
            "Lc_km": 0.5,
            "manning_n": 0.03,
        }
        parameters = by_uh_nash(small, 2.0)
        assert parameters["k_min"] < 10.0

        estimated = run_command(
            "hydrograph generate", watershed=small, timestep_min=2.0, **STORM, **LUTZ
        ).to_dict()
        given = run_command(
            "hydrograph generate",
            watershed=small,
            timestep_min=2.0,
            uh_model="nash",
            nash_n=parameters["n"],
            nash_k_min=parameters["k_min"],
            **STORM,
        ).to_dict()

        codes = [notice["code"] for notice in estimated["notices"]]
        assert "outside_unverified_range" not in codes
        assert "outside_unverified_range" in [n["code"] for n in given["notices"]]

    def test_a_watershed_larger_than_lutzs_is_a_notice_of_the_area(self):
        envelope = generated({**KAMIENNIK, "area_km2": 300.0}, **LUTZ)

        found = [
            notice["details"]
            for notice in envelope["notices"]
            if notice["code"] == "outside_typical_range"
        ]
        assert [(d["method"], d["parameter"], d["field"]) for d in found] == [
            ("lutz", "area_km2", "area_km2")
        ]

    def test_the_typical_ranges_it_serves_include_lutzs_area(self):
        for name in ("hydrograph generate", "report generate"):
            served = command_schema(name).to_dict()["commands"][0]["typical_ranges"]

            lutz = [found for found in served if found["method"] == "lutz"]
            assert [(r["parameter"], r["inputs"], r["maximum"]) for r in lutz] == [
                ("area_km2", ["area_km2"], 236.0)
            ]

    @pytest.mark.parametrize(
        ("options", "option", "reason"),
        [
            ({"uh_model": "scs", "nash_estimation": "lutz"}, "nash_estimation", None),
            ({**LUTZ, "nash_n": 3.0}, "nash_estimation", "conflict"),
            ({**LUTZ, "nash_k_min": 60.0}, "nash_estimation", "conflict"),
            ({"uh_model": "nash"}, "nash_n", "required"),
            ({"uh_model": "nash", "nash_k_min": 60.0}, "nash_n", "required"),
            ({"uh_model": "nash", "nash_n": 3.0}, "nash_k_min", "required"),
            ({**LUTZ, "nash_estimation": "urban"}, "nash_estimation", "choice"),
        ],
    )
    def test_a_misplaced_option_is_refused_with_the_reason_of_tc_method(
        self, options, option, reason
    ):
        error = refused(
            lambda: hydrograph_generate(watershed=KAMIENNIK, **STORM, **options)
        )

        assert error.details["option"] == option
        assert error.details["reason"] == (reason or "not_applicable")
        if option == "nash_n":
            assert "nash_estimation" in str(error.hint)

    def test_without_a_watershed_there_is_nothing_to_estimate_from(self):
        error = refused(
            lambda: hydrograph_generate(area_km2=37.22, cn=65, **STORM, **LUTZ)
        )

        assert (error.details["option"], error.details["reason"]) == (
            "nash_estimation",
            "not_applicable",
        )

    def test_a_watershed_without_lutzs_fields_is_refused_naming_them(self):
        lacking = {
            key: value
            for key, value in KAMIENNIK.items()
            if key not in ("Lc_km", "manning_n")
        }

        error = refused(lambda: hydrograph_generate(watershed=lacking, **STORM, **LUTZ))

        assert error.details["reason"] == "missing_field"
        assert (error.details["option"], error.details["missing"]) == (
            "Lc_km",
            ["Lc_km", "manning_n"],
        )
        assert error.details["method"] == "lutz"

    def test_the_run_keeps_the_steps_of_the_estimation_for_the_report(self):
        run = compute_hydrograph(watershed=KAMIENNIK, **STORM, **LUTZ)

        assert run.nash_estimation == "lutz" and run.lutz is not None
        cascade = NashIUH.from_lutz(
            **WatershedParameters.from_dict(KAMIENNIK).nash_parameters()
        )
        assert run.lutz == cascade.lutz_params
        assert (run.uh_params["n"], run.uh_params["k"]) == (cascade.n, cascade.k_min)


class TestTheReport:
    def test_the_unit_hydrograph_section_shows_the_steps_of_lutz(self, tmp_path):
        output = tmp_path / "raport.md"

        envelope = run_command(
            "report generate",
            output=str(output),
            watershed=KAMIENNIK,
            timestep_min=10.0,
            **STORM,
            **LUTZ,
        ).to_dict()

        text = output.read_text(encoding="utf-8")
        parameters = by_uh_nash(KAMIENNIK, 10.0)
        assert envelope["result"]["peak_discharge_m3s"] == pytest.approx(
            generated(KAMIENNIK, **LUTZ)["result"]["peak_discharge_m3s"], rel=1e-12
        )
        assert "**Dane wejściowe metody Lutza:**" in text
        assert "**Krok 1: Współczynnik P1**" in text
        assert "**Krok 6: Stała zbiornika K**" in text
        assert "$L$ = 15.880 km" in text and "$J_g$ = 0.0114" in text
        assert f"otrzymano: $n = {parameters['n']:.3f}$" in text
        assert f"= {parameters['k_min']:.1f} \\text{{ min}}$$" in text

    def test_given_n_and_k_have_no_steps_of_an_estimation(self, tmp_path):
        output = tmp_path / "raport.md"

        run_command(
            "report generate",
            output=str(output),
            watershed=KAMIENNIK,
            timestep_min=10.0,
            uh_model="nash",
            nash_n=3.0,
            nash_k_min=60.0,
            **STORM,
        )

        assert "Lutz" not in output.read_text(encoding="utf-8")


class TestTheNetwork:
    def test_the_node_gives_the_hydrograph_of_the_command(self):
        command = generated(KAMIENNIK, **LUTZ)["result"]

        routed = run_command("route network", network=network(KAMIENNIK, RUNOFF))

        node = routed.to_dict()["result"]["nodes"][0]
        np.testing.assert_allclose(
            node["discharge_m3s"], command["discharge_m3s"], rtol=1e-9, atol=0
        )
        assert node["parameters"]["nash_n"] == pytest.approx(
            command["uh_parameters"]["n"], rel=1e-12
        )
        assert node["parameters"]["nash_k_min"] == pytest.approx(
            command["uh_parameters"]["k_min"], rel=1e-12
        )

    def test_the_node_lists_the_estimation_as_given_and_n_and_k_as_computed(self):
        result = RoutingNetwork.from_document(network(KAMIENNIK, RUNOFF)).route()

        listed = {p.name: p for p in result.nodes["Z1"].parameters}

        assert (listed["nash_estimation"].value, listed["nash_estimation"].source) == (
            "lutz",
            "given",
        )
        cascade = NashIUH.from_lutz(
            **WatershedParameters.from_dict(KAMIENNIK).nash_parameters()
        )
        assert (listed["nash_n"].value, listed["nash_n"].source) == (
            cascade.n,
            "computed",
        )
        assert (listed["nash_k_min"].value, listed["nash_k_min"].unit) == (
            cascade.k_min,
            "min",
        )

    def test_the_runoff_is_read_and_written_back_with_the_estimation(self):
        document = {"model": "curve-number", "amc": "III", **LUTZ}

        model = runoff_from_document(document)

        assert isinstance(model, CurveNumberRunoff)
        assert model.nash_estimation == "lutz"
        assert json.dumps(model.to_document()) == json.dumps(document)
        written = RoutingNetwork.from_document(network(KAMIENNIK, document))
        assert written.to_document()["nodes"][0]["runoff"] == document

    @pytest.mark.parametrize(
        ("fields", "option", "reason"),
        [
            ({"nash_estimation": "lutz"}, "nash_estimation", "not_applicable"),
            ({**LUTZ, "nash_n": 3.0}, "nash_estimation", "conflict"),
            ({**LUTZ, "nash_k_min": 30.0}, "nash_estimation", "conflict"),
            ({**LUTZ, "nash_estimation": "urban"}, "nash_estimation", "choice"),
            ({"uh_model": "nash"}, "nash_n", "required"),
        ],
    )
    def test_a_misplaced_field_is_refused_with_the_reason_of_the_command(
        self, fields, option, reason
    ):
        error = refused(lambda: CurveNumberRunoff(**fields))

        assert (error.details["option"], error.details["reason"]) == (option, reason)

    def test_a_node_without_lutzs_fields_is_refused_naming_the_node_and_them(self):
        lacking = {
            key: value
            for key, value in KAMIENNIK.items()
            if key not in ("flow_path_length_km", "manning_n")
        }

        error = refused(lambda: RoutingNetwork.from_document(network(lacking, RUNOFF)))

        assert error.details["node_id"] == "Z1"
        assert error.details["reason"] == "missing_field"
        assert error.details["option"] == "watershed.flow_path_length_km"
        assert error.details["missing"] == ["flow_path_length_km", "manning_n"]
        assert error.details["method"] == "lutz"
