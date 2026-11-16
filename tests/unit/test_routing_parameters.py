"""Tests of ``describe``: the values a calculation used, with their unit and source.

A schematic of a network is drawn from these lists, so they must say what the run used:
the values of the run, not a copy of the arguments. The unit follows from the name, and
the source tells a value that was given from one that is the default of the library and
one that the calculation derived.
"""

import json

import pytest

from hydrolog.routing import (
    CascadeReach,
    Channel,
    Context,
    Hydrograph,
    Junction,
    LagReach,
    LevelPoolReach,
    MuskingumCungeReach,
    MuskingumReach,
    Outlet,
    Parameter,
    Reservoir,
    RoutingNetwork,
    Subcatchment,
)
from hydrolog.routing.parameters import parameter, unit_of

FLOOD = Hydrograph.from_step([0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0], 10.0)


def listed(parameters: list[Parameter]) -> dict[str, Parameter]:
    """The parameters by name (a name is listed once)."""
    assert len({p.name for p in parameters}) == len(parameters)
    return {p.name: p for p in parameters}


class TestTheUnit:
    @pytest.mark.parametrize(
        ("name", "unit"),
        [
            ("tc_min", "min"),
            ("area_km2", "km2"),
            ("length_km", "km"),
            ("slope_m_per_m", "m/m"),
            ("celerity_m_per_s", "m/s"),
            ("reference_discharge_m3s", "m3/s"),
            ("storage_peak_m3", "m3"),
            ("total_mm", "mm"),
            ("top_width_m", "m"),
            ("urban_pct", "%"),
            ("x", None),
            ("cn", None),
            ("subreaches", None),
            ("lag_steps", None),
        ],
    )
    def test_it_follows_from_the_last_part_of_the_name(self, name, unit):
        assert unit_of(name) == unit

    def test_a_name_that_only_ends_like_a_unit_can_be_given_none(self):
        assert parameter("subreaches_min", 2, "computed").unit == "min"
        assert (
            parameter("subreaches_min", 2, "computed", {"subreaches_min": None}).unit
            is None
        )

    def test_a_value_that_is_not_a_number_or_a_string_is_refused(self):
        with pytest.raises(TypeError):
            parameter("storage_m3", [0.0, 1.0], "given")


class TestAReach:
    def test_without_a_run_it_lists_what_was_given(self):
        listing = listed(MuskingumReach(k_min=40.0, x=0.2).describe())

        assert {name: (p.value, p.unit, p.source) for name, p in listing.items()} == {
            "k_min": (40.0, "min", "given"),
            "x": (0.2, None, "given"),
        }

    def test_after_a_run_it_lists_the_values_that_the_run_used(self):
        reach = MuskingumReach(k_min=40.0, x=0.2)
        run = reach.route(FLOOD)

        listing = listed(reach.describe(run))

        for name, value in run.parameters.items():
            assert listing[name].value == value, name
        assert listing["k_min"].source == "given" and listing["x"].source == "given"
        assert listing["subreaches"].source == "computed"
        assert listing["subreaches"].value == run.parameters["subreaches"] == 4
        assert listing["c_current"].source == "computed"
        # the window of the sub-reaches is a pair of numbers, not minutes
        assert listing["subreaches_min"].unit is None

    def test_a_number_of_subreaches_that_is_given_is_given(self):
        reach = MuskingumReach(k_min=40.0, x=0.2, subreaches=2)

        listing = listed(reach.describe(reach.route(FLOOD)))

        assert listing["subreaches"].source == "given"
        assert listing["subreaches"].value == 2

    def test_the_celerity_is_given_for_a_wave_and_computed_for_a_section(self):
        wave = MuskingumCungeReach(
            length_km=8.0,
            slope_m_per_m=0.001,
            celerity_m_per_s=1.2,
            top_width_m=200.0,
        )
        section = MuskingumCungeReach(
            length_km=8.0,
            slope_m_per_m=0.001,
            manning_n=0.035,
            bottom_width_m=6.0,
            side_slope_m_per_m=2.0,
        )

        from_wave = listed(wave.describe(wave.route(FLOOD)))
        from_section = listed(section.describe(section.route(FLOOD)))

        assert from_wave["celerity_m_per_s"].source == "given"
        assert from_wave["celerity_m_per_s"].value == 1.2
        assert "manning_n" not in from_wave
        assert from_section["celerity_m_per_s"].source == "computed"
        assert from_section["celerity_m_per_s"].unit == "m/s"
        assert from_section["manning_n"].source == "given"
        assert from_section["top_width_m"].source == "computed"
        # the reference discharge is the peak of the inflow unless it is given
        assert from_wave["reference_discharge_m3s"].source == "computed"
        assert from_wave["reference_discharge_m3s"].value == FLOOD.peak_discharge_m3s

    def test_a_default_of_the_constructor_is_a_default(self):
        section = MuskingumCungeReach(
            length_km=8.0,
            slope_m_per_m=0.001,
            manning_n=0.035,
            bottom_width_m=6.0,
        )
        pool = LevelPoolReach(storage_m3=[0.0, 3e4, 9e4], outflow_m3s=[0.0, 10.0, 40.0])

        assert listed(section.describe())["side_slope_m_per_m"].source == "default"
        assert listed(pool.describe())["subreaches"].source == "default"

    def test_a_cascade_given_by_its_length_computes_the_storage_constant(self):
        by_length = CascadeReach(n=3.0, length_km=6.0, celerity_m_per_s=1.0)
        by_storage = CascadeReach(n=3.0, k_min=20.0)

        from_length = listed(by_length.describe(by_length.route(FLOOD)))
        from_storage = listed(by_storage.describe(by_storage.route(FLOOD)))

        assert from_length["k_min"].source == "computed"
        assert from_length["k_min"].value == pytest.approx(100.0 / 3.0)
        assert from_length["length_km"].source == "given"
        assert from_storage["k_min"].source == "given"

    def test_a_table_is_not_a_parameter_but_its_range_is_listed(self):
        pool = LevelPoolReach(storage_m3=[0.0, 3e4, 9e4], outflow_m3s=[0.0, 10.0, 40.0])

        listing = listed(pool.describe(pool.route(FLOOD)))

        assert "storage_m3" not in listing and "outflow_m3s" not in listing
        assert listing["storage_max_m3"].value == 9e4
        assert listing["outflow_max_m3s"].value == 40.0
        assert listing["storage_peak_m3"].source == "computed"


class TestANode:
    def test_a_channel_adds_the_options_of_its_run(self):
        a = Subcatchment("A", FLOOD)
        given = Channel("R", LagReach(lag_min=25.0), inflow=a, extend_min=30.0)
        automatic = Channel("S", LagReach(lag_min=25.0), inflow=a)

        explicit = listed(given.describe(given.evaluate([FLOOD], Context(10.0))))
        output = automatic.evaluate([FLOOD], Context(10.0))
        implicit = listed(automatic.describe(output))

        assert explicit["extend_min"].source == "given"
        assert explicit["extend_min"].value == 30.0
        assert implicit["extend_min"].source == "default"
        added = (len(output.hydrograph) - len(FLOOD)) * FLOOD.timestep_min
        assert implicit["extend_min"].value == added > 0.0
        # the first inflow ordinate is the outflow at rest that the run started from
        assert implicit["initial_outflow_m3s"].source == "default"
        assert implicit["initial_outflow_m3s"].value == FLOOD.discharge_m3s[0]

    def test_without_a_run_only_what_was_given_is_listed(self):
        channel = Channel("R", LagReach(lag_min=25.0), initial_outflow_m3s=3.0)

        listing = listed(channel.describe())

        assert set(listing) == {"lag_min", "initial_outflow_m3s"}
        assert listing["initial_outflow_m3s"].value == 3.0

    def test_a_junction_an_outlet_and_a_given_hydrograph_have_nothing_to_list(self):
        assert Junction("J").describe() == []
        assert Outlet("OUT").describe() == []
        assert Subcatchment("A", FLOOD).describe() == []


class TestTheSummaryOfAResult:
    def network(self) -> RoutingNetwork:
        a = Subcatchment("A", FLOOD)
        r = Channel("R", MuskingumReach(k_min=40.0, x=0.2), inflow=a)
        d = Reservoir(
            "D",
            LevelPoolReach(
                storage_m3=[0.0, 30000.0, 90000.0, 180000.0, 400000.0],
                outflow_m3s=[0.0, 10.0, 40.0, 100.0, 300.0],
            ),
            inflow=r,
        )
        return RoutingNetwork(Outlet("OUT", inflow=d))

    def test_every_node_has_its_figures_and_its_place(self):
        result = self.network().route()

        assert list(result.nodes) == list(result.order)
        for node_id, summary in result.nodes.items():
            hydrograph = result.hydrographs[node_id]
            assert summary.id == node_id
            assert summary.peak_m3s == hydrograph.peak_discharge_m3s
            assert summary.time_to_peak_min == hydrograph.time_to_peak_min
            assert summary.volume_m3 == hydrograph.volume_m3
        assert result.nodes["D"].type == "reservoir"
        assert result.nodes["D"].inflows == ("R",)
        assert result.nodes["A"].inflows == ()

    def test_the_parameters_of_a_reach_are_those_of_its_run(self):
        result = self.network().route()

        listing = listed(result.nodes["R"].parameters)

        for name, value in result.runs["R"].parameters.items():
            assert listing[name].value == value, name
        assert listing["k_min"].source == "given"
        assert listing["subreaches"].source == "computed"

    def test_the_result_is_json_with_the_parameters_as_objects(self):
        result = self.network().route()

        document = json.loads(result.to_json())

        parameters = document["nodes"]["R"]["parameters"]
        assert {"name": "k_min", "value": 40.0, "unit": "min", "source": "given"} in (
            parameters
        )
        assert document["nodes"]["R"]["peak_m3s"] == result.nodes["R"].peak_m3s
