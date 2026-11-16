"""Tests for the homogeneity tests of a split series (ADR-0022)."""

import math

import numpy as np
import pytest

from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.statistics import homogeneity_tests


def _spread(n):
    """Values spread evenly over [0, 1) in no order in time (golden-ratio steps)."""
    golden = (math.sqrt(5.0) - 1.0) / 2.0
    return np.array([(i * golden) % 1.0 for i in range(1, n + 1)])


def _decisions(result):
    return [
        result.mann_whitney.homogeneous,
        result.kolmogorov_smirnov.homogeneous,
        result.pettitt.homogeneous,
    ]


class TestDecisions:
    def test_a_step_is_rejected_by_all_three_tests(self):
        series = 100.0 + 20.0 * _spread(40)
        series[20:] += 100.0

        result = homogeneity_tests(series)

        assert _decisions(result) == [False, False, False]
        # Every value of the first part is below every value of the second.
        assert result.mann_whitney.statistic == 0.0
        assert result.kolmogorov_smirnov.statistic == 1.0

    def test_values_without_a_change_are_not_rejected(self):
        result = homogeneity_tests(100.0 + 20.0 * _spread(40))

        assert _decisions(result) == [True, True, True]

    def test_the_decision_follows_alpha(self):
        # Ten values with a step in the middle: Pettitt's p-value is 0.066.
        series = np.array([52.0, 48.0, 55.0, 50.0, 47.0, 81.0, 86.0, 79.0, 90.0, 84.0])

        assert homogeneity_tests(series, alpha=0.05).pettitt.homogeneous is True
        assert homogeneity_tests(series, alpha=0.1).pettitt.homogeneous is False


class TestPettitt:
    def test_k_of_a_small_series_by_hand(self):
        # U_t = sum over i <= t < j of sgn(x_i - x_j): -4, -4, -6, -2.
        result = homogeneity_tests(np.array([1.0, 3.0, 2.0, 5.0, 4.0]))

        assert result.pettitt.statistic == 6.0
        assert result.pettitt.p_value == pytest.approx(2.0 * math.exp(-216.0 / 150.0))
        assert result.pettitt.change_point_index == 3

    def test_ties_take_mid_ranks_and_the_p_value_is_at_most_one(self):
        # U_t: 0, -3, -3, so K = 3 first at t = 2; 2 exp(-6 * 9 / 80) is above 1.
        result = homogeneity_tests(np.array([2.0, 1.0, 2.0, 3.0]))

        assert result.pettitt.statistic == 3.0
        assert result.pettitt.change_point_index == 2
        assert result.pettitt.p_value == 1.0

    def test_the_change_point_of_a_step_is_its_first_value_after_the_change(self):
        years = np.arange(1961, 1991)
        series = np.where(years < 1973, 50.0, 80.0)

        result = homogeneity_tests(series, years)

        assert result.pettitt.change_point_index == 12
        assert result.pettitt.change_point_year == 1973
        assert result.pettitt.statistic == 12 * 18
        assert result.pettitt.homogeneous is False
        # As the split year, the change point separates the two levels exactly.
        split = homogeneity_tests(
            series, years, split_year=result.pettitt.change_point_year
        )
        assert split.split_index == 12
        assert split.mann_whitney.statistic == 0.0
        assert split.kolmogorov_smirnov.statistic == 1.0


class TestSplit:
    SEVEN = np.array([3.0, 1.0, 4.0, 1.5, 5.0, 9.0, 2.0])

    def test_by_default_the_middle_value_of_an_odd_series_is_in_the_second_part(self):
        dated = homogeneity_tests(self.SEVEN, np.arange(2001, 2008))
        undated = homogeneity_tests(self.SEVEN)

        assert (dated.split_index, dated.split_year) == (3, 2004)
        assert (undated.split_index, undated.split_year) == (3, None)
        assert undated.pettitt.change_point_year is None

    def test_split_year_is_the_first_year_of_the_second_part(self):
        series = np.array([60.0, 61.0, 62.0, 10.0, 70.0, 11.0, 12.0, 13.0, 14.0, 15.0])

        result = homogeneity_tests(series, np.arange(1981, 1991), split_year=1984)

        assert (result.split_index, result.split_year) == (3, 1984)
        # U of the first part, not the smaller U: the pairs in which its value is the
        # larger one (60, 61 and 62 each above six of the seven later values).
        assert result.mann_whitney.statistic == 18.0

    def test_a_split_year_missing_from_the_series_splits_between_its_neighbours(self):
        years = np.array([1981, 1982, 1984, 1985, 1986])

        result = homogeneity_tests(
            np.array([1.0, 5.0, 2.0, 7.0, 3.0]), years, split_year=1983
        )

        assert (result.split_index, result.split_year) == (2, 1984)

    @pytest.mark.parametrize(("split_year", "index"), [(2002, 1), (2004, 3)])
    def test_each_part_may_hold_one_value(self, split_year, index):
        result = homogeneity_tests(
            np.array([1.0, 2.0, 3.0, 4.0]), np.arange(2001, 2005), split_year=split_year
        )

        assert result.split_index == index

    @pytest.mark.parametrize("split_year", [2001, 2005])
    def test_a_split_year_that_leaves_a_part_empty_is_refused(self, split_year):
        with pytest.raises(InvalidParameterError) as caught:
            homogeneity_tests(
                np.array([1.0, 2.0, 3.0, 4.0]),
                np.arange(2001, 2005),
                split_year=split_year,
            )

        assert caught.value.details == {
            "option": "split_year",
            "reason": "range",
            "value": str(split_year),
            "minimum": 2002,
            "maximum": 2004,
        }

    def test_split_year_needs_the_years(self):
        with pytest.raises(InvalidParameterError) as caught:
            homogeneity_tests(np.array([1.0, 2.0, 3.0, 4.0]), split_year=2002)

        assert caught.value.details == {"option": "years", "reason": "required"}


class TestErrors:
    def test_fewer_than_three_values_are_a_calculation_error(self):
        with pytest.raises(CalculationError) as caught:
            homogeneity_tests(np.array([1.0, 2.0]))

        assert caught.value.code == "calculation_error"
        assert caught.value.details == {
            "reason": "too_few_values",
            "count": 2,
            "minimum": 3,
        }

    def test_equal_values_are_a_calculation_error(self):
        with pytest.raises(CalculationError) as caught:
            homogeneity_tests(np.full(6, 5.0))

        assert caught.value.details == {"reason": "constant_values"}

    @pytest.mark.parametrize(
        ("series", "years", "option", "reason"),
        [
            (np.array([1.0, np.nan, 3.0, 4.0]), None, "series", "not_finite"),
            (
                np.array([1.0, 2.0, 3.0, 4.0]),
                np.arange(2001.0, 2005.0),
                "years",
                "type",
            ),
            (
                np.array([1.0, 2.0, 3.0, 4.0]),
                np.array([2001, 2002, 2003]),
                "years",
                "length_mismatch",
            ),
            (
                np.array([1.0, 2.0, 3.0, 4.0]),
                np.array([2001, 2003, 2003, 2004]),
                "years",
                "not_increasing",
            ),
        ],
    )
    def test_invalid_input_is_a_validation_error(self, series, years, option, reason):
        with pytest.raises(InvalidParameterError) as caught:
            homogeneity_tests(series, years)

        assert caught.value.code == "validation_error"
        assert (caught.value.details["option"], caught.value.details["reason"]) == (
            option,
            reason,
        )
