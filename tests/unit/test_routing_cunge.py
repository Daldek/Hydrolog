"""Tests of Muskingum-Cunge: NEH-630 example 17-4, identities, the grid rules."""

import math

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing import Hydrograph, MuskingumCungeReach, MuskingumReach
from hydrolog.routing._kernels import (
    linear_reservoir_coefficients,
    muskingum_coefficients,
    three_point,
)
from hydrolog.routing.cunge import MIN_RISE_STEPS, rise_steps
from hydrolog.routing.muskingum import MAX_SUBSTEPS

from ._routing_reference import (
    CFS_M3S,
    FT_M,
    NEH17_4_CELERITY_FT_PER_S,
    NEH17_4_COEFFICIENTS,
    NEH17_4_COURANT,
    NEH17_4_DX_FT,
    NEH17_4_GRID_REYNOLDS,
    NEH17_4_GRID_REYNOLDS_LIMIT,
    NEH17_4_INFLOW_CFS,
    NEH17_4_K_S,
    NEH17_4_LENGTH_FT,
    NEH17_4_OUTFLOW_CFS,
    NEH17_4_PEAK_OUTFLOW_CFS,
    NEH17_4_PEAK_TIME_H,
    NEH17_4_ROUNDING_CFS,
    NEH17_4_SECTION,
    NEH17_4_SLOPE,
    NEH17_4_START_MIN,
    NEH17_4_STEP_MIN,
    NEH17_4_TOP_WIDTH_FT,
    NEH17_4_X,
)


def codes(result) -> list[str]:
    return [notice.code for notice in result.notices]


def neh_inflow() -> Hydrograph:
    """The 37 ordinates of Table 17-18 in m3/s, at 6 min from 10.0 h."""
    return Hydrograph.from_step(
        np.array(NEH17_4_INFLOW_CFS) * CFS_M3S,
        NEH17_4_STEP_MIN,
        start_min=NEH17_4_START_MIN,
    )


def neh_reach(**options) -> MuskingumCungeReach:
    """Example 17-4 with the celerity and the top width of the text."""
    arguments = {
        "length_km": NEH17_4_LENGTH_FT * FT_M / 1000.0,
        "slope_m_per_m": NEH17_4_SLOPE,
        "celerity_m_per_s": NEH17_4_CELERITY_FT_PER_S * FT_M,
        "top_width_m": NEH17_4_TOP_WIDTH_FT * FT_M,
        **options,
    }
    return MuskingumCungeReach(**arguments)


def neh_outflow_cfs(result) -> np.ndarray:
    return result.outflow.discharge_m3s / CFS_M3S


def triangle(peak: float, rise: int, fall: int, step_min: float) -> Hydrograph:
    """A dry start, a straight rise of ``rise`` steps, a straight fall and a dry end."""
    values = np.concatenate(
        [
            [0.0],
            np.linspace(0.0, peak, rise + 1)[1:],
            np.linspace(peak, 0.0, fall + 1)[1:],
            np.zeros(3),
        ]
    )
    return Hydrograph.from_step(values, step_min)


class TestPublishedExample:
    def test_the_printed_coefficients_reproduce_the_table_to_its_rounding(self):
        # The text computes O2 = C1 I1 + C2 I2 + C3 O1 with C = 0.028, 0.355, 0.617;
        # run as printed, the loop gives the printed table to half of its last digit.
        previous, current, outflow = NEH17_4_COEFFICIENTS

        series = three_point(
            NEH17_4_INFLOW_CFS, current, previous, outflow, initial_outflow=0.0
        )

        difference = np.abs(series - NEH17_4_OUTFLOW_CFS)
        assert difference.max() < NEH17_4_ROUNDING_CFS

    def test_the_parameters_are_those_of_the_worked_example(self):
        parameters = neh_reach().route(neh_inflow(), extend_min=0.0).parameters

        assert parameters["k_min"] * 60.0 == pytest.approx(NEH17_4_K_S, abs=0.005)
        assert parameters["x"] == pytest.approx(NEH17_4_X, abs=5e-4)
        assert parameters["courant_number"] == pytest.approx(NEH17_4_COURANT, abs=5e-4)
        assert parameters["grid_reynolds_number"] == pytest.approx(
            NEH17_4_GRID_REYNOLDS, abs=1e-3
        )
        assert parameters["grid_reynolds_limit"] == pytest.approx(
            NEH17_4_GRID_REYNOLDS_LIMIT, abs=5e-3
        )
        assert parameters["dx_reference_m"] / FT_M == pytest.approx(
            NEH17_4_DX_FT, abs=0.5
        )
        # one distance step: the 2,600 ft reach is shorter than dx_c = 2,735 ft
        assert parameters["subreaches"] == 1
        assert parameters["dx_m"] / FT_M == pytest.approx(NEH17_4_LENGTH_FT)
        assert parameters["substeps"] == 1

    def test_the_weights_agree_with_the_printed_coefficients(self):
        parameters = neh_reach().route(neh_inflow(), extend_min=0.0).parameters

        previous, current, outflow = NEH17_4_COEFFICIENTS
        # the text rounds K, X and the weights to three decimals
        assert parameters["c_previous"] == pytest.approx(previous, abs=6e-4)
        assert parameters["c_current"] == pytest.approx(current, abs=1e-3)
        assert parameters["c_outflow"] == pytest.approx(outflow, abs=6e-4)
        assert sum(
            parameters[name] for name in ("c_previous", "c_current", "c_outflow")
        ) == pytest.approx(1.0, abs=1e-14)

    def test_the_outflow_agrees_with_table_17_18_within_the_rounded_coefficients(self):
        # The exact weights differ from the printed ones by up to 0.0006, which moves
        # the outflow by up to 0.24 ft3/s (0.04 % of the peak): 0.25 is the bound.
        result = neh_reach().route(neh_inflow(), extend_min=0.0)

        outflow = neh_outflow_cfs(result)

        assert np.abs(outflow - NEH17_4_OUTFLOW_CFS).max() < 0.25
        assert outflow.max() == pytest.approx(NEH17_4_PEAK_OUTFLOW_CFS, abs=0.1)
        assert result.outflow.time_to_peak_min / 60.0 == pytest.approx(
            NEH17_4_PEAK_TIME_H
        )

    def test_a_routed_hydrograph_that_rises_in_twelve_steps_needs_no_refinement(self):
        result = neh_reach().route(neh_inflow(), extend_min=0.0)

        assert rise_steps(neh_inflow().discharge_m3s) >= MIN_RISE_STEPS
        assert codes(result) == ["tail_truncated"]

    def test_the_volume_balance_closes(self):
        result = neh_reach().route(neh_inflow(), extend_min=0.0)

        assert abs(result.balance_error_m3) < 1e-9 * result.volume_in_m3

    def test_the_section_of_the_example_gives_the_same_reach_to_the_celerity(self):
        # b = 15 ft, 2:1, n = 0.04: Manning's dQ/dA is 2 % below the text's m Q / A,
        # so the reach is a little slower and the table is matched to 2.5 ft3/s (0.4 %)
        reach = neh_reach(
            celerity_m_per_s=None,
            top_width_m=None,
            manning_n=NEH17_4_SECTION["manning_n"],
            bottom_width_m=NEH17_4_SECTION["bottom_width_ft"] * FT_M,
            side_slope_m_per_m=NEH17_4_SECTION["side_slope"],
        )

        result = reach.route(neh_inflow(), extend_min=0.0)

        assert np.abs(neh_outflow_cfs(result) - NEH17_4_OUTFLOW_CFS).max() < 2.5
        assert result.parameters["celerity_m_per_s"] / FT_M == pytest.approx(
            NEH17_4_CELERITY_FT_PER_S, rel=0.03
        )
        assert result.parameters["top_width_m"] / FT_M == pytest.approx(
            NEH17_4_TOP_WIDTH_FT, rel=2e-3
        )


class TestIdentities:
    def test_with_cunge_parameters_in_range_it_is_the_muskingum_reach(self):
        # D = 1000 m, c dt = 2400 m: one step of 1667 m has X = 0.2 and K = 833 s; the
        # window of Muskingum (X >= 0) holds the same K and X for one sub-reach
        cunge = MuskingumCungeReach(
            length_km=5.0 / 3.0,
            slope_m_per_m=0.001,
            celerity_m_per_s=2.0,
            top_width_m=10.0,
            reference_discharge_m3s=20.0,
        )
        inflow = triangle(20.0, 14, 30, 20.0)

        routed = cunge.route(inflow, extend_min=200.0)
        parameters = routed.parameters
        muskingum = MuskingumReach(
            k_min=parameters["k_min"],
            x=parameters["x"],
            subreaches=parameters["subreaches"],
        ).route(inflow, extend_min=200.0)

        assert parameters["x"] == pytest.approx(0.2)
        assert parameters["subreaches"] == 1
        np.testing.assert_allclose(
            routed.outflow.discharge_m3s,
            muskingum.outflow.discharge_m3s,
            rtol=1e-12,
            atol=1e-14,
        )
        assert routed.storage_end_m3 == pytest.approx(muskingum.storage_end_m3)

    def test_the_negative_x_of_the_example_uses_the_weights_of_the_kernel(self):
        parameters = neh_reach().route(neh_inflow(), extend_min=0.0).parameters

        assert parameters["x"] < 0.0
        assert muskingum_coefficients(
            parameters["k_min"], parameters["x"], NEH17_4_STEP_MIN
        ) == pytest.approx(
            (
                parameters["c_current"],
                parameters["c_previous"],
                parameters["c_outflow"],
            )
        )

    def test_with_x_zero_it_is_the_linear_reservoir_of_the_clark_scheme(self):
        # D = Q / (T S0 c) = 10 / (10 * 0.001 * 1) = 1000 m, so a 1 km reach in one
        # step has X = 0 and K = dx / c = 1000 s; the step is 20 min (c dt = 1200 m)
        reach = MuskingumCungeReach(
            length_km=1.0,
            slope_m_per_m=0.001,
            celerity_m_per_s=1.0,
            top_width_m=10.0,
            reference_discharge_m3s=10.0,
        )
        values = triangle(10.0, 12, 12, 20.0).discharge_m3s
        step_min, storage_min = 20.0, 1000.0 / 60.0
        c = step_min / (2.0 * storage_min + step_min)
        clark = np.zeros_like(values)
        for i in range(1, len(values)):
            clark[i] = clark[i - 1] + c * (
                values[i] + values[i - 1] - 2.0 * clark[i - 1]
            )

        result = reach.route(
            Hydrograph.from_step(values, step_min),
            initial_outflow_m3s=0.0,
            extend_min=0.0,
        )

        assert result.parameters["x"] == pytest.approx(0.0, abs=1e-15)
        assert result.parameters["subreaches"] == 1
        np.testing.assert_allclose(
            result.outflow.discharge_m3s, clark, rtol=1e-12, atol=1e-14
        )
        assert linear_reservoir_coefficients(storage_min, step_min) == pytest.approx(
            (result.parameters["c_current"],) * 2 + (result.parameters["c_outflow"],)
        )

    def test_with_a_given_reference_the_scheme_is_linear_and_shift_invariant(self):
        reach = MuskingumCungeReach(
            length_km=5.0,
            slope_m_per_m=0.002,
            celerity_m_per_s=1.5,
            top_width_m=20.0,
            reference_discharge_m3s=50.0,
        )
        size = 60
        shapes = (triangle(30.0, 12, 24, 10.0), triangle(12.0, 15, 15, 10.0))
        first, second = (np.pad(s.discharge_m3s, (0, size - len(s))) for s in shapes)

        def route(values):
            return reach.route(Hydrograph.from_step(values, 10.0), extend_min=100.0)

        np.testing.assert_allclose(
            route(first + second).outflow.discharge_m3s,
            route(first).outflow.discharge_m3s + route(second).outflow.discharge_m3s,
            atol=1e-10,
        )
        late = route(np.concatenate([np.zeros(4), first]))
        early = route(first)
        np.testing.assert_allclose(
            late.outflow.discharge_m3s,
            np.concatenate([np.zeros(4), early.outflow.discharge_m3s]),
            atol=1e-10,
        )

    def test_a_longer_run_extends_a_shorter_one(self):
        # the plan and the reference do not depend on the extension of the series
        reach = neh_reach()

        short = reach.route(neh_inflow(), extend_min=0.0)
        long = reach.route(neh_inflow(), extend_min=300.0)

        np.testing.assert_array_equal(
            long.outflow.discharge_m3s[: len(short.outflow)],
            short.outflow.discharge_m3s,
        )
        assert long.parameters == short.parameters

    def test_the_reference_discharge_is_the_inflow_peak_unless_given(self):
        default = neh_reach().route(neh_inflow(), extend_min=0.0)
        peak = neh_inflow().peak_discharge_m3s
        explicit = neh_reach(reference_discharge_m3s=peak).route(
            neh_inflow(), extend_min=0.0
        )
        higher = neh_reach(reference_discharge_m3s=0.95 * peak).route(
            neh_inflow(), extend_min=0.0
        )

        assert default.parameters["reference_discharge_m3s"] == pytest.approx(peak)
        np.testing.assert_array_equal(
            default.outflow.discharge_m3s, explicit.outflow.discharge_m3s
        )
        # a lower reference means less diffusion: a larger X and a sharper peak (the
        # reach stays one distance step, dx = L, in both)
        assert higher.parameters["subreaches"] == default.parameters["subreaches"] == 1
        assert higher.parameters["x"] > default.parameters["x"]
        assert higher.outflow.peak_discharge_m3s > default.outflow.peak_discharge_m3s

    def test_a_steady_state_is_kept(self):
        result = MuskingumCungeReach(
            length_km=8.0,
            slope_m_per_m=0.001,
            celerity_m_per_s=1.2,
            top_width_m=15.0,
        ).route(Hydrograph.from_step([6.0] * 12, 30.0))

        np.testing.assert_allclose(result.outflow.discharge_m3s, 6.0, rtol=1e-12)
        assert "tail_extended" not in codes(result)


class TestRiseTime:
    @pytest.mark.parametrize(
        ("values", "steps"),
        [
            ([0, 0, 1, 5, 10, 8, 4, 2, 0], 3),  # 5 % = 0.5: first above at index 2
            ([0, 2, 10, 4, 3, 12, 6], 2),  # the first peak above half of 12 is 10
            ([0, 1, 5, 5, 5, 2], 2),  # the first ordinate of a plateau
            ([0, 5, 5, 9, 1], 3),  # a flat part of the rise is not a peak
            ([10, 8, 5], 0),  # a hydrograph that starts at its peak has no rise
            ([0, 1, 2, 3, 4, 5], 5),  # still rising at the last ordinate
            ([0, 0, 0], 0),  # no flow at all
        ],
    )
    def test_the_steps_from_five_percent_of_the_peak_to_the_peak(self, values, steps):
        assert rise_steps(np.array(values, dtype=float)) == steps

    def test_the_rise_of_the_example_is_twelve_or_thirteen_steps(self):
        # the text counts 12 steps from about 11.7 h; the ordinate before it is 11.6 h
        steps = rise_steps(np.array(NEH17_4_INFLOW_CFS))

        assert steps == 13

    def test_a_short_rise_divides_the_step_and_says_so(self):
        inflow = triangle(40.0, 3, 9, 20.0)
        reach = MuskingumCungeReach(
            length_km=6.0,
            slope_m_per_m=0.002,
            celerity_m_per_s=1.0,
            top_width_m=25.0,
            reference_discharge_m3s=40.0,
        )

        result = reach.route(inflow)

        assert result.parameters["substeps"] >= 4  # ceil(10 / 3)
        assert codes(result)[0] == "timestep_refined"
        assert "3 time step" in result.notices[0].message
        assert result.outflow.discharge_m3s.min() >= 0.0
        # the outflow is read at the original ordinates
        assert len(result.outflow) >= len(inflow)

    def test_a_refined_run_is_the_routing_of_the_interpolated_hydrograph(self):
        inflow = triangle(40.0, 3, 9, 20.0)
        options = {
            "length_km": 6.0,
            "slope_m_per_m": 0.002,
            "celerity_m_per_s": 1.0,
            "top_width_m": 25.0,
            "reference_discharge_m3s": 40.0,
        }
        coarse = MuskingumCungeReach(**options).route(inflow, extend_min=60.0)
        substeps = coarse.parameters["substeps"]

        fine = MuskingumCungeReach(**options).route(
            inflow.extended(3).refined(substeps), extend_min=0.0
        )

        assert fine.parameters["substeps"] == 1
        np.testing.assert_allclose(
            coarse.outflow.discharge_m3s,
            fine.outflow.discharge_m3s[::substeps],
            rtol=1e-12,
            atol=1e-12,
        )
        # the balance of the coarse run is a sampling error, which is small
        assert abs(coarse.balance_error_m3) < 0.01 * coarse.volume_in_m3


class TestGrid:
    def test_a_flat_reach_takes_fewer_steps_than_the_nrcs_rule(self):
        # c dt = 3600 m, D = Q / (T S0 c) = 16,667 m, L = 20 km: the NRCS step
        # 10,133 m gives 2 steps of 10,000 m, shorter than |c dt - D| = 13,067 m,
        # which makes the weight of the previous inflow negative; one step does not
        reach = MuskingumCungeReach(
            length_km=20.0,
            slope_m_per_m=0.0002,
            celerity_m_per_s=1.0,
            top_width_m=60.0,
            reference_discharge_m3s=200.0,
        )
        inflow = triangle(200.0, 12, 24, 60.0)

        result = reach.route(inflow)

        assert result.parameters["subreaches"] == 1
        assert codes(result)[:1] == ["subreaches_adjusted"]
        assert "2 step(s)" in result.notices[0].message
        assert result.parameters["c_previous"] >= 0.0
        assert result.outflow.discharge_m3s.min() >= 0.0

    def test_the_nrcs_grid_beyond_the_accuracy_limit_is_replaced_and_reported(self):
        # D = 2000 m, c dt = 120 m, L = 4 km: the NRCS step 1060 m gives 4 steps with
        # Dg = 2.0 above exp(2.3 Cg) = 1.32; X = 0 on 2 steps of 2000 m is inside it
        reach = MuskingumCungeReach(
            length_km=4.0,
            slope_m_per_m=0.001,
            celerity_m_per_s=0.2,
            top_width_m=10.0,
            reference_discharge_m3s=4.0,
        )

        result = reach.route(triangle(4.0, 20, 40, 10.0))

        assert codes(result)[:2] == ["accuracy_limit", "subreaches_adjusted"]
        assert result.parameters["subreaches"] == 2
        assert result.parameters["x"] == pytest.approx(0.0, abs=1e-12)
        assert (
            result.parameters["grid_reynolds_number"]
            <= result.parameters["grid_reynolds_limit"]
        )

    def test_a_steep_reach_with_a_long_step_divides_the_step(self):
        # c dt = 3000 m but D = 500 m and L = 2 km: the weight of the previous outflow
        # of any whole number of steps is negative; halving the time step gives 2 steps
        reach = MuskingumCungeReach(
            length_km=2.0,
            slope_m_per_m=0.001,
            celerity_m_per_s=5.0,
            top_width_m=20.0,
            reference_discharge_m3s=50.0,
        )

        result = reach.route(triangle(50.0, 12, 24, 10.0))

        assert result.parameters["substeps"] == 2
        assert result.parameters["subreaches"] == 2
        assert "substeps_added" in codes(result)
        assert "accuracy_limit" not in codes(result)
        assert result.parameters["c_outflow"] >= 0.0
        assert result.outflow.discharge_m3s.min() >= 0.0

    def test_a_reach_too_short_and_flat_for_any_step_is_refused_with_a_remedy(self):
        reach = MuskingumCungeReach(
            length_km=0.1,
            slope_m_per_m=0.0002,
            celerity_m_per_s=1.0,
            top_width_m=60.0,
            reference_discharge_m3s=200.0,
        )

        with pytest.raises(InvalidParameterError) as caught:
            reach.route(triangle(200.0, 12, 24, 60.0))

        details = caught.value.details
        assert (details["option"], details["reason"]) == (
            "times_min",
            "unstable_timestep",
        )
        assert details["maximum_substeps"] == MAX_SUBSTEPS
        assert details["length_m"] == pytest.approx(100.0)
        assert details["diffusion_length_m"] == pytest.approx(200.0 / (60.0 * 0.0002))
        assert "route level-pool" in caught.value.hint

    def test_a_divided_series_beyond_the_ordinate_limit_is_refused(self):
        reach = MuskingumCungeReach(
            length_km=2.0,
            slope_m_per_m=0.001,
            celerity_m_per_s=5.0,
            top_width_m=20.0,
            reference_discharge_m3s=50.0,
        )
        long = Hydrograph.from_step(np.full(600_000, 50.0), 10.0)

        with pytest.raises(InvalidParameterError) as caught:
            reach.route(long, extend_min=0.0)

        assert caught.value.details["reason"] == "unstable_timestep"
        assert caught.value.details["substeps"] == 2

    def test_every_routed_reach_has_non_negative_weights_inside_the_limit(self):
        rng = np.random.default_rng(11)
        routed = refused = 0
        for _ in range(300):
            reach = MuskingumCungeReach(
                length_km=float(10 ** rng.uniform(-1.5, 1.8)),
                slope_m_per_m=float(10 ** rng.uniform(-4, -1.5)),
                celerity_m_per_s=float(10 ** rng.uniform(-0.5, 0.8)),
                top_width_m=float(10 ** rng.uniform(0.5, 2.2)),
                reference_discharge_m3s=float(10 ** rng.uniform(0, 3)),
            )
            inflow = triangle(
                10.0,
                int(rng.integers(10, 30)),
                30,
                float(rng.choice([5.0, 15.0, 60.0])),
            )

            try:
                result = reach.route(inflow, extend_min=0.0)
            except InvalidParameterError as error:
                assert error.details["reason"] == "unstable_timestep"
                refused += 1
                continue
            routed += 1
            parameters = result.parameters
            weights = (
                parameters["c_current"],
                parameters["c_previous"],
                parameters["c_outflow"],
            )
            assert min(weights) >= -1e-9, parameters
            assert parameters["grid_reynolds_number"] <= parameters[
                "grid_reynolds_limit"
            ] * (1.0 + 1e-9), parameters
            assert result.outflow.discharge_m3s.min() >= 0.0
        assert routed > 100
        assert refused >= 1


class TestParameters:
    def test_one_group_of_hydraulics_is_needed(self):
        with pytest.raises(InvalidParameterError) as caught:
            MuskingumCungeReach(length_km=5.0, slope_m_per_m=0.001)

        details = caught.value.details
        assert details["reason"] == "one_of"
        assert details["groups"] == [
            ["manning_n", "bottom_width_m"],
            ["celerity_m_per_s", "top_width_m"],
        ]
        assert details["given"] == []

    def test_a_half_group_names_what_is_missing(self):
        with pytest.raises(InvalidParameterError) as caught:
            MuskingumCungeReach(length_km=5.0, slope_m_per_m=0.001, manning_n=0.03)

        assert caught.value.details["missing"] == ["bottom_width_m"]
        assert caught.value.details["option"] == "bottom_width_m"
        assert "missing for the closest group" in str(caught.value)

    def test_both_groups_at_once_are_refused(self):
        with pytest.raises(InvalidParameterError) as caught:
            MuskingumCungeReach(
                length_km=5.0,
                slope_m_per_m=0.001,
                manning_n=0.03,
                bottom_width_m=5.0,
                celerity_m_per_s=1.0,
                top_width_m=10.0,
            )

        assert caught.value.details["reason"] == "one_of"
        assert "several are given" in str(caught.value)

    @pytest.mark.parametrize(
        ("name", "value", "reason"),
        [
            ("length_km", 0.0, "exclusive_minimum"),
            ("length_km", -2.0, "exclusive_minimum"),
            ("slope_m_per_m", 0.0, "exclusive_minimum"),
            ("slope_m_per_m", float("nan"), "type"),
            ("celerity_m_per_s", -1.0, "exclusive_minimum"),
            ("top_width_m", 0.0, "exclusive_minimum"),
            ("reference_discharge_m3s", 0.0, "exclusive_minimum"),
        ],
    )
    def test_the_numbers_must_be_positive(self, name, value, reason):
        options = {
            "length_km": 5.0,
            "slope_m_per_m": 0.001,
            "celerity_m_per_s": 1.0,
            "top_width_m": 10.0,
            name: value,
        }

        with pytest.raises(InvalidParameterError) as caught:
            MuskingumCungeReach(**options)

        assert caught.value.details["option"] == name
        assert caught.value.details["reason"] == reason

    def test_a_section_is_checked_when_the_reach_is_made(self):
        with pytest.raises(InvalidParameterError) as caught:
            MuskingumCungeReach(
                length_km=5.0,
                slope_m_per_m=0.001,
                manning_n=0.03,
                bottom_width_m=0.0,
            )

        assert caught.value.details["reason"] == "degenerate_section"

    def test_a_hydrograph_without_flow_has_no_reference(self):
        with pytest.raises(InvalidParameterError) as caught:
            neh_reach().route(Hydrograph.from_step([0.0] * 5, 6.0))

        assert caught.value.details["option"] == "reference_discharge_m3s"
        assert "Give reference_discharge_m3s" in caught.value.hint

    def test_a_huge_courant_number_does_not_overflow_the_accuracy_limit(self):
        # a 1 m reach, c dt = 3000 m and D = 3000.5 m: one step is inside the window,
        # Cg = 3000 and exp(2.3 Cg) is beyond a float
        reach = MuskingumCungeReach(
            length_km=0.001,
            slope_m_per_m=0.001,
            celerity_m_per_s=5.0,
            top_width_m=20.0,
            reference_discharge_m3s=300.05,
        )

        result = reach.route(triangle(300.05, 12, 12, 10.0), extend_min=0.0)

        assert result.parameters["courant_number"] == pytest.approx(3000.0)
        assert math.isfinite(result.parameters["grid_reynolds_limit"])
        assert (
            result.parameters["grid_reynolds_number"]
            < result.parameters["grid_reynolds_limit"]
        )
