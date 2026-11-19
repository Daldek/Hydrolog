"""Seasonality of annual extremes: the circular statistics of their dates.

The date of each annual maximum (or minimum) is an angle on the circle of its calendar
year, θ = 2π (d − 0.5) / L, d the day of the year (1 = 1 January) and L its length (365
or 366 days): the middle of the day. The mean of the unit vectors of the n dates,
x̄ = Σ cos θ / n and ȳ = Σ sin θ / n, points to the mean date, atan2(ȳ, x̄), a day of a
year of 365.25 days, and its length r = √(x̄² + ȳ²) is the concentration of the dates:
1 when they all fall on one day, near 0 when they spread over the year (Bayliss and
Jones, 1992; Burn, 1997; FEH, 1999). :func:`circular_mean` computes the direction and
length of times on the circles of their years (spec :data:`CIRCULAR_MEAN`),
:func:`circular_mean_date` reads dates into it and its mean back into a day
(:data:`TIER_B`). The annual extremes are those of the complete hydrological years of
a daily series (:func:`daily_extremes`) or IMGW-PIB's published ones
(:func:`half_year_extremes`, the larger of the half-year maxima, the smaller of the
minima, as :func:`~hydrolog.statistics.characteristic_values_from_half_years`).
``docs/FORMULAS.md`` shows the spec (ADR-0063).

Examples
--------
Two dates ten days either side of 1 April point to it, read back on the mean year:

>>> mean = circular_mean_date(["2001-03-22", "2001-04-11"])
>>> mean.mean_date, round(mean.mean_day, 3), round(mean.concentration, 4)
('04-01', 91.062, 0.9852)

Dates half a year apart in a leap year have no direction: r is (nearly) zero:

>>> round(circular_mean([0.5, 183.5], [366.0, 366.0]).concentration, 12)
0.0

References
----------
Bayliss, A. C. & Jones, R. C. (1992): The peaks-over-threshold database at the
    Institute of Hydrology. Report to MAFF, Institute of Hydrology, Wallingford,
    section 3 (published as IH Report No. 121, 1993).
Robson, A. & Reed, D. (1999): Flood Estimation Handbook, Volume 3: Statistical
    procedures for flood frequency estimation. Institute of Hydrology, Wallingford,
    Additional Note 16.1.
Burn, D. H. (1997): Catchment similarity for regional flood frequency analysis using
    seasonality measures. Journal of Hydrology, 202(1–4), 212–230.
Hall, J. & Blöschl, G. (2018): Spatial patterns and characteristics of flood
    seasonality in Europe. Hydrology and Earth System Sciences, 22, 3883–3901.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final, Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Constant,
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    Symmetry,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._hydrological_year import (
    AnnualExtremes,
    annual_extremes,
    hydrological_year,
)
from hydrolog.statistics.characteristic import (
    HalfYearValues,
    characteristic_values_from_half_years,
)

__all__ = [
    "CIRCULAR_MEAN",
    "SPECS",
    "TIER_B",
    "CircularMean",
    "CircularMeanTime",
    "DatedExtreme",
    "ExtremeSeasonality",
    "circular_mean",
    "circular_mean_date",
    "daily_extremes",
    "extreme_seasonality",
    "half_year_extremes",
]

Statistic = Literal["max", "min"]


class CircularMean(NamedTuple):
    """The mean date and the concentration of dates over the year.

    Attributes
    ----------
    mean_day : float
        Day of the year of the mean date (1 = 1 January, 0.5 to 365.75). With a
        concentration near 0 the dates have no clear mean and it says little.
    mean_date : str
        The month and day of ``mean_day`` rounded, in a common year (``MM-DD``).
    concentration : float
        Length of the mean vector, 0 to 1.
    """

    mean_day: float
    mean_date: str
    concentration: float


@dataclass
class DatedExtreme(JsonResultMixin):
    """The extreme of one hydrological year with its date.

    Attributes
    ----------
    year : int
        Hydrological year (1 November - 31 October, named after its end).
    value : float
        The annual maximum or minimum, in the unit of the series.
    date : str
        Its date (ISO ``YYYY-MM-DD``), the first day it occurs.
    """

    year: int
    value: float
    date: str


@dataclass
class ExtremeSeasonality(JsonResultMixin):
    """The seasonality of the annual maxima or minima of a station.

    Attributes
    ----------
    statistic : {"max", "min"}
        Annual maxima or minima.
    parameter : str
        The variable: ``"Q"``, ``"H"`` or ``"T"``.
    source : {"daily", "half_years"}
        The complete years of a daily series, or IMGW-PIB's half-year file.
    first_year, last_year : int
        First and last hydrological year of ``years``.
    period_years : int
        Number of ``years``.
    years : list of DatedExtreme
        The dated annual extreme of each year, in order.
    mean_day : float
        Day of the year of the mean date (1 = 1 January), see :class:`CircularMean`.
    mean_date : str
        The mean date as ``MM-DD``.
    concentration : float
        Concentration r of the dates, 0 (spread) to 1 (one day).
    winter_share, summer_share : float
        Shares of the extremes dated in the winter (November to April) and the
        summer (May to October) half-year.
    """

    statistic: str
    parameter: str
    source: str
    first_year: int
    last_year: int
    period_years: int
    years: list[DatedExtreme]
    mean_day: float
    mean_date: str
    concentration: float
    winter_share: float
    summer_share: float


def _calendar(days: NDArray[np.datetime64]) -> tuple[NDArray[np.int64], ...]:
    """Calendar year, month and day of the year (1 = 1 January) of each date."""
    years = days.astype("datetime64[Y]")
    day_of_year = (days - years.astype("datetime64[D]")).astype(np.int64) + 1
    months = days.astype("datetime64[M]").astype(np.int64) % 12 + 1
    return years.astype(np.int64) + 1970, months, day_of_year


class CircularMeanTime(NamedTuple):
    """The mean direction and length of times on their years (spec ``circular_mean``).

    Attributes
    ----------
    mean_fraction : float
        Direction of the mean vector as the fraction of the year from its start, 0 to
        1; with a concentration near 0 it says little.
    concentration : float
        Length r of the mean vector, 0 (spread over the year) to 1 (a single time).
    """

    mean_fraction: float
    concentration: float


# --- the spec of the circular mean (Nogat CMP-2.1; ADR-0063) -------------------------

_BAYLISS_JONES = Source(
    citation="Bayliss, A.C. and Jones, R.C. (1992). The peaks-over-threshold database "
    "at the Institute of Hydrology. Report to MAFF, Institute of Hydrology, "
    "Wallingford, March 1992 (published as IH Report No. 121, 1993)",
    locator="section 3.2, pp. 18-19: theta_i = day 2 pi / LENYR - ADJUST with ADJUST "
    "= (1/2)(2 pi / 365) for the middle of the day, LENYR 365 or 366; xbar, ybar the "
    "means of cos and sin; tan(thetabar) = ybar / xbar with pi or 2 pi added by their "
    "signs; MPD = thetabar 365 / (2 pi) + 0.5; section 3.3, p. 21: r = sqrt(xbar^2 + "
    "ybar^2), MPD less meaningful when r is close to zero",
    url="https://nora.nerc.ac.uk/id/eprint/14407/",
)
_FEH = Source(
    citation="Robson, A. and Reed, D. (1999). Flood Estimation Handbook, Volume 3: "
    "Statistical procedures for flood frequency estimation. Institute of Hydrology, "
    "Wallingford",
    locator="Additional Note 16.1, pp. 177-179: theta = (day no. - 0.5) 2 pi / LENYR, "
    "LENYR 365 or 366, the 0.5 for the middle of the day; XFLOOD and YFLOOD the means "
    "of cos theta and sin theta; thetabar by their quadrant, r their length; when r is "
    "small the direction is less meaningful",
    url="https://www.ceh.ac.uk/sites/default/files/2021-11/Flood-Estimation-Handbook-3-"
    "Statistical-Procedures-For-Flood-Frequency-Estimation_Alice-Robson_Duncan-Reed.pdf",
)
_HALL_BLOSCHL = Source(
    citation="Hall, J. and Blöschl, G. (2018). Spatial patterns and characteristics of "
    "flood seasonality in Europe. Hydrology and Earth System Sciences 22, 3883-3901",
    locator="eqs. 1-5: theta_i = D_i 2 pi / m_i (D_i = 1 on 1 January, m_i 365 or "
    "366); the mean date by the quadrant rules times m / (2 pi), m the mean number of "
    "days per year, undefined for xbar = ybar = 0; R = sqrt(xbar^2 + ybar^2)",
    url="https://hess.copernicus.org/articles/22/3883/2018/hess-22-3883-2018.pdf",
)
_BURN = Source(
    citation="Burn, D.H. (1997). Catchment similarity for regional flood frequency "
    "analysis using seasonality measures. Journal of Hydrology 202, 212-230",
    locator="the seasonality measures of flood dates; not opened",
    access="author-provided",
)
_IMGW_URL = (
    "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/"
)
_HUGE_TIME_REASON = (
    "a year in seconds is about 3.2e7: the bound leaves room for times in any unit "
    "down to the second"
)

_BASE_DATES: Final = (
    "2001-03-15",
    "2002-03-20",
    "2003-04-02",
    "2004-02-28",
    "2005-03-30",
    "2006-12-30",
    "2007-01-05",
)
"""Seven dates of annual maxima, mostly in spring (the oracle sample of the audit)."""


def _circular(
    elapsed: NDArray[np.float64], length: NDArray[np.float64]
) -> tuple[float, float]:
    """Return the mean direction as a fraction of the year and the length r."""
    angles = 2.0 * np.pi * elapsed / length
    x = float(np.mean(np.cos(angles)))
    y = float(np.mean(np.sin(angles)))
    direction = math.atan2(y, x) % (2.0 * math.pi)
    return direction / (2.0 * math.pi), math.hypot(x, y)


def _times_of(dates: Sequence[str]) -> tuple[list[float], list[float]]:
    """Return the time of each date in its year (its middle) and the year's length."""
    days = np.asarray(dates, dtype="datetime64[D]")
    years, _, day_of_year = _calendar(days)
    return (day_of_year - 0.5).tolist(), (365 + _leap(years)).astype(float).tolist()


def _quadrant_direction(x: float, y: float) -> float:
    """Return thetabar of Bayliss and Jones: arctan(y / x) plus pi or 2 pi by signs."""
    if x == 0.0:
        return 0.5 * math.pi if y > 0 else 1.5 * math.pi if y < 0 else 0.0
    theta = math.atan(y / x)
    if x < 0.0:
        return theta + math.pi
    return theta + 2.0 * math.pi if y < 0.0 else theta


def _bayliss_jones(run: Callable[..., Values]) -> None:
    rng = np.random.default_rng(20261119)
    samples = [_times_of(_BASE_DATES)]
    for _ in range(200):
        size = int(rng.integers(1, 60))
        day = np.datetime64("1951-01-01") + rng.integers(0, 365 * 70, size)
        samples.append(_times_of([str(d) for d in day]))
    for elapsed, length in samples:
        out = run(elapsed_days=elapsed, year_days=length)
        angles = [2.0 * math.pi * t / n for t, n in zip(elapsed, length, strict=True)]
        x = math.fsum(math.cos(a) for a in angles) / len(angles)
        y = math.fsum(math.sin(a) for a in angles) / len(angles)
        r = math.sqrt(x * x + y * y)
        assert_within(
            out.real("concentration"),
            r,
            abs=4e-16,
            reason="r of Bayliss and Jones from math.fsum against NumPy's pairwise "
            "sums: a few ulps of the sums",
        )
        if r < 1e-3:
            continue  # the direction of a near-zero vector is noise (section 3.3)
        turn = _quadrant_direction(x, y) / (2.0 * math.pi) - out.real("mean_fraction")
        assert_within(
            (turn + 0.5) % 1.0 - 0.5,
            0.0,
            abs=1e-12,
            reason="arctan with the quadrant rules of Bayliss and Jones against atan2: "
            "the sums differ by a few ulps, which turn the direction by that over r",
        )


CIRCULAR_MEAN: Final[FormulaSpec] = FormulaSpec(
    name="circular_mean",
    title="Mean direction and concentration of times on the circles of their years "
    "(Bayliss and Jones)",
    function="hydrolog.statistics.seasonality.circular_mean",
    family="statistic",
    equation="theta_i = 2 pi t_i / L_i; xbar = sum(cos theta_i) / n, ybar = "
    "sum(sin theta_i) / n; f = (atan2(ybar, xbar) mod 2 pi) / (2 pi); r = sqrt(xbar^2 "
    "+ ybar^2)",
    latex=r"\theta_i = \frac{2\pi t_i}{L_i},\quad \bar{x} = \frac{1}{n}\sum_i "
    r"\cos\theta_i,\quad \bar{y} = \frac{1}{n}\sum_i \sin\theta_i,\quad "
    r"f = \frac{\operatorname{atan2}(\bar{y}, \bar{x}) \bmod 2\pi}{2\pi},\quad "
    r"r = \sqrt{\bar{x}^2 + \bar{y}^2}",
    variables=(
        Variable(
            name="elapsed_days",
            symbol="t_i",
            unit="day",
            kind="real_array",
            description="Time of each date from the start of its year: the day of the "
            "year minus a half, the middle of the day.",
            physical=Range(low=0.0, test_high=1.0e9, test_reason=_HUGE_TIME_REASON),
            applicability="unstated",
            typical=Range(
                low=2.5,
                high=336.5,
                source=Source(
                    citation="IMGW-PIB, public hydrological data: the half-year "
                    "characteristics of discharge at station 150160180 Kłodzko on the "
                    "Nysa Kłodzka, hydrological years 1971-2015 but 1997",
                    locator="the dates of the 44 annual maxima, the larger of the "
                    "half-year maxima: days 3 to 337 of their calendar years",
                    url=_IMGW_URL,
                ),
            ),
        ),
        Variable(
            name="year_days",
            symbol="L_i",
            unit="day",
            kind="real_array",
            description="Length of the year of each date, in the unit of the times.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1.0e9,
                test_reason=_HUGE_TIME_REASON,
            ),
            applicability="unstated",
            typical=Range(
                low=365.0,
                high=366.0,
                source=Source(
                    citation=_FEH.citation,
                    locator="Additional Note 16.1: LENYR, 365 or 366 days",
                    url=_FEH.url,
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="mean_fraction",
            unit="-",
            symbol="f",
            description="Direction of the mean vector as the fraction of the year.",
            physical=Range(low=0.0, high=1.0),
        ),
        Output(
            name="concentration",
            unit="-",
            symbol="r",
            description="Length of the mean vector: 1 for one time, near 0 when the "
            "times spread over the year.",
            physical=Range(low=0.0, high=1.0),
            boundary_tolerance=1e-13,
        ),
    ),
    sources=(_BAYLISS_JONES, _FEH, _HALL_BLOSCHL, _BURN),
    constraints=(
        Constraint(
            name="same_length",
            cls="physical",
            check=lambda x: x.array("elapsed_days").shape == x.array("year_days").shape,
            text="one year length per time",
            source=_FEH,
            satisfied={"year_days": [365.0, 365.0, 365.0, 366.0, 365.0, 365.0, 365.0]},
            violated={"year_days": [365.0, 365.0, 365.0, 366.0, 365.0, 365.0]},
        ),
        Constraint(
            name="within_its_year",
            cls="physical",
            check=lambda x: (
                x.array("elapsed_days").shape == x.array("year_days").shape
                and bool(np.all(x.array("elapsed_days") < x.array("year_days")))
            ),
            text="0 <= t_i < L_i: each time lies in its year",
            source=_FEH,
            satisfied={"elapsed_days": [364.5, 78.5, 91.5, 58.5, 88.5, 363.5, 4.5]},
            boundary={"elapsed_days": [365.0, 78.5, 91.5, 58.5, 88.5, 363.5, 4.5]},
            boundary_holds=False,
            violated={"elapsed_days": [400.0, 78.5, 91.5, 58.5, 88.5, 363.5, 4.5]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="time_in_another_unit",
                inputs={"elapsed_days": 1.0, "year_days": 1.0},
                outputs={},
                tolerance=Tolerance(
                    abs=1e-300,
                    reason="t / L is the same float when both double, but for a "
                    "subnormal angle",
                ),
            ),
        ),
        symmetries=(
            Symmetry(
                name="reversed_order",
                text="the times in reverse order give the same concentration",
                inputs=lambda x: {
                    "elapsed_days": x.array("elapsed_days")[::-1].copy(),
                    "year_days": x.array("year_days")[::-1].copy(),
                },
                outputs=lambda out: {"concentration": out.real("concentration")},
                tolerance=Tolerance(
                    abs=1e-15, reason="the same terms summed in another order"
                ),
            ),
        ),
        limits=(
            Limit(
                name="one_time",
                text="a single time is its own mean, with r = 1",
                inputs={"elapsed_days": [100.5], "year_days": [365.0]},
                expected={"mean_fraction": 100.5 / 365.0, "concentration": 1.0},
                tolerance=Tolerance(
                    abs=1e-15,
                    reason="atan2 of the cosine and sine of an angle gives it back "
                    "within a few ulps of 2 pi",
                ),
            ),
            Limit(
                name="opposite_times",
                text="two times half a year apart have no direction: r = 0",
                inputs={"elapsed_days": [0.5, 183.5], "year_days": [366.0, 366.0]},
                expected={"concentration": 0.0},
                tolerance=Tolerance(
                    abs=4e-16,
                    reason="the cosines and sines of angles rounded to a few 1e-16 "
                    "cancel to that, not to zero",
                ),
            ),
            Limit(
                name="quadrant_rules",
                text="the direction and length equal Bayliss and Jones's arctan with "
                "the quadrant rules and their r, of sums by math.fsum",
                check=_bayliss_jones,
            ),
        ),
    ),
    validation="none: a description of the timing of floods; Bayliss and Jones "
    "(1992) and the FEH map it for British rivers, Hall and Blöschl (2018) for Europe",
    formula_version=1,
    status="oracle only",
    conventions=(
        "the times and the lengths of their years in one unit of time, days for "
        "dates; the angle 2 pi t / L of a time t from the start of its year of L",
        "for dates t is the day of the year minus a half, the middle of the day, and L "
        "365 or 366 (Bayliss and Jones's ADJUST, FEH's day no. - 0.5); Hall and "
        "Blöschl (2018) take the day itself, D 2 pi / m_i",
        "the mean direction atan2(ybar, xbar) taken into [0, 2 pi): Bayliss and Jones "
        "and the FEH add pi or 2 pi to arctan(ybar / xbar) by the signs, the same "
        "angle; at xbar = ybar = 0 the direction is undefined (Hall and Blöschl) and "
        "the formula gives 0, as scipy.stats.circmean does",
        "near r = 0 the direction is ill-conditioned: a rounding moves it; read the "
        "mean with r (Bayliss and Jones, section 3.3; the FEH)",
    ),
    assumptions=(
        "the times are the dates of independent events, one annual extreme per year; "
        "Hall and Blöschl keep the stations where a Rayleigh test rejects uniform "
        "dates, which Hydrolog does not compute",
    ),
    traps={
        "singular_at_bound": "atan2 at xbar = ybar = 0 has no direction: limit "
        "opposite_times and test_no_direction_gives_the_start_of_the_year",
        "gap_propagation": "type cases elapsed_days-nan_element and "
        "year_days-nan_element: a gap is refused",
        "many_small_terms": "test_many_dates_keep_their_sums: 100,000 dates against "
        "math.fsum of the cosines and sines",
    },
    oracles=(
        Oracle(
            kind="algorithm",
            description="Bayliss and Jones's (1992) and the FEH's arctan(ybar / xbar) "
            "with pi or 2 pi added by the signs, and r, of sums by math.fsum",
            test="tests/unit/test_formulas_regime.py (limit quadrant_rules)",
        ),
        Oracle(
            kind="established",
            description="scipy.stats.circmean of the angles (SciPy 1.18)",
            test="tests/unit/test_formulas_regime.py "
            "(test_the_mean_direction_is_scipys)",
            conventions=(
                "circmean returns the mean angle in [low, high) = [0, 2 pi), the "
                "formula's direction; it takes the angles as given, so both sides "
                "get Bayliss and Jones's half-day offset",
                "Hall and Blöschl's D 2 pi / m_i without the offset moves the mean day "
                "by 0.5 (1 - 365.25 / L) of a day, at most 0.001 day",
            ),
        ),
    ),
    base={
        "elapsed_days": [73.5, 78.5, 91.5, 58.5, 88.5, 363.5, 4.5],
        "year_days": [365.0, 365.0, 365.0, 366.0, 365.0, 365.0, 365.0],
    },
)

SPECS: Final[tuple[FormulaSpec, ...]] = (CIRCULAR_MEAN,)
"""The Tier A formula of the module."""

_MEAN_YEAR = Constant(
    name="mean_year_days",
    value=Fraction(1461, 4),
    unit="day",
    symbol="m",
    source=Source(
        citation=_HALL_BLOSCHL.citation,
        locator="eq. 2: m, the mean number of days per year, taken as 365.25, the "
        "mean of 1901-2099; Bayliss and Jones (1992, p. 19) take 365",
        url=_HALL_BLOSCHL.url,
    ),
)
_IMGW_HALF_YEARS = Source(
    citation="IMGW-PIB, Rocznik Hydrologiczny 2022 and hydrologia_info_ogolne.txt of "
    "the public data",
    locator="the winter half-year 1 November to 30 April, the summer one 1 May to 31 "
    "October; the hydrological year named after the year of its end; no "
    "characteristic for a period with a break in the observations",
    url=_IMGW_URL,
)

TIER_B: Final[tuple[TierBSpec, ...]] = (
    TierBSpec(
        name="circular_mean_of_dates",
        function="hydrolog.statistics.seasonality.circular_mean_date",
        definition="The time of each date, its day of the calendar year (1 = 1 "
        "January) minus a half, and the length of its year, 365 or 366 days; their "
        "circular_mean; the mean day 365.25 f + 0.5 and its MM-DD in the common year "
        "2001",
        convention="leap years by the Gregorian rule; the direction back to a day on "
        "the mean year of 365.25 days (Hall and Blöschl's m; Bayliss and Jones take "
        "365, up to a quarter of a day earlier at the end of the year); the date of "
        "the mean day rounded by Python's round (a half to the even day), a day "
        "beyond 365 on 31 December",
        source=_BAYLISS_JONES,
        constants=(_MEAN_YEAR,),
    ),
    TierBSpec(
        name="extremes_of_complete_years",
        function="hydrolog.statistics.seasonality.daily_extremes",
        definition="The maximum or minimum of each complete hydrological year of a "
        "daily series, dated by the first day it occurs",
        convention="a year counts only with a value for every day, as IMGW-PIB gives "
        "no characteristic for a period with a break; the extremes are of daily "
        "values, not of all observations",
        source=_IMGW_HALF_YEARS,
    ),
    TierBSpec(
        name="extremes_of_half_years",
        function="hydrolog.statistics.seasonality.half_year_extremes",
        definition="IMGW-PIB's annual maximum, the larger of the half-year maxima (the "
        "winter one when they are equal), or minimum, the smaller of the minima, "
        "with the date of that half-year's extreme",
        convention="a year without both half-years has no extreme; one whose extreme "
        "has no date is left out and named",
        source=_IMGW_HALF_YEARS,
    ),
    TierBSpec(
        name="seasonality_of_extremes",
        function="hydrolog.statistics.seasonality.extreme_seasonality",
        definition="The circular mean date and concentration of the dated annual "
        "extremes and their shares in the winter (November to April) and the summer "
        "(May to October) half-year",
        convention="IMGW-PIB's half-years by the calendar month of each date",
        source=_IMGW_HALF_YEARS,
    ),
)
"""The Tier B formulas of the module (Nogat CMP-2.2)."""


def _leap(years: NDArray[np.int64]) -> NDArray[np.bool_]:
    """Return whether each year is a leap year of the Gregorian calendar."""
    leap: NDArray[np.bool_] = (years % 4 == 0) & (
        (years % 100 != 0) | (years % 400 == 0)
    )
    return leap


def circular_mean(
    elapsed_days: NDArray[np.float64] | Sequence[float],
    year_days: NDArray[np.float64] | Sequence[float],
) -> CircularMeanTime:
    """Return the circular mean of times in their years, spec circular_mean.

    Parameters
    ----------
    elapsed_days : array_like of float
        Time of each date from the start of its year [days].
    year_days : array_like of float
        Length of the year of each date [days].

    Returns
    -------
    CircularMeanTime
        The direction of the mean vector as a fraction of the year and its length.

    Raises
    ------
    InvalidParameterError
        If the times are refused by the spec: none, not finite, negative, of
        different lengths or beyond their years.
    """
    x = checked_inputs(CIRCULAR_MEAN, elapsed_days=elapsed_days, year_days=year_days)
    fraction, concentration = _circular(x.array("elapsed_days"), x.array("year_days"))
    out = checked_outputs(
        CIRCULAR_MEAN, {"mean_fraction": fraction, "concentration": concentration}
    )
    return CircularMeanTime(out.real("mean_fraction"), out.real("concentration"))


def circular_mean_date(
    dates: Sequence[str] | NDArray[np.datetime64],
) -> CircularMean:
    """Return the mean date and the concentration of dates over the year.

    The times of the dates in their years go to :func:`circular_mean` and its
    direction comes back as a day of the mean year (:data:`TIER_B`).

    Parameters
    ----------
    dates : sequence of str or NDArray[np.datetime64]
        ISO dates; at least one.

    Returns
    -------
    CircularMean
        The mean day of the year, its ``MM-DD`` and the concentration r.

    Raises
    ------
    InvalidParameterError
        If there is no date.
    """
    days = np.asarray(dates, dtype="datetime64[D]")
    years, _, day_of_year = _calendar(days)
    elapsed = (day_of_year - 0.5).astype(np.float64)
    mean = circular_mean(elapsed, (365 + _leap(years)).astype(np.float64))
    mean_day = mean.mean_fraction * float(_MEAN_YEAR.value) + 0.5
    whole = min(max(round(mean_day), 1), 365)
    moment = np.datetime64("2001-01-01", "D") + np.timedelta64(whole - 1, "D")
    return CircularMean(mean_day, str(moment)[5:], mean.concentration)


def daily_extremes(
    values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    statistic: Statistic,
) -> tuple[list[DatedExtreme], AnnualExtremes]:
    """Return the dated extremes of the complete hydrological years of a daily series.

    A hydrological year is complete when every one of its days has a value
    (:func:`~hydrolog.statistics._hydrological_year.annual_extremes`); the date of its
    extreme is the first day with that value.

    Parameters
    ----------
    values : NDArray[np.float64]
        Daily values; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates, strictly increasing (days may be absent).
    statistic : {"max", "min"}
        The annual maximum or minimum.

    Returns
    -------
    list of DatedExtreme
        The extreme of each complete year, in order.
    AnnualExtremes
        The complete years and those skipped as incomplete.
    """
    flows = np.asarray(values, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[D]")
    extremes = annual_extremes(flows, days, statistic)
    year_of_day = hydrological_year(days)
    known = np.isfinite(flows)
    out: list[DatedExtreme] = []
    for year in extremes.years.tolist():
        mine = np.flatnonzero((year_of_day == year) & known)
        pick = np.argmax if statistic == "max" else np.argmin
        at = int(mine[pick(flows[mine])])
        out.append(DatedExtreme(int(year), float(flows[at]), str(days[at])))
    return out, extremes


def half_year_extremes(
    half_years: HalfYearValues, statistic: Statistic
) -> tuple[list[DatedExtreme], list[int]]:
    """Return IMGW-PIB's dated annual extremes from its half-year values.

    The annual maximum is the larger of the two half-year maxima (the winter one when
    they are equal), the annual minimum the smaller of the minima, each with the date
    of that half-year's extreme; a year without both half-years has none
    (:func:`~hydrolog.statistics.characteristic_values_from_half_years`).

    Parameters
    ----------
    half_years : HalfYearValues
        The published values of one variable.
    statistic : {"max", "min"}
        The annual maximum or minimum.

    Returns
    -------
    list of DatedExtreme
        The dated annual extremes, in order.
    list of int
        The years whose extreme has no date in the file (left out).
    """
    rows = characteristic_values_from_half_years(half_years).years
    out: list[DatedExtreme] = []
    undated: list[int] = []
    for row in rows:
        annual = row.annual
        value = annual.max if statistic == "max" else annual.min
        date = annual.max_date if statistic == "max" else annual.min_date
        if value is None:
            continue
        if date is None:
            undated.append(row.year)
            continue
        out.append(DatedExtreme(row.year, value, date))
    return out, undated


def extreme_seasonality(
    extremes: Sequence[DatedExtreme],
    *,
    statistic: Statistic,
    parameter: str,
    source: str,
) -> ExtremeSeasonality:
    """Compute the seasonality of dated annual extremes.

    Parameters
    ----------
    extremes : sequence of DatedExtreme
        The dated annual extremes of the years of the period; at least one.
    statistic : {"max", "min"}
        Whether they are maxima or minima.
    parameter : str
        The variable (``"Q"``, ``"H"``, ``"T"``).
    source : {"daily", "half_years"}
        Where they come from.

    Returns
    -------
    ExtremeSeasonality
        The mean date, the concentration and the half-year shares of the extremes.

    Raises
    ------
    InvalidParameterError
        If there is no extreme.
    """
    if not extremes:
        raise InvalidParameterError("extreme_seasonality needs at least one extreme")
    rows = list(extremes)
    days = np.array([row.date for row in rows], dtype="datetime64[D]")
    mean = circular_mean_date(days)
    _, months, _ = _calendar(days)
    in_winter = (months >= 11) | (months <= 4)
    return ExtremeSeasonality(
        statistic=statistic,
        parameter=parameter,
        source=source,
        first_year=rows[0].year,
        last_year=rows[-1].year,
        period_years=len(rows),
        years=rows,
        mean_day=mean.mean_day,
        mean_date=mean.mean_date,
        concentration=mean.concentration,
        winter_share=float(np.mean(in_winter)),
        summer_share=float(np.mean(~in_winter)),
    )
