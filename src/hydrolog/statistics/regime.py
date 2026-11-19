"""Flow regime of a daily discharge series: Pardé's coefficients and Dynowska's types.

The mean flow of each calendar month over the period (all its days with a value) over
the mean annual flow (all days with a value) is the month's Pardé coefficient (Pardé,
1933). Dynowska's (1997) classification of the Polish river regimes reads the type
from the coefficients of the spring and the summer month, with the criteria as
Wrzesiński (2018) states them (:func:`dynowska_regime_type`). The monthly volumes, the
mean flows times the days of the month (28.25 for February), give the March–April share
of the annual volume and Walsh and Lawler's (1981) seasonality index
(:func:`seasonality_index`, declared by its spec :data:`SEASONALITY_INDEX`, Nogat's
computation standard, ADR-0059; ``docs/FORMULAS.md`` shows it).

References
----------
Pardé, M. (1933): Fleuves et rivières. Armand Colin, Paris.
Dynowska, I. (1997): Reżim odpływu rzecznego. In: Atlas Rzeczypospolitej Polskiej.
    Główny Geodeta Kraju, Warszawa.
Wrzesiński, D. (2018): Typologia reżimu odpływu rzek w Polsce w różnych fazach
    oscylacji północnoatlantyckiej. Badania Fizjograficzne, Seria A, 9 (A69),
    249–261 (the criteria on p. 250). doi:10.14746/bfg.2018.9.19
Perz, A. (2019): Cechy reżimu odpływu rzek Kotliny Kłodzkiej. Badania Fizjograficzne,
    Seria A, 10 (A70), 65–83 (the spring month is March or April, p. 79).
    doi:10.14746/bfg.2019.10.6
Walsh, R. P. D. & Lawler, D. M. (1981): Rainfall seasonality: description, spatial
    patterns and change through time. Weather, 36(7), 201–208.
Sumner, G., Homar, V. & Ramis, C. (2001): Precipitation seasonality in eastern and
    southern coastal Spain. International Journal of Climatology 21, 219-247.

Examples
--------
>>> seasonality_index([10.0] * 12), seasonality_index([0.0] * 11 + [50.0])
(0.0, 1.8333333333333333)
"""

from __future__ import annotations

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
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._hydrological_year import hydrological_year

__all__ = [
    "HYDROLOGICAL_MONTHS",
    "FlowRegime",
    "RegimeCriteria",
    "RegimeType",
    "SEASONALITY_INDEX",
    "SPECS",
    "dynowska_regime_type",
    "flow_regime",
    "seasonality_index",
]

HYDROLOGICAL_MONTHS: tuple[int, ...] = (11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
"""Calendar months in the order of the hydrological year, November first."""

# Days of each calendar month for the monthly volumes; February is the mean of the
# Gregorian years, so twelve months add up to 365.25 days.
_MONTH_DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
# The calendar months whose coefficients decide the type: spring and summer.
_SPRING_MONTHS = (3, 4)
_SUMMER_MONTHS = (6, 7, 8)
# Dynowska's limits of the spring coefficient (Wrzesiński 2018): up to 1.30 a weakly,
# up to 1.80 a moderately and above it a strongly developed nival regime.
_NIVAL_LIMITS = (1.30, 1.80)
# A summer rise to at least the mean annual flow makes the regime nival-pluvial.
_SUMMER_RISE = 1.00
# The summer coefficient "nearly equal" to the spring one: at least this share of it
# (the sources give no number; Hydrolog's reading).
_NEARLY_EQUAL = 0.95


@dataclass
class RegimeCriteria(JsonResultMixin):
    """The coefficients and limits that decide Dynowska's regime type.

    Attributes
    ----------
    spring_month : int
        March (3) or April (4): the spring month with the larger coefficient.
    spring_coefficient : float
        Its Pardé coefficient.
    summer_month : int
        June (6), July (7) or August (8): the summer month with the largest
        coefficient.
    summer_coefficient : float
        Its Pardé coefficient.
    nival_limits : list of float
        Spring coefficients up to which the nival regime is weakly (1.30) and
        moderately (1.80) developed.
    summer_rise : float
        Summer coefficient from which the regime is nival-pluvial (1.00).
    nearly_equal : float
        Share of the spring coefficient from which the summer one counts as nearly
        equal to it: a pluvio-nival regime (0.95).
    """

    spring_month: int
    spring_coefficient: float
    summer_month: int
    summer_coefficient: float
    nival_limits: list[float] = field(default_factory=lambda: list(_NIVAL_LIMITS))
    summer_rise: float = _SUMMER_RISE
    nearly_equal: float = _NEARLY_EQUAL


@dataclass
class RegimeType(JsonResultMixin):
    """Dynowska's (1997) type of a river regime.

    Attributes
    ----------
    code : int
        1 nival, weakly developed; 2 nival, moderately developed; 3 nival, strongly
        developed; 4 nival-pluvial; 5 pluvio-nival (Wrzesiński, 2018).
    criteria : RegimeCriteria
        The coefficients and limits the type was read from.
    """

    code: int
    criteria: RegimeCriteria


@dataclass
class FlowRegime(JsonResultMixin):
    """The flow regime of a daily discharge series over a period.

    Attributes
    ----------
    first_year, last_year : int
        First and last hydrological year with a value.
    period_years : int
        Hydrological years with a value.
    n_values : int
        Days with a value.
    months : list of int
        The calendar months of the monthly lists, November to October.
    monthly_mean : list of float
        Mean flow of each month over its days with a value [m³/s].
    annual_mean : float
        Mean flow of all days with a value [m³/s].
    parde : list of float
        Pardé's coefficients: ``monthly_mean`` over ``annual_mean``.
    regime_type : RegimeType
        Dynowska's regime type.
    spring_share : float
        Share of March and April in the annual volume (the monthly means times the
        days of the month), 0 to 1.
    seasonality_index : float
        Walsh and Lawler's (1981) index of the monthly volumes: 0 for equal months,
        1.83 when one month holds the whole volume.
    """

    first_year: int
    last_year: int
    period_years: int
    n_values: int
    months: list[int]
    monthly_mean: list[float]
    annual_mean: float
    parde: list[float]
    regime_type: RegimeType
    spring_share: float
    seasonality_index: float


_SUMNER = Source(
    citation="Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality "
    "in eastern and southern coastal Spain. International Journal of Climatology 21, "
    "219-247",
    locator="eq. 1, p. 225: SI = (1/R) sum |x_n - R/12|, R the annual total; 0 when "
    "every month has the same total, 1.83 when one month has all of it",
)
_HYDROTSM = Source(
    citation="Zambrano-Bigiarini, M. hydroTSM: time series management and analysis "
    "for hydrological modelling, R package (CRAN)",
    locator="si(): the seasonality index of Walsh and Lawler (1981), from 0 to 1.83",
    url="https://cran.r-project.org/package=hydroTSM",
)
_WALSH_LAWLER = Source(
    citation="Walsh, R. P. D. and Lawler, D. M. (1981). Rainfall seasonality: "
    "description, spatial patterns and change through time. Weather 36(7), 201-208",
    locator="the index; not opened here: as Sumner et al. (2001) and hydroTSM print it",
    access="author-provided",
)
_MONTH_RECORD = (
    "a month holds less than the world's greatest 12-month rainfall, 26,470 mm at "
    "Cherrapunji, 1 August 1860 - 31 July 1861 (WMO Archive of Weather and Climate "
    "Extremes)"
)
_WARSZAWA = Source(
    citation="Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: "
    "the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020",
    locator="the monthly sums of 1991-2020: 0.4 to 295.0 mm",
)


def _si(monthly: NDArray[np.float64]) -> float:
    """Return the index from the shares of the total: no sum near zero divides."""
    shares = monthly / float(np.sum(monthly))
    return float(np.sum(np.abs(shares - 1 / 12)))


def _exact_si(monthly: Sequence[float]) -> float:
    values = [Fraction(value) for value in monthly]
    total = sum(values, Fraction(0))
    deviations = [abs(value - total / 12) for value in values]
    return float(sum(deviations, Fraction(0)) / total)


def _si_oracle(run: Callable[..., Values]) -> None:
    rng = np.random.default_rng(20261119)
    samples = [
        [31.0, 29.8, 29.0, 35.1, 55.5, 63.9, 82.2, 60.6, 50.4, 40.2, 36.0, 36.1],
        [0.0] * 6 + [1e-300] + [0.0] * 5,
        *(np.round(rng.gamma(1.5, 30.0, size=12), 1).tolist() for _ in range(20)),
    ]
    for monthly in samples:
        assert_within(
            run(monthly_mm=monthly).real("si"),
            _exact_si(monthly),
            abs=1e-14,
            reason="exact fractions against twelve shares, each rounding 1.1e-16",
        )


def _reversed(x: Values) -> dict[str, object]:
    return {"monthly_mm": x.array("monthly_mm")[::-1].copy()}


SEASONALITY_INDEX: Final = FormulaSpec(
    name="seasonality_index",
    title="Walsh and Lawler's seasonality index of twelve monthly totals",
    function="hydrolog.statistics.regime.seasonality_index",
    family="index",
    equation="SI = (1/R) sum |x_n - R/12| over the twelve monthly totals x_n, R = "
    "sum x_n",
    latex=r"\mathrm{SI} = \frac{1}{R}\sum_{n=1}^{12}\left|x_n - \frac{R}{12}\right|,"
    r"\quad R = \sum_{n=1}^{12} x_n",
    variables=(
        Variable(
            name="monthly_mm",
            symbol="x_n",
            unit="mm",
            kind="real_array",
            description="The twelve monthly totals in any order: precipitation, or "
            "runoff volumes in any unit (the index has none).",
            physical=Range(low=0.0, test_high=26_470.0, test_reason=_MONTH_RECORD),
            applicability="unstated",
            typical=Range(low=0.4, high=295.0, source=_WARSZAWA),
            min_length=12,
            max_length=12,
        ),
    ),
    outputs=(
        Output(
            name="si",
            unit="-",
            symbol=r"\mathrm{SI}",
            description="The index: 0 for equal months, 11/6 for one wet month.",
            physical=Range(low=0.0, high=11 / 6),
            boundary_tolerance=1e-12,
        ),
    ),
    sources=(_SUMNER, _HYDROTSM, _WALSH_LAWLER),
    constraints=(
        Constraint(
            name="a_positive_total",
            cls="precondition",
            check=lambda x: float(np.sum(x.array("monthly_mm"))) > 0.0,
            text="the total of the twelve months is positive",
            source=_SUMNER,
            satisfied={"monthly_mm": [0.0] * 11 + [0.1]},
            violated={"monthly_mm": [0.0] * 12},
        ),
    ),
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
                inputs=_reversed,
                outputs=lambda out: {"si": out.real("si")},
                tolerance=Tolerance(
                    abs=1e-14, reason="twelve terms summed in another order"
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_oracle",
                text="SI equals the equation in exact fractions",
                check=_si_oracle,
            ),
            Limit(
                name="one_wet_month",
                text="one month with all the precipitation gives 11/6",
                inputs={"monthly_mm": [0.0] * 11 + [50.0]},
                expected={"si": 11 / 6},
                tolerance=Tolerance(abs=1e-15, reason="twelve terms of 1/12 or 11/12"),
            ),
        ),
    ),
    validation="none: an index of the monthly totals",
    formula_version=1,
    status="referenced",
    conventions=(
        "computed as the sum of |x_n / R - 1/12|, which equals the equation without "
        "R/12, which underflows for a subnormal R",
        "precipitation_seasonality gives the twelve normals of a reference period or "
        "the twelve monthly sums of a year with all of them, flow_regime the monthly "
        "volumes of a discharge series; a total of 0 has no index",
    ),
    traps={
        "difference_denominator": "precondition a_positive_total: R divides",
        "singular_at_bound": "limit exact_oracle: a single month of 1e-300 mm gives "
        "11/6",
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
SPECS: Final = (SEASONALITY_INDEX,)
"""The Tier A formulas of the module."""


def seasonality_index(monthly_mm: NDArray[np.float64] | Sequence[float]) -> float:
    """Return Walsh and Lawler's seasonality index, spec seasonality_index.

    Parameters
    ----------
    monthly_mm : array_like of float
        The twelve monthly totals [mm], in any order; runoff volumes in any unit too.

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
    x = checked_inputs(SEASONALITY_INDEX, monthly_mm=monthly_mm)
    value = _si(x.array("monthly_mm"))
    return checked_outputs(SEASONALITY_INDEX, {"si": value}).real("si")


def dynowska_regime_type(parde: Sequence[float] | NDArray[np.float64]) -> RegimeType:
    """Read Dynowska's (1997) regime type from twelve Pardé coefficients.

    The criteria as Wrzesiński (2018, p. 250) states them, with the spring month the
    larger of March and April (Perz, 2019) and the summer month the largest of June to
    August: (5) pluvio-nival when the summer coefficient is at least 0.95 of the
    spring one ("higher or nearly equal"); otherwise (4) nival-pluvial when the
    summer coefficient is at least 1.00 (the summer rise to the mean annual flow);
    otherwise nival by the spring coefficient: (1) weakly developed up to 1.30, (2)
    moderately developed up to 1.80, (3) strongly developed above it. The sources'
    "as a rule 130–180 %" of types 4 and 5 is not tested; of two equal coefficients
    the earlier month is taken.

    Parameters
    ----------
    parde : sequence of float
        Pardé's coefficients of the months November to October.

    Returns
    -------
    RegimeType
        The type and the coefficients and limits it was read from.

    Raises
    ------
    InvalidParameterError
        If there are not twelve finite coefficients.
    """
    values = np.asarray(parde, dtype=np.float64)
    if values.shape != (12,) or not np.isfinite(values).all():
        raise InvalidParameterError("dynowska_regime_type needs twelve coefficients")
    by_month = dict(zip(HYDROLOGICAL_MONTHS, values.tolist(), strict=True))
    spring_month = max(_SPRING_MONTHS, key=lambda month: by_month[month])
    summer_month = max(_SUMMER_MONTHS, key=lambda month: by_month[month])
    spring = by_month[spring_month]
    summer = by_month[summer_month]
    if summer >= _NEARLY_EQUAL * spring:
        code = 5
    elif summer >= _SUMMER_RISE:
        code = 4
    elif spring <= _NIVAL_LIMITS[0]:
        code = 1
    elif spring <= _NIVAL_LIMITS[1]:
        code = 2
    else:
        code = 3
    return RegimeType(
        code=code,
        criteria=RegimeCriteria(
            spring_month=spring_month,
            spring_coefficient=spring,
            summer_month=summer_month,
            summer_coefficient=summer,
        ),
    )


def flow_regime(
    discharge: NDArray[np.float64], dates: NDArray[np.datetime64]
) -> FlowRegime:
    """Compute the flow regime of a daily discharge series.

    Parameters
    ----------
    discharge : NDArray[np.float64]
        Daily mean discharge [m³/s]; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates (days may be absent).

    Returns
    -------
    FlowRegime
        The monthly means and Pardé's coefficients (November to October), the regime
        type, the March–April share of the volume and the seasonality index.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, a calendar month has no value
        (``details.missing_months``) or the mean annual flow is not positive.
    """
    flows = np.asarray(discharge, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[D]")
    if flows.size == 0 or flows.size != days.size:
        raise InvalidParameterError(
            "discharge and dates must be non-empty and of the same length"
        )
    known = np.isfinite(flows)
    flows, days = flows[known], days[known]
    months = days.astype("datetime64[M]").astype(np.int64) % 12 + 1
    counts = np.bincount(months, minlength=13)[1:]
    missing = [month for month in range(1, 13) if counts[month - 1] == 0]
    if missing:
        raise InvalidParameterError(
            "The regime needs values in every calendar month; no values in "
            f"month(s): {', '.join(str(month) for month in missing)}",
            details={"missing_months": missing},
        )
    calendar_means = np.bincount(months, weights=flows, minlength=13)[1:] / counts
    annual_mean = float(flows.mean())
    if not annual_mean > 0:
        raise InvalidParameterError(
            f"The mean annual flow must be positive, got {annual_mean}"
        )
    volumes = calendar_means * _MONTH_DAYS
    order = [month - 1 for month in HYDROLOGICAL_MONTHS]
    monthly_mean = calendar_means[order]
    parde = monthly_mean / annual_mean
    years = np.unique(hydrological_year(days))
    return FlowRegime(
        first_year=int(years[0]),
        last_year=int(years[-1]),
        period_years=int(years.size),
        n_values=int(flows.size),
        months=list(HYDROLOGICAL_MONTHS),
        monthly_mean=[float(value) for value in monthly_mean],
        annual_mean=annual_mean,
        parde=[float(value) for value in parde],
        regime_type=dynowska_regime_type(parde),
        spring_share=float(volumes[2:4].sum() / volumes.sum()),
        seasonality_index=seasonality_index(volumes),
    )
