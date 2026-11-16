"""The list filter of ``meteo spells`` and the period fields of spells and snow.

``min_duration_days`` shortens the list of spells only: the yearly and period
summaries are those of every spell, as CDD and CWD of the ETCCDI (Zhang et al., 2011)
have no minimum duration.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from hydrolog.catalog import run_command
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics import precipitation_spells

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "meteo_daily.csv"


def _days(first: str, count: int) -> list[str]:
    start = np.datetime64(first)
    return [str(start + np.timedelta64(n, "D")) for n in range(count)]


def _result(command: str, **options) -> dict:
    return run_command(command, options).to_dict()["result"]


def _without_list(result: dict) -> str:
    rest = {
        key: value
        for key, value in result.items()
        if key not in ("spells", "min_duration_days")
    }
    return json.dumps(rest, sort_keys=True)


class TestMinDurationDays:
    """Only the list is filtered; the summaries take every spell."""

    @pytest.mark.parametrize(
        ("kind", "threshold_mm"), [("dry", 1.0), ("wet", 1.0), ("wet", 0.1)]
    )
    def test_the_list_shrinks_and_the_summaries_stay(self, kind, threshold_mm):
        options = {
            "input_file": str(FIXTURE),
            "kind": kind,
            "threshold_mm": threshold_mm,
        }
        every = _result("meteo spells", **options)
        long = _result("meteo spells", **options, min_duration_days=5)
        assert every["min_duration_days"] == 1
        assert long["min_duration_days"] == 5
        assert long["spells"] == [s for s in every["spells"] if s["duration_days"] >= 5]
        assert 0 < len(long["spells"]) < len(every["spells"]) == every["n_spells"]
        assert _without_list(long) == _without_list(every)

    def test_a_minimum_above_every_spell_leaves_an_empty_list(self):
        every = _result("meteo spells", input_file=str(FIXTURE))
        none = _result(
            "meteo spells",
            input_file=str(FIXTURE),
            min_duration_days=every["max_duration_days"] + 1,
        )
        assert none["spells"] == []
        assert _without_list(none) == _without_list(every)

    @pytest.mark.parametrize("value", [0, -3])
    def test_below_one_is_a_validation_error(self, value):
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "meteo spells", {"input_file": str(FIXTURE), "min_duration_days": value}
            )
        assert caught.value.code == "validation_error"
        assert caught.value.details["option"] == "min_duration_days"

    @pytest.mark.parametrize("value", [0, 1.5, True])
    def test_the_library_refuses_anything_but_an_integer_of_at_least_one(self, value):
        with pytest.raises(InvalidParameterError, match="min_duration_days"):
            precipitation_spells(
                [0.0, 2.0], _days("2001-01-01", 2), min_duration_days=value
            )


class TestSpellFields:
    """The fields of a spell, of a year and of the period, by hand."""

    def test_a_complete_year_and_an_incomplete_one(self):
        dates = _days("2001-01-01", 365 + 31)
        rain = [5.0] * len(dates)
        for first, count in ((9, 5), (59, 5), (151, 1), (365 + 19, 1)):
            rain[first : first + count] = [0.0] * count  # 10 Jan, 1 Mar, 1 Jun 2001
        result = _result(
            "meteo spells", dates=dates, precipitation_mm=rain, min_duration_days=2
        )
        assert (result["n_spells"], result["max_duration_days"]) == (4, 5)
        assert [
            (s["start_date"], s["end_date"], s["duration_days"])
            for s in result["spells"]
        ] == [("2001-01-10", "2001-01-14", 5), ("2001-03-01", "2001-03-05", 5)]
        full, partial = result["years"]
        assert full == {
            "year": 2001,
            "complete": True,
            "n_spells": 3,
            "max_duration_days": 5,
            "max_start_date": "2001-01-10",  # the first of two equally long
            "max_end_date": "2001-01-14",
            "spells_10_days": 0,
            "spells_15_days": 0,
            "spells_20_days": 0,
        }
        assert (partial["year"], partial["complete"]) == (2002, False)
        assert partial["max_duration_days"] is None
        period = result["period"]
        assert period["n_years"] == 1
        assert period["mean_max_duration_days"] == 5.0
        assert period["mean_n_spells"] == 3.0
        assert [c["count"] for c in period["classes"][:4]] == [1, 0, 0, 2]


class TestSnowPeriod:
    def test_an_incomplete_winter_is_listed_and_left_out(self):
        dates = _days("2020-08-01", 365 + 61)  # to 30 September 2021
        depth = [0.0] * len(dates)
        depth[180] = 12.0  # 28 January 2021
        depth[400] = 30.0  # 5 September 2021, winter 2022: incomplete
        period = _result("meteo snow", dates=dates, snow_cover_cm=depth)["period"]
        assert period["n_years"] == 1
        assert period["incomplete_years"] == [2022]
        assert period["max_depth_cm"] == 12.0  # not the 30 cm of winter 2022
