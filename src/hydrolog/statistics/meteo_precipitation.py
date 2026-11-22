"""Precipitation statistics of a daily series of a meteorological station.

Six indices of the daily precipitation P [mm] of a period of years (calendar years, or
hydrological years November - October), each a function of this module:

* :func:`precipitation_sums` -- sums of the months, half-years (XI-IV, V-X), seasons
  (DJF, MAM, JJA, SON) and years, the normals of the period and the sums in % of
  them (M1 of Nogat's plan);
* :func:`precipitation_maxima` -- the largest daily sum of each year and month and the
  largest sums of n consecutive days, with their dates (M2);
* :func:`precipitation_days` -- days with P at or above thresholds, per month and year
  (M5; R10mm and R20mm of the ETCCDI for 10 and 20 mm);
* :func:`precipitation_intensity` -- the mean annual sum and the mean precipitation of
  a wet day, SDII (M4);
* :func:`heavy_precipitation` -- the sums on the days above percentiles of the wet days
  of the period and their share in the total of the wet days, R95pTOT and R99pTOT
  (M7);
* :func:`precipitation_seasonality` -- the monthly regime of the normals, Oliver's
  precipitation concentration index and Walsh and Lawler's seasonality index (M9).

Missing days follow WMO-No. 1203 (:mod:`hydrolog.statistics._climate`): a monthly sum
needs every day, a multi-day total flagged as accumulated (``accumulated``) stands for
the missing days it covers in the sums and is a missing day for every daily statistic;
a monthly count of days is scaled to the days of the month when fewer than 11 days,
and fewer than 5 in a row, are missing; an annual value needs its twelve months, and
the annual maxima, the percentile sums and the spells need every day of the year. A
monthly normal is the mean of the years of the reference period with a value when
they are at least 80 % of its years (4.4.2); the normal of a year, half-year or season
is the sum of the normals of its months (4.3.3). Every sum of daily precipitation is
rounded to 1e-6 mm, so that sums equal in decimal are equal numbers.

The baselines of :func:`precipitation_sums`, :func:`heavy_precipitation` and
:func:`precipitation_seasonality` come from a reference period
(``reference_first_year`` to ``reference_last_year``, by default the analysed years
``first_year`` to ``last_year``), the values of each analysed year from its own days:
the normals are the benchmark of the sums in % of them (WMO-No. 1203, chapters 2 and
3, section 5.1: the climatological standard normal 1991-2020 for monitoring, the
reference normal 1961-1990 for climate change), the percentiles of R95p and R99p are
those of the wet days of a base period (Klein Tank et al., 2009; Zhang et al., 2011:
1961-1990; WMO-No. 1203, 5.2.2: a period longer than 30 years suits percentiles),
and the regime is that of the normals.

The formulas of a span of days or of twelve months are declared by specs (Nogat's
computation standard, ADR-0050 and ADR-0059): :data:`SDII` (``sdii``),
:data:`WET_DAY_PERCENTILE` (``wet_day_percentile``), :data:`HEAVY_SHARE`
(``heavy_precipitation_share``), :data:`PCI` (``precipitation_concentration_index``),
:data:`PCI_CLASS` (``pci_class``) and :data:`SI_CLASS` (``si_class``), with the
seasonality index of :mod:`hydrolog.statistics.regime` (``seasonality_index``). The
series functions compute through them; the sums, normals, maxima, counts of days and
the regime around them are the module's :data:`TIER_B`, and ``docs/FORMULAS.md``
shows both.

References
----------
WMO (2017): WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203.
Zhang, X. et al. (2011): Indices for monitoring changes in extremes based on daily
    temperature and precipitation data. WIREs Climate Change 2(6), 851-870.
Zhang, X., Hegerl, G., Zwiers, F. W. & Kenyon, J. (2005): Avoiding inhomogeneity in
    percentile-based indices of temperature extremes. Journal of Climate 18(11),
    1641-1651.
Klein Tank, A. M. G., Zwiers, F. W. & Zhang, X. (2009): Guidelines on analysis of
    extremes in a changing climate in support of informed decisions for adaptation.
    WCDMP-No. 72, WMO-TD No. 1500, Geneva.
Oliver, J. E. (1980): Monthly precipitation distribution: a comparative index.
    Professional Geographer 32(3), 300-309.
Walsh, R. P. D. & Lawler, D. M. (1981): Rainfall seasonality: description, spatial
    patterns and change through time. Weather 36(7), 201-208.
Hyndman, R. J. & Fan, Y. (1996): Sample quantiles in statistical packages. The
    American Statistician 50(4), 361-365 (quantile type 8).

Examples
--------
>>> found = wet_day_intensity([0.0, 1.0, 2.5, np.nan, 13.1], 1.0)
>>> found.wet_days, round(found.wet_day_total_mm, 6), round(found.sdii_mm, 4)
(3, 16.6, 5.5333)
>>> round(wet_day_percentile(np.arange(1.0, 101.0), 1.0, 95.0), 4)
95.65
>>> share = heavy_precipitation_share(np.arange(1.0, 101.0), 1.0, 95.65)
>>> share.heavy_mm, share.heavy_days, round(share.share_percent, 5)
(490.0, 5, 9.70297)
>>> precipitation_concentration_index([0.0] * 11 + [50.0]), pci_class(10.0)
(100.0, 'uniform')
>>> si_class(0.2)
'equable_wetter_season'
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final, NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import CalculationError, InvalidParameterError
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
    Symmetry,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._climate import (
    DailyGrid,
    DailyPrecipitation,
    block_extreme,
    complete_years,
    finite,
    mean_of,
    month_quality,
    monthly_counts,
    monthly_normals,
    multimonth_normal,
    normal,
    precipitation_periods,
    precipitation_record,
    rolling_sum,
    round_sum,
    round_sums,
)
from hydrolog.statistics.regime import seasonality_index

__all__ = [
    "DEFAULT_DURATIONS_DAYS",
    "DEFAULT_PERCENTILES",
    "DEFAULT_THRESHOLDS_MM",
    "DEFAULT_WET_DAY_MM",
    "HEAVY_SHARE",
    "HeavyPrecipitation",
    "HeavyPrecipitationPeriod",
    "HeavyPrecipitationShare",
    "HeavyPrecipitationYear",
    "MIN_WET_DAYS",
    "PCI",
    "PCI_CLASS",
    "PCI_CLASSES",
    "PrecipitationDays",
    "PrecipitationDaysMonth",
    "PrecipitationDaysPeriod",
    "PrecipitationDaysYear",
    "PrecipitationDuration",
    "PrecipitationDurationSummary",
    "PrecipitationIntensity",
    "PrecipitationIntensityMonth",
    "PrecipitationIntensityPeriod",
    "PrecipitationIntensityYear",
    "PrecipitationMaxima",
    "PrecipitationMaximaPeriod",
    "PrecipitationMaximaYear",
    "PrecipitationMonthMaximum",
    "PrecipitationMonthMaximumSummary",
    "PrecipitationMonthStatistics",
    "PrecipitationMonthSum",
    "PrecipitationRegimeMonth",
    "PrecipitationSeasonality",
    "PrecipitationSeasonalityPeriod",
    "PrecipitationSeasonalityYear",
    "PrecipitationSumPeriod",
    "PrecipitationSumYear",
    "PrecipitationSums",
    "SDII",
    "SI_CLASS",
    "SI_CLASSES",
    "SPECS",
    "TIER_B",
    "WET_DAY_PERCENTILE",
    "WetDayIntensity",
    "heavy_precipitation",
    "heavy_precipitation_share",
    "precipitation_concentration_index",
    "precipitation_days",
    "precipitation_intensity",
    "precipitation_maxima",
    "precipitation_seasonality",
    "precipitation_sums",
    "pci_class",
    "si_class",
    "wet_day_intensity",
    "wet_day_percentile",
    "PRECIPITATION_INDICES",
]

PRECIPITATION_INDICES: tuple[str, ...] = (
    "sums",
    "maxima",
    "days",
    "intensity",
    "heavy",
    "seasonality",
)
"""The indices of ``meteo precipitation``, one function of this module each."""
DEFAULT_DURATIONS_DAYS: tuple[int, ...] = (2, 3, 5, 10)
"""Durations [days] of the largest multi-day sums (Nogat's plan, M2; Rx5day of the
ETCCDI for 5)."""
DEFAULT_THRESHOLDS_MM: tuple[float, ...] = (0.1, 1.0, 10.0, 20.0)
"""Thresholds [mm] of the days with precipitation: a day with precipitation (0.1 mm),
a wet day, R10mm and R20mm of the ETCCDI."""
DEFAULT_WET_DAY_MM = 1.0
"""A wet day has at least this precipitation [mm] (ETCCDI, Zhang et al., 2011)."""
DEFAULT_PERCENTILES: tuple[float, ...] = (95.0, 99.0)
"""Percentiles of the wet days of R95pTOT and R99pTOT (ETCCDI)."""
MIN_WET_DAYS = 100
"""Fewest wet days of the period the percentiles of :func:`heavy_precipitation` are
estimated from."""

PCI_CLASSES: tuple[str, ...] = (
    "uniform",
    "moderate",
    "irregular",
    "strongly_irregular",
)
"""Classes of the precipitation concentration index (Oliver, 1980; spec
``pci_class``)."""
SI_CLASSES: tuple[str, ...] = (
    "very_equable",
    "equable_wetter_season",
    "rather_seasonal",
    "seasonal",
    "markedly_seasonal",
    "most_in_three_months",
    "extreme",
)
"""Classes of the seasonality index (Walsh and Lawler, 1981; spec ``si_class``)."""


# --- the formulas of a span of days and of twelve months (specs) ----------------------

_ETCCDI_URL = "https://etccdi.pacificclimate.org/list_27_indices.shtml"
_ETCCDI = (
    "ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. "
    "Expert Team on Climate Change Detection and Indices"
)
_ETCCDI_WET = Source(
    citation=_ETCCDI,
    locator="SDII: the precipitation of the wet days (RR >= 1 mm) of a period over "
    "their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: "
    "the annual total of the days with RR > RRwn95, the 95th percentile of the "
    "precipitation of the wet days of the base period 1961-1990",
    url=_ETCCDI_URL,
)
_CLIMPACT = Source(
    citation="ClimPACT2, the indices of the Expert Team on Sector-specific Climate "
    "Indices (ET-SCI)",
    locator="climate.indices.csv: R95p, the annual sum of the precipitation of the "
    "days above the 95th percentile of the wet days; R95pTOT = 100 R95p / PRCPTOT",
    url="https://github.com/ARCCSS-extremes/climpact",
)
_HYNDMAN_FAN = Source(
    citation="Hyndman, R. J. and Fan, Y. (1996). Sample quantiles in statistical "
    "packages. The American Statistician 50(4), 361-365",
    locator="definition 8: Q(p) = x(k) + (h - k) (x(k + 1) - x(k)), h = (n + 1/3) p + "
    "1/3 and k its whole part, x(k) the k-th smallest of n values",
    access="author-provided",
)
_NUMPY_PERCENTILE = Source(
    citation="NumPy 2 documentation, numpy.percentile",
    locator="method 'median_unbiased': definition 8 of Hyndman and Fan (1996), "
    "virtual index n p + 1/3 + p / 3 - 1 counted from 0",
    url="https://numpy.org/doc/stable/reference/generated/numpy.percentile.html",
)
_CLIMDEX = Source(
    citation="Bronaugh, D. (2020). climdex.pcic 1.1-11: PCIC implementation of "
    "Climdex routines, R package",
    locator="R/climdex.r: the percentiles of the wet days (not NA, at least 1 mm) of "
    "the base period by quantile type 8",
    url="https://cran.r-project.org/src/contrib/Archive/climdex.pcic/",
)
_DE_LUIS = (
    "de Luis, M., González-Hidalgo, J. C., Brunetti, M. and Longares, L. A. (2011). "
    "Precipitation concentration changes in Spain 1946-2005. Natural Hazards and "
    "Earth System Sciences 11, 1259-1265"
)
_DE_LUIS_URL = "https://nhess.copernicus.org/articles/11/1259/2011/"
_OLIVER = Source(
    citation="Oliver, J. E. (1980). Monthly precipitation distribution: a "
    "comparative index. Professional Geographer 32(3), 300-309",
    locator="the index and its classes; not opened here: as de Luis et al. (2011) "
    "print them",
    access="author-provided",
)
_SUMNER = (
    "Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in "
    "eastern and southern coastal Spain. International Journal of Climatology 21, "
    "219-247"
)
_HYDROTSM = Source(
    citation="Zambrano-Bigiarini, M. hydroTSM: time series management and analysis "
    "for hydrological modelling, R package (CRAN)",
    locator="si(): the seasonality index of Walsh and Lawler (1981), from 0 to 1.83, "
    "and its seven classes",
    url="https://cran.r-project.org/package=hydroTSM",
)
_DAILY_RECORD = (
    "the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January "
    "1966 (WMO Archive of Weather and Climate Extremes)"
)
_MONTH_RECORD = (
    "a month holds less than the world's greatest 12-month rainfall, 26,470 mm at "
    "Cherrapunji, 1 August 1860 - 31 July 1861 (WMO Archive of Weather and Climate "
    "Extremes)"
)
_WARSZAWA = (
    "Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the "
    "daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020"
)
_PRECIPITATION = Variable(
    name="precipitation_mm",
    symbol="P_i",
    unit="mm",
    kind="real_array",
    description="Daily precipitation of the days of a period; NaN on a missing day, "
    "which is left out.",
    physical=Range(low=0.0, test_high=1825.0, test_reason=_DAILY_RECORD),
    applicability="unstated",
    typical=Range(
        low=0.0,
        high=75.8,
        source=Source(
            citation=_WARSZAWA, locator="the daily precipitation: 0 to 75.8 mm"
        ),
    ),
    gaps_allowed=True,
)
_WET_DAY = Variable(
    name="wet_day_mm",
    symbol="P_w",
    unit="mm",
    description="The least precipitation of a wet day.",
    physical=Range(
        low=0.0, low_inclusive=False, test_high=1825.0, test_reason=_DAILY_RECORD
    ),
    applicability="unstated",
    typical=Range(low=1.0, high=1.0, source=_ETCCDI_WET),
)
_WHOLE = Tolerance(abs=0.0, reason="whole numbers of days")


def _wet(x: Values) -> NDArray[np.float64]:
    """Return the precipitation of the wet days, P >= P_w; a missing day is none."""
    values = x.array("precipitation_mm")
    with np.errstate(invalid="ignore"):
        wet: NDArray[np.float64] = values[values >= x.real("wet_day_mm")]
    return wet


def _a_wet_day(source: Source, **base: object) -> Constraint:
    return Constraint(
        name="a_wet_day",
        cls="precondition",
        check=lambda x: _wet(x).size > 0,
        text="at least one day has P >= P_w",
        source=source,
        satisfied={"precipitation_mm": [0.0, 1.0], "wet_day_mm": 1.0, **base},
        violated={"precipitation_mm": [0.0, 0.9], "wet_day_mm": 1.0, **base},
    )


def _exact_wet(values: Sequence[float], wet_day: float) -> list[Fraction]:
    """Return the wet days as exact fractions, the oracles' own selection."""
    return [Fraction(v) for v in values if not math.isnan(v) and v >= wet_day]


def _seeded_days(seed: int) -> list[float]:
    """Return a year of daily precipitation in tenths of a mm, with gaps."""
    rng = np.random.default_rng(seed)
    days = np.round(rng.gamma(0.5, 6.0, size=365), 1)
    days[rng.random(365) < 0.03] = math.nan
    return [float(day) for day in days]


def _sdii(x: Values) -> dict[str, object]:
    wet = _wet(x)
    total = float(np.sum(wet))
    return {
        "sdii_mm": total / wet.size,
        "wet_days": int(wet.size),
        "wet_day_total_mm": total,
    }


def _sdii_oracle(run: Callable[..., Values]) -> None:
    samples = (
        ([0.0, 1.0, 2.5, math.nan, 0.4, 13.1, 1.0], 1.0),
        (_seeded_days(1), 1.0),
        (_seeded_days(2), 0.1),
    )
    for values, wet_day in samples:
        out = run(precipitation_mm=values, wet_day_mm=wet_day)
        wet = _exact_wet(values, wet_day)
        assert out.integer("wet_days") == len(wet), "the wet days are counted wrong"
        assert_within(
            [out.real("wet_day_total_mm"), out.real("sdii_mm")],
            [float(sum(wet)), float(sum(wet) / len(wet))],
            rel=1e-14,
            reason="exact fractions against a pairwise sum of up to 365 terms, each "
            "addition rounding 1.1e-16 of a partial sum",
        )


SDII: Final = FormulaSpec(
    name="sdii",
    title="Simple daily intensity index: the mean precipitation of a wet day",
    function="hydrolog.statistics.meteo_precipitation.wet_day_intensity",
    family="index",
    equation=(
        "W = the number of days with P >= Pw; PRCPTOT = the sum of their P; SDII = "
        "PRCPTOT / W"
    ),
    latex=(
        r"W = \#\{i : P_i \ge P_w\},\quad \mathrm{PRCPTOT} = \sum_{P_i \ge P_w} P_i,"
        r"\quad \mathrm{SDII} = \frac{\mathrm{PRCPTOT}}{W}"
    ),
    variables=(_PRECIPITATION, _WET_DAY),
    outputs=(
        Output(
            name="sdii_mm",
            unit="mm",
            symbol=r"\mathrm{SDII}",
            description="The mean precipitation of a wet day.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="wet_days",
            unit="d",
            kind="integer",
            symbol="W",
            description="The wet days.",
            physical=Range(low=1.0),
        ),
        Output(
            name="wet_day_total_mm",
            unit="mm",
            symbol=r"\mathrm{PRCPTOT}",
            description="The precipitation of the wet days.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
    ),
    sources=(_ETCCDI_WET,),
    constraints=(_a_wet_day(_ETCCDI_WET),),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="precipitation_in_another_unit",
                inputs={"precipitation_mm": 1.0, "wet_day_mm": 1.0},
                outputs={"sdii_mm": 1.0, "wet_day_total_mm": 1.0},
                tolerance=Tolerance(
                    abs=2e-323,
                    reason="doubling every value is exact in binary but for a "
                    "quotient in the subnormal range, rounded to a multiple of 5e-324",
                ),
            ),
        ),
        conservation=(
            Conservation(
                name="intensity_times_days_is_the_total",
                text="SDII W = PRCPTOT",
                residual=lambda x, out: (
                    out.real("sdii_mm") * out.integer("wet_days")
                    - out.real("wet_day_total_mm")
                ),
                tolerance=Tolerance(
                    abs=1e-10,
                    reason="one division and one multiplication of a total below "
                    "1e5 mm, each rounding 1.1e-16 of it",
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_oracle",
                text="W, PRCPTOT and SDII equal their values in exact fractions",
                check=_sdii_oracle,
            ),
            Limit(
                name="a_day_at_the_threshold_is_wet",
                text="P = Pw counts as a wet day",
                inputs={"precipitation_mm": [1.0, 0.9, 3.0], "wet_day_mm": 1.0},
                expected={"sdii_mm": 2.0, "wet_day_total_mm": 4.0},
                tolerance=Tolerance(abs=0.0, reason="sums of whole numbers"),
                source=_ETCCDI_WET,
            ),
        ),
    ),
    validation="none: an index of the daily precipitation",
    formula_version=1,
    status="oracle only",
    conventions=(
        "a wet day has P >= Pw (RR >= 1 mm of the ETCCDI); a missing day (NaN) is "
        "left out",
        "the series function takes the days of a complete month or year, or of a "
        "calendar month's complete months pooled, and rounds PRCPTOT to 1e-6 mm; a "
        "span without a wet day has no SDII (climdex.pcic gives 0)",
    ),
    traps={
        "gap_propagation": "type case precipitation_mm-nan_element: a missing day is "
        "left out, never NaN in the outputs",
        "many_small_terms": "limit exact_oracle: PRCPTOT of 365 days against exact "
        "fractions to 1e-14",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="W, PRCPTOT and SDII in exact fractions (fractions.Fraction) "
            "of hand-made and seeded series with gaps",
            test="tests/unit/test_formulas_meteo_precipitation.py (limit exact_oracle)",
        ),
    ),
)


class WetDayIntensity(NamedTuple):
    """The wet days of a period (spec ``sdii``).

    Attributes
    ----------
    sdii_mm : float
        The mean precipitation of a wet day [mm].
    wet_days : int
        The wet days.
    wet_day_total_mm : float
        Their precipitation [mm].
    """

    sdii_mm: float
    wet_days: int
    wet_day_total_mm: float


def wet_day_intensity(
    precipitation_mm: NDArray[np.float64] | Sequence[float], wet_day_mm: float
) -> WetDayIntensity:
    """Return the mean precipitation of a wet day of a period, spec sdii.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day, which is left out.
    wet_day_mm : float
        The least precipitation of a wet day [mm].

    Returns
    -------
    WetDayIntensity
        The index, the wet days and their precipitation.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec, a period without a wet day among them
        (``precondition_failed``).
    """
    x = checked_inputs(SDII, precipitation_mm=precipitation_mm, wet_day_mm=wet_day_mm)
    out = checked_outputs(SDII, _sdii(x), inputs=x)
    return WetDayIntensity(
        out.real("sdii_mm"), out.integer("wet_days"), out.real("wet_day_total_mm")
    )


_PERCENTILE = Variable(
    name="percentile",
    symbol="p",
    unit="%",
    description="The percentile.",
    physical=Range(low=0.0, high=100.0, low_inclusive=False, high_inclusive=False),
    applicability="unstated",
    typical=Range(low=95.0, high=99.0, source=_ETCCDI_WET),
)


def _type8(values: Sequence[float], wet_day: float, percent: float) -> float:
    """Return definition 8 of Hyndman and Fan in exact fractions: the oracle."""
    ranked = sorted(_exact_wet(values, wet_day))
    size = len(ranked)
    h = (size + Fraction(1, 3)) * Fraction(percent) / 100 + Fraction(1, 3)
    if h <= 1:
        return float(ranked[0])
    if h >= size:
        return float(ranked[-1])
    k = math.floor(h)
    return float(ranked[k - 1] + (h - k) * (ranked[k] - ranked[k - 1]))


def _percentile_oracle(run: Callable[..., Values]) -> None:
    samples = (
        ([float(day) for day in range(1, 101)], 1.0),
        ([2.0, 0.5, math.nan, 7.5, 1.0, 1.0, 30.2], 1.0),
        (_seeded_days(3), 1.0),
    )
    for values, wet_day in samples:
        for percent in (0.5, 25.0, 50.0, 95.0, 99.0, 99.9):
            out = run(precipitation_mm=values, wet_day_mm=wet_day, percentile=percent)
            assert_within(
                out.real("percentile_mm"),
                _type8(values, wet_day, percent),
                rel=1e-14,
                reason="exact fractions against NumPy's interpolation, a few "
                "roundings of 1.1e-16",
            )


WET_DAY_PERCENTILE: Final = FormulaSpec(
    name="wet_day_percentile",
    title="Percentile of the precipitation of the wet days (quantile type 8)",
    function="hydrolog.statistics.meteo_precipitation.wet_day_percentile",
    family="statistic",
    equation=(
        "x(1) <= ... <= x(n) the precipitation of the days with P >= Pw; h = (n + 1/3) "
        "p / 100 + 1/3, k its whole part; Q = x(1) for h <= 1, x(n) for h >= n, else "
        "x(k) + (h - k) (x(k + 1) - x(k))"
    ),
    latex=(
        r"h = \left(n + \tfrac{1}{3}\right)\frac{p}{100} + \tfrac{1}{3},\quad Q = "
        r"x_{(k)} + (h - k)\left(x_{(k+1)} - x_{(k)}\right),\quad k = \lfloor h "
        r"\rfloor"
    ),
    variables=(_PRECIPITATION, _WET_DAY, _PERCENTILE),
    outputs=(
        Output(
            name="percentile_mm",
            unit="mm",
            symbol="Q",
            description="The percentile of the precipitation of the wet days.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
    ),
    sources=(_HYNDMAN_FAN, _NUMPY_PERCENTILE, _CLIMDEX, _ETCCDI_WET),
    constraints=(_a_wet_day(_HYNDMAN_FAN),),
    properties=Properties(
        units="homogeneous",
        monotonic={"percentile": 1},
        scalings=(
            Scaling(
                name="precipitation_in_another_unit",
                inputs={"precipitation_mm": 1.0, "wet_day_mm": 1.0},
                outputs={"percentile_mm": 1.0},
                tolerance=Tolerance(
                    abs=2e-323,
                    reason="doubling every value is exact in binary but for an "
                    "interpolation in the subnormal range, rounded to a multiple of "
                    "5e-324",
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_oracle",
                text="Q equals definition 8 of Hyndman and Fan in exact fractions",
                check=_percentile_oracle,
            ),
        ),
    ),
    validation="none: a sample quantile",
    formula_version=1,
    status="referenced",
    conventions=(
        "quantile type 8 of Hyndman and Fan (1996), median-unbiased, as climdex.pcic "
        "1.1-11 (quantile type 8) and NumPy's method median_unbiased",
        "the wet days (P >= Pw) of the period given; a missing day (NaN) is left out",
        "the series function gives the wet days of the reference period and needs "
        "at least 100 of them (too_few_wet_days, Hydrolog's minimum, ADR-0032)",
    ),
    traps={
        "gap_propagation": "type case precipitation_mm-nan_element: a missing day is "
        "left out",
        "singular_at_bound": "the percentile is in (0, 100): h is clipped to [1, n] "
        "by definition 8, limit exact_oracle at 0.5 and 99.9",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="definition 8 of Hyndman and Fan in exact fractions "
            "(fractions.Fraction), written from the paper's equation",
            test="tests/unit/test_formulas_meteo_precipitation.py (limit exact_oracle)",
        ),
    ),
)


def wet_day_percentile(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    wet_day_mm: float,
    percentile: float,
) -> float:
    """Return a percentile of the wet days' precipitation, spec wet_day_percentile.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day, which is left out.
    wet_day_mm : float
        The least precipitation of a wet day [mm].
    percentile : float
        The percentile [%].

    Returns
    -------
    float
        The percentile [mm].

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec, a period without a wet day among them
        (``precondition_failed``).
    """
    x = checked_inputs(
        WET_DAY_PERCENTILE,
        precipitation_mm=precipitation_mm,
        wet_day_mm=wet_day_mm,
        percentile=percentile,
    )
    value = float(
        np.percentile(_wet(x), x.real("percentile"), method="median_unbiased")
    )
    return checked_outputs(WET_DAY_PERCENTILE, {"percentile_mm": value}).real(
        "percentile_mm"
    )


def _heavy(x: Values) -> dict[str, object]:
    values = x.array("precipitation_mm")
    with np.errstate(invalid="ignore"):
        heavy = values[values > x.real("threshold_mm")]
    amount = float(np.sum(heavy))
    total = float(np.sum(_wet(x)))
    return {
        "heavy_mm": amount,
        "heavy_days": int(heavy.size),
        "wet_day_total_mm": total,
        "share_percent": 100.0 * amount / total,
    }


def _heavy_oracle(run: Callable[..., Values]) -> None:
    samples = (
        ([float(day) for day in range(1, 101)], 1.0, 95.65),
        (_seeded_days(4), 1.0, 16.8),
        (_seeded_days(5), 0.1, 29.4),
    )
    for values, wet_day, threshold in samples:
        out = run(precipitation_mm=values, wet_day_mm=wet_day, threshold_mm=threshold)
        heavy = [v for v in _exact_wet(values, wet_day) if v > Fraction(threshold)]
        total = sum(_exact_wet(values, wet_day))
        assert out.integer("heavy_days") == len(heavy), "the heavy days differ"
        assert_within(
            [out.real("heavy_mm"), out.real("share_percent")],
            [float(sum(heavy)), float(100 * sum(heavy) / total)],
            rel=1e-14,
            reason="exact fractions against pairwise sums of up to 365 terms",
        )


HEAVY_SHARE: Final = FormulaSpec(
    name="heavy_precipitation_share",
    title="Precipitation of the days above a threshold and its share of the wet days'",
    function="hydrolog.statistics.meteo_precipitation.heavy_precipitation_share",
    family="index",
    equation=(
        "R = the sum of P over the days with P > Pt (R95p for the 95th percentile of "
        "the wet days), D their number, PRCPTOT the sum of P over the days with P >= "
        "Pw; share = 100 R / PRCPTOT (R95pTOT); Pt >= Pw"
    ),
    latex=(
        r"R = \sum_{P_i > P_t} P_i,\quad \mathrm{PRCPTOT} = \sum_{P_i \ge P_w} P_i,"
        r"\quad s = \frac{100\,R}{\mathrm{PRCPTOT}},\quad P_t \ge P_w"
    ),
    variables=(
        _PRECIPITATION,
        _WET_DAY,
        Variable(
            name="threshold_mm",
            symbol="P_t",
            unit="mm",
            description="The threshold, a percentile of the wet days of a reference "
            "period.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1825.0,
                test_reason=_DAILY_RECORD,
            ),
            applicability="unstated",
            typical=Range(
                low=16.8,
                high=29.43,
                source=Source(
                    citation=_WARSZAWA,
                    locator="the 95th and 99th percentiles of the wet days of "
                    "1991-2020: 16.8 and 29.43 mm",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="heavy_mm",
            unit="mm",
            symbol="R",
            description="The precipitation of the days above the threshold (R95p).",
            physical=Range(low=0.0),
        ),
        Output(
            name="heavy_days",
            unit="d",
            kind="integer",
            symbol="D",
            description="The days above the threshold.",
            physical=Range(low=0.0),
        ),
        Output(
            name="wet_day_total_mm",
            unit="mm",
            symbol=r"\mathrm{PRCPTOT}",
            description="The precipitation of the wet days.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="share_percent",
            unit="%",
            symbol="s",
            description="R in % of PRCPTOT (R95pTOT of ClimPACT).",
            physical=Range(low=0.0, high=100.0),
            boundary_tolerance=1e-9,
        ),
    ),
    sources=(_ETCCDI_WET, _CLIMPACT),
    constraints=(
        _a_wet_day(_ETCCDI_WET, threshold_mm=20.0),
        Constraint(
            name="threshold_of_a_wet_day",
            cls="precondition",
            check=lambda x: x.real("threshold_mm") >= x.real("wet_day_mm"),
            text="Pt >= Pw: a day above the threshold is a wet day",
            source=_ETCCDI_WET,
            satisfied={"wet_day_mm": 1.0, "threshold_mm": 16.8},
            violated={"wet_day_mm": 1.0, "threshold_mm": 0.9},
            boundary={"wet_day_mm": 1.0, "threshold_mm": 1.0},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"precipitation_mm": 1, "threshold_mm": -1},
        scalings=(
            Scaling(
                name="precipitation_in_another_unit",
                inputs={
                    "precipitation_mm": 1.0,
                    "wet_day_mm": 1.0,
                    "threshold_mm": 1.0,
                },
                outputs={"heavy_mm": 1.0, "wet_day_total_mm": 1.0},
                tolerance=Tolerance(
                    abs=0.0, reason="doubling every value is exact in binary"
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_oracle",
                text="R, D and the share equal their values in exact fractions",
                check=_heavy_oracle,
            ),
        ),
    ),
    validation="none: an index of the daily precipitation",
    formula_version=1,
    status="referenced",
    conventions=(
        "a day counts above the threshold when P > Pt (strictly), a wet day when P "
        ">= Pw; a missing day (NaN) is left out",
        "R is R95p of ClimPACT and of the ETCCDI's list (a sum in mm), the share "
        "R95pTOT of ClimPACT (100 R / PRCPTOT); ECA&D's R95pTOT divides by the "
        "precipitation of every day",
        "the series function takes the days of a complete year, the threshold of "
        "wet_day_percentile, and rounds R and PRCPTOT to 1e-6 mm; a year without a "
        "wet day has no share",
    ),
    traps={
        "difference_denominator": "precondition a_wet_day: PRCPTOT > 0, the sum of "
        "values of at least Pw > 0",
        "gap_propagation": "type case precipitation_mm-nan_element: a missing day is "
        "left out",
        "many_small_terms": "limit exact_oracle: the sums of 365 days against exact "
        "fractions to 1e-14",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="R, D and the share in exact fractions (fractions.Fraction) "
            "of the wet days 1 to 100 mm and of seeded series with gaps",
            test="tests/unit/test_formulas_meteo_precipitation.py (limit exact_oracle)",
        ),
    ),
)


class HeavyPrecipitationShare(NamedTuple):
    """The days above a threshold (spec ``heavy_precipitation_share``).

    Attributes
    ----------
    heavy_mm : float
        Their precipitation [mm] (R95p for the 95th percentile).
    heavy_days : int
        Their number.
    wet_day_total_mm : float
        The precipitation of the wet days [mm] (PRCPTOT).
    share_percent : float
        ``heavy_mm`` in % of ``wet_day_total_mm`` (R95pTOT).
    """

    heavy_mm: float
    heavy_days: int
    wet_day_total_mm: float
    share_percent: float


def heavy_precipitation_share(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    wet_day_mm: float,
    threshold_mm: float,
) -> HeavyPrecipitationShare:
    """Sum the days above a threshold, spec heavy_precipitation_share.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day, which is left out.
    wet_day_mm : float
        The least precipitation of a wet day [mm].
    threshold_mm : float
        The threshold [mm], not below ``wet_day_mm``.

    Returns
    -------
    HeavyPrecipitationShare
        The precipitation and the days above the threshold and their share.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec, a period without a wet day among them
        (``precondition_failed``).
    """
    x = checked_inputs(
        HEAVY_SHARE,
        precipitation_mm=precipitation_mm,
        wet_day_mm=wet_day_mm,
        threshold_mm=threshold_mm,
    )
    out = checked_outputs(HEAVY_SHARE, _heavy(x), inputs=x)
    return HeavyPrecipitationShare(
        out.real("heavy_mm"),
        out.integer("heavy_days"),
        out.real("wet_day_total_mm"),
        out.real("share_percent"),
    )


def _months_variable(symbol: str) -> Variable:
    return Variable(
        name="monthly_mm",
        symbol=symbol,
        unit="mm",
        kind="real_array",
        description="The twelve monthly totals of a year or the twelve monthly "
        "normals, in any order.",
        physical=Range(low=0.0, test_high=26_470.0, test_reason=_MONTH_RECORD),
        applicability="unstated",
        typical=Range(
            low=0.4,
            high=295.0,
            source=Source(
                citation=_WARSZAWA,
                locator="the monthly sums of 1991-2020: 0.4 to 295.0 mm",
            ),
        ),
        min_length=12,
        max_length=12,
    )


def _a_positive_total(source: Source) -> Constraint:
    return Constraint(
        name="a_positive_total",
        cls="precondition",
        check=lambda x: float(np.sum(x.array("monthly_mm"))) > 0.0,
        text="the total of the twelve months is positive",
        source=source,
        satisfied={"monthly_mm": [0.0] * 11 + [0.1]},
        violated={"monthly_mm": [0.0] * 12},
    )


def _shares(x: Values) -> NDArray[np.float64]:
    """Return each month's share of the total: the indices need no squares of sums."""
    monthly = x.array("monthly_mm")
    shares: NDArray[np.float64] = monthly / float(np.sum(monthly))
    return shares


def _exact_pci(monthly: Sequence[float]) -> float:
    values = [Fraction(v) for v in monthly]
    total = sum(values)
    return float(100 * sum(v * v for v in values) / (total * total))


def _months_oracle(
    output: str, exact: Callable[[Sequence[float]], float]
) -> Callable[[Callable[..., Values]], None]:
    def check(run: Callable[..., Values]) -> None:
        rng = np.random.default_rng(20261119)
        samples = [
            [31.0, 29.8, 29.0, 35.1, 55.5, 63.9, 82.2, 60.6, 50.4, 40.2, 36.0, 36.1],
            [0.0] * 6 + [1e-300] + [0.0] * 5,
            *(np.round(rng.gamma(1.5, 30.0, size=12), 1).tolist() for _ in range(20)),
        ]
        for monthly in samples:
            assert_within(
                run(monthly_mm=monthly).real(output),
                exact(monthly),
                rel=1e-14,
                reason="exact fractions against a sum of twelve shares, each "
                "rounding 1.1e-16",
            )

    return check


def _permuted(x: Values) -> dict[str, object]:
    return {"monthly_mm": x.array("monthly_mm")[::-1].copy()}


PCI: Final = FormulaSpec(
    name="precipitation_concentration_index",
    title="Oliver's precipitation concentration index of twelve monthly totals",
    function="hydrolog.statistics.meteo_precipitation.precipitation_concentration_index",
    family="index",
    equation="PCI = 100 sum(p_i^2) / (sum p_i)^2 over the twelve monthly totals p_i",
    latex=r"\mathrm{PCI} = 100\,\frac{\sum_{i=1}^{12} p_i^2}{\left(\sum_{i=1}^{12} "
    r"p_i\right)^2}",
    variables=(_months_variable("p_i"),),
    outputs=(
        Output(
            name="pci",
            unit="-",
            symbol=r"\mathrm{PCI}",
            description="The index: 100/12 for equal months, 100 for one wet month.",
            physical=Range(low=100 / 12, high=100.0),
            boundary_tolerance=1e-12,
        ),
    ),
    sources=(
        Source(
            citation=_DE_LUIS,
            locator="eq. 1, p. 1260: PCI = 100 sum p_i^2 / (sum p_i)^2 of the twelve "
            "monthly totals; 8.3 for equal months, 100 for all in one month",
            url=_DE_LUIS_URL,
        ),
        _OLIVER,
    ),
    constraints=(_a_positive_total(_OLIVER),),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="totals_in_another_unit",
                inputs={"monthly_mm": 1.0},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0, reason="doubling every total leaves each share exact"
                ),
            ),
        ),
        symmetries=(
            Symmetry(
                name="months_in_another_order",
                text="the months in reverse order give the same index",
                inputs=_permuted,
                outputs=lambda out: {"pci": out.real("pci")},
                tolerance=Tolerance(
                    abs=1e-12, reason="twelve shares summed in another order"
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_oracle",
                text="PCI equals 100 sum p^2 / (sum p)^2 in exact fractions",
                check=_months_oracle("pci", _exact_pci),
            ),
            Limit(
                name="equal_months",
                text="twelve equal months give 100/12",
                inputs={"monthly_mm": [10.0] * 12},
                expected={"pci": 100 / 12},
                tolerance=Tolerance(abs=1e-13, reason="twelve shares of 1/12"),
            ),
        ),
    ),
    validation="none: an index of the monthly totals",
    formula_version=1,
    status="referenced",
    conventions=(
        "computed from the shares p_i / sum p, which equals the equation without "
        "squaring a sum (no overflow or underflow of the squares)",
        "the series function gives the twelve normals of the reference period or the "
        "twelve monthly sums of a year with all of them; a total of 0 has no index",
    ),
    traps={
        "difference_denominator": "precondition a_positive_total: the total divides",
        "singular_at_bound": "limit exact_oracle: a single month of 1e-300 mm, whose "
        "square underflows, gives 100",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the equation in exact fractions (fractions.Fraction) of the "
            "normals of Warszawa and of seeded monthly totals",
            test="tests/unit/test_formulas_meteo_precipitation.py (limit exact_oracle)",
        ),
    ),
)


def precipitation_concentration_index(
    monthly_mm: NDArray[np.float64] | Sequence[float],
) -> float:
    """Return Oliver's index of monthly totals, spec precipitation_concentration_index.

    Parameters
    ----------
    monthly_mm : array_like of float
        The twelve monthly totals [mm].

    Returns
    -------
    float
        The index.

    Raises
    ------
    InvalidParameterError
        If the totals are refused by the spec, a total of zero among them
        (``precondition_failed``).
    """
    x = checked_inputs(PCI, monthly_mm=monthly_mm)
    value = 100.0 * float(np.sum(_shares(x) ** 2))
    return checked_outputs(PCI, {"pci": value}).real("pci")


def _class_constant(name: str, value: float, source: Source) -> Constant:
    return Constant(
        name=name, value=value, unit="-", symbol=f"{value:g}", source=source
    )


def _ordered_classes(
    variable: str, names: Sequence[str], low: float, top: float, steps: int
) -> Callable[[Callable[..., Values]], None]:
    def check(run: Callable[..., Values]) -> None:
        points = np.linspace(low, top, steps + 1).tolist()
        ranks = [
            names.index(run(**{variable: point}).choice("index_class"))
            for point in points
        ]
        assert ranks == sorted(ranks), "a larger index gave a class below"

    return check


_PCI_FROM = ("uniform_to", "moderate_to", "irregular_to")


def _pci_class(x: Values) -> str:
    value = x.real("pci")
    for limit, name in zip(_PCI_FROM, PCI_CLASSES, strict=False):
        if value <= PCI_CLASS.constant(limit):
            return name
    return PCI_CLASSES[-1]


_PCI_LIMITS_SOURCE = Source(
    citation=_DE_LUIS,
    locator="p. 1260, Oliver's classes: below 10 uniform, 11-15 moderate "
    "concentration, 16-20 irregular, above 20 strong irregularity",
    url=_DE_LUIS_URL,
)

PCI_CLASS: Final = FormulaSpec(
    name="pci_class",
    title="Oliver's class of a precipitation concentration index",
    function="hydrolog.statistics.meteo_precipitation.pci_class",
    family="classification",
    equation="PCI <= 10 uniform, (10, 15] moderate, (15, 20] irregular, above 20 "
    "strongly irregular",
    latex=r"\mathrm{PCI} \le 10,\ (10, 15],\ (15, 20],\ > 20",
    variables=(
        Variable(
            name="pci",
            symbol=r"\mathrm{PCI}",
            unit="-",
            description="A precipitation concentration index.",
            physical=Range(low=100 / 12, high=100.0),
            applicability="unstated",
            typical=Range(
                low=9.4,
                high=27.3,
                source=Source(
                    citation=_WARSZAWA,
                    locator="the yearly PCI of 1991-2020: 9.4 to 27.3",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="index_class",
            unit="-",
            kind="choice",
            description="The class, the most uniform first.",
            choices=PCI_CLASSES,
        ),
    ),
    sources=(_PCI_LIMITS_SOURCE, _OLIVER),
    constants=tuple(
        _class_constant(name, value, _PCI_LIMITS_SOURCE)
        for name, value in zip(_PCI_FROM, (10.0, 15.0, 20.0), strict=True)
    ),
    properties=Properties(
        units="unit_specific",
        limits=(
            Limit(
                name="ordered_classes",
                text="a larger index never gives a more uniform class",
                check=_ordered_classes("pci", PCI_CLASSES, 100 / 12, 100.0, 400),
            ),
        ),
    ),
    validation="none: a classification",
    formula_version=1,
    status="referenced",
    conventions=(
        "the source's classes are of whole numbers (below 10, 11-15, 16-20, above "
        "20); the gaps between them go to the class above: 10 is uniform, 10.5 "
        "moderate, 15 moderate and 15.5 irregular",
    ),
    traps={
        "class_limit": "reference cases pci-class-*: each limit and just beyond it",
        "gap_propagation": "type case pci-nan: NaN is refused; a year without an "
        "index has no class",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
)


def pci_class(pci: float) -> str:
    """Return Oliver's class of a precipitation concentration index, spec pci_class.

    Parameters
    ----------
    pci : float
        The index.

    Returns
    -------
    str
        The class (:data:`PCI_CLASSES`).

    Raises
    ------
    InvalidParameterError
        If the index is refused by the spec.
    """
    x = checked_inputs(PCI_CLASS, pci=pci)
    return checked_outputs(PCI_CLASS, {"index_class": _pci_class(x)}).choice(
        "index_class"
    )


_SI_BELOW = (
    "very_equable_below",
    "equable_wetter_season_below",
    "rather_seasonal_below",
    "seasonal_below",
    "markedly_seasonal_below",
    "most_in_three_months_below",
)
_SI_LIMITS_SOURCE = Source(
    citation=_SUMNER,
    locator="Table II, p. 226, after Walsh and Lawler (1981): <= 0.19 very equable, "
    "0.20-0.39 equable but with a definite wetter season, 0.40-0.59 rather seasonal "
    "with a short drier season, 0.60-0.79 seasonal, 0.80-0.99 markedly seasonal with "
    "a long drier season, 1.00-1.19 most rain in 3 months or less, >= 1.20 extreme",
)


def _si_class(x: Values) -> str:
    value = x.real("si")
    for limit, name in zip(_SI_BELOW, SI_CLASSES, strict=False):
        if value < SI_CLASS.constant(limit):
            return name
    return SI_CLASSES[-1]


SI_CLASS: Final = FormulaSpec(
    name="si_class",
    title="Walsh and Lawler's class of a seasonality index",
    function="hydrolog.statistics.meteo_precipitation.si_class",
    family="classification",
    equation="SI < 0.2 very equable, [0.2, 0.4) equable with a wetter season, [0.4, "
    "0.6) rather seasonal, [0.6, 0.8) seasonal, [0.8, 1.0) markedly seasonal, [1.0, "
    "1.2) most in three months, from 1.2 extreme",
    latex=r"\mathrm{SI} < 0.2,\ [0.2, 0.4),\ [0.4, 0.6),\ [0.6, 0.8),\ [0.8, 1.0),\ "
    r"[1.0, 1.2),\ \ge 1.2",
    variables=(
        Variable(
            name="si",
            symbol=r"\mathrm{SI}",
            unit="-",
            description="A seasonality index.",
            physical=Range(low=0.0, high=11 / 6),
            applicability="unstated",
            typical=Range(
                low=0.31,
                high=0.85,
                source=Source(
                    citation=_WARSZAWA,
                    locator="the yearly SI of 1991-2020: 0.31 to 0.85",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="index_class",
            unit="-",
            kind="choice",
            description="The class, the most equable first.",
            choices=SI_CLASSES,
        ),
    ),
    sources=(_SI_LIMITS_SOURCE, _HYDROTSM),
    constants=tuple(
        _class_constant(name, value, _SI_LIMITS_SOURCE)
        for name, value in zip(_SI_BELOW, (0.2, 0.4, 0.6, 0.8, 1.0, 1.2), strict=True)
    ),
    properties=Properties(
        units="unit_specific",
        limits=(
            Limit(
                name="ordered_classes",
                text="a larger index never gives a more equable class",
                check=_ordered_classes("si", SI_CLASSES, 0.0, 11 / 6, 440),
            ),
        ),
    ),
    validation="none: a classification",
    formula_version=1,
    status="referenced",
    conventions=(
        "the table's classes are of two decimals (<= 0.19, 0.20-0.39 ... >= 1.20); "
        "each class runs up to the next limit: 0.199 is very equable, 0.2 equable "
        "with a wetter season, 1.2 extreme",
    ),
    traps={
        "class_limit": "reference cases si-class-*: each limit and just below it",
        "gap_propagation": "type case si-nan: NaN is refused; a year without an index "
        "has no class",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
)


def si_class(si: float) -> str:
    """Return Walsh and Lawler's class of a seasonality index, spec si_class.

    Parameters
    ----------
    si : float
        The index.

    Returns
    -------
    str
        The class (:data:`SI_CLASSES`).

    Raises
    ------
    InvalidParameterError
        If the index is refused by the spec.
    """
    x = checked_inputs(SI_CLASS, si=si)
    return checked_outputs(SI_CLASS, {"index_class": _si_class(x)}).choice(
        "index_class"
    )


def _unless_refused[T](compute: Callable[[], T]) -> T | None:
    """Return ``compute()``, ``None`` when its spec refuses a precondition."""
    try:
        return compute()
    except InvalidParameterError as refused:
        if refused.details.get("reason") == "precondition_failed":
            return None
        raise


# --- the series on its years ----------------------------------------------------------


def _daily(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    accumulated: NDArray[np.bool_] | Sequence[bool] | None,
    year_type: str,
) -> DailyPrecipitation:
    """Check a daily series and lay all its days on the years of its values."""
    record = precipitation_record(precipitation_mm, dates, accumulated, year_type)
    return record.on_grid()


def _first_at(values: NDArray[np.float64], largest: bool) -> int:
    """Position of the first largest (smallest) finite value."""
    return int(np.nanargmax(values) if largest else np.nanargmin(values))


# --- M1: sums, normals and % of the normal --------------------------------------------


@dataclass
class PrecipitationMonthSum(JsonResultMixin):
    """The precipitation of one month of a year.

    Attributes
    ----------
    month : int
        Calendar month (1 = January).
    total_mm : float or None
        Monthly sum [mm]; ``None`` when a day is missing (WMO-No. 1203, 4.4.1 c).
    percent_of_normal : float or None
        ``total_mm`` in % of the normal of the month (of the reference period).
    """

    month: int
    total_mm: float | None
    percent_of_normal: float | None


@dataclass
class PrecipitationSumYear(JsonResultMixin):
    """The precipitation sums of one year.

    Attributes
    ----------
    year : int
        The year (a hydrological year is named after the year in which it ends).
    total_mm : float or None
        Annual sum [mm]; ``None`` without all twelve monthly sums.
    percent_of_normal : float or None
        ``total_mm`` in % of the annual normal (of the reference period).
    winter_mm, summer_mm : float or None
        Sums of the half-years XI-IV and V-X of the hydrological year that ends in
        ``year`` [mm].
    djf_mm, mam_mm, jja_mm, son_mm : float or None
        Sums of the seasons December (of the year before) to February, March to May,
        June to August and September to November [mm].
    months : list of PrecipitationMonthSum
        The twelve months in the order of the year.
    """

    year: int
    total_mm: float | None
    percent_of_normal: float | None
    winter_mm: float | None
    summer_mm: float | None
    djf_mm: float | None
    mam_mm: float | None
    jja_mm: float | None
    son_mm: float | None
    months: list[PrecipitationMonthSum]


@dataclass
class PrecipitationMonthStatistics(JsonResultMixin):
    """The monthly sums of one calendar month: their normal and the analysed years.

    Attributes
    ----------
    month : int
        Calendar month.
    normal_mm : float or None
        Mean of the monthly sums of the reference period when at least 80 % of its
        years have one [mm].
    n_years : int
        Analysed years with a sum of the month.
    mean_mm, min_mm, max_mm : float or None
        Mean, smallest and largest sum of the month [mm].
    min_year, max_year : int or None
        The first year with the smallest and the largest sum.
    """

    month: int
    normal_mm: float | None
    n_years: int
    mean_mm: float | None
    min_mm: float | None
    min_year: int | None
    max_mm: float | None
    max_year: int | None


@dataclass
class PrecipitationSumPeriod(JsonResultMixin):
    """The normals of the reference period and the annual sums of the analysed years.

    Attributes
    ----------
    normal_mm : float or None
        Annual normal: the sum of the twelve monthly normals, ``None`` when one is
        missing (WMO-No. 1203, 4.3.3) [mm].
    normal_years : int
        The fewest years of the reference period with a sum among the twelve months;
        every monthly normal needs 80 % of its years (WMO-No. 1203, 4.4.2).
    winter_normal_mm, summer_normal_mm : float or None
        Normals of the half-years: the sums of the normals of their months [mm].
    djf_normal_mm, mam_normal_mm, jja_normal_mm, son_normal_mm : float or None
        Normals of the seasons: the sums of the normals of their months [mm].
    mean_mm : float or None
        Mean annual sum of the analysed years with one [mm].
    std_mm : float or None
        Its standard deviation (n - 1) [mm].
    cv : float or None
        Coefficient of variation, ``std_mm / mean_mm``.
    min_mm, max_mm : float or None
        Smallest and largest annual sum [mm].
    min_year, max_year : int or None
        Their (first) years.
    months : list of PrecipitationMonthStatistics
        The twelve months in the order of the year.
    """

    normal_mm: float | None
    normal_years: int
    winter_normal_mm: float | None
    summer_normal_mm: float | None
    djf_normal_mm: float | None
    mam_normal_mm: float | None
    jja_normal_mm: float | None
    son_normal_mm: float | None
    mean_mm: float | None
    std_mm: float | None
    cv: float | None
    min_mm: float | None
    min_year: int | None
    max_mm: float | None
    max_year: int | None
    months: list[PrecipitationMonthStatistics]


@dataclass
class PrecipitationSums(JsonResultMixin):
    """Precipitation sums of the months, half-years, seasons and years (M1).

    Attributes
    ----------
    index : str
        ``"sums"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year : int
        First and last analysed year with a value.
    period_years : int
        Analysed years with a value.
    reference_first_year, reference_last_year : int
        The reference period of the normals, as given or by default the analysed
        years (``first_year`` to ``last_year``).
    reference_period_years : int
        Its years with a value.
    years : list of PrecipitationSumYear
        Every analysed year with a value, in order.
    period : PrecipitationSumPeriod
        Normals and the statistics of the annual sums.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    reference_first_year: int
    reference_last_year: int
    reference_period_years: int
    years: list[PrecipitationSumYear]
    period: PrecipitationSumPeriod


def _percent(value: float, reference: float | None) -> float | None:
    if reference is None or reference == 0 or not math.isfinite(value):
        return None
    return 100.0 * value / reference


_SPAN_MONTHS: dict[str, tuple[int, ...]] = {
    "winter": (11, 12, 1, 2, 3, 4),
    "summer": (5, 6, 7, 8, 9, 10),
    "djf": (12, 1, 2),
    "mam": (3, 4, 5),
    "jja": (6, 7, 8),
    "son": (9, 10, 11),
}
"""The calendar months of the half-years and seasons."""


def _spans(
    grid: DailyGrid, flat: NDArray[np.float64]
) -> dict[str, NDArray[np.float64]]:
    """Sum the half-years and seasons named after each year of the grid [mm]."""

    def span(year: int, month: int, count: int) -> float:
        start = grid.flat_index(year, month)
        if start is None or start + count > flat.size:
            return math.nan
        return float(flat[start : start + count].sum())

    parts = {
        "winter": (-1, 11, 6),
        "summer": (0, 5, 6),
        "djf": (-1, 12, 3),
        "mam": (0, 3, 3),
        "jja": (0, 6, 3),
        "son": (0, 9, 3),
    }
    return {
        name: round_sums(
            np.array([span(int(y) + shift, month, count) for y in grid.years])
        )
        for name, (shift, month, count) in parts.items()
    }


def _sum_tables(
    data: DailyPrecipitation,
) -> tuple[NDArray[np.float64], NDArray[np.float64], dict[str, NDArray[np.float64]]]:
    """Return the monthly, annual, half-year and season sums of the years [mm]."""
    table = data.monthly()
    return table, round_sums(table.sum(axis=1)), _spans(data.grid, table.reshape(-1))


def precipitation_sums(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
    first_year: int | None = None,
    last_year: int | None = None,
    reference_first_year: int | None = None,
    reference_last_year: int | None = None,
) -> PrecipitationSums:
    """Sum the months, half-years, seasons and years and their normals (M1).

    The sums of each analysed year come from its own days, the normals from the
    reference period: the normal of a month is the mean sum of its years with one when
    they are at least 80 % of its years, those without data too (WMO-No. 1203, 4.4.2),
    and the normal of a year, half-year or season the sum of the normals of its months
    (4.3.3). The normals are the benchmark of the sums in % of them (WMO-No. 1203,
    chapter 2).

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing (days may be absent).
    accumulated : array_like of bool, optional
        The values that are accumulated totals of the missing days before them.
    year_type : {"calendar", "hydrological"}, optional
        Calendar years (default) or hydrological years (November - October).
    first_year, last_year : int, optional
        The analysed years (of ``year_type``), by default those of the record.
    reference_first_year, reference_last_year : int, optional
        The reference period of the normals (years of ``year_type``), each by default
        that of the analysed years as resolved; each period keeps the days of its own
        years only.

    Returns
    -------
    PrecipitationSums
        The sums of each analysed year with a value, in % of the normals.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, the dates do not increase, a
        value is negative, no day has a value, ``year_type`` is unknown or a period
        starts after its last year (``details.reason`` ``range``).
    CalculationError
        If a period has no value (``details.reason`` ``no_values_in_period``).
    """
    periods = precipitation_periods(
        precipitation_mm,
        dates,
        accumulated,
        year_type,
        first_year=first_year,
        last_year=last_year,
        reference_first_year=reference_first_year,
        reference_last_year=reference_last_year,
    )
    data = periods.data
    grid = data.grid
    table, annual, spans = _sum_tables(data)
    base_table = table if periods.reference is data else periods.reference.monthly()
    month_normals, normal_years = monthly_normals(base_table, periods.period.n_years)
    by_month = dict(zip(grid.months, month_normals, strict=True))
    normal_mm = multimonth_normal(month_normals)
    span_normals = {
        name: multimonth_normal([by_month[month] for month in members])
        for name, members in _SPAN_MONTHS.items()
    }
    months = grid.months
    rows: list[PrecipitationSumYear] = []
    for row in np.flatnonzero(data.present).tolist():
        rows.append(
            PrecipitationSumYear(
                year=grid.first_year + row,
                total_mm=finite(annual[row]),
                percent_of_normal=_percent(annual[row], normal_mm),
                winter_mm=finite(spans["winter"][row]),
                summer_mm=finite(spans["summer"][row]),
                djf_mm=finite(spans["djf"][row]),
                mam_mm=finite(spans["mam"][row]),
                jja_mm=finite(spans["jja"][row]),
                son_mm=finite(spans["son"][row]),
                months=[
                    PrecipitationMonthSum(
                        month=month,
                        total_mm=finite(table[row, slot]),
                        percent_of_normal=_percent(
                            table[row, slot], month_normals[slot]
                        ),
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    statistics: list[PrecipitationMonthStatistics] = []
    for slot, month in enumerate(months):
        column = table[:, slot]
        have = np.isfinite(column)
        statistics.append(
            PrecipitationMonthStatistics(
                month=month,
                normal_mm=month_normals[slot],
                n_years=int(have.sum()),
                mean_mm=mean_of(column),
                min_mm=finite(column[_first_at(column, False)]) if have.any() else None,
                min_year=grid.first_year + _first_at(column, False)
                if have.any()
                else None,
                max_mm=finite(column[_first_at(column, True)]) if have.any() else None,
                max_year=grid.first_year + _first_at(column, True)
                if have.any()
                else None,
            )
        )
    valid = np.isfinite(annual)
    sums = annual[valid]
    labels = grid.years[valid]
    mean_mm = float(sums.mean()) if sums.size else None
    std_mm = float(sums.std(ddof=1)) if sums.size > 1 else None
    period = PrecipitationSumPeriod(
        normal_mm=normal_mm,
        normal_years=normal_years,
        winter_normal_mm=span_normals["winter"],
        summer_normal_mm=span_normals["summer"],
        djf_normal_mm=span_normals["djf"],
        mam_normal_mm=span_normals["mam"],
        jja_normal_mm=span_normals["jja"],
        son_normal_mm=span_normals["son"],
        mean_mm=mean_mm,
        std_mm=std_mm,
        cv=std_mm / mean_mm if std_mm is not None and mean_mm else None,
        min_mm=float(sums.min()) if sums.size else None,
        min_year=int(labels[int(np.argmin(sums))]) if sums.size else None,
        max_mm=float(sums.max()) if sums.size else None,
        max_year=int(labels[int(np.argmax(sums))]) if sums.size else None,
        months=statistics,
    )
    return PrecipitationSums(
        index="sums",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        reference_first_year=periods.period.first_year,
        reference_last_year=periods.period.last_year,
        reference_period_years=periods.reference_period_years,
        years=rows,
        period=period,
    )


# --- M2: the largest daily and multi-day sums -----------------------------------------


@dataclass
class PrecipitationDuration(JsonResultMixin):
    """The largest sum of n consecutive days of a year.

    Attributes
    ----------
    days : int
        n, the number of consecutive days.
    sum_mm : float or None
        The largest sum of n days whose last day lies in the year [mm]; ``None`` for
        a year with a missing day.
    start_date, end_date : str or None
        Its first and last day (the first such window of the year).
    """

    days: int
    sum_mm: float | None
    start_date: str | None
    end_date: str | None


@dataclass
class PrecipitationMonthMaximum(JsonResultMixin):
    """The largest daily precipitation of one month of a year.

    Attributes
    ----------
    month : int
        Calendar month.
    max_mm : float or None
        The largest daily sum of the days with a value [mm] (WMO-No. 1203, 4.4.1 b).
    date : str or None
        Its (first) day.
    """

    month: int
    max_mm: float | None
    date: str | None


@dataclass
class PrecipitationMaximaYear(JsonResultMixin):
    """The maxima of one year.

    Attributes
    ----------
    year : int
        The year.
    complete : bool
        Every day of the year has a daily value; the annual maxima need it.
    durations : list of PrecipitationDuration
        The largest sums of 1 day and of each of ``durations_days``.
    months : list of PrecipitationMonthMaximum
        The largest daily sum of each month, in the order of the year.
    """

    year: int
    complete: bool
    durations: list[PrecipitationDuration]
    months: list[PrecipitationMonthMaximum]


@dataclass
class PrecipitationDurationSummary(JsonResultMixin):
    """The annual maxima of one duration over the complete years.

    Attributes
    ----------
    days : int
        The duration [days].
    n_years : int
        Complete years.
    mean_mm, median_mm, min_mm, max_mm : float or None
        Statistics of the annual maxima [mm].
    max_start_date, max_end_date : str or None
        First and last day of the largest one.
    """

    days: int
    n_years: int
    mean_mm: float | None
    median_mm: float | None
    min_mm: float | None
    max_mm: float | None
    max_start_date: str | None
    max_end_date: str | None


@dataclass
class PrecipitationMonthMaximumSummary(JsonResultMixin):
    """The monthly maxima of one calendar month over the period.

    Attributes
    ----------
    month : int
        Calendar month.
    max_mm : float or None
        The largest daily precipitation of the month in the period [mm].
    date : str or None
        Its (first) day.
    mean_max_mm : float or None
        Mean of the monthly maxima of the months with enough days (WMO-No. 1203,
        4.4.2) [mm].
    n_months : int
        Those months.
    annual_maxima : int
        Complete years whose largest daily sum fell in this month.
    """

    month: int
    max_mm: float | None
    date: str | None
    mean_max_mm: float | None
    n_months: int
    annual_maxima: int


@dataclass
class PrecipitationMaximaPeriod(JsonResultMixin):
    """The maxima over the period.

    Attributes
    ----------
    n_years : int
        Complete years.
    incomplete_years : list of int
        Years with a value but a missing day: no annual maxima.
    durations : list of PrecipitationDurationSummary
        One per duration, 1 day first.
    months : list of PrecipitationMonthMaximumSummary
        The twelve months in the order of the year.
    """

    n_years: int
    incomplete_years: list[int]
    durations: list[PrecipitationDurationSummary]
    months: list[PrecipitationMonthMaximumSummary]


@dataclass
class PrecipitationMaxima(JsonResultMixin):
    """The largest daily and multi-day precipitation of each year and month (M2).

    Attributes
    ----------
    index : str
        ``"maxima"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period: first and last year with a value, years with a value.
    durations_days : list of int
        The durations of ``years[].durations``: 1 and the durations asked for.
    years : list of PrecipitationMaximaYear
        Every year with a value.
    period : PrecipitationMaximaPeriod
        The maxima over the complete years.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    durations_days: list[int]
    years: list[PrecipitationMaximaYear]
    period: PrecipitationMaximaPeriod


def _durations(durations_days: Sequence[int]) -> list[int]:
    chosen: set[int] = {1}
    for item in durations_days:
        if isinstance(item, bool) or int(item) != item or item < 1:
            raise InvalidParameterError(
                f"durations_days must be whole numbers of at least 1, got {item!r}"
            )
        chosen.add(int(item))
    return sorted(chosen)


def precipitation_maxima(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    durations_days: Sequence[int] = DEFAULT_DURATIONS_DAYS,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> PrecipitationMaxima:
    """Find the largest daily and n-day precipitation of each year and month (M2).

    The n-day sum of a day is the sum of the n days that end on it; it belongs to the
    year of its last day and needs all n days. An annual maximum needs every day of
    the year; a monthly maximum takes whatever days the month has.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    durations_days : sequence of int, optional
        Durations of the multi-day sums [days], each at least 1, by default 2, 3, 5
        and 10; the 1-day maximum is always given.
    accumulated : array_like of bool, optional
        Accumulated totals: missing days for the maxima.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    PrecipitationMaxima
        The maxima of each year and month and their summary over the period.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid (see :func:`precipitation_sums`) or a duration is
        not a whole number of at least 1.
    """
    durations = _durations(durations_days)
    data = _daily(precipitation_mm, dates, accumulated, year_type)
    grid = data.grid
    known = np.isfinite(data.daily)
    complete = complete_years(grid, known)
    starts = grid.year_starts()
    found = {
        days: block_extreme(rolling_sum(data.daily, days), starts) for days in durations
    }
    month_best, month_at = block_extreme(data.daily, grid.month_starts())
    month_best = month_best.reshape(grid.n_years, 12)
    month_at = month_at.reshape(grid.n_years, 12)
    enough = month_quality(grid, known).enough
    months = grid.months

    def duration(days: int, row: int) -> PrecipitationDuration:
        best, end = found[days]
        if not complete[row] or not math.isfinite(best[row]):
            return PrecipitationDuration(days, None, None, None)
        last = int(end[row])
        return PrecipitationDuration(
            days, float(best[row]), grid.iso(last - days + 1), grid.iso(last)
        )

    rows: list[PrecipitationMaximaYear] = []
    for row in np.flatnonzero(data.present).tolist():
        rows.append(
            PrecipitationMaximaYear(
                year=grid.first_year + row,
                complete=bool(complete[row]),
                durations=[duration(days, row) for days in durations],
                months=[
                    PrecipitationMonthMaximum(
                        month,
                        finite(month_best[row, slot]),
                        grid.iso(int(month_at[row, slot])),
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    chosen = data.present & complete
    summaries: list[PrecipitationDurationSummary] = []
    for days in durations:
        best, end = found[days]
        use = chosen & np.isfinite(best)
        values = best[use]
        if values.size == 0:
            summaries.append(
                PrecipitationDurationSummary(
                    days, 0, None, None, None, None, None, None
                )
            )
            continue
        top = int(end[use][int(np.argmax(values))])
        summaries.append(
            PrecipitationDurationSummary(
                days=days,
                n_years=int(values.size),
                mean_mm=float(values.mean()),
                median_mm=float(np.median(values)),
                min_mm=float(values.min()),
                max_mm=float(values.max()),
                max_start_date=grid.iso(top - days + 1),
                max_end_date=grid.iso(top),
            )
        )
    one_day_best, one_day_end = found[1]
    annual_month = grid.month[one_day_end[chosen & np.isfinite(one_day_best)]]
    month_summaries: list[PrecipitationMonthMaximumSummary] = []
    for slot, month in enumerate(months):
        column = month_best[:, slot]
        usable = column[enough[:, slot] & np.isfinite(column)]
        if np.isfinite(column).any():
            at = _first_at(column, True)
            top_mm: float | None = float(column[at])
            top_date = grid.iso(int(month_at[at, slot]))
        else:
            top_mm, top_date = None, None
        month_summaries.append(
            PrecipitationMonthMaximumSummary(
                month=month,
                max_mm=top_mm,
                date=top_date,
                mean_max_mm=float(usable.mean()) if usable.size else None,
                n_months=int(usable.size),
                annual_maxima=int((annual_month == month).sum()),
            )
        )
    return PrecipitationMaxima(
        index="maxima",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        durations_days=durations,
        years=rows,
        period=PrecipitationMaximaPeriod(
            n_years=int(chosen.sum()),
            incomplete_years=[
                int(year) for year in grid.years[data.present & ~complete]
            ],
            durations=summaries,
            months=month_summaries,
        ),
    )


# --- M5: days with precipitation ------------------------------------------------------


@dataclass
class PrecipitationDaysMonth(JsonResultMixin):
    """Days with precipitation of one month.

    Attributes
    ----------
    month : int
        Calendar month.
    days : list of float or None
        Days with P at or above each of ``thresholds_mm``, scaled to the days of the
        month when some are missing; ``None`` without enough days (WMO-No. 1203,
        4.4.1 d). In ``period.months`` the mean over the years.
    """

    month: int
    days: list[float | None]


@dataclass
class PrecipitationDaysYear(JsonResultMixin):
    """Days with precipitation of one year.

    Attributes
    ----------
    year : int
        The year.
    days : list of float or None
        Days with P at or above each of ``thresholds_mm``: the sum of the twelve
        monthly counts; ``None`` without all of them.
    months : list of PrecipitationDaysMonth
        The twelve months in the order of the year.
    """

    year: int
    days: list[float | None]
    months: list[PrecipitationDaysMonth]


@dataclass
class PrecipitationDaysPeriod(JsonResultMixin):
    """Mean days with precipitation over the period.

    Attributes
    ----------
    n_years : int
        Years with annual counts.
    days : list of float or None
        Mean annual days at or above each threshold.
    months : list of PrecipitationDaysMonth
        Mean monthly days, in the order of the year.
    """

    n_years: int
    days: list[float | None]
    months: list[PrecipitationDaysMonth]


@dataclass
class PrecipitationDays(JsonResultMixin):
    """Days with precipitation at or above thresholds (M5).

    Attributes
    ----------
    index : str
        ``"days"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period.
    thresholds_mm : list of float
        The thresholds [mm] of every ``days`` list.
    years : list of PrecipitationDaysYear
        Every year with a value.
    period : PrecipitationDaysPeriod
        The means of the period.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    thresholds_mm: list[float]
    years: list[PrecipitationDaysYear]
    period: PrecipitationDaysPeriod


def _positive_list(option: str, values: Sequence[float]) -> list[float]:
    chosen = [float(item) for item in values]
    if not chosen or not all(math.isfinite(item) and item > 0 for item in chosen):
        raise InvalidParameterError(
            f"{option} must be a non-empty list of positive numbers, got {values!r}"
        )
    return chosen


def precipitation_days(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    thresholds_mm: Sequence[float] = DEFAULT_THRESHOLDS_MM,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> PrecipitationDays:
    """Days with precipitation at or above each threshold, per month and year (M5).

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    thresholds_mm : sequence of float, optional
        Thresholds [mm], each positive, by default 0.1, 1, 10 and 20 (R10mm and
        R20mm of the ETCCDI for 10 and 20).
    accumulated : array_like of bool, optional
        Accumulated totals: missing days for the counts.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    PrecipitationDays
        The days of each month and year and their means.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid or a threshold is not a positive number.
    """
    thresholds = _positive_list("thresholds_mm", thresholds_mm)
    data = _daily(precipitation_mm, dates, accumulated, year_type)
    grid = data.grid
    with np.errstate(invalid="ignore"):
        tables = [
            monthly_counts(grid, data.daily, data.daily >= threshold)
            for threshold in thresholds
        ]
    annual = [table.sum(axis=1) for table in tables]
    months = grid.months
    rows: list[PrecipitationDaysYear] = []
    for row in np.flatnonzero(data.present).tolist():
        rows.append(
            PrecipitationDaysYear(
                year=grid.first_year + row,
                days=[finite(values[row]) for values in annual],
                months=[
                    PrecipitationDaysMonth(
                        month, [finite(table[row, slot]) for table in tables]
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    valid = np.isfinite(annual[0])
    return PrecipitationDays(
        index="days",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        thresholds_mm=thresholds,
        years=rows,
        period=PrecipitationDaysPeriod(
            n_years=int(valid.sum()),
            days=[mean_of(values[valid]) for values in annual],
            months=[
                PrecipitationDaysMonth(
                    month, [mean_of(table[:, slot]) for table in tables]
                )
                for slot, month in enumerate(months)
            ],
        ),
    )


# --- M4: mean annual sum and intensity of a wet day -----------------------------------


@dataclass
class PrecipitationIntensityMonth(JsonResultMixin):
    """Wet days of one month.

    Attributes
    ----------
    month : int
        Calendar month.
    wet_days : int or None
        Days with P >= ``wet_day_mm``; ``None`` when a day of the month is missing.
    wet_day_total_mm : float or None
        Their precipitation [mm].
    sdii_mm : float or None
        Mean precipitation of a wet day [mm]; in ``period.months`` pooled over the
        complete months of the period.
    """

    month: int
    wet_days: int | None
    wet_day_total_mm: float | None
    sdii_mm: float | None


@dataclass
class PrecipitationIntensityYear(JsonResultMixin):
    """The annual sum and the intensity of the wet days of one year.

    Attributes
    ----------
    year : int
        The year.
    total_mm : float or None
        Annual sum [mm] (as ``years[].total_mm`` of ``sums``).
    wet_days : int or None
        Wet days; ``None`` unless every month is complete.
    wet_day_total_mm : float or None
        Precipitation of the wet days, PRCPTOT of the ETCCDI [mm].
    sdii_mm : float or None
        Simple daily intensity index SDII: ``wet_day_total_mm / wet_days`` [mm].
    months : list of PrecipitationIntensityMonth
        The twelve months in the order of the year.
    """

    year: int
    total_mm: float | None
    wet_days: int | None
    wet_day_total_mm: float | None
    sdii_mm: float | None
    months: list[PrecipitationIntensityMonth]


@dataclass
class PrecipitationIntensityPeriod(JsonResultMixin):
    """Mean annual sum and mean intensity over the period.

    Attributes
    ----------
    mean_total_mm : float or None
        Mean annual sum of the years with one [mm].
    n_years : int
        Those years.
    mean_sdii_mm : float or None
        Mean of the annual SDII [mm].
    sdii_years : int
        Years with an SDII.
    months : list of PrecipitationIntensityMonth
        Wet days of each month pooled over its complete months (``wet_days`` and
        ``wet_day_total_mm`` are their sums), in the order of the year.
    """

    mean_total_mm: float | None
    n_years: int
    mean_sdii_mm: float | None
    sdii_years: int
    months: list[PrecipitationIntensityMonth]


@dataclass
class PrecipitationIntensity(JsonResultMixin):
    """The mean annual sum and the precipitation intensity of a wet day (M4).

    Attributes
    ----------
    index : str
        ``"intensity"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period.
    wet_day_mm : float
        A wet day has at least this precipitation [mm].
    years : list of PrecipitationIntensityYear
        Every year with a value.
    period : PrecipitationIntensityPeriod
        The means of the period.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    wet_day_mm: float
    years: list[PrecipitationIntensityYear]
    period: PrecipitationIntensityPeriod


def _intensity_of(
    values: NDArray[np.float64], wet_day_mm: float
) -> tuple[int, float, float | None]:
    """Return W, PRCPTOT rounded and SDII of known days; W = 0 has no SDII."""
    found = _unless_refused(lambda: wet_day_intensity(values, wet_day_mm))
    if found is None:
        return 0, 0.0, None
    return found.wet_days, round_sum(found.wet_day_total_mm), found.sdii_mm


def _stops(starts: NDArray[np.intp], size: int) -> NDArray[np.intp]:
    """Return where each span of a grid that starts at ``starts`` stops."""
    return np.append(starts[1:], size)


def precipitation_intensity(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    wet_day_mm: float = DEFAULT_WET_DAY_MM,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> PrecipitationIntensity:
    """Compute the mean annual sum and the mean precipitation of a wet day (M4).

    SDII = the precipitation of the wet days (P >= ``wet_day_mm``) of a year over
    their number (ETCCDI, Zhang et al., 2011); a year needs every day of every month.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    wet_day_mm : float, optional
        A wet day has at least this precipitation [mm], by default 1.
    accumulated : array_like of bool, optional
        Accumulated totals: they count in the annual sums, not in the wet days.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    PrecipitationIntensity
        The annual sums and the intensity of each year and month.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid or ``wet_day_mm`` is not positive.
    """
    data = _daily(precipitation_mm, dates, accumulated, year_type)
    grid = data.grid
    daily = data.daily
    known = np.isfinite(daily)
    full_month = month_quality(grid, known).complete
    full_year = complete_years(grid, known)
    month_start = grid.month_starts()
    month_stop = _stops(month_start, daily.size)
    year_start = grid.year_starts()
    year_stop = _stops(year_start, daily.size)
    annual = round_sums(data.monthly().sum(axis=1))
    months = grid.months

    def month_of(row: int, slot: int) -> PrecipitationIntensityMonth:
        flat = row * 12 + slot
        if not full_month[row, slot]:
            return PrecipitationIntensityMonth(months[slot], None, None, None)
        span = daily[month_start[flat] : month_stop[flat]]
        return PrecipitationIntensityMonth(
            months[slot], *_intensity_of(span, wet_day_mm)
        )

    rows: list[PrecipitationIntensityYear] = []
    year_sdii: list[float] = []
    for row in np.flatnonzero(data.present).tolist():
        found = _intensity_of(daily[year_start[row] : year_stop[row]], wet_day_mm)
        wet_days, total, sdii = found if full_year[row] else (None, None, None)
        if sdii is not None:
            year_sdii.append(sdii)
        rows.append(
            PrecipitationIntensityYear(
                year=grid.first_year + row,
                total_mm=finite(annual[row]),
                wet_days=wet_days,
                wet_day_total_mm=total,
                sdii_mm=sdii,
                months=[month_of(row, slot) for slot in range(12)],
            )
        )
    pooled: list[PrecipitationIntensityMonth] = []
    for slot, month in enumerate(months):
        spans = [
            daily[month_start[flat] : month_stop[flat]]
            for flat in range(slot, 12 * grid.n_years, 12)
            if full_month[flat // 12, slot]
        ]
        pooled.append(
            PrecipitationIntensityMonth(
                month, *_intensity_of(np.concatenate(spans), wet_day_mm)
            )
            if spans
            else PrecipitationIntensityMonth(month, None, None, None)
        )
    have_total = np.isfinite(annual)
    return PrecipitationIntensity(
        index="intensity",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        wet_day_mm=float(wet_day_mm),
        years=rows,
        period=PrecipitationIntensityPeriod(
            mean_total_mm=mean_of(annual),
            n_years=int(have_total.sum()),
            mean_sdii_mm=float(np.mean(year_sdii)) if year_sdii else None,
            sdii_years=len(year_sdii),
            months=pooled,
        ),
    )


# --- M7: heavy precipitation ----------------------------------------------------------


@dataclass
class HeavyPrecipitationYear(JsonResultMixin):
    """Heavy precipitation of one year.

    Attributes
    ----------
    year : int
        The year.
    complete : bool
        Every day of the year has a daily value; the sums need it.
    wet_day_total_mm : float or None
        Precipitation of the wet days, PRCPTOT [mm].
    sums_mm : list of float or None
        For each percentile: the precipitation of the days with P above its
        threshold (R95p, R99p) [mm].
    shares_percent : list of float or None
        Those sums in % of ``wet_day_total_mm`` (R95pTOT, R99pTOT).
    days : list of int or None
        The days above each threshold.
    """

    year: int
    complete: bool
    wet_day_total_mm: float | None
    sums_mm: list[float | None]
    shares_percent: list[float | None]
    days: list[int | None]


@dataclass
class HeavyPrecipitationPeriod(JsonResultMixin):
    """The thresholds of the reference period and the mean shares of the analysed years.

    Attributes
    ----------
    wet_days : int
        Wet days of the reference period the percentiles are taken of.
    thresholds_mm : list of float
        The percentiles of their precipitation [mm] (quantile type 8, Hyndman and
        Fan, 1996).
    n_years : int
        Complete analysed years.
    mean_shares_percent : list of float or None
        Mean annual share of each percentile [%].
    """

    wet_days: int
    thresholds_mm: list[float]
    n_years: int
    mean_shares_percent: list[float | None]


@dataclass
class HeavyPrecipitation(JsonResultMixin):
    """Precipitation on the days above percentiles of the wet days (M7).

    Attributes
    ----------
    index : str
        ``"heavy"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The analysed years: first and last year with a value, years with a value.
    reference_first_year, reference_last_year : int
        The reference period of the thresholds, as given or by default the analysed
        years.
    reference_period_years : int
        Its years with a value.
    wet_day_mm : float
        A wet day has at least this precipitation [mm].
    percentiles : list of float
        The percentiles of the wet days [%].
    years : list of HeavyPrecipitationYear
        Every analysed year with a value.
    period : HeavyPrecipitationPeriod
        The thresholds and the mean shares.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    reference_first_year: int
    reference_last_year: int
    reference_period_years: int
    wet_day_mm: float
    percentiles: list[float]
    years: list[HeavyPrecipitationYear]
    period: HeavyPrecipitationPeriod


def heavy_precipitation(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    wet_day_mm: float = DEFAULT_WET_DAY_MM,
    percentiles: Sequence[float] = DEFAULT_PERCENTILES,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
    first_year: int | None = None,
    last_year: int | None = None,
    reference_first_year: int | None = None,
    reference_last_year: int | None = None,
) -> HeavyPrecipitation:
    """Sum the days above percentiles of the wet days and give their shares (M7).

    The thresholds are percentiles of the precipitation of the wet days (P >=
    ``wet_day_mm``) of the reference period, quantile type 8 (Hyndman and Fan, 1996,
    as climdex.pcic of the ETCCDI), from at least 100 wet days; a year sums the
    precipitation of its days above each threshold (R95p, R99p) and gives it in % of
    the precipitation of its wet days (R95pTOT, R99pTOT; Zhang et al., 2011). A year
    needs every day. The ETCCDI takes the percentiles of a base period, 1961-1990
    (Klein Tank et al., 2009; Zhang et al., 2011), and a period longer than 30 years
    gives steadier percentiles (WMO-No. 1203, 5.2.2); the bootstrap of the years
    inside the base period (Zhang et al., 2005) is one of the temperature indices,
    not of R95pTOT.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    wet_day_mm : float, optional
        A wet day has at least this precipitation [mm], by default 1.
    percentiles : sequence of float, optional
        Percentiles in (0, 100), by default 95 and 99.
    accumulated : array_like of bool, optional
        Accumulated totals: missing days.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.
    first_year, last_year : int, optional
        The analysed years (of ``year_type``), by default those of the record.
    reference_first_year, reference_last_year : int, optional
        The reference period of the thresholds, each by default that of the analysed
        years as resolved; each period keeps the days of its own years only.

    Returns
    -------
    HeavyPrecipitation
        The thresholds and the heavy precipitation of each year.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid, ``wet_day_mm`` is not positive, a percentile is
        outside (0, 100) or a period starts after its last year (``range``).
    CalculationError
        If a period has no value (``details.reason`` ``no_values_in_period``) or the
        reference period has fewer than 100 wet days (``too_few_wet_days``).
    """
    levels = list(percentiles)
    if not levels:
        raise InvalidParameterError(
            f"percentiles must be numbers in (0, 100), got {percentiles!r}"
        )
    periods = precipitation_periods(
        precipitation_mm,
        dates,
        accumulated,
        year_type,
        first_year=first_year,
        last_year=last_year,
        reference_first_year=reference_first_year,
        reference_last_year=reference_last_year,
    )
    data = periods.data
    grid = data.grid
    base = periods.reference.daily

    def threshold_of(level: float) -> float | None:
        return _unless_refused(lambda: wet_day_percentile(base, wet_day_mm, level))

    found = [threshold_of(level) for level in levels]
    with np.errstate(invalid="ignore"):
        wet_days = int(np.count_nonzero(base >= float(wet_day_mm)))
    if wet_days < MIN_WET_DAYS:
        raise CalculationError(
            f"The percentiles need at least {MIN_WET_DAYS} wet days (P >= "
            f"{float(wet_day_mm):g} mm) in the reference period "
            f"{periods.period.first_year}-{periods.period.last_year}, got {wet_days}",
            details={
                "reason": "too_few_wet_days",
                "count": wet_days,
                "minimum": MIN_WET_DAYS,
            },
            hint="Choose a longer reference period (by default the analysed years).",
        )
    limits = [limit for limit in found if limit is not None]

    def share_of(
        values: NDArray[np.float64], limit: float
    ) -> HeavyPrecipitationShare | None:
        return _unless_refused(
            lambda: heavy_precipitation_share(values, wet_day_mm, limit)
        )

    complete = complete_years(grid, np.isfinite(data.daily))
    starts = grid.year_starts()
    stops = _stops(starts, data.daily.size)
    rows: list[HeavyPrecipitationYear] = []
    shares: list[list[float]] = [[] for _ in levels]
    for row in np.flatnonzero(data.present).tolist():
        if not complete[row]:
            rows.append(
                HeavyPrecipitationYear(
                    grid.first_year + row,
                    False,
                    None,
                    [None] * len(levels),
                    [None] * len(levels),
                    [None] * len(levels),
                )
            )
            continue
        values = data.daily[starts[row] : stops[row]]
        heavy = [share_of(values, limit) for limit in limits]
        year_shares = [None if item is None else item.share_percent for item in heavy]
        for number, share in enumerate(year_shares):
            if share is not None:
                shares[number].append(share)
        first = heavy[0]
        rows.append(
            HeavyPrecipitationYear(
                year=grid.first_year + row,
                complete=True,
                wet_day_total_mm=0.0
                if first is None
                else round_sum(first.wet_day_total_mm),
                sums_mm=[
                    0.0 if item is None else round_sum(item.heavy_mm) for item in heavy
                ],
                shares_percent=year_shares,
                days=[0 if item is None else item.heavy_days for item in heavy],
            )
        )
    return HeavyPrecipitation(
        index="heavy",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        reference_first_year=periods.period.first_year,
        reference_last_year=periods.period.last_year,
        reference_period_years=periods.reference_period_years,
        wet_day_mm=float(wet_day_mm),
        percentiles=[float(level) for level in levels],
        years=rows,
        period=HeavyPrecipitationPeriod(
            wet_days=wet_days,
            thresholds_mm=limits,
            n_years=int((data.present & complete).sum()),
            mean_shares_percent=[
                float(np.mean(values)) if values else None for values in shares
            ],
        ),
    )


# --- M9: regime and seasonality -------------------------------------------------------


def _pci_of(monthly: NDArray[np.float64] | Sequence[float]) -> float | None:
    """Return the PCI of twelve monthly sums, ``None`` for a total of 0."""
    return _unless_refused(lambda: precipitation_concentration_index(monthly))


def _si_of(monthly: NDArray[np.float64] | Sequence[float]) -> float | None:
    """Return the SI of twelve monthly sums, ``None`` for a total of 0."""
    return _unless_refused(lambda: seasonality_index(monthly))


def _pci_class_of(value: float | None) -> str | None:
    return None if value is None else pci_class(value)


def _si_class_of(value: float | None) -> str | None:
    return None if value is None else si_class(value)


@dataclass
class PrecipitationRegimeMonth(JsonResultMixin):
    """One month of the regime of the normals.

    Attributes
    ----------
    month : int
        Calendar month.
    normal_mm : float or None
        Normal of the month (of the reference period) [mm].
    share_percent : float or None
        Its share in the sum of the twelve normals [%].
    coefficient : float or None
        The normal over the mean of the twelve normals.
    """

    month: int
    normal_mm: float | None
    share_percent: float | None
    coefficient: float | None


@dataclass
class PrecipitationSeasonalityYear(JsonResultMixin):
    """Concentration and seasonality of the monthly sums of one year.

    Attributes
    ----------
    year : int
        The year.
    pci : float or None
        Precipitation concentration index (Oliver, 1980).
    pci_class : str or None
        Its class (:data:`PCI_CLASSES`).
    si : float or None
        Seasonality index (Walsh and Lawler, 1981).
    si_class : str or None
        Its class (:data:`SI_CLASSES`).
    """

    year: int
    pci: float | None
    pci_class: str | None
    si: float | None
    si_class: str | None


@dataclass
class PrecipitationSeasonalityPeriod(JsonResultMixin):
    """The regime of the normals and the mean indices of the analysed years.

    Attributes
    ----------
    months : list of PrecipitationRegimeMonth
        The twelve months in the order of the year.
    pci, si : float or None
        The indices of the twelve monthly normals of the reference period.
    pci_class, si_class : str or None
        Their classes.
    mean_pci, mean_si : float or None
        The means of the indices of the analysed years.
    mean_pci_class, mean_si_class : str or None
        Their classes.
    n_years : int
        Analysed years with all twelve monthly sums.
    """

    months: list[PrecipitationRegimeMonth]
    pci: float | None
    pci_class: str | None
    si: float | None
    si_class: str | None
    mean_pci: float | None
    mean_pci_class: str | None
    mean_si: float | None
    mean_si_class: str | None
    n_years: int


@dataclass
class PrecipitationSeasonality(JsonResultMixin):
    """The monthly regime, the concentration and the seasonality of precipitation (M9).

    Attributes
    ----------
    index : str
        ``"seasonality"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The analysed years: first and last year with a value, years with a value.
    reference_first_year, reference_last_year : int
        The reference period of the regime, as given or by default the analysed
        years.
    reference_period_years : int
        Its years with a value.
    years : list of PrecipitationSeasonalityYear
        Every analysed year with a value.
    period : PrecipitationSeasonalityPeriod
        The regime of the normals and the mean indices.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    reference_first_year: int
    reference_last_year: int
    reference_period_years: int
    years: list[PrecipitationSeasonalityYear]
    period: PrecipitationSeasonalityPeriod


def precipitation_seasonality(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
    first_year: int | None = None,
    last_year: int | None = None,
    reference_first_year: int | None = None,
    reference_last_year: int | None = None,
) -> PrecipitationSeasonality:
    """Compute the monthly regime, PCI and SI of the normals and of each year (M9).

    The regime, PCI and SI of the period are those of the twelve monthly normals of
    the reference period; the indices of each analysed year those of its own sums.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    accumulated : array_like of bool, optional
        Accumulated totals of the missing days before them.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.
    first_year, last_year : int, optional
        The analysed years (of ``year_type``), by default those of the record.
    reference_first_year, reference_last_year : int, optional
        The reference period of the normals, each by default that of the analysed
        years as resolved; each period keeps the days of its own years only.

    Returns
    -------
    PrecipitationSeasonality
        The regime of the normals and the indices of each year.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid or a period starts after its last year
        (``details.reason`` ``range``).
    CalculationError
        If a period has no value (``details.reason`` ``no_values_in_period``).
    """
    periods = precipitation_periods(
        precipitation_mm,
        dates,
        accumulated,
        year_type,
        first_year=first_year,
        last_year=last_year,
        reference_first_year=reference_first_year,
        reference_last_year=reference_last_year,
    )
    data = periods.data
    grid = data.grid
    table = data.monthly()
    base = table if periods.reference is data else periods.reference.monthly()
    normals = [normal(base[:, slot], periods.period.n_years)[0] for slot in range(12)]
    months = grid.months
    regime: list[PrecipitationRegimeMonth]
    if all(value is not None for value in normals):
        values = [float(value) for value in normals if value is not None]
        total = sum(values)
        regime = [
            PrecipitationRegimeMonth(
                month,
                value,
                100.0 * value / total if total > 0 else None,
                value / (total / 12.0) if total > 0 else None,
            )
            for month, value in zip(months, values, strict=True)
        ]
        pci = _pci_of(values)
        si = _si_of(values)
    else:
        regime = [
            PrecipitationRegimeMonth(month, value, None, None)
            for month, value in zip(months, normals, strict=True)
        ]
        pci = si = None
    rows: list[PrecipitationSeasonalityYear] = []
    year_pci: list[float] = []
    year_si: list[float] = []
    for row in np.flatnonzero(data.present).tolist():
        year_values = table[row]
        complete = bool(np.isfinite(year_values).all())
        value_pci = _pci_of(year_values) if complete else None
        value_si = _si_of(year_values) if complete else None
        if value_pci is not None:
            year_pci.append(value_pci)
        if value_si is not None:
            year_si.append(value_si)
        rows.append(
            PrecipitationSeasonalityYear(
                grid.first_year + row,
                value_pci,
                _pci_class_of(value_pci),
                value_si,
                _si_class_of(value_si),
            )
        )
    mean_pci = float(np.mean(year_pci)) if year_pci else None
    mean_si = float(np.mean(year_si)) if year_si else None
    return PrecipitationSeasonality(
        index="seasonality",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        reference_first_year=periods.period.first_year,
        reference_last_year=periods.period.last_year,
        reference_period_years=periods.reference_period_years,
        years=rows,
        period=PrecipitationSeasonalityPeriod(
            months=regime,
            pci=pci,
            pci_class=_pci_class_of(pci),
            si=si,
            si_class=_si_class_of(si),
            mean_pci=mean_pci,
            mean_pci_class=_pci_class_of(mean_pci),
            mean_si=mean_si,
            mean_si_class=_si_class_of(mean_si),
            n_years=len(year_pci),
        ),
    )


SPECS: Final = (SDII, WET_DAY_PERCENTILE, HEAVY_SHARE, PCI, PCI_CLASS, SI_CLASS)
"""The Tier A formulas of the module."""

_WMO_1203 = (
    "WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, "
    "Geneva"
)
_WMO_1203_URL = "https://library.wmo.int/idurl/4/55797"

TIER_B: Final = (
    TierBSpec(
        name="precipitation_sums",
        function="hydrolog.statistics.meteo_precipitation.precipitation_sums",
        definition="the sum of the daily precipitation of a month, needing every day "
        "or accumulated totals that cover the missing days; of a half-year (XI-IV, "
        "V-X), a season (DJF with the December before, MAM, JJA, SON) and a year, the "
        "sum of its months, needing each; a sum in % of its normal, 100 P / N",
        convention="every sum of daily precipitation rounded to 1e-6 mm (round_sums); "
        "no percentage without a normal or with a normal of 0",
        source=Source(
            citation=_WMO_1203,
            locator="section 4.3.1 (c) and 4.4.1 (c), pp. 5-8: a sum needs complete "
            "data or accumulated observations covering the missing days",
            url=_WMO_1203_URL,
        ),
    ),
    TierBSpec(
        name="precipitation_normals",
        function="hydrolog.statistics.meteo_precipitation.precipitation_sums",
        definition="the normal of a calendar month: the mean of its sums in the years "
        "of the reference period that have one, when they are at least 80 % of its "
        "years; of a half-year, a season or the year: the sum of the normals of its "
        "months",
        convention="the reference period is by default the analysed years; its years "
        "without data count among its years",
        source=Source(
            citation=_WMO_1203,
            locator="section 4.4.2, pp. 8-9: values in at least 80 % of the years; "
            "section 4.3.3, p. 6: the normal of several months from the monthly "
            "normals",
            url=_WMO_1203_URL,
        ),
        constants=(
            Constant(
                name="normal_share",
                value=Fraction(4, 5),
                unit="-",
                symbol="80 %",
                source=Source(
                    citation=_WMO_1203, locator="section 4.4.2", url=_WMO_1203_URL
                ),
            ),
        ),
    ),
    TierBSpec(
        name="precipitation_maxima",
        function="hydrolog.statistics.meteo_precipitation.precipitation_maxima",
        definition="Rx1day and the largest n-day sums (Rx5day for 5): the n-day sum of "
        "a day is the sum of the n days ending on it, credited to the year of its last "
        "day and missing unless all n are known; a month's maximum takes the days it "
        "has, a year's needs every day of the year",
        convention="the first of equal maxima, with its dates; climdex.pcic 1.1-11 "
        "credits a 5-day window to its middle day and takes a missing day as 0",
        source=Source(
            citation=_ETCCDI,
            locator="Rx1day, the largest daily precipitation of a period; Rx5day, the "
            "largest precipitation of 5 consecutive days (the interval ending on a "
            "day)",
            url=_ETCCDI_URL,
        ),
    ),
    TierBSpec(
        name="precipitation_days",
        function="hydrolog.statistics.meteo_precipitation.precipitation_days",
        definition="the days with P at or above each threshold (R10mm and R20mm for 10 "
        "and 20 mm); a month's count scaled to its days when fewer than 11 days, and "
        "fewer than 5 in a row, are missing; a year's the sum of its twelve months",
        convention="P >= threshold; with gaps a month's count is not a whole number "
        "(climdex.pcic counts the days it has)",
        source=Source(
            citation=_ETCCDI,
            locator="R10mm and R20mm: the annual count of days with RR >= 10 mm and "
            ">= 20 mm",
            url=_ETCCDI_URL,
        ),
    ),
    TierBSpec(
        name="precipitation_intensity",
        function="hydrolog.statistics.meteo_precipitation.precipitation_intensity",
        definition="sdii of each month and year with every day, and of each calendar "
        "month over those months of the period together; the mean annual sum and the "
        "mean SDII of the years with one",
        convention="an accumulated total is a missing day for sdii and counts in the "
        "annual sum; PRCPTOT rounded to 1e-6 mm; a month or year without a wet day "
        "has W = 0 and no SDII",
        source=_ETCCDI_WET,
    ),
    TierBSpec(
        name="heavy_precipitation_thresholds",
        function="hydrolog.statistics.meteo_precipitation.heavy_precipitation",
        definition="the thresholds: wet_day_percentile of the wet days of the "
        "reference period at each percentile, from at least 100 wet days; each year "
        "with every day: heavy_precipitation_share at each threshold, and the mean "
        "share of those years",
        convention="the reference period is by default the analysed years (the "
        "ETCCDI's base is 1961-1990); the minimum of 100 wet days is Hydrolog's "
        "(ADR-0032), no source gives one",
        source=_CLIMDEX,
    ),
    TierBSpec(
        name="precipitation_regime",
        function="hydrolog.statistics.meteo_precipitation.precipitation_seasonality",
        definition="each monthly normal of the reference period in % of their sum and "
        "over their mean; precipitation_concentration_index and seasonality_index, "
        "with their classes, of the twelve normals and of each year with its twelve "
        "monthly sums, and the means of the yearly indices",
        convention="the indices of the normals and the means of the yearly indices "
        "differ and both are given (Sumner et al. 2001); a total of 0 has no index",
        source=Source(
            citation=_SUMNER,
            locator="p. 225: the SI of the mean monthly "
            "totals and the mean of the yearly SI",
        ),
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""
