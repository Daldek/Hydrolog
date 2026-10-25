"""Tests of level-pool routing: the published example, oracles, identities and rules.

The references share nothing with the implementation. NEH-630 example 17-1 is compared
with its printed table. A table of constant storage constant is the linear reservoir,
which the Muskingum scheme with ``X = 0`` computes with other code. A tank that drains
through a weir has an exact solution, and a tank that a flood fills is integrated by an
ODE solver. The invariants of a monotone scheme (the outflow stays between the lowest
and the highest flow of the run, the volume balance closes) are checked on random
tables, and the rules for the table and for the time step on hand-made ones.
"""

import math

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.routing import (
    Hydrograph,
    LevelPoolReach,
    MuskingumReach,
    timestep_limit_min,
)
from hydrolog.routing.level_pool import check_rating
from hydrolog.routing.reach import MAX_ORDINATES

from ._routing_reference import (
    CFS_M3S,
    NEH17_1_AVERAGE_INFLOW_CFS,
    NEH17_1_INFLOW_CFS,
    NEH17_1_OUTFLOW_CFS,
    NEH17_1_ROUNDING_CFS,
    NEH17_1_STEP_MIN,
    NEH17_1_TABLE_OUTFLOW_CFS,
    NEH17_1_TABLE_STORAGE_CFS_H,
    NEH17_1_TOLERANCE_CFS,
    NEH17_1_WORKING_STATE_CFS,
)

CFS_H = 3600.0 * CFS_M3S
"""One ft3/s-h in m3."""


def codes(result) -> list[str]:
    return [notice.code for notice in result.notices]


def neh_pool(**options) -> LevelPoolReach:
    """The channel reach of example 17-1 (Table 17-4) in SI."""
    return LevelPoolReach(
        storage_m3=[s * CFS_H for s in NEH17_1_TABLE_STORAGE_CFS_H],
        outflow_m3s=[q * CFS_M3S for q in NEH17_1_TABLE_OUTFLOW_CFS],
        **options,
    )


def neh_flood(inflow_cfs=NEH17_1_INFLOW_CFS) -> Hydrograph:
    return Hydrograph.from_step([q * CFS_M3S for q in inflow_cfs], NEH17_1_STEP_MIN)


def route_neh(inflow_cfs=NEH17_1_INFLOW_CFS, **options):
    """Route example 17-1 on the printed axis (no extension)."""
    return neh_pool(**options).route(neh_flood(inflow_cfs), extend_min=0.0)


class TestNehExample171:
    def test_the_outflow_is_the_printed_table_to_its_rounding(self):
        result = route_neh()

        np.testing.assert_allclose(
            result.outflow.discharge_m3s / CFS_M3S,
            NEH17_1_OUTFLOW_CFS,
            rtol=0,
            atol=NEH17_1_TOLERANCE_CFS,
        )
        assert result.outflow.time_to_peak_min == 180.0
        assert result.outflow.peak_discharge_m3s / CFS_M3S == pytest.approx(
            3827.0, abs=NEH17_1_TOLERANCE_CFS
        )

    def test_the_printed_average_inflows_explain_the_difference(self):
        # Table 17-7 prints an average inflow that ends in .5 rounded up: 4,687.5 as
        # 4,688. Those averages belong to ordinates 1 ft3/s higher at 2.5, 3.5, 4.5
        # and 5.5 h; with them the table is reproduced inside the rounding of its print
        ordinates = [0.0]
        for average in NEH17_1_AVERAGE_INFLOW_CFS[1:]:
            ordinates.append(2.0 * average - ordinates[-1])
        assert ordinates[4:13] == [5000, 4376, 3750, 3126, 2500, 1876, 1250, 626, 0]

        result = route_neh(ordinates)

        np.testing.assert_allclose(
            result.outflow.discharge_m3s / CFS_M3S,
            NEH17_1_OUTFLOW_CFS,
            rtol=0,
            atol=NEH17_1_ROUNDING_CFS,
        )

    def test_the_storage_at_the_peak_follows_from_the_printed_working_state(self):
        # S = (S/dt + O/2 - O/2) dt at 3.0 h, from the printed 9,056 and 3,827 ft3/s
        result = route_neh()

        state, outflow = NEH17_1_WORKING_STATE_CFS[6], NEH17_1_OUTFLOW_CFS[6]
        expected = (state - outflow / 2.0) * NEH17_1_STEP_MIN * 60.0 * CFS_M3S
        assert result.parameters["storage_peak_m3"] == pytest.approx(
            expected, abs=2.0 * NEH17_1_STEP_MIN * 60.0 * CFS_M3S
        )
        assert result.parameters["storage_peak_time_min"] == 180.0
        assert result.storage_start_m3 == 0.0

    def test_the_published_step_is_inside_the_limit_of_the_table(self):
        result = route_neh()

        # the flows up to the 5,000 ft3/s peak use the rows to 5,000: the shortest
        # K = dS/dO is that of 50 to 150 ft3/s, (136.9 - 71.8) / (150 - 50) = 0.651 h,
        # so the step may be 2 K = 78.12 min; the whole table gives 60.83 min
        assert result.parameters["timestep_limit_min"] == pytest.approx(78.12)
        assert result.parameters["substeps"] == 1
        assert timestep_limit_min(
            [s * CFS_H for s in NEH17_1_TABLE_STORAGE_CFS_H],
            [q * CFS_M3S for q in NEH17_1_TABLE_OUTFLOW_CFS],
        ) == pytest.approx(120.0 * (7131.9 - 5611.1) / 3000.0)
        assert codes(result) == [
            "tail_truncated"
        ]  # extend_min 0 keeps the printed axis
        assert abs(result.balance_error_m3) < 1e-9 * result.inflow.volume_m3


class TestLinearReservoirIdentity:
    @pytest.mark.parametrize("subreaches", [1, 3, 6])
    def test_a_table_of_constant_storage_constant_is_the_linear_reservoir_scheme(
        self, subreaches
    ):
        k_min = 40.0
        rng = np.random.default_rng(7)
        inflow = Hydrograph.from_step(rng.uniform(2.0, 45.0, 30), 10.0)
        pool = LevelPoolReach(
            storage_m3=[0.0, k_min * 60.0 * 50.0],
            outflow_m3s=[0.0, 50.0],
            subreaches=subreaches,
        )

        by_table = pool.route(inflow, initial_outflow_m3s=5.0, extend_min=0.0)
        by_scheme = MuskingumReach(k_min=k_min, x=0.0, subreaches=subreaches).route(
            inflow, initial_outflow_m3s=5.0, extend_min=0.0
        )

        np.testing.assert_allclose(
            by_table.outflow.discharge_m3s,
            by_scheme.outflow.discharge_m3s,
            rtol=1e-12,
        )
        assert by_table.storage_start_m3 == pytest.approx(by_scheme.storage_start_m3)
        assert by_table.storage_end_m3 == pytest.approx(by_scheme.storage_end_m3)
        assert codes(by_table) == codes(by_scheme) == ["tail_truncated"]


class TestOracles:
    AREA, WEIR = 50_000.0, 20.0
    """A tank of 50,000 m2 with a weir ``O = 20 h^1.5``."""

    def pool(self) -> LevelPoolReach:
        depth = np.linspace(0.0, 3.0, 6001)
        return LevelPoolReach(self.AREA * depth, self.WEIR * depth**1.5)

    def test_a_tank_draining_through_a_weir_follows_its_exact_solution(self):
        # dh/dt = -C h^1.5 / A has the solution h = (h0^-1/2 + C t / (2 A))^-2
        start = 2.0
        errors = []
        for step_min in (10.0, 5.0, 2.5):
            dry = Hydrograph.from_step(np.zeros(int(120 / step_min) + 1), step_min)
            result = self.pool().route(
                dry, initial_outflow_m3s=self.WEIR * start**1.5, extend_min=0.0
            )
            seconds = dry.times_min * 60.0
            exact = self.WEIR * (
                start**-0.5 + self.WEIR * seconds / (2.0 * self.AREA)
            ) ** (-3.0)
            errors.append(np.abs(result.outflow.discharge_m3s - exact).max())

        # second order in the step, and small: 0.04 m3/s of 56.6 at the 2.5 min step
        assert errors[-1] < 0.05
        for coarse, fine in zip(errors, errors[1:], strict=False):
            assert 3.5 < coarse / fine < 4.5

    def test_a_tank_filled_by_a_flood_follows_the_integrated_equation(self):
        knots, flows = [0, 30, 90, 180, 240], [10.0, 10.0, 70.0, 10.0, 10.0]
        start = (flows[0] / self.WEIR) ** (1.0 / 1.5)

        def rate(seconds, level):
            inflow = np.interp(seconds / 60.0, knots, flows)
            return [(inflow - self.WEIR * max(level[0], 0.0) ** 1.5) / self.AREA]

        errors = []
        for step_min in (10.0, 5.0, 2.5):
            times = np.arange(0.0, 240.0 + step_min / 2.0, step_min)
            flood = Hydrograph(times, np.interp(times, knots, flows))
            result = self.pool().route(flood, extend_min=0.0)
            solved = solve_ivp(
                rate,
                [0.0, 240.0 * 60.0],
                [start],
                t_eval=times * 60.0,
                rtol=1e-11,
                atol=1e-13,
                max_step=30.0,
            )
            reference = self.WEIR * np.maximum(solved.y[0], 0.0) ** 1.5
            errors.append(np.abs(result.outflow.discharge_m3s - reference).max())

        assert errors[-1] < 0.03
        for coarse, fine in zip(errors, errors[1:], strict=False):
            assert 3.5 < coarse / fine < 4.5


def random_table(seed: int):
    """A random table with a dead zone, and a flood that stays inside it."""
    rng = np.random.default_rng(seed)
    dead = int(rng.integers(1, 3))
    rows = int(rng.integers(2, 9))
    outflow = np.concatenate([np.zeros(dead), np.cumsum(rng.uniform(0.5, 20.0, rows))])
    storage = np.cumsum(rng.uniform(1e2, 5e4, len(outflow)))
    storage -= storage[0]
    peak = rng.uniform(0.2, 0.95) * outflow[-1]
    base = rng.uniform(0.0, 0.15) * peak
    times = np.linspace(0.0, 1.0, int(rng.integers(6, 40)))
    centre, width = rng.uniform(0.2, 0.5), rng.uniform(0.08, 0.3)
    flows = base + (peak - base) * np.exp(-(((times - centre) / width) ** 2))
    return storage, outflow, flows


class TestMonotoneScheme:
    @pytest.mark.parametrize("subreaches", [1, 2])
    @pytest.mark.parametrize("fraction", [0.5, 1.0])
    @pytest.mark.parametrize("seed", range(40))
    def test_a_step_inside_the_limit_keeps_the_outflow_between_the_flows_of_the_run(
        self, seed, fraction, subreaches
    ):
        storage, outflow, flows = random_table(seed)
        limit = timestep_limit_min(
            storage,
            outflow,
            subreaches=subreaches,
            outflow_floor_m3s=flows.min(),
            outflow_cap_m3s=flows.max(),
        )
        step = min(120.0, fraction * limit) if math.isfinite(limit) else 60.0
        pool = LevelPoolReach(storage, outflow, subreaches=subreaches)

        result = pool.route(Hydrograph.from_step(flows, step))

        routed = result.outflow.discharge_m3s
        assert "timestep_refined" not in codes(result)
        assert routed.min() >= flows.min() - 1e-9
        assert routed.max() <= flows.max() + 1e-9
        assert abs(result.balance_error_m3) <= 1e-9 * result.inflow.volume_m3

    @pytest.mark.parametrize("seed", range(40))
    def test_a_longer_step_is_divided_and_the_outflow_stays_between_the_flows(
        self, seed
    ):
        storage, outflow, flows = random_table(seed)
        limit = timestep_limit_min(
            storage,
            outflow,
            outflow_floor_m3s=flows.min(),
            outflow_cap_m3s=flows.max(),
        )
        if not math.isfinite(limit) or limit > 40.0:
            pytest.skip("the table allows any step of the test")
        pool = LevelPoolReach(storage, outflow)

        result = pool.route(Hydrograph.from_step(flows, 2.5 * limit))

        routed = result.outflow.discharge_m3s
        assert "timestep_refined" in codes(result)
        assert result.parameters["substeps"] == 3
        assert routed.min() >= flows.min() - 1e-9
        assert routed.max() <= flows.max() + 1e-9

    def test_a_step_that_a_whole_curve_rule_lets_through_is_divided_on_a_kinked_table(
        self,
    ):
        # K is 100 s up to 20 m3/s and 5 s above. The ratio S/O at 70 m3/s is 32 s, so
        # the rule of NEH-630 for the whole curve allows a step of 64 s; a 1 min step
        # answers a rise of the inflow from 40 to 60 m3/s with a sawtooth that
        # overshoots 60 (62.0, 58.5, 61.0...). The steep part needs 10 s: the step is
        # divided, and the outflow rises to 60 and stays
        pool = LevelPoolReach([0.0, 2000.0, 2250.0], [0.0, 20.0, 70.0])
        rise = Hydrograph.from_step([40.0, 40.0] + [60.0] * 10, 1.0)

        result = pool.route(rise, extend_min=0.0)

        routed = result.outflow.discharge_m3s
        assert result.parameters["timestep_limit_min"] == pytest.approx(10.0 / 60.0)
        assert result.parameters["substeps"] == 6
        assert "timestep_refined" in codes(result)
        assert routed.max() <= 60.0 + 1e-9
        assert (np.diff(routed) >= -1e-9).all()


class TestStepRule:
    def test_a_table_of_constant_storage_constant_allows_twice_k_over_n(self):
        # K = 72 s: 100 m3/s hold 7,200 m3
        for subreaches, expected in ((1, 144.0), (3, 48.0)):
            limit = timestep_limit_min(
                [0.0, 7200.0], [0.0, 100.0], subreaches=subreaches
            )
            assert limit == pytest.approx(expected / 60.0)

    @pytest.mark.parametrize(
        ("options", "seconds"),
        [
            ({}, 2.0),  # K of the first segment, 100 m3 per 100 m3/s
            ({"outflow_cap_m3s": 50.0}, 2.0),
            ({"outflow_floor_m3s": 150.0}, 18.0),  # starts in the segment of 9 s
            ({"outflow_floor_m3s": 150.0, "outflow_cap_m3s": 150.0}, 18.0),
            ({"outflow_floor_m3s": 250.0, "outflow_cap_m3s": 300.0}, 40.0),
            ({"outflow_floor_m3s": 300.0}, math.inf),  # at the last row
            ({"outflow_cap_m3s": 0.0}, math.inf),  # the pool never moves
        ],
    )
    def test_only_the_segments_between_the_flows_of_the_run_count(
        self, options, seconds
    ):
        storage = [0.0, 100.0, 1000.0, 3000.0]  # K = 1, 9 and 20 s
        outflow = [0.0, 100.0, 200.0, 300.0]

        limit = timestep_limit_min(storage, outflow, **options)

        assert limit == pytest.approx(seconds / 60.0)

    def test_a_flat_stretch_rests_at_its_highest_storage_and_is_not_a_segment(self):
        # no outflow up to 50 m3, then 10 m3/s per 100 m3: K = 10 s from the crest
        assert timestep_limit_min(
            [0.0, 50.0, 150.0], [0.0, 0.0, 10.0]
        ) == pytest.approx(20.0 / 60.0)

    def test_a_segment_without_storage_is_a_limit_of_zero_and_refuses_the_run(self):
        storage, outflow = [0.0, 100.0, 100.0], [0.0, 10.0, 20.0]
        assert timestep_limit_min(storage, outflow) == 0.0
        assert timestep_limit_min(storage, outflow, outflow_cap_m3s=10.0) > 0.0
        pool = LevelPoolReach(storage, outflow)

        with pytest.raises(InvalidParameterError) as caught:
            pool.route(Hydrograph.from_step([0.0, 15.0, 0.0], 1.0))
        assert caught.value.details["option"] == "storage_m3"
        assert caught.value.details["reason"] == "working_curve"
        # the same table is fine for a flood that stays below the vertical segment
        assert pool.route(Hydrograph.from_step([0.0, 8.0, 0.0], 1.0)).outflow


def linear_pool(**options) -> LevelPoolReach:
    """K = 5 min: a step of 10 min or less is allowed."""
    return LevelPoolReach([0.0, 30_000.0], [0.0, 100.0], **options)


class TestTimeStepDivision:
    def test_a_longer_step_is_divided_into_the_fewest_equal_sub_steps(self):
        flood = Hydrograph.from_step([0.0, 20.0, 60.0, 30.0, 10.0, 0.0], 30.0)

        result = linear_pool().route(flood)

        assert result.parameters["substeps"] == 3
        assert result.parameters["timestep_limit_min"] == pytest.approx(10.0)
        notice = next(n for n in result.notices if n.code == "timestep_refined")
        assert notice.level == "info"
        assert "3 sub-steps of 10 min" in notice.message

    def test_the_divided_run_is_the_run_on_the_refined_hydrograph_read_back(self):
        flood = Hydrograph.from_step([0.0, 20.0, 60.0, 30.0, 10.0, 0.0], 30.0)

        divided = linear_pool().route(flood, extend_min=0.0)
        fine = linear_pool().route(flood.refined(3), extend_min=0.0)

        assert "timestep_refined" not in codes(fine)
        np.testing.assert_allclose(
            divided.outflow.discharge_m3s,
            fine.outflow.coarsened(3).discharge_m3s,
            rtol=1e-12,
        )
        assert divided.storage_end_m3 == pytest.approx(fine.storage_end_m3)

    def test_a_step_at_the_limit_is_not_divided_and_just_above_it_is(self):
        at_limit = Hydrograph.from_step([0.0, 20.0, 60.0, 0.0], 10.0)
        above = Hydrograph.from_step([0.0, 20.0, 60.0, 0.0], 10.0 * (1.0 + 1e-6))

        assert codes(linear_pool().route(at_limit)).count("timestep_refined") == 0
        divided = linear_pool().route(above)
        assert divided.parameters["substeps"] == 2

    def test_a_step_needing_more_than_100_parts_is_refused(self):
        # K = 0.6 s: 0.02 min is the longest step, a 10 min step would need 500 parts
        pool = LevelPoolReach([0.0, 60.0], [0.0, 100.0])

        with pytest.raises(InvalidParameterError) as caught:
            pool.route(Hydrograph.from_step([0.0, 20.0, 60.0, 0.0], 10.0))

        details = caught.value.details
        assert (details["option"], details["reason"]) == (
            "times_min",
            "unstable_timestep",
        )
        assert details["maximum_timestep_min"] == pytest.approx(0.02)
        assert (details["substeps"], details["maximum_substeps"]) == (500, 100)

    def test_a_divided_series_of_more_than_the_ordinate_limit_is_refused(self):
        # 20,000 ordinates divided by 60 are 1.2 million
        pool = LevelPoolReach([0.0, 500.0], [0.0, 100.0])  # K = 5 s: 10 s steps
        flood = Hydrograph.from_step(np.full(20_000, 10.0), 10.0)

        with pytest.raises(InvalidParameterError) as caught:
            pool.route(flood, extend_min=0.0)

        assert caught.value.details["reason"] == "unstable_timestep"
        assert caught.value.details["maximum"] == MAX_ORDINATES


class TestInitialState:
    TABLE = {"storage_m3": [0.0, 1000.0, 5000.0], "outflow_m3s": [0.0, 10.0, 30.0]}

    def test_a_steady_inflow_is_kept_and_its_storage_read_from_the_table(self):
        pool = LevelPoolReach(**self.TABLE)

        result = pool.route(Hydrograph.from_step([20.0] * 6, 1.0))

        np.testing.assert_allclose(result.outflow.discharge_m3s, 20.0, rtol=1e-12)
        # 1,000 m3 at 10 m3/s and 5,000 at 30: 3,000 at 20
        assert result.storage_start_m3 == pytest.approx(3000.0)
        assert result.storage_end_m3 == pytest.approx(3000.0)
        assert result.notices == []

    def test_an_outflow_above_the_inflow_drains_the_pool_and_the_balance_closes(self):
        pool = LevelPoolReach(**self.TABLE)

        result = pool.route(
            Hydrograph.from_step([5.0] * 12, 1.0), initial_outflow_m3s=25.0
        )

        routed = result.outflow.discharge_m3s
        assert routed[0] == 25.0
        assert (np.diff(routed) < 0.0).all()
        assert routed[-1] > 5.0
        assert result.storage_end_m3 < result.storage_start_m3
        assert abs(result.balance_error_m3) < 1e-9 * result.outflow.volume_m3

    def test_a_pool_with_a_crest_starts_full_to_it_and_returns_to_it(self):
        # no outflow up to 200,000 m3, then 10 m3/s per 100,000 m3
        pool = LevelPoolReach([0.0, 2e5, 3e5, 5e5], [0.0, 0.0, 10.0, 40.0])
        flood = Hydrograph.from_step([0.0, 5.0, 15.0, 12.0, 6.0, 2.0, 0.0], 20.0)

        result = pool.route(flood)

        assert result.storage_start_m3 == pytest.approx(2e5)
        assert result.storage_end_m3 == pytest.approx(2e5, abs=1e-3 * flood.volume_m3)
        assert result.outflow.peak_discharge_m3s < flood.peak_discharge_m3s
        assert abs(result.balance_error_m3) < 1e-9 * flood.volume_m3
        assert "tail_truncated" not in codes(result)

    @pytest.mark.parametrize(
        ("initial", "reason", "bound"),
        [(31.0, "maximum", "maximum"), (0.5, "minimum", "minimum")],
    )
    def test_an_initial_outflow_outside_the_table_is_a_validation_error(
        self, initial, reason, bound
    ):
        pool = LevelPoolReach([0.0, 100.0, 500.0], [1.0, 10.0, 30.0])
        flood = Hydrograph.from_step([10.0, 12.0, 10.0], 1.0)

        with pytest.raises(InvalidParameterError) as caught:
            pool.route(flood, initial_outflow_m3s=initial)

        details = caught.value.details
        assert (details["option"], details["reason"]) == ("initial_outflow_m3s", reason)
        assert details[bound] in (1.0, 30.0)

    def test_the_first_inflow_ordinate_is_the_default_initial_outflow(self):
        pool = LevelPoolReach([0.0, 100.0, 500.0], [1.0, 10.0, 30.0])

        with pytest.raises(InvalidParameterError) as caught:
            pool.route(Hydrograph.from_step([40.0, 12.0, 10.0], 1.0))

        assert caught.value.details["option"] == "initial_outflow_m3s"
        assert caught.value.details["value"] == 40.0


class TestTableRange:
    POOL = LevelPoolReach([0.0, 36_000.0], [0.0, 10.0])

    def test_a_flood_that_fills_the_reservoir_beyond_the_table_is_a_calculation_error(
        self,
    ):
        flood = Hydrograph.from_step([0.0, 20.0, 20.0, 20.0, 20.0, 0.0], 60.0)

        with pytest.raises(CalculationError) as caught:
            self.POOL.route(flood)

        error = caught.value
        assert error.code == "calculation_error"
        assert error.details["reason"] == "table_exceeded"
        assert error.details["maximum_outflow_m3s"] == 10.0
        assert 0.0 < error.details["time_min"] <= flood.duration_min
        assert "Extend the table" in error.hint

    def test_a_flow_that_just_fills_the_table_is_routed(self):
        result = self.POOL.route(Hydrograph.from_step([10.0] * 5, 60.0))

        np.testing.assert_allclose(result.outflow.discharge_m3s, 10.0, rtol=1e-12)
        assert result.storage_end_m3 == pytest.approx(36_000.0)

    def test_an_inflow_that_lets_the_pool_drain_below_the_table_is_a_calculation_error(
        self,
    ):
        # the table starts at 5 m3/s: a long dry spell takes the pool below it
        pool = LevelPoolReach([0.0, 18_000.0, 36_000.0], [5.0, 10.0, 15.0])
        flood = Hydrograph.from_step([10.0, 8.0, 2.0, 0.0, 0.0, 0.0, 0.0], 60.0)

        with pytest.raises(CalculationError) as caught:
            pool.route(flood, extend_min=0.0)

        assert caught.value.details["reason"] == "table_emptied"
        assert caught.value.details["minimum_outflow_m3s"] == 5.0

    def test_the_sub_reach_that_fails_is_named(self):
        flood = Hydrograph.from_step([0.0, 30.0, 30.0, 30.0, 0.0], 60.0)

        with pytest.raises(CalculationError) as caught:
            LevelPoolReach([0.0, 36_000.0], [0.0, 10.0], subreaches=2).route(flood)

        assert "sub-reach 1 of 2" in str(caught.value)


class TestSubreaches:
    def test_more_sub_reaches_attenuate_less_with_the_same_storage_at_rest(self):
        peaks = []
        for subreaches in (1, 2, 3):
            result = neh_pool(subreaches=subreaches).route(
                neh_flood(), initial_outflow_m3s=100.0 * CFS_M3S, extend_min=0.0
            )
            peaks.append(result.outflow.peak_discharge_m3s)
            # the storage at rest is the table's, whatever the division
            assert result.storage_start_m3 == pytest.approx(
                (71.8 + (100.0 - 50.0) / 100.0 * (136.9 - 71.8)) * CFS_H
            )
            assert result.parameters["subreaches"] == subreaches

        assert peaks[0] < peaks[1] < peaks[2]

    def test_a_division_that_makes_the_step_too_long_divides_the_step(self):
        # each of 3 sub-reaches holds a third: the limit falls from 78.12 to 26.04 min
        result = neh_pool(subreaches=3).route(neh_flood(), extend_min=0.0)

        assert result.parameters["timestep_limit_min"] == pytest.approx(78.12 / 3.0)
        assert result.parameters["substeps"] == 2
        assert "timestep_refined" in codes(result)

    @pytest.mark.parametrize("value", [0, -1, 2.5, True, "2"])
    def test_the_number_of_sub_reaches_is_a_whole_number_of_at_least_one(self, value):
        with pytest.raises(InvalidParameterError) as caught:
            LevelPoolReach([0.0, 1.0], [0.0, 1.0], subreaches=value)

        assert caught.value.details["option"] == "subreaches"


class TestDatum:
    def test_the_datum_of_the_storage_changes_nothing_but_the_storage(self):
        table = {"storage_m3": [0.0, 1.8e4, 9.0e4], "outflow_m3s": [0.0, 10.0, 40.0]}
        shifted = {**table, "storage_m3": [s + 5e6 for s in table["storage_m3"]]}
        flood = Hydrograph.from_step([2.0, 12.0, 30.0, 18.0, 8.0, 3.0, 2.0], 30.0)

        base = LevelPoolReach(**table).route(flood)
        moved = LevelPoolReach(**shifted).route(flood)

        np.testing.assert_allclose(
            moved.outflow.discharge_m3s, base.outflow.discharge_m3s, rtol=1e-9
        )
        assert moved.storage_start_m3 - base.storage_start_m3 == pytest.approx(5e6)
        assert moved.storage_end_m3 - base.storage_end_m3 == pytest.approx(5e6)
        assert moved.parameters["timestep_limit_min"] == pytest.approx(
            base.parameters["timestep_limit_min"]
        )


class TestStage:
    TABLE = {
        "storage_m3": [0.0, 4e4, 1.2e5, 2.4e5],
        "outflow_m3s": [0.0, 5.0, 20.0, 60.0],
        "stage_m": [100.0, 101.0, 102.0, 103.0],
    }

    def test_the_peak_stage_is_the_stage_of_the_peak_storage(self):
        flood = Hydrograph.from_step([0.0, 8.0, 30.0, 26.0, 14.0, 6.0, 2.0], 30.0)

        result = LevelPoolReach(**self.TABLE).route(flood)

        peak = result.parameters["storage_peak_m3"]
        expected = float(
            np.interp(peak, self.TABLE["storage_m3"], self.TABLE["stage_m"])
        )
        assert result.parameters["stage_peak_m"] == pytest.approx(expected)
        assert (
            result.parameters["stage_peak_time_min"]
            == result.parameters["storage_peak_time_min"]
        )
        assert 100.0 < expected < 103.0

    def test_without_a_stage_the_result_has_none(self):
        table = {k: v for k, v in self.TABLE.items() if k != "stage_m"}

        result = LevelPoolReach(**table).route(
            Hydrograph.from_step([1.0, 6.0, 1.0], 30.0)
        )

        assert "stage_peak_m" not in result.parameters
        assert "stage_peak_time_min" not in result.parameters

    def test_the_peak_stage_does_not_depend_on_the_time_step_division(self):
        flood = Hydrograph.from_step([0.0, 8.0, 30.0, 26.0, 14.0, 6.0, 2.0], 30.0)

        coarse = LevelPoolReach(**self.TABLE).route(flood)
        fine = LevelPoolReach(**self.TABLE).route(flood.refined(4))

        assert coarse.parameters["stage_peak_m"] == pytest.approx(
            fine.parameters["stage_peak_m"], abs=0.05
        )


class TestReachContract:
    def test_a_longer_run_extends_a_shorter_one(self):
        pool = neh_pool()
        short = pool.route(neh_flood(NEH17_1_INFLOW_CFS[:14]), extend_min=0.0)
        long = pool.route(neh_flood(NEH17_1_INFLOW_CFS), extend_min=0.0)

        np.testing.assert_allclose(
            long.outflow.discharge_m3s[:14],
            short.outflow.discharge_m3s,
            rtol=1e-12,
            atol=1e-12,
        )

    def test_the_tail_is_extended_until_the_pool_has_released_the_flood(self):
        pool = neh_pool()

        result = pool.route(neh_flood())

        assert "tail_extended" in codes(result)
        assert "tail_truncated" not in codes(result)
        routed = result.outflow.discharge_m3s
        assert routed[-1] == pytest.approx(0.0, abs=1e-3 * routed.max())
        assert abs(result.balance_error_m3) < 1e-9 * result.inflow.volume_m3


class TestTable:
    @pytest.mark.parametrize(
        ("columns", "option", "reason"),
        [
            (
                {"storage_m3": [0, 10], "outflow_m3s": [0, 1, 2]},
                "outflow_m3s",
                "length_mismatch",
            ),
            (
                {
                    "storage_m3": [0, 10, 20],
                    "outflow_m3s": [0, 1, 2],
                    "stage_m": [1, 2],
                },
                "stage_m",
                "length_mismatch",
            ),
            ({"storage_m3": [0], "outflow_m3s": [0]}, "storage_m3", "too_short"),
            (
                {"storage_m3": [0, math.nan], "outflow_m3s": [0, 1]},
                "storage_m3",
                "not_finite",
            ),
            (
                {"storage_m3": [0, 10], "outflow_m3s": [0, math.inf]},
                "outflow_m3s",
                "not_finite",
            ),
            ({"storage_m3": [-1, 10], "outflow_m3s": [0, 1]}, "storage_m3", "negative"),
            (
                {"storage_m3": [0, 10], "outflow_m3s": [-1, 1]},
                "outflow_m3s",
                "negative",
            ),
            (
                {"storage_m3": [0, 10, 5], "outflow_m3s": [0, 1, 2]},
                "storage_m3",
                "decreasing",
            ),
            (
                {"storage_m3": [0, 10, 20], "outflow_m3s": [0, 2, 1]},
                "outflow_m3s",
                "decreasing",
            ),
            (
                {
                    "storage_m3": [0, 10, 20],
                    "outflow_m3s": [0, 1, 2],
                    "stage_m": [5, 6, 4],
                },
                "stage_m",
                "decreasing",
            ),
            (
                {"storage_m3": [0, 10, 10], "outflow_m3s": [0, 1, 1]},
                "outflow_m3s",
                "repeated_row",
            ),
            (
                {"storage_m3": [[0, 1], [2, 3]], "outflow_m3s": [[0, 1], [2, 3]]},
                "storage_m3",
                "type",
            ),
            ({"storage_m3": ["a", "b"], "outflow_m3s": [0, 1]}, "storage_m3", "type"),
        ],
    )
    def test_a_bad_table_is_refused_with_its_option_and_reason(
        self, columns, option, reason
    ):
        with pytest.raises(InvalidParameterError) as caught:
            LevelPoolReach(**columns)

        assert (caught.value.details["option"], caught.value.details["reason"]) == (
            option,
            reason,
        )

    def test_the_first_offending_row_is_reported(self):
        problem = check_rating(
            np.array([0.0, 10.0, 20.0, 15.0]),
            np.array([0.0, 1.0, 2.0, 3.0]),
        )

        assert problem is not None
        assert (problem.option, problem.reason, problem.details["index"]) == (
            "storage_m3",
            "decreasing",
            3,
        )

    def test_a_dead_zone_and_a_flat_stage_are_valid(self):
        problem = check_rating(
            np.array([0.0, 50.0, 150.0]),
            np.array([0.0, 0.0, 10.0]),
            np.array([100.0, 100.0, 101.0]),
        )

        assert problem is None

    def test_the_table_is_kept_read_only(self):
        pool = LevelPoolReach([0.0, 1.0], [0.0, 1.0], stage_m=[5.0, 6.0])

        for column in (pool.storage_m3, pool.outflow_m3s, pool.stage_m):
            assert not column.flags.writeable
