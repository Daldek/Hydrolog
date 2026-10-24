"""Tests of the routing core: hydrograph table, Reach template and lag routing."""

import numpy as np
import pytest

from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.routing import Hydrograph, LagReach, Reach
from hydrolog.routing.reach import MAX_ORDINATES, ReachRun

FLOOD = [0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0, 0.0, 0.0]


def flood() -> Hydrograph:
    """A ten-ordinate flood at a 10 min step, with a dry tail."""
    return Hydrograph.from_step(FLOOD, 10.0)


def codes(result) -> list[str]:
    return [notice.code for notice in result.notices]


class TestHydrographTable:
    def test_a_triangle_by_hand(self):
        hydrograph = Hydrograph.from_step([0.0, 12.0, 4.0], 30.0)

        assert hydrograph.timestep_min == 30.0
        assert hydrograph.start_min == 0.0
        assert hydrograph.duration_min == 60.0
        assert hydrograph.peak_discharge_m3s == 12.0
        assert hydrograph.time_to_peak_min == 30.0
        # trapezoid rule: (0 + 4) / 2 + 12 = 14 m3/s * 30 min * 60 s/min
        assert hydrograph.volume_m3 == pytest.approx(14.0 * 30.0 * 60.0)

    def test_the_time_to_peak_is_that_of_the_first_largest_ordinate(self):
        assert Hydrograph.from_step([0.0, 5.0, 5.0, 0.0], 10.0).time_to_peak_min == 10.0

    @pytest.mark.parametrize(
        ("times", "discharges", "option", "reason", "index"),
        [
            ([0, 10, 20], [1, 2], "discharge_m3s", "length_mismatch", None),
            ([0], [1], "times_min", "too_short", None),
            ([0, 10, 5], [1, 2, 3], "times_min", "not_increasing", 2),
            ([0, 10, 25], [1, 2, 3], "times_min", "irregular_step", 1),
            ([0, 10, 20], [1, -2, 3], "discharge_m3s", "negative", 1),
            ([0, 10, 20], [1, float("nan"), 3], "discharge_m3s", "not_finite", 1),
            ([0, float("inf"), 20], [1, 2, 3], "times_min", "not_finite", 1),
            ([0, 10, 20], [1, "x", 3], "discharge_m3s", "type", None),
        ],
    )
    def test_a_table_that_breaks_a_rule_names_the_option_and_the_reason(
        self, times, discharges, option, reason, index
    ):
        with pytest.raises(InvalidParameterError) as caught:
            Hydrograph(times, discharges)

        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason
        assert caught.value.details.get("index") == index

    def test_the_step_may_deviate_by_rounding_only(self):
        hours = (10.0 + 0.1 * np.arange(8)) * 60.0  # 600.0000000000001, 606.0, ...

        assert Hydrograph(hours, np.ones(8)).timestep_min == pytest.approx(6.0)

    def test_the_arrays_are_read_only_copies(self):
        values = [0.0, 1.0, 2.0]

        hydrograph = Hydrograph.from_step(values, 5.0)
        values[0] = 99.0

        assert hydrograph.discharge_m3s[0] == 0.0
        with pytest.raises(ValueError, match="read-only"):
            hydrograph.discharge_m3s[0] = 1.0

    def test_extended_holds_the_last_ordinate(self):
        hydrograph = Hydrograph.from_step([0.0, 10.0, 4.0], 30.0).extended(2)

        assert hydrograph.times_min.tolist() == [0.0, 30.0, 60.0, 90.0, 120.0]
        assert hydrograph.discharge_m3s.tolist() == [0.0, 10.0, 4.0, 4.0, 4.0]

    def test_extended_by_nothing_is_the_same_hydrograph(self):
        hydrograph = flood()

        assert hydrograph.extended(0) is hydrograph

    def test_refined_and_coarsened_are_inverse_and_keep_the_volume(self):
        hydrograph = flood()

        fine = hydrograph.refined(4)

        assert len(fine) == 9 * 4 + 1
        assert fine.timestep_min == pytest.approx(2.5)
        assert fine.volume_m3 == pytest.approx(hydrograph.volume_m3, rel=1e-12)
        assert fine.discharge_m3s[1] == pytest.approx(0.25 * 10.0)  # on the line 0-10
        np.testing.assert_array_equal(
            fine.coarsened(4).discharge_m3s, hydrograph.discharge_m3s
        )
        np.testing.assert_allclose(fine.coarsened(4).times_min, hydrograph.times_min)

    def test_coarsened_needs_a_whole_number_of_groups(self):
        with pytest.raises(InvalidParameterError, match="cannot be divided"):
            flood().coarsened(4)

    def test_the_table_text_reads_back_the_same_numbers(self):
        hydrograph = Hydrograph.from_step([0.1, 0.30000000000000004, 7.0], 0.5)

        lines = hydrograph.to_table().splitlines()

        assert lines[0] == "time_min,discharge_m3s"
        rows = [tuple(float(cell) for cell in line.split(",")) for line in lines[1:]]
        assert rows == list(
            zip(
                hydrograph.times_min.tolist(),
                hydrograph.discharge_m3s.tolist(),
                strict=True,
            )
        )

    def test_to_dict_lists_the_arrays(self):
        document = Hydrograph.from_step([1.0, 2.0], 5.0).to_dict()

        assert document == {"times_min": [0.0, 5.0], "discharge_m3s": [1.0, 2.0]}


class TestLagReach:
    def test_a_whole_number_of_steps_is_an_exact_shift(self):
        result = LagReach(lag_min=30.0).route(flood())

        np.testing.assert_array_equal(
            result.outflow.discharge_m3s,
            [0.0, 0.0, 0.0, 0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0],
        )
        assert codes(result) == ["tail_extended"]
        assert result.extension_min == 10.0
        assert result.peak_delay_min == 30.0
        assert result.peak_attenuation_pct == 0.0
        assert result.volume_out_m3 == result.volume_in_m3
        assert result.balance_error_m3 == 0.0
        assert result.parameters == {"lag_min": 30.0, "lag_steps": 3.0}

    def test_a_fraction_of_a_step_is_interpolated_by_hand(self):
        # 25 min = 2.5 steps: O[i] = (I[i-2] + I[i-3]) / 2, the flood before it is 0
        result = LagReach(lag_min=25.0).route(flood())

        np.testing.assert_allclose(
            result.outflow.discharge_m3s,
            [0.0, 0.0, 0.0, 5.0, 25.0, 65.0, 75.0, 45.0, 20.0, 5.0, 0.0],
            atol=1e-12,
        )
        assert codes(result) == ["lag_interpolated", "tail_extended"]
        assert result.notices[0].level == "info"
        assert result.peak_attenuation_pct == pytest.approx(100.0 * 15.0 / 90.0)
        assert result.volume_out_m3 == pytest.approx(result.volume_in_m3, rel=1e-12)
        assert abs(result.balance_error_m3) < 1e-6

    def test_a_lag_shorter_than_a_step_averages_with_the_previous_ordinate(self):
        result = LagReach(lag_min=5.0).route(flood())

        np.testing.assert_allclose(
            result.outflow.discharge_m3s,
            [0.0, 5.0, 25.0, 65.0, 75.0, 45.0, 20.0, 5.0, 0.0, 0.0],
            atol=1e-12,
        )
        assert codes(result) == ["lag_interpolated"]

    def test_the_initial_outflow_fills_the_time_before_the_first_ordinate(self):
        result = LagReach(lag_min=30.0).route(flood(), initial_outflow_m3s=5.0)

        np.testing.assert_array_equal(
            result.outflow.discharge_m3s,
            [5.0, 5.0, 5.0, 0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0],
        )
        assert result.storage_start_m3 == 5.0 * 30.0 * 60.0

    def test_a_steady_state_stays_and_needs_no_extension(self):
        result = LagReach(lag_min=30.0).route(Hydrograph.from_step([7.0] * 10, 10.0))

        assert result.outflow.discharge_m3s.tolist() == [7.0] * 10
        assert result.notices == []
        assert result.storage_start_m3 == result.storage_end_m3 == 7.0 * 30.0 * 60.0
        assert result.balance_error_m3 == 0.0

    def test_a_lag_longer_than_the_series_releases_the_whole_flood(self):
        result = LagReach(lag_min=1000.0).route(flood())

        assert len(result.outflow) == 108
        assert result.volume_out_m3 == pytest.approx(result.volume_in_m3)
        assert result.storage_end_m3 == pytest.approx(0.0)
        assert codes(result) == ["tail_extended"]

    def test_the_extension_is_the_shortest_that_releases_the_flood(self):
        reach = LagReach(lag_min=123.0)

        automatic = reach.route(flood())
        one_step_less = reach.route(flood(), extend_min=100.0)
        as_long = reach.route(flood(), extend_min=110.0)

        assert automatic.extension_min == 110.0
        assert "tail_truncated" in codes(one_step_less)
        assert "tail_truncated" not in codes(as_long)
        np.testing.assert_array_equal(
            as_long.outflow.discharge_m3s, automatic.outflow.discharge_m3s
        )

    def test_a_lag_beyond_the_cap_ends_with_the_truncation_warning(self):
        result = LagReach(lag_min=5000.0).route(flood())

        assert result.extension_min == 1000.0  # ten times the 100 min of the inflow
        notice = result.notices[-1]
        assert (notice.code, notice.level) == ("tail_truncated", "warning")
        assert result.volume_out_m3 < result.volume_in_m3

    def test_no_extension_keeps_the_axis_and_warns_when_the_flood_is_cut(self):
        result = LagReach(lag_min=30.0).route(flood(), extend_min=0.0)

        assert len(result.outflow) == 10
        assert codes(result) == ["tail_truncated"]

    def test_an_extension_is_rounded_up_to_whole_steps(self):
        result = LagReach(lag_min=30.0).route(flood(), extend_min=25.0)

        assert len(result.outflow) == 13
        assert "tail_truncated" not in codes(result)

    def test_the_result_is_linear_in_the_inflow(self):
        first = np.array([0.0, 3.0, 9.0, 4.0, 0.0, 0.0, 0.0, 0.0])
        second = np.array([0.0, 0.0, 5.0, 8.0, 6.0, 1.0, 0.0, 0.0])
        reach = LagReach(lag_min=25.0)  # interpolating, so not a trivial shift

        def route(values):
            return reach.route(Hydrograph.from_step(values, 10.0), extend_min=50.0)

        np.testing.assert_allclose(
            route(first + second).outflow.discharge_m3s,
            route(first).outflow.discharge_m3s + route(second).outflow.discharge_m3s,
            atol=1e-12,
        )

    def test_the_result_does_not_depend_on_when_the_flood_starts(self):
        reach = LagReach(lag_min=25.0)

        early = reach.route(flood(), extend_min=100.0)
        late = reach.route(
            Hydrograph.from_step(np.concatenate([np.zeros(3), FLOOD]), 10.0),
            extend_min=100.0,
        )

        np.testing.assert_allclose(
            late.outflow.discharge_m3s,
            np.concatenate([np.zeros(3), early.outflow.discharge_m3s]),
            atol=1e-12,
        )

    @pytest.mark.parametrize(
        ("lag", "reason"),
        [
            (0.0, "exclusive_minimum"),
            (-5.0, "exclusive_minimum"),
            (float("inf"), "not_finite"),
            (float("nan"), "type"),
            (True, "type"),
            ("10", "type"),
        ],
    )
    def test_the_lag_must_be_a_finite_positive_number(self, lag, reason):
        with pytest.raises(InvalidParameterError) as caught:
            LagReach(lag_min=lag)

        assert caught.value.details["option"] == "lag_min"
        assert caught.value.details["reason"] == reason

    @pytest.mark.parametrize(
        ("options", "option", "reason"),
        [
            ({"initial_outflow_m3s": -1.0}, "initial_outflow_m3s", "minimum"),
            (
                {"initial_outflow_m3s": float("nan")},
                "initial_outflow_m3s",
                "not_finite",
            ),
            ({"extend_min": -10.0}, "extend_min", "minimum"),
            ({"extend_min": 10.0 * MAX_ORDINATES}, "extend_min", "maximum"),
        ],
    )
    def test_the_run_options_are_validated(self, options, option, reason):
        with pytest.raises(InvalidParameterError) as caught:
            LagReach(lag_min=30.0).route(flood(), **options)

        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason


class TestReachTemplate:
    class Broken(Reach):
        """A model that returns the given outflow, whatever the inflow."""

        model = "broken"

        def __init__(self, outflow: float) -> None:
            self.outflow = outflow

        def _run(self, inflow, initial_outflow_m3s):
            return ReachRun(
                outflow_m3s=np.full(len(inflow), self.outflow),
                storage_start_m3=0.0,
                storage_end_m3=0.0,
                storage_steady_m3=0.0,
                parameters={},
            )

    def test_a_negative_outflow_is_a_calculation_error(self):
        with pytest.raises(CalculationError) as caught:
            self.Broken(-0.5).route(Hydrograph.from_step([0.0, 1.0, 0.0], 10.0))

        assert caught.value.details["reason"] == "negative_outflow"

    def test_rounding_below_zero_is_removed(self):
        result = self.Broken(-1e-15).route(Hydrograph.from_step([0.0, 1.0, 0.0], 10.0))

        assert result.outflow.discharge_m3s.min() == 0.0
