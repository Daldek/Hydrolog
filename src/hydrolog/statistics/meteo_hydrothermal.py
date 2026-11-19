"""Sielianinov's hydrothermal coefficient of a meteorological station.

The coefficient relates precipitation to the sum of temperatures, a measure of the
evaporation (Selyaninov, 1928): k = P / (0.1 Σt). For a month (Skowera and Puła,
2004, p. 172), P is its precipitation sum [mm] and Σt its mean daily temperature times
its days [°C], for a month with a mean above 0 °C; the months of the growing season,
April to September (Radzka, 2014), are given. For the season, P and Σt are summed over
the days of April to September with a mean daily temperature above 10 °C (Miś, 2026,
eq. 4 and "calculated for the April-September period"; Chmist-Sikorska et al., 2022),
in a year whose every day of April to September has both values. This is the day
filter of Polish practice, not the classical season of Russian practice, which sums
every day between the dates of the stable spring and autumn transition of the mean
temperature through 10 °C (Национальный атлас России, vol. 2), cool days inside it
included and warm days outside it left out; Selyaninov's own papers are not openly
available. Classes of Skowera and Puła (2004, p. 172): k <= 0.4 extremely dry, <= 0.7
very dry, <= 1.0 dry, <= 1.3 fairly dry, <= 1.6 optimal, <= 2.0 fairly wet, <= 2.5
wet, <= 3.0 very wet, above 3.0 extremely wet (Miś and Chmist-Sikorska et al. use
other limits). The monthly sums and means follow WMO-No. 1203 (4.4.1 a, c); the
precipitation sums are rounded to 1e-6 mm, so that sums equal in decimal are equal
numbers.

References
----------
Selyaninov, G. T. (1928): O sel'skokhozyaystvennoy otsenke klimata (On the
    agricultural evaluation of climate). Trudy po sel'skokhozyaystvennoy meteorologii
    20, 165-177.
Skowera, B. & Puła, J. (2004): Skrajne warunki pluwiotermiczne w okresie wiosennym na
    obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177.
Radzka, E. (2014): Hydrothermal characteristics of vegetation period in central-
    eastern Poland in years 1971-2005. Folia Pomeranae Universitatis Technologiae
    Stetinensis, Agric., Aliment., Pisc., Zootech. 312(31), 133-142.
Miś, F. (2026): Spatiotemporal variability of atmospheric drought during the growing
    season in Poland: a multi-index analysis based on SPEI, VPD, and HTC (1980-2024).
    Theoretical and Applied Climatology 157(12), 790 (section 2, eq. 4).
Chmist-Sikorska, J., Kępińska-Kasprzak, M. & Struzik, P. (2022): Agricultural drought
    assessment on the base of Hydro-thermal Coefficient of Selyaninov in Poland.
    Italian Journal of Agrometeorology (1), 3-12 (p. 5).

The coefficient and its classes are declared by the specs :data:`SIELIANINOV`
(``sielianinov_coefficient``) and :data:`SIELIANINOV_CLASS` (``sielianinov_class``),
Nogat's computation standard (ADR-0050 and ADR-0059); the months, the season and the
means around them are the module's :data:`TIER_B`, and ``docs/FORMULAS.md`` shows both.

Examples
--------
>>> round(sielianinov_coefficient(200.1, 16.3 * 183), 4)
0.6708
>>> sielianinov_class(0.4), sielianinov_class(1.6)
('extremely_dry', 'optimal')
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

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
    Source,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._climate import (
    as_days,
    check_daily,
    complete_years,
    finite,
    grid_of_values,
    mean_of,
    monthly_means,
    monthly_precipitation,
    round_sums,
    years_with_values,
)

__all__ = [
    "HYDROTHERMAL_MONTHS",
    "HydrothermalCoefficient",
    "HydrothermalMonth",
    "HydrothermalMonthSummary",
    "HydrothermalPeriod",
    "HydrothermalYear",
    "SEASON_TEMPERATURE_C",
    "SIELIANINOV",
    "SIELIANINOV_CLASS",
    "SIELIANINOV_CLASSES",
    "SPECS",
    "TIER_B",
    "hydrothermal_coefficient",
    "sielianinov_class",
    "sielianinov_coefficient",
]

HYDROTHERMAL_MONTHS: tuple[int, ...] = (4, 5, 6, 7, 8, 9)
"""The months of the growing season (April to September): their coefficients are
given and the season is taken from their days."""
SEASON_TEMPERATURE_C = 10.0
"""The season sums the days of April to September with a mean temperature above this
[°C]."""
SIELIANINOV_CLASSES: tuple[str, ...] = (
    "extremely_dry",
    "very_dry",
    "dry",
    "fairly_dry",
    "optimal",
    "fairly_wet",
    "wet",
    "very_wet",
    "extremely_wet",
)
"""The classes of Skowera and Puła (2004), driest first."""

_SKOWERA = (
    "Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie "
    "wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177"
)
_SKOWERA_URL = "http://www.acta-agrophysica.org/pdf-108195-38985?filename=38985.pdf"
_SKOWERA_K = Source(
    citation=_SKOWERA,
    locator="p. 172: k = P / (0.1 sum t), P the monthly precipitation [mm], sum t the "
    "monthly sum of the air temperatures above 0 °C, the monthly mean times the days",
    url=_SKOWERA_URL,
)
_KULIK = Source(
    citation="Kulik, M., Baryła, R., Czarnecki, Z. and Bochniak, A. (2016). Warunki "
    "hydrotermiczne w centralnej części rejonu kanału Wieprz-Krzna w 50-leciu "
    "(1966-2015). Agronomy Science 71(3), 1-12",
    locator="p. 2: the coefficient; Table 1, pp. 5-6: P, the mean temperature and k "
    "of April-September at Sosnowica",
    url="https://doi.org/10.24326/as.2016.3.1",
)
_SELYANINOV = Source(
    citation="Selyaninov, G. T. (1928). O sel'skokhozyaystvennoy otsenke klimata. "
    "Trudy po sel'skokhozyaystvennoy meteorologii 20, 165-177",
    locator="the coefficient; not opened here: as Skowera and Puła (2004) print it",
    access="author-provided",
)
_WARSZAWA_K = (
    "Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the "
    "daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020"
)
_TENTH = Fraction(1, 10)


def _coefficient(x: Values) -> float:
    """Return k = P / (0.1 sum t) as 10 P / sum t, the factor exact."""
    return (
        float(1 / _TENTH)
        * x.real("precipitation_mm")
        / x.real("temperature_sum_c_days")
    )


def _finite_coefficient(x: Values) -> bool:
    return not x.real("temperature_sum_c_days") > 0.0 or math.isfinite(_coefficient(x))


def _coefficient_oracle(run: Callable[..., Values]) -> None:
    for rain, warmth in (
        (200.1, 16.3 * 183),
        (21.7, 13.2 * 30),
        (0.4, 1e-300),
        (535.2, 2334.0),
        (3.2, 728.8),
    ):
        out = run(precipitation_mm=rain, temperature_sum_c_days=warmth)
        assert_within(
            out.real("coefficient"),
            float(Fraction(rain) / (_TENTH * Fraction(warmth))),
            rel=1e-15,
            reason="one multiplication and one division, each rounding 1.1e-16",
        )


SIELIANINOV: Final = FormulaSpec(
    name="sielianinov_coefficient",
    title="Sielianinov's hydrothermal coefficient of a month or a season",
    function="hydrolog.statistics.meteo_hydrothermal.sielianinov_coefficient",
    family="index",
    equation="k = P / (0.1 sum t): P the precipitation [mm] and sum t the sum of the "
    "daily mean temperatures [°C·d] of the same days",
    latex=r"k = \frac{P}{0.1\,\sum t}",
    variables=(
        Variable(
            name="precipitation_mm",
            symbol="P",
            unit="mm",
            description="The precipitation of a month or a season.",
            physical=Range(
                low=0.0,
                test_high=26_470.0,
                test_reason="a season holds less than the world's greatest 12-month "
                "rainfall, 26,470 mm at Cherrapunji, 1 August 1860 - 31 July 1861 "
                "(WMO Archive of Weather and Climate Extremes)",
            ),
            applicability="unstated",
            typical=Range(
                low=3.2,
                high=535.2,
                source=Source(
                    citation=_WARSZAWA_K,
                    locator="the precipitation of the months April to September and "
                    "of the seasons of 1991-2020: 3.2 to 535.2 mm",
                ),
            ),
        ),
        Variable(
            name="temperature_sum_c_days",
            symbol=r"\sum t",
            unit="°C·d",
            description="The sum of the daily mean temperatures of the same days: a "
            "month's mean times its days, or the sum over the days of a season.",
            physical=Range(
                test_low=-99_700.0,
                test_high=20_700.0,
                test_reason="a year of daily means at absolute zero (-273.15 °C times "
                "365) or at the highest temperature on record (56.7 °C times 365)",
            ),
            applicability="unstated",
            typical=Range(
                low=150.8,
                high=3297.0,
                source=Source(
                    citation=_WARSZAWA_K,
                    locator="the sums of the months April to September and of the "
                    "seasons of 1991-2020: 150.8 to 3297.0 °C·d",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="coefficient",
            unit="-",
            symbol="k",
            description="The hydrothermal coefficient.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_SKOWERA_K, _KULIK, _SELYANINOV),
    constraints=(
        Constraint(
            name="a_positive_temperature_sum",
            cls="precondition",
            check=lambda x: x.real("temperature_sum_c_days") > 0.0,
            text="sum t > 0: a month with a mean above 0 °C, a season with a warm day",
            source=_SKOWERA_K,
            satisfied={"temperature_sum_c_days": 400.0},
            violated={"temperature_sum_c_days": -10.0},
            boundary={"temperature_sum_c_days": 0.0},
            boundary_holds=False,
        ),
        Constraint(
            name="a_finite_coefficient",
            cls="precondition",
            check=_finite_coefficient,
            text="P / (0.1 sum t) is a finite number: sum t is not vanishingly small "
            "against P",
            source=_SKOWERA_K,
            satisfied={"precipitation_mm": 200.1, "temperature_sum_c_days": 2982.9},
            violated={"precipitation_mm": 200.1, "temperature_sum_c_days": 1e-307},
        ),
    ),
    constants=(
        Constant(
            name="tenth",
            value=_TENTH,
            unit="mm/(°C·d)",
            symbol="0.1",
            source=_SKOWERA_K,
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"precipitation_mm": 1, "temperature_sum_c_days": -1},
        limits=(
            Limit(
                name="exact_oracle",
                text="k equals P / (0.1 sum t) in exact fractions",
                check=_coefficient_oracle,
            ),
            Limit(
                name="no_precipitation",
                text="no precipitation gives k = 0",
                inputs={"precipitation_mm": 0.0, "temperature_sum_c_days": 400.0},
                expected={"coefficient": 0.0},
                tolerance=Tolerance(abs=0.0, reason="0 divided by a positive sum"),
            ),
        ),
    ),
    validation="none: an index of precipitation and temperature",
    formula_version=1,
    status="referenced",
    conventions=(
        "computed as 10 P / sum t, the factor 1 / 0.1 exact",
        "the series function gives a month's sum and mean times its days (April to "
        "September, a mean above 0 °C) or the sums over the days of April to September "
        "above 10 °C (Miś 2026; Tier B hydrothermal_season)",
    ),
    traps={
        "singular_at_bound": "preconditions a_positive_temperature_sum and "
        "a_finite_coefficient: sum t at 0 and vanishingly small is refused",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="P / (0.1 sum t) in exact fractions (fractions.Fraction)",
            test="tests/unit/test_formulas_meteo_hydrothermal.py (limit exact_oracle)",
        ),
    ),
)


def sielianinov_coefficient(
    precipitation_mm: float, temperature_sum_c_days: float
) -> float:
    """Return Sielianinov's hydrothermal coefficient, spec sielianinov_coefficient.

    Parameters
    ----------
    precipitation_mm : float
        The precipitation of a month or a season [mm].
    temperature_sum_c_days : float
        The sum of the daily mean temperatures of the same days [°C·d].

    Returns
    -------
    float
        The coefficient.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec, a sum of temperatures that is not
        positive among them (``precondition_failed``).
    """
    x = checked_inputs(
        SIELIANINOV,
        precipitation_mm=precipitation_mm,
        temperature_sum_c_days=temperature_sum_c_days,
    )
    return checked_outputs(SIELIANINOV, {"coefficient": _coefficient(x)}).real(
        "coefficient"
    )


_CLASS_TO = tuple(f"{name}_to" for name in SIELIANINOV_CLASSES[:-1])
_CLASS_LIMITS = Source(
    citation=_SKOWERA,
    locator="p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 "
    "dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly "
    "wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet",
    url=_SKOWERA_URL,
)


def _class(x: Values) -> str:
    value = x.real("coefficient")
    for limit, name in zip(_CLASS_TO, SIELIANINOV_CLASSES, strict=False):
        if value <= SIELIANINOV_CLASS.constant(limit):
            return name
    return SIELIANINOV_CLASSES[-1]


def _ordered_classes(run: Callable[..., Values]) -> None:
    ranks = [
        SIELIANINOV_CLASSES.index(
            run(coefficient=step / 100).choice("sielianinov_class")
        )
        for step in range(501)
    ]
    assert ranks == sorted(ranks), "a larger coefficient gave a drier class"


SIELIANINOV_CLASS: Final = FormulaSpec(
    name="sielianinov_class",
    title="Class of Sielianinov's hydrothermal coefficient (Skowera and Puła)",
    function="hydrolog.statistics.meteo_hydrothermal.sielianinov_class",
    family="classification",
    equation="k <= 0.4 extremely dry, (0.4, 0.7] very dry, (0.7, 1.0] dry, (1.0, 1.3] "
    "fairly dry, (1.3, 1.6] optimal, (1.6, 2.0] fairly wet, (2.0, 2.5] wet, (2.5, "
    "3.0] very wet, above 3.0 extremely wet",
    latex=r"k \le 0.4,\ (0.4, 0.7],\ (0.7, 1.0],\ (1.0, 1.3],\ (1.3, 1.6],\ (1.6, "
    r"2.0],\ (2.0, 2.5],\ (2.5, 3.0],\ > 3.0",
    variables=(
        Variable(
            name="coefficient",
            symbol="k",
            unit="-",
            description="A hydrothermal coefficient.",
            physical=Range(
                low=0.0,
                test_high=52.7,
                test_reason="ten times the largest monthly coefficient of the "
                "project's data (5.27 at Warszawa-Okęcie)",
            ),
            applicability="unstated",
            typical=Range(
                low=0.1,
                high=5.27,
                source=Source(
                    citation=_WARSZAWA_K,
                    locator="the coefficients of the months April to September of "
                    "1991-2020: 0.10 to 5.27",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="sielianinov_class",
            unit="-",
            kind="choice",
            description="The class, driest first.",
            choices=SIELIANINOV_CLASSES,
        ),
    ),
    sources=(_CLASS_LIMITS,),
    constants=tuple(
        Constant(
            name=name,
            value=value,
            unit="-",
            symbol=f"{value:g}",
            source=_CLASS_LIMITS,
        )
        for name, value in zip(
            _CLASS_TO, (0.4, 0.7, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0), strict=True
        )
    ),
    properties=Properties(
        units="unit_specific",
        limits=(
            Limit(
                name="ordered_classes",
                text="a larger coefficient never gives a drier class",
                check=_ordered_classes,
            ),
        ),
    ),
    validation="none: a classification",
    formula_version=1,
    status="referenced",
    conventions=(
        "each limit belongs to the class below it, as the source prints (k <= 0.4 "
        "extremely dry); the source's text speaks of ten classes and lists nine",
        "Miś (2026) and Chmist-Sikorska et al. (2022) use other limits",
    ),
    traps={
        "class_limit": "reference cases skowera-pula-*: each limit and just above it",
        "gap_propagation": "type case coefficient-nan: NaN is refused; a month without "
        "a coefficient has no class",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
)


def sielianinov_class(coefficient: float) -> str:
    """Return the class of a hydrothermal coefficient, spec sielianinov_class.

    Parameters
    ----------
    coefficient : float
        The coefficient.

    Returns
    -------
    str
        The class (:data:`SIELIANINOV_CLASSES`).

    Raises
    ------
    InvalidParameterError
        If the coefficient is refused by the spec.
    """
    x = checked_inputs(SIELIANINOV_CLASS, coefficient=coefficient)
    return checked_outputs(SIELIANINOV_CLASS, {"sielianinov_class": _class(x)}).choice(
        "sielianinov_class"
    )


def _coefficient_of(precipitation: float, temperature_sum: float) -> float:
    """Return k, ``NaN`` where its spec refuses a precondition (no warmth)."""
    try:
        return sielianinov_coefficient(precipitation, temperature_sum)
    except InvalidParameterError as refused:
        if refused.details.get("reason") == "precondition_failed":
            return math.nan
        raise


def _class_of(coefficient: float | None) -> str | None:
    return None if coefficient is None else sielianinov_class(coefficient)


@dataclass
class HydrothermalMonth(JsonResultMixin):
    """The coefficient of one month of a year.

    Attributes
    ----------
    month : int
        Calendar month.
    coefficient : float or None
        k = 10 P / (T n): P the monthly sum [mm], T the monthly mean temperature
        [°C], n the days of the month; ``None`` without both or with T <= 0.
    sielianinov_class : str or None
        Its class (:data:`SIELIANINOV_CLASSES`).
    """

    month: int
    coefficient: float | None
    sielianinov_class: str | None


@dataclass
class HydrothermalYear(JsonResultMixin):
    """The coefficients of one year.

    Attributes
    ----------
    year : int
        The calendar year.
    months : list of HydrothermalMonth
        April to September.
    season_coefficient : float or None
        k of the days of April to September with a mean temperature above 10 °C;
        ``None`` unless every day of April to September has both values.
    season_class : str or None
        Its class.
    season_days : int or None
        Those days.
    """

    year: int
    months: list[HydrothermalMonth]
    season_coefficient: float | None
    season_class: str | None
    season_days: int | None


@dataclass
class HydrothermalMonthSummary(JsonResultMixin):
    """One month over the period.

    Attributes
    ----------
    month : int
        Calendar month.
    n_years : int
        Years with a coefficient of the month.
    mean_coefficient : float or None
        Their mean.
    class_counts : dict of str to int
        How many of them fall in each class.
    """

    month: int
    n_years: int
    mean_coefficient: float | None
    class_counts: dict[str, int]


@dataclass
class HydrothermalPeriod(JsonResultMixin):
    """The coefficients over the period.

    Attributes
    ----------
    n_years : int
        Years with a season coefficient.
    mean_season_coefficient : float or None
        Their mean.
    mean_season_class : str or None
        Its class.
    months : list of HydrothermalMonthSummary
        April to September.
    """

    n_years: int
    mean_season_coefficient: float | None
    mean_season_class: str | None
    months: list[HydrothermalMonthSummary]


@dataclass
class HydrothermalCoefficient(JsonResultMixin):
    """Sielianinov's hydrothermal coefficient of months and seasons (M14).

    Attributes
    ----------
    first_year, last_year : int
        First and last calendar year with a value.
    period_years : int
        Years with a value.
    years : list of HydrothermalYear
        Every year with a value.
    period : HydrothermalPeriod
        The means and the class counts.
    """

    first_year: int
    last_year: int
    period_years: int
    years: list[HydrothermalYear]
    period: HydrothermalPeriod


def hydrothermal_coefficient(
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    tmean_c: NDArray[np.float64] | Sequence[float],
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
) -> HydrothermalCoefficient:
    """Sielianinov's hydrothermal coefficient of the months IV-IX and of the season.

    The season is the days of April to September with a mean temperature above 10 °C
    (Miś, 2026, eq. 4).

    Parameters
    ----------
    dates : array_like of datetime64
        The days, strictly increasing (days may be absent).
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    tmean_c : array_like of float
        Daily mean temperature [°C]; ``NaN`` on a missing day.
    accumulated : array_like of bool, optional
        Accumulated totals of precipitation: they stand for the missing days before
        them in the monthly sums and are missing days of the season.

    Returns
    -------
    HydrothermalCoefficient
        The coefficients of each calendar year and their means.

    Raises
    ------
    InvalidParameterError
        If an array is empty or of another length, the dates do not increase, a
        precipitation is negative or no day has a value.
    """
    days = as_days(dates)
    rain = np.asarray(precipitation_mm, dtype=np.float64)
    temperature = np.asarray(tmean_c, dtype=np.float64)
    check_daily(days, rain, temperature)
    flags = (
        np.zeros(rain.size, dtype=bool)
        if accumulated is None
        else np.asarray(accumulated, dtype=bool)
    )
    if flags.size != rain.size:
        raise InvalidParameterError("accumulated must have one flag per value")
    negative = np.flatnonzero(rain < 0)
    if negative.size:
        at = int(negative[0])
        raise InvalidParameterError(
            f"precipitation must not be negative; precipitation_mm[{at}] = "
            f"{rain[at]:g} mm is outside its physical range [0, inf)",
            details={
                "reason": "outside_physical_range",
                "option": "precipitation_mm",
                "variable": "precipitation_mm",
                "value": float(rain[at]),
                "index": [at],
            },
        )
    grid = grid_of_values(
        days, np.isfinite(rain) | np.isfinite(temperature), "calendar"
    )
    raw = grid.place(days, rain)
    totals = grid.place_flags(days, flags) & np.isfinite(raw)
    daily_rain = np.where(totals, np.nan, raw)
    daily_t = grid.place(days, temperature)
    month_rain = monthly_precipitation(grid, raw, totals)
    month_warmth = monthly_means(grid, daily_t) * grid.days_in_month()
    both = np.isfinite(daily_rain) & np.isfinite(daily_t)
    in_season = np.isin(grid.month, HYDROTHERMAL_MONTHS)
    complete = complete_years(grid, both | ~in_season)
    with np.errstate(invalid="ignore"):
        warm = both & in_season & (daily_t > SEASON_TEMPERATURE_C)
    starts = grid.year_starts()
    warm_rain = round_sums(np.add.reduceat(np.where(warm, daily_rain, 0.0), starts))
    warm_t = np.add.reduceat(np.where(warm, daily_t, 0.0), starts)
    warm_days = np.add.reduceat(warm.astype(np.int64), starts)
    present = years_with_values(grid, np.isfinite(raw) | np.isfinite(daily_t))
    slots = [grid.months.index(month) for month in HYDROTHERMAL_MONTHS]
    monthly = np.full(month_rain.shape, np.nan)
    season = np.full(grid.n_years, np.nan)
    for row in np.flatnonzero(present).tolist():
        for slot in slots:
            rain_of, warmth_of = month_rain[row, slot], month_warmth[row, slot]
            if np.isfinite(rain_of) and np.isfinite(warmth_of):
                monthly[row, slot] = _coefficient_of(rain_of, warmth_of)
        if complete[row]:
            season[row] = _coefficient_of(warm_rain[row], warm_t[row])
    rows: list[HydrothermalYear] = []
    for row in np.flatnonzero(present).tolist():
        months = [
            HydrothermalMonth(
                month,
                finite(monthly[row, slot]),
                _class_of(finite(monthly[row, slot])),
            )
            for month, slot in zip(HYDROTHERMAL_MONTHS, slots, strict=True)
        ]
        value = finite(season[row])
        rows.append(
            HydrothermalYear(
                year=grid.first_year + row,
                months=months,
                season_coefficient=value,
                season_class=_class_of(value),
                season_days=int(warm_days[row]) if complete[row] else None,
            )
        )
    summaries: list[HydrothermalMonthSummary] = []
    for month, slot in zip(HYDROTHERMAL_MONTHS, slots, strict=True):
        column = monthly[present, slot]
        values = column[np.isfinite(column)]
        counts = dict.fromkeys(SIELIANINOV_CLASSES, 0)
        for value in values.tolist():
            counts[sielianinov_class(value)] += 1
        summaries.append(
            HydrothermalMonthSummary(
                month=month,
                n_years=int(values.size),
                mean_coefficient=mean_of(values),
                class_counts=counts,
            )
        )
    seasons = season[present]
    mean_season = mean_of(seasons)
    return HydrothermalCoefficient(
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(present.sum()),
        years=rows,
        period=HydrothermalPeriod(
            n_years=int(np.isfinite(seasons).sum()),
            mean_season_coefficient=mean_season,
            mean_season_class=_class_of(mean_season),
            months=summaries,
        ),
    )


SPECS: Final = (SIELIANINOV, SIELIANINOV_CLASS)
"""The Tier A formulas of the module."""

_WMO_1203_H = Source(
    citation="WMO (2017). WMO Guidelines on the Calculation of Climate Normals. "
    "WMO-No. 1203, Geneva",
    locator="section 4.4.1 (a) and (c), pp. 7-8: a monthly mean needs fewer than 11 "
    "missing days and fewer than 5 in a row, a monthly sum every day or accumulated "
    "totals covering the missing days",
    url="https://library.wmo.int/idurl/4/55797",
)

TIER_B: Final = (
    TierBSpec(
        name="hydrothermal_months",
        function="hydrolog.statistics.meteo_hydrothermal.hydrothermal_coefficient",
        definition="sielianinov_coefficient of each month April to September: P its "
        "precipitation sum, sum t its mean daily temperature times its days, for a "
        "month with both and a mean above 0 °C",
        convention="the months April to September (Radzka 2014); the sums of "
        "precipitation rounded to 1e-6 mm",
        source=_WMO_1203_H,
    ),
    TierBSpec(
        name="hydrothermal_season",
        function="hydrolog.statistics.meteo_hydrothermal.hydrothermal_coefficient",
        definition="sielianinov_coefficient of the days of April to September with a "
        "mean temperature above 10 °C: P and sum t summed over them, in a year whose "
        "every day of April to September has both values",
        convention="the day filter of Polish practice (Miś 2026), not the period "
        "between the stable transitions through 10 °C of Russian practice; an "
        "accumulated total is a missing day of the season",
        source=Source(
            citation="Miś, F. (2026). Spatiotemporal variability of atmospheric "
            "drought during the growing season in Poland: a multi-index analysis based "
            "on SPEI, VPD, and HTC (1980-2024). Theoretical and Applied Climatology "
            "157(12), 790",
            locator="section 2, eq. 4: the days with a mean temperature above 10 °C, "
            "calculated for the April-September period",
        ),
    ),
    TierBSpec(
        name="hydrothermal_period",
        function="hydrolog.statistics.meteo_hydrothermal.hydrothermal_coefficient",
        definition="per month April to September: the mean coefficient of the years "
        "with one and the count of each class; the mean season coefficient and its "
        "class",
        convention="the class of the mean, not the most frequent class",
        source=_CLASS_LIMITS,
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""
