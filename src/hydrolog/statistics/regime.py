"""Flow regime of a daily discharge series: Pardé's coefficients and Dynowska's types.

The mean flow of each calendar month over the period (all its days with a value) over
the mean annual flow (all days with a value) is the month's Pardé coefficient (Pardé,
1933; :func:`parde_coefficients`, spec :data:`PARDE_COEFFICIENTS`). Dynowska's (1997)
classification of the Polish river regimes reads the type from the coefficients of
the spring and the summer month, with the criteria as Wrzesiński (2017, 2018) and Perz
(2019) state them (:func:`dynowska_regime_type`, spec :data:`DYNOWSKA_REGIME_TYPE`).
The monthly volumes, the mean flows times the days of the month (February of the
mean year), give the March–April share of the annual volume (:func:`spring_share`,
spec :data:`SPRING_SHARE`) and Walsh and Lawler's (1981) seasonality index
(:func:`seasonality_index`); :func:`flow_regime` gathers them for a daily series
(:data:`TIER_B`). ``docs/FORMULAS.md`` shows the equations, constants and ranges of
the specs (ADR-0063).

Examples
--------
The mean coefficients of the nival-pluvial rivers in Wrzesiński's (2018) Table 1 give
that type, read from April and July:

>>> type_4 = [0.74, 0.85, 0.85, 0.93, 1.45, 1.46, 1.12, 1.08, 1.15, 0.87, 0.79, 0.69]
>>> regime = dynowska_regime_type(type_4)
>>> regime.code, regime.criteria.spring_month, regime.criteria.summer_month
(4, 4, 7)

Equal monthly flows put 61 of the 365.25 days of the mean year in March and April:

>>> spring_share([10.0] * 12) == 61 / 365.25
True

References
----------
Pardé, M. (1933): Fleuves et rivières. Armand Colin, Paris.
Dynowska, I. (1997): Reżim odpływu rzecznego. In: Atlas Rzeczypospolitej Polskiej.
    Główny Geodeta Kraju, Warszawa.
Wrzesiński, D. (2017): Typologia reżimu odpływu rzek w Polsce w podejściu
    nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68),
    253–264 (the criteria on p. 255). doi:10.14746/bfg.2017.8.19
Wrzesiński, D. (2018): Typologia reżimu odpływu rzek w Polsce w różnych fazach
    oscylacji północnoatlantyckiej. Badania Fizjograficzne, Seria A, 9 (A69),
    249–261 (the criteria on p. 250). doi:10.14746/bfg.2018.9.19
Perz, A. (2019): Cechy reżimu odpływu rzek Kotliny Kłodzkiej. Badania Fizjograficzne,
    Seria A, 10 (A70), 65–83 (the spring month is March or April, p. 79).
    doi:10.14746/bfg.2019.10.6
Walsh, R. P. D. & Lawler, D. M. (1981): Rainfall seasonality: description, spatial
    patterns and change through time. Weather, 36(7), 201–208.
"""

from __future__ import annotations

import calendar
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Final, NamedTuple

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
    Symmetry,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._hydrological_year import hydrological_year

__all__ = [
    "DYNOWSKA_REGIME_TYPE",
    "HYDROLOGICAL_MONTHS",
    "PARDE_COEFFICIENTS",
    "SPECS",
    "SPRING_SHARE",
    "TIER_B",
    "FlowRegime",
    "PardeCoefficients",
    "RegimeCriteria",
    "RegimeType",
    "dynowska_regime_type",
    "flow_regime",
    "parde_coefficients",
    "seasonality_index",
    "spring_share",
]

HYDROLOGICAL_MONTHS: tuple[int, ...] = (11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
"""Calendar months in the order of the hydrological year, November first."""

# The calendar months whose coefficients decide the type: spring and summer.
_SPRING_MONTHS = (3, 4)
_SUMMER_MONTHS = (6, 7, 8)


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
        Spring coefficients up to which the nival regime is weakly and moderately
        developed (the constants ``weakly_nival`` and ``moderately_nival`` of
        :data:`DYNOWSKA_REGIME_TYPE`).
    summer_rise : float
        Summer coefficient from which the regime is nival-pluvial (``summer_rise``).
    nearly_equal : float
        Share of the spring coefficient from which the summer one counts as nearly
        equal to it: a pluvio-nival regime (``nearly_equal``, Hydrolog's reading).
    """

    spring_month: int
    spring_coefficient: float
    summer_month: int
    summer_coefficient: float
    nival_limits: list[float] = field(
        default_factory=lambda: [
            DYNOWSKA_REGIME_TYPE.constant("weakly_nival"),
            DYNOWSKA_REGIME_TYPE.constant("moderately_nival"),
        ]
    )
    summer_rise: float = field(
        default_factory=lambda: DYNOWSKA_REGIME_TYPE.constant("summer_rise")
    )
    nearly_equal: float = field(
        default_factory=lambda: DYNOWSKA_REGIME_TYPE.constant("nearly_equal")
    )


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


class PardeCoefficients(NamedTuple):
    """Pardé's coefficients of a daily discharge series (spec ``parde_coefficients``).

    Attributes
    ----------
    monthly_mean : NDArray[np.float64]
        Mean discharge of each month, November to October, over its days with a value,
        in the unit of the daily values.
    annual_mean : float
        Mean discharge of all days with a value.
    parde : NDArray[np.float64]
        The coefficients: ``monthly_mean`` over ``annual_mean``.
    """

    monthly_mean: NDArray[np.float64]
    annual_mean: float
    parde: NDArray[np.float64]


# --- the specs of the regime (Nogat CMP-2.1; ADR-0063) -------------------------------

_WRZESINSKI_2017 = (
    "Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu "
    "nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), "
    "253-264. doi:10.14746/bfg.2017.8.19"
)
_WRZESINSKI_2017_URL = (
    "https://repozytorium.amu.edu.pl/server/api/core/bitstreams/"
    "2a303457-aae6-4476-a766-985a3a4ac0b6/content"
)
_DYNOWSKA_CRITERIA = Source(
    citation=_WRZESINSKI_2017,
    locator="p. 255: Dynowska's (1997) five types: the spring month's mean flow at "
    "most 130 % of the mean annual flow (1), 130-180 % (2), above 180 % (3); as a "
    "rule 130-180 % with a summer rise of at least 100 % (4); the summer month's "
    "mean flow higher than or nearly equal to the spring month's (5)",
    url=_WRZESINSKI_2017_URL,
)
_WRZESINSKI_2018 = Source(
    citation="Wrzesiński, D. (2018). Typologia reżimu odpływu rzek w Polsce w różnych "
    "fazach oscylacji północnoatlantyckiej. Badania Fizjograficzne, Seria A, 9 "
    "(A69), 249-261. doi:10.14746/bfg.2018.9.19",
    locator="p. 250: the five types in the words of Wrzesiński (2017, p. 255); Table "
    "1, pp. 253-254: the mean coefficients of each type, 516 gauges, 1971-2010",
    url="https://pressto.amu.edu.pl/index.php/bfg/article/download/24472/22684/50308",
)
_PERZ = Source(
    citation="Perz, A. (2019). Cechy reżimu odpływu rzek Kotliny Kłodzkiej. Badania "
    "Fizjograficzne, Seria A, 10 (A70), 65-83. doi:10.14746/bfg.2019.10.6",
    locator="p. 79: Dynowska's criteria, 130-180 % and at least 100 % of the mean "
    "annual flow, the spring month March or April (marzec-kwiecień)",
    url="https://pressto.amu.edu.pl/index.php/bfg/article/download/23873/22299/",
)
_DYNOWSKA = Source(
    citation="Dynowska, I. (1997). Reżim odpływu rzecznego. In: Atlas "
    "Rzeczypospolitej Polskiej. Główny Geodeta Kraju, Warszawa",
    locator="the five types of the river regime; not opened: as Wrzesiński (2017, "
    "2018) and Perz (2019) quote them",
    access="author-provided",
)
_REGIME_RULE = Source(
    citation="Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope "
    "and baseflow (docs/decisions/), restated in ADR-0063",
    locator="point 1: where the sources name no month and no number, the spring month "
    "is the larger of March and April, the summer month the largest of June to "
    "August and 'nearly equal' at least 0.95 of the spring coefficient (the "
    "mockup's REGIME_RULE)",
)
_SPRING_SHARE_RULE = Source(
    citation="Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope "
    "and baseflow (docs/decisions/), restated in ADR-0063",
    locator="point 1: spring_share, the March-April share of the annual volume, the "
    "monthly means times the days of the month",
)
_BAWIKI = Source(
    citation="Bundesanstalt für Wasserbau, BAWiki glossary: Parde coefficient",
    locator="the quotient of the long-term mean monthly discharge and the long-term "
    "mean annual runoff",
    url="http://wiki.baw.de/en/index.php/Parde_coefficient",
)
_MONTHLY_COEFFICIENTS = Source(
    citation=_WRZESINSKI_2017,
    locator="p. 254: Dynowska's (1997) types read from the monthly flow coefficients "
    "W (miesięczne współczynniki przepływu); Table 1, p. 260, in % of the mean annual "
    "flow",
    url=_WRZESINSKI_2017_URL,
)
_PARDE_1933 = Source(
    citation="Pardé, M. (1933). Fleuves et rivières. Armand Colin, Paris",
    locator="the monthly coefficient of discharge; not opened",
    access="author-provided",
)
_IMGW_URL = (
    "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/"
)
_KLODZKO_MONTHLY = (
    "IMGW-PIB, public hydrological data: the monthly characteristics of station "
    "150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 but 1997 "
    "(tests/fixtures/imgw_klodzko/imgw_150160180_mies_1971_2015.csv)"
)

_HUGE_DISCHARGE_REASON = (
    "a million m3/s, about five times the mean discharge of the Amazon (about 2.1e5 "
    "m3/s), the largest of any river"
)
_EXACT_SCALING = Tolerance(
    abs=1e-300,
    rel=4.5e-16,
    reason="doubling every discharge doubles each sum and mean exactly and leaves each "
    "quotient as it was; a mean below the normal floats keeps fewer bits",
)


def _calendar_months(days: NDArray[np.datetime64]) -> NDArray[np.float64]:
    """Return the calendar month of each day, January = 1, as floats."""
    months = days.astype("datetime64[M]").astype(np.int64) % 12 + 1
    return months.astype(np.float64)


def _month_days() -> NDArray[np.float64]:
    """Return the days of each month, November to October, February of the mean year."""
    return np.array(
        [
            SPRING_SHARE.constant("february_days")
            if month == 2
            else float(calendar.monthrange(2001, month)[1])  # a common year
            for month in HYDROLOGICAL_MONTHS
        ]
    )


def _mean(values: NDArray[np.float64]) -> float:
    """Return the mean by the correctly rounded sum: NaN of none, inf beyond float64."""
    if values.size == 0:
        return math.nan
    try:
        return math.fsum(values.tolist()) / values.size
    except OverflowError:
        return math.inf


def _means(x: Values) -> tuple[NDArray[np.float64], float]:
    """Return the means of the months, November to October, and of all days."""
    flows = x.array("values")
    months = x.array("month")
    known = ~np.isnan(flows)
    monthly = np.array(
        [_mean(flows[known & (months == m)]) for m in HYDROLOGICAL_MONTHS]
    )
    return monthly, _mean(flows[known])


def _every_month_has_a_value(x: Values) -> bool:
    flows = x.array("values")
    present = set(x.array("month")[~np.isnan(flows)].tolist())
    return all(month in present for month in HYDROLOGICAL_MONTHS)


def _day_weighted_residual(x: Values, out: Values) -> float:
    """Return sum(n_m K_m) / N - 1, n_m the days with a value of month m."""
    flows = x.array("values")
    months = x.array("month")[~np.isnan(flows)]
    counts = [int(np.count_nonzero(months == month)) for month in HYDROLOGICAL_MONTHS]
    weighted = math.fsum(
        count * coefficient
        for count, coefficient in zip(counts, out.array("parde").tolist(), strict=True)
    )
    return weighted / sum(counts) - 1.0


def _rational_means(
    discharge: Sequence[float], month: Sequence[float]
) -> tuple[list[Fraction], Fraction]:
    """Return the monthly means (November to October) and the annual mean exactly."""
    sums = dict.fromkeys(HYDROLOGICAL_MONTHS, Fraction(0))
    counts = dict.fromkeys(HYDROLOGICAL_MONTHS, 0)
    for value, calendar_month in zip(discharge, month, strict=True):
        if not math.isnan(value):
            sums[int(calendar_month)] += Fraction(value)
            counts[int(calendar_month)] += 1
    annual = sum(sums.values(), Fraction(0)) / sum(counts.values())
    return [sums[m] / counts[m] for m in HYDROLOGICAL_MONTHS], annual


_BASE_MONTHS: Final = tuple(float(m) for m in HYDROLOGICAL_MONTHS for _ in range(2))
"""Two days of each month, November to October: the typical point of the spec."""
_BASE_DISCHARGE: Final = (
    8.0, 8.5, 8.2, 8.7, 9.2, 9.7, 13.5, 14.5, 27.5, 28.7, 31.2, 32.2,
    32.4, 33.4, 29.0, 30.0, 15.0, 16.0, 15.2, 16.2, 22.0, 23.0, 13.0, 14.0,
)  # fmt: skip
"""Two days of each month about the monthly means of Kłodzko in 2010 [m3/s]."""


def _parde_samples() -> list[tuple[list[float], list[float]]]:
    """Return the base days and two seeded hydrological years, a tenth missing."""
    rng = np.random.default_rng(20261119)
    days = np.arange(np.datetime64("2019-11-01"), np.datetime64("2021-11-01"))
    flows = np.round(rng.gamma(2.0, 8.0, days.size), 3)
    flows[rng.random(days.size) < 0.1] = np.nan
    return [
        (list(_BASE_DISCHARGE), list(_BASE_MONTHS)),
        (flows.tolist(), _calendar_months(days).tolist()),
    ]


def _exact_parde(run: Callable[..., Values]) -> None:
    for discharge, month in _parde_samples():
        out = run(values=discharge, month=month)
        monthly, annual = _rational_means(discharge, month)
        assert_within(
            [
                *out.array("monthly_mean").tolist(),
                out.real("annual_mean"),
            ],
            [*(float(mean) for mean in monthly), float(annual)],
            rel=4.5e-16,
            reason="exact fractions against a correctly rounded sum (math.fsum) and "
            "one division: two roundings",
        )
        assert_within(
            out.array("parde"),
            [float(mean / annual) for mean in monthly],
            rel=9e-16,
            reason="exact fractions against the quotient of two means of two roundings "
            "each, rounded once more",
        )


PARDE_COEFFICIENTS: Final[FormulaSpec] = FormulaSpec(
    name="parde_coefficients",
    title="Pardé's coefficients: the mean discharge of each month over the mean annual "
    "discharge",
    function="hydrolog.statistics.regime.parde_coefficients",
    family="index",
    equation="K_m = Qbar_m / Qbar, Qbar_m the mean of the days with a value of "
    "calendar month m over the period, Qbar the mean of all days with a value",
    latex=r"K_m = \frac{\bar{Q}_m}{\bar{Q}},\quad \bar{Q}_m = \frac{1}{n_m}"
    r"\sum_{d \in m} Q_d,\quad \bar{Q} = \frac{1}{N}\sum_{d} Q_d",
    variables=(
        Variable(
            name="values",
            symbol="Q_d",
            unit="m3/s",
            kind="real_array",
            description="Daily mean discharge, in m3/s or any unit; NaN marks a day "
            "without a value.",
            physical=Range(
                low=0.0, test_high=1.0e6, test_reason=_HUGE_DISCHARGE_REASON
            ),
            applicability="unstated",
            typical=Range(
                low=1.24,
                high=522.0,
                source=Source(
                    citation=_KLODZKO_MONTHLY,
                    locator="the smallest monthly minimum 1.24 m3/s and the largest "
                    "monthly maximum 522 m3/s of discharge, which bound its daily "
                    "means",
                    url=_IMGW_URL,
                ),
            ),
            gaps_allowed=True,
        ),
        Variable(
            name="month",
            symbol="m_d",
            unit="-",
            kind="real_array",
            description="The calendar month of each day, January = 1.",
            physical=Range(low=1.0, high=12.0),
            applicability="unstated",
            typical=Range(
                low=1.0,
                high=12.0,
                source=Source(
                    citation="IMGW-PIB, MIES_publiczne_format.txt, the format of the "
                    "public monthly files",
                    locator="the calendar month of a row, 1 to 12",
                    url=_IMGW_URL,
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="monthly_mean",
            unit="m3/s",
            kind="real_array",
            symbol=r"\bar{Q}_m",
            description="Mean discharge of each month, November to October.",
            physical=Range(low=0.0),
        ),
        Output(
            name="annual_mean",
            unit="m3/s",
            symbol=r"\bar{Q}",
            description="Mean discharge of all days with a value.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="parde",
            unit="-",
            kind="real_array",
            symbol="K_m",
            description="Pardé's coefficient of each month, November to October.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_BAWIKI, _MONTHLY_COEFFICIENTS, _PARDE_1933),
    constraints=(
        Constraint(
            name="same_length",
            cls="physical",
            check=lambda x: x.array("values").shape == x.array("month").shape,
            text="one month per day",
            source=_BAWIKI,
            satisfied={"month": list(_BASE_MONTHS)},
            violated={"month": list(_BASE_MONTHS[:-1])},
        ),
        Constraint(
            name="whole_months",
            cls="physical",
            check=lambda x: bool(
                np.all(np.floor(x.array("month")) == x.array("month"))
            ),
            text="each month is a whole number, a calendar month 1 to 12",
            source=_BAWIKI,
            satisfied={"month": list(_BASE_MONTHS)},
            violated={"month": [11.5, *_BASE_MONTHS[1:]]},
        ),
        Constraint(
            name="every_month_has_a_value",
            cls="precondition",
            check=_every_month_has_a_value,
            text="every calendar month has a day with a value: twelve means exist",
            source=_BAWIKI,
            satisfied={"values": list(_BASE_DISCHARGE)},
            violated={
                "values": [
                    math.nan if index in (16, 17) else value
                    for index, value in enumerate(_BASE_DISCHARGE)
                ]
            },
        ),
        Constraint(
            name="positive_mean",
            cls="precondition",
            check=lambda x: 0.0 < _means(x)[1] < math.inf,
            text="0 < Qbar < inf: some day has a positive discharge, and float64 holds "
            "the mean and its sum",
            source=_BAWIKI,
            satisfied={"values": list(_BASE_DISCHARGE)},
            violated={"values": [0.0] * len(_BASE_DISCHARGE)},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"values": 1},
        scalings=(
            Scaling(
                name="discharge_in_another_unit",
                inputs={"values": 1.0},
                outputs={"monthly_mean": 1.0, "annual_mean": 1.0},
                tolerance=_EXACT_SCALING,
            ),
        ),
        conservation=(
            Conservation(
                name="day_weighted_mean_of_one",
                text="the coefficients weighted by the days with a value of their "
                "months average one, sum(n_m K_m) = N; they sum to twelve only when "
                "every month has as many days",
                residual=_day_weighted_residual,
                tolerance=Tolerance(
                    abs=4e-15,
                    reason="twelve coefficients of three roundings each, weighted and "
                    "summed by math.fsum",
                ),
            ),
        ),
        limits=(
            Limit(
                name="constant_discharge",
                text="a constant discharge gives every coefficient one",
                inputs={"values": [2.5] * len(_BASE_DISCHARGE)},
                expected={
                    "monthly_mean": [2.5] * 12,
                    "annual_mean": 2.5,
                    "parde": [1.0] * 12,
                },
                tolerance=Tolerance(
                    abs=0.0,
                    reason="sums of 2.5, a number of three bits, are exact, and so are "
                    "their quotients by the counts",
                ),
            ),
            Limit(
                name="exact_rational",
                text="the means and coefficients of the float inputs in exact rational "
                "arithmetic",
                check=_exact_parde,
            ),
        ),
    ),
    validation="none: Pardé's coefficients describe the mean annual cycle of "
    "discharge; their sources compare them with no observations",
    formula_version=1,
    status="referenced",
    conventions=(
        "Qbar_m the mean of the days with a value of calendar month m over the whole "
        "period (the month's days of every year together), Qbar the mean of all days "
        "with a value, as IMGW-PIB's monthly and annual means of a year: the twelve "
        "coefficients weighted by the days of their months average one and sum to 12 "
        "only when every month has as many days (a gapless year: about 11.96 for a "
        "strong spring flood); the mean of the twelve monthly means would make them "
        "sum to 12",
        "a day without a value (NaN) counts in neither mean; with gaps gathered in "
        "some months Qbar leans towards the better observed ones",
        "the input months are calendar months (January = 1), the outputs run from "
        "November to October, the months of the hydrological year",
        "discharge in m3/s or any unit (the coefficients have none); Wrzesiński's "
        "tables print them in % of the mean annual flow",
    ),
    assumptions=(
        "the period's days represent its months: a period of a few years describes "
        "those years, not the climate (the regime of Polish rivers is read from 30 to "
        "40 years, Wrzesiński 2017)",
    ),
    traps={
        "singular_at_bound": "Qbar -> 0 divides every coefficient: the precondition "
        "positive_mean refuses a series without a positive day and a mean that "
        "underflows (test_a_tiny_or_vanishing_mean)",
        "gap_propagation": "type case values-nan_element and "
        "test_gaps_are_left_out_of_both_means: a NaN day is left out, never "
        "propagated",
        "many_small_terms": "test_a_century_of_days_keeps_the_exact_means: 36,525 "
        "days of math.fsum against exact fractions",
    },
    reference_cases=("tests/fixtures/formulas/regime-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the monthly and annual means and the coefficients of the "
            "float inputs in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_regime.py (limit exact_rational, trap "
            "many_small_terms)",
        ),
    ),
    base={
        "values": list(_BASE_DISCHARGE),
        "month": list(_BASE_MONTHS),
    },
)


_FEBRUARY_DAYS: Final = Constant(
    name="february_days",
    value=Fraction(113, 4),
    unit="day",
    symbol="d_{II}",
    source=Source(
        citation="Hydrolog, ADR-0031 (2026), restated in ADR-0063",
        locator="February of the mean year of 1901-2099, in which every fourth year is "
        "a leap year: 28 + 1/4 days, so the twelve months make 365.25 days; the other "
        "months have their days of a common year",
    ),
)


def _volumes(monthly: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return the monthly means times the days of their months, November to October."""
    return monthly * _month_days()


def _total_volume(monthly: NDArray[np.float64]) -> float:
    """Return the sum of the monthly volumes, correctly rounded; inf beyond float64."""
    try:
        return math.fsum(_volumes(monthly).tolist())
    except OverflowError:
        return math.inf


def _spring_share(monthly: NDArray[np.float64]) -> float:
    """Return (V_III + V_IV) / sum(V_m) of means with a positive, finite volume."""
    volumes = _volumes(monthly)
    spring = sum(volumes[HYDROLOGICAL_MONTHS.index(month)] for month in _SPRING_MONTHS)
    return float(spring / _total_volume(monthly))


def _rational_spring_share(monthly: Sequence[float]) -> Fraction:
    days = {
        month: Fraction(_FEBRUARY_DAYS.value)
        if month == 2
        else Fraction(calendar.monthrange(2001, month)[1])
        for month in HYDROLOGICAL_MONTHS
    }
    volumes = {
        month: Fraction(mean) * days[month]
        for month, mean in zip(HYDROLOGICAL_MONTHS, monthly, strict=True)
    }
    return (volumes[3] + volumes[4]) / sum(volumes.values(), Fraction(0))


def _exact_spring_share(run: Callable[..., Values]) -> None:
    rng = np.random.default_rng(20261119)
    samples = [
        [8.27, 8.47, 9.47, 14.0, 28.1, 31.7, 32.9, 29.5, 15.5, 15.7, 22.5, 13.5],
        [0.0, 0.0, 0.0, 0.0, 0.0, 1e-300, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        *(np.round(rng.gamma(2.0, 8.0, 12), 2).tolist() for _ in range(20)),
    ]
    for monthly in samples:
        assert_within(
            run(monthly_mean=monthly).real("spring_share"),
            float(_rational_spring_share(monthly)),
            rel=1.2e-15,
            reason="exact fractions against twelve rounded volumes summed by math.fsum "
            "and a quotient: a few roundings of 1.1e-16",
        )


SPRING_SHARE: Final[FormulaSpec] = FormulaSpec(
    name="spring_share",
    title="The March-April share of the annual volume of the mean monthly flows",
    function="hydrolog.statistics.regime.spring_share",
    family="index",
    equation="s = (V_III + V_IV) / sum(V_m) with V_m = Qbar_m * d_m, d_m the days of "
    "month m, February 28.25",
    latex=r"s = \frac{V_{III} + V_{IV}}{\sum_{m} V_m},\quad V_m = \bar{Q}_m\,d_m",
    variables=(
        Variable(
            name="monthly_mean",
            symbol=r"\bar{Q}_m",
            unit="m3/s",
            kind="real_array",
            description="The mean discharge of each month, November to October.",
            physical=Range(
                low=0.0, test_high=1.0e6, test_reason=_HUGE_DISCHARGE_REASON
            ),
            applicability="unstated",
            typical=Range(
                low=2.67,
                high=58.9,
                source=Source(
                    citation=_KLODZKO_MONTHLY,
                    locator="the monthly means of discharge, 2.67 to 58.9 m3/s",
                    url=_IMGW_URL,
                ),
            ),
            min_length=12,
            max_length=12,
        ),
    ),
    outputs=(
        Output(
            name="spring_share",
            unit="-",
            symbol="s",
            description="The share of March and April in the annual volume, 0 to 1.",
            physical=Range(low=0.0, high=1.0),
        ),
    ),
    sources=(_SPRING_SHARE_RULE,),
    constants=(_FEBRUARY_DAYS,),
    constraints=(
        Constraint(
            name="positive_volume",
            cls="precondition",
            check=lambda x: 0.0 < _total_volume(x.array("monthly_mean")) < math.inf,
            text="0 < sum(V_m) < inf: some month has a positive mean, and float64 "
            "holds the volumes",
            source=_SPRING_SHARE_RULE,
            satisfied={"monthly_mean": [0.0] * 4 + [1.0] + [0.0] * 7},
            violated={"monthly_mean": [0.0] * 12},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="discharge_in_another_unit",
                inputs={"monthly_mean": 1.0},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="equal_months",
                text="equal monthly means give the 61 days of March and April in the "
                "365.25 of the mean year",
                inputs={"monthly_mean": [10.0] * 12},
                expected={"spring_share": 61 / 365.25},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the volumes and their sum are exact, so the quotient is "
                    "the float nearest 61 / 365.25",
                ),
            ),
            Limit(
                name="all_in_spring",
                text="flow in March and April only gives a share of one",
                inputs={"monthly_mean": [0.0] * 4 + [3.0, 7.0] + [0.0] * 6},
                expected={"spring_share": 1.0},
                tolerance=Tolerance(
                    abs=0.0, reason="the same exact sum above and below"
                ),
            ),
            Limit(
                name="exact_rational",
                text="the share of the float inputs in exact rational arithmetic",
                check=_exact_spring_share,
            ),
        ),
    ),
    validation="none: Hydrolog's descriptive index of the regime (ADR-0031)",
    formula_version=1,
    status="oracle only",
    conventions=(
        "the volumes are the long-term monthly means times the days of the month, "
        "February 28.25 days (the mean year of 365.25 days), not the days of the "
        "period's years",
        "the inputs run from November to October, as the outputs of "
        "parde_coefficients; March and April are the fifth and sixth",
        "the volumes in m3/s times days, a unit that cancels in the share",
    ),
    traps={
        "singular_at_bound": "sum(V_m) -> 0 divides the share: the precondition "
        "positive_volume refuses twelve zero means (constraint case "
        "positive_volume-violated); a single month of 1e-300 m3/s gives a finite share "
        "(limit exact_rational)",
        "gap_propagation": "type case monthly_mean-nan_element: a gap is "
        "refused, the twelve means need values",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="the share of the float inputs in exact rational arithmetic "
            "(fractions), February 113/4 days",
            test="tests/unit/test_formulas_regime.py (limit exact_rational)",
        ),
    ),
    base={
        "monthly_mean": [
            8.27,
            8.47,
            9.47,
            14.0,
            28.1,
            31.7,
            32.9,
            29.5,
            15.5,
            15.7,
            22.5,
            13.5,
        ]
    },
)


def _regime_type(parde: NDArray[np.float64]) -> tuple[int, int, float, int, float]:
    """Return the code, the spring month and coefficient, the summer month and one."""
    by_month = dict(zip(HYDROLOGICAL_MONTHS, parde.tolist(), strict=True))
    spring_month = max(_SPRING_MONTHS, key=lambda month: by_month[month])
    summer_month = max(_SUMMER_MONTHS, key=lambda month: by_month[month])
    spring = by_month[spring_month]
    summer = by_month[summer_month]
    constant = DYNOWSKA_REGIME_TYPE.constant
    if summer >= constant("nearly_equal") * spring:
        code = 5
    elif summer >= constant("summer_rise"):
        code = 4
    elif spring <= constant("weakly_nival"):
        code = 1
    elif spring <= constant("moderately_nival"):
        code = 2
    else:
        code = 3
    return code, spring_month, spring, summer_month, summer


def _with(spring: float, summer: float) -> list[float]:
    """Twelve coefficients of 0.5 but March at ``spring`` and July at ``summer``."""
    parde = [0.5] * 12
    parde[HYDROLOGICAL_MONTHS.index(3)] = spring
    parde[HYDROLOGICAL_MONTHS.index(7)] = summer
    return parde


_CLASS_LIMITS: Final = (
    # the spring coefficient at most 130 %, then above it
    (1.3, 0.5, 1),
    (math.nextafter(1.3, math.inf), 0.5, 2),
    # at most 180 %, then above it
    (1.8, 0.5, 2),
    (math.nextafter(1.8, math.inf), 0.5, 3),
    # the summer rise to at least 100 %, then just below it
    (1.5, 1.0, 4),
    (1.5, math.nextafter(1.0, -math.inf), 2),
    # summer at 0.95 of spring, exact in binary, then just below it
    (1.25, 1.1875, 5),
    (1.25, math.nextafter(1.1875, -math.inf), 4),
    # the printed 142.0 % and 134.9 % = 0.95 x 142.0 %, then 134.8 %
    (1.42, 1.349, 5),
    (1.42, 1.348, 4),
)
"""(spring, summer, type) at each limit of the classes and just beyond it."""


def _class_limits(run: Callable[..., Values]) -> None:
    for spring, summer, code in _CLASS_LIMITS:
        found = run(parde=_with(spring, summer)).integer("code")
        if found != code:
            raise AssertionError(
                f"spring {spring!r} and summer {summer!r} give type {found}, the "
                f"criteria type {code} (trap class_limit)"
            )


def _decimal_type(parde: Sequence[float]) -> int:
    """Dynowska's type of the printed decimals of the coefficients, in fractions."""
    value = {
        month: Fraction(repr(float(coefficient)))
        for month, coefficient in zip(HYDROLOGICAL_MONTHS, parde, strict=True)
    }
    spring = max(value[month] for month in _SPRING_MONTHS)
    summer = max(value[month] for month in _SUMMER_MONTHS)
    if 20 * summer >= 19 * spring:
        return 5
    if summer >= 1:
        return 4
    if spring <= Fraction(13, 10):
        return 1
    return 2 if spring <= Fraction(9, 5) else 3


def _decision_table(run: Callable[..., Values]) -> None:
    rng = np.random.default_rng(20261119)
    samples = [np.round(rng.uniform(0.2, 2.9, 12), 3).tolist() for _ in range(300)]
    for thousandths in range(1000, 3001, 20):  # 0.95 of these is printed exactly
        spring = thousandths / 1000
        samples.append(_with(spring, round(0.95 * spring, 3)))
    for parde in samples:
        found = run(parde=parde).integer("code")
        if found != _decimal_type(parde):
            raise AssertionError(
                f"{parde}: type {found}, the decimal criteria type "
                f"{_decimal_type(parde)}"
            )


def _months_that_do_not_decide(x: Values) -> dict[str, object]:
    parde = x.array("parde").copy()
    for index, month in enumerate(HYDROLOGICAL_MONTHS):
        if month not in _SPRING_MONTHS + _SUMMER_MONTHS:
            parde[index] = 1.0
    return {"parde": parde}


DYNOWSKA_REGIME_TYPE: Final[FormulaSpec] = FormulaSpec(
    name="dynowska_regime_type",
    title="Dynowska's type of a Polish river regime from Pardé's coefficients",
    function="hydrolog.statistics.regime.dynowska_regime_type",
    family="classification",
    equation="S = max(K_III, K_IV), L = max(K_VI, K_VII, K_VIII); type 5 if L >= 0.95 "
    "S, else 4 if L >= 1.00, else 1 if S <= 1.30, 2 if S <= 1.80, 3 otherwise",
    latex=r"S = \max(K_{III}, K_{IV}),\ L = \max(K_{VI}, K_{VII}, K_{VIII});\ "
    r"\text{type} = \begin{cases} 5 & L \ge 0.95\,S \\ 4 & L \ge 1.00 \\ "
    r"1 & S \le 1.30 \\ 2 & S \le 1.80 \\ 3 & \text{otherwise} \end{cases}",
    variables=(
        Variable(
            name="parde",
            symbol="K_m",
            unit="-",
            kind="real_array",
            description="Pardé's coefficients of the months November to October.",
            physical=Range(
                low=0.0,
                test_high=30.0,
                test_reason="ten times the largest monthly coefficient of Polish "
                "rivers in Wrzesiński's (2017) Table 1, 2.819 (March, type 3), rounded "
                "up; a coefficient grows without a bound only through gaps",
            ),
            applicability="unstated",
            typical=Range(
                low=0.224,
                high=2.819,
                source=Source(
                    citation=_WRZESINSKI_2017,
                    locator="Table 1, p. 260: the smallest coefficient 22.4 % "
                    "(February, type 5) and the largest 281.9 % (March, type 3) of 516 "
                    "gauges, 1971-2010",
                    url=_WRZESINSKI_2017_URL,
                ),
            ),
            min_length=12,
            max_length=12,
        ),
    ),
    outputs=(
        Output(
            name="code",
            unit="-",
            kind="integer",
            description="1 nival, weakly developed; 2 nival, moderately developed; 3 "
            "nival, strongly developed; 4 nival-pluvial; 5 pluvio-nival.",
            physical=Range(low=1, high=5),
        ),
    ),
    sources=(_DYNOWSKA_CRITERIA, _WRZESINSKI_2018, _PERZ, _DYNOWSKA, _REGIME_RULE),
    constants=(
        Constant(
            name="weakly_nival",
            value=Fraction(13, 10),
            unit="-",
            symbol="S_1",
            source=_DYNOWSKA_CRITERIA,
        ),
        Constant(
            name="moderately_nival",
            value=Fraction(9, 5),
            unit="-",
            symbol="S_2",
            source=_DYNOWSKA_CRITERIA,
        ),
        Constant(
            name="summer_rise",
            value=Fraction(1),
            unit="-",
            symbol="L_1",
            source=_DYNOWSKA_CRITERIA,
        ),
        Constant(
            name="nearly_equal",
            value=Fraction(19, 20),
            unit="-",
            symbol="r",
            source=_REGIME_RULE,
        ),
    ),
    properties=Properties(
        units="unit_specific",
        symmetries=(
            Symmetry(
                name="months_that_do_not_decide",
                text="the coefficients of the months other than March, April and June "
                "to August leave the type as it is",
                inputs=_months_that_do_not_decide,
                outputs=lambda out: {"code": out.integer("code")},
                tolerance=Tolerance(abs=0.0, reason="a class"),
            ),
        ),
        limits=(
            Limit(
                name="class_limits",
                text="a coefficient exactly at a limit of a class and just beyond it "
                "gives the class of the criteria's inclusive limit and the next one",
                check=_class_limits,
            ),
            Limit(
                name="decision_table",
                text="the type of three-decimal coefficients is that of the criteria "
                "applied to their printed decimals in exact fractions",
                check=_decision_table,
            ),
        ),
    ),
    validation="none: a typology; Wrzesiński (2017, 2018) classified 516 gauges of "
    "1971-2010 and Perz (2019) the rivers of the Kłodzko basin by it, without a "
    "measure of agreement",
    formula_version=1,
    status="referenced",
    conventions=(
        "the coefficients are Pardé's of the months November to October, as 1.30 for "
        "130 % of the mean annual flow",
        "the spring month is the larger of March and April (Perz 2019, p. 79), the "
        "summer month the largest of June to August (Hydrolog's reading); of equal "
        "coefficients the earlier month",
        "the types are tested in the order 5, 4, then 1 to 3: 'higher than or nearly "
        "equal' reads as at least 0.95 of the spring coefficient (Hydrolog's reading, "
        "no source gives a number); the sources' 'as a rule 130-180 %' of types 4 and "
        "5 is not tested",
        "inclusive limits as the sources word them: 'at most 130 %' is type 1, 'above "
        "180 %' type 3, so 180 % is type 2, 'at least 100 %' type 4; the limits are "
        "compared as the floats 1.3, 1.8 and 1.0, and summer with the float 0.95 "
        "times spring, which keeps every printed three-decimal tie inside its class",
    ),
    assumptions=(
        "the coefficients describe a long period, 30 to 40 years in the sources; the "
        "type of a few years or of coefficients near a limit is not robust: Kłodzko's "
        "June of 1971-2015 lies 0.05 % above 100 % (Perz's case)",
        "Wrzesiński's two classifications of the same 516 gauges of 1971-2010 count 24 "
        "(2017) and 33 (2018) pluvio-nival rivers: the reading of 'nearly equal' is "
        "not settled in the sources either",
    ),
    traps={
        "class_limit": "limit class_limits: 1.30, 1.80, 1.00 and 0.95 of spring, each "
        "exactly and just beyond (math.nextafter, or the next printed thousandth)",
        "gap_propagation": "type case parde-nan_element: a gap is refused, the twelve "
        "coefficients need values",
    },
    reference_cases=("tests/fixtures/formulas/regime-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="the criteria applied to the printed decimals of the "
            "coefficients in exact fractions, 'nearly equal' as 20 L >= 19 S",
            test="tests/unit/test_formulas_regime.py (limit decision_table)",
            conventions=(
                "the code compares floats with the floats of the limits, the oracle "
                "the decimals the floats print as with the rational limits",
            ),
        ),
    ),
    base={
        "parde": [
            0.74,
            0.85,
            0.85,
            0.93,
            1.45,
            1.46,
            1.12,
            1.08,
            1.15,
            0.87,
            0.79,
            0.69,
        ]
    },
)

SPECS: Final[tuple[FormulaSpec, ...]] = (
    PARDE_COEFFICIENTS,
    SPRING_SHARE,
    DYNOWSKA_REGIME_TYPE,
)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""

TIER_B: Final[tuple[TierBSpec, ...]] = (
    TierBSpec(
        name="flow_regime_of_a_daily_series",
        function="hydrolog.statistics.regime.flow_regime",
        definition="The calendar month of each date; Pardé's coefficients, the spring "
        "share and Dynowska's type of the series (the specs parde_coefficients, "
        "spring_share, dynowska_regime_type), Walsh and Lawler's index of the monthly "
        "volumes (the means times the days of the month, February 28.25 days) and the "
        "first, last and number of the hydrological years with a value",
        convention="months of the Gregorian calendar; the lists from November to "
        "October; a day without a value (NaN) is left out; a hydrological year runs "
        "from November to October and is named after the year of its end (IMGW-PIB)",
        source=Source(
            citation="Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's "
            "slope and baseflow (docs/decisions/)",
            locator="point 1: the result of stats regime",
        ),
        constants=(_FEBRUARY_DAYS,),
    ),
)
"""The Tier B formula of the module (Nogat CMP-2.2)."""


def seasonality_index(monthly: Sequence[float] | NDArray[np.float64]) -> float:
    """Walsh and Lawler's (1981) seasonality index of twelve monthly totals.

    SI = Σ |xₙ − R/12| / R, R = Σ xₙ: 0 when every month has the same total, 11/6 ≈
    1.83 when one month has all of it.

    Parameters
    ----------
    monthly : sequence of float
        The twelve monthly totals (precipitation, runoff volumes), in any order.

    Returns
    -------
    float
        The index.

    Raises
    ------
    InvalidParameterError
        If there are not twelve finite values or their sum is not positive.
    """
    values = np.asarray(monthly, dtype=np.float64)
    if values.shape != (12,) or not np.isfinite(values).all():
        raise InvalidParameterError("seasonality_index needs twelve finite values")
    total = float(values.sum())
    if total <= 0:
        raise InvalidParameterError("seasonality_index needs a positive total")
    return float(np.abs(values - total / 12).sum() / total)


def parde_coefficients(
    values: NDArray[np.float64] | Sequence[float],
    month: NDArray[np.float64] | NDArray[np.integer] | Sequence[float],
) -> PardeCoefficients:
    """Return Pardé's coefficients of daily discharge, spec parde_coefficients.

    Parameters
    ----------
    values : array_like of float
        Daily mean discharge [m³/s]; NaN marks a day without a value.
    month : array_like of int
        The calendar month of each day, January first.

    Returns
    -------
    PardeCoefficients
        The monthly means, the annual mean and the coefficients, the months from
        November to October.

    Raises
    ------
    InvalidParameterError
        If the series is refused by the spec: a negative or infinite discharge, a month
        that is no calendar month, arrays of different lengths, a calendar month
        without a value or no positive discharge.
    """
    x = checked_inputs(PARDE_COEFFICIENTS, values=values, month=month)
    monthly, annual = _means(x)
    out = checked_outputs(
        PARDE_COEFFICIENTS,
        {
            "monthly_mean": monthly,
            "annual_mean": annual,
            "parde": monthly / annual,
        },
    )
    return PardeCoefficients(
        out.array("monthly_mean"),
        out.real("annual_mean"),
        out.array("parde"),
    )


def spring_share(
    monthly_mean: NDArray[np.float64] | Sequence[float],
) -> float:
    """Return the March–April share of the annual volume, spec spring_share.

    Parameters
    ----------
    monthly_mean : array_like of float
        The mean discharge of each month, November to October [m³/s].

    Returns
    -------
    float
        The share of March and April in the volume of the mean year.

    Raises
    ------
    InvalidParameterError
        If the means are refused by the spec: not twelve, negative or not finite, or
        all zero.
    """
    x = checked_inputs(SPRING_SHARE, monthly_mean=monthly_mean)
    share = _spring_share(x.array("monthly_mean"))
    return checked_outputs(SPRING_SHARE, {"spring_share": share}).real("spring_share")


def dynowska_regime_type(parde: Sequence[float] | NDArray[np.float64]) -> RegimeType:
    """Return Dynowska's regime type of Pardé's coefficients, spec dynowska_regime_type.

    Parameters
    ----------
    parde : array_like of float
        Pardé's coefficients of the months November to October.

    Returns
    -------
    RegimeType
        The type and the coefficients and limits it was read from.

    Raises
    ------
    InvalidParameterError
        If the coefficients are refused by the spec: not twelve, negative or not
        finite.
    """
    x = checked_inputs(DYNOWSKA_REGIME_TYPE, parde=parde)
    code, spring_month, spring, summer_month, summer = _regime_type(x.array("parde"))
    out = checked_outputs(DYNOWSKA_REGIME_TYPE, {"code": code})
    return RegimeType(
        code=out.integer("code"),
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

    Pardé's coefficients (:func:`parde_coefficients`), the March–April share of the
    volume (:func:`spring_share`), Dynowska's type (:func:`dynowska_regime_type`) and
    Walsh and Lawler's index of the monthly volumes (:func:`seasonality_index`), the
    volumes January to December (:data:`TIER_B`).

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
        If the series is refused by the spec ``parde_coefficients``: arrays empty or of
        different lengths, a negative or infinite discharge, a calendar month without
        a value (``details.constraint`` ``every_month_has_a_value``) or no positive
        discharge (``positive_mean``).
    """
    days = np.asarray(dates).astype("datetime64[D]")
    coefficients = parde_coefficients(discharge, _calendar_months(days))
    known = ~np.isnan(np.asarray(discharge, dtype=np.float64))
    years = np.unique(hydrological_year(days[known]))
    monthly_mean = coefficients.monthly_mean
    january_first = [HYDROLOGICAL_MONTHS.index(month) for month in range(1, 13)]
    return FlowRegime(
        first_year=int(years[0]),
        last_year=int(years[-1]),
        period_years=int(years.size),
        n_values=int(known.sum()),
        months=list(HYDROLOGICAL_MONTHS),
        monthly_mean=monthly_mean.tolist(),
        annual_mean=coefficients.annual_mean,
        parde=coefficients.parde.tolist(),
        regime_type=dynowska_regime_type(coefficients.parde),
        spring_share=spring_share(monthly_mean),
        seasonality_index=seasonality_index(_volumes(monthly_mean)[january_first]),
    )
