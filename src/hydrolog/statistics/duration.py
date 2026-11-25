"""Duration curves of daily series and the frequencies of their classes.

The duration curve gives the value equalled or exceeded on p % of the days (the
„krzywa sum czasów trwania wraz z wyższymi” of Polish practice). Its values are the
formula :data:`EXCEEDANCE_VALUES` (spec ``exceedance_values``, Nogat's computation
standard, ADR-0050 and ADR-0063): the n values ranked from the highest have the
Weibull plotting positions m / (n + 1), a percentage between two positions is
interpolated linearly between their values (Vogel and Fennessey, 1994, eq. 3; method
R6 of Hyndman and Fan, NIST/SEMATECH e-Handbook, 7.2.6.2) and the end values hold
beyond the extreme positions. The classes count the days of each class of values from
the highest down, with the cumulative days „including higher” and „including lower”
and their split by hydrological month, as Searcy's (1959) total-period method counts
them (Byczkowski 1996; the author's table of 2024). The classes and the days the curve
takes are Tier B (:data:`TIER_B`); ``docs/FORMULAS.md`` shows the equations, ranges
and sources. Searcy (1959) and WMO-No. 1029 (sect. 6.1) give the days of a class
their share i/N of the record; the positions of the curve are m / (n + 1).

Beside that curve of the whole period, the median annual curve of Vogel and Fennessey
(1994) takes the curve of each complete hydrological year and, per percentage, the
median of the annual values, with its interval: the pair of their order statistics
whose binomial coverage is at least the confidence level asked, the years taken as
independent (:data:`DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL`, spec
``duration_curve_annual_median_interval``; Helsel and Hirsch, 2002, sect. 3.3.1).

Examples
--------
The positions of four values are 20, 40, 60 and 80 %; between them the values are
interpolated, beyond them held:

>>> exceedance_values([10.0, 20.0, 30.0, 40.0], [20.0, 50.0, 80.0, 95.0])
array([40., 25., 10., 10.])

A day without a value is left out:

>>> exceedance_values([10.0, float("nan"), 30.0], [50.0])
array([20.])

The median of six annual values and its interval at the level 0.95: the smallest and
the largest of them, whose binomial coverage is 1 - 2 / 2**6 = 0.96875:

>>> found = annual_median_interval([[3.0], [1.0], [2.0], [6.0], [5.0], [4.0]], [0.95])
>>> found.median.tolist(), found.lower.tolist(), found.upper.tolist()
([3.5], [[1.0]], [[6.0]])

References
----------
Searcy, J. K. (1959): Flow-duration curves. Manual of Hydrology, Part 2. USGS
    Water-Supply Paper 1542-A.
Vogel, R. M. & Fennessey, N. M. (1994): Flow-duration curves. I: New interpretation
    and confidence intervals. Journal of Water Resources Planning and Management
    120(4), 485-504.
NIST/SEMATECH (2012): e-Handbook of Statistical Methods, section 7.2.6.2,
    Percentiles.
Byczkowski, A. (1996): Hydrologia, t. 1. Wydawnictwo SGGW, Warszawa.
Helsel, D. R. & Hirsch, R. M. (2002): Statistical Methods in Water Resources. USGS
    Techniques of Water-Resources Investigations, book 4, chapter A3.
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from typing import Final, Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog._warnings import IntervalNotComputed
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
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
    FIRST_MONTH,
    days_in_hydrological_year,
    hydrological_year,
)
from hydrolog.statistics.intervals import (
    ConfidenceInterval,
    interval_entries,
    intervals_not_computed,
)
from hydrolog.statistics.intervals import (
    confidence_levels as asked_levels,
)

__all__ = [
    "CURVE_PERCENTS",
    "DEFAULT_PERCENTS",
    "DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL",
    "EXCEEDANCE_VALUES",
    "SPECS",
    "TIER_B",
    "AnnualMedianInterval",
    "DurationClass",
    "DurationCurve",
    "ModalClass",
    "annual_median_interval",
    "duration_curve",
    "exceedance_values",
]

BinMethod = Literal["width", "log"]

CURVE_PERCENTS: tuple[float, ...] = (
    0.1,
    0.2,
    0.5,
    *(float(percent) for percent in range(1, 100)),
    99.5,
    99.8,
    99.9,
)
"""Exceedance percentages of the drawn curve (:attr:`DurationCurve.curve_values`)."""

DEFAULT_PERCENTS: tuple[float, ...] = (
    1.0,
    5.0,
    10.0,
    30.0,
    50.0,
    70.0,
    90.0,
    95.0,
    99.0,
)
"""Exceedance percentages of the table when none are given."""

# Calendar months in the order of the hydrological year: November first.
_HYDROLOGICAL_MONTHS = (11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)


# --- the values of the curve (spec exceedance_values) ---------------------------------

_VF94: Final = Source(
    citation="Vogel, R.M. and Fennessey, N.M. (1994). Flow-duration curves. I: New "
    "interpretation and confidence intervals. Journal of Water Resources Planning and "
    "Management 120(4), 485-504 (the authors' copy)",
    locator="pp. 488-489, eqs. (2a) and (3): Q_p,2 = (1 - theta) q(i) + theta q(i+1) "
    "with i = [(n + 1) p] and theta = (n + 1) p - i, the ordered observations q(i) "
    "plotted at the Weibull position p_i = i / (n + 1)",
    url="https://sites.tufts.edu/richardvogel/files/2019/04/flowDuration1.pdf",
)
_NIST: Final = Source(
    citation="NIST/SEMATECH (2012). e-Handbook of Statistical Methods, section "
    "7.2.6.2, Percentiles",
    locator="p (N + 1) = k + d: Y(p) = Y[k] + d (Y[k+1] - Y[k]) for 0 < k < N, Y[1] "
    "for k = 0 and Y[N] for k >= N, method R6 of Hyndman and Fan (1996); the "
    "example of twelve resistivities, 90th percentile 95.1981 ohm.cm",
    url="https://www.itl.nist.gov/div898/handbook/prc/section2/prc262.htm",
)
_SEARCY: Final = Source(
    citation="Searcy, J.K. (1959). Flow-duration curves. Manual of Hydrology, Part 2, "
    "Low-flow techniques. U.S. Geological Survey Water-Supply Paper 1542-A",
    locator="p. 3: the total-period method, the days of each class cumulated from the "
    "highest class; figs. 4-5 (form 9-217c), p. 9: the days equal to or greater than "
    "a class limit and less than the next",
    url="https://pubs.usgs.gov/wsp/1542a/report.pdf",
)
_WMO_1029: Final = (
    "WMO (2008). Manual on Low-flow Estimation and Prediction, WMO-No. 1029, "
    "Operational Hydrology Report No. 50 (Gustard, A. and Demuth, S., eds.)"
)
_WMO_1029_URL: Final = "https://library.wmo.int/idurl/4/32176"
_KLODZKO: Final = Source(
    citation="IMGW-PIB, public hydrological data: the half-yearly characteristic "
    "flows (polr_Q) of station 150160180 Kłodzko on the Nysa Kłodzka, hydrological "
    "years 1971-2015 (1997 absent)",
    locator="the lowest flow NNQ 1.24 m3/s (2015) and the highest WWQ 522 m3/s "
    "(2006), between which its daily mean flows lie",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/"
    "dane_hydrologiczne/",
)


def _normalised(data: NDArray[np.float64]) -> tuple[NDArray[np.float64], int]:
    """Return the values over the power of two bringing the largest into [½, 1).

    The division is exact, so the curve of the scaled values, multiplied back, is the
    curve of the values, and a difference of two values near the largest float does
    not overflow.
    """
    largest = float(np.max(np.abs(data)))
    exponent = math.frexp(largest)[1] if largest > 0.0 else 0
    return np.ldexp(data, -exponent), exponent


def _exceedance(x: Values) -> NDArray[np.float64]:
    """Return Q_p of checked inputs: eq. (3) of Vogel and Fennessey, ends held."""
    data = x.array("values")
    scaled, exponent = _normalised(data[~np.isnan(data)])
    ordered = np.sort(scaled)[::-1]  # q(1) >= q(2) >= ... >= q(n)
    count = ordered.size
    position = x.array("exceedance_percent") * (count + 1) / 100.0  # (n + 1) p
    rank = np.floor(position)
    inside = (rank >= 1) & (rank < count)
    first = np.clip(rank, 1, count).astype(np.intp) - 1
    second = np.minimum(first + 1, count - 1)
    theta = np.where(inside, position - rank, 0.0)
    value = ordered[first] + theta * (ordered[second] - ordered[first])
    return np.ldexp(value, exponent)


def _exact_values(values: Sequence[float], percents: Sequence[float]) -> list[float]:
    """Q_p,2 of Vogel and Fennessey (1994, eq. 3) in rational arithmetic, ends held."""
    known = sorted((Fraction(v) for v in values if not math.isnan(v)), reverse=True)
    count = len(known)
    out: list[float] = []
    for percent in percents:
        position = Fraction(percent) * (count + 1) / 100
        rank = math.floor(position)
        if rank < 1:
            out.append(float(known[0]))
        elif rank >= count:
            out.append(float(known[-1]))
        else:
            theta = position - rank
            out.append(float((1 - theta) * known[rank - 1] + theta * known[rank]))
    return out


_RATIONAL_SERIES: Final = (
    (
        (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0),
        (10.0, 50.0, 90.0, 5.0, 95.0, 15.0),
    ),
    (
        (0.0, 0.0, 0.12, 0.12, 0.35, 1.7, 1.7, 1.7, 4.93, 96.0),
        (0.1, 10.0, 33.3, 50.0, 66.7, 70.0, 90.0, 95.0, 99.9),
    ),
    ((-12.0, -3.5, 0.0, 41.0, 41.0, 205.5), (1.0, 14.2857, 50.0, 85.7143, 99.0)),
    ((math.nan, 3.0, math.nan, 1.0, 2.0), (12.5, 25.0, 37.5, 50.0, 62.5, 75.0, 87.5)),
    ((61.0,), (0.1, 50.0, 99.9)),
    ((2.57, 1.66), (10.0, 33.3333, 50.0, 66.6667, 90.0)),
)
"""Series of the exact oracle: whole numbers, decimal flows with zeros and ties, stages
below the gauge's zero, gaps, one value and two."""


def _seeded_series() -> tuple[list[float], list[float]]:
    """Return 400 seeded daily flows rounded to 0.01 m3/s and the curve's percents."""
    flows = np.round(np.random.default_rng(20261119).gamma(0.8, 12.0, 400), 2)
    return flows.tolist(), list(CURVE_PERCENTS)


def _rational_curve(run: Callable[..., Values]) -> None:
    for values, percents in (*_RATIONAL_SERIES, _seeded_series()):
        known = [v for v in values if not math.isnan(v)]
        spread = max(known) - min(known)
        largest = max(abs(v) for v in known)
        out = run(values=list(values), exceedance_percent=list(percents))
        assert_within(
            out.array("exceedance_values"),
            _exact_values(values, percents),
            abs=2.3e-16 * ((len(known) + 1) * spread + 4.0 * largest),
            reason="eq. (3) of Vogel and Fennessey in exact rational arithmetic from "
            "the float inputs: (n + 1) p / 100 rounds twice, by 2.3e-16 (n + 1) at "
            "most, which moves theta times the spread, and the interpolation rounds "
            "by a few units in the last place of the largest value",
        )


def _mirrored(x: Values) -> dict[str, object]:
    return {
        "values": -x.array("values"),
        "exceedance_percent": 100.0 - x.array("exceedance_percent"),
    }


_CURVE_PERCENTS_SOURCE: Final = Source(
    citation="Hydrolog's duration curve: CURVE_PERCENTS of hydrolog.statistics."
    "duration, the percentages of every drawn curve, and the table's "
    "DEFAULT_PERCENTS; the thresholds Q70, Q90 and Q95 of Polish low-flow studies "
    "(Tokarczyk 2010, p. 32; Tomaszewski 2012, p. 68) lie between",
    locator="0.1 to 99.9 %",
)
_ANY_VALUE_REASON: Final = (
    "the curve is homogeneous in the unit of the series (its scaling), so any bound "
    "tests its arithmetic: a million m3/s exceeds the discharge of every river, and a "
    "stage below its gauge's zero or a temperature may be negative, so the same bound "
    "holds below 0"
)
_EXACT_SCALING: Final = Tolerance(
    abs=1e-300,
    rel=4.5e-16,
    reason="the curve runs on the values divided by a power of two, so doubling them "
    "changes no rounding; a value below the normal floats keeps fewer bits",
)

EXCEEDANCE_VALUES: Final = FormulaSpec(
    name="exceedance_values",
    title="Values of the duration curve equalled or exceeded on p % of the days "
    "(Weibull positions, linear interpolation)",
    function="hydrolog.statistics.duration.exceedance_values",
    family="statistic",
    equation=(
        "q(1) >= ... >= q(n) the n values with a value; h = (n + 1) p / 100, i = "
        "floor(h), theta = h - i; Q_p = q(i) + theta (q(i+1) - q(i)) for 1 <= i < n, "
        "q(1) for i < 1 and q(n) for i >= n"
    ),
    latex=(
        r"Q_p = q_{(i)} + \theta\,\bigl(q_{(i+1)} - q_{(i)}\bigr),\quad i = "
        r"\left\lfloor \tfrac{(n+1)\,p}{100} \right\rfloor,\quad \theta = "
        r"\tfrac{(n+1)\,p}{100} - i,\quad q_{(1)} \ge \dots \ge q_{(n)}"
    ),
    variables=(
        Variable(
            name="values",
            symbol="q",
            unit="m3/s",
            kind="real_array",
            description="The daily values of the series, in any order; NaN on a day "
            "without a value, which is left out.",
            physical=Range(
                test_low=-1.0e6, test_high=1.0e6, test_reason=_ANY_VALUE_REASON
            ),
            applicability="unstated",
            typical=Range(low=1.24, high=522.0, source=_KLODZKO),
            gaps_allowed=True,
        ),
        Variable(
            name="exceedance_percent",
            symbol="p",
            unit="%",
            kind="real_array",
            description="The percentages of the days on which the value is equalled or "
            "exceeded.",
            physical=Range(
                low=0.0, high=100.0, low_inclusive=False, high_inclusive=False
            ),
            applicability="unstated",
            typical=Range(low=0.1, high=99.9, source=_CURVE_PERCENTS_SOURCE),
        ),
    ),
    outputs=(
        Output(
            name="exceedance_values",
            unit="m3/s",
            kind="real_array",
            symbol="Q_p",
            description="The value equalled or exceeded on each percentage of the "
            "days, in the unit of the series.",
            physical=Range(),
        ),
    ),
    sources=(_VF94, _NIST),
    constraints=(
        Constraint(
            name="has_values",
            cls="precondition",
            check=lambda x: bool(np.any(~np.isnan(x.array("values")))),
            text="n >= 1: at least one day with a value",
            source=_NIST,
            satisfied={"values": [5.0, math.nan]},
            violated={"values": [math.nan, math.nan]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"values": 1, "exceedance_percent": -1},
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={"exceedance_values": 1.0},
                tolerance=_EXACT_SCALING,
            ),
        ),
        symmetries=(
            Symmetry(
                name="mirror",
                text="the negated series at 100 - p gives the negated value at p: the "
                "positions m / (n + 1) are symmetric",
                inputs=_mirrored,
                outputs=lambda out: {
                    "exceedance_values": -out.array("exceedance_values")
                },
                tolerance=Tolerance(
                    abs=1e-6,
                    reason="100 - p and (n + 1) p / 100 round, moving theta by a few "
                    "units in the last place of n + 1 (at most 51 values are drawn), "
                    "times a spread of at most 2e6 within the test bounds of the "
                    "values: about 1e-8",
                ),
            ),
        ),
        limits=(
            Limit(
                name="plotting_positions",
                text="at its position m / (n + 1) the curve gives the m-th largest "
                "value, halfway between two positions their mean",
                inputs={
                    "values": [30.0, 10.0, 40.0, 20.0],
                    "exceedance_percent": [20.0, 40.0, 50.0, 60.0, 80.0],
                },
                expected={"exceedance_values": [40.0, 30.0, 25.0, 20.0, 10.0]},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="n + 1 = 5 and multiples of 20 % make (n + 1) p / 100 whole "
                    "or a half, and the values over a power of two are exact",
                ),
                source=_VF94,
            ),
            Limit(
                name="end_values_held",
                text="before the first position the curve holds the largest value, "
                "after the last the smallest (NIST's k = 0 and k >= N)",
                inputs={
                    "values": [30.0, 10.0, 40.0, 20.0],
                    "exceedance_percent": [1.0, 19.9, 80.1, 99.0],
                },
                expected={"exceedance_values": [40.0, 40.0, 10.0, 10.0]},
                tolerance=Tolerance(
                    abs=0.0, reason="values of the series, not computed"
                ),
                source=_NIST,
            ),
            Limit(
                name="constant_series",
                text="a series of equal values (ties) gives that value at every "
                "percentage, and a day without a value changes nothing",
                inputs={
                    "values": [7.5, 7.5, math.nan, 7.5, 7.5, 7.5],
                    "exceedance_percent": [1.0, 50.0, 99.0],
                },
                expected={"exceedance_values": [7.5, 7.5, 7.5]},
                tolerance=Tolerance(abs=0.0, reason="the value plus theta times zero"),
            ),
            Limit(
                name="exact_rational",
                text="the values equal eq. (3) of Vogel and Fennessey in exact "
                "rational arithmetic, on whole numbers, decimal flows with zeros and "
                "ties, negative stages, gaps, one and two values and 400 seeded flows",
                check=_rational_curve,
            ),
        ),
    ),
    validation=(
        "none: a nonparametric estimate from the observed series itself; Vogel and "
        "Fennessey (1994) compare its sampling properties, not its agreement with "
        "observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "p is the exceedance percentage: the share of the days with a value on which "
        "the value is equalled or exceeded (krzywa sum czasów trwania wraz z "
        "wyższymi); Q_p is the (100 - p)-th percentile of the values",
        "the Weibull plotting position m / (n + 1) of the value of rank m from the "
        "highest, linear interpolation between positions: Q_p,2 of Vogel and "
        "Fennessey (1994, eq. 3), method R6 of Hyndman and Fan (NIST e-Handbook "
        "7.2.6.2), numpy's method 'weibull' and R's quantile type 6",
        "beyond the extreme positions 100 / (n + 1) and 100 n / (n + 1) % the end "
        "values hold, as R6 sets k = 0 to the minimum and k >= N to the maximum; "
        "Vogel and Fennessey leave Q_p,2 undefined before the first position and "
        "recommend interpolating to q(n+1) = 0 after the last, which Hydrolog does not",
        "not the class method of Searcy (1959) and WMO-No. 1029 (sect. 6.1), whose "
        "share of a class is i / N, nor lfstat's Qxx (R's quantile type 7)",
        "equal values (ties) keep a position each and zeros are values; a day without "
        "a value (NaN) is left out, n counts the days with a value",
        "the series in any unit: the values of the curve in that unit (m3/s in the "
        "documents, cm for stages)",
        "the interpolation runs on the values divided by a power of two, so a "
        "difference of two values near the largest float does not overflow",
    ),
    assumptions=(
        "the values are those of one station over one period: the curve describes "
        "that period (the period-of-record curve of Vogel and Fennessey), not a "
        "climate",
        "no independence of the days is needed: the curve is descriptive and has no "
        "interval; the median annual curve beside it, whose years are taken as "
        "independent, has one (spec duration_curve_annual_median_interval)",
    ),
    traps={
        "gap_propagation": "type case values-nan_element, limit constant_series and "
        "test_gaps_are_left_out: a day without a value is left out, never a NaN of the "
        "curve",
    },
    reference_cases=(
        "tests/fixtures/formulas/daily-cases.json",
        "tests/fixtures/formulas/camels-pl-cases.json",
    ),
    oracles=(
        Oracle(
            kind="exact",
            description="eq. (3) of Vogel and Fennessey (1994), (1 - theta) q(i) + "
            "theta q(i+1), in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_daily.py (limit exact_rational)",
        ),
        Oracle(
            kind="established",
            description="numpy.quantile with method='weibull' (NumPy 2.5) at the "
            "non-exceedance probability 1 - p / 100",
            test="tests/unit/test_formulas_daily.py "
            "(test_the_values_are_numpys_weibull_quantiles)",
            conventions=(
                "numpy's 'weibull' is Hyndman and Fan's type 6: the k-th smallest of "
                "n values at k / (n + 1), linear interpolation, the ends held",
                "numpy takes the non-exceedance probability; the exceedance "
                "percentage p is 1 - p / 100 of it, the positions being symmetric",
            ),
        ),
    ),
)


def exceedance_values(
    values: NDArray[np.float64] | Sequence[float],
    exceedance_percent: NDArray[np.float64] | Sequence[float],
) -> NDArray[np.float64]:
    """Return the duration curve's values at percentages, spec exceedance_values.

    Parameters
    ----------
    values : array_like of float
        The daily values of the series; ``NaN`` marks a day without a value, which
        is left out.
    exceedance_percent : array_like of float
        The percentages of the days on which the value is equalled or exceeded [%].

    Returns
    -------
    numpy.ndarray
        The value equalled or exceeded on each percentage, in the unit of the series.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec: a percentage outside the open interval of
        percentages, an infinite value, or no day with a value.
    """
    x = checked_inputs(
        EXCEEDANCE_VALUES, values=values, exceedance_percent=exceedance_percent
    )
    return checked_outputs(
        EXCEEDANCE_VALUES, {"exceedance_values": _exceedance(x)}
    ).array("exceedance_values")


# --- the median annual curve (spec duration_curve_annual_median_interval) -------------

_VF94_ANNUAL: Final = Source(
    citation=_VF94.citation,
    locator="pp. 494-497: 'Annual Interpretation of Flow-Duration Curves', the FDC of "
    "each of the n years from its own daily flows by Q_p,2 and, per exceedance "
    "probability, the median of the n annual values, the median annual FDC (p. 494), "
    "the distribution of daily flow in a typical year (p. 496); 'Confidence Intervals "
    "for Quantiles of Flow-Duration Curves', the n values Q_p(i) treated as a random "
    "sample (p. 496) and their interval, eqs. (10a)-(10b) (p. 497)",
    url=_VF94.url,
)
_HELSEL_HIRSCH: Final = Source(
    citation="Helsel, D.R. and Hirsch, R.M. (2002). Statistical Methods in Water "
    "Resources. Techniques of Water-Resources Investigations of the U.S. Geological "
    "Survey, book 4, chapter A3 (superseded by Techniques and Methods 4-A3, 2020)",
    locator="sect. 3.3.1, pp. 70-72, eqs. 3.2-3.3: the nonparametric interval of the "
    "median between the R_l-th observations from each end, R_l = x' + 1 and R_u = "
    "n - x', x' the critical value of the binomial distribution with p = 0.5 at "
    "alpha/2 (table B5); example 2, 25 arsenic concentrations: 4.8 <= C_0.5 <= 110 "
    "at alpha = 0.044",
    url="https://pubs.usgs.gov/twri/twri4a3/twri4a3.pdf",
)
_ECO_091: Final = Source(
    citation="Nogat (2026). Decisions of the ecosystem, ECO-091: Intervals beside "
    "point estimates, computed by Hydrolog, shown by Obserwator",
    locator="two-sided and central at each confidence_level asked; Obserwator stores "
    "0.95 and 0.68",
    url="https://github.com/Daldek/Nogat/blob/main/standards/DECISIONS.md",
)


def _pair_rank(count: int, level: float) -> int:
    """Return the k of the pair Q(k), Q(N + 1 - k) of N annual values at a level c.

    The largest k >= 1 whose coverage 1 - 2 F(k - 1) is at least c, F the binomial
    distribution function of N trials with probability 1/2, or 0 when even k = 1
    falls short. Exact in integers: c is a / b, as every float is, and the coverage
    is at least c when 2 b S <= (b - a) 2**N, S = C(N, 0) + ... + C(N, k - 1).
    """
    share = Fraction(level)
    allowed = (share.denominator - share.numerator) << count
    term, tail, rank = 1, 0, 0  # C(N, k - 1), S and the k found
    for k in range(1, count // 2 + 1):
        tail += term
        if 2 * share.denominator * tail > allowed:
            break
        rank = k
        term = term * (count - k + 1) // k
    return rank


def _years_needed(level: float) -> int:
    """Return the fewest years whose extreme pair, k = 1, reaches the level c.

    The smallest N with 1 - 2**(1 - N) >= c, exact in integers as in
    :func:`_pair_rank`; one year has no pair.
    """
    share = Fraction(level)
    count = 2
    while 2 * share.denominator > (share.denominator - share.numerator) << count:
        count += 1
    return count


_ORACLE_SEED: Final = 20261125
_EXACT_COVERAGES: Final = 53
"""Up to this many years every coverage, a multiple of 2**(1 - N), is a float."""


def _exact_ranks(count: int, levels: Sequence[float]) -> list[int]:
    """Return per level the oracle's k at N years, 0 where no pair reaches it.

    The pair Q(k), Q(N + 1 - k) holds the median when from k to N - k of the N
    values lie below it, B ~ Bin(N, 1/2): its coverage is the middle terms of the
    binomial distribution summed as fractions, and k the largest whose coverage is
    at least c.
    """
    whole = 2**count
    inside = {
        k: Fraction(sum(math.comb(count, j) for j in range(k, count - k + 1)), whole)
        for k in range(1, count // 2 + 1)
    }
    return [
        max((k for k, held in inside.items() if held >= Fraction(level)), default=0)
        for level in levels
    ]


def _levels_to_try(count: int) -> list[float]:
    """Return usual levels and, up to 53 years, each coverage and the float above it."""
    levels = {0.5, 0.68, 0.8, 0.9, 0.95, 0.99, 0.999}
    if count <= _EXACT_COVERAGES:
        whole = 2**count
        for k in range(1, count // 2 + 1):
            middle = sum(math.comb(count, j) for j in range(k, count - k + 1))
            coverage = float(Fraction(middle, whole))
            levels |= {coverage, math.nextafter(coverage, 1.0)}
    return sorted(levels)


def _binomial_pairs(run: Callable[..., Values]) -> None:
    """Assert the pairs of 1 to 200 years against the binomial coverage in fractions."""
    order = np.random.default_rng(_ORACLE_SEED)
    for count in (*range(1, 61), *range(61, 200, 13), 200):
        ranks = order.permutation(count) + 1.0  # the k-th smallest value is k
        levels = _levels_to_try(count)
        out = run(annual_values=ranks[:, np.newaxis], confidence_levels=levels)
        pairs = _exact_ranks(count, levels)
        reason = (
            "the k-th smallest of the values 1 to N is k: the bounds are the ranks "
            "that the binomial coverage in exact rational arithmetic chooses"
        )
        assert_within(
            out.array("lower")[:, 0],
            [float(k) if k else math.nan for k in pairs],
            abs=0.0,
            reason=reason,
        )
        assert_within(
            out.array("upper")[:, 0],
            [float(count + 1 - k) if k else math.nan for k in pairs],
            abs=0.0,
            reason=reason,
        )
        assert_within(
            out.array("median"),
            [(count + 1) / 2],
            abs=0.0,
            reason="the middle rank, or the mean of the two middle ones: a half",
        )


_FEWEST_YEARS: Final = ((0.95, 6), (0.9, 5), (0.68, 3))
"""Levels and the fewest years whose smallest and largest values reach them."""


def _fewest_years(run: Callable[..., Values]) -> None:
    """Assert that a level has bounds from its fewest years on and none before."""
    for level, fewest in _FEWEST_YEARS:
        for count in (fewest - 1, fewest):
            out = run(
                annual_values=[[float(year)] for year in range(count, 0, -1)],
                confidence_levels=[level],
            )
            reached = count == fewest
            reason = "values of the sample, or a gap where the years are too few"
            assert_within(
                out.array("lower"),
                [[1.0 if reached else math.nan]],
                abs=0.0,
                reason=reason,
            )
            assert_within(
                out.array("upper"),
                [[float(count) if reached else math.nan]],
                abs=0.0,
                reason=reason,
            )


def _mirrored_years(x: Values) -> dict[str, object]:
    return {
        "annual_values": -x.array("annual_values"),
        "confidence_levels": x.array("confidence_levels"),
    }


_ORDER_FREE: Final = Tolerance(
    abs=0.0,
    reason="the order statistics and the halves of the middle ones do not depend on "
    "the order of the years or of the levels",
)

DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL: Final = FormulaSpec(
    name="duration_curve_annual_median_interval",
    title="Median annual flow-duration curve and its confidence interval by order "
    "statistics (binomial coverage, the years independent)",
    function="hydrolog.statistics.duration.annual_median_interval",
    family="statistic",
    equation=(
        "Q_p(1) <= ... <= Q_p(N) the N annual values of a percentage p in order; "
        "their median Q_p,0.5 = Q_p((N + 1) / 2) for N odd, (Q_p(N / 2) + "
        "Q_p(N / 2 + 1)) / 2 for N even; per confidence level c the bounds Q_p(k) and "
        "Q_p(N + 1 - k) with the largest k >= 1 such that 1 - 2 F(k - 1) >= c, F(j) "
        "the sum of C(N, i) 2^-N for i = 0 to j; without such k no bounds"
    ),
    latex=(
        r"Q_{p,0.5} = \tfrac{1}{2}\bigl(Q_{p,(\lfloor (N+1)/2 \rfloor)} + "
        r"Q_{p,(\lceil (N+1)/2 \rceil)}\bigr),\quad \bigl[Q_{p,(k)},\ "
        r"Q_{p,(N+1-k)}\bigr],\quad k = \max\Bigl\{k \ge 1 : 1 - 2\sum_{j=0}^{k-1}"
        r"\binom{N}{j}\,2^{-N} \ge c\Bigr\}"
    ),
    variables=(
        Variable(
            name="annual_values",
            symbol="Q_p(i)",
            unit="m3/s",
            kind="real_array",
            description="The values of the annual curves: a row per complete "
            "hydrological year i, in any order, a column per exceedance percentage p "
            "(Q_p(i) of Vogel and Fennessey, each from the days of its year).",
            physical=Range(
                test_low=-1.0e6, test_high=1.0e6, test_reason=_ANY_VALUE_REASON
            ),
            applicability="unstated",
            typical=Range(low=1.24, high=522.0, source=_KLODZKO),
            dims=2,
        ),
        Variable(
            name="confidence_levels",
            symbol="c",
            unit="-",
            kind="real_array",
            description="Confidence levels, distinct: each interval is two-sided and "
            "central, each tail at most (1 - c) / 2.",
            physical=Range(
                low=0.0, high=1.0, low_inclusive=False, high_inclusive=False
            ),
            applicability="unstated",
            typical=Range(low=0.68, high=0.95, source=_ECO_091),
        ),
    ),
    outputs=(
        Output(
            name="median",
            unit="m3/s",
            kind="real_array",
            symbol="Q_{p,0.5}",
            description="The median annual curve: per percentage the median of the N "
            "annual values, in the unit of the series.",
            physical=Range(),
        ),
        Output(
            name="lower",
            unit="m3/s",
            kind="real_array",
            symbol="Q_{p,(k)}",
            description="The lower bound of each median, a row per level in the order "
            "given: the k-th smallest annual value; a gap where N years cannot reach "
            "the level.",
            physical=Range(),
            gaps_allowed=True,
        ),
        Output(
            name="upper",
            unit="m3/s",
            kind="real_array",
            symbol="Q_{p,(N+1-k)}",
            description="The upper bound: the k-th largest annual value; a gap as the "
            "lower.",
            physical=Range(),
            gaps_allowed=True,
        ),
    ),
    sources=(_VF94_ANNUAL, _HELSEL_HIRSCH),
    constraints=(
        Constraint(
            name="distinct_levels",
            cls="precondition",
            check=lambda x: (
                np.unique(x.array("confidence_levels")).size
                == x.array("confidence_levels").size
            ),
            text="the confidence levels are distinct",
            source=_ECO_091,
            satisfied={"confidence_levels": [0.95, 0.68]},
            violated={"confidence_levels": [0.95, 0.95]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"annual_values": 1},
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"annual_values": 1.0},
                outputs={"median": 1.0, "lower": 1.0, "upper": 1.0},
                tolerance=_EXACT_SCALING,
            ),
        ),
        symmetries=(
            Symmetry(
                name="mirror",
                text="the negated values give the negated median and the negated "
                "bounds swapped: the k-th smallest of them is minus the k-th largest",
                inputs=_mirrored_years,
                outputs=lambda out: {
                    "median": -out.array("median"),
                    "lower": -out.array("upper"),
                    "upper": -out.array("lower"),
                },
                tolerance=Tolerance(
                    abs=0.0,
                    reason="negation is exact and rounding to nearest is symmetric "
                    "about zero",
                ),
            ),
            Symmetry(
                name="order_of_the_years",
                text="the years in reverse order give the same median and bounds",
                inputs=lambda x: {
                    "annual_values": x.array("annual_values")[::-1],
                    "confidence_levels": x.array("confidence_levels"),
                },
                outputs=lambda out: {
                    "median": out.array("median"),
                    "lower": out.array("lower"),
                    "upper": out.array("upper"),
                },
                tolerance=_ORDER_FREE,
            ),
            Symmetry(
                name="order_of_the_levels",
                text="the levels in reverse order give the rows of the bounds in "
                "reverse order",
                inputs=lambda x: {
                    "annual_values": x.array("annual_values"),
                    "confidence_levels": x.array("confidence_levels")[::-1],
                },
                outputs=lambda out: {
                    "median": out.array("median"),
                    "lower": out.array("lower")[::-1],
                    "upper": out.array("upper")[::-1],
                },
                tolerance=_ORDER_FREE,
            ),
        ),
        limits=(
            Limit(
                name="exact_binomial",
                text="the bounds of every N from 1 to 60 years and of twelve from 61 "
                "to 200 are the order statistics that the binomial coverage in exact "
                "rational arithmetic chooses, at usual levels, at levels equal to a "
                "coverage and at the float above each",
                check=_binomial_pairs,
            ),
            Limit(
                name="fewest_years",
                text="a level has bounds from the fewest years whose smallest and "
                "largest values reach it on: 6 at c = 0.95, 5 at 0.90, 3 at 0.68",
                check=_fewest_years,
            ),
            Limit(
                name="too_few_years",
                text="five years reach 0.90 and 0.68 with their smallest and largest "
                "values, not 0.95: the rows of that level alone are gaps",
                inputs={
                    "annual_values": [[2.0], [5.0], [1.0], [4.0], [3.0]],
                    "confidence_levels": [0.95, 0.9, 0.68],
                },
                expected={
                    "median": [3.0],
                    "lower": [[math.nan], [1.0], [1.0]],
                    "upper": [[math.nan], [5.0], [5.0]],
                },
                tolerance=Tolerance(
                    abs=0.0, reason="values of the sample, not computed"
                ),
            ),
            Limit(
                name="median_of_an_even_count",
                text="the median of an even count is the mean of the two middle "
                "values, Q_0.5,2 of Vogel and Fennessey's eq. (3)",
                inputs={
                    "annual_values": [
                        [4.0, 40.0],
                        [1.0, 10.0],
                        [3.0, 30.0],
                        [2.0, 20.0],
                    ],
                    "confidence_levels": [0.68],
                },
                expected={
                    "median": [2.5, 25.0],
                    "lower": [[1.0, 10.0]],
                    "upper": [[4.0, 40.0]],
                },
                tolerance=Tolerance(
                    abs=0.0, reason="halves of whole numbers and values of the sample"
                ),
                source=_VF94,
            ),
            Limit(
                name="equal_values",
                text="equal annual values (ties) give that value as the median and as "
                "both bounds",
                inputs={
                    "annual_values": [[7.5]] * 6,
                    "confidence_levels": [0.95, 0.68],
                },
                expected={
                    "median": [7.5],
                    "lower": [[7.5], [7.5]],
                    "upper": [[7.5], [7.5]],
                },
                tolerance=Tolerance(abs=0.0, reason="values of the sample"),
            ),
            Limit(
                name="one_year",
                text="one year gives its values as the median and no bounds at any "
                "level: its only pair, k = 1, covers with probability 0",
                inputs={"annual_values": [[12.0, 3.0]], "confidence_levels": [0.68]},
                expected={
                    "median": [12.0, 3.0],
                    "lower": [[math.nan, math.nan]],
                    "upper": [[math.nan, math.nan]],
                },
                tolerance=Tolerance(abs=0.0, reason="values of the sample"),
            ),
        ),
    ),
    validation="none: an interval of an estimator; its coverage, simulated from "
    "log-normal annual values at 30 and 60 years, is reported under the formula "
    "(CMP-6.11)",
    formula_version=1,
    status="referenced",
    conventions=(
        "two-sided and central at each confidence level c: the order statistics "
        "Q_p(k) and Q_p(N + 1 - k) of the N annual values of a percentage, the k-th "
        "from each end, with the largest k >= 1 whose coverage 1 - 2 F(k - 1) is at "
        "least c, F the binomial distribution function of N trials with probability "
        "1/2 (the years below the true median): each tail at most (1 - c) / 2 "
        "(Helsel and Hirsch 2002, eqs. 3.2-3.3)",
        "order statistics, distribution-free: the coverage is exact for a continuous "
        "distribution of the annual values; not eq. (10) of Vogel and Fennessey "
        "(1994, p. 497), whose bounds, the alpha/2 and 1 - alpha/2 quantiles Q_p,2 "
        "of the n annual values, bracket the value of one year rather than the "
        "median and do not narrow as n grows",
        "the coverage is compared with c exactly, in integers: a level equal to a "
        "coverage takes its pair (c = 0.75 at N = 3: the smallest and the largest "
        "value); Helsel and Hirsch (2002, p. 71) take the tail nearest (1 - c) / 2, "
        "which may leave the coverage below c",
        "a level that even k = 1 cannot reach, 1 - 2^(1 - N) < c (fewer than 6 years "
        "at c = 0.95, 5 at 0.90, 3 at 0.68), has no bounds: its rows of lower and "
        "upper are gaps, and duration_curve gives its interval as not computed with "
        "the notice interval_not_computed (too_few_complete_years)",
        "the median of an odd count is the middle value, of an even count the mean "
        "of the two middle values, taken as the sum of their halves so that values "
        "near the largest float do not overflow: Q_0.5,2 of Vogel and Fennessey's "
        "eq. (3) and numpy.median",
        "ties: equal annual values keep a rank each; with ties the coverage is at "
        "least the binomial one, as P(Q < M) <= 1/2 <= P(Q <= M) at the median M",
        "gaps: none; the annual values are the curves of the complete hydrological "
        "years (Tier B annual_duration_curves), and a gap is refused",
        "the values in any unit: the median and the bounds in that unit (m3/s in the "
        "documents, cm for stages)",
        "every level of one call from one sort of each percentage's values; the rows "
        "of lower and upper follow the levels in the order given",
    ),
    assumptions=(
        "the N annual values of a percentage are independent and identically "
        "distributed: the years are taken as independent, as Vogel and Fennessey "
        "(1994, p. 496) treat the n values Q_p(i) as a random sample; a serial "
        "correlation of the years, as in droughts of several years, would lower the "
        "coverage below c",
        "the interval is that of the median annual curve, the curve of a typical "
        "year (Vogel and Fennessey 1994, p. 496), not of the period-of-record curve "
        "(spec exceedance_values), which has none",
    ),
    traps={
        "singular_at_bound": "range case confidence_levels-physical_high_inside: a "
        "level just below 1 needs 54 years, so the 10 of the typical point leave "
        "its rows gaps and the other level's bounds finite",
        "gap_propagation": "type case annual_values-nan_element: a gap is refused; "
        "limit too_few_years: a level the years cannot reach leaves gaps in its own "
        "rows only",
        "many_small_terms": "limit exact_binomial: the binomial tail, a sum of up to "
        "N / 2 terms C(N, j) 2^-N, is summed in integers and matches the fractions "
        "up to N = 200",
    },
    reference_cases=("tests/fixtures/formulas/duration-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the coverage P(k <= B <= N - k) of B ~ Bin(N, 1/2) in exact "
            "rational arithmetic (fractions) and its pair, the largest k with a "
            "coverage of at least c, for every N from 1 to 60 and twelve from 61 to "
            "200",
            test="tests/unit/test_formulas_duration.py (limit exact_binomial)",
        ),
        Oracle(
            kind="established",
            description="scipy.stats.quantile_test(x, p=0.5).confidence_interval(c), "
            "two-sided (SciPy 1.18), and numpy.median",
            test="tests/unit/test_formulas_duration.py "
            "(test_the_interval_is_scipys_quantile_test)",
            conventions=(
                "both the order statistics of ranks k and N + 1 - k of the binomial "
                "distribution with probability 1/2, each tail at most (1 - c) / 2",
                "where a tail equals (1 - c) / 2 exactly, scipy takes the lower bound "
                "one rank further out (none below the smallest value) and keeps the "
                "upper; the test draws levels that are no coverage",
            ),
        ),
    ),
    base={"confidence_levels": [0.95, 0.68]},
)

SPECS: Final[tuple[FormulaSpec, ...]] = (
    EXCEEDANCE_VALUES,
    DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL,
)
"""The Tier A formulas of the module."""


class AnnualMedianInterval(NamedTuple):
    """The median annual curve and its interval (``annual_median_interval``).

    Attributes
    ----------
    median : NDArray[np.float64]
        Per percentage, the median of the annual values.
    lower, upper : NDArray[np.float64]
        The bounds of the medians, a row per confidence level in the order given and
        a column per percentage; NaN in the rows of a level the years cannot reach.
    """

    median: NDArray[np.float64]
    lower: NDArray[np.float64]
    upper: NDArray[np.float64]


def annual_median_interval(
    annual_values: NDArray[np.float64] | Sequence[Sequence[float]],
    confidence_levels: NDArray[np.float64] | Sequence[float],
) -> AnnualMedianInterval:
    """Return the median annual curve and its interval by order statistics.

    The formula of spec duration_curve_annual_median_interval: per percentage the
    median of the values of the complete years and, per level, the pair of their
    order statistics whose binomial coverage is at least the level.

    Parameters
    ----------
    annual_values : array_like of float
        The values of the annual curves: a row per complete hydrological year, in
        any order, a column per exceedance percentage.
    confidence_levels : array_like of float
        Distinct confidence levels, each between nought and one, both excluded.

    Returns
    -------
    AnnualMedianInterval
        The median of each percentage and, per level, the order statistics that
        bound it; NaN in the rows of a level the years are too few to reach.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input: no year, a value that is not finite, a level
        outside its range or a level given twice.
    """
    x = checked_inputs(
        DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL,
        annual_values=annual_values,
        confidence_levels=confidence_levels,
    )
    ordered = np.sort(x.array("annual_values"), axis=0)  # Q_p(1) <= ... <= Q_p(N)
    count = int(ordered.shape[0])
    middle = count // 2
    if count % 2:
        median = ordered[middle].copy()
    else:  # the halves are exact, so their sum cannot overflow
        median = 0.5 * ordered[middle - 1] + 0.5 * ordered[middle]
    levels = x.array("confidence_levels")
    lower = np.full((levels.size, ordered.shape[1]), np.nan)
    upper = np.full_like(lower, np.nan)
    for row, level in enumerate(levels.tolist()):
        rank = _pair_rank(count, level)
        if rank:
            lower[row] = ordered[rank - 1]
            upper[row] = ordered[count - rank]
    checked = checked_outputs(
        DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL,
        {"median": median, "lower": lower, "upper": upper},
    )
    return AnnualMedianInterval(
        checked.array("median"), checked.array("lower"), checked.array("upper")
    )


@dataclass
class DurationClass(JsonResultMixin):
    """One class of values and its days.

    Attributes
    ----------
    lower, upper : float
        Bounds of the class: a value v belongs to it when lower <= v < upper (the
        highest class also holds its upper bound).
    days : int
        Days with a value in the class.
    share_percent : float
        ``days`` as a percentage of the days counted [%].
    days_with_higher : int
        Days in this class or a higher one („including higher”: the duration of the
        values from ``lower`` up).
    days_with_lower : int
        Days in this class or a lower one („including lower”).
    months : list of int
        ``days`` by hydrological month, November to October.
    """

    lower: float
    upper: float
    days: int
    share_percent: float
    days_with_higher: int
    days_with_lower: int
    months: list[int]


@dataclass
class ModalClass(JsonResultMixin):
    """The most frequent class (the lowest one when several are as frequent).

    Attributes
    ----------
    lower, upper : float
        Bounds of the class.
    days : int
        Its days.
    share_percent : float
        Its share of the days counted [%].
    """

    lower: float
    upper: float
    days: int
    share_percent: float


@dataclass
class DurationCurve(JsonResultMixin):
    """Duration curve of a daily series with the frequencies of its classes.

    Attributes
    ----------
    first_year, last_year : int
        First and last hydrological year of the days used.
    period_years : int
        Hydrological years with a value among the days used.
    month : int or None
        The calendar month whose days were used; ``None`` for every day.
    n_values : int
        Days with a value used.
    min, max, mean, median : float
        Statistics of those values.
    exceedance_percents : list of float
        Exceedance percentages of the table [%].
    values : list of float
        The value equalled or exceeded on each percentage of ``exceedance_percents``.
    curve_exceedance_percents : list of float
        Exceedance percentages of the drawn curve (:data:`CURVE_PERCENTS`) [%].
    curve_values : list of float
        The curve at ``curve_exceedance_percents``.
    bin_method : {"width", "log"}
        Classes of equal width or logarithmic classes.
    bin_width : float or None
        Width of the classes (``"width"``), in the unit of the series.
    bin_count : int or None
        Number of logarithmic classes (``"log"``).
    classes : list of DurationClass
        The classes from the highest down. Logarithmic classes count the positive
        values only.
    modal_class : ModalClass or None
        The most frequent class; ``None`` without classes.
    annual_median_values : list of float or None
        The median annual curve at ``curve_exceedance_percents``: per percentage the
        median of the curves of the complete hydrological years (Vogel and
        Fennessey, 1994; spec ``duration_curve_annual_median_interval``); ``None``
        when no year is complete.
    intervals : list of ConfidenceInterval
        Per confidence level asked, in the order asked, the interval of each value
        of ``annual_median_values`` (``ci_method`` ``"order_statistics"``); not
        computed (method and bounds ``None``) at a level the complete years are too
        few for, with the warning ``IntervalNotComputed``.
    """

    first_year: int
    last_year: int
    period_years: int
    month: int | None
    n_values: int
    min: float
    max: float
    mean: float
    median: float
    exceedance_percents: list[float]
    values: list[float]
    curve_exceedance_percents: list[float]
    curve_values: list[float]
    bin_method: str
    bin_width: float | None
    bin_count: int | None
    classes: list[DurationClass] = field(default_factory=list)
    modal_class: ModalClass | None = None
    annual_median_values: list[float | None] = field(default_factory=list)
    intervals: list[ConfidenceInterval] = field(default_factory=list)


def _class_edges(
    values: NDArray[np.float64],
    method: BinMethod,
    width: float,
    count: int,
) -> NDArray[np.float64]:
    """Edges of the classes, ascending; empty when the values allow no class.

    Classes of a width are counted in decimal arithmetic on the shortest decimal form
    of the values and of the width (``repr``), so a value written on a class bound is
    in the class it starts: 0.3 with the width 0.1 is in [0.3, 0.4), not in
    [0.2, 0.3) as 0.3 / 0.1 = 2.9999999999999996 in binary floating point would put
    it. The edges are the floats nearest to the decimal bounds, which rounding keeps
    in order with the values.
    """
    if method == "width":
        step = Decimal(repr(width))
        first = _class_number(float(values.min()), step)
        last = _class_number(float(values.max()), step)
        return np.array(
            [float(step * k) for k in range(first, last + 2)], dtype=np.float64
        )
    positive = values[values > 0]
    if positive.size < 2 or positive.min() == positive.max():
        return np.empty(0, dtype=np.float64)
    edges: NDArray[np.float64] = np.logspace(
        math.log10(float(positive.min())), math.log10(float(positive.max())), count + 1
    )
    # The end edges are the extreme values themselves, not their rounded logarithms.
    edges[0], edges[-1] = float(positive.min()), float(positive.max())
    return edges


def _class_number(value: float, step: Decimal) -> int:
    """Return the k of the class [k step, (k + 1) step) of ``value``, in decimals."""
    whole, rest = divmod(Decimal(repr(value)), step)  # whole rounds toward zero
    return int(whole) - 1 if rest and value < 0 else int(whole)


def _classes(
    values: NDArray[np.float64],
    months: NDArray[np.int_],
    edges: NDArray[np.float64],
) -> tuple[list[DurationClass], ModalClass | None]:
    """Count the days of each class, highest first, and find the modal class."""
    if edges.size < 2:
        return [], None
    inside = (values >= edges[0]) & (values <= edges[-1])
    counted = values[inside]
    month_index = (months[inside] - 11) % 12  # 0 = November ... 11 = October
    total = int(counted.size)
    index = np.clip(
        np.searchsorted(edges, counted, side="right") - 1, 0, edges.size - 2
    )
    table = np.zeros((edges.size - 1, 12), dtype=np.int64)
    np.add.at(table, (index, month_index), 1)
    days = table.sum(axis=1)
    classes: list[DurationClass] = []
    higher = 0
    for at in range(edges.size - 2, -1, -1):
        count = int(days[at])
        lower_days = total - higher
        higher += count
        classes.append(
            DurationClass(
                lower=float(edges[at]),
                upper=float(edges[at + 1]),
                days=count,
                share_percent=count / total * 100.0 if total else 0.0,
                days_with_higher=higher,
                days_with_lower=lower_days,
                months=[int(item) for item in table[at]],
            )
        )
    modal = int(np.argmax(days))
    return classes, ModalClass(
        lower=float(edges[modal]),
        upper=float(edges[modal + 1]),
        days=int(days[modal]),
        share_percent=float(days[modal]) / total * 100.0 if total else 0.0,
    )


def _annual_curves(
    values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    usable: NDArray[np.bool_],
    month: int | None,
) -> NDArray[np.float64]:
    """Return the curve of each complete hydrological year at CURVE_PERCENTS, by rows.

    A year is complete when each of its days, or with ``month`` each day of that
    calendar month in it, is ``usable`` (has a finite value). The dates increase
    strictly, so the days of a year are one run of the series and none counts twice.
    """
    labels, starts = np.unique(hydrological_year(dates), return_index=True)
    present = np.add.reduceat(usable.astype(np.int64), starts)
    if month is None:
        needed = days_in_hydrological_year(labels)
    else:  # November and December lie in the calendar year before the year's name
        calendar = labels - 1 if month >= FIRST_MONTH else labels
        months = ((calendar - 1970) * 12 + month - 1).astype("timedelta64[M]")
        first = np.datetime64("1970-01", "M") + months
        after = first + np.timedelta64(1, "M")
        days = after.astype("datetime64[D]") - first.astype("datetime64[D]")
        needed = days.astype(np.int64)
    ends = np.append(starts[1:], dates.size)
    curves = [
        exceedance_values(values[start:end][usable[start:end]], CURVE_PERCENTS)
        for start, end, complete in zip(starts, ends, present == needed, strict=True)
        if complete
    ]
    return np.array(curves, dtype=np.float64).reshape(len(curves), len(CURVE_PERCENTS))


def _median_annual_curve(
    annual: NDArray[np.float64], levels: tuple[float, ...]
) -> tuple[list[float | None], list[ConfidenceInterval]]:
    """Return the median annual curve and its interval at each level, in order.

    A level the complete years cannot reach has its interval not computed, with the
    warning ``IntervalNotComputed`` (``too_few_complete_years``) for all such levels.
    """
    years = int(annual.shape[0])
    needed = [_years_needed(level) for level in levels]
    short = [row for row, fewest in enumerate(needed) if fewest > years]
    if short:
        warnings.warn(
            IntervalNotComputed(
                reason="too_few_complete_years",
                confidence_levels=[levels[row] for row in short],
                distribution=None,
                fit_method=None,
                return_periods=None,
                complete_years=years,
                required_years=[needed[row] for row in short],
            ),
            stacklevel=3,
        )
    if not years:
        nothing: list[float | None] = [None] * len(CURVE_PERCENTS)
        return nothing, intervals_not_computed(levels)
    found = annual_median_interval(annual, list(levels))
    intervals: list[ConfidenceInterval] = []
    for row, level in enumerate(levels):
        intervals += (
            intervals_not_computed([level])
            if row in short
            else interval_entries(
                [level],
                "order_statistics",
                found.lower[row : row + 1],
                found.upper[row : row + 1],
            )
        )
    return [float(value) for value in found.median], intervals


def duration_curve(
    values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    *,
    month: int | None = None,
    exceedance_percents: Sequence[float] = DEFAULT_PERCENTS,
    bin_method: BinMethod = "width",
    bin_width: float = 10.0,
    bin_count: int = 40,
    confidence_level: float | Sequence[float] = 0.95,
) -> DurationCurve:
    """Compute the duration curve and the class frequencies of a daily series.

    Parameters
    ----------
    values : NDArray[np.float64]
        Daily values; ``NaN`` values are left out.
    dates : NDArray[np.datetime64]
        Their dates, strictly increasing (days may be absent).
    month : int, optional
        Use only the days of this calendar month (1-12).
    exceedance_percents : sequence of float, optional
        Exceedance percentages of the table [%], each in (0, 100), by default
        :data:`DEFAULT_PERCENTS`.
    bin_method : {"width", "log"}, optional
        Classes of equal width ``bin_width`` starting at the multiple of the width
        at or below the smallest value (default), or ``bin_count`` logarithmic
        classes between the smallest positive and the largest value.
    bin_width : float, optional
        Width of the classes, positive, in the unit of the series, by default 10.
    bin_count : int, optional
        Number of logarithmic classes, at least 2, by default 40.
    confidence_level : float or sequence of float, optional
        The confidence level of the interval of the median annual curve, or a list
        of distinct levels, each in (0, 1), by default 0.95.

    Returns
    -------
    DurationCurve
        The curve, its table, the classes, and the median annual curve of the
        complete hydrological years with its intervals.

    Raises
    ------
    InvalidParameterError
        If the arrays differ in length, the dates do not increase strictly, an option
        is out of its range, or no day (of ``month``) has a value.

    Warns
    -----
    IntervalNotComputed
        ``too_few_complete_years``: fewer complete years than the interval needs at
        a level (6 at 0.95, 3 at 0.68), whose interval is not computed.
    """
    values = np.asarray(values, dtype=np.float64)
    dates = np.asarray(dates).astype("datetime64[D]")
    if values.size != dates.size:
        raise InvalidParameterError("values and dates must have the same length")
    if np.any(dates[1:] <= dates[:-1]):
        raise InvalidParameterError("the dates must increase strictly")
    table_percents = np.asarray(exceedance_percents, dtype=np.float64)
    if (
        table_percents.ndim != 1
        or table_percents.size == 0
        or not np.all((table_percents > 0) & (table_percents < 100))
    ):
        raise InvalidParameterError(
            "exceedance_percents must lie in the open interval (0, 100)"
        )
    if bin_method not in ("width", "log"):
        raise InvalidParameterError(f"unknown bin_method {bin_method!r}")
    if not (math.isfinite(bin_width) and bin_width > 0) or bin_count < 2:
        raise InvalidParameterError(
            "bin_width must be positive and bin_count at least 2"
        )
    levels = asked_levels(confidence_level)
    calendar_months = dates.astype("datetime64[M]").astype(np.int64) % 12 + 1
    keep = np.isfinite(values)
    if month is not None:
        if not 1 <= month <= 12:
            raise InvalidParameterError(f"month must be 1 to 12, got {month}")
        keep &= calendar_months == month
    if not keep.any():
        raise InvalidParameterError("no day has a value")
    used = values[keep]
    years = hydrological_year(dates[keep])
    curve = exceedance_values(used, CURVE_PERCENTS)
    table = exceedance_values(used, table_percents)
    edges = _class_edges(used, bin_method, bin_width, bin_count)
    classes, modal = _classes(used, calendar_months[keep], edges)
    annual_median, intervals = _median_annual_curve(
        _annual_curves(values, dates, keep, month), levels
    )
    return DurationCurve(
        first_year=int(years.min()),
        last_year=int(years.max()),
        period_years=int(np.unique(years).size),
        month=month,
        n_values=int(used.size),
        min=float(used.min()),
        max=float(used.max()),
        mean=float(used.mean()),
        median=float(np.median(used)),
        exceedance_percents=[float(item) for item in table_percents],
        values=[float(item) for item in table],
        curve_exceedance_percents=list(CURVE_PERCENTS),
        curve_values=[float(item) for item in curve],
        bin_method=bin_method,
        bin_width=float(bin_width) if bin_method == "width" else None,
        bin_count=int(bin_count) if bin_method == "log" else None,
        classes=classes,
        modal_class=modal,
        annual_median_values=annual_median,
        intervals=intervals,
    )


TIER_B: Final = (
    TierBSpec(
        name="duration_curve_days",
        function="hydrolog.statistics.duration.duration_curve",
        definition="the days the curve and the classes take: every day with a value, "
        "or only those of one calendar month (month); their count n_values, minimum, "
        "maximum, mean and median, the curve at CURVE_PERCENTS and the table at "
        "exceedance_percents (spec exceedance_values), and the hydrological years "
        "(1 November - 31 October, named after the year of their end) of those days: "
        "first_year, last_year and period_years",
        convention="the total-period curve of all the days of the record (Searcy "
        "1959, p. 3; WMO-No. 1029, sect. 6.1); a day whose value is NaN or not finite "
        "has no value and is left out, not filled; a month's curve takes that calendar "
        "month of every year; the dates increase strictly, one value a day",
        source=_SEARCY,
    ),
    TierBSpec(
        name="duration_classes",
        function="hydrolog.statistics.duration.duration_curve",
        definition="classes of equal width w, [k w, (k + 1) w) from the multiple of w "
        "at or below the smallest value to the class of the largest, or bin_count "
        "classes of equal steps of log10 between the smallest positive and the "
        "largest value, whose end edges are those values and which count the positive "
        "values only; a value v is in the class with lower <= v < upper, the highest "
        "class also holding its upper edge; per class from the highest down: its days, "
        "their share of the days counted [%], the days of the class and every higher "
        "one (including higher) and of the class and every lower one (including "
        "lower), and its days by hydrological month, November to October; the modal "
        "class has the most days, the lowest one of equal counts",
        convention="the days counted from the highest class down, a class holding the "
        "days equal to or greater than its lower limit and less than the next (Searcy "
        "1959, figs. 4-5); the edges of equal widths are computed in decimal "
        "arithmetic on the shortest decimal forms of the values and the width, so a "
        "value written on a class bound starts its class (0.3 with the width 0.1 is in "
        "[0.3, 0.4); ADR-0048); the edges are the floats nearest those bounds",
        source=_SEARCY,
    ),
    TierBSpec(
        name="annual_duration_curves",
        function="hydrolog.statistics.duration.duration_curve",
        definition="the curve of each complete hydrological year at CURVE_PERCENTS "
        "(spec exceedance_values) from the days of that year, or with month from the "
        "days of that calendar month in it; a year is complete when each of its days "
        "(365 or 366, or those of the month) has a value; per percentage the median "
        "of the curves of the complete years, annual_median_values, and its intervals "
        "at each confidence level asked (spec duration_curve_annual_median_interval)",
        convention="the annual flow-duration curves of Vogel and Fennessey (1994, p. "
        "494), one per year from its own daily values, here per hydrological year (1 "
        "November - 31 October); a year with a day without a value (its date absent, "
        "its value NaN or not finite) is left out, not filled, as for the annual "
        "extremes (complete_year_extremes); a leap year counts its 366 days, where "
        "Vogel and Fennessey count 365 a year; with month the days of that month in "
        "the hydrological year, those of November and December in the calendar year "
        "before its name; without a complete year annual_median_values is null and "
        "every interval not computed",
        source=_VF94_ANNUAL,
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""
