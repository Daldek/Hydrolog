"""Baseflow separation by the Lyne and Hollick filter and the recession constant.

The one-parameter recursive digital filter of Lyne and Hollick (1979) splits the
daily flow Q into quickflow and baseflow:

    qₜ = α qₜ₋₁ + (1 + α)/2 (Qₜ − Qₜ₋₁),   bₜ = Qₜ − qₜ when qₜ > 0, else Qₜ,

passed forward, backward and forward over the series (Nathan and McMahon, 1990), each
pass filtering the baseflow of the one before. The filter follows the standard
approach of Ladson et al. (2013) and their published code: α = 0.925, three passes,
the series reflected by 30 days at each end so that the passes start outside it, the
quickflow of each pass starting at the first value of its input and kept as it is
(negative too) for the next step, and the baseflow below 0 set to 0 at the end. A
daily series with gaps is filtered on each gapless span of at least 60 days; the
baseflow index is BFI = Σ b / Σ Q over the days filtered.

The recession constant k is the median of the daily ratios Qₜ₊₁ / Qₜ of the total flow
on the runs of at least 5 consecutive days of falling flow, Hydrolog's own choice of
recession segments; k is the daily constant of Qₜ = Q₀ kᵗ (WMO No. 1029, 2009, sec.
5.3), but its segments include the quickflow after a peak, which WMO's baseflow
recession analysis leaves out. The half-life of a recession is ln 2 / (−ln k) days.

The three Tier A formulas of Nogat's computation standard are declared by their
specs (ADR-0050, ADR-0063): :data:`LYNE_HOLLICK` (:func:`lyne_hollick_filter`),
:data:`BASEFLOW_INDEX` (:func:`baseflow_index`) and :data:`RECESSION`
(:func:`recession_ratio`, which :func:`recession_constant` wraps); the spans, the
years and a series without a recession are the Tier B rows of :data:`TIER_B`.

Examples
--------
The 67 daily flows [ML/d] of the Bass River at Loch, the worked example of Ladson et
al. (2013), with their α = 0.98:

>>> import numpy as np
>>> from hydrolog.statistics.baseflow import (
...     baseflow_index, lyne_hollick_filter, recession_constant)
>>> flows = np.array([
...     5, 7, 108, 117, 57, 36, 26, 95, 1169, 308, 144, 89, 62, 48, 40, 35, 73, 82,
...     342, 393, 310, 275, 260, 245, 256, 141, 119, 934, 382, 158, 96, 122, 103, 83,
...     67, 148, 366, 161, 119, 82, 330, 294, 261, 266, 153, 247, 703, 498, 286, 163,
...     124, 85, 94, 81, 62, 47, 37, 30, 26, 24, 24, 22, 21, 20, 19, 18, 18,
... ], dtype=float)
>>> base = lyne_hollick_filter(flows, alpha=0.98)
>>> [round(float(value), 1) for value in base[:5]]  # their Table 3
[5.0, 7.0, 22.1, 23.2, 24.1]
>>> round(baseflow_index(flows, base), 7)  # BFI_example.R
0.1965759

An exponential recession Qₜ = 10 · 0.9ᵗ has the daily constant 0.9:

>>> recession = recession_constant(10 * 0.9 ** np.arange(8.0))
>>> round(recession.k, 12), recession.n_segments
(0.9, 1)
>>> round(recession.half_life_days, 4)
6.5788

References
----------
Lyne, V. & Hollick, M. (1979): Stochastic time-variable rainfall-runoff modelling.
    Hydrology and Water Resources Symposium, Institution of Engineers Australia, Perth.
Nathan, R. J. & McMahon, T. A. (1990): Evaluation of automated techniques for base
    flow and recession analyses. Water Resources Research, 26(7), 1465–1473.
Ladson, A. R., Brown, R., Neal, B. & Nathan, R. (2013): A standard approach to baseflow
    separation using the Lyne and Hollick filter. Australasian Journal of Water
    Resources, 17(1), 25–34; code: github.com/TonyLadson/BaseflowSeparation_LyneHollick.
World Meteorological Organization (2009): Manual on Low-flow Estimation and
    Prediction. WMO No. 1029, Operational Hydrology Report No. 50, Geneva, sec. 5.3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy.signal import lfilter

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
)
from hydrolog.statistics._hydrological_year import (
    days_in_hydrological_year,
    hydrological_year,
    hydrological_year_start,
    on_daily_calendar,
)

__all__ = [
    "BASEFLOW_ALPHA",
    "BASEFLOW_INDEX",
    "BASEFLOW_PASSES",
    "LYNE_HOLLICK",
    "MIN_RECESSION_DAYS",
    "MIN_SPAN_DAYS",
    "MIN_YEAR_DAYS",
    "RECESSION",
    "REFLECTED_DAYS",
    "SPECS",
    "TIER_B",
    "BaseflowSeparation",
    "BaseflowYear",
    "RecessionConstant",
    "baseflow_index",
    "baseflow_separation",
    "lyne_hollick_filter",
    "recession_constant",
    "recession_ratio",
]

BASEFLOW_ALPHA = 0.925
"""Filter parameter α of Nathan and McMahon (1990) for daily flows."""
BASEFLOW_PASSES = 3
"""Passes of the filter: forward, backward, forward."""
REFLECTED_DAYS = 30
"""Days reflected at each end of a span (Ladson et al., 2013)."""
MIN_SPAN_DAYS = 60
"""Shortest gapless span of days that is filtered."""
MIN_YEAR_DAYS = 300
"""Days with a baseflow that a hydrological year needs for an index of its own."""
MIN_RECESSION_DAYS = 5
"""Shortest recession segment: days of falling flow in a row."""


@dataclass
class BaseflowYear(JsonResultMixin):
    """The baseflow of one hydrological year.

    Attributes
    ----------
    year : int
        Hydrological year (1 November - 31 October, named after its end).
    bfi : float or None
        Baseflow index Σ b / Σ Q of its days with a baseflow (spec
        ``baseflow_index``); ``None`` when no water flowed on them, where the index
        is undefined.
    n_values : int
        Days with a baseflow.
    baseflow_mean, discharge_mean : float
        Mean baseflow and mean discharge of those days [m³/s].
    """

    year: int
    bfi: float | None
    n_values: int
    baseflow_mean: float
    discharge_mean: float


@dataclass
class RecessionConstant(JsonResultMixin):
    """The recession constant of a daily series (spec ``recession_constant``).

    Attributes
    ----------
    k : float or None
        Median ratio Qₜ₊₁ / Qₜ of the total flow over the recession segments;
        ``None`` without one.
    half_life_days : float or None
        ln 2 / (−ln k): the days in which such a recession halves the flow.
    n_segments : int
        Recession segments found.
    """

    k: float | None
    half_life_days: float | None
    n_segments: int


@dataclass
class BaseflowSeparation(JsonResultMixin):
    """Baseflow of a daily discharge series by the Lyne and Hollick filter.

    Attributes
    ----------
    alpha : float
        The filter parameter.
    passes : int
        Passes of the filter.
    first_year, last_year : int
        First and last hydrological year with a value.
    period_years : int
        Hydrological years with a value.
    bfi : float
        Baseflow index Σ b / Σ Q over the days with a baseflow.
    n_values : int
        Days with a baseflow: those of the gapless spans of at least 60 days.
    n_spans : int
        Gapless spans filtered.
    years : list of BaseflowYear
        Each year with at least :data:`MIN_YEAR_DAYS` days with a baseflow.
    recession : RecessionConstant
        The recession constant of the period.
    series_year : int
        Hydrological year of ``series_dates`` and ``series_baseflow``.
    series_dates : list of str
        Every day of ``series_year`` (ISO dates).
    series_baseflow : list of float or None
        The baseflow of each of those days [m³/s]; ``None`` without one.
    """

    alpha: float
    passes: int
    first_year: int
    last_year: int
    period_years: int
    bfi: float
    n_values: int
    n_spans: int
    years: list[BaseflowYear]
    recession: RecessionConstant
    series_year: int
    series_dates: list[str] = field(default_factory=list)
    series_baseflow: list[float | None] = field(default_factory=list)


# --- sources ----------------------------------------------------------------------

_LADSON_CITATION: Final = (
    "Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to "
    "baseflow separation using the Lyne and Hollick filter. Australasian Journal of "
    "Water Resources 17(1), 25-34 (the authors' accepted manuscript)"
)
_LADSON_URL: Final = (
    "https://tonyladson.wordpress.com/2013/10/01/"
    "a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/"
)
_LADSON_CODE_CITATION: Final = (
    "Ladson, A.R. (2013). BFI.R and BFI_example.R, the code of Ladson et al. (2013), "
    "github.com/TonyLadson/BaseflowSeparation_LyneHollick, commit 8d09646 "
    "(2014-02-12), copied into tests/oracles/baseflow/"
)
_LADSON_CODE_URL: Final = "https://github.com/TonyLadson/BaseflowSeparation_LyneHollick"
_WMO_1029_CITATION: Final = (
    "WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology "
    "Report No. 50, WMO-No. 1029"
)
_WMO_1029_URL: Final = "https://library.wmo.int/idurl/4/32176"


def _ladson(locator: str) -> Source:
    return Source(citation=_LADSON_CITATION, locator=locator, url=_LADSON_URL)


def _ladson_code(locator: str) -> Source:
    return Source(citation=_LADSON_CODE_CITATION, locator=locator, url=_LADSON_CODE_URL)


def _wmo_1029(locator: str) -> Source:
    return Source(citation=_WMO_1029_CITATION, locator=locator, url=_WMO_1029_URL)


_NATHAN_MCMAHON: Final = Source(
    citation="Nathan, R.J. and McMahon, T.A. (1990). Evaluation of automated "
    "techniques for base flow and recession analyses. Water Resources Research 26(7), "
    "1465-1473",
    locator="the filter with three passes and alpha 0.925 for daily flows, as quoted "
    "by Ladson et al. (2013), sect. 1.1 and 2.5, and by Murphy et al. (2009), p. 16",
    url="https://doi.org/10.1029/WR026i007p01465",
    access="author-provided",
)
_ARR_P7: Final = Source(
    citation="Murphy, R., Graszkiewicz, Z., Hill, P., Neal, B., Nathan, R. and Ladson, "
    "T. (2009). Australian Rainfall and Runoff Revision Project 7: Baseflow for "
    "Catchment Simulation, Stage 1 report, P7/S1/004, Engineers Australia",
    locator="p. 15, eq. 7 (the filter); p. 16 (three passes, forward, backward and "
    "forward; alpha 0.925 of Nathan and McMahon 1990 for daily data)",
    url="https://www.arr-software.org/pdfs/ARR_Project07_Stage1_Final%20Report.pdf",
)
_DAILY_FLOWS: Final = Source(
    citation="IMGW-PIB, public hydrological data: daily discharge of the Nysa Kłodzka "
    "at Kłodzko (station 150160180) in 2010, files codz_2010_01 to codz_2010_12; and "
    "Hydrolog's synthetic station of the GUI guide, tests/fixtures/station_daily.csv",
    locator="Kłodzko 2010: 4.93 to 96.0 m3/s; station_daily.csv, 2018-11 to 2023-10: "
    "0.52 to 122.34 m3/s",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/"
    "dane_hydrologiczne/",
)
_ADR_0031: Final = Source(
    citation="Hydrolog's own rules, ADR-0031: Regime, seasonality, harmonics, Sen's "
    "slope and baseflow of a station",
    locator="point 5: the filter on each gapless span of at least 60 days, a year's "
    "index from 300 days with a baseflow (no published source; Ladson et al. 2013 "
    "filter every segment longer than the 30 reflected values, sect. 2.1 and 2.4)",
    url="docs/decisions/0031-regime-seasonality-harmonics-sens-slope-and-baseflow.md",
)
_HYDROLOG_DEFAULTS: Final = Source(
    citation="Hydrolog's catalog and tests: the defaults of stats baseflow (alpha "
    "0.925, passes 3, recession segments of 5 days), with which Obserwator calls it, "
    "and alpha 0.98 of the worked example of Ladson et al. (2013) in its verification",
    locator="src/hydrolog/catalog/groups/stats.py (stats baseflow); "
    "tests/unit/test_station_regime.py (TestBaseflow)",
)

_UNIT: Final = "m3/s"
"""The unit of the series in the documents: the formulas are homogeneous (their
scalings), so a series in any unit, ML/d as in Ladson et al. (2013), gives its baseflow
in that unit."""

_ANY_FLOW: Final = Range(
    low=0.0,
    test_high=1.0e6,
    test_reason=(
        "the formulas are homogeneous in the unit of the series (their scalings), so "
        "any bound tests their arithmetic: a million m3/s exceeds the discharge of "
        "every river (the Amazon's floods reach about 300,000 m3/s)"
    ),
)
"""A discharge: not negative, unbounded above."""

_TYPICAL_FLOWS: Final = Range(low=0.5, high=125.0, source=_DAILY_FLOWS)
"""Daily discharges of a Polish gauge and of Hydrolog's station fixture."""

_BASS_RIVER: Final = (
    5.0, 7.0, 108.0, 117.0, 57.0, 36.0, 26.0, 95.0, 1169.0, 308.0, 144.0, 89.0, 62.0,
    48.0, 40.0, 35.0, 73.0, 82.0, 342.0, 393.0, 310.0, 275.0, 260.0, 245.0, 256.0,
    141.0, 119.0, 934.0, 382.0, 158.0, 96.0, 122.0, 103.0, 83.0, 67.0, 148.0, 366.0,
    161.0, 119.0, 82.0, 330.0, 294.0, 261.0, 266.0, 153.0, 247.0, 703.0, 498.0, 286.0,
    163.0, 124.0, 85.0, 94.0, 81.0, 62.0, 47.0, 37.0, 30.0, 26.0, 24.0, 24.0, 22.0,
    21.0, 20.0, 19.0, 18.0, 18.0,
)  # fmt: skip
"""The 67 daily flows [ML/d] of the Bass River at Loch, 30 June - 4 September 1974
(Ladson et al. 2013, Table 3): the typical series of the generated tests."""

_EXACT: Final = Tolerance(
    abs=1e-300,
    rel=4.5e-16,
    reason="doubling every value of a series doubles every term of the recursion and "
    "of the sums exactly, so no rounding changes; a result below the normal floats "
    "keeps fewer bits",
)


# --- the Lyne and Hollick filter -----------------------------------------------------


def _pass(series: NDArray[np.float64], alpha: float) -> NDArray[np.float64]:
    """One forward pass: the baseflow of ``series`` (Ladson et al., 2013)."""
    # q₀ = Q₀; qₜ = α qₜ₋₁ + (1 + α)/2 (Qₜ − Qₜ₋₁): a linear recursion, unclamped.
    quick = np.empty_like(series)
    quick[0] = series[0]
    quick[1:] = lfilter(
        [(1.0 + alpha) / 2.0], [1.0, -alpha], np.diff(series), zi=[alpha * series[0]]
    )[0]
    base: NDArray[np.float64] = np.where(quick > 0, series - quick, series)
    return base


def _filtered(
    flows: NDArray[np.float64], alpha: float, passes: int
) -> NDArray[np.float64]:
    """Return the baseflow of a checked gapless series (spec ``lyne_hollick``)."""
    n = flows.size
    # Q₃₀ … Q₁, Q₀ … Qₙ₋₁, Qₙ₋₂ … Qₙ₋₃₁: the reflection leaves out the end values.
    head = flows[np.arange(REFLECTED_DAYS, 0, -1)]
    tail = flows[np.arange(n - 2, n - 2 - REFLECTED_DAYS, -1)]
    base = _pass(np.concatenate((head, flows, tail)), alpha)
    for _ in range((passes - 1) // 2):
        base = _pass(base[::-1], alpha)[::-1]
        base = _pass(base, alpha)
    out: NDArray[np.float64] = np.maximum(
        base[REFLECTED_DAYS : REFLECTED_DAYS + n], 0.0
    )
    return out


def _not_above_flow(inputs: Values, outputs: Values) -> float:
    """Return the largest excess of the baseflow over the flow, or below 0."""
    flows = inputs.array("values")
    base = outputs.array("baseflow")
    return float(max(np.max(base - flows), np.max(-base), 0.0))


LYNE_HOLLICK: Final = FormulaSpec(
    name="lyne_hollick",
    title="Baseflow of a daily series by the Lyne and Hollick filter "
    "(standard approach of Ladson et al. 2013)",
    function="hydrolog.statistics.baseflow.lyne_hollick_filter",
    family="scheme",
    equation=(
        "q_t = alpha q_(t-1) + (1 + alpha)/2 (Q_t - Q_(t-1)); b_t = Q_t - q_t if "
        "q_t > 0 else Q_t; passes alternately forward and backward, each on the "
        "baseflow of "
        "the pass before, over Q_31, ..., Q_2, Q_1, ..., Q_n, Q_(n-1), ..., Q_(n-30); "
        "q of each pass starts at the first value of its input; the baseflow of days "
        "1 to n after the last pass, below 0 set to 0"
    ),
    latex=(
        r"q_t = \alpha\,q_{t-1} + \frac{1 + \alpha}{2}\,(Q_t - Q_{t-1}),\quad "
        r"b_t = \begin{cases} Q_t - q_t & q_t > 0 \\ Q_t & q_t \le 0 \end{cases}"
    ),
    variables=(
        Variable(
            name="values",
            symbol="Q_t",
            unit=_UNIT,
            kind="real_array",
            description="Daily discharge, every day known, in time order.",
            physical=_ANY_FLOW,
            applicability="unstated",
            typical=_TYPICAL_FLOWS,
        ),
        Variable(
            name="alpha",
            symbol=r"\alpha",
            unit="-",
            description="Filter parameter.",
            physical=Range(
                low=0.0, high=1.0, low_inclusive=False, high_inclusive=False
            ),
            applicability=Range(
                low=0.9,
                high=0.98,
                source=_ladson(
                    "sect. 2.5, pp. 9-10: Nathan and McMahon (1990) found 0.9, 0.925 "
                    "and 0.95 satisfactory against manual separation, and 0.98 matched "
                    "chemical tracers better than 0.925 in 9 catchments; sect. 3.1, "
                    "p. 16: alpha 'anywhere in the range 0.9 to 0.98'"
                ),
            ),
            typical=Range(low=0.925, high=0.98, source=_HYDROLOG_DEFAULTS),
        ),
        Variable(
            name="passes",
            symbol="N",
            unit="-",
            kind="integer",
            description="Passes of the filter, alternately forward and backward.",
            physical=Range(
                low=1,
                test_high=99,
                test_reason="99 passes far exceed the 9 that Ladson et al. (2013, "
                "sect. 2.3) recommend for hourly data, and only cost time",
            ),
            applicability="unstated",
            typical=Range(low=3, high=3, source=_HYDROLOG_DEFAULTS),
        ),
    ),
    outputs=(
        Output(
            name="baseflow",
            unit=_UNIT,
            kind="real_array",
            symbol="b_t",
            description="Baseflow of each day, in the unit of the series.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        _ladson(
            "sect. 1.1, eqs. 1 and 2 (the filter); sect. 2.1 to 2.3 (reflection, "
            "initial values, passes); sect. 3, Tables 3 and 4 (the worked example)"
        ),
        _ladson_code("BFI.R: FirstPass, BackwardPass, ForwardPass and BFI.calc"),
        _NATHAN_MCMAHON,
        _ARR_P7,
    ),
    constraints=(
        Constraint(
            name="longer_than_reflection",
            cls="precondition",
            check=lambda x: x.array("values").size > REFLECTED_DAYS,
            text="n > 30",
            source=_ladson(
                "sect. 2.1, p. 7: 'the data set must be longer than the amount of "
                "reflection'; BFI.R, l. 297"
            ),
            satisfied={"values": [float(day % 7) for day in range(32)]},
            violated={"values": [float(day % 7) for day in range(30)]},
            boundary={"values": [float(day % 7) for day in range(31)]},
        ),
        Constraint(
            name="odd_passes",
            cls="precondition",
            check=lambda x: x.integer("passes") >= 3 and x.integer("passes") % 2 == 1,
            text="passes odd and passes >= 3",
            source=_ladson(
                "sect. 2.2 and 2.3, pp. 8-9: three passes for daily data, in order "
                "forward, backward, forward; BFI.R, l. 290: 'passes must be odd and "
                "greater than 2'"
            ),
            satisfied={"passes": 5},
            violated={"passes": 4},
            boundary={"passes": 3},
        ),
    ),
    constants=(
        Constant(
            name="reflected_values",
            value=float(REFLECTED_DAYS),
            unit="d",
            symbol="30",
            source=_ladson("sect. 2.1, pp. 6-7; BFI.R, n.reflect = 30"),
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={"baseflow": 1.0},
                tolerance=_EXACT,
            ),
        ),
        conservation=(
            Conservation(
                name="baseflow_within_flow",
                text="0 <= b_t <= Q_t on every day: each pass takes a positive "
                "quickflow away from its input (eq. 2) and the last sets b < 0 to 0",
                residual=_not_above_flow,
                tolerance=Tolerance(
                    abs=0.0,
                    reason="Q - q with q > 0 rounds to at most Q, and max(b, 0) is "
                    "exact: the bounds hold in floating point without slack",
                ),
            ),
        ),
        limits=(
            Limit(
                name="no_flow",
                text="a series without flow has no baseflow",
                inputs={"values": [0.0] * 40},
                expected={"baseflow": [0.0] * 40},
                tolerance=Tolerance(
                    abs=0.0, reason="every term of the recursion is exactly 0"
                ),
            ),
        ),
    ),
    validation=(
        "Ladson et al. (2013, sect. 2.5, Table 2, Fig. 2): on 9 Australian catchments "
        "the BFI with alpha 0.98 matched chemical-tracer estimates better than with "
        "0.925, with large scatter; Nathan and McMahon (1990) found alpha 0.9 to 0.95 "
        "satisfactory against manual separation on 122 catchments of 4.2 to 210 km2 "
        "(as quoted by Ladson et al.)"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "the standard approach as Ladson et al. worked it in their spreadsheet, Table "
        "4 and BFI.R: the quickflow is kept unclipped, negative too, as the state of "
        "the next day (Table 4, notes d to f), not set to 0 as the printed eq. 1 "
        "('q_f = 0 otherwise') and Murphy et al. (2009) eq. 7 ('subject to q_f(i) >= "
        "0') read",
        "30 values reflected at each end without repeating the end value: Q_31, ..., "
        "Q_2 before the series and Q_(n-1), ..., Q_(n-30) after it (sect. 2.1)",
        "the quickflow of each pass starts at the first value of its input: Q_31 for "
        "the first pass, the last baseflow of the pass before for a backward pass and "
        "its first for a forward one (sect. 2.2)",
        "an odd number of passes, alternately forward and backward, so that the last "
        "runs forward (sect. 2.3: three for daily data, nine for hourly)",
        "the baseflow below 0 is set to 0 after the last pass, and the reflected "
        "values are dropped (BFI.R, BFI.calc)",
        "the series in any unit, the baseflow in the same (sect. 2: 'In general the "
        "units of flow are not important')",
        "daily data without a gap: a gap is refused; baseflow_separation filters each "
        "gapless span of a series with gaps (Tier B baseflow_spans)",
    ),
    assumptions=(
        "the quickflow is the high-frequency part of the hydrograph and the baseflow "
        "the low-frequency rest; the filter has no physical basis (Ladson et al., "
        "sect. 1)",
        "the start of each pass is an end effect that the reflection damps but does "
        "not remove: a constant series of 10 gets the baseflow 6.78 on its first day "
        "and the BFI 0.983 over 400 days; Ladson et al. (sect. 2.1) found the effect "
        "of the reflection on the BFI negligible from about 300 days",
    ),
    traps={
        "stability_bound": "test_alpha_next_to_one_keeps_the_baseflow_within_the_flow: "
        "alpha just below 1, where the quickflow hardly decays, against the exact "
        "recursion; alpha = 1 is refused (range case alpha-physical_high)",
        "gap_propagation": "type case values-nan_element: a gap is refused; "
        "test_a_gap_parts_the_spans: baseflow_separation filters around it",
        "many_small_terms": "test_a_long_series_matches_the_exact_recursion: the "
        "quickflow sums alpha-weighted differences over 3,000 days, against Fraction "
        "arithmetic",
    },
    reference_cases=("tests/fixtures/formulas/baseflow-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the recursion of Ladson et al. (sect. 2.1 to 2.3) in exact "
            "rational arithmetic (fractions), written as loops over the padded series",
            test="tests/unit/test_formulas_baseflow.py::"
            "test_the_filter_is_the_exact_recursion",
        ),
        Oracle(
            kind="frozen",
            description="Ladson's BFI() of BFI.R (ReturnQbase = TRUE) run by R 4.5.3 "
            "on the Bass River and a seeded 730-day series, alpha 0.9 to 0.987, 3, 5 "
            "and 9 passes",
            test="tests/oracles/baseflow/lyne_hollick_r.csv",
            conventions=(
                "BFI.R and Hydrolog: 30 values reflected without the end value, the "
                "quickflow unclipped, starting at the first value of each pass's "
                "input, baseflow below 0 set to 0 after the last pass",
            ),
        ),
    ),
    base={"values": list(_BASS_RIVER), "alpha": BASEFLOW_ALPHA},
)


def lyne_hollick_filter(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
    *,
    alpha: float = BASEFLOW_ALPHA,
    passes: int = BASEFLOW_PASSES,
) -> NDArray[np.float64]:
    """Filter the baseflow of a gapless daily series, spec lyne_hollick.

    Parameters
    ----------
    values : array_like of float
        Daily discharge, every value known, longer than :data:`REFLECTED_DAYS`.
    alpha : float, optional
        Filter parameter, by default :data:`BASEFLOW_ALPHA`.
    passes : int, optional
        Odd number of passes, by default :data:`BASEFLOW_PASSES`.

    Returns
    -------
    ndarray of float
        The baseflow of each day, in the unit of ``values``.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs: a negative or non-finite value, a series
        too short, ``alpha`` outside its range or ``passes`` not odd from three.

    Warns
    -----
    OutsideApplicability
        If ``alpha`` lies outside the values its sources validated.
    """
    x = checked_inputs(LYNE_HOLLICK, values=values, alpha=alpha, passes=passes)
    base = _filtered(x.array("values"), x.real("alpha"), x.integer("passes"))
    return checked_outputs(LYNE_HOLLICK, {"baseflow": base}).array("baseflow")


# --- the baseflow index ------------------------------------------------------------


def _counted(x: Values) -> NDArray[np.bool_]:
    """Return the days with both a discharge and a baseflow."""
    return np.isfinite(x.array("values")) & np.isfinite(x.array("baseflow"))


def _same_days(x: Values) -> bool:
    return bool(x.array("values").shape == x.array("baseflow").shape)


def _within_flow(x: Values) -> bool:
    if not _same_days(x):
        return True  # the precondition same_days refuses it
    days = _counted(x)
    return bool(np.all(x.array("baseflow")[days] <= x.array("values")[days]))


def _flowing(x: Values) -> bool:
    return bool(np.any(x.array("values")[_counted(x)] > 0.0))


def _baseflow_of_bass_river() -> list[float]:
    """Return the baseflow of the typical series with Ladson et al.'s alpha."""
    base = _filtered(np.array(_BASS_RIVER), 0.98, BASEFLOW_PASSES)
    return [float(value) for value in base]


BASEFLOW_INDEX: Final = FormulaSpec(
    name="baseflow_index",
    title="Baseflow index: the volume of baseflow over the volume of flow",
    function="hydrolog.statistics.baseflow.baseflow_index",
    family="index",
    equation="BFI = sum(b_t) / sum(Q_t) over the days with both values",
    latex=r"\mathrm{BFI} = \frac{\sum_t b_t}{\sum_t Q_t}",
    variables=(
        Variable(
            name="values",
            symbol="Q_t",
            unit=_UNIT,
            kind="real_array",
            description="Daily discharge; a gap (NaN) is a day without a value.",
            physical=_ANY_FLOW,
            applicability="unstated",
            typical=_TYPICAL_FLOWS,
            gaps_allowed=True,
        ),
        Variable(
            name="baseflow",
            symbol="b_t",
            unit=_UNIT,
            kind="real_array",
            description="Baseflow of the same days; a gap is a day without one.",
            physical=_ANY_FLOW,
            applicability="unstated",
            typical=_TYPICAL_FLOWS,
            gaps_allowed=True,
        ),
    ),
    outputs=(
        Output(
            name="bfi",
            unit="-",
            symbol="BFI",
            description="Share of the baseflow in the volume of flow.",
            physical=Range(low=0.0, high=1.0),
        ),
    ),
    sources=(
        _ladson(
            "sect. 1.1, p. 5: 'the ratio of the baseflow volume (calculated from q_b) "
            "to the volume of streamflow (q) over a specified period'; sect. 2.4, "
            "p. 9: 'the sum of baseflow divided by the sum of total flow over the "
            "period of available raw data segments'"
        ),
        _ladson_code("BFI.R, BFI.calc: BFI.value <- sum(Qbase)/sum(Qin)"),
        _wmo_1029(
            "sect. 5.2, pp. 43-44: 'BFI = V_baseflow/V_total'; annual BFI from the "
            "volumes of each year"
        ),
    ),
    constraints=(
        Constraint(
            name="baseflow_not_above_flow",
            cls="physical",
            check=_within_flow,
            text="b_t <= Q_t on every day with both values",
            source=_ladson("sect. 1.1, eq. 2: q_b = q - q_f with q_f >= 0"),
            satisfied={"values": [2.0, 4.0], "baseflow": [2.0, 1.0]},
            violated={"values": [2.0, 4.0], "baseflow": [2.5, 1.0]},
            boundary={"values": [2.0, 4.0], "baseflow": [2.0, 4.0]},
        ),
        Constraint(
            name="same_days",
            cls="precondition",
            check=_same_days,
            text="len(b) = len(Q)",
            source=_ladson(
                "sect. 2.4, p. 9: baseflow statistics 'only from time steps in which "
                "raw data were available'"
            ),
            satisfied={"values": [2.0, 4.0], "baseflow": [1.0, 2.0]},
            violated={"values": [2.0, 4.0], "baseflow": [1.0]},
        ),
        Constraint(
            name="positive_flow_volume",
            cls="precondition",
            check=_flowing,
            text="sum(Q_t) > 0",
            source=_ladson(
                "sect. 1.1, p. 5: a ratio to the volume of streamflow, undefined "
                "without flow"
            ),
            satisfied={"values": [0.0, 1.0], "baseflow": [0.0, 1.0]},
            violated={"values": [0.0, 0.0], "baseflow": [0.0, 0.0]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"baseflow": 1, "values": -1},
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0, "baseflow": 1.0},
                outputs={"bfi": 0.0},
                tolerance=_EXACT,
            ),
        ),
        limits=(
            Limit(
                name="all_baseflow",
                text="a flow that is all baseflow has BFI = 1",
                inputs={"values": [3.0, 7.0, 5.0], "baseflow": [3.0, 7.0, 5.0]},
                expected={"bfi": 1.0},
                tolerance=Tolerance(abs=0.0, reason="the two sums are the same sum"),
            ),
            Limit(
                name="no_baseflow",
                text="a flow without baseflow has BFI = 0",
                inputs={"values": [3.0, 7.0, 5.0], "baseflow": [0.0, 0.0, 0.0]},
                expected={"bfi": 0.0},
                tolerance=Tolerance(abs=0.0, reason="a zero sum over a positive one"),
            ),
        ),
    ),
    validation="none: the definition of the index",
    formula_version=1,
    status="referenced",
    conventions=(
        "the volumes are the sums of the daily values (each day the same length), "
        "summed exactly once rounded (math.fsum)",
        "a day counts when it has both a discharge and a baseflow; with gaps the "
        "index is the ratio of the sums over the days with values (Ladson et al., "
        "sect. 2.4), not the mean of the spans' indices weighted by their lengths "
        "that BFI.R computes",
        "the series in any unit: the index has none",
    ),
    traps={
        "singular_at_bound": "constraint case positive_flow_volume-violated: no flow "
        "is refused before the division; test_a_trickle_has_a_finite_index: the "
        "smallest flows divide without underflow",
        "gap_propagation": "test_a_day_without_a_value_is_left_out: a gap in either "
        "series leaves the day out of both sums",
        "many_small_terms": "test_a_long_series_sums_exactly: 50,000 days against the "
        "exact rational sums",
    },
    reference_cases=(
        "tests/fixtures/formulas/baseflow-cases.json",
        "tests/fixtures/formulas/camels-pl-cases.json",
    ),
    oracles=(
        Oracle(
            kind="exact",
            description="the ratio of the sums in exact rational arithmetic "
            "(fractions)",
            test="tests/unit/test_formulas_baseflow.py::"
            "test_the_index_is_the_exact_ratio",
        ),
        Oracle(
            kind="frozen",
            description="the BFI that Ladson's BFI() of BFI.R reports, run by R "
            "4.5.3, of the filter's baseflow",
            test="tests/oracles/baseflow/lyne_hollick_bfi_r.csv",
            conventions=(
                "BFI.R: sum(Qbase)/sum(Qin) of a gapless series, the spec's ratio",
            ),
        ),
    ),
    base={"values": list(_BASS_RIVER), "baseflow": _baseflow_of_bass_river()},
)


def baseflow_index(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
    baseflow: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> float:
    """Return the baseflow index of a daily series, spec baseflow_index.

    Parameters
    ----------
    values : array_like of float
        Daily discharge; ``NaN`` marks a day without a value.
    baseflow : array_like of float
        The baseflow of the same days, at most the discharge.

    Returns
    -------
    float
        The share of the baseflow in the volume of flow.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs: a negative or non-finite value, a baseflow
        above the discharge, series of different lengths or no flow.
    """
    x = checked_inputs(BASEFLOW_INDEX, values=values, baseflow=baseflow)
    days = _counted(x)
    bfi = math.fsum(x.array("baseflow")[days]) / math.fsum(x.array("values")[days])
    return checked_outputs(BASEFLOW_INDEX, {"bfi": bfi}).real("bfi")


# --- the recession constant ---------------------------------------------------------


def _recession_runs(
    flows: NDArray[np.float64], min_days: int
) -> list[NDArray[np.float64]]:
    """Return the ratios Qₜ₊₁ / Qₜ of each run of at least ``min_days`` falls."""
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        ratio = flows[1:] / flows[:-1]
        falling = np.isfinite(ratio) & (ratio < 1.0) & (flows[:-1] > 0)
    padded = np.concatenate(([False], falling, [False]))
    edges = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    return [ratio[s:e] for s, e in zip(starts, ends, strict=True) if e - s >= min_days]


def _has_recession(x: Values) -> bool:
    return bool(_recession_runs(x.array("values"), x.integer("min_days")))


_RECESSION_BASE: Final = [
    *(100.0 * 0.95**day for day in range(11)),
    150.0,
    *(80.0 * 0.95**day for day in range(11)),
]
"""Two exponential recessions of k = 0.95 parted by a rise: the analytic case of the
research of 2026-11-18 (RECESSION-EXACT-EXPONENTIAL)."""


RECESSION: Final = FormulaSpec(
    name="recession_constant",
    title="Recession constant of the total flow: the median daily ratio of runs of "
    "falling flow",
    function="hydrolog.statistics.baseflow.recession_ratio",
    family="statistic",
    equation=(
        "k = median of Q_(t+1) / Q_t over the runs of at least min_days consecutive "
        "days with Q_t > 0 and Q_(t+1) < Q_t; half-life = ln 2 / (-ln k) (0 for k = 0)"
    ),
    latex=(
        r"k = \operatorname{median}\left\{\frac{Q_{t+1}}{Q_t}\right\},\quad "
        r"T_{1/2} = \frac{\ln 2}{-\ln k}"
    ),
    variables=(
        Variable(
            name="values",
            symbol="Q_t",
            unit=_UNIT,
            kind="real_array",
            description="Daily discharge on consecutive days; a gap (NaN) is a day "
            "without a value.",
            physical=_ANY_FLOW,
            applicability="unstated",
            typical=_TYPICAL_FLOWS,
            gaps_allowed=True,
        ),
        Variable(
            name="min_days",
            symbol="m",
            unit="d",
            kind="integer",
            description="Shortest recession segment: falls in a row.",
            physical=Range(
                low=1,
                test_high=365,
                test_reason="a segment of a year of falling daily flow; longer ones "
                "only test the count",
            ),
            applicability="unstated",
            typical=Range(low=5, high=5, source=_HYDROLOG_DEFAULTS),
        ),
    ),
    outputs=(
        Output(
            name="k",
            unit="-",
            symbol="k",
            description="Daily recession constant of the total flow.",
            physical=Range(low=0.0, high=1.0, high_inclusive=False),
        ),
        Output(
            name="half_life_days",
            unit="d",
            symbol="T_{1/2}",
            description="Days in which such a recession halves the flow.",
            physical=Range(low=0.0),
        ),
        Output(
            name="n_segments",
            unit="-",
            kind="integer",
            description="Recession segments found.",
            physical=Range(low=1),
        ),
    ),
    sources=(
        _wmo_1029(
            "sect. 5.3, p. 45, eqs. 5.1 to 5.3: Q_t = Q_0 exp(-t/C), k = Q_t/Q_(t-1), "
            "C = -dt/ln(k); 'A minimum length in the order of five to seven days is, "
            "however, commonly used'"
        ),
    ),
    constraints=(
        Constraint(
            name="recession_segment",
            cls="precondition",
            check=_has_recession,
            text="a run of at least min_days days with 0 < Q_(t+1) / Q_t < 1",
            source=_wmo_1029(
                "sect. 5.3, p. 45: the recession is analysed on segments of a minimum "
                "length"
            ),
            satisfied={"min_days": 5},
            violated={"min_days": 12},
            boundary={"min_days": 11},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={"k": 0.0, "half_life_days": 0.0},
                tolerance=_EXACT,
            ),
        ),
        limits=(
            Limit(
                name="exponential_recession",
                text="two recessions Q_t = Q_0 0.95^t parted by a rise: k = 0.95 and "
                "the half-life ln 2 / (-ln 0.95), from both segments",
                inputs={"values": _RECESSION_BASE, "min_days": 5},
                expected={
                    "k": 0.95,
                    "half_life_days": math.log(2.0) / -math.log(0.95),
                    "n_segments": 2,
                },
                tolerance=Tolerance(
                    rel=1e-14,
                    reason="each ratio of the rounded powers 0.95^(t+1) and 0.95^t "
                    "differs from 0.95 by a few ulp; ln k magnifies a relative "
                    "error of k by 1 / ln(1/0.95) = 19.5 in the half-life",
                ),
                source=_wmo_1029("sect. 5.3, p. 45, eqs. 5.1 to 5.3"),
            ),
        ),
    ),
    validation=(
        "none: the median ratio of the total flow is Hydrolog's own estimator; on "
        "WMO-No. 1029's Ngaruroro example (1963-1989) it gives k = 0.932 where WMO's "
        "master recession curve gives 0.9602 and lfstat's MRC 0.954 (the research of "
        "2026-11-18): its segments include the quickflow after a peak"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        "k is the daily ratio Q_(t+1) / Q_t of WMO-No. 1029 eq. 5.2, and the "
        "half-life ln 2 / (-ln k) is C ln 2 of its eq. 5.3",
        "segments of Hydrolog's own rule: every run of at least min_days falls, from "
        "the first day after a peak, no threshold (WMO starts below Q70 and two days "
        "after a peak, on segments of seven days, and fits them by regression)",
        "the median of all the ratios of all the segments pooled, not a regression "
        "through the origin (WMO's master recession curve) nor the mean of the "
        "segments' constants (WMO's individual recession segments)",
        "a fall is strict: a day of equal flow (a tie) ends a run, as a rise does",
        "a day without a value or a day without flow (Q_t = 0) ends a run; a fall to "
        "0 is the last ratio of its run, so k = 0 and a half-life of 0 only when "
        "min_days is 1",
    ),
    assumptions=(
        "the recession is exponential within each segment (WMO-No. 1029 eq. 5.1)",
        "the series is daily: k is per day and the half-life in days",
    ),
    traps={
        "singular_at_bound": "test_a_ratio_next_to_one_has_a_finite_half_life and "
        "test_a_fall_to_no_flow_has_a_half_life_of_zero: ln k at both ends of (0, 1)",
        "gap_propagation": "test_a_gap_ends_a_segment: a day without a value ends a "
        "run and is never a ratio",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="the runs found by a scan of the days and the median of "
            "their ratios in exact rational arithmetic (fractions, statistics.median)",
            test="tests/unit/test_formulas_baseflow.py::"
            "test_the_recession_constant_is_the_exact_median",
        ),
    ),
    base={"values": list(_RECESSION_BASE), "min_days": MIN_RECESSION_DAYS},
)


def recession_ratio(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
    *,
    min_days: int = MIN_RECESSION_DAYS,
) -> RecessionConstant:
    """Return the recession constant of the total flow, spec recession_constant.

    Parameters
    ----------
    values : array_like of float
        Daily discharge on consecutive days; ``NaN`` marks a day without a value,
        which ends a segment.
    min_days : int, optional
        Shortest segment, falls in a row, by default :data:`MIN_RECESSION_DAYS`.

    Returns
    -------
    RecessionConstant
        The median ratio of the segments, the half-life and the number of segments.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs: a negative or infinite value, ``min_days``
        below one, or no recession segment (precondition ``recession_segment``).
    """
    x = checked_inputs(RECESSION, values=values, min_days=min_days)
    runs = _recession_runs(x.array("values"), x.integer("min_days"))
    k = float(np.median(np.concatenate(runs)))
    half_life = math.log(2.0) / -math.log(k) if k > 0.0 else 0.0
    out = checked_outputs(
        RECESSION, {"k": k, "half_life_days": half_life, "n_segments": len(runs)}
    )
    return RecessionConstant(
        k=out.real("k"),
        half_life_days=out.real("half_life_days"),
        n_segments=out.integer("n_segments"),
    )


def recession_constant(
    discharge: NDArray[np.float64], *, min_days: int = MIN_RECESSION_DAYS
) -> RecessionConstant:
    """Compute the recession constant of the total flow of a daily series.

    k is the median of the daily ratios Qₜ₊₁ / Qₜ over the runs of at least
    ``min_days`` consecutive falls of the flow, the daily recession constant of
    Q_t = Q_0 k^t (WMO No. 1029, 2009, sec. 5.3, Eq. 5.1–5.3), by
    :func:`recession_ratio` (spec ``recession_constant``). The segments are
    Hydrolog's own rule: they start at any fall, the first days after a peak
    (quickflow) included, so k describes the recession of the total flow and is
    smaller (a faster recession) than the baseflow recession constant of WMO's
    master recession curve, built from 7-day segments below Q70 without the days
    right after a peak.

    Parameters
    ----------
    discharge : NDArray[np.float64]
        Daily discharge on a calendar of consecutive days; ``NaN`` marks a day
        without a value, which ends a segment.
    min_days : int, optional
        Shortest segment: days of falling flow in a row, by default 5.

    Returns
    -------
    RecessionConstant
        The median ratio Qₜ₊₁ / Qₜ of the segments, the half-life and the number of
        segments; ``k`` and ``half_life_days`` are ``None`` without a segment.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the series: a negative or infinite value, or
        ``min_days`` below 1.
    """
    try:
        return recession_ratio(discharge, min_days=min_days)
    except InvalidParameterError as exc:
        if exc.details.get("constraint") != "recession_segment":
            raise
    return RecessionConstant(k=None, half_life_days=None, n_segments=0)


# --- a daily series with gaps ---------------------------------------------------------


def _year_index(flows: NDArray[np.float64], base: NDArray[np.float64]) -> float | None:
    """Return the index of a year's days, ``None`` when no water flowed on them."""
    try:
        return baseflow_index(flows, base)
    except InvalidParameterError as exc:
        if exc.details.get("constraint") != "positive_flow_volume":
            raise
    return None


def baseflow_separation(
    discharge: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    *,
    alpha: float = BASEFLOW_ALPHA,
    passes: int = BASEFLOW_PASSES,
    series_year: int | None = None,
) -> BaseflowSeparation:
    """Separate the baseflow of a daily discharge series.

    Each gapless span of at least :data:`MIN_SPAN_DAYS` days is filtered by
    :func:`lyne_hollick_filter`; the baseflow index of the period and of each year
    is :func:`baseflow_index` of their days with a baseflow, and the recession
    constant :func:`recession_constant` of the whole series (Tier B rows of
    :data:`TIER_B`).

    Parameters
    ----------
    discharge : NDArray[np.float64]
        Daily discharge [m³/s]; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates, strictly increasing (days may be absent).
    alpha : float, optional
        Filter parameter in (0, 1), by default 0.925.
    passes : int, optional
        Odd number of passes, at least 3, by default 3.
    series_year : int, optional
        Hydrological year of the daily baseflow in the result; by default the last
        complete year (every day with a value), or the last year with a baseflow.

    Returns
    -------
    BaseflowSeparation
        The baseflow index of the period and of its years, the recession constant
        and the daily baseflow of ``series_year``.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, no gapless span has
        :data:`MIN_SPAN_DAYS` days or ``series_year`` has no value; or if a spec
        refuses the series or the options: a negative discharge, ``alpha`` or
        ``passes`` out of range, or no flow on the days with a baseflow
        (precondition ``positive_flow_volume`` of ``baseflow_index``).
    """
    flows = np.asarray(discharge, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[D]")
    if flows.size == 0 or flows.size != days.size:
        raise InvalidParameterError(
            "discharge and dates must be non-empty and of the same length"
        )
    calendar, daily = on_daily_calendar(flows, days)
    known = np.isfinite(daily)
    padded = np.concatenate(([False], known, [False]))
    edges = np.diff(padded.astype(np.int8))
    base = np.full(daily.shape, np.nan)
    spans = 0
    for start, end in zip(
        np.flatnonzero(edges == 1), np.flatnonzero(edges == -1), strict=True
    ):
        if end - start >= MIN_SPAN_DAYS:
            base[start:end] = lyne_hollick_filter(
                daily[start:end], alpha=alpha, passes=passes
            )
            spans += 1
    if spans == 0:
        raise InvalidParameterError(
            f"No gapless span of at least {MIN_SPAN_DAYS} days to filter"
        )
    filtered = np.isfinite(base)
    bfi = baseflow_index(daily[filtered], base[filtered])
    year_of_day = hydrological_year(calendar)
    present = np.unique(year_of_day[known])
    rows: list[BaseflowYear] = []
    complete: list[int] = []
    for year in present.tolist():
        in_year = year_of_day == year
        mine = in_year & filtered
        count = int(mine.sum())
        length = int(days_in_hydrological_year(np.array([year]))[0])
        if int((in_year & known).sum()) == length:
            complete.append(int(year))
        if count < MIN_YEAR_DAYS:
            continue
        rows.append(
            BaseflowYear(
                year=int(year),
                bfi=_year_index(daily[mine], base[mine]),
                n_values=count,
                baseflow_mean=float(base[mine].mean()),
                discharge_mean=float(daily[mine].mean()),
            )
        )
    if series_year is None:
        with_base = np.unique(year_of_day[filtered])
        series_year = complete[-1] if complete else int(with_base[-1])
    elif series_year not in set(present.tolist()):
        raise InvalidParameterError(
            f"series_year {series_year} has no value in the series"
        )
    first_day = hydrological_year_start(series_year)
    length = int(days_in_hydrological_year(np.array([series_year]))[0])
    year_days = first_day + np.arange(length)
    year_base = np.full(length, np.nan)
    inside = (calendar >= year_days[0]) & (calendar <= year_days[-1])
    year_base[(calendar[inside] - first_day).astype(np.int64)] = base[inside]
    return BaseflowSeparation(
        alpha=float(alpha),
        passes=int(passes),
        first_year=int(present[0]),
        last_year=int(present[-1]),
        period_years=int(present.size),
        bfi=bfi,
        n_values=int(filtered.sum()),
        n_spans=spans,
        years=rows,
        recession=recession_constant(daily),
        series_year=int(series_year),
        series_dates=[str(day) for day in year_days],
        series_baseflow=[
            float(value) if np.isfinite(value) else None for value in year_base
        ],
    )


# --- the computation standard: Tier B -------------------------------------------------

TIER_B: Final = (
    TierBSpec(
        name="baseflow_spans",
        function="hydrolog.statistics.baseflow.baseflow_separation",
        definition="the daily series is laid on a calendar of consecutive days (an "
        "absent date is a day without a value); each gapless span of at least 60 days "
        "is filtered on its own (spec lyne_hollick), reflected at both of its ends; a "
        "day of a shorter span has no baseflow; series_baseflow is the baseflow of "
        "each day of series_year, by default the last complete hydrological year",
        convention="spans of at least 60 days are Hydrolog's own rule; Ladson et al. "
        "(2013, sect. 2.4) filter every segment of non-missing values and their "
        "BFI.R every one longer than the 30 reflected values",
        source=_ladson(
            "sect. 2.4, p. 9: 'Flow data should be divided into segments of "
            "non-missing values ... data should be reflected at each end of each "
            "segment'"
        ),
        constants=(
            Constant(
                name="min_span_days",
                value=float(MIN_SPAN_DAYS),
                unit="d",
                symbol="60",
                source=_ADR_0031,
            ),
        ),
    ),
    TierBSpec(
        name="baseflow_index_by_year",
        function="hydrolog.statistics.baseflow.baseflow_separation",
        definition="the baseflow index of the period and of each hydrological year "
        "(1 November - 31 October, named after its end) is the index (spec "
        "baseflow_index) of their days with a baseflow; a year needs 300 such days "
        "for an index of its own, and a year without flow on them has none (null); "
        "a period without flow on them is refused",
        convention="the ratio of the volumes over the days with a baseflow (Ladson et "
        "al., sect. 2.4; WMO-No. 1029, sect. 5.2), not BFI.R's mean of the spans' "
        "indices weighted by their lengths; 300 days a year is Hydrolog's own rule",
        source=_wmo_1029(
            "sect. 5.2, p. 44: 'Annual BFI values can be determined by summing up the "
            "base-flow and total-flow volume separately for each year'"
        ),
        constants=(
            Constant(
                name="min_year_days",
                value=float(MIN_YEAR_DAYS),
                unit="d",
                symbol="300",
                source=_ADR_0031,
            ),
        ),
    ),
    TierBSpec(
        name="recession_without_segment",
        function="hydrolog.statistics.baseflow.recession_constant",
        definition="the recession constant of a series (spec recession_constant) "
        "with k and the half-life null and no segments when the series has no "
        "recession segment",
        convention="the recession of baseflow_separation is that of the whole daily "
        "calendar of the series, gaps included as ends of segments",
        source=_wmo_1029("sect. 5.3, p. 45"),
    ),
)
"""The Tier B formulas of the module (Nogat CMP-2.2)."""

SPECS: Final = (LYNE_HOLLICK, BASEFLOW_INDEX, RECESSION)
"""The Tier A formulas of the module (Nogat CMP-2.1)."""
