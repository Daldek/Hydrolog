"""Hydrological signatures of a daily discharge series, after the CAMELS data sets.

A signature condenses a daily record into one number that compares catchments (Addor
et al., 2017, sect. 5; Westerberg and McMillan, 2015). Five of the signatures that the
CAMELS data sets publish for every gauge are Tier A formulas of Nogat's computation
standard here, each declared by its spec:

* :data:`FDC_SLOPE` (:func:`fdc_slope`): the slope of the duration curve between two
  exceedance percentages in log space, S = [ln Q(p₁) − ln Q(p₂)] / [(p₂ − p₁)/100],
  33 and 66 % by Sawicz et al. (2011, eq. 3), on Hydrolog's duration curve
  (spec ``exceedance_values``);
* :data:`HIGH_FLOW_DAYS` (:func:`high_flow_days`): the days per year with a flow above
  nine times the median and the mean length of their runs (Clausen and Biggs, 2000, as
  Westerberg and McMillan, 2015, and Addor et al., 2017, take them);
* :data:`LOW_FLOW_DAYS` (:func:`low_flow_days`): the days per year with a flow below a
  fifth of the mean and the mean length of their runs (after Olden and Poff, 2003);
* :data:`ZERO_FLOW_FRACTION` (:func:`zero_flow_fraction`): the share of the days without
  flow;
* :data:`HALF_FLOW_DATE` (:func:`half_flow_date`): the day of a year on which the flow
  summed from its first day first exceeds half of the year's (Court, 1962).

The quantiles Q5 and Q95 of CAMELS are values of the duration curve (spec
``exceedance_values`` at 95 and 5 %), and the baseflow index is that of
:mod:`hydrolog.statistics.baseflow`. The formulas take a sample, never a calendar
(ADR-0063): the days of a record in order, a day without a value NaN, or one year's
days for the half-flow date. The signatures of CAMELS-PL 2.1.0 (Brzezińska et al.,
2026) are their reference cases (``tests/fixtures/formulas/camels-pl-cases.json``),
with the sample CAMELS-PL computed each of them on and each step where its computation
and Hydrolog's part (ADR-0073).

Examples
--------
A curve q(m) = e^(−2 m / 100) of 99 values falls by 2 in log space per unit of the
exceedance probability:

>>> import numpy as np
>>> from hydrolog.statistics.signatures import (
...     fdc_slope, half_flow_date, high_flow_days, zero_flow_fraction)
>>> curve = np.exp(-2.0 * np.arange(1, 100) / 100.0)
>>> round(fdc_slope(curve), 12)
2.0
>>> found = high_flow_days([1.0] * 9 + [10.0, 10.0] + [1.0] * 9)
>>> found.days_per_year, found.mean_duration_days
(36.525, 2.0)
>>> zero_flow_fraction([0.0, 1.5, float("nan"), 2.0])
0.3333333333333333
>>> half_flow_date([1.0] * 365)
183

References
----------
Addor, N., Newman, A. J., Mizukami, N. & Clark, M. P. (2017): The CAMELS data set:
    catchment attributes and meteorology for large-sample studies. Hydrology and Earth
    System Sciences 21, 5293–5313.
Sawicz, K., Wagener, T., Sivapalan, M., Troch, P. A. & Carrillo, G. (2011): Catchment
    classification: empirical analysis of hydrologic similarity based on catchment
    function in the eastern USA. Hydrology and Earth System Sciences 15, 2895–2911.
Westerberg, I. K. & McMillan, H. K. (2015): Uncertainty in hydrological signatures.
    Hydrology and Earth System Sciences 19, 3951–3968.
Clausen, B. & Biggs, B. J. F. (2000): Flow variables for ecological studies in
    temperate streams: groupings based on covariance. Journal of Hydrology 237,
    184–197.
Olden, J. D. & Poff, N. L. (2003): Redundancy and the choice of hydrologic indices for
    characterizing streamflow regimes. River Research and Applications 19, 101–121.
Court, A. (1962): Measures of streamflow timing. Journal of Geophysical Research
    67(11), 4335–4339.
Brzezińska, W. et al. (2026): CAMELS-PL: hydro-meteorological time series and
    landscape attributes for 869 catchments in Poland, version 2.1.0. Zenodo,
    doi:10.5281/zenodo.23275336.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import accumulate
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
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
    Tolerance,
    Values,
    Variable,
)
from hydrolog.statistics.duration import _exceedance, _normalised, exceedance_values

__all__ = [
    "FDC_SLOPE",
    "HALF_FLOW_DATE",
    "HIGH_FLOW_DAYS",
    "LOW_FLOW_DAYS",
    "SPECS",
    "ZERO_FLOW_FRACTION",
    "FlowDays",
    "fdc_slope",
    "half_flow_date",
    "high_flow_days",
    "low_flow_days",
    "zero_flow_fraction",
]


@dataclass(frozen=True)
class FlowDays(JsonResultMixin):
    """The days of a series beyond a threshold: their frequency and their runs.

    Attributes
    ----------
    days_per_year : float
        The days beyond the threshold per year of 365.25 days of the days with a
        value [d/yr].
    mean_duration_days : float
        The mean length of the runs of such days, 0 without one [d].
    days : int
        The days beyond the threshold.
    events : int
        The runs of such days, a day without a value ending a run.
    """

    days_per_year: float
    mean_duration_days: float
    days: int
    events: int


# --- sources --------------------------------------------------------------------------

_ADDOR_CITATION: Final = (
    "Addor, N., Newman, A.J., Mizukami, N. and Clark, M.P. (2017). The CAMELS data "
    "set: catchment attributes and meteorology for large-sample studies. Hydrology "
    "and Earth System Sciences 21, 5293-5313"
)
_ADDOR_URL: Final = "https://doi.org/10.5194/hess-21-5293-2017"
_ADDOR_CODE_CITATION: Final = (
    "Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of "
    "CAMELS (Addor et al. 2017), github.com/naddor/camels"
)
_ADDOR_CODE_URL: Final = (
    "https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R"
)
_CAMELS_DE_CODE_CITATION: Final = (
    "Dolich, A. (2024). 08_hydrologic_attributes.ipynb, the code of the hydrologic "
    "attributes of CAMELS-DE version 1 (Loritz et al. 2024, ESSD 16, 5625-5642), "
    "github.com/CAMELS-DE/camels_de"
)
_CAMELS_DE_CODE_URL: Final = (
    "https://github.com/CAMELS-DE/camels_de/blob/main/version1/scripts/"
    "08_hydrologic_attributes.ipynb"
)
_CAMELS_PL_CITATION: Final = (
    "Brzezińska, W., Marcinkowski, P., Dolich, A., Perz, A. E., Maharjan, A., "
    "Piniewski, M., Kardel, I., Loritz, R. and Wrzesiński, D. (2026). CAMELS-PL: "
    "hydro-meteorological time series and landscape attributes for 869 catchments in "
    "Poland, version 2.1.0 [dataset], Zenodo record 23275336, CC BY 4.0"
)
_CAMELS_PL_URL: Final = "https://doi.org/10.5281/zenodo.23275336"


def _addor(locator: str) -> Source:
    return Source(citation=_ADDOR_CITATION, locator=locator, url=_ADDOR_URL)


def _addor_code(locator: str) -> Source:
    return Source(citation=_ADDOR_CODE_CITATION, locator=locator, url=_ADDOR_CODE_URL)


def _camels_de_code(locator: str) -> Source:
    return Source(
        citation=_CAMELS_DE_CODE_CITATION, locator=locator, url=_CAMELS_DE_CODE_URL
    )


_SAWICZ: Final = Source(
    citation="Sawicz, K., Wagener, T., Sivapalan, M., Troch, P.A. and Carrillo, G. "
    "(2011). Catchment classification: empirical analysis of hydrologic similarity "
    "based on catchment function in the eastern USA. Hydrology and Earth System "
    "Sciences 15, 2895-2911",
    locator="sect. 3.2, eq. 3, p. 2898: S_FDC = [ln(Q33%) - ln(Q66%)] / (0.66 - "
    "0.33), on the flow duration curve, 'the distribution of probabilities of "
    "streamflow being greater than or equal to a specified magnitude'",
    url="https://doi.org/10.5194/hess-15-2895-2011",
)
_WESTERBERG: Final = Source(
    citation="Westerberg, I.K. and McMillan, H.K. (2015). Uncertainty in hydrological "
    "signatures. Hydrology and Earth System Sciences 19, 3951-3968",
    locator="Table 2, p. 3956: QHF and QHD, the frequency and the duration of daily "
    "flows higher than 9 times the median daily flow (Clausen and Biggs 2000); QLF "
    "and QLD, of daily flows lower than 0.2 times the mean daily flow (Olden and Poff "
    "2003, who used a 5 % threshold)",
    url="https://doi.org/10.5194/hess-19-3951-2015",
)
_CLAUSEN_BIGGS: Final = Source(
    citation="Clausen, B. and Biggs, B.J.F. (2000). Flow variables for ecological "
    "studies in temperate streams: groupings based on covariance. Journal of "
    "Hydrology 237, 184-197",
    locator="the frequency of high flows above a multiple of the median flow, as "
    "Westerberg and McMillan (2015, Table 2) and Addor et al. (2017, Table 3) cite it",
    url="https://doi.org/10.1016/S0022-1694(00)00306-1",
    access="author-provided",
)
_OLDEN_POFF: Final = Source(
    citation="Olden, J.D. and Poff, N.L. (2003). Redundancy and the choice of "
    "hydrologic indices for characterizing streamflow regimes. River Research and "
    "Applications 19, 101-121",
    locator="the frequency and duration of low flows, as Westerberg and McMillan "
    "(2015, Table 2) and Addor et al. (2017, Table 3) cite it, with a threshold of 5 % "
    "of the mean, which they raise to 0.2 times the mean",
    url="https://doi.org/10.1002/rra.700",
)
_COURT: Final = Source(
    citation="Court, A. (1962). Measures of streamflow timing. Journal of Geophysical "
    "Research 67(11), 4335-4339",
    locator="the half-flow date, as Addor et al. (2017, Table 3) cite it",
    access="author-provided",
)
_CAMELS_PL_FLOWS: Final = Source(
    citation=_CAMELS_PL_CITATION,
    locator="discharge_vol_obs of the 13 gauges of tests/fixtures/camels_pl/ (5.93 to "
    "193,728 km2): 0 m3/s on days without flow (Brynica, Czarna, Gardęga, Noteć and "
    "five more) to 6430 m3/s (the Wisła at Tczew)",
    url=_CAMELS_PL_URL,
)
_SLOPE_PERCENTS: Final = Source(
    citation=_CAMELS_PL_CITATION,
    locator="CAMELS_PL_Data_Description.pdf, Table 7, slope_fdc between the 33rd and "
    "66th percentiles, the flows exceeded on 67 and 34 % of the days; Sawicz et al. "
    "(2011, eq. 3) take the flows exceeded on 33 and 66 %",
    url=_CAMELS_PL_URL,
)

_UNIT: Final = "m3/s"
"""The unit of the series in the documents: every signature here is free of the unit
of the series (their scalings), so a specific discharge in mm/d, as CAMELS gives it,
serves as well."""

_ANY_FLOW: Final = Range(
    low=0.0,
    test_high=1.0e6,
    test_reason=(
        "the signatures are free of the unit of the series (their scalings), so any "
        "bound tests their arithmetic: a million m3/s exceeds the discharge of every "
        "river (the Amazon's floods reach about 300,000 m3/s)"
    ),
)
"""A discharge: not negative, unbounded above."""

_TYPICAL_FLOWS: Final = Range(low=0.0, high=6430.0, source=_CAMELS_PL_FLOWS)
"""Daily discharges of the thirteen gauges of CAMELS-PL that the tests keep."""

_EXACT_SCALING: Final = Tolerance(
    abs=0.0,
    reason="the comparisons and sums run on the values divided by the power of two "
    "that brings the largest into [1/2, 1), the same numbers for the series and the "
    "series doubled, so the result is the same to the bit",
)

_HIGH_FLOW_MULTIPLE: Final = Constant(
    name="high_flow_multiple",
    value=Fraction(9),
    unit="-",
    symbol="9",
    source=_addor(
        "Table 3, p. 5300: high_q_freq, the frequency of high-flow days (> 9 times "
        "the median daily flow); confirmed by Westerberg and McMillan (2015), Table 2, "
        "p. 3956, QHF"
    ),
)
_LOW_FLOW_MULTIPLE: Final = Constant(
    name="low_flow_multiple",
    value=Fraction(1, 5),
    unit="-",
    symbol="0.2",
    source=_addor(
        "Table 3, p. 5300: low_q_freq, the frequency of low-flow days (< 0.2 times the "
        "mean daily flow); confirmed by Westerberg and McMillan (2015), Table 2, p. "
        "3956, QLF"
    ),
)
_DAYS_PER_YEAR: Final = Constant(
    name="days_per_year",
    value=Fraction(1461, 4),
    unit="d",
    symbol="365.25",
    source=_addor_code(
        "compute_hf_freq_dur and compute_lf_freq_dur: hf_freq <- sum(hf) / "
        "sum(avail_data) * 365.25; the same in the code of CAMELS-DE "
        "(08_hydrologic_attributes.ipynb): high_q_freq = hf.sum() / len(df) * 365.25"
    ),
)

HIGH_FLOW_MULTIPLE: Final = float(_HIGH_FLOW_MULTIPLE.value)
"""A high-flow day has a flow above this multiple of the median."""
LOW_FLOW_MULTIPLE: Final = float(_LOW_FLOW_MULTIPLE.value)
"""A low-flow day has a flow below this multiple of the mean."""
DAYS_PER_YEAR: Final = float(_DAYS_PER_YEAR.value)
"""The days of a year in the frequencies: the mean year of 1901–2099."""
SAWICZ_FROM_PERCENT: Final = 33.0
"""Exceedance percentage of the first point of Sawicz et al.'s slope."""
SAWICZ_TO_PERCENT: Final = 66.0
"""Exceedance percentage of the second point of Sawicz et al.'s slope."""


def _has_values(x: Values) -> bool:
    return bool(np.any(~np.isnan(x.array("values"))))


_HAS_VALUES: Final = Constraint(
    name="has_values",
    cls="precondition",
    check=_has_values,
    text="n >= 1: at least one day with a value",
    source=_addor_code(
        "find_avail_data_array: a signature needs the days with a value, NA without"
    ),
    satisfied={"values": [5.0, math.nan]},
    violated={"values": [math.nan, math.nan]},
)


def _known(x: Values) -> NDArray[np.float64]:
    """Return the days with a value, divided by the power of two of the largest."""
    data = x.array("values")
    scaled: NDArray[np.float64] = _normalised(data[~np.isnan(data)])[0]
    return scaled


# --- the slope of the duration curve ---------------------------------------------


def _curve_at(x: Values, percent: float) -> float:
    """Return the scaled duration curve at an exceedance percentage."""
    curve = Values(
        values=_known(x), exceedance_percent=np.array([percent], dtype=np.float64)
    )
    return float(_exceedance(curve)[0])


def _flow_at_both_points(x: Values) -> bool:
    if not _has_values(x):
        return True  # the precondition has_values refuses it
    return _curve_at(x, x.real("to_percent")) > 0.0


def _log_ratio(high: float, low: float) -> float:
    """Return ln(high / low) of two positive values, high >= low, without overflow."""
    high_mantissa, high_exponent = math.frexp(high)
    low_mantissa, low_exponent = math.frexp(low)
    return math.log(high_mantissa / low_mantissa) + (
        high_exponent - low_exponent
    ) * math.log(2.0)


def _exponential_curve(rate: float) -> list[float]:
    """Return the 99 values q(m) = exp(-rate m / 100) of a curve of slope ``rate``."""
    return [math.exp(-rate * m / 100.0) for m in range(1, 100)]


FDC_SLOPE: Final = FormulaSpec(
    name="fdc_slope",
    title="Slope of the duration curve between two exceedance percentages in log space",
    function="hydrolog.statistics.signatures.fdc_slope",
    family="index",
    equation=(
        "S = [ln Q(p_1) - ln Q(p_2)] / [(p_2 - p_1) / 100], Q(p) the value equalled or "
        "exceeded on p % of the days (spec exceedance_values), p_1 < p_2"
    ),
    latex=(r"S = \frac{\ln Q(p_1) - \ln Q(p_2)}{(p_2 - p_1)/100},\quad p_1 < p_2"),
    variables=(
        Variable(
            name="values",
            symbol="Q_t",
            unit=_UNIT,
            kind="real_array",
            description="The daily values of the series, in any order; NaN on a day "
            "without a value, which is left out.",
            physical=_ANY_FLOW,
            applicability="unstated",
            typical=_TYPICAL_FLOWS,
            gaps_allowed=True,
        ),
        Variable(
            name="from_percent",
            symbol="p_1",
            unit="%",
            description="Exceedance percentage of the first, higher point of the "
            "curve.",
            physical=Range(
                low=0.0, high=100.0, low_inclusive=False, high_inclusive=False
            ),
            applicability="unstated",
            typical=Range(low=33.0, high=34.0, source=_SLOPE_PERCENTS),
        ),
        Variable(
            name="to_percent",
            symbol="p_2",
            unit="%",
            description="Exceedance percentage of the second, lower point of the "
            "curve.",
            physical=Range(
                low=0.0, high=100.0, low_inclusive=False, high_inclusive=False
            ),
            applicability="unstated",
            typical=Range(low=66.0, high=67.0, source=_SLOPE_PERCENTS),
        ),
    ),
    outputs=(
        Output(
            name="slope",
            unit="-",
            symbol="S",
            description="The fall of the curve in log space per unit of the exceedance "
            "probability.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        _SAWICZ,
        _addor(
            "sect. 5.1, p. 5298: 'the slope of the flow duration curve ... between the "
            "log-transformed 33rd and 66th streamflow percentiles', undefined where "
            "the flow is 0 on more than a third of the days; Table 3, p. 5300, "
            "slope_fdc"
        ),
        _addor_code(
            "comp_s_fdc: sfdc_sawicz_2011 on the exceedance percentages 33 and 66, "
            "sfdc_addor_2017 on the quantiles 0.33 and 0.66, NA when q66 = 0"
        ),
    ),
    constraints=(
        _HAS_VALUES,
        Constraint(
            name="ordered_percents",
            cls="precondition",
            check=lambda x: x.real("from_percent") < x.real("to_percent"),
            text="p_1 < p_2",
            source=_SAWICZ,
            satisfied={"from_percent": 33.0, "to_percent": 66.0},
            violated={"from_percent": 67.0, "to_percent": 66.0},
            boundary={"from_percent": 66.0, "to_percent": 66.0},
            boundary_holds=False,
        ),
        Constraint(
            name="flow_at_both_points",
            cls="precondition",
            check=_flow_at_both_points,
            text="Q(p_2) > 0",
            source=_addor(
                "sect. 5.1, p. 5298: 'In intermittent streams, the frequency of days "
                "with no flow can be greater than 33 % ... Since the logarithm cannot "
                "be extracted, the slope of the flow duration curve is undefined'"
            ),
            satisfied={"values": [4.0, 3.0, 2.0, 1.0]},
            violated={"values": [4.0, 0.0, 0.0, 0.0]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={"slope": 0.0},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="constant_series",
                text="a series of equal values has a flat curve, S = 0",
                inputs={"values": [7.5] * 20},
                expected={"slope": 0.0},
                tolerance=Tolerance(
                    abs=0.0, reason="the two values of the curve are the same value"
                ),
            ),
            Limit(
                name="exponential_curve",
                text="99 values q(m) = exp(-2 m / 100) stand at their Weibull "
                "positions m / 100, so the slope from 33 to 66 % is 2",
                inputs={
                    "values": _exponential_curve(2.0),
                    "from_percent": 33.0,
                    "to_percent": 66.0,
                },
                expected={"slope": 2.0},
                tolerance=Tolerance(
                    abs=1e-14,
                    reason="exp rounds each value by half an ulp and log the ratio "
                    "by another: a few units in the last place of 0.66, over 0.33",
                ),
                source=_SAWICZ,
            ),
        ),
    ),
    validation=(
        "none: a descriptive statistic of the observed record; Sawicz et al. (2011) "
        "and Addor et al. (2017) relate it to catchment properties, not to an "
        "observation of the same quantity"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "Q(p) is Hydrolog's duration curve (spec exceedance_values): the value "
        "equalled or exceeded on p % of the days with a value, Weibull positions "
        "m / (n + 1) and linear interpolation; Sawicz et al. (2011) read the flows "
        "exceeded on 33 and 66 % of the days, the defaults",
        "Addor et al. (2017) and the codes of CAMELS-DE and CAMELS-PL take the "
        "non-exceedance quantiles 0.33 and 0.66, the flows exceeded on 67 and 34 % of "
        "the days ('slightly different', the code of CAMELS-US says): from_percent 34 "
        "and to_percent 67 give their slope",
        "zeros are values of the curve, as in Sawicz et al. and the code of CAMELS-US: "
        "a curve at 0 at p_2 is refused (precondition flow_at_both_points); the codes "
        "of CAMELS-DE and CAMELS-PL drop the days without flow first, which a caller "
        "does by passing the flows above 0",
        "the curve runs on the values divided by the power of two that brings the "
        "largest into [1/2, 1), and ln Q(p_1) - ln Q(p_2) is taken from their "
        "mantissas and exponents: the slope does not depend on the unit of the series "
        "and does not overflow",
        "Q(p_2) is held at most Q(p_1): the rounding of the interpolation could "
        "otherwise put a value a unit in the last place above the higher one",
        "a day without a value (NaN) is left out, n counts the days with a value",
    ),
    assumptions=(
        "the values are those of one station over one period: the slope describes that "
        "period's curve",
        "the curve between the two points is nearly straight in log space, which is "
        "why Sawicz et al. chose 33 and 66 %; other points give a slope of their part "
        "of the curve",
    ),
    traps={
        "difference_denominator": "constraint cases ordered_percents-boundary and "
        "-violated: p_1 = p_2 and p_1 > p_2 are refused before the division; "
        "test_close_percents_give_a_finite_slope",
        "singular_at_bound": "constraint case flow_at_both_points-violated: the "
        "logarithm of a curve at 0 is refused; test_a_tiny_flow_has_a_finite_slope "
        "takes the logarithm of the smallest positive values",
        "gap_propagation": "type case values-nan_element and "
        "test_a_day_without_a_value_is_left_out: a gap is left out, never a NaN slope",
    },
    reference_cases=("tests/fixtures/formulas/camels-pl-cases.json",),
    oracles=(
        Oracle(
            kind="established",
            description="numpy.quantile with method='weibull' (NumPy 2.5) at the "
            "non-exceedance probabilities 1 - p / 100 and math.log of their ratio",
            test="tests/unit/test_formulas_signatures.py::"
            "test_the_slope_is_numpys_weibull_curve",
            conventions=(
                "numpy's 'weibull' is Hyndman and Fan's type 6, the positions of "
                "exceedance_values counted from the other end",
            ),
        ),
    ),
    base={
        "values": [float(v) for v in np.linspace(0.0, 6430.0, 10)],
        "from_percent": SAWICZ_FROM_PERCENT,
        "to_percent": SAWICZ_TO_PERCENT,
    },
)


def fdc_slope(
    values: NDArray[np.float64] | Sequence[float],
    from_percent: float = SAWICZ_FROM_PERCENT,
    to_percent: float = SAWICZ_TO_PERCENT,
) -> float:
    """Return the slope of the duration curve between two points, spec fdc_slope.

    Parameters
    ----------
    values : array_like of float
        The daily values of the series; ``NaN`` marks a day without a value, which is
        left out.
    from_percent : float, optional
        Exceedance percentage of the higher point of the curve, by default
        :data:`SAWICZ_FROM_PERCENT`.
    to_percent : float, optional
        Exceedance percentage of the lower point, by default
        :data:`SAWICZ_TO_PERCENT`.

    Returns
    -------
    float
        The fall of the curve in log space per unit of the exceedance probability.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs: a negative or infinite value, a percentage
        outside the open interval of percentages, no day with a value, the points in
        the wrong order or no flow at the lower point.
    """
    x = checked_inputs(
        FDC_SLOPE, values=values, from_percent=from_percent, to_percent=to_percent
    )
    first, second = x.real("from_percent"), x.real("to_percent")
    high, low = (float(v) for v in exceedance_values(_known(x), [first, second]))
    slope = _log_ratio(high, min(low, high)) / ((second - first) / 100.0)
    return checked_outputs(FDC_SLOPE, {"slope": slope}).real("slope")


# --- the days beyond a threshold: high and low flows ------------------------------


def _runs(beyond: NDArray[np.bool_]) -> int:
    """Return the number of runs of consecutive days beyond the threshold."""
    padded = np.concatenate(([False], beyond))
    return int(np.count_nonzero(beyond & ~padded[:-1]))


def _flow_days(x: Values, beyond: NDArray[np.bool_]) -> FlowDays:
    """Return the frequency and the runs of the days beyond a threshold."""
    data = x.array("values")
    days = int(np.count_nonzero(beyond))
    events = _runs(beyond)
    known = int(np.count_nonzero(~np.isnan(data)))
    return FlowDays(
        days_per_year=days * DAYS_PER_YEAR / known,
        mean_duration_days=days / events if events else 0.0,
        days=days,
        events=events,
    )


def _scaled_series(x: Values) -> NDArray[np.float64]:
    """Return the series divided by the power of two of its largest value, NaN kept."""
    data = x.array("values")
    known = data[~np.isnan(data)]
    exponent = _normalised(known)[1]
    scaled: NDArray[np.float64] = np.ldexp(data, -exponent)
    return scaled


def _flow_days_outputs(name: str) -> tuple[Output, Output]:
    return (
        Output(
            name="days_per_year",
            unit="d/yr",
            symbol=f"F_{name}",
            description="The days beyond the threshold per year of the days with a "
            "value.",
            physical=Range(low=0.0, high=DAYS_PER_YEAR),
        ),
        Output(
            name="mean_duration_days",
            unit="d",
            symbol=f"D_{name}",
            description="The mean length of the runs of such days, 0 without one.",
            physical=Range(low=0.0),
        ),
    )


def _one_event(flows: list[float], days: int, length: int) -> Limit:
    return Limit(
        name="one_event",
        text=f"one run of {days} days beyond the threshold in {length} days with a "
        "value",
        inputs={"values": flows},
        expected={
            "days_per_year": days * DAYS_PER_YEAR / length,
            "mean_duration_days": float(days),
        },
        tolerance=Tolerance(
            abs=0.0,
            reason="the count, the run and their quotients are exact or one rounding "
            "of the same quotient",
        ),
    )


def _gap_parts_the_event(flows: list[float], length: int) -> Limit:
    return Limit(
        name="gap_parts_the_event",
        text="a day without a value inside a run ends it and is not counted: two "
        f"runs of one day in {length} days with a value",
        inputs={"values": flows},
        expected={
            "days_per_year": 2 * DAYS_PER_YEAR / length,
            "mean_duration_days": 1.0,
        },
        tolerance=Tolerance(abs=0.0, reason="one rounding of the same quotient"),
    )


_FLOW_DAYS_ORACLE: Final = Oracle(
    kind="algorithm",
    description="a loop over the days that counts each day beyond the threshold and "
    "each run of them, with the median and the mean in exact rational arithmetic "
    "(fractions)",
    test="tests/unit/test_formulas_signatures.py::test_the_flow_days_are_counted_day_by_day",
)

_FLOW_DAYS_CONVENTIONS: Final = (
    "the frequency counts per day with a value, times 365.25 days: Addor et al.'s code "
    "(sum(hf) / sum(avail_data) * 365.25); the codes of CAMELS-DE and CAMELS-PL divide "
    "by every day of their frame, the days without a value too",
    "an event is a run of consecutive days beyond the threshold, and a day without a "
    "value ends it, as in the code of CAMELS-DE; Addor et al.'s code drops such days "
    "and joins the runs around them",
    "the mean duration is the days beyond the threshold over the events; a series "
    "without such a day has the frequency 0 and the duration 0, as the codes of "
    "CAMELS-US, CAMELS-DE and CAMELS-PL give them",
    "the comparisons run on the values divided by the power of two that brings the "
    "largest into [1/2, 1): the same numbers for a series in any unit",
)

HIGH_FLOW_DAYS: Final = FormulaSpec(
    name="high_flow_days",
    title="High-flow days: their frequency and the mean duration of their runs",
    function="hydrolog.statistics.signatures.high_flow_days",
    family="index",
    equation=(
        "a high-flow day has Q_t > 9 median(Q); F = 365.25 N_h / n, n the days with a "
        "value; D = N_h / E, E the runs of consecutive high-flow days, D = 0 when E = 0"
    ),
    latex=(
        r"Q_t > 9\,\tilde{Q},\quad F = 365.25\,\frac{N_h}{n},\quad "
        r"D = \frac{N_h}{E}"
    ),
    variables=(
        Variable(
            name="values",
            symbol="Q_t",
            unit=_UNIT,
            kind="real_array",
            description="Daily discharge in time order; NaN on a day without a value.",
            physical=_ANY_FLOW,
            applicability="unstated",
            typical=_TYPICAL_FLOWS,
            gaps_allowed=True,
        ),
    ),
    outputs=_flow_days_outputs("h"),
    sources=(
        _addor("Table 3, p. 5300: high_q_freq and high_q_dur"),
        _WESTERBERG,
        _CLAUSEN_BIGGS,
        _addor_code("compute_hf_freq_dur: hf <- q > 9 * median(q)"),
    ),
    constraints=(_HAS_VALUES,),
    constants=(_HIGH_FLOW_MULTIPLE, _DAYS_PER_YEAR),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={"days_per_year": 0.0, "mean_duration_days": 0.0},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="constant_series",
                text="no day of a constant series is above nine times its median",
                inputs={"values": [3.0] * 30},
                expected={"days_per_year": 0.0, "mean_duration_days": 0.0},
                tolerance=Tolerance(abs=0.0, reason="no day is counted"),
            ),
            _one_event([1.0] * 9 + [10.0, 10.0] + [1.0] * 9, 2, 20),
            _gap_parts_the_event([1.0] * 9 + [10.0, math.nan, 10.0] + [1.0] * 8, 19),
        ),
    ),
    validation=(
        "none: a descriptive statistic of the observed record; Westerberg and McMillan "
        "(2015) estimate its uncertainty from the data's"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "a high-flow day has a flow strictly above 9 times the median of the days with "
        "a value (Addor et al. 2017, Table 3; Westerberg and McMillan 2015, Table 2); "
        "the median of an even count is the mean of the two middle values",
        "where the median is 0, every day with flow is a high-flow day (the code of "
        "CAMELS-US notes it)",
        *_FLOW_DAYS_CONVENTIONS,
    ),
    assumptions=(
        "the record is long enough for its median to be that of the regime: the "
        "frequency of a short or partial record says little",
    ),
    traps={
        "difference_denominator": "constraint case has_values-violated: a series "
        "without a value is refused before n divides",
        "gap_propagation": "type case values-nan_element and limit "
        "gap_parts_the_event: a gap is neither a high-flow day nor counted, and it "
        "ends a run",
    },
    reference_cases=("tests/fixtures/formulas/camels-pl-cases.json",),
    oracles=(_FLOW_DAYS_ORACLE,),
)


def high_flow_days(values: NDArray[np.float64] | Sequence[float]) -> FlowDays:
    """Return the frequency and duration of the high-flow days, spec high_flow_days.

    Parameters
    ----------
    values : array_like of float
        Daily discharge in time order; ``NaN`` marks a day without a value.

    Returns
    -------
    FlowDays
        The high-flow days per year, the mean length of their runs, their count and
        the number of runs.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the series: a negative or infinite value or no day with a
        value.
    """
    x = checked_inputs(HIGH_FLOW_DAYS, values=values)
    scaled = _scaled_series(x)
    known = ~np.isnan(scaled)
    threshold = HIGH_FLOW_MULTIPLE * float(np.median(scaled[known]))
    found = _flow_days(x, known & (np.where(known, scaled, 0.0) > threshold))
    checked_outputs(
        HIGH_FLOW_DAYS,
        {
            "days_per_year": found.days_per_year,
            "mean_duration_days": found.mean_duration_days,
        },
    )
    return found


LOW_FLOW_DAYS: Final = FormulaSpec(
    name="low_flow_days",
    title="Low-flow days: their frequency and the mean duration of their runs",
    function="hydrolog.statistics.signatures.low_flow_days",
    family="index",
    equation=(
        "a low-flow day has Q_t < 0.2 mean(Q); F = 365.25 N_l / n, n the days with a "
        "value; D = N_l / E, E the runs of consecutive low-flow days, D = 0 when E = 0"
    ),
    latex=(
        r"Q_t < 0.2\,\bar{Q},\quad F = 365.25\,\frac{N_l}{n},\quad "
        r"D = \frac{N_l}{E}"
    ),
    variables=(
        Variable(
            name="values",
            symbol="Q_t",
            unit=_UNIT,
            kind="real_array",
            description="Daily discharge in time order; NaN on a day without a value.",
            physical=_ANY_FLOW,
            applicability="unstated",
            typical=_TYPICAL_FLOWS,
            gaps_allowed=True,
        ),
    ),
    outputs=_flow_days_outputs("l"),
    sources=(
        _addor("Table 3, p. 5300: low_q_freq and low_q_dur"),
        _WESTERBERG,
        _OLDEN_POFF,
        _addor_code("compute_lf_freq_dur: lf <- q <= 0.2 * mean(q)"),
    ),
    constraints=(_HAS_VALUES,),
    constants=(_LOW_FLOW_MULTIPLE, _DAYS_PER_YEAR),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={"days_per_year": 0.0, "mean_duration_days": 0.0},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="constant_series",
                text="no day of a constant series is below a fifth of its mean",
                inputs={"values": [3.0] * 30},
                expected={"days_per_year": 0.0, "mean_duration_days": 0.0},
                tolerance=Tolerance(abs=0.0, reason="no day is counted"),
            ),
            _one_event([10.0] * 9 + [0.0, 0.0] + [10.0] * 9, 2, 20),
            _gap_parts_the_event([10.0] * 9 + [0.0, math.nan, 0.0] + [10.0] * 8, 19),
        ),
    ),
    validation=(
        "none: a descriptive statistic of the observed record; Westerberg and McMillan "
        "(2015) estimate its uncertainty from the data's"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "a low-flow day has a flow strictly below 0.2 times the mean of the days with "
        "a value (Addor et al. 2017, Table 3, and the codes of CAMELS-DE and "
        "CAMELS-PL; Westerberg and McMillan 2015, Table 2: 'lower than'); the code of "
        "CAMELS-US takes <=",
        "the mean is the sum of the days with a value, exactly rounded once "
        "(math.fsum), over their number",
        *_FLOW_DAYS_CONVENTIONS,
    ),
    assumptions=(
        "the record is long enough for its mean to be that of the regime: the "
        "frequency of a short or partial record says little",
    ),
    traps={
        "difference_denominator": "constraint case has_values-violated: a series "
        "without a value is refused before n divides",
        "gap_propagation": "type case values-nan_element and limit "
        "gap_parts_the_event: a gap is neither a low-flow day nor counted, and it "
        "ends a run",
        "many_small_terms": "test_the_mean_of_many_days_is_summed_exactly: the mean "
        "of 50,000 days against the exact rational sum",
    },
    reference_cases=("tests/fixtures/formulas/camels-pl-cases.json",),
    oracles=(_FLOW_DAYS_ORACLE,),
)


def low_flow_days(values: NDArray[np.float64] | Sequence[float]) -> FlowDays:
    """Return the frequency and duration of the low-flow days, spec low_flow_days.

    Parameters
    ----------
    values : array_like of float
        Daily discharge in time order; ``NaN`` marks a day without a value.

    Returns
    -------
    FlowDays
        The low-flow days per year, the mean length of their runs, their count and
        the number of runs.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the series: a negative or infinite value or no day with a
        value.
    """
    x = checked_inputs(LOW_FLOW_DAYS, values=values)
    scaled = _scaled_series(x)
    known = ~np.isnan(scaled)
    mean = math.fsum(scaled[known]) / int(np.count_nonzero(known))
    threshold = LOW_FLOW_MULTIPLE * mean
    found = _flow_days(x, known & (np.where(known, scaled, threshold) < threshold))
    checked_outputs(
        LOW_FLOW_DAYS,
        {
            "days_per_year": found.days_per_year,
            "mean_duration_days": found.mean_duration_days,
        },
    )
    return found


# --- the days without flow ---------------------------------------------------------

ZERO_FLOW_FRACTION: Final = FormulaSpec(
    name="zero_flow_fraction",
    title="Share of the days without flow",
    function="hydrolog.statistics.signatures.zero_flow_fraction",
    family="index",
    equation="f_0 = N_0 / n, N_0 the days with Q_t = 0, n the days with a value",
    latex=r"f_0 = \frac{N_0}{n}",
    variables=(
        Variable(
            name="values",
            symbol="Q_t",
            unit=_UNIT,
            kind="real_array",
            description="Daily discharge; NaN on a day without a value.",
            physical=_ANY_FLOW,
            applicability="unstated",
            typical=_TYPICAL_FLOWS,
            gaps_allowed=True,
        ),
    ),
    outputs=(
        Output(
            name="fraction",
            unit="-",
            symbol="f_0",
            description="The share of the days with a value that have no flow.",
            physical=Range(low=0.0, high=1.0),
        ),
    ),
    sources=(
        _addor("Table 3, p. 5300: zero_q_freq, the frequency of days with Q = 0"),
        _addor_code("compute_no_flow: sum(q[avail_data] <= thres) / length(...)"),
    ),
    constraints=(_HAS_VALUES,),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={"fraction": 0.0},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="a value doubled is 0 exactly when the value is: the count "
                    "is the same",
                ),
            ),
        ),
        limits=(
            Limit(
                name="always_flowing",
                text="a series without a day of no flow has f_0 = 0",
                inputs={"values": [0.5, 2.0, 1.0]},
                expected={"fraction": 0.0},
                tolerance=Tolerance(abs=0.0, reason="no day is counted"),
            ),
            Limit(
                name="never_flowing",
                text="a series of days without flow has f_0 = 1",
                inputs={"values": [0.0, 0.0, math.nan, 0.0]},
                expected={"fraction": 1.0},
                tolerance=Tolerance(abs=0.0, reason="every day with a value counts"),
            ),
            Limit(
                name="gap_left_out",
                text="a day without a value is neither counted nor a day without flow",
                inputs={"values": [0.0, 1.5, math.nan, 2.0]},
                expected={"fraction": 1.0 / 3.0},
                tolerance=Tolerance(abs=0.0, reason="one rounding of 1 / 3"),
            ),
        ),
    ),
    validation="none: a count of the observed record",
    formula_version=1,
    status="referenced",
    conventions=(
        "a day without flow has a discharge of 0 exactly, in the rounding of the data: "
        "a flow below half the last printed unit is 0 (CAMELS-PL counts the days whose "
        "specific discharge, printed to 0.001 mm/d, is 0)",
        "the share of the days with a value (the code of CAMELS-US); the codes of "
        "CAMELS-DE and CAMELS-PL divide by every day of their frame, the days without "
        "a value too",
        "a fraction, not a percentage (Addor et al. 2017, Table 3, give %, the files "
        "of CAMELS-US, CAMELS-DE and CAMELS-PL fractions)",
    ),
    traps={
        "difference_denominator": "constraint case has_values-violated: a series "
        "without a value is refused before n divides",
        "gap_propagation": "type case values-nan_element and limit gap_left_out: a "
        "gap is left out of both counts",
    },
    reference_cases=("tests/fixtures/formulas/camels-pl-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the count of the days without flow over the days with a "
            "value, as an exact fraction",
            test="tests/unit/test_formulas_signatures.py::"
            "test_the_zero_flow_fraction_is_the_exact_share",
        ),
    ),
)


def zero_flow_fraction(values: NDArray[np.float64] | Sequence[float]) -> float:
    """Return the share of the days without flow, spec zero_flow_fraction.

    Parameters
    ----------
    values : array_like of float
        Daily discharge; ``NaN`` marks a day without a value.

    Returns
    -------
    float
        The share of the days with a value that have no flow.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the series: a negative or infinite value or no day with a
        value.
    """
    x = checked_inputs(ZERO_FLOW_FRACTION, values=values)
    data = x.array("values")
    known = data[~np.isnan(data)]
    fraction = int(np.count_nonzero(known == 0.0)) / known.size
    return checked_outputs(ZERO_FLOW_FRACTION, {"fraction": fraction}).real("fraction")


# --- the half-flow date ------------------------------------------------------------


def _common_integers(flows: NDArray[np.float64]) -> list[int]:
    """Return the flows as integer multiples of one power of two, exactly."""
    ratios = [float(flow).as_integer_ratio() for flow in flows]
    scale = max(denominator for _, denominator in ratios)
    return [numerator * (scale // denominator) for numerator, denominator in ratios]


def _positive_volume(x: Values) -> bool:
    data = x.array("values")
    return bool(np.any(data[~np.isnan(data)] > 0.0))


HALF_FLOW_DATE: Final = FormulaSpec(
    name="half_flow_date",
    title="Half-flow date: the day on which half of a year's flow has passed",
    function="hydrolog.statistics.signatures.half_flow_date",
    family="index",
    equation=(
        "d = min { k : 2 sum_(t=1..k) Q_t > sum_(t=1..n) Q_t }, the days numbered from "
        "the first day of the year, 1; a day without a value adds nothing"
    ),
    latex=r"d = \min\Bigl\{k : 2\sum_{t=1}^{k} Q_t > \sum_{t=1}^{n} Q_t\Bigr\}",
    variables=(
        Variable(
            name="values",
            symbol="Q_t",
            unit=_UNIT,
            kind="real_array",
            description="The daily discharge of one year, from its first day; NaN on a "
            "day without a value.",
            physical=_ANY_FLOW,
            applicability="unstated",
            typical=_TYPICAL_FLOWS,
            gaps_allowed=True,
            max_length=366,
        ),
    ),
    outputs=(
        Output(
            name="day",
            unit="d",
            kind="integer",
            symbol="d",
            description="The day of the year, from 1, on which the flow summed from "
            "its first day first exceeds half of the year's.",
            physical=Range(low=1.0, high=366.0),
        ),
    ),
    sources=(
        _COURT,
        _addor(
            "Table 3, p. 5300: hfd_mean, the mean half-flow date, the 'date on which "
            "the cumulative discharge since 1 October reaches half of the annual "
            "discharge'"
        ),
        _addor_code(
            "compute_hfd_mean_sd: which(cumsum(hy_q) > 0.5 * sum(hy_q))[1], the number "
            "of days since the beginning of the hydrological year"
        ),
        _camels_de_code(
            "hfd_mean: the first day whose cumulative discharge since the start of the "
            "year exceeds half of the year's, counted from 1"
        ),
    ),
    constraints=(
        Constraint(
            name="positive_flow_volume",
            cls="precondition",
            check=_positive_volume,
            text="sum(Q_t) > 0",
            source=_addor_code(
                "compute_hfd_mean_sd: 'hfd can't be computed if annual discharge is 0'"
            ),
            satisfied={"values": [0.0, 1.0, math.nan]},
            violated={"values": [0.0, 0.0, math.nan]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={"day": 0.0},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the sums are exact: doubling every value doubles both "
                    "sides of the comparison",
                ),
            ),
        ),
        limits=(
            Limit(
                name="uniform_flow",
                text="a year of equal flows passes half of its flow on the day after "
                "its middle: day 183 of 365, day 184 of 366",
                inputs={"values": [2.5] * 365},
                expected={"day": 183},
                tolerance=Tolerance(abs=0.0, reason="a day"),
            ),
            Limit(
                name="one_day_of_flow",
                text="all the flow of the year on one day is that day",
                inputs={"values": [0.0] * 99 + [40.0] + [0.0] * 265},
                expected={"day": 100},
                tolerance=Tolerance(abs=0.0, reason="a day"),
            ),
            Limit(
                name="half_reached_is_not_exceeded",
                text="a sum equal to half of the year's is not past it: the date is "
                "the next day with flow",
                inputs={"values": [1.0, 1.0, math.nan, 1.0, 1.0]},
                expected={"day": 4},
                tolerance=Tolerance(abs=0.0, reason="a day"),
            ),
        ),
    ),
    validation=(
        "none: a timing statistic of the observed record; Court (1962) and Addor et "
        "al. (2017) use it to compare the timing of runoff"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "the values are the days of one year in order, day 1 its first: IMGW-PIB's "
        "hydrological year from 1 November (CAMELS-PL), CAMELS-US's from 1 October; "
        "the mean half-flow date of a record is the mean of its years' dates",
        "the date is the first day whose summed flow exceeds half of the year's "
        "(strictly, as the codes of CAMELS-US and CAMELS-DE take it; Addor et al.'s "
        "Table 3 says 'reaches')",
        "a day without a value (NaN) adds nothing to either sum, so it is never the "
        "date (the code of CAMELS-US drops it and keeps the numbers of the days)",
        "the sums are exact for the binary values given, integer multiples of their "
        "smallest power of two: no rounding decides the date, and a sum equal to half "
        "of the year's, a tie, is not past it; values equal in their printed decimals "
        "can still tie in decimals and not in binary",
    ),
    assumptions=(
        "the days without a value are few: each takes its flow out of the year and can "
        "move the date",
    ),
    traps={
        "many_small_terms": "test_a_tie_is_decided_exactly: ten flows of 0.1, whose "
        "float sums put the date a day early, give the exact day",
        "gap_propagation": "type case values-nan_element and limit "
        "half_reached_is_not_exceeded: a gap adds nothing and is never the date",
    },
    reference_cases=("tests/fixtures/formulas/camels-pl-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the cumulative sums in exact rational arithmetic (fractions), "
            "day by day",
            test="tests/unit/test_formulas_signatures.py::"
            "test_the_date_is_the_exact_crossing",
        ),
    ),
)


def half_flow_date(values: NDArray[np.float64] | Sequence[float]) -> int:
    """Return the day on which half of a year's flow has passed, spec half_flow_date.

    Parameters
    ----------
    values : array_like of float
        The daily discharge of one year, from its first day; ``NaN`` marks a day
        without a value.

    Returns
    -------
    int
        The day of the year, the first being one, on which the flow summed from the
        first day first exceeds half of the year's.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the series: a negative or infinite value, more days than a
        year has or no flow.
    """
    x = checked_inputs(HALF_FLOW_DATE, values=values)
    data = x.array("values")
    flows = _common_integers(np.where(np.isnan(data), 0.0, data))
    total = sum(flows)
    day = next(
        day
        for day, running in enumerate(accumulate(flows), start=1)
        if 2 * running > total
    )
    return checked_outputs(HALF_FLOW_DATE, {"day": day}).integer("day")


SPECS: Final = (
    FDC_SLOPE,
    HIGH_FLOW_DAYS,
    LOW_FLOW_DAYS,
    ZERO_FLOW_FRACTION,
    HALF_FLOW_DATE,
)
"""The Tier A formulas of the module (Nogat CMP-2.1)."""
