"""Tests of the ``route`` operations: result, outflow file, check and conflicts."""

from pathlib import Path

import numpy as np
import pytest

from hydrolog.catalog import run_command
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.catalog.inputs import load_hydrograph
from hydrolog.exceptions import (
    ConflictError,
    InputDataError,
    InvalidParameterError,
    OutputError,
)
from hydrolog.operations import RouteResult, route_lag, route_muskingum
from hydrolog.routing import Hydrograph, LagReach, MuskingumReach

from ._routing_reference import (
    IOWA_INFLOW,
    IOWA_K_MIN,
    IOWA_OUTFLOW,
    IOWA_STEP_MIN,
    IOWA_TIMES_MIN,
    IOWA_TOLERANCE,
    IOWA_X,
)

FIXTURES = Path(__file__).parents[1] / "fixtures"
FLOOD_INFLOW = FIXTURES / "flood_inflow.csv"
TIMES = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]
FLOOD = [0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0]


def inline(**options):
    """The options of ``route lag`` for the inline flood."""
    return {"lag_min": 25.0, "times_min": TIMES, "discharge_m3s": FLOOD, **options}


def run(**options) -> OperationOutput:
    return route_lag(**inline(**options))


class TestResult:
    def test_the_series_is_in_the_result_without_an_output(self):
        output = run()

        result = output.result
        assert isinstance(result, RouteResult)
        assert result.times_min.tolist() == [i * 10.0 for i in range(11)]
        np.testing.assert_allclose(
            result.outflow_m3s,
            [0.0, 0.0, 0.0, 5.0, 25.0, 65.0, 75.0, 45.0, 20.0, 5.0, 0.0],
            atol=1e-12,
        )
        assert output.files == ()
        assert output.check is False

    def test_the_summary_follows_from_the_series(self):
        result = run().result

        assert result.model == "lag"
        assert result.parameters == {"lag_min": 25.0, "lag_steps": 2.5}
        assert result.timestep_min == 10.0
        assert result.extension_min == 30.0
        assert (result.inflow_peak_m3s, result.inflow_time_to_peak_min) == (90.0, 30.0)
        assert (result.outflow_peak_m3s, result.outflow_time_to_peak_min) == (
            75.0,
            60.0,
        )
        assert result.peak_attenuation_pct == pytest.approx(100.0 * 15.0 / 90.0)
        assert result.peak_delay_min == 30.0
        assert result.inflow_volume_m3 == pytest.approx(144000.0)
        assert result.outflow_volume_m3 == pytest.approx(144000.0)
        assert abs(result.balance_error_m3) < 1e-6

    def test_the_notices_of_the_run_become_catalog_notices(self):
        notices = run().notices

        assert all(isinstance(notice, Notice) for notice in notices)
        assert [(n.level, n.code) for n in notices] == [
            ("info", "lag_interpolated"),
            ("info", "tail_extended"),
        ]

    def test_the_run_options_reach_the_model(self):
        result = run(initial_outflow_m3s=5.0, extend_min=0.0).result

        assert result.extension_min == 0.0
        assert result.outflow_m3s[0] == 5.0
        assert len(result.outflow_m3s) == len(FLOOD)

    def test_a_file_input_gives_the_same_result_as_the_inline_lists(self):
        from_file = route_lag(lag_min=30.0, input_file=FLOOD_INFLOW).result
        hydrograph = load_hydrograph(input_file=FLOOD_INFLOW)
        inline_lists = route_lag(
            lag_min=30.0,
            times_min=hydrograph.times_min.tolist(),
            discharge_m3s=hydrograph.discharge_m3s.tolist(),
        ).result

        assert from_file.to_dict() == inline_lists.to_dict()

    def test_a_bad_parameter_or_table_is_a_validation_error(self):
        with pytest.raises(InvalidParameterError) as caught:
            route_lag(lag_min=0.0, times_min=TIMES, discharge_m3s=FLOOD)
        assert caught.value.details["option"] == "lag_min"

        with pytest.raises(InvalidParameterError) as caught:
            route_lag(lag_min=10.0, times_min=[0, 10, 25], discharge_m3s=[1, 2, 3])
        assert caught.value.details["reason"] == "irregular_step"

    def test_a_bad_file_is_a_data_error(self, tmp_path):
        path = tmp_path / "bad.csv"
        path.write_text("time_min,discharge_m3s\n0,1\n10,2\n25,3\n", encoding="utf-8")

        with pytest.raises(InputDataError) as caught:
            route_lag(lag_min=10.0, input_file=path)

        assert caught.value.details["reason"] == "irregular_step"


class TestOutputFile:
    def test_the_outflow_is_written_as_a_hydrograph_table(self, tmp_path):
        target = tmp_path / "out" / "outflow.csv"

        output = run(output=target)

        expected = LagReach(25.0).route(Hydrograph(TIMES, FLOOD)).outflow
        assert target.read_text(encoding="utf-8") == expected.to_table()
        assert b"\r" not in target.read_bytes()
        assert output.files == (target,)
        assert output.replaced == ()
        assert output.result.times_min is None
        assert output.result.outflow_m3s is None
        assert output.result.outflow_peak_m3s == 75.0

    def test_the_file_is_a_valid_input_of_the_next_command(self, tmp_path):
        target = tmp_path / "outflow.csv"
        run(output=target)

        again = route_lag(lag_min=20.0, input_file=target).result

        assert again.inflow_peak_m3s == 75.0
        assert again.outflow_peak_m3s == 75.0
        assert again.peak_delay_min == 20.0

    def test_an_existing_file_is_a_conflict_that_leaves_it_alone(self, tmp_path):
        target = tmp_path / "outflow.csv"
        target.write_text("keep me", encoding="utf-8")

        with pytest.raises(ConflictError) as caught:
            run(output=target)

        assert caught.value.details["reason"] == "output_exists"
        assert caught.value.details["paths"] == [str(target)]
        assert target.read_text(encoding="utf-8") == "keep me"

    def test_force_replaces_the_file_and_reports_it(self, tmp_path):
        target = tmp_path / "outflow.csv"
        target.write_text("old", encoding="utf-8")

        output = run(output=target, force=True)

        assert output.replaced == (str(target),)
        assert target.read_text(encoding="utf-8").startswith("time_min,discharge_m3s\n")

    def test_the_output_must_not_be_the_input_file(self, tmp_path):
        source = tmp_path / "inflow.csv"
        source.write_text(Hydrograph(TIMES, FLOOD).to_table(), encoding="utf-8")
        before = source.read_bytes()

        with pytest.raises(InvalidParameterError) as caught:
            route_lag(lag_min=10.0, input_file=source, output=source, force=True)

        assert caught.value.details == {
            "option": "output",
            "reason": "conflict",
            "input": "input_file",
        }
        assert source.read_bytes() == before

    def test_an_invalid_inflow_writes_nothing(self, tmp_path):
        target = tmp_path / "out" / "outflow.csv"

        with pytest.raises(InvalidParameterError):
            route_lag(
                lag_min=10.0,
                times_min=[0, 10, 25],
                discharge_m3s=[1, 2, 3],
                output=target,
            )

        assert not target.parent.exists()

    def test_an_unwritable_target_is_an_output_error(self, tmp_path):
        blocker = tmp_path / "file"
        blocker.write_text("x", encoding="utf-8")

        with pytest.raises(OutputError) as caught:
            run(output=blocker / "outflow.csv")

        assert caught.value.details["reason"] == "output_unwritable"


class TestCheck:
    def test_with_an_output_it_plans_and_writes_nothing(self, tmp_path):
        target = tmp_path / "outflow.csv"

        output = run(output=target, check=True)

        assert output.check is True
        assert output.result["targets"] == [
            {"option": "output", "path": str(target), "action": "write"}
        ]
        assert not target.exists()

    def test_the_plan_of_an_existing_file_shows_the_conflict_or_the_replacement(
        self, tmp_path
    ):
        target = tmp_path / "outflow.csv"
        target.write_text("old", encoding="utf-8")

        without = run(output=target, check=True).result["targets"][0]
        forced = run(output=target, check=True, force=True).result["targets"][0]

        assert (without["action"], without["reason"]) == ("conflict", "output_exists")
        assert forced["action"] == "replace"
        assert target.read_text(encoding="utf-8") == "old"

    def test_without_an_output_there_is_nothing_to_plan_and_it_computes(self):
        output = run(check=True)

        assert output.check is False
        assert isinstance(output.result, RouteResult)
        assert output.result.outflow_peak_m3s == 75.0


class TestThroughTheCatalog:
    def test_an_example_option_set_gives_a_valid_envelope(self, tmp_path):
        envelope = run_command(
            "route lag",
            {
                "lag_min": 30.0,
                "input_file": str(FLOOD_INFLOW),
                "output": str(tmp_path / "outflow.csv"),
            },
        ).to_dict()

        assert envelope["result"]["schema"] == "hydrolog-route-lag/1"
        assert [record["status"] for record in envelope["result"]["files"]] == [
            "written"
        ]
        assert envelope["result"]["outflow_m3s"] is None

    def test_the_inline_and_the_file_alternative_exclude_each_other(self):
        with pytest.raises(InvalidParameterError) as caught:
            run_command("route lag", inline(input_file=str(FLOOD_INFLOW)))

        assert caught.value.details["reason"] == "one_of"


class TestRouteMuskingum:
    def iowa(self, **options) -> OperationOutput:
        return route_muskingum(
            k_min=IOWA_K_MIN,
            x=IOWA_X,
            subreaches=1,
            times_min=IOWA_TIMES_MIN,
            discharge_m3s=IOWA_INFLOW,
            extend_min=0.0,
            **options,
        )

    def test_the_published_example_gives_the_published_outflow(self):
        result = self.iowa().result

        assert isinstance(result, RouteResult)
        np.testing.assert_allclose(
            result.outflow_m3s, IOWA_OUTFLOW, rtol=0, atol=IOWA_TOLERANCE
        )
        assert result.times_min.tolist() == IOWA_TIMES_MIN

    def test_the_summary_of_the_published_example(self):
        result = self.iowa().result

        assert result.model == "muskingum"
        assert result.timestep_min == IOWA_STEP_MIN
        assert result.parameters["subreaches"] == 1
        assert result.parameters["substeps"] == 1
        assert (result.inflow_peak_m3s, result.inflow_time_to_peak_min) == (
            680.0,
            3 * IOWA_STEP_MIN,
        )
        assert result.outflow_time_to_peak_min == pytest.approx(5 * IOWA_STEP_MIN)
        assert result.outflow_peak_m3s == pytest.approx(487.2, abs=IOWA_TOLERANCE)
        assert result.peak_delay_min == pytest.approx(2 * IOWA_STEP_MIN)
        assert result.peak_attenuation_pct == pytest.approx(
            100.0 * (1.0 - 487.2 / 680.0), abs=0.01
        )
        # the water the reach holds: K [X I + (1 - X) O] at the first and last ordinate
        assert result.storage_start_m3 == pytest.approx(IOWA_K_MIN * 60.0 * 100.0)
        assert result.storage_end_m3 > result.storage_start_m3
        assert abs(result.balance_error_m3) < 1e-6 * result.inflow_volume_m3

    def test_the_notices_of_a_divided_step_become_catalog_notices(self):
        # K = 0.4 steps: no whole number of sub-reaches fits, the step is halved
        output = route_muskingum(k_min=4.0, x=0.2, times_min=TIMES, discharge_m3s=FLOOD)

        assert output.result.parameters["substeps"] == 2
        assert all(isinstance(notice, Notice) for notice in output.notices)
        assert [(n.level, n.code) for n in output.notices] == [
            ("info", "substeps_added"),
            ("info", "tail_extended"),
        ]

    def test_a_number_of_sub_reaches_outside_the_window_is_a_validation_error(self):
        with pytest.raises(InvalidParameterError) as caught:
            route_muskingum(
                k_min=60.0, x=0.2, subreaches=2, times_min=TIMES, discharge_m3s=FLOOD
            )

        details = caught.value.details
        assert (details["option"], details["reason"]) == (
            "subreaches",
            "unstable_timestep",
        )
        assert (details["minimum"], details["maximum"]) == (3, 9)

    def test_the_outflow_file_is_the_inflow_of_the_next_reach(self, tmp_path):
        target = tmp_path / "upstream.csv"
        first = route_muskingum(
            k_min=40.0, x=0.2, input_file=FLOOD_INFLOW, output=target
        )
        series = load_hydrograph(input_file=target)

        from_file = route_muskingum(k_min=30.0, x=0.1, input_file=target).result
        from_memory = route_muskingum(
            k_min=30.0,
            x=0.1,
            times_min=series.times_min.tolist(),
            discharge_m3s=series.discharge_m3s.tolist(),
        ).result

        assert first.result.outflow_m3s is None
        assert from_file.to_dict() == from_memory.to_dict()
        assert from_file.inflow_peak_m3s == first.result.outflow_peak_m3s

    @pytest.mark.parametrize(
        ("name", "value"),
        [
            ("x", 0.51),
            ("x", -0.01),
            ("k_min", 0.0),
            ("k_min", -5.0),
            ("subreaches", 0),
            ("subreaches", 2.5),
        ],
    )
    def test_the_command_and_the_class_refuse_a_value_in_the_same_words(
        self, name, value
    ):
        options = {"k_min": 60.0, "x": 0.2, **{name: value}}

        with pytest.raises(InvalidParameterError) as via_command:
            run_command(
                "route muskingum",
                {**options, "times_min": TIMES, "discharge_m3s": FLOOD},
            )
        with pytest.raises(InvalidParameterError) as via_class:
            MuskingumReach(**options)

        for key in ("option", "reason"):
            assert via_class.value.details[key] == via_command.value.details[key]

    def test_an_example_option_set_gives_a_valid_envelope(self, tmp_path):
        envelope = run_command(
            "route muskingum",
            {
                "k_min": 40.0,
                "x": 0.2,
                "input_file": str(FLOOD_INFLOW),
                "output": str(tmp_path / "outflow.csv"),
            },
        ).to_dict()

        assert envelope["result"]["schema"] == "hydrolog-route-muskingum/1"
        assert [record["status"] for record in envelope["result"]["files"]] == [
            "written"
        ]
        assert envelope["result"]["parameters"]["subreaches"] == 4
        assert envelope["result"]["outflow_m3s"] is None
