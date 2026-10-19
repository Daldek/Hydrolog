"""Tests of the complete-year rule for annual extremes.

``annual_extremes`` takes the annual maximum or minimum of the *complete* hydrological
years of a daily series (KZGW, 2017; WMO No. 1029, 2009). Regression: the extremes of
every year present in the dates were used, including the stub years at both ends of a
calendar-year series (see ``tests/unit/test_low_flows.py`` and
``tests/unit/test_operations_analysis.py`` for the effect on the analyses).
"""

from __future__ import annotations

import numpy as np
import pytest

from hydrolog.statistics._hydrological_year import (
    annual_extremes,
    days_in_hydrological_year,
    describe_incomplete_years,
    incomplete_years_message,
)


def _days(first: str, last: str) -> np.ndarray:
    """Every day from ``first`` to ``last`` inclusive (ISO dates)."""
    return np.arange(
        np.datetime64(first), np.datetime64(last) + 1, dtype="datetime64[D]"
    )


class TestDaysInHydrologicalYear:
    @pytest.mark.parametrize("year", [1900, 1999, 2000, 2019, 2020, 2021, 2024, 2100])
    def test_equals_the_number_of_calendar_days_between_1_nov_and_31_oct(self, year):
        counted = len(_days(f"{year - 1}-11-01", f"{year}-10-31"))
        assert days_in_hydrological_year(np.array([year]))[0] == counted

    def test_the_year_with_29_february_has_366_days(self):
        assert days_in_hydrological_year(np.array([2019, 2020, 2021])).tolist() == [
            365,
            366,
            365,
        ]

    def test_century_years_are_leap_years_only_when_divisible_by_400(self):
        assert days_in_hydrological_year(np.array([1900, 2000, 2100])).tolist() == [
            365,
            366,
            365,
        ]


class TestCompleteYears:
    def test_a_calendar_year_series_loses_its_first_and_last_hydrological_year(self):
        """1991-01-01 .. 2020-12-31: HY 1991 lacks Nov-Dec 1990, HY 2021 is Nov-Dec."""
        dates = _days("1991-01-01", "2020-12-31")
        result = annual_extremes(np.ones(len(dates)), dates, "max")
        assert result.years.tolist() == list(range(1992, 2021))
        assert result.incomplete_years == [1991, 2021]
        first, last = result.incomplete
        assert (first.days_with_data, first.days_in_year) == (304, 365)
        assert (last.days_with_data, last.days_in_year) == (61, 365)

    def test_whole_hydrological_years_are_all_complete_leap_year_included(self):
        dates = _days("2019-11-01", "2023-10-31")  # HY 2020 (366 days) .. HY 2023
        result = annual_extremes(np.ones(len(dates)), dates, "min")
        assert result.years.tolist() == [2020, 2021, 2022, 2023]
        assert result.incomplete == ()
        assert result.incomplete_years == []

    @pytest.mark.parametrize("how", ["absent date", "nan value"])
    def test_one_missing_day_makes_the_year_incomplete(self, how):
        dates = _days("2019-11-01", "2023-10-31")
        values = np.arange(len(dates), dtype=float)
        day = int(np.flatnonzero(dates == np.datetime64("2021-03-15"))[0])
        if how == "absent date":
            values, dates = np.delete(values, day), np.delete(dates, day)
        else:
            values[day] = np.nan
        result = annual_extremes(values, dates, "max")
        assert result.years.tolist() == [2020, 2022, 2023]
        assert [tuple(item) for item in result.incomplete] == [(2021, 364, 365)]

    def test_a_leap_year_needs_29_february(self):
        dates = _days("2019-11-01", "2021-10-31")
        keep = dates != np.datetime64("2020-02-29")
        result = annual_extremes(np.ones(keep.sum()), dates[keep], "max")
        assert result.years.tolist() == [2021]
        assert [tuple(item) for item in result.incomplete] == [(2020, 365, 366)]

    def test_a_duplicated_date_counts_once(self):
        """Without it a year with a gap and a repeated day would pass for complete."""
        dates = _days("2020-11-01", "2021-10-31")
        gap, repeated = 10, 100
        keep = np.arange(len(dates)) != gap
        dates_with_gap = np.concatenate([dates[keep], dates[[repeated]]])
        order = np.argsort(dates_with_gap, kind="stable")
        result = annual_extremes(
            np.ones(len(dates_with_gap)), dates_with_gap[order], "max"
        )
        assert len(dates_with_gap) == 365  # as many values as days, yet one is absent
        assert result.years.tolist() == []
        assert [tuple(item) for item in result.incomplete] == [(2021, 364, 365)]

        complete = np.concatenate([dates, dates[[repeated]]])
        again = annual_extremes(np.ones(len(complete)), np.sort(complete), "max")
        assert again.years.tolist() == [2021]

    def test_a_year_with_every_value_missing_is_incomplete_with_zero_days(self):
        dates = _days("2020-11-01", "2021-10-31")
        result = annual_extremes(np.full(len(dates), np.nan), dates, "min")
        assert result.years.size == 0 and result.values.size == 0
        assert [tuple(item) for item in result.incomplete] == [(2021, 0, 365)]


class TestExtremes:
    @staticmethod
    def _series():
        """Three whole hydrological years (2021-2023) plus November 2023."""
        dates = _days("2020-11-01", "2023-11-30")
        values = np.full(len(dates), 5.0)
        for day, value in (
            ("2021-03-10", 12.0),
            ("2021-09-10", 2.0),
            ("2022-03-10", 15.0),
            ("2022-09-10", 1.0),
            ("2023-03-10", 11.0),
            ("2023-09-10", 3.0),
            ("2023-11-20", 99.0),  # the stub HY 2024: a flood the maxima must ignore
            ("2023-11-21", -9.0),  # ... and a dip the minima must ignore
        ):
            values[int(np.flatnonzero(dates == np.datetime64(day))[0])] = value
        return values, dates

    def test_maxima_of_the_complete_years_only(self):
        values, dates = self._series()
        result = annual_extremes(values, dates, "max")
        assert result.years.tolist() == [2021, 2022, 2023]
        assert result.values.tolist() == [12.0, 15.0, 11.0]
        assert result.incomplete_years == [2024]

    def test_minima_of_the_complete_years_only(self):
        values, dates = self._series()
        result = annual_extremes(values, dates, "min")
        assert result.years.tolist() == [2021, 2022, 2023]
        assert result.values.tolist() == [2.0, 1.0, 3.0]

    def test_the_order_of_the_input_does_not_matter(self):
        values, dates = self._series()
        shuffled = np.random.default_rng(3).permutation(len(dates))
        straight = annual_extremes(values, dates, "max")
        mixed = annual_extremes(values[shuffled], dates[shuffled], "max")
        assert mixed.years.tolist() == straight.years.tolist()
        assert mixed.values.tolist() == straight.values.tolist()
        assert mixed.incomplete == straight.incomplete

    def test_a_series_shorter_than_a_year_has_no_extremes(self):
        dates = _days("2021-01-01", "2021-04-10")
        result = annual_extremes(np.ones(len(dates)), dates, "max")
        assert result.years.size == 0 and result.values.size == 0
        assert result.incomplete_years == [2021]


class TestMessages:
    def test_the_message_lists_the_skipped_years_with_their_days(self):
        dates = _days("1991-01-01", "2020-12-31")
        result = annual_extremes(np.ones(len(dates)), dates, "max")
        assert describe_incomplete_years(result) == (
            "1991 (304 of 365 days), 2021 (61 of 365 days)"
        )
        message = incomplete_years_message(result)
        assert "2 of 31" in message
        assert message.endswith("1991 (304 of 365 days), 2021 (61 of 365 days)")
        assert "\n" not in message

    def test_a_long_list_is_cut_after_ten_years(self):
        # one day in each of 15 calendar years: 15 incomplete hydrological years
        dates = np.array(
            [f"{year}-06-15" for year in range(2001, 2016)], dtype="datetime64[D]"
        )
        result = annual_extremes(np.ones(len(dates)), dates, "max")
        listed = describe_incomplete_years(result)
        assert listed.startswith("2001 (1 of 365 days), 2002 (1 of 365 days)")
        assert "2010 (1 of 365 days)" in listed
        assert "2011" not in listed
        assert listed.endswith(", and 5 more")
        assert "15 of 15" in incomplete_years_message(result)
