"""Tests of the cascade of linear reservoirs: the exact kernel and its oracles.

The oracles share nothing with the implementation: the matrix exponential of the chain
of reservoirs (whole ``n``), the integral of the gamma density of
:class:`~hydrolog.runoff.NashIUH` against the inflow (any ``n``), the closed forms of
one reservoir, and the trapezoid recurrence of ``route_muskingum_cascade`` as ``dt``
falls.
"""

import math
from decimal import Decimal, localcontext

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.linalg import expm
from scipy.stats import gamma

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing import CascadeReach, Hydrograph, cascade_weights
from hydrolog.routing import cascade as cascade_module
from hydrolog.routing._kernels import route_muskingum_cascade
from hydrolog.runoff import NashIUH


def codes(result) -> list[str]:
    return [notice.code for notice in result.notices]


def random_inflow(seed: int, size: int = 40) -> np.ndarray:
    """A rough, not negative inflow: the kernel must not depend on a smooth shape."""
    return np.abs(np.random.default_rng(seed).normal(10.0, 6.0, size))


def exact_chain(n, k_min, dt, inflow, start):
    """Whole ``n`` reservoirs solved exactly for the piecewise-linear inflow.

    The state is the outflow of each reservoir, the inflow and a constant; over one
    step the inflow is linear, so the matrix exponential of the step is the exact
    propagator. Returns the outflow of the last reservoir at every ordinate and the
    water held by all reservoirs at the end [flow * min].
    """
    size = n + 2
    matrix = np.zeros((size, size))
    for i in range(n):
        matrix[i, i] = -1.0 / k_min
        matrix[i, i - 1 if i else n] = 1.0 / k_min
    state = np.zeros(size)
    state[:n] = start
    outflow = [start]
    for before, after in zip(inflow[:-1], inflow[1:], strict=True):
        step = matrix.copy()
        step[n, n + 1] = (after - before) / dt
        state[n], state[n + 1] = before, 1.0
        state = expm(step * dt) @ state
        outflow.append(state[n - 1])
    return np.array(outflow), k_min * float(state[:n].sum())


def sixty_digit_weights(n: int, ratio: str, count: int) -> np.ndarray:
    """The weights of whole ``n`` from ``V`` evaluated with 60 significant digits.

    ``Q(n, x) = exp(-x) sum_{i < n} x^i / i!`` for whole ``n``, so no special function
    of scipy is involved.
    """
    with localcontext() as context:
        context.prec = 60
        step = Decimal(ratio)

        def upper(order: int, x: Decimal) -> Decimal:
            term = total = Decimal(1)
            for i in range(1, order):
                term = term * x / i
                total += term
            return (-x).exp() * total

        def integral(m: int) -> Decimal:
            x = step * m
            return x * upper(n, x) + n * (1 - upper(n + 1, x))

        v = [integral(m) for m in range(count + 1)]
        weights = [1 - v[1] / step]
        weights += [-(v[m + 1] - 2 * v[m] + v[m - 1]) / step for m in range(1, count)]
        return np.array([float(w) for w in weights])


class TestExactness:
    @pytest.mark.parametrize("n", [1, 2, 3, 5])
    @pytest.mark.parametrize(
        ("dt", "k"), [(10.0, 30.0), (30.0, 10.0), (2.0, 40.0), (60.0, 5.0)]
    )
    @pytest.mark.parametrize("start", [None, 3.0])
    def test_whole_reservoirs_give_the_exact_response_of_the_chain(
        self, n, dt, k, start
    ):
        inflow = random_inflow(n + int(dt))
        first = float(inflow[0]) if start is None else start

        result = CascadeReach(n, k_min=k).route(
            Hydrograph.from_step(inflow, dt),
            initial_outflow_m3s=start,
            extend_min=0.0,
        )

        expected, storage = exact_chain(n, k, dt, inflow, first)
        np.testing.assert_allclose(
            result.outflow.discharge_m3s, expected, rtol=0, atol=1e-10
        )
        assert result.storage_start_m3 == pytest.approx(n * k * first * 60.0)
        assert result.storage_end_m3 == pytest.approx(storage * 60.0, rel=1e-10)

    @pytest.mark.parametrize("n", [1.5, 2.5, 4.3])
    @pytest.mark.parametrize("start", [None, 2.0])
    def test_any_n_gives_the_nash_convolution_of_the_interpolated_inflow(
        self, n, start
    ):
        k, dt = 25.0, 10.0
        inflow = random_inflow(7, 14)
        times = dt * np.arange(len(inflow))
        first = float(inflow[0]) if start is None else start
        iuh = NashIUH(n=n, k_min=k)

        def held(t):
            # linear between the ordinates; before the first the state of the start
            return float(np.interp(t, times, inflow, left=first))

        result = CascadeReach(n, k_min=k).route(
            Hydrograph.from_step(inflow, dt),
            initial_outflow_m3s=start,
            extend_min=0.0,
        )

        for j in (1, 3, 7, 13):
            age = times[j]
            # the inflow of the span of the series, then the state before it (every
            # reservoir at `first`: the share of the water that is still inside)
            knots = [age - t for t in times[:j]]
            inside, _ = quad(
                lambda s, t=times[j]: iuh.ordinate(s) * held(t - s),
                0.0,
                age,
                points=knots,
                epsabs=1e-13,
                epsrel=1e-12,
                limit=200,
            )
            beyond, _ = quad(iuh.ordinate, age, np.inf, epsabs=1e-14, epsrel=1e-12)
            # the jump of the inflow at the first ordinate is from `first` to inflow[0]
            expected = inside + first * beyond
            assert result.outflow.discharge_m3s[j] == pytest.approx(
                expected, rel=0, abs=1e-8
            )

    @pytest.mark.parametrize("n", [1.0, 1.5, 3.0, 6.7])
    @pytest.mark.parametrize("ratio", [0.2, 1.0, 3.5])
    def test_the_weights_are_the_unit_hat_response_of_the_nash_iuh(self, n, ratio):
        iuh = NashIUH(n=n, k_min=1.0)

        weights = cascade_weights(n, ratio, 12)

        for m, weight in enumerate(weights):
            centre = m * ratio
            hat, _ = quad(
                lambda s, c=centre: iuh.ordinate(s) * (1.0 - abs(c - s) / ratio),
                max(0.0, centre - ratio),
                centre + ratio,
                points=[centre] if centre > ratio else None,
                epsabs=1e-14,
                epsrel=1e-12,
                limit=200,
            )
            assert weight == pytest.approx(hat, rel=0, abs=1e-11)

    def test_a_narrow_pulse_gives_the_iuh_with_an_error_of_second_order(self):
        n, k = 4.5, 1.0
        iuh = NashIUH(n=n, k_min=k)
        errors = []
        for dt in (0.04, 0.02):
            # a hat of unit volume at the second ordinate (height 1/dt, base 2 dt)
            pulse = Hydrograph.from_step([0.0, 1.0 / dt, 0.0], dt)
            result = CascadeReach(n, k_min=k).route(
                pulse, extend_min=14.0 * k, initial_outflow_m3s=0.0
            )
            times = result.outflow.times_min - dt
            reference = np.array([iuh.ordinate(t) for t in times])
            # volumes are in m3/s * min here: the series is unit flow * time, so the
            # outflow in m3/s is the IUH ordinate [1/min] times one unit of volume
            errors.append(
                np.abs(result.outflow.discharge_m3s - reference)[times > 0].max()
            )

        assert errors[1] < 5e-6
        assert errors[0] / errors[1] == pytest.approx(4.0, rel=0.05)

    def test_one_reservoir_has_the_hand_checkable_step_response(self):
        # n = 1, dt = K, the inflow rises from 0 to 1 over the first step and stays:
        # O_1 = 1/e, and O_(j+1) = O_j / e + (1 - 1/e)  (the inflow is 1)
        result = CascadeReach(1, k_min=10.0).route(
            Hydrograph.from_step([0.0, 1.0, 1.0, 1.0, 1.0, 1.0], 10.0),
            extend_min=0.0,
        )

        expected = [0.0, math.exp(-1.0)]
        for _ in range(4):
            expected.append(expected[-1] * math.exp(-1.0) + 1.0 - math.exp(-1.0))
        np.testing.assert_allclose(
            result.outflow.discharge_m3s, expected, rtol=0, atol=1e-14
        )

    def test_a_constant_inflow_into_another_state_follows_the_gamma_distribution(self):
        # all reservoirs start at 2 and the inflow is 5 from the first ordinate on:
        # O(t) = 2 [1 - P(n, t/K)] + 5 P(n, t/K)
        n, k, dt = 3.4, 20.0, 5.0
        result = CascadeReach(n, k_min=k).route(
            Hydrograph.from_step(np.full(60, 5.0), dt),
            initial_outflow_m3s=2.0,
            extend_min=0.0,
        )

        share = gamma.cdf(dt * np.arange(60) / k, n)
        np.testing.assert_allclose(
            result.outflow.discharge_m3s, 2.0 + 3.0 * share, rtol=0, atol=1e-12
        )

    def test_the_trapezoid_recurrence_of_linear_reservoirs_converges_to_it(self):
        # the same samples, the trapezoid rule in each of 3 reservoirs against the
        # exact kernel: the difference falls with the square of the step
        differences = []
        for dt in (8.0, 4.0, 2.0):
            times = np.arange(0.0, 400.0 + dt, dt)
            inflow = 10.0 + 30.0 * np.exp(-(((times - 100.0) / 40.0) ** 2))
            exact = CascadeReach(3, k_min=30.0).route(
                Hydrograph.from_step(inflow, dt), extend_min=0.0
            )
            scheme = route_muskingum_cascade(inflow, 30.0, 0.0, dt, 3, inflow[0])
            differences.append(
                np.abs(exact.outflow.discharge_m3s - scheme.outflow).max()
            )

        assert differences[0] / differences[1] == pytest.approx(4.0, rel=0.15)
        assert differences[1] / differences[2] == pytest.approx(4.0, rel=0.15)
        assert differences[2] < 5e-3


class TestKernel:
    @pytest.mark.parametrize("n", [0.3, 1.0, 2.5, 8.0, 40.0])
    @pytest.mark.parametrize("ratio", [0.05, 0.5, 2.0, 25.0])
    def test_the_weights_are_not_negative_add_up_to_one_and_have_the_mean_delay(
        self, n, ratio
    ):
        count = int((n + 12.0 * math.sqrt(n) + 60.0) / ratio) + 5
        weights = cascade_weights(n, ratio, count)

        assert weights.min() >= 0.0
        assert weights.sum() == pytest.approx(1.0, abs=1e-8)
        # the hats reproduce a straight line, so the mean delay is exact: n K
        assert (np.arange(count) * weights).sum() * ratio == pytest.approx(n, rel=1e-8)

    def test_the_first_weights_of_one_reservoir_and_a_step_of_one_constant(self):
        e = math.exp(1.0)

        weights = cascade_weights(1.0, 1.0, 3)

        np.testing.assert_allclose(
            weights, [1 / e, (1 - 1 / e) ** 2, (1 - 1 / e) ** 2 / e], rtol=1e-13
        )

    def test_a_step_far_longer_than_the_storage_hardly_attenuates(self):
        # dt = 1000 K: the water that enters leaves within the step
        weights = cascade_weights(2.0, 1000.0, 3)

        assert weights[0] == pytest.approx(1.0 - 2.0 / 1000.0, abs=1e-12)
        assert weights.sum() == pytest.approx(1.0, abs=1e-12)

    @pytest.mark.parametrize(
        ("ratio", "tolerance"), [("1", 1e-13), ("0.1", 1e-11), ("0.01", 1e-9)]
    )
    def test_the_weights_agree_with_sixty_digit_arithmetic(self, ratio, tolerance):
        # relative to the largest weight: the second difference loses digits like
        # 1 / a^2, so the tolerance grows as the step falls (module documentation)
        count = min(int(60.0 / float(ratio)), 2500)

        exact = sixty_digit_weights(3, ratio, count)

        weights = cascade_weights(3.0, float(ratio), count)
        assert np.abs(weights - exact).max() <= tolerance * exact.max()

    @pytest.mark.parametrize(
        ("arguments", "option", "reason"),
        [
            ((0.0, 1.0, 3), "n", "exclusive_minimum"),
            ((2.0, -1.0, 3), "step_ratio", "exclusive_minimum"),
            ((2.0, 1.0, 0), "count", "minimum"),
            ((2.0, 1.0, 2.5), "count", "type"),
        ],
    )
    def test_arguments_out_of_range_are_refused(self, arguments, option, reason):
        with pytest.raises(InvalidParameterError) as caught:
            cascade_weights(*arguments)

        assert (caught.value.details["option"], caught.value.details["reason"]) == (
            option,
            reason,
        )


class TestRouting:
    def reach(self) -> CascadeReach:
        return CascadeReach(3.5, k_min=25.0)

    def flood(self) -> Hydrograph:
        return Hydrograph.from_step(
            [0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0], 10.0
        )

    def test_a_steady_state_is_kept(self):
        result = self.reach().route(Hydrograph.from_step(np.full(12, 7.0), 15.0))

        np.testing.assert_allclose(result.outflow.discharge_m3s, 7.0, rtol=1e-13)
        assert codes(result) == []
        assert result.storage_start_m3 == pytest.approx(3.5 * 25.0 * 60.0 * 7.0)
        assert result.storage_end_m3 == pytest.approx(result.storage_start_m3)

    def test_the_response_is_linear_and_shift_invariant(self):
        # both series start at rest: with another first ordinate the inflow would jump
        # at the start, and the jump has no counterpart in a shifted series
        a, b = random_inflow(1, 30), random_inflow(2, 30)
        a[0] = b[0] = 0.0
        reach = CascadeReach(2.2, k_min=12.0)

        def route(values, start=0.0):
            return reach.route(
                Hydrograph.from_step(values, 6.0),
                initial_outflow_m3s=start,
                extend_min=60.0,
            ).outflow.discharge_m3s

        np.testing.assert_allclose(route(a + 2.0 * b), route(a) + 2.0 * route(b))
        shifted = route(np.concatenate([[0.0] * 5, a]))
        np.testing.assert_allclose(
            shifted[5:], route(a)[: len(shifted) - 5], atol=1e-12
        )

    def test_the_outflow_is_never_negative_and_a_dry_inflow_stays_dry(self):
        wet = CascadeReach(6.0, k_min=2.0).route(
            Hydrograph.from_step([0.0, 1000.0, 0.0, 0.0, 0.0, 0.0], 0.5)
        )
        dry = self.reach().route(Hydrograph.from_step([0.0] * 6, 10.0))

        assert wet.outflow.discharge_m3s.min() >= 0.0
        assert dry.outflow.discharge_m3s.tolist() == [0.0] * 6
        assert codes(dry) == []

    def test_a_longer_run_extends_a_shorter_one(self):
        short = self.reach().route(self.flood(), extend_min=40.0)
        long = self.reach().route(self.flood(), extend_min=200.0)

        count = len(short.outflow)
        np.testing.assert_allclose(
            long.outflow.discharge_m3s[:count],
            short.outflow.discharge_m3s,
            rtol=0,
            atol=1e-12,
        )

    def test_the_time_axis_is_extended_until_the_cascade_has_emptied(self):
        result = self.reach().route(self.flood())

        assert codes(result) == ["tail_extended"]
        assert result.outflow.discharge_m3s[-1] < 1e-3 * 90.0
        assert result.storage_end_m3 < 1e-3 * result.volume_in_m3
        assert result.peak_delay_min > 0.0
        assert result.peak_attenuation_pct > 0.0

    def test_the_balance_error_is_the_trapezoid_error_of_the_series_and_falls_with_dt(
        self,
    ):
        # a series that ends in the middle of the flood has a sampling error of
        # (dt^2 / 12) [O'(end) - O'(start)]: second order in the step
        errors = []
        for dt in (10.0, 5.0, 2.5):
            times = np.arange(0.0, 200.0 + dt, dt)
            values = 5.0 + 30.0 * np.exp(-(((times - 100.0) / 30.0) ** 2))
            result = CascadeReach(3.0, k_min=20.0).route(
                Hydrograph.from_step(values, dt), extend_min=0.0
            )
            errors.append(abs(result.balance_error_m3))

        assert errors[0] / errors[1] == pytest.approx(4.0, rel=0.1)
        assert errors[1] / errors[2] == pytest.approx(4.0, rel=0.1)

    def test_a_series_at_rest_at_both_ends_balances_to_the_quadrature_error(self):
        result = self.reach().route(self.flood())

        assert abs(result.balance_error_m3) < 1e-4 * result.volume_in_m3

    def test_the_fft_and_the_direct_convolution_agree(self, monkeypatch):
        inflow = Hydrograph.from_step(random_inflow(5, 300), 3.0)
        direct = self.reach().route(inflow, extend_min=0.0).outflow.discharge_m3s

        monkeypatch.setattr(cascade_module, "_DIRECT_LIMIT", 0)
        blocks = self.reach().route(inflow, extend_min=0.0).outflow.discharge_m3s

        np.testing.assert_allclose(blocks, direct, rtol=0, atol=1e-11)

    def test_a_reach_that_holds_the_water_longer_than_the_series_keeps_the_start(self):
        # a delay of 10^6 min: nothing has come out within a day
        result = CascadeReach(1e6, k_min=1.0).route(
            Hydrograph.from_step([1.0, 5.0, 9.0, 3.0], 60.0),
            initial_outflow_m3s=2.0,
            extend_min=0.0,
        )

        assert result.outflow.discharge_m3s.tolist() == [2.0, 2.0, 2.0, 2.0]
        assert codes(result) == ["tail_truncated"]


class TestParameters:
    def test_the_time_scale_follows_from_the_length_and_the_celerity(self):
        result = CascadeReach(4, length_km=12.0, celerity_m_per_s=1.0).route(
            Hydrograph.from_step([0.0, 10.0, 40.0, 20.0, 0.0], 30.0)
        )
        same = CascadeReach(4, k_min=50.0).route(
            Hydrograph.from_step([0.0, 10.0, 40.0, 20.0, 0.0], 30.0)
        )

        # the travel time 12 km / (1 m/s) = 200 min is shared by 4 reservoirs of 50 min
        assert result.parameters["k_min"] == pytest.approx(50.0)
        assert result.parameters["lag_min"] == pytest.approx(200.0)
        assert result.parameters["length_km"] == 12.0
        assert result.parameters["celerity_m_per_s"] == 1.0
        np.testing.assert_allclose(
            result.outflow.discharge_m3s, same.outflow.discharge_m3s, rtol=1e-12
        )
        assert "length_km" not in same.parameters

    def test_the_parameters_report_the_step_over_the_storage_constant(self):
        parameters = (
            CascadeReach(2.0, k_min=20.0)
            .route(Hydrograph.from_step([1.0, 1.0, 1.0], 5.0))
            .parameters
        )

        assert parameters == {
            "n": 2.0,
            "k_min": 20.0,
            "lag_min": 40.0,
            "timestep_over_k": 0.25,
        }

    @pytest.mark.parametrize(
        ("options", "given", "missing"),
        [
            ({}, [], ["k_min"]),
            ({"length_km": 5.0}, ["length_km"], ["celerity_m_per_s"]),
            (
                {"k_min": 20.0, "length_km": 5.0, "celerity_m_per_s": 1.0},
                ["k_min", "length_km", "celerity_m_per_s"],
                None,
            ),
        ],
        ids=["none", "half", "both"],
    )
    def test_exactly_one_group_of_time_scale_options_is_needed(
        self, options, given, missing
    ):
        with pytest.raises(InvalidParameterError) as caught:
            CascadeReach(3.0, **options)

        details = caught.value.details
        assert details["reason"] == "one_of"
        assert details["groups"] == [["k_min"], ["length_km", "celerity_m_per_s"]]
        assert details["given"] == given
        if missing is not None:
            assert details["missing"] == missing

    @pytest.mark.parametrize(
        ("name", "value", "reason"),
        [
            ("n", 0.0, "exclusive_minimum"),
            ("n", -2.0, "exclusive_minimum"),
            ("n", math.nan, "type"),
            ("n", math.inf, "not_finite"),
            ("n", True, "type"),
            ("k_min", 0.0, "exclusive_minimum"),
            ("k_min", math.inf, "not_finite"),
            ("length_km", -1.0, "exclusive_minimum"),
            ("celerity_m_per_s", 0.0, "exclusive_minimum"),
        ],
    )
    def test_the_numbers_must_be_positive_and_finite(self, name, value, reason):
        options = {"n": 3.0, "k_min": 20.0, "length_km": 5.0, "celerity_m_per_s": 1.0}
        options[name] = value
        if name in ("n", "k_min"):
            options.pop("length_km"), options.pop("celerity_m_per_s")
        else:
            options.pop("k_min")

        with pytest.raises(InvalidParameterError) as caught:
            CascadeReach(**options)

        assert (caught.value.details["option"], caught.value.details["reason"]) == (
            name,
            reason,
        )
