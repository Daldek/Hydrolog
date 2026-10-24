"""Tests of the channel sections: Manning's normal depth, top width and celerity."""

import math

import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing import TrapezoidalSection

from ._routing_reference import (
    CFS_M3S,
    FT_M,
    NEH17_4_AREA_FT2,
    NEH17_4_CELERITY_FT_PER_S,
    NEH17_4_SECTION,
    NEH17_4_SLOPE,
    NEH17_4_TOP_WIDTH_FT,
)


def manning_discharge(width, side_slope, n, slope, depth):
    """Manning's equation written out for a trapezoid (SI), the reference."""
    area = (width + side_slope * depth) * depth
    perimeter = width + 2.0 * depth * math.sqrt(1.0 + side_slope**2)
    return area * (area / perimeter) ** (2.0 / 3.0) * math.sqrt(slope) / n


class TestFlow:
    def test_a_rectangle_by_hand(self):
        # b = 2 m, y = 1 m, n = 0.03, S = 0.001: A = 2, P = 4, R = 0.5
        q = 2.0 * 0.5 ** (2.0 / 3.0) * math.sqrt(0.001) / 0.03

        state = TrapezoidalSection(2.0, 0.0, 0.03).flow(q, 0.001)

        assert state.depth_m == pytest.approx(1.0, rel=1e-12)
        assert state.area_m2 == pytest.approx(2.0, rel=1e-12)
        assert state.top_width_m == 2.0
        assert state.velocity_m_per_s == pytest.approx(q / 2.0, rel=1e-12)
        # c = Q (5/3 T/A - 2/3 P'/P) / T with P' = 2: (5/3 - 1/3) Q / T
        assert state.celerity_m_per_s == pytest.approx(q * (4.0 / 3.0) / 2.0, rel=1e-12)

    @pytest.mark.parametrize(
        ("width", "side_slope", "n", "slope", "depth"),
        [
            (4.0, 2.0, 0.035, 0.001, 1.5),
            (15.0 * FT_M, 2.0, 0.04, 0.00091, 7.4 * FT_M),
            (0.0, 1.5, 0.03, 0.01, 0.8),
            (30.0, 0.0, 0.05, 0.0002, 3.0),
        ],
    )
    def test_the_depth_gives_back_the_discharge_of_manning(
        self, width, side_slope, n, slope, depth
    ):
        q = manning_discharge(width, side_slope, n, slope, depth)

        state = TrapezoidalSection(width, side_slope, n).flow(q, slope)

        assert state.depth_m == pytest.approx(depth, rel=1e-10)
        assert state.top_width_m == pytest.approx(width + 2.0 * side_slope * depth)

    @pytest.mark.parametrize(
        ("width", "side_slope"), [(4.0, 2.0), (0.0, 1.0), (20.0, 0.0), (3.0, 0.5)]
    )
    def test_the_celerity_is_the_slope_of_the_rating_in_area(self, width, side_slope):
        # c = dQ/dA at constant slope: two discharges a hair apart
        section = TrapezoidalSection(width, side_slope, 0.03)
        low = section.flow(10.0 * (1.0 - 1e-6), 0.002)
        high = section.flow(10.0 * (1.0 + 1e-6), 0.002)

        slope = (10.0 * 2e-6) / (high.area_m2 - low.area_m2)

        assert section.flow(10.0, 0.002).celerity_m_per_s == pytest.approx(
            slope, rel=1e-6
        )

    def test_a_wide_rectangle_has_the_kinematic_celerity_five_thirds_of_the_velocity(
        self,
    ):
        state = TrapezoidalSection(5000.0, 0.0, 0.03).flow(2000.0, 0.0005)

        assert state.celerity_m_per_s / state.velocity_m_per_s == pytest.approx(
            5.0 / 3.0, rel=1e-3
        )

    def test_a_triangle_has_four_thirds(self):
        # Q ~ y^(8/3) and A ~ y^2, so Q ~ A^(4/3) and c = 4/3 V, whatever the size
        state = TrapezoidalSection(0.0, 2.0, 0.03).flow(7.0, 0.003)

        assert state.celerity_m_per_s == pytest.approx(
            4.0 / 3.0 * state.velocity_m_per_s, rel=1e-12
        )

    def test_a_larger_discharge_is_deeper_and_wider(self):
        section = TrapezoidalSection(4.0, 2.0, 0.035)

        small, large = section.flow(5.0, 0.001), section.flow(50.0, 0.001)

        assert small.depth_m < large.depth_m
        assert small.top_width_m < large.top_width_m
        assert small.area_m2 < large.area_m2

    def test_a_very_large_discharge_is_still_found(self):
        state = TrapezoidalSection(1.0, 0.0, 0.1).flow(1.0e6, 1e-5)

        assert state.depth_m > 100.0
        assert manning_discharge(1.0, 0.0, 0.1, 1e-5, state.depth_m) == pytest.approx(
            1.0e6, rel=1e-9
        )

    def test_the_text_book_trapezoid_of_nrcs_example_17_4(self):
        # b = 15 ft, 2:1, n = 0.04, S = 0.00091 at 684.18 ft3/s. The NEH table (from
        # HEC-RAS) has A = 220.9 ft2 and T = 44.6 ft; its celerity c = m Q / A uses
        # the weighted log-log slope m = 1.3873 of the whole table, 2 % above the
        # local dQ/dA of Manning's equation.
        section = TrapezoidalSection(
            NEH17_4_SECTION["bottom_width_ft"] * FT_M,
            NEH17_4_SECTION["side_slope"],
            NEH17_4_SECTION["manning_n"],
        )

        state = section.flow(684.18 * CFS_M3S, NEH17_4_SLOPE)

        assert state.area_m2 / FT_M**2 == pytest.approx(NEH17_4_AREA_FT2, rel=2e-3)
        assert state.top_width_m / FT_M == pytest.approx(NEH17_4_TOP_WIDTH_FT, rel=2e-3)
        celerity = state.celerity_m_per_s / FT_M
        assert celerity == pytest.approx(NEH17_4_CELERITY_FT_PER_S, rel=0.03)
        assert celerity < NEH17_4_CELERITY_FT_PER_S


class TestParameters:
    @pytest.mark.parametrize(
        ("arguments", "option", "reason"),
        [
            ((-1.0, 1.0, 0.03), "bottom_width_m", "minimum"),
            ((4.0, -0.5, 0.03), "side_slope_m_per_m", "minimum"),
            ((4.0, 1.0, 0.0), "manning_n", "exclusive_minimum"),
            ((4.0, 1.0, float("nan")), "manning_n", "type"),
            ((float("inf"), 1.0, 0.03), "bottom_width_m", "not_finite"),
            ((0.0, 0.0, 0.03), "bottom_width_m", "degenerate_section"),
        ],
    )
    def test_a_section_must_be_a_valid_shape(self, arguments, option, reason):
        with pytest.raises(InvalidParameterError) as caught:
            TrapezoidalSection(*arguments)

        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason

    @pytest.mark.parametrize(
        ("discharge", "slope", "option"),
        [
            (0.0, 0.001, "discharge_m3s"),
            (5.0, 0.0, "slope_m_per_m"),
            (-1.0, 0.1, "discharge_m3s"),
        ],
    )
    def test_the_flow_needs_a_positive_discharge_and_slope(
        self, discharge, slope, option
    ):
        with pytest.raises(InvalidParameterError) as caught:
            TrapezoidalSection(4.0, 1.0, 0.03).flow(discharge, slope)

        assert caught.value.details["option"] == option
