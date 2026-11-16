"""Tests of the recurrences shared by the routing models and the Clark IUH."""

import numpy as np
import pytest

from hydrolog.routing._kernels import (
    linear_reservoir_coefficients,
    muskingum_coefficients,
    route_linear_reservoir,
    three_point,
)


def explicit_loop(inflow, c_current, c_previous, c_outflow, initial_outflow):
    """The recurrence written out, the reference of the vectorised kernel."""
    outflow = np.empty(len(inflow))
    outflow[0] = initial_outflow
    for t in range(1, len(inflow)):
        outflow[t] = (
            c_current * inflow[t]
            + c_previous * inflow[t - 1]
            + c_outflow * outflow[t - 1]
        )
    return outflow


def clark_loop(inflow, r_min, timestep_min):
    """The loop that ``ClarkIUH._route_linear_reservoir`` had before the kernel."""
    c1 = timestep_min / (2.0 * r_min + timestep_min)
    outflow = np.zeros_like(inflow)
    for i in range(1, len(inflow)):
        outflow[i] = outflow[i - 1] + c1 * (
            inflow[i] + inflow[i - 1] - 2.0 * outflow[i - 1]
        )
    return outflow


class TestThreePoint:
    @pytest.mark.parametrize(
        ("c_current", "c_previous", "c_outflow", "initial"),
        [
            (0.0476, 0.5238, 0.4286, 3.0),
            (0.25, 0.25, 0.5, 0.0),
            (0.355, 0.028, 0.617, 12.5),
            (0.0, 1.0, 0.0, 7.0),
            (0.9, 0.0, -0.3, 1.0),
        ],
    )
    def test_equals_the_explicit_loop(self, c_current, c_previous, c_outflow, initial):
        inflow = np.random.default_rng(7).random(300) * 40.0

        result = three_point(inflow, c_current, c_previous, c_outflow, initial)

        np.testing.assert_allclose(
            result,
            explicit_loop(inflow, c_current, c_previous, c_outflow, initial),
            rtol=1e-12,
            atol=1e-12,
        )

    def test_the_first_outflow_is_the_initial_outflow(self):
        result = three_point([5.0, 9.0, 2.0], 0.3, 0.3, 0.4, 1.25)

        assert result[0] == 1.25

    def test_a_single_ordinate_gives_the_initial_outflow(self):
        np.testing.assert_array_equal(three_point([4.0], 0.3, 0.3, 0.4, 2.5), [2.5])

    def test_one_step_by_hand(self):
        # O1 = 0.2 * 10 + 0.3 * 4 + 0.5 * 6
        result = three_point([4.0, 10.0], 0.2, 0.3, 0.5, 6.0)

        assert result[1] == pytest.approx(0.2 * 10.0 + 0.3 * 4.0 + 0.5 * 6.0)

    def test_a_steady_state_is_kept_when_the_weights_sum_to_one(self):
        result = three_point(np.full(50, 8.0), 0.2, 0.3, 0.5, 8.0)

        np.testing.assert_allclose(result, 8.0, rtol=1e-14)

    def test_returns_a_float_array_of_the_inflow_length(self):
        result = three_point(np.arange(6), 0.5, 0.5, 0.0, 0.0)

        assert result.dtype == np.float64
        assert result.shape == (6,)


class TestLinearReservoir:
    def test_the_weights_follow_the_trapezoid_rule(self):
        current, previous, outflow = linear_reservoir_coefficients(k=30.0, dt=10.0)

        assert current == previous == pytest.approx(10.0 / 70.0)
        assert outflow == pytest.approx(50.0 / 70.0)
        assert current + previous + outflow == pytest.approx(1.0)

    def test_the_weight_of_the_outflow_is_zero_at_twice_the_constant(self):
        assert linear_reservoir_coefficients(k=5.0, dt=10.0) == (0.5, 0.5, 0.0)

    def test_the_weight_of_the_outflow_is_negative_above_twice_the_constant(self):
        assert linear_reservoir_coefficients(k=2.0, dt=5.0)[2] < 0.0

    @pytest.mark.parametrize(("r_min", "timestep_min"), [(30.0, 10.0), (60.0, 5.0)])
    def test_equals_the_loop_the_clark_iuh_used_before(self, r_min, timestep_min):
        inflow = np.random.default_rng(3).random(120)
        inflow[0] = 0.0

        result = route_linear_reservoir(inflow, r_min, timestep_min)

        np.testing.assert_allclose(
            result, clark_loop(inflow, r_min, timestep_min), rtol=1e-12, atol=1e-15
        )

    def test_the_step_response_converges_to_the_exponential_with_second_order(self):
        # S = K O with a unit step in the inflow: O(t) = 1 - exp(-t / K).
        k = 60.0

        def worst_error(dt):
            steps = int(600.0 / dt) + 1
            time = np.arange(steps) * dt
            outflow = route_linear_reservoir(np.ones(steps), k, dt)
            return float(np.abs(outflow - (1.0 - np.exp(-time / k))).max())

        coarse, fine = worst_error(15.0), worst_error(7.5)

        assert coarse < 0.02
        assert fine < coarse / 3.5  # the trapezoid rule is second-order accurate

    def test_the_volume_of_a_pulse_is_kept(self):
        inflow = np.zeros(400)
        inflow[1:6] = [2.0, 7.0, 11.0, 4.0, 1.0]

        outflow = route_linear_reservoir(inflow, k=20.0, dt=5.0)

        assert outflow.sum() == pytest.approx(inflow.sum(), rel=1e-9)
        assert outflow.min() >= 0.0


class TestMuskingum:
    def test_the_weights_of_the_published_example(self):
        # University of Iowa, Lesson 27: K = 20 h, X = 0.25, dt = 12 h
        current, previous, outflow = muskingum_coefficients(k=20.0, x=0.25, dt=12.0)

        assert (current, previous, outflow) == pytest.approx((1 / 21, 11 / 21, 9 / 21))
        assert round(current, 4) == 0.0476
        assert round(previous, 4) == 0.5238
        assert round(outflow, 4) == 0.4286

    @pytest.mark.parametrize(
        ("k", "x", "dt"),
        [(20.0, 0.25, 12.0), (5.0, 0.0, 10.0), (3.0, 0.5, 2.0), (8.0, -0.25, 6.0)],
    )
    def test_the_weights_sum_to_one(self, k, x, dt):
        assert sum(muskingum_coefficients(k, x, dt)) == pytest.approx(1.0, abs=1e-15)

    def test_x_zero_is_the_linear_reservoir(self):
        k, dt = 30.0, 10.0

        assert muskingum_coefficients(k, 0.0, dt) == (
            dt / (2 * k + dt),
            dt / (2 * k + dt),
            (2 * k - dt) / (2 * k + dt),
        )

    def test_x_half_with_k_equal_to_dt_passes_the_previous_inflow_on(self):
        assert muskingum_coefficients(k=10.0, x=0.5, dt=10.0) == (0.0, 1.0, 0.0)

    def test_the_borders_of_the_window_are_where_a_weight_is_zero(self):
        k, x = 20.0, 0.25

        # dt = 2KX: the current inflow has no weight;
        # dt = 2K(1 - X): the previous outflow has none
        assert muskingum_coefficients(k, x, 2 * k * x)[0] == 0.0
        assert muskingum_coefficients(k, x, 2 * k * (1 - x))[2] == 0.0
        # a negative X: dt = -2KX is where the weight of the previous inflow vanishes
        assert muskingum_coefficients(k, -0.25, 2 * k * 0.25)[1] == 0.0

    def test_outside_the_window_a_weight_is_negative(self):
        k, x = 20.0, 0.25

        assert muskingum_coefficients(k, x, 0.5 * 2 * k * x)[0] < 0.0
        assert muskingum_coefficients(k, x, 1.5 * 2 * k * (1 - x))[2] < 0.0

    def test_a_pulse_after_a_dry_start_gives_a_negative_outflow_below_the_window(self):
        # dt < 2KX: the weight of the current inflow is negative, so the first ordinate
        # of a rising limb takes water out of the outflow, the case the window excludes
        weights = muskingum_coefficients(k=60.0, x=0.4, dt=10.0)

        outflow = three_point([0.0, 100.0, 0.0, 0.0], *weights, initial_outflow=0.0)

        assert outflow[1] < 0.0

    def test_the_sinusoidal_response_converges_to_the_transfer_function(self):
        # S = K [X I + (1 - X) O] has the transfer function (1 - K X s) / (1 + K (1 - X)
        # s). For I = 1 + sin(w t) the periodic outflow is 1 + |H| sin(w t + arg H); the
        # trapezoid rule is second-order accurate in dt.
        k, x, omega = 60.0, 0.3, 2.0 * np.pi / 600.0
        response = (1.0 - 1j * omega * k * x) / (1.0 + 1j * omega * k * (1.0 - x))

        def worst_error(dt):
            time = np.arange(int(3000.0 / dt) + 1) * dt
            exact = 1.0 + np.abs(response) * np.sin(omega * time + np.angle(response))
            outflow = three_point(
                1.0 + np.sin(omega * time),
                *muskingum_coefficients(k, x, dt),
                initial_outflow=exact[0],
            )
            late = time >= 1800.0
            return float(np.abs(outflow - exact)[late].max())

        coarse, fine = worst_error(40.0), worst_error(20.0)

        assert coarse < 0.01
        assert fine < coarse / 3.5
