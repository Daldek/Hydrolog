"""Tests of the Muskingum reach: the published example, identities, moments, window."""

import math

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing import Hydrograph, LagReach, MuskingumReach
from hydrolog.routing.muskingum import MAX_SUBSTEPS, subreach_window
from hydrolog.routing.reach import MAX_ORDINATES

from ._routing_reference import (
    IOWA_INFLOW,
    IOWA_K_MIN,
    IOWA_OUTFLOW,
    IOWA_STEP_MIN,
    IOWA_TOLERANCE,
    IOWA_WEIGHTS,
    IOWA_X,
)

FLOOD = [0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0, 0.0, 0.0]


def flood() -> Hydrograph:
    """A ten-ordinate flood at a 10 min step with a dry tail."""
    return Hydrograph.from_step(FLOOD, 10.0)


def codes(result) -> list[str]:
    return [notice.code for notice in result.notices]


def reference(inflow, k, x, dt, count, initial):
    """Muskingum written out sub-reach by sub-reach, the reference of the class.

    Returns the outflow and the storage at the first and at the last ordinate
    [flow * min]; nothing here is shared with the implementation.
    """
    sub_k = k / count
    total = 2.0 * sub_k * (1.0 - x) + dt
    c_now = (dt - 2.0 * sub_k * x) / total
    c_before = (dt + 2.0 * sub_k * x) / total
    c_out = (2.0 * sub_k * (1.0 - x) - dt) / total
    entering = list(inflow)
    first, last = 0.0, 0.0
    for _ in range(count):
        leaving = [initial]
        for t in range(1, len(entering)):
            leaving.append(
                c_now * entering[t] + c_before * entering[t - 1] + c_out * leaving[-1]
            )
        first += sub_k * (x * entering[0] + (1.0 - x) * leaving[0])
        last += sub_k * (x * entering[-1] + (1.0 - x) * leaving[-1])
        entering = leaving
    return np.array(entering), first, last


class TestPublishedExample:
    def reach(self) -> MuskingumReach:
        return MuskingumReach(k_min=IOWA_K_MIN, x=IOWA_X, subreaches=1)

    def route(self):
        inflow = Hydrograph.from_step(
            IOWA_INFLOW, IOWA_STEP_MIN, start_min=IOWA_STEP_MIN
        )
        return self.reach().route(inflow, extend_min=0.0)

    def test_the_outflow_agrees_with_the_handout_within_its_rounding(self):
        outflow = self.route().outflow.discharge_m3s

        difference = np.abs(outflow - IOWA_OUTFLOW)
        assert difference.max() < IOWA_TOLERANCE
        assert len(outflow) == len(IOWA_OUTFLOW)

    def test_the_weights_are_those_of_the_handout(self):
        parameters = self.route().parameters

        weights = (
            parameters["c_current"],
            parameters["c_previous"],
            parameters["c_outflow"],
        )
        np.testing.assert_allclose(weights, IOWA_WEIGHTS, atol=5e-5)
        assert sum(weights) == pytest.approx(1.0, abs=1e-15)

    def test_the_first_step_by_hand(self):
        # (300 + 11 * 100 + 9 * 100) / 21: the weights are 1/21, 11/21 and 9/21
        assert self.route().outflow.discharge_m3s[1] == pytest.approx(2300.0 / 21.0)

    def test_the_storage_follows_the_wedge_formula(self):
        result = self.route()

        # S = K [X I + (1 - X) O] in m3: K in seconds times the weighted flow
        assert result.storage_start_m3 == pytest.approx(IOWA_K_MIN * 60.0 * 100.0)
        last = result.outflow.discharge_m3s[-1]
        assert result.storage_end_m3 == pytest.approx(
            IOWA_K_MIN * 60.0 * (IOWA_X * 50.0 + (1.0 - IOWA_X) * last)
        )
        assert result.storage_end_m3 > result.storage_start_m3

    def test_the_volume_balance_closes_on_the_published_axis(self):
        result = self.route()

        assert abs(result.balance_error_m3) < 1e-6 * result.volume_in_m3

    def test_the_axis_is_kept_when_no_extension_is_asked_and_the_cut_is_reported(self):
        result = self.route()

        assert len(result.outflow) == len(IOWA_INFLOW)
        assert codes(result) == ["tail_truncated"]


class TestIdentities:
    def test_x_zero_is_the_linear_reservoir_of_the_clark_scheme(self):
        inflow = np.array([0, 5, 20, 40, 30, 15, 5, 0, 0, 0, 0, 0], dtype=float)
        storage, step = 30.0, 10.0
        # the loop that ClarkIUH used: O_i = O_{i-1} + C (I_i + I_{i-1} - 2 O_{i-1})
        c = step / (2.0 * storage + step)
        clark = np.zeros_like(inflow)
        for i in range(1, len(inflow)):
            clark[i] = clark[i - 1] + c * (
                inflow[i] + inflow[i - 1] - 2.0 * clark[i - 1]
            )

        result = MuskingumReach(k_min=storage, x=0.0, subreaches=1).route(
            Hydrograph.from_step(inflow, step), initial_outflow_m3s=0.0, extend_min=0.0
        )

        np.testing.assert_allclose(
            result.outflow.discharge_m3s, clark, rtol=1e-13, atol=1e-15
        )
        # S = K O: the storage of the reservoir is K times the outflow
        assert result.storage_end_m3 == pytest.approx(
            storage * 60.0 * clark[-1], rel=1e-12
        )

    def test_x_half_with_k_equal_to_the_step_is_a_lag_of_one_step(self):
        reach = MuskingumReach(k_min=10.0, x=0.5)
        lag = LagReach(lag_min=10.0)

        muskingum = reach.route(flood(), extend_min=30.0)
        shifted = lag.route(flood(), extend_min=30.0)

        assert muskingum.parameters["subreaches"] == 1
        np.testing.assert_array_equal(
            muskingum.outflow.discharge_m3s, shifted.outflow.discharge_m3s
        )
        assert muskingum.storage_end_m3 == pytest.approx(shifted.storage_end_m3)
        assert muskingum.peak_attenuation_pct == 0.0

    def test_x_half_with_k_of_n_steps_is_a_lag_of_n_steps(self):
        for steps in (2, 3, 7):
            muskingum = MuskingumReach(k_min=10.0 * steps, x=0.5).route(
                flood(), extend_min=100.0
            )
            shifted = LagReach(lag_min=10.0 * steps).route(flood(), extend_min=100.0)

            assert muskingum.parameters["subreaches"] == steps
            np.testing.assert_allclose(
                muskingum.outflow.discharge_m3s,
                shifted.outflow.discharge_m3s,
                atol=1e-12,
            )
            assert muskingum.storage_start_m3 == pytest.approx(shifted.storage_start_m3)
            assert muskingum.storage_end_m3 == pytest.approx(shifted.storage_end_m3)

    def test_the_lag_identity_holds_for_a_given_initial_outflow(self):
        # before the first ordinate the lag holds the initial outflow and so does every
        # sub-reach; the storage at the first ordinate is defined differently (the
        # lag has the initial outflow in transit, the sub-reach 1 the first inflow)
        muskingum = MuskingumReach(k_min=30.0, x=0.5).route(
            flood(), initial_outflow_m3s=4.0, extend_min=100.0
        )
        shifted = LagReach(lag_min=30.0).route(
            flood(), initial_outflow_m3s=4.0, extend_min=100.0
        )

        np.testing.assert_allclose(
            muskingum.outflow.discharge_m3s, shifted.outflow.discharge_m3s, atol=1e-12
        )
        assert muskingum.outflow.discharge_m3s[:3].tolist() == [4.0, 4.0, 4.0]
        assert muskingum.storage_end_m3 == pytest.approx(shifted.storage_end_m3)

    def test_x_half_with_a_fractional_number_of_steps_is_the_interpolated_lag(self):
        # K = 3.2 steps: no whole number of sub-reaches, so the step is divided by 5
        muskingum = MuskingumReach(k_min=32.0, x=0.5).route(flood(), extend_min=60.0)
        shifted = LagReach(lag_min=32.0).route(flood(), extend_min=60.0)

        np.testing.assert_allclose(
            muskingum.outflow.discharge_m3s, shifted.outflow.discharge_m3s, atol=1e-12
        )

    @pytest.mark.parametrize(
        ("count", "step"), [(1, 60.0), (1, 30.0), (2, 30.0), (3, 30.0), (4, 15.0)]
    )
    def test_the_mean_delay_is_k_and_the_variance_k_squared_one_minus_2x_over_n(
        self, count, step
    ):
        # The trapezoid scheme is the bilinear map of the continuous transfer function
        # (1 - KXs) / (1 + K(1 - X)s), whose first two moments it keeps exactly.
        k, x = 60.0, 0.2
        pulse = np.zeros(int(3600 / step))
        pulse[1] = 1.0
        times = step * np.arange(len(pulse))

        result = MuskingumReach(k_min=k, x=x, subreaches=count).route(
            Hydrograph(times, pulse), extend_min=0.0
        )

        outflow = result.outflow.discharge_m3s
        mean = (outflow * times).sum() / outflow.sum()
        variance = (outflow * (times - mean) ** 2).sum() / outflow.sum()
        assert outflow.sum() == pytest.approx(1.0, rel=1e-12)
        assert mean - step == pytest.approx(k, rel=1e-9)
        assert variance == pytest.approx(k * k * (1.0 - 2.0 * x) / count, rel=1e-9)

    def test_more_sub_reaches_attenuate_less(self):
        # K = 60, X = 0.2 and dt = 10 allow 3 to 9 sub-reaches
        peaks = [
            MuskingumReach(k_min=60.0, x=0.2, subreaches=count)
            .route(flood(), extend_min=300.0)
            .outflow.peak_discharge_m3s
            for count in (3, 4, 6, 9)
        ]

        assert peaks == sorted(peaks)
        assert peaks[0] < peaks[-1] < max(FLOOD)

    def test_a_steady_state_is_kept(self):
        result = MuskingumReach(k_min=60.0, x=0.3).route(
            Hydrograph.from_step([7.0] * 12, 10.0)
        )

        np.testing.assert_allclose(result.outflow.discharge_m3s, 7.0, rtol=1e-13)
        assert result.notices == []
        assert result.storage_start_m3 == pytest.approx(result.storage_end_m3)
        assert result.storage_start_m3 == pytest.approx(7.0 * 60.0 * 60.0)


class TestAgainstTheReferenceLoop:
    @pytest.mark.parametrize(
        ("k", "x", "step", "count", "initial"),
        [
            (60.0, 0.2, 10.0, 6, None),
            (60.0, 0.2, 10.0, 4, 5.0),
            (45.0, 0.0, 15.0, 3, 0.0),
            (45.0, 0.3, 10.0, 5, 20.0),
            (1200.0, 0.25, 720.0, 1, None),
            (1200.0, 0.25, 720.0, 2, 12.0),
        ],
    )
    def test_outflow_and_storage_equal_the_loop(self, k, x, step, count, initial):
        inflow = Hydrograph.from_step(FLOOD, step)
        start = FLOOD[0] if initial is None else initial

        result = MuskingumReach(k_min=k, x=x, subreaches=count).route(
            inflow, initial_outflow_m3s=initial, extend_min=0.0
        )

        outflow, first, last = reference(FLOOD, k, x, step, count, start)
        np.testing.assert_allclose(
            result.outflow.discharge_m3s, outflow, rtol=1e-12, atol=1e-12
        )
        assert result.storage_start_m3 == pytest.approx(first * 60.0, rel=1e-12)
        assert result.storage_end_m3 == pytest.approx(last * 60.0, rel=1e-12)

    @pytest.mark.parametrize("count", [4, 6, 8])
    def test_the_volume_balance_closes_with_a_given_initial_outflow(self, count):
        # the trapezoid continuity holds in every sub-reach, so the junctions cancel
        result = MuskingumReach(k_min=60.0, x=0.3, subreaches=count).route(
            flood(), initial_outflow_m3s=15.0, extend_min=200.0
        )

        assert abs(result.balance_error_m3) < 1e-9 * result.volume_in_m3

    def test_the_result_is_linear_in_the_inflow(self):
        first = np.array([0.0, 3.0, 9.0, 4.0, 0.0, 0.0, 0.0, 0.0])
        second = np.array([1.0, 0.0, 5.0, 8.0, 6.0, 1.0, 0.0, 0.0])
        reach = MuskingumReach(k_min=40.0, x=0.2)

        def route(values):
            return reach.route(Hydrograph.from_step(values, 10.0), extend_min=80.0)

        np.testing.assert_allclose(
            route(first + second).outflow.discharge_m3s,
            route(first).outflow.discharge_m3s + route(second).outflow.discharge_m3s,
            atol=1e-12,
        )

    def test_the_result_does_not_depend_on_when_the_flood_starts(self):
        reach = MuskingumReach(k_min=40.0, x=0.2)

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

    def test_the_extension_releases_the_flood_and_no_more(self):
        result = MuskingumReach(k_min=60.0, x=0.2).route(flood())

        assert "tail_extended" in codes(result)
        assert "tail_truncated" not in codes(result)
        assert result.volume_out_m3 == pytest.approx(result.volume_in_m3, rel=1e-3)
        assert result.storage_end_m3 == pytest.approx(
            0.0, abs=1e-3 * result.volume_in_m3
        )
        assert result.outflow.discharge_m3s[-1] < 1e-3 * max(FLOOD)


class TestSubreaches:
    def test_the_default_is_the_nearest_whole_number_of_steps(self):
        counts = {
            k: MuskingumReach(k_min=k, x=0.2).route(flood()).parameters["subreaches"]
            for k in (40.0, 34.0, 35.0, 36.0, 100.0)
        }

        # K / dt = 4, 3.4, 3.5, 3.6, 10; a half goes up
        assert counts == {40.0: 4, 34.0: 3, 35.0: 4, 36.0: 4, 100.0: 10}

    def test_no_notice_when_the_rule_of_thumb_is_inside_the_window(self):
        result = MuskingumReach(k_min=60.0, x=0.2).route(flood())

        assert result.parameters["substeps"] == 1
        assert "substeps_added" not in codes(result)

    def test_the_rule_of_thumb_is_inside_the_window_whenever_there_is_a_window(self):
        # the window [2KX/dt, 2K(1-X)/dt] is symmetric about K/dt, so the whole number
        # nearest to K/dt is in it as soon as it holds any whole number
        ratios = np.concatenate(
            [np.linspace(0.3, 12.0, 2000), np.arange(0.5, 12.0, 0.5)]
        )
        checked = 0
        for x in (0.0, 0.1, 0.25, 0.4, 0.49, 0.5):
            for ratio in ratios:
                lowest, highest = subreach_window(float(ratio) * 10.0, x, 10.0)
                if lowest <= highest:
                    assert lowest <= math.floor(ratio + 0.5) <= highest, (ratio, x)
                    checked += 1
        assert checked > 5000

    @pytest.mark.parametrize(
        ("k", "x", "step", "expected"),
        [
            (1200.0, 0.25, 720.0, (1, 2)),  # the Iowa example
            (60.0, 0.0, 10.0, (1, 12)),  # a linear reservoir: any N up to 2K/dt
            (10.0, 0.5, 10.0, (1, 1)),  # pure lag: the border is inside
            (25.0, 0.5, 10.0, (3, 2)),  # K = 2.5 dt and X = 0.5: no whole number
            (4.0, 0.2, 10.0, (1, 0)),  # K too short for the step: not even one
        ],
    )
    def test_the_window_of_a_step(self, k, x, step, expected):
        assert subreach_window(k, x, step) == expected

    @pytest.mark.parametrize("count", [3, 4, 6, 9])
    def test_a_whole_window_gives_non_negative_outflows(self, count):
        # a dry start followed by a sharp peak, the case that the window protects
        spike = Hydrograph.from_step([0, 0, 0, 100, 0, 0, 0, 0, 0, 0], 10.0)

        result = MuskingumReach(k_min=60.0, x=0.2, subreaches=count).route(spike)

        assert result.outflow.discharge_m3s.min() >= 0.0

    @pytest.mark.parametrize("count", [1, 2, 10, 13, 50])
    def test_an_explicit_number_outside_the_window_is_refused_with_the_window(
        self, count
    ):
        # K = 60, X = 0.2, dt = 10: 2KX / dt = 2.4 and 2K(1 - X) / dt = 9.6 for N = 1,
        # that is N from 3 (c_current >= 0) to 9 sub-reaches (c_outflow >= 0)
        reach = MuskingumReach(k_min=60.0, x=0.2, subreaches=count)
        lowest, highest = subreach_window(60.0, 0.2, 10.0)
        assert (lowest, highest) == (3, 9)

        with pytest.raises(InvalidParameterError) as caught:
            reach.route(flood())

        details = caught.value.details
        assert details["option"] == "subreaches"
        assert details["reason"] == "unstable_timestep"
        assert (details["minimum"], details["maximum"]) == (3, 9)
        assert details["value"] == count
        assert details["timestep_min"] == 10.0
        assert "3 to 9" in caught.value.hint

    def test_the_border_of_the_window_is_inside_it(self):
        for count in (3, 9):
            result = MuskingumReach(k_min=60.0, x=0.2, subreaches=count).route(flood())

            assert result.parameters["subreaches"] == count
            assert result.outflow.discharge_m3s.min() >= 0.0

    def test_an_explicit_number_is_refused_when_the_window_is_empty(self):
        reach = MuskingumReach(k_min=25.0, x=0.5, subreaches=2)

        with pytest.raises(InvalidParameterError) as caught:
            reach.route(flood())

        assert caught.value.details["reason"] == "unstable_timestep"
        assert "no whole number" in str(caught.value)
        assert "Leave subreaches out" in caught.value.hint

    def test_a_short_k_divides_the_step_and_says_so(self):
        # K = 0.4 dt with X = 0.2: 2K(1 - X) = 0.64 dt, so even one sub-reach is too
        # long for the step; the step is divided by 2 (K = 0.8 of a sub-step)
        result = MuskingumReach(k_min=4.0, x=0.2).route(flood())

        assert result.parameters["substeps"] == 2
        assert result.parameters["subreaches"] == 1
        assert codes(result)[0] == "substeps_added"
        assert result.notices[0].level == "info"
        assert "2 sub-steps of 5 min" in result.notices[0].message
        assert result.outflow.discharge_m3s.min() >= 0.0
        # the weights are those of the sub-step, and are all non-negative
        assert result.parameters["c_outflow"] >= 0.0
        assert result.parameters["c_current"] >= 0.0
        assert (
            result.parameters["subreaches_min"]
            <= 1
            <= result.parameters["subreaches_max"]
        )

    def test_a_divided_step_is_the_scheme_on_the_interpolated_inflow(self):
        result = MuskingumReach(k_min=4.0, x=0.2).route(flood(), extend_min=40.0)
        steps = result.parameters["substeps"]

        fine = Hydrograph.from_step(FLOOD, 10.0).extended(4).refined(steps)
        outflow, _, _ = reference(
            fine.discharge_m3s, 4.0, 0.2, 10.0 / steps, 1, FLOOD[0]
        )
        np.testing.assert_allclose(
            result.outflow.discharge_m3s, outflow[::steps], rtol=1e-12, atol=1e-12
        )

    def test_the_balance_of_a_divided_step_is_a_small_sampling_error(self):
        result = MuskingumReach(k_min=4.0, x=0.2).route(flood(), extend_min=40.0)

        # not zero (the outflow is read at every second fine ordinate), but small
        assert result.balance_error_m3 != 0.0
        assert abs(result.balance_error_m3) < 0.01 * result.volume_in_m3

    def test_a_k_that_is_not_a_whole_number_of_steps_at_x_half_needs_a_finer_step(self):
        result = MuskingumReach(k_min=25.0, x=0.5).route(flood())

        # K = 2.5 dt: translation by a whole number of sub-steps needs dt / 2
        assert result.parameters["substeps"] == 2
        assert result.parameters["subreaches"] == 5
        assert codes(result)[0] == "substeps_added"

    def test_a_k_too_short_for_a_hundred_sub_steps_is_refused(self):
        # needs 2K(1 - X) >= dt / 100: K = dt / 500 gives a window only at 313 parts
        reach = MuskingumReach(k_min=10.0 / 500.0, x=0.2)

        with pytest.raises(InvalidParameterError) as caught:
            reach.route(flood())

        assert caught.value.details["option"] == "k_min"
        assert caught.value.details["reason"] == "unstable_timestep"
        assert caught.value.details["maximum_substeps"] == MAX_SUBSTEPS

    def test_an_incommensurable_k_at_x_half_is_refused(self):
        reach = MuskingumReach(k_min=10.0 * np.pi, x=0.5)

        with pytest.raises(InvalidParameterError) as caught:
            reach.route(flood())

        assert caught.value.details["reason"] == "unstable_timestep"
        assert "route lag" in caught.value.hint

    def test_a_divided_step_that_would_exceed_the_ordinate_limit_is_refused(self):
        long = Hydrograph.from_step(np.ones(20_000), 10.0)

        with pytest.raises(InvalidParameterError) as caught:
            MuskingumReach(k_min=0.1, x=0.2).route(long, extend_min=0.0)

        details = caught.value.details
        assert details["reason"] == "unstable_timestep"
        assert details["maximum"] == MAX_ORDINATES
        assert details["substeps"] * 19_999 + 1 > MAX_ORDINATES


class TestParameters:
    @pytest.mark.parametrize(
        ("k", "reason"),
        [
            (0.0, "exclusive_minimum"),
            (-10.0, "exclusive_minimum"),
            (float("inf"), "not_finite"),
            (float("nan"), "type"),
            (True, "type"),
            ("60", "type"),
        ],
    )
    def test_k_must_be_a_finite_positive_number(self, k, reason):
        with pytest.raises(InvalidParameterError) as caught:
            MuskingumReach(k_min=k, x=0.2)

        assert caught.value.details["option"] == "k_min"
        assert caught.value.details["reason"] == reason

    @pytest.mark.parametrize(
        ("x", "reason"),
        [
            (-0.01, "minimum"),
            (0.51, "maximum"),
            (float("inf"), "not_finite"),
            (float("nan"), "type"),
            (False, "type"),
            ("0.2", "type"),
        ],
    )
    def test_x_must_lie_between_zero_and_a_half(self, x, reason):
        with pytest.raises(InvalidParameterError) as caught:
            MuskingumReach(k_min=60.0, x=x)

        assert caught.value.details["option"] == "x"
        assert caught.value.details["reason"] == reason

    @pytest.mark.parametrize("x", [0.0, 0.5])
    def test_the_bounds_of_x_are_allowed(self, x):
        assert MuskingumReach(k_min=10.0, x=x).x == x

    @pytest.mark.parametrize(
        ("count", "reason"),
        [(0, "minimum"), (-2, "minimum"), (2.5, "type"), (True, "type"), ("3", "type")],
    )
    def test_subreaches_must_be_a_whole_number_of_at_least_one(self, count, reason):
        with pytest.raises(InvalidParameterError) as caught:
            MuskingumReach(k_min=60.0, x=0.2, subreaches=count)

        assert caught.value.details["option"] == "subreaches"
        assert caught.value.details["reason"] == reason

    def test_numpy_integers_are_whole_numbers(self):
        assert MuskingumReach(60.0, 0.2, subreaches=np.int64(6)).subreaches == 6
