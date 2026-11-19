"""Harmonic analysis of the annual cycle of a daily series.

The annual cycle is fitted by least squares as a mean and K harmonics of the year,

    x(t) = A₀ + Σₖ [aₖ cos(2πkt / P) + bₖ sin(2πkt / P)],  k = 1 … K,

with t the day of the hydrological year counted from 0 (1 November) and P = 365.25
days, the mean year of 1901–2099 (:func:`harmonic_fit`, spec :data:`HARMONIC_FIT`).
Each harmonic has the amplitude Cₖ = √(aₖ² + bₖ²) and the phase φₖ = atan2(bₖ, aₖ),
which puts its first maximum on the day φₖ P / (2πk) + 1 of the hydrological year;
its share of the variance is what it adds to the R² of the fit of the harmonics
before it. The days with a value must cover the year: a gap of P / (2K) days or more
between them leaves the harmonics unresolved (Feichtinger, Gröchenig and Strohmer,
1995). The fit of a whole period is the mean annual cycle of its years; a year is
fitted on its own when it has at least 300 days with a value that allow a fit
(:func:`annual_cycle`, :data:`TIER_B`). The method serves any daily variable: water
or air temperature, discharge, stage. ``docs/FORMULAS.md`` shows the spec (ADR-0063).

Examples
--------
A cycle of mean 10 with an annual harmonic of amplitude 5 peaking on day 101 and a
half-year one of amplitude 2 peaking on day 31, a value a day for a year:

>>> import numpy as np
>>> day = np.arange(1, 366)
>>> t = day - 1.0
>>> annual = 5 * np.cos(2 * np.pi * (t - 100) / 365.25)
>>> x = 10 + annual + 2 * np.cos(4 * np.pi * (t - 30) / 365.25)
>>> fit = harmonic_fit(day, x)
>>> round(fit.mean, 6), [round(h.amplitude, 6) for h in fit.harmonics]
(10.0, [5.0, 2.0])
>>> [round(h.phase_day, 6) for h in fit.harmonics], round(fit.r_squared, 9)
([101.0, 31.0], 1.0)

References
----------
Wilks, D. S. (2011): Statistical Methods in the Atmospheric Sciences, 3rd ed.
    Academic Press, section 9.4 (harmonic analysis).
Feichtinger, H. G., Gröchenig, K. & Strohmer, T. (1995): Efficient numerical methods
    in non-uniform sampling theory. Numerische Mathematik 69, 423–440.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Conservation,
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
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._hydrological_year import (
    hydrological_day_of_year,
    hydrological_year,
)

__all__ = [
    "HARMONIC_FIT",
    "MAX_HARMONICS",
    "MIN_YEAR_VALUES",
    "PERIOD_DAYS",
    "SPECS",
    "TIER_B",
    "AnnualCycle",
    "Harmonic",
    "HarmonicFit",
    "HarmonicYear",
    "annual_cycle",
    "harmonic_fit",
]

_ADR_0031 = (
    "Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and "
    "baseflow (docs/decisions/), restated in ADR-0063"
)
_PERIOD = Constant(
    name="period_days",
    value=Fraction(1461, 4),
    unit="day",
    symbol="P",
    source=Source(
        citation=_ADR_0031,
        locator="point 3: the period P = 365.25 d, the mean year of 1901-2099, in "
        "which every fourth year is a leap year (the Julian year)",
    ),
)
_MIN_YEAR_VALUES = Constant(
    name="min_year_values",
    value=Fraction(300),
    unit="day",
    source=Source(
        citation=_ADR_0031,
        locator="point 3: each hydrological year with at least 300 values has a fit "
        "of its own",
    ),
)

PERIOD_DAYS: Final = float(_PERIOD.value)
"""Period of the first harmonic [days]: the mean year of 1901–2099, 365.25 days."""
MAX_HARMONICS: Final = 4
"""Largest number of harmonics fitted."""
MIN_YEAR_VALUES: Final = int(_MIN_YEAR_VALUES.value)
"""Days with a value that a hydrological year needs for a fit of its own."""


@dataclass
class Harmonic(JsonResultMixin):
    """One harmonic of a fitted annual cycle.

    Attributes
    ----------
    amplitude : float
        Cₖ = √(aₖ² + bₖ²), in the unit of the series.
    phase_day : float
        Day of the hydrological year of its first maximum (1 = 1 November); a
        harmonic of no amplitude has no phase, and this day is then noise.
    explained_variance : float or None
        What the harmonic adds to the R² of the fit of the harmonics before it, 0 to
        1 (a number since the spec refuses a constant series; ``None`` stays in the
        type for the results of Hydrolog 0.8).
    """

    amplitude: float
    phase_day: float
    explained_variance: float | None


@dataclass
class HarmonicFit(JsonResultMixin):
    """A fit of the annual cycle: the mean and the harmonics (spec ``harmonic_fit``).

    Attributes
    ----------
    mean : float
        A₀, the mean of the fitted cycle, in the unit of the series.
    harmonics : list of Harmonic
        Harmonics 1 to K.
    r_squared : float or None
        Share of the variance explained by the whole fit, 0 to 1 (a number since the
        spec refuses a constant series).
    n_values : int
        Days with a value in the fit.
    """

    mean: float
    harmonics: list[Harmonic]
    r_squared: float | None
    n_values: int

    @property
    def amplitudes(self) -> list[float]:
        """The amplitude of each harmonic."""
        return [harmonic.amplitude for harmonic in self.harmonics]

    @property
    def phase_days(self) -> list[float]:
        """The day of the first maximum of each harmonic."""
        return [harmonic.phase_day for harmonic in self.harmonics]

    @property
    def explained_variances(self) -> list[float | None]:
        """The share of the variance of each harmonic."""
        return [harmonic.explained_variance for harmonic in self.harmonics]


@dataclass
class HarmonicYear(JsonResultMixin):
    """The fit of one hydrological year (fields of :class:`HarmonicFit`).

    Attributes
    ----------
    year : int
        Hydrological year (1 November - 31 October, named after its end).
    mean, harmonics, r_squared, n_values
        As in :class:`HarmonicFit`, from the days of this year.
    """

    year: int
    mean: float
    harmonics: list[Harmonic]
    r_squared: float | None
    n_values: int


@dataclass
class AnnualCycle(JsonResultMixin):
    """The harmonic fits of the annual cycle of a period and of its years.

    Attributes
    ----------
    n_harmonics : int
        Harmonics fitted, 1 to 4.
    period_days : float
        Period of the first harmonic [days], 365.25.
    first_year, last_year : int
        First and last hydrological year with a value.
    period_years : int
        Hydrological years with a value.
    period : HarmonicFit
        The fit of every day of the period: the mean annual cycle.
    years : list of HarmonicYear
        The fit of each year with at least :data:`MIN_YEAR_VALUES` days with a value
        that meet the preconditions of the fit.
    """

    n_harmonics: int
    period_days: float
    first_year: int
    last_year: int
    period_years: int
    period: HarmonicFit
    years: list[HarmonicYear] = field(default_factory=list)


# --- the spec of the harmonic fit (Nogat CMP-2.1; ADR-0063) ---------------------------

_WILKS = Source(
    citation="Wilks, D.S. (2011). Statistical Methods in the Atmospheric Sciences, "
    "3rd ed. Academic Press, Oxford",
    locator="section 9.4: the harmonic functions of a periodic series, their "
    "amplitude, phase and share of the variance, fitted by regression; not opened",
    access="author-provided",
)
_FGS = Source(
    citation="Feichtinger, H.G., Gröchenig, K. and Strohmer, T. (1995). Efficient "
    "numerical methods in non-uniform sampling theory. Numerische Mathematik 69, "
    "423-440",
    locator="section 4, Propositions 1 and 2, pp. 429-430: a trigonometric polynomial "
    "of degree M on a period of 1 sampled with a largest gap delta < 1/(2M) (on the "
    "circle) is a stable sampling set, its condition number at most ((1 + 2 delta M) / "
    "(1 - 2 delta M))^2; for larger gaps no estimate is known (after Gröchenig 1992, "
    "Math. Comp. 59, 181-194)",
    url="http://www.math.ucdavis.edu/~strohmer/papers/1995/fgs0195.ps.gz",
)
_DRAPER_SMITH = Source(
    citation="Draper, N.R. and Smith, H. (1998). Applied Regression Analysis, 3rd ed. "
    "Wiley, New York",
    locator="section 6.1: the extra sum of squares of terms added to a fitted model, "
    "which never increases the residual sum of squares; not opened",
    access="author-provided",
)
_WARSZAWA_TEMPERATURE = Source(
    citation="IMGW-PIB, synoptic station Warszawa-Okęcie (352200375), daily data "
    "1991-2020 (tests/fixtures/warszawa_okecie_1991_2020.csv.gz)",
    locator="the daily mean air temperature, -22.2 to 29.3 degC",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/",
)
_HYDROLOGICAL_YEAR = Source(
    citation="IMGW-PIB, hydrologia_info_ogolne.txt of the public hydrological data",
    locator="the hydrological year from 1 November to 31 October: days 1 to 365, or "
    "366 when it ends in a leap year",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/"
    "dane_hydrologiczne/",
)
_HUGE_VALUE_REASON = (
    "a million in the series' unit: a thousand times the largest water and air "
    "temperatures and Polish discharges, and above any river stage in cm"
)


def _design(t: NDArray[np.float64], harmonics: int) -> NDArray[np.float64]:
    """Return the columns 1, cos and sin of each harmonic at the times ``t``."""
    columns = [np.ones_like(t)]
    for k in range(1, harmonics + 1):
        omega = 2.0 * np.pi * k * t / PERIOD_DAYS
        columns += [np.cos(omega), np.sin(omega)]
    return np.column_stack(columns)


def _known(x: Values) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return the times t = day - 1 and the values of the days with a value."""
    values = x.array("values")
    keep = ~np.isnan(values)
    return x.array("day_of_year")[keep] - 1.0, values[keep]


def _sum_of_squares(y: NDArray[np.float64]) -> float:
    """Return the sum of squared deviations from the mean, from the deviations."""
    if y.size == 0:
        return 0.0
    with np.errstate(over="ignore"):
        return float(np.sum((y - y.mean()) ** 2))


def _largest_gap(t: NDArray[np.float64]) -> float:
    """Return the longest gap between the days with a value on the circle of P."""
    days = np.unique(t)
    if days.size == 0:
        return math.inf
    wrap = PERIOD_DAYS - float(days[-1]) + float(days[0])
    return max(float(np.max(np.diff(days), initial=0.0)), wrap)


def _fit(x: Values) -> dict[str, object]:
    """Return the outputs of the spec: the full fit and the nested ones for R²."""
    t, y = _known(x)
    count = x.integer("n_harmonics")
    design = _design(t, count)
    coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
    total = _sum_of_squares(y)
    amplitudes: list[float] = []
    phases: list[float] = []
    shares: list[float] = []
    explained = 0.0
    for k in range(1, count + 1):
        a, b = float(coefficients[2 * k - 1]), float(coefficients[2 * k])
        amplitudes.append(math.hypot(a, b))
        phase = math.atan2(b, a) % (2.0 * math.pi)
        phases.append(phase * PERIOD_DAYS / (2.0 * math.pi * k) + 1.0)
        nested = design[:, : 2 * k + 1]
        part = coefficients if k == count else np.linalg.lstsq(nested, y, rcond=None)[0]
        cumulative = 1.0 - float(np.sum((y - nested @ part) ** 2)) / total
        shares.append(cumulative - explained)
        explained = cumulative
    return {
        "mean": float(coefficients[0]),
        "amplitudes": amplitudes,
        "phase_days": phases,
        "explained_variances": shares,
        "r_squared": explained,
    }


def _signal_days(years: int) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return the day of the hydrological year of each day of ``years`` years."""
    dates = np.arange(
        np.datetime64("2014-11-01"), np.datetime64(f"{2014 + years}-11-01")
    )
    day = hydrological_day_of_year(dates).astype(np.float64)
    return day, day - 1.0


def _two_harmonics(run: Callable[..., Values]) -> None:
    day, t = _signal_days(5)
    values = (
        10.0
        + 5.0 * np.cos(2.0 * np.pi * (t - 100.0) / PERIOD_DAYS)
        + 2.0 * np.cos(4.0 * np.pi * (t - 30.0) / PERIOD_DAYS)
    )
    out = run(day_of_year=day, values=values, n_harmonics=2)
    assert_within(
        [out.real("mean"), *out.array("amplitudes"), *out.array("phase_days")],
        [10.0, 5.0, 2.0, 101.0, 31.0],
        abs=1e-8,
        reason="least squares on an exact signal of five hydrological years: the "
        "rounding of 1,826 values and of the solver",
    )
    assert_within(
        out.real("r_squared"),
        1.0,
        abs=1e-14,
        reason="an exact signal leaves only rounded residuals",
    )


def _normal_equations(
    t: NDArray[np.float64], y: NDArray[np.float64], count: int
) -> list[Fraction]:
    """Solve the normal equations of the float design, summed by math.fsum, exactly."""
    design = _design(t, count)
    size = design.shape[1]
    matrix = [
        [
            Fraction(math.fsum((design[:, i] * design[:, j]).tolist()))
            for j in range(size)
        ]
        + [Fraction(math.fsum((design[:, i] * y).tolist()))]
        for i in range(size)
    ]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(matrix[row][column]))
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        for row in range(size):
            if row != column and matrix[row][column] != 0:
                factor = matrix[row][column] / matrix[column][column]
                matrix[row] = [
                    a - factor * b
                    for a, b in zip(matrix[row], matrix[column], strict=True)
                ]
    return [matrix[i][size] / matrix[i][i] for i in range(size)]


def _normal_equations_fit(run: Callable[..., Values]) -> None:
    rng = np.random.default_rng(20261119)
    day = np.arange(1.0, 366.0)
    t = day - 1.0
    noisy = 8.0 + 9.0 * np.cos(2.0 * np.pi * (t - 200.0) / PERIOD_DAYS)
    noisy += rng.normal(0.0, 1.5, day.size)
    noisy[rng.random(day.size) < 0.15] = np.nan  # gaps of a few days
    for count in (1, 2, 3):
        out = run(day_of_year=day, values=noisy, n_harmonics=count)
        keep = ~np.isnan(noisy)
        exact = _normal_equations(t[keep], noisy[keep], count)
        amplitudes = [
            math.hypot(float(exact[2 * k - 1]), float(exact[2 * k]))
            for k in range(1, count + 1)
        ]
        assert_within(
            [out.real("mean"), *out.array("amplitudes")],
            [float(exact[0]), *amplitudes],
            abs=1e-11,
            reason="the singular value decomposition of LAPACK against the normal "
            "equations solved in fractions: the design's condition number near one "
            "keeps both within a few hundred ulps",
        )


HARMONIC_FIT: Final[FormulaSpec] = FormulaSpec(
    name="harmonic_fit",
    title="Least squares fit of the mean and the harmonics of the annual cycle",
    function="hydrolog.statistics.harmonics.harmonic_fit",
    family="statistic",
    equation="x(t) = A0 + sum_k (a_k cos(2 pi k t / P) + b_k sin(2 pi k t / P)), k = 1 "
    "... K, by least squares with t = day - 1; C_k = sqrt(a_k^2 + b_k^2); phase day = "
    "(atan2(b_k, a_k) mod 2 pi) P / (2 pi k) + 1; share_k = R2(1..k) - R2(1..k-1) of "
    "the nested fits",
    latex=r"x(t) = A_0 + \sum_{k=1}^{K}\left(a_k \cos\frac{2\pi k t}{P} + b_k "
    r"\sin\frac{2\pi k t}{P}\right),\quad C_k = \sqrt{a_k^2 + b_k^2},\quad "
    r"d_k = \frac{(\operatorname{atan2}(b_k, a_k) \bmod 2\pi)\,P}{2\pi k} + 1",
    variables=(
        Variable(
            name="day_of_year",
            symbol="d",
            unit="day",
            kind="real_array",
            description="Day of the hydrological year of each value, 1 = 1 November.",
            physical=Range(low=1.0, high=366.0),
            applicability="unstated",
            typical=Range(low=1.0, high=366.0, source=_HYDROLOGICAL_YEAR),
        ),
        Variable(
            name="values",
            symbol="x",
            unit="degC",
            kind="real_array",
            description="The daily values in any unit, water or air temperature most "
            "often; NaN marks a day without a value.",
            physical=Range(
                test_low=-1.0e6, test_high=1.0e6, test_reason=_HUGE_VALUE_REASON
            ),
            applicability="unstated",
            typical=Range(low=-22.2, high=29.3, source=_WARSZAWA_TEMPERATURE),
            gaps_allowed=True,
        ),
        Variable(
            name="n_harmonics",
            symbol="K",
            unit="-",
            kind="integer",
            description="Number of harmonics fitted.",
            physical=Range(low=1, high=MAX_HARMONICS),
            applicability="unstated",
            typical=Range(
                low=1,
                high=MAX_HARMONICS,
                source=Source(
                    citation=_ADR_0031,
                    locator="point 3: harmonics 1 to 4 (default 2: the annual and the "
                    "half-year one), as the option of stats harmonics",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="mean",
            unit="degC",
            symbol="A_0",
            description="The mean of the fitted cycle, in the unit of the values.",
            physical=Range(),
        ),
        Output(
            name="amplitudes",
            unit="degC",
            kind="real_array",
            symbol="C_k",
            description="The amplitude of each harmonic, in the unit of the values.",
            physical=Range(low=0.0),
        ),
        Output(
            name="phase_days",
            unit="day",
            kind="real_array",
            symbol="d_k",
            description="The day of the hydrological year of the first maximum of each "
            "harmonic.",
            physical=Range(low=1.0, high=1.0 + PERIOD_DAYS),
        ),
        Output(
            name="explained_variances",
            unit="-",
            kind="real_array",
            description="The share of the variance each harmonic adds to the fit of "
            "the harmonics before it.",
            physical=Range(low=0.0, high=1.0),
            boundary_tolerance=1e-12,
        ),
        Output(
            name="r_squared",
            unit="-",
            symbol="R^2",
            description="The share of the variance explained by the whole fit.",
            physical=Range(low=0.0, high=1.0),
            boundary_tolerance=1e-12,
        ),
    ),
    sources=(_WILKS, _FGS, _DRAPER_SMITH),
    constants=(_PERIOD,),
    constraints=(
        Constraint(
            name="same_length",
            cls="physical",
            check=lambda x: x.array("day_of_year").shape == x.array("values").shape,
            text="one day per value",
            source=_WILKS,
            satisfied={"day_of_year": list(range(1, 366))},
            violated={"day_of_year": list(range(1, 365))},
        ),
        Constraint(
            name="enough_values",
            cls="precondition",
            check=lambda x: (
                np.count_nonzero(~np.isnan(x.array("values")))
                >= 4 * x.integer("n_harmonics") + 2
            ),
            text="at least 4 K + 2 values: twice the 2 K + 1 coefficients (Hydrolog's "
            "rule)",
            source=Source(citation=_ADR_0031, locator="point 3: too_few_values"),
            satisfied={"day_of_year": list(range(1, 366))},
            boundary={
                "day_of_year": [1, 37, 73, 109, 145, 181, 217, 253, 289, 325],
                "values": [9.0, 11.0, 14.0, 15.0, 13.0, 10.0, 7.0, 5.0, 6.0, 8.0],
            },
            violated={
                "day_of_year": [1, 41, 81, 121, 161, 201, 241, 281, 321],
                "values": [9.0, 11.0, 14.0, 15.0, 13.0, 10.0, 7.0, 5.0, 6.0],
            },
        ),
        Constraint(
            name="year_covered",
            cls="precondition",
            check=lambda x: (
                _largest_gap(_known(x)[0])
                < PERIOD_DAYS / (2 * x.integer("n_harmonics"))
            ),
            text="the longest gap between days with a value, on the circle of the "
            "year, is shorter than P / (2 K): the harmonics are resolved",
            source=_FGS,
            satisfied={"day_of_year": list(range(1, 366))},
            boundary={
                "day_of_year": [*range(1, 271), 361.3125],
                "values": [10.0] * 270 + [11.0],
            },
            boundary_holds=False,
            violated={
                "day_of_year": list(range(1, 201)),
                "values": [10.0 + day % 7 for day in range(1, 201)],
            },
        ),
        Constraint(
            name="values_not_all_equal",
            cls="precondition",
            check=lambda x: 0.0 < _sum_of_squares(_known(x)[1]) < math.inf,
            text="0 < sum((x - mean)^2) < inf: the values are not all equal and "
            "float64 holds their variance, so R2 and the phases exist",
            source=_WILKS,
            satisfied={"day_of_year": list(range(1, 366))},
            violated={"values": [7.0] * 365},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="values_in_another_unit",
                inputs={"values": 1.0},
                outputs={"mean": 1.0, "amplitudes": 1.0},
                tolerance=Tolerance(
                    abs=1e-300,
                    rel=1e-12,
                    reason="the fit is linear in the values; doubling them is exact "
                    "but where LAPACK rescales a small or large right-hand side",
                ),
            ),
        ),
        conservation=(
            Conservation(
                name="shares_add_up_to_r_squared",
                text="the shares of the harmonics add up to R2 of the whole fit",
                residual=lambda x, out: (
                    math.fsum(out.array("explained_variances")) - out.real("r_squared")
                ),
                tolerance=Tolerance(
                    abs=1e-14,
                    reason="differences of up to four nested R2 summed again: a few "
                    "roundings",
                ),
            ),
        ),
        limits=(
            Limit(
                name="two_harmonics",
                text="an exact signal of two harmonics is recovered: mean 10, "
                "amplitudes 5 and 2, days 101 and 31, R2 = 1",
                check=_two_harmonics,
            ),
            Limit(
                name="normal_equations",
                text="the mean and the amplitudes equal those of the normal equations "
                "of the same design solved in exact fractions",
                check=_normal_equations_fit,
            ),
        ),
    ),
    validation="none: a description of the mean annual cycle; Wilks (2011) gives no "
    "measure of its agreement with observations",
    formula_version=1,
    status="oracle only",
    conventions=(
        "t is the day of the hydrological year minus one (1 November = 0), P = 365.25 "
        "days: a leap year's 31 October is t = 365, so t jumps by 1.25 days at the "
        "turn of the year",
        "the phase day is the day of the hydrological year whose value the harmonic "
        "peaks at: a day's value sits at t = day - 1 and the phase day is t + 1",
        "a harmonic's share of the variance is the increase of R2 when it joins the "
        "least squares fit of the harmonics before it (nested fits, the extra sum of "
        "squares of Draper and Smith); for a whole number of years of equally spaced "
        "days the harmonics are orthogonal and the share is Wilks's (n/2) C_k^2 / "
        "((n - 1) s^2); Hydrolog 0.8 cut the coefficients of the whole fit instead, "
        "which gave negative shares on years with gaps",
        "R2 = 1 - SSR / SST with SST the sum of squared deviations from the mean of "
        "the values",
        "the values in any unit (degC in the documents): the mean and the amplitudes "
        "come in that unit",
    ),
    assumptions=(
        "the annual cycle is periodic with the mean year; a trend or a change of "
        "regime over the period is spread over the harmonics",
        "a harmonic of no amplitude has no phase: its phase day is then noise of the "
        "rounding, read it only with its amplitude",
    ),
    traps={
        "singular_at_bound": "atan2 of a harmonic without amplitude: the precondition "
        "values_not_all_equal refuses a constant series "
        "(test_a_constant_series_is_refused); a harmonic missing from the signal keeps "
        "a finite phase in range (test_a_missing_harmonic_has_a_finite_phase)",
        "unbounded_iteration": "the least squares are LAPACK's divide and conquer "
        "singular value decomposition (numpy.linalg.lstsq, delegated), bounded by its "
        "own count; the precondition year_covered keeps the design well conditioned "
        "(test_a_season_of_values_is_refused)",
        "gap_propagation": "a NaN day is left out of the fit: type case "
        "values-nan_element and test_gaps_are_left_out_of_the_fit",
        "many_small_terms": "test_thirty_years_of_temperature_match_the_normal_"
        "equations: 10,958 days of Warszawa-Okęcie",
        "moment_cancellation": "SST from the deviations from the mean, not as E[x^2] - "
        "E[x]^2: test_a_large_offset_keeps_the_amplitudes, a signal on top of 1e6",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="exact signals of one or two harmonics recovered: their mean, "
            "amplitudes, phase days and R2 = 1",
            test="tests/unit/test_formulas_regime.py (limit two_harmonics)",
        ),
        Oracle(
            kind="algorithm",
            description="the normal equations of the same design, summed by math.fsum "
            "and solved in exact fractions",
            test="tests/unit/test_formulas_regime.py (limit normal_equations, trap "
            "many_small_terms)",
        ),
    ),
    base={
        "day_of_year": list(range(1, 366)),
        "values": [
            10.0
            + 5.0 * math.cos(2.0 * math.pi * (day - 101) / 365.25)
            + 2.0 * math.cos(4.0 * math.pi * (day - 31) / 365.25)
            for day in range(1, 366)
        ],
        "n_harmonics": 2,
    },
)

SPECS: Final[tuple[FormulaSpec, ...]] = (HARMONIC_FIT,)
"""The Tier A formula of the module."""

TIER_B: Final[tuple[TierBSpec, ...]] = (
    TierBSpec(
        name="annual_cycle_of_a_daily_series",
        function="hydrolog.statistics.harmonics.annual_cycle",
        definition="The day of the hydrological year of each date (1 = 1 November); "
        "the harmonic_fit of every day of the period, the mean annual cycle, and of "
        "each hydrological year with at least 300 days with a value that meet its "
        "preconditions",
        convention="a hydrological year runs from November to October and is named "
        "after the year of its end (IMGW-PIB); a year whose values the fit refuses "
        "(all equal, or a gap too long for the harmonics) has no fit of its own",
        source=Source(
            citation=_ADR_0031, locator="point 3: the result of stats harmonics"
        ),
        constants=(_MIN_YEAR_VALUES,),
    ),
)
"""The Tier B formula of the module (Nogat CMP-2.2)."""


def harmonic_fit(
    day_of_year: NDArray[np.integer] | NDArray[np.float64] | Sequence[float],
    values: NDArray[np.float64] | Sequence[float],
    n_harmonics: int = 2,
) -> HarmonicFit:
    """Fit the mean and the harmonics of the year by least squares, spec harmonic_fit.

    Parameters
    ----------
    day_of_year : array_like of float
        Day of the hydrological year of each value, the first of November first.
    values : array_like of float
        The values; NaN marks a day without a value.
    n_harmonics : int, optional
        Number of harmonics, by default the annual and the half-year one.

    Returns
    -------
    HarmonicFit
        The mean, the harmonics and the share of the variance explained.

    Raises
    ------
    InvalidParameterError
        If the series is refused by the spec: arrays of different lengths, a day
        outside the year, an infinite value, too few values, a gap the harmonics
        cannot span or values all equal (``details.reason``, ``details.constraint``).
    """
    x = checked_inputs(
        HARMONIC_FIT, day_of_year=day_of_year, values=values, n_harmonics=n_harmonics
    )
    out = checked_outputs(HARMONIC_FIT, _fit(x))
    harmonics = [
        Harmonic(amplitude=amplitude, phase_day=phase, explained_variance=share)
        for amplitude, phase, share in zip(
            out.array("amplitudes").tolist(),
            out.array("phase_days").tolist(),
            out.array("explained_variances").tolist(),
            strict=True,
        )
    ]
    return HarmonicFit(
        mean=out.real("mean"),
        harmonics=harmonics,
        r_squared=out.real("r_squared"),
        n_values=int(np.count_nonzero(~np.isnan(x.array("values")))),
    )


def annual_cycle(
    values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    n_harmonics: int = 2,
) -> AnnualCycle:
    """Fit the annual cycle of a daily series over the period and in each year.

    The fit of every day (:func:`harmonic_fit`) and of each hydrological year with
    at least :data:`MIN_YEAR_VALUES` days with a value that the fit accepts
    (:data:`TIER_B`).

    Parameters
    ----------
    values : NDArray[np.float64]
        Daily values; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates (days may be absent).
    n_harmonics : int, optional
        Number of harmonics, 1 to 4, by default 2.

    Returns
    -------
    AnnualCycle
        The fit of the period and of each year with at least
        :data:`MIN_YEAR_VALUES` days with a value that the fit accepts.

    Raises
    ------
    InvalidParameterError
        If the period is refused by the spec ``harmonic_fit``: arrays empty or of
        different lengths, ``n_harmonics`` out of range, fewer than ``4 n_harmonics +
        2`` values, a gap of ``365.25 / (2 n_harmonics)`` days or more, or values all
        equal.
    """
    days = np.asarray(dates).astype("datetime64[D]")
    day_of_year = hydrological_day_of_year(days)
    period = harmonic_fit(day_of_year, values, n_harmonics)
    numbers = np.asarray(values, dtype=np.float64)
    known = ~np.isnan(numbers)
    year_of_day = hydrological_year(days)
    years = np.unique(year_of_day[known])
    rows: list[HarmonicYear] = []
    for year in years.tolist():
        mine = year_of_day == year
        if int(np.count_nonzero(mine & known)) < MIN_YEAR_VALUES:
            continue
        try:
            fit = harmonic_fit(day_of_year[mine], numbers[mine], n_harmonics)
        except InvalidParameterError as refused:
            if refused.details.get("reason") != "precondition_failed":
                raise
            continue  # all equal, or a gap the harmonics cannot span
        rows.append(
            HarmonicYear(
                year=int(year),
                mean=fit.mean,
                harmonics=fit.harmonics,
                r_squared=fit.r_squared,
                n_values=fit.n_values,
            )
        )
    return AnnualCycle(
        n_harmonics=n_harmonics,
        period_days=PERIOD_DAYS,
        first_year=int(years[0]),
        last_year=int(years[-1]),
        period_years=int(years.size),
        period=period,
        years=rows,
    )
