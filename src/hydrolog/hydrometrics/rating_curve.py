"""Rating curves and water level zones, declared by specs (Nogat CMP).

Four Tier A formulas are declared here by their specs (ADR-0050); ``docs/FORMULAS.md``
shows their equations, ranges, sources and conventions:

* :data:`RATING_CURVE` (``rating_curve``), the power-law rating equation of WMO-No.
  1044, computed by :func:`rating_discharge`;
* :data:`RATING_CURVE_FIT` (``rating_curve_fit``), its least-squares fit to
  stage-discharge pairs, :func:`fit_rating_curve`, whose search SciPy's ``curve_fit``
  runs (a delegated computation, ``hydrolog._formulas.DELEGATED``);
* :data:`RATING_CURVE_PLAUSIBILITY` (``rating_curve_plausibility``), Hydrolog's check
  of a curve as the curve of one stage-discharge relation (ADR-0041),
  :func:`rating_curve_plausibility`;
* :data:`RYBCZYNSKI_ZONES` (``rybczynski_zones``), the zones of low, medium and high
  background water from the frequency distribution of water levels,
  :func:`rybczynski_zones`.

``TIER_B`` declares the frequency distribution of the levels, the default start of the
search for H₀ and the screening of outlying pairs. :class:`RatingCurve` and
:class:`WaterLevelFrequency` keep their interface and compute through these functions.

The levels may be in any one unit, cm as IMGW-PIB gives them or m: H₀ is in that unit
and ``a`` in m³/s per (unit of H)^b, so the same curve with the levels in m has an
``a`` 100^b times larger and an H₀ 100 times smaller.

Examples
--------
The curve of six gaugings, two of them below the gauge zero (fewer than the 12 of
WMO-No. 1044, so the fit warns that its applicability is not met):

>>> import warnings
>>> with warnings.catch_warnings():
...     warnings.simplefilter("ignore")
...     fit = fit_rating_curve(
...         [-10.0, 5.0, 20.0, 40.0, 80.0, 120.0],
...         [0.5, 1.2, 2.5, 4.8, 10.1, 17.3],
...         -23.0,
...     )
>>> round(fit.a, 6), round(fit.b, 4), round(fit.h0, 2), round(fit.r_squared, 4)
(0.004917, 1.6401, -25.17, 0.9998)

The discharge of a curve at its levels, none below the stage of zero flow:

>>> rating_discharge([20.0, 33.0, 132.0], 0.012, 1.62, 32.0).round(4).tolist()
[0.0, 0.012, 20.8536]
>>> rating_curve_plausibility([45.0, 161.0], 6.5, -88.0).reasons
('b_out_of_range', 'h0_too_low')
"""

from __future__ import annotations

import dataclasses
import math
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext
from functools import lru_cache
from typing import Final, NamedTuple, cast

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import curve_fit

from hydrolog._formulas import checked_inputs, checked_outputs, constraint_range
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

__all__ = [
    "GAUGINGS",
    "RATING_CURVE",
    "RATING_CURVE_FIT",
    "RATING_CURVE_PLAUSIBILITY",
    "RYBCZYNSKI_ZONES",
    "SPECS",
    "TIER_B",
    "FrequencyDistributionResult",
    "RatingCurve",
    "RatingCurveResult",
    "RatingPlausibility",
    "WaterLevelFrequency",
    "WaterLevelZones",
    "fit_rating_curve",
    "rating_curve_plausibility",
    "rating_discharge",
    "rybczynski_zones",
]

Levels = NDArray[np.float64] | Sequence[float]
"""Water levels as an array or a sequence of numbers."""

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class RatingCurveResult(JsonResultMixin):
    """
    Result of rating curve fitting Q = a * (H - H0)^b.

    Attributes
    ----------
    a : float
        Scale coefficient, the discharge at a head H - H0 of one unit of H
        [m³/s per (unit of H)^b]. With H in cm (IMGW-PIB stages) it is typically
        0.005-0.015; the same curve with H in m has an ``a`` 100^b times larger.
    b : float
        Power exponent [-].
    h0 : float
        Stage of zero flow H0, in the unit of H: the gauge height at which the
        flow is zero, or effectively zero for a control of irregular shape
        (WMO-No. 1044, 2010, Vol. II, eq. 1.4). It is not the gauge zero, the
        datum of the staff gauge from which H is read.
    r_squared : float
        Coefficient of determination R² [-].
    std_residuals : float
        Standard deviation of residuals [m³/s].
    n_points : int
        Number of data points used for final fit.
    n_outliers_removed : int
        Number of outlier observations removed before final fit.
    """

    a: float
    b: float
    h0: float
    r_squared: float
    std_residuals: float
    n_points: int
    n_outliers_removed: int


@dataclass
class WaterLevelZones(JsonResultMixin):
    """
    Rybczyński water level zones.

    The water levels are divided into three zones by the frequency distribution of
    the levels (spec ``rybczynski_zones``):

    - NTW (Niskie Tło Wodne / Low Background Water): up to the centre of the most
      frequent class
    - STW (Średnie Tło Wodne / Medium Background Water): from there up to the centre
      of the first class at whose lower edge the duration curve falls below 50 %
    - WTW (Wysokie Tło Wodne / High Background Water): above STW

    Attributes
    ----------
    ntw_upper : float
        Upper boundary of the NTW zone.
    stw_upper : float
        Upper boundary of the STW zone.
    ntw_range : tuple[float, float]
        (lowest class edge, ntw_upper).
    stw_range : tuple[float, float]
        (ntw_upper, stw_upper).
    wtw_range : tuple[float, float]
        (stw_upper, highest class edge).
    """

    ntw_upper: float
    stw_upper: float
    ntw_range: tuple[float, float]
    stw_range: tuple[float, float]
    wtw_range: tuple[float, float]


@dataclass
class FrequencyDistributionResult(JsonResultMixin):
    """
    Result of water level frequency distribution analysis.

    Attributes
    ----------
    bin_edges : NDArray[np.float64]
        Edges of histogram bins, length = n_bins + 1.
    bin_centers : NDArray[np.float64]
        Centre of each bin, length = n_bins.
    counts : NDArray[np.float64]
        Observation count per bin.
    frequency_pct : NDArray[np.float64]
        Relative frequency [%], sums to 100.
    cumulative_frequency_pct : NDArray[np.float64]
        Cumulative frequency from lowest to highest bin [%].
    duration_pct : NDArray[np.float64]
        Exceedance probability (duration curve) [%]:
        ``duration_pct[i]`` is the percentage of time H >= bin_edges[i].
    """

    bin_edges: NDArray[np.float64]
    bin_centers: NDArray[np.float64]
    counts: NDArray[np.float64]
    frequency_pct: NDArray[np.float64]
    cumulative_frequency_pct: NDArray[np.float64]
    duration_pct: NDArray[np.float64]


class RatingPlausibility(NamedTuple):
    """The verdict of spec ``rating_curve_plausibility`` on a rating curve.

    Attributes
    ----------
    exponent : str
        ``plausible``, or ``b_out_of_range`` for an exponent outside 1 to 4.
    zero_flow_stage : str
        ``plausible``, or ``h0_too_low`` for an H0 below the lowest level by more than
        the range of the levels.
    """

    exponent: str
    zero_flow_stage: str

    @property
    def reasons(self) -> tuple[str, ...]:
        """Why the curve is not plausible, in the order of ADR-0041; empty if it is."""
        return tuple(
            v for v in (self.exponent, self.zero_flow_stage) if v != _PLAUSIBLE
        )

    @property
    def plausible(self) -> bool:
        """Whether the curve is plausible as the curve of one relation."""
        return not self.reasons


# ---------------------------------------------------------------------------
# Sources and ranges shared by the specs
# ---------------------------------------------------------------------------

_WMO_1044 = (
    "WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, "
    "WMO-No. 1044, Geneva"
)
_WMO_URL = "https://library.wmo.int/idurl/4/32726"
_EQUATION = Source(
    citation=_WMO_1044,
    locator="sect. 1.5.4, eq. 1.4, pp. II.1-6 to II.1-7: Q = C (h - e)^beta, h the "
    "gauge height, e the gauge height of zero flow for a control of regular shape, "
    "or of effective zero flow for a control of irregular shape, C the discharge "
    "when the head h - e equals 1, beta the slope of the rating on logarithmic paper",
    url=_WMO_URL,
)
_ISO_1100_2 = Source(
    citation="ISO 1100-2:2010. Hydrometry - Measurement of liquid flow in open "
    "channels - Part 2: Determination of the stage-discharge relationship",
    locator="the power-law rating equation and its fit to gaugings",
    access="author-provided",
)
_GAUGINGS = Source(
    citation=_WMO_1044,
    locator="sect. 1.5.1, p. II.1-3: at a minimum the list of discharge measurements "
    "should include at least 12 to 15 measurements, all made during the period of "
    "analysis",
    url=_WMO_URL,
)
_LEAST_SQUARES = Source(
    citation=_WMO_1044,
    locator="sect. 1.12.2, p. II.1-20: the equation of the relation may be computed by "
    "the method of least squares, which assumes that the relation plots as a straight "
    "line on logarithmic paper",
    url=_WMO_URL,
)
_SECTION_CONTROLS = Source(
    citation=_WMO_1044,
    locator="sect. 1.3, eq. 1.1, p. II.1-2: beta = 1.5 for a rectangular and 2.5 for "
    "a V-shaped section control; sect. 1.5.6, p. II.1-8: logarithmic ratings of "
    "section controls in natural channels almost always have a slope of 2 or greater, "
    "those of channel controls usually less than 2",
    url=_WMO_URL,
)
_REAL_SECTION_CONTROL = Source(
    citation=_WMO_1044,
    locator="sect. 1.5.6, fig. II.1.5, p. II.1-9: the rating of a real stream with "
    "section control throughout, e = 0.6 m, has a slope of about 4.3 below 1.4 m and "
    "2.8 above 1.5 m",
    url=_WMO_URL,
)
_ADR_0041 = Source(
    citation="Hydrolog ADR-0041 (2026). Implausible rating curves: flagged, not "
    "refused, docs/decisions/0041-implausible-rating-curves-flagged-not-refused.md",
    locator="decision 1: b from 1 to 4, H0 below the lowest stage by at most the range "
    "of the stages; Hydrolog's own rule, published by no source",
)
_FLOAT64 = Source(
    citation="NumPy documentation, numpy.finfo",
    locator="float64: the largest number 1.7976931348623157e+308",
    url="https://numpy.org/doc/stable/reference/generated/numpy.finfo.html",
)
_PROJECT = (
    "Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, "
    "tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics "
    "rating-curve and IMGW-PIB 150170070 in ADR-0041"
)
_LEVELS_SOURCE = Source(
    citation=_PROJECT,
    locator="stages of -10 cm (below the gauge zero, the catalog's example) to 329 cm "
    "(station_daily.csv); 6 to 161 cm at 150170070",
)
_DISCHARGES_SOURCE = Source(
    citation=_PROJECT,
    locator="discharges of 0.5 (the catalog's example) to 122.3 m3/s "
    "(station_daily.csv)",
)
_FITS_SOURCE = Source(
    citation=_PROJECT,
    locator="the curves fitted to them with levels in cm: a 0.0049 to 0.035, b 1.28 "
    "to 3.02 (all the pairs of 150170070), H0 -25.2 to 52.6 cm",
)
_LEVEL_TEST = 1.0e4
_LEVEL_REASON = (
    "100 m above or below a gauge's zero in cm: the stages of the largest rivers in "
    "flood range over a few tens of metres, so every stage of a gauge lies within"
)
_DISCHARGE_TEST = 1.0e6
_DISCHARGE_REASON = (
    "a million m3/s, above the largest flood discharge of any river (the Amazon's, a "
    "few hundred thousand m3/s)"
)
_COEFFICIENT_REASON = (
    "the discharge at a head of one cm cannot exceed the largest discharge of any "
    "river, below a million m3/s"
)
_EXPONENT_TEST = 20.0
_EXPONENT_REASON = (
    "five times the largest exponent of a plausible curve (4, ADR-0041), three times "
    "the exponent of the curve of two relations at IMGW-PIB 150170070 (6.6)"
)
_PLAUSIBLE: Final = "plausible"
_SMALLEST_NORMAL = 2.2250738585072014e-308


def _levels_variable(description: str, min_length: int) -> Variable:
    return Variable(
        name="water_levels",
        symbol="H",
        unit="cm",
        kind="real_array",
        description=description,
        physical=Range(
            test_low=-_LEVEL_TEST, test_high=_LEVEL_TEST, test_reason=_LEVEL_REASON
        ),
        applicability="unstated",
        typical=Range(low=-10.0, high=330.0, source=_LEVELS_SOURCE),
        min_length=min_length,
    )


def _exponent_variable(description: str) -> Variable:
    return Variable(
        name="b",
        symbol="b",
        unit="-",
        description=description,
        physical=Range(low=0.0, test_high=_EXPONENT_TEST, test_reason=_EXPONENT_REASON),
        applicability="unstated",
        typical=Range(low=1.2, high=3.1, source=_FITS_SOURCE),
    )


def _zero_flow_variable(description: str) -> Variable:
    return Variable(
        name="h0",
        symbol="H_0",
        unit="cm",
        description=description,
        physical=Range(
            test_low=-_LEVEL_TEST, test_high=_LEVEL_TEST, test_reason=_LEVEL_REASON
        ),
        applicability="unstated",
        typical=Range(low=-30.0, high=55.0, source=_FITS_SOURCE),
    )


# ---------------------------------------------------------------------------
# The rating equation
# ---------------------------------------------------------------------------


def _discharges(
    levels: NDArray[np.float64], a: float, b: float, h0: float
) -> NDArray[np.float64]:
    """Return a (H - H0)^b above H0 and 0 at and below it; inf where it overflows."""
    with np.errstate(over="ignore", invalid="ignore"):
        head = levels - h0
        flowing = head > 0.0
        power = np.where(flowing, np.maximum(head, 0.0) ** b, 0.0)
        return np.where(flowing, a * power, 0.0)


def _finite_curve(x: Values) -> bool:
    curve = _discharges(x.array("water_levels"), x.real("a"), x.real("b"), x.real("h0"))
    return bool(np.all(np.isfinite(curve)))


_EXACT_CURVES: Final = (
    ((40.0, 55.0, 70.0, 90.0, 120.0, 160.0, 210.0, 270.0), 0.012, 1.62, 32.0),
    ((-10.0, 5.0, 20.0, 40.0, 80.0, 120.0), 0.0049173, 1.6401, -25.17),
    ((0.45, 0.62, 1.61), 20.85, 1.62, 0.32),
    ((1.4, 1.5, 2.8), 12.0, 4.3, 0.6),
)
"""Curves of the exact oracle: levels, a, b and H0 (the analytic case in cm and in m,
the catalog's example, WMO's section control of slope 4.3)."""


def _exact_discharge(level: float, a: float, b: float, h0: float) -> float:
    """Return a (H - H0)^b of float inputs at 50 decimal digits, rounded once."""
    with localcontext() as context:
        context.prec = 50
        head = Decimal(level) - Decimal(h0)
        if head <= 0:
            return 0.0
        return float(Decimal(a) * head ** Decimal(b))


def _exact_decimal(run: Callable[..., Values]) -> None:
    for levels, a, b, h0 in _EXACT_CURVES:
        assert_within(
            run(water_levels=list(levels), a=a, b=b, h0=h0).array("discharge_m3s"),
            [_exact_discharge(level, a, b, h0) for level in levels],
            rel=4e-15,
            reason="the power of the head and the product round a few times each, "
            "against the same curve at 50 decimal digits rounded once",
        )


def _no_flow_below(run: Callable[..., Values]) -> None:
    for b in (0.0, 0.5, 1.62):
        assert_within(
            run(water_levels=[-5.0, 31.0, 32.0], a=0.012, b=b, h0=32.0).array(
                "discharge_m3s"
            ),
            [0.0, 0.0, 0.0],
            abs=0.0,
            reason="no flow at and below the gauge height of zero flow, whatever b",
        )


def _rating_unit(x: Values) -> dict[str, object]:
    """Return the inputs with the levels and H0 doubled and a scaled by 2^-b."""
    b = x.real("b")
    return {
        "water_levels": 2.0 * x.array("water_levels"),
        "a": x.real("a") * 2.0**-b,
        "b": b,
        "h0": 2.0 * x.real("h0"),
    }


RATING_CURVE: Final = FormulaSpec(
    name="rating_curve",
    title="Discharge at a water level by the power-law rating curve",
    function="hydrolog.hydrometrics.rating_curve.rating_discharge",
    family="empirical",
    equation="Q = a * (H - H0)**b for H > H0; Q = 0 for H <= H0",
    latex=(
        r"Q = \begin{cases} a\,(H - H_0)^{b} & H > H_0 \\ 0 & H \le H_0 \end{cases}"
    ),
    variables=(
        _levels_variable(
            "Water levels H at which the discharge is read, in the unit of the "
            "curve's levels.",
            min_length=0,
        ),
        Variable(
            name="a",
            symbol="a",
            unit="m3/s per cm^b",
            description="The discharge at a head H - H0 of one unit of H (WMO's C).",
            physical=Range(
                low=0.0, test_high=_DISCHARGE_TEST, test_reason=_COEFFICIENT_REASON
            ),
            applicability="unstated",
            typical=Range(low=0.003, high=0.04, source=_FITS_SOURCE),
        ),
        _exponent_variable("The exponent of the head (WMO's beta)."),
        _zero_flow_variable(
            "The gauge height of zero flow, or of effective zero flow (WMO's e)."
        ),
    ),
    outputs=(
        Output(
            name="discharge_m3s",
            unit="m3/s",
            kind="real_array",
            symbol="Q",
            description="The discharge at each level.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_EQUATION, _ISO_1100_2),
    constraints=(
        Constraint(
            name="finite_discharge",
            cls="precondition",
            check=_finite_curve,
            text="a (max(H) - H0)**b < 1.8e308: the discharge at every level is a "
            "float64 number",
            source=_FLOAT64,
            satisfied={"b": 1.62},
            violated={"b": 200.0},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"water_levels": 1, "a": 1, "h0": -1},
        scalings=(
            Scaling(
                name="discharge",
                inputs={"a": 1},
                outputs={"discharge_m3s": 1},
                tolerance=Tolerance(
                    abs=_SMALLEST_NORMAL,
                    reason="a doubled doubles every product exactly, but one below "
                    "the smallest normal float, which keeps fewer digits",
                ),
            ),
        ),
        symmetries=(
            Symmetry(
                name="levels_in_another_unit",
                text="levels and H0 in a unit twice as small with a times 2^-b give "
                "the same discharges: the curve in cm and in m is one curve",
                inputs=_rating_unit,
                outputs=lambda out: {"discharge_m3s": out.array("discharge_m3s")},
                tolerance=Tolerance(
                    rel=1e-13,
                    abs=1e-200,
                    reason="(2 head)^b against 2^b head^b and the rounding of 2^-b: a "
                    "few units in the last place of b's power; a below the normal "
                    "floats gives discharges below 1e-200 m3/s",
                ),
            ),
        ),
        limits=(
            Limit(
                name="unit_head",
                text="the discharge at a head of one unit is a (WMO's C)",
                inputs={"water_levels": [33.0], "a": 0.012, "b": 1.62, "h0": 32.0},
                expected={"discharge_m3s": [0.012]},
                tolerance=Tolerance(
                    abs=0.0, reason="1 to any power is 1 exactly: Q is a itself"
                ),
                source=_EQUATION,
            ),
            Limit(
                name="no_flow_at_or_below_zero_flow",
                text="no discharge at and below H0, also for b = 0",
                check=_no_flow_below,
            ),
            Limit(
                name="exact_decimal",
                text="Q equals the curve evaluated at 50 decimal digits",
                check=_exact_decimal,
            ),
        ),
    ),
    validation=(
        "none: WMO-No. 1044 presents the equation as the rating of section and channel "
        "controls (sects. 1.3 and 1.5.4 to 1.5.6) and reports no statistic of its "
        "agreement with gaugings; a curve's fit to its gaugings is that of spec "
        "rating_curve_fit"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        (
            "H and H0 in one unit of the levels, cm as IMGW-PIB gives them or m; a in "
            "m3/s per (unit of H)^b, so the same curve with the levels in m has a "
            "100^b times larger and H0 100 times smaller (symmetry "
            "levels_in_another_unit); Q in m3/s"
        ),
        (
            "Q = 0 at and below H0, the gauge height of zero flow (WMO's e): no flow "
            "over the control, whatever b"
        ),
        (
            "H0 is the stage of zero flow, not the gauge zero (the datum of the "
            "staff gauge)"
        ),
    ),
    assumptions=(
        "one stage-discharge relation of one control (a section or a channel control) "
        "over the levels: no shift, hysteresis or variable backwater",
    ),
    traps={
        "singular_at_bound": "the fractional power of the head at its bound 0: "
        "test_the_power_at_the_stage_of_zero_flow_is_finite",
        "exp_overflow": "the power of a head with a large b: test_a_power_that_"
        "overflows_is_refused (the precondition finite_discharge)",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="the curve evaluated with Python's decimal at 50 digits, "
            "rounded once",
            test="tests/unit/test_formulas_hydrometrics.py (limit exact_decimal)",
        ),
    ),
    base={
        "water_levels": [40.0, 55.0, 70.0, 90.0, 120.0, 160.0, 210.0, 270.0],
        "a": 0.012,
        "b": 1.62,
        "h0": 32.0,
    },
)


def rating_discharge(
    water_levels: Levels, a: float, b: float, h0: float
) -> NDArray[np.float64]:
    """Return the discharge at each water level by the rating curve, spec rating_curve.

    The last input is the gauge height of zero flow H₀, in the unit of the levels (its
    name holds a digit, which the standard's check of this docstring allows nowhere,
    so it stays out of the list below).

    Parameters
    ----------
    water_levels : array_like of float
        Water levels H, in the unit of the curve's levels.
    a : float
        The discharge at a head of one unit of H [m³/s per (unit of H)^b].
    b : float
        The exponent of the head.

    Returns
    -------
    ndarray of float
        The discharge at each level [m³/s]; none at and below H₀.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs (``details.reason``, ``details.option`` or
        ``details.constraint``).
    """
    x = checked_inputs(RATING_CURVE, water_levels=water_levels, a=a, b=b, h0=h0)
    curve = _discharges(x.array("water_levels"), x.real("a"), x.real("b"), x.real("h0"))
    return checked_outputs(RATING_CURVE, {"discharge_m3s": curve}).array(
        "discharge_m3s"
    )


# ---------------------------------------------------------------------------
# The fit
# ---------------------------------------------------------------------------

_START: Final = (1.0, 1.5)
"""The start of the search for a and b, on the normalised pairs."""
_H0_GAP: Final = 2.0**-30
"""How far below the lowest normalised level H0 stays: 2^-30 of the levels' scale."""
_MAX_EVALUATIONS: Final = 10_000
_SEARCH_TOLERANCE: Final = 1e-12
"""ftol, xtol and gtol of the trust region search."""


def _power_law(
    h: NDArray[np.float64], a: float, b: float, h0: float
) -> NDArray[np.float64]:
    """Return a (h - h0)^b of the search, 0 at and below h0."""
    return a * np.maximum(h - h0, 0.0) ** b


def _scale(values: NDArray[np.float64]) -> int:
    """Return the exponent e that brings the largest magnitude into [1/2, 1) by 2^-e."""
    largest = float(np.max(np.abs(values)))
    return math.frexp(largest)[1] if largest > 0.0 else 0


class _Search(NamedTuple):
    """The least squares of normalised pairs (``None`` where they did not settle)."""

    found: tuple[float, float, float, float, float] | None
    caught: tuple[tuple[type[Warning], str], ...]


@lru_cache(maxsize=32)
def _normalised_search(levels: bytes, discharges: bytes, start: float) -> _Search:
    """Fit the curve to normalised pairs, given as float64 bytes, from a start of H0.

    Returns a', b, H0', R² and the standard deviation of the residuals of the
    normalised pairs, and the warnings the search gave, which the fit issues again
    (the cache keeps them, so a cached search warns as a new one). Cached by the
    bytes: the precondition ``least_squares_minimum`` and the fit run one search, and
    pairs scaled by powers of two share it.
    """
    h = np.frombuffer(levels, dtype=np.float64)
    q = np.frombuffer(discharges, dtype=np.float64)
    upper = float(np.min(h)) - _H0_GAP
    found: tuple[float, float, float, float, float] | None = None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            point, _ = curve_fit(
                _power_law,
                h,
                q,
                p0=[*_START, min(start, upper)],
                bounds=([0.0, 0.0, -np.inf], [np.inf, np.inf, upper]),
                maxfev=_MAX_EVALUATIONS,
                ftol=_SEARCH_TOLERANCE,
                xtol=_SEARCH_TOLERANCE,
                gtol=_SEARCH_TOLERANCE,
            )
        except (RuntimeError, ValueError, ArithmeticError):
            point = None
        if point is not None:
            a, b, h0 = (float(value) for value in point)
            with np.errstate(all="ignore"):
                residuals = q - _power_law(h, a, b, h0)
                ss_res = float(np.sum(residuals**2))
                ss_tot = float(np.sum((q - np.mean(q)) ** 2))
                spread = float(np.std(residuals, ddof=1))
            numbers = (a, b, h0, ss_res, ss_tot, spread)
            if all(math.isfinite(n) for n in numbers) and ss_tot > 0.0:
                found = (a, b, h0, 1.0 - ss_res / ss_tot, spread)
    warned = tuple((item.category, str(item.message)) for item in caught)
    return _Search(found, warned)


class _Fit(NamedTuple):
    a: float
    b: float
    h0: float
    r_squared: float
    std_residuals: float
    caught: tuple[tuple[type[Warning], str], ...]


def _fit(x: Values) -> _Fit | None:
    """Return the curve of checked inputs in their units; ``None`` where none settles.

    The search runs on the levels and discharges divided by the powers of two that
    bring their largest magnitudes into [1/2, 1), exactly, and the curve is scaled
    back: a by 2^eQ 2^(-eH b), H0 by 2^eH. Levels in cm and in m, or discharges
    doubled, give the same search, so the curve of each is the same curve exactly.
    The curve must be a float64 number in the units of the inputs, at every level.
    """
    levels = x.array("water_levels")
    discharges = x.array("discharges_m3s")
    eh, eq = _scale(levels), _scale(discharges)
    search = _normalised_search(
        np.ldexp(levels, -eh).tobytes(),
        np.ldexp(discharges, -eq).tobytes(),
        math.ldexp(x.real("h0_initial"), -eh),
    )
    if search.found is None:
        return None
    a_normal, b, h0_normal, r_squared, spread = search.found
    try:
        a = math.ldexp(a_normal, eq) * 2.0 ** (-eh * b)
        h0 = math.ldexp(h0_normal, eh)
        std = math.ldexp(spread, eq)
    except OverflowError:
        return None
    if not (math.isfinite(a) and (a > 0.0) == (a_normal > 0.0)):
        return None
    if not np.all(np.isfinite(_discharges(levels, a, b, h0))):
        return None
    return _Fit(a, b, h0, r_squared, std, search.caught)


def _settles(x: Values) -> bool:
    return _fit(x) is not None


def _same_length(x: Values) -> bool:
    return x.array("water_levels").shape == x.array("discharges_m3s").shape


_PAIRS_H: Final = (
    62.0, 75.0, 88.0, 101.0, 115.0, 128.0, 142.0, 155.0, 170.0, 185.0, 200.0, 218.0,
    235.0, 252.0, 270.0,
)  # fmt: skip
_PAIRS_Q: Final = (
    1.05, 2.14, 3.40, 4.67, 6.32, 8.27, 10.48, 12.46, 20.75, 17.72, 20.50, 23.40,
    26.63, 31.80, 34.92,
)  # fmt: skip
"""The 15 gaugings of tests/fixtures/rating_curve_pairs.csv [cm, m3/s]: the typical
pairs of the generated tests (one of them, 170 cm, an outlier)."""
_BELOW_ZERO_H: Final = (-10.0, 5.0, 20.0, 40.0, 80.0, 120.0)
_BELOW_ZERO_Q: Final = (0.5, 1.2, 2.5, 4.8, 10.1, 17.3)
"""Six gaugings of the catalog's example, two below the gauge zero [cm, m3/s]."""
_UNSETTLED_H: Final = (10.0, 20.0, 30.0)
_UNSETTLED_Q: Final = (1.0, 10.0, 1000.0)
"""Three pairs whose least squares have no minimum that the search reaches [cm,
m3/s]: a discharge rising like an exponential draws b without bound and H0 to minus
infinity, until the search's count of evaluations runs out."""


def _noise_free(run: Callable[..., Values]) -> None:
    levels = np.array([40.0, 55.0, 70.0, 90.0, 120.0, 160.0, 210.0, 270.0])
    discharges = 0.012 * (levels - 32.0) ** 1.62
    for scale, a in ((1.0, 0.012), (0.01, 0.012 * 100.0**1.62)):
        out = run(
            water_levels=levels * scale,
            discharges_m3s=discharges,
            h0_initial=float(levels[0] * scale - max(scale * 23.0, 1.0)),
        )
        assert_within(
            [out.real("a"), out.real("b"), out.real("h0")],
            [a, 1.62, 32.0 * scale],
            rel=1e-9,
            reason="pairs of an exact power law: the least squares reach zero at the "
            "curve itself, within the search's tolerance of 1e-12",
        )


def _squares(
    levels: NDArray[np.float64], discharges: NDArray[np.float64], point: Sequence[float]
) -> float:
    a, b, h0 = point
    return math.fsum(((discharges - _discharges(levels, a, b, h0)) ** 2).tolist())


def _local_minimum(run: Callable[..., Values]) -> None:
    for levels_in, discharges_in, start in (
        (_PAIRS_H, _PAIRS_Q, 41.2),
        (_BELOW_ZERO_H, _BELOW_ZERO_Q, -23.0),
    ):
        levels = np.array(levels_in)
        discharges = np.array(discharges_in)
        out = run(water_levels=levels, discharges_m3s=discharges, h0_initial=start)
        point = [out.real("a"), out.real("b"), out.real("h0")]
        least = _squares(levels, discharges, point)
        for index in range(3):
            for sign in (-1.0, 1.0):
                moved = list(point)
                moved[index] += sign * 1e-4 * max(abs(point[index]), 1.0)
                if moved[2] >= float(levels.min()):
                    continue
                assert_within(
                    min(_squares(levels, discharges, moved) - least, 0.0),
                    0.0,
                    abs=1e-12 * least,
                    reason="no point a step of 1e-4 from the estimate has a smaller "
                    "sum of squares, beyond the sums' rounding",
                )


def _below_the_levels(run: Callable[..., Values]) -> None:
    for levels, discharges, start in (
        (_PAIRS_H, _PAIRS_Q, 41.2),
        (_BELOW_ZERO_H, _BELOW_ZERO_Q, -23.0),
    ):
        out = run(
            water_levels=list(levels), discharges_m3s=list(discharges), h0_initial=start
        )
        assert out.real("h0") < min(levels), "H0 lies below every level of the fit"


def _fit_unit(x: Values) -> dict[str, object]:
    """Return the inputs with the levels and the start of H0 doubled."""
    return {
        "water_levels": 2.0 * x.array("water_levels"),
        "discharges_m3s": x.array("discharges_m3s"),
        "h0_initial": 2.0 * x.real("h0_initial"),
    }


def _fit_in_another_unit(out: Values) -> dict[str, object]:
    b = out.real("b")
    return {
        "a": out.real("a") * 2.0**-b,
        "b": b,
        "h0": 2.0 * out.real("h0"),
        "r_squared": out.real("r_squared"),
        "std_residuals": out.real("std_residuals"),
    }


RATING_CURVE_FIT: Final = FormulaSpec(
    name="rating_curve_fit",
    title="Rating curve Q = a (H - H0)^b fitted to stage-discharge pairs by least "
    "squares on Q",
    function="hydrolog.hydrometrics.rating_curve.fit_rating_curve",
    family="statistic",
    equation=(
        "(a, b, H0) minimise sum((Q_i - a * (H_i - H0)**b)**2) over a >= 0, b >= 0, "
        "H0 < min(H); R2 = 1 - SS_res / SS_tot with SS_tot = sum((Q_i - mean(Q))**2); "
        "s = sqrt(sum((r_i - mean(r))**2) / (n - 1)) of the residuals r_i"
    ),
    latex=(
        r"(\hat a, \hat b, \hat H_0) = \arg\min_{a \ge 0,\, b \ge 0,\, H_0 < \min H}"
        r" \sum_{i=1}^{n} \left(Q_i - a\,(H_i - H_0)^{b}\right)^2,\quad"
        r" R^2 = 1 - \frac{SS_{res}}{SS_{tot}}"
    ),
    variables=(
        _levels_variable(
            "The water level H of each gauging, in one unit of the levels.", 1
        ),
        Variable(
            name="discharges_m3s",
            symbol="Q",
            unit="m3/s",
            kind="real_array",
            description="The discharge measured at each level.",
            physical=Range(
                low=0.0, test_high=_DISCHARGE_TEST, test_reason=_DISCHARGE_REASON
            ),
            applicability="unstated",
            typical=Range(low=0.5, high=125.0, source=_DISCHARGES_SOURCE),
        ),
        Variable(
            name="h0_initial",
            symbol="H_{0,start}",
            unit="cm",
            description="The start of the search for H0, below every level.",
            physical=Range(
                test_low=-_LEVEL_TEST, test_high=_LEVEL_TEST, test_reason=_LEVEL_REASON
            ),
            applicability="unstated",
            typical=Range(
                low=-30.0,
                high=60.0,
                source=Source(
                    citation=_PROJECT,
                    locator="the starts of their fits: -23 (the catalog's example of "
                    "stages below the gauge zero), 40 and 41.2 cm",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="a",
            unit="m3/s per cm^b",
            symbol="a",
            description="The discharge at a head of one unit of H.",
            physical=Range(low=0.0),
        ),
        Output(
            name="b",
            unit="-",
            symbol="b",
            description="The exponent of the head.",
            physical=Range(low=0.0),
        ),
        Output(
            name="h0",
            unit="cm",
            symbol="H_0",
            description="The gauge height of zero flow, below every level.",
            physical=Range(),
        ),
        Output(
            name="r_squared",
            unit="-",
            symbol="R^2",
            description="The coefficient of determination of the curve on Q.",
            physical=Range(high=1.0),
        ),
        Output(
            name="std_residuals",
            unit="m3/s",
            symbol="s",
            description="The standard deviation of the residuals Q - Q(H).",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_EQUATION, _LEAST_SQUARES, _ISO_1100_2),
    constraints=(
        Constraint(
            name="same_length",
            cls="physical",
            check=_same_length,
            text="one discharge per level",
            source=_GAUGINGS,
            satisfied={"water_levels": list(_PAIRS_H)},
            violated={"water_levels": list(_PAIRS_H[:-1])},
        ),
        Constraint(
            name="enough_pairs",
            cls="precondition",
            check=lambda x: x.array("water_levels").size >= 3,
            text="n >= 3: three pairs or more for the three parameters a, b and H0",
            source=_EQUATION,
            satisfied={
                "water_levels": [62.0, 128.0, 200.0, 270.0],
                "discharges_m3s": [1.05, 8.27, 20.5, 34.92],
            },
            boundary={
                "water_levels": [62.0, 128.0, 270.0],
                "discharges_m3s": [1.05, 8.27, 34.92],
            },
            violated={"water_levels": [62.0, 270.0], "discharges_m3s": [1.05, 34.92]},
        ),
        Constraint(
            name="levels_not_all_equal",
            cls="precondition",
            check=lambda x: bool(np.ptp(x.array("water_levels")) > 0.0),
            text="min(H) < max(H): levels all equal determine neither b nor H0",
            source=_EQUATION,
            satisfied={"water_levels": list(_PAIRS_H)},
            violated={"water_levels": [100.0] * len(_PAIRS_H)},
        ),
        Constraint(
            name="discharges_not_all_equal",
            cls="precondition",
            check=lambda x: bool(np.ptp(x.array("discharges_m3s")) > 0.0),
            text="min(Q) < max(Q): a discharge that does not change with the level "
            "fits b = 0 at any H0",
            source=_EQUATION,
            satisfied={"discharges_m3s": list(_PAIRS_Q)},
            violated={"discharges_m3s": [5.0] * len(_PAIRS_Q)},
        ),
        Constraint(
            name="start_below_levels",
            cls="precondition",
            check=lambda x: (
                x.real("h0_initial") < float(np.min(x.array("water_levels")))
            ),
            text="h0_initial < min(H): the search starts inside its bound, H0 below "
            "every level",
            source=_EQUATION,
            satisfied={"h0_initial": 41.2},
            boundary={"h0_initial": 62.0},
            boundary_holds=False,
            violated={"h0_initial": 70.0},
        ),
        Constraint(
            name="least_squares_minimum",
            cls="precondition",
            check=_settles,
            text="the sum of squares has a minimum that the search reaches in 10,000 "
            "evaluations, at which the curve is a float64 number at every level",
            source=_LEAST_SQUARES,
            satisfied={"h0_initial": 41.2},
            violated={
                "water_levels": list(_UNSETTLED_H),
                "discharges_m3s": list(_UNSETTLED_Q),
                "h0_initial": 9.0,
            },
        ),
        Constraint(
            name="enough_gaugings",
            cls="applicability",
            check=lambda x: x.array("water_levels").size >= 12,
            text="n >= 12: at least 12 to 15 gaugings of the period of analysis",
            source=_GAUGINGS,
            satisfied={"h0_initial": 41.2},
            boundary={
                "water_levels": list(_PAIRS_H[:12]),
                "discharges_m3s": list(_PAIRS_Q[:12]),
            },
            violated={
                "water_levels": list(_BELOW_ZERO_H),
                "discharges_m3s": list(_BELOW_ZERO_Q),
                "h0_initial": -23.0,
            },
        ),
    ),
    constants=(
        Constant(name="least_gaugings", value=12.0, unit="-", source=_GAUGINGS),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="discharges",
                inputs={"discharges_m3s": 1},
                outputs={"a": 1, "std_residuals": 1},
                tolerance=Tolerance(
                    abs=_SMALLEST_NORMAL,
                    reason="the search runs on the discharges divided by a power of "
                    "two, so doubled discharges give the same search and a doubled "
                    "exactly, but below the smallest normal float",
                ),
            ),
        ),
        symmetries=(
            Symmetry(
                name="levels_in_another_unit",
                text="levels and the start in a unit twice as small give the same "
                "curve: a times 2^-b, H0 doubled, b, R2 and s unchanged",
                inputs=_fit_unit,
                outputs=_fit_in_another_unit,
                tolerance=Tolerance(
                    rel=1e-12,
                    abs=1e-300,
                    reason="the same search on the normalised levels; a is scaled "
                    "back by 2^(-eH b), whose exponent rounds once: a few units in the "
                    "last place times eH b",
                ),
            ),
        ),
        limits=(
            Limit(
                name="noise_free_power_law",
                text="pairs of an exact power law give back its a, b and H0, with "
                "levels in cm and in m",
                check=_noise_free,
                source=_EQUATION,
            ),
            Limit(
                name="local_minimum",
                text="no point a step of 1e-4 from the estimate has a smaller sum of "
                "squares",
                check=_local_minimum,
            ),
            Limit(
                name="zero_flow_below_the_levels",
                text="H0 lies below every level of the pairs",
                check=_below_the_levels,
            ),
        ),
    ),
    validation=(
        "none: the least squares give the curve closest to the gaugings on Q; WMO-No. "
        "1044 (sect. 1.12.2) reports no statistic of the agreement of such a fit, and "
        "the research found no open worked example with gaugings and fitted "
        "parameters (WMO-No. 1044, Rantz 1982, Kennedy 1984)"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        (
            "least squares on Q, the arithmetic residuals of every pair weighted "
            "equally; WMO-No. 1044 (sect. 1.12.2) fits the straight line on "
            "logarithmic paper, log Q on log(H - H0), which gives another curve (the "
            "catalog's six gaugings: b = 1.640 on Q, 1.820 in logarithms)"
        ),
        (
            "bounds a >= 0, b >= 0 and H0 below the lowest level by 2^-30 of the "
            "levels' scale (the power of two that brings the largest |H| into "
            "[1/2, 1)), about 5e-7 cm for stages of a few metres"
        ),
        (
            "the search: SciPy's curve_fit, the trust region reflective method with "
            "ftol, xtol and gtol of 1e-12 and at most 10,000 evaluations, from a = 1, "
            "b = 1.5 and H0 = h0_initial, on the levels and discharges divided "
            "exactly by the powers of two that bring their largest magnitudes into "
            "[1/2, 1); the curve is scaled back, so levels in cm or m and discharges "
            "scaled by a power of two give the same curve"
        ),
        (
            "R2 = 1 - SS_res / SS_tot on Q; s the standard deviation of the residuals "
            "with n - 1 (numpy.std, ddof 1)"
        ),
        (
            "H, H0 and h0_initial in one unit of the levels (cm or m); a in m3/s per "
            "(unit of H)^b; Q in m3/s"
        ),
    ),
    assumptions=(
        (
            "the pairs follow one stage-discharge relation of one control over the "
            "period (no shift, hysteresis or variable backwater); the check of spec "
            "rating_curve_plausibility flags curves that do not"
        ),
        "errors in Q only, independent and of equal variance",
    ),
    traps={
        "singular_at_bound": "the fractional power of a head at H0's bound below the "
        "lowest level: test_a_curve_at_its_bound_is_finite",
        "exp_overflow": "the power of the head at the levels' test bounds: "
        "test_levels_at_their_test_bounds_fit_or_are_refused",
        "unbounded_iteration": "the search's bounded count of 10,000 evaluations: "
        "test_a_search_that_does_not_settle_is_refused (precondition "
        "least_squares_minimum)",
        "gap_propagation": "type cases water_levels-nan_element and "
        "discharges_m3s-nan_element: a gap is refused",
        "many_small_terms": "test_many_pairs_keep_their_sums: 20,000 pairs against "
        "math.fsum",
        "moment_cancellation": "test_a_large_mean_discharge_keeps_r_squared: SS_tot "
        "of discharges near 1e6 against exact fractions",
    },
    oracles=(
        Oracle(
            kind="frozen",
            description="R 4.4.3 stats::nls(algorithm = 'port') from a = 1, b = 1.5 "
            "and H0 = min(H) - max(1, 0.1 range), bounds a, b >= 0, H0 <= min(H) - "
            "1e-6: tests/oracles/rating_curve/r_rating_outputs.csv",
            test="tests/unit/test_formulas_hydrometrics.py "
            "(test_the_fit_equals_r_nls_port; the cases of "
            "tests/fixtures/formulas/hydrometrics-cases.json)",
            conventions=(
                "both: least squares on Q, every pair weighted equally",
                "R: the port algorithm (PORT library's nl2sol), Hydrolog: SciPy's "
                "trust "
                "region reflective method on the normalised pairs",
            ),
        ),
        Oracle(
            kind="exact",
            description="pairs of the exact power law Q = 0.012 (H - 32)^1.62 give "
            "back a, b and H0, with levels in cm and in m",
            test="tests/unit/test_formulas_hydrometrics.py (limit noise_free_power_"
            "law; case rating_curve_exact_power_law_and_units)",
        ),
        Oracle(
            kind="algorithm",
            description="the sum of squares at points a step of 1e-4 from the "
            "estimate, by math.fsum",
            test="tests/unit/test_formulas_hydrometrics.py (limit local_minimum)",
        ),
    ),
    base={
        "water_levels": list(_PAIRS_H),
        "discharges_m3s": list(_PAIRS_Q),
        "h0_initial": 41.2,
    },
)

GAUGINGS: Final = constraint_range(
    RATING_CURVE_FIT,
    "enough_gaugings",
    parameter="gaugings",
    value=lambda x: x.array("water_levels").size,
    minimum=12,
)
"""The number of gaugings that the applicability constraint ``enough_gaugings``
bounds: fewer than 12 give the notice ``outside_applicability`` of ``gaugings``."""


def fit_rating_curve(
    water_levels: Levels,
    discharges_m3s: Levels,
    h0_initial: float,
) -> RatingCurveResult:
    """Return the rating curve fitted to stage-discharge pairs, spec rating_curve_fit.

    The second input is the discharge measured at each level in cubic metres per
    second, the third the start of the search for H₀, below every level, in the unit
    of the levels (their names hold digits, which the standard's check of this
    docstring allows nowhere, so they stay out of the list below).

    Parameters
    ----------
    water_levels : array_like of float
        The water level of each gauging, in one unit of the levels.

    Returns
    -------
    RatingCurveResult
        The coefficient, the exponent and the stage of zero flow of the curve, its
        coefficient of determination and the standard deviation of its residuals,
        with the number of pairs; no outlier is removed.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs (``details.reason``, ``details.option`` or
        ``details.constraint``: ``least_squares_minimum`` where the search does not
        settle).

    Warns
    -----
    OutsideApplicability
        For fewer gaugings than the applicability of the fit (``parameter``
        ``gaugings``).
    """
    x = checked_inputs(
        RATING_CURVE_FIT,
        water_levels=water_levels,
        discharges_m3s=discharges_m3s,
        h0_initial=h0_initial,
    )
    fit = cast("_Fit", _fit(x))  # the precondition least_squares_minimum holds
    for category, text in fit.caught:
        warnings.warn(text, category, stacklevel=2)
    out = checked_outputs(
        RATING_CURVE_FIT,
        {
            "a": fit.a,
            "b": fit.b,
            "h0": fit.h0,
            "r_squared": fit.r_squared,
            "std_residuals": fit.std_residuals,
        },
    )
    return RatingCurveResult(
        a=out.real("a"),
        b=out.real("b"),
        h0=out.real("h0"),
        r_squared=out.real("r_squared"),
        std_residuals=out.real("std_residuals"),
        n_points=int(x.array("water_levels").size),
        n_outliers_removed=0,
    )


# ---------------------------------------------------------------------------
# The plausibility of a curve (ADR-0041)
# ---------------------------------------------------------------------------

_LOWEST_EXPONENT: Final = 1.0
_HIGHEST_EXPONENT: Final = 4.0


def _plausibility(x: Values) -> RatingPlausibility:
    levels = x.array("water_levels")
    lowest, highest = float(levels.min()), float(levels.max())
    b = x.real("b")
    exponent = (
        _PLAUSIBLE if _LOWEST_EXPONENT <= b <= _HIGHEST_EXPONENT else "b_out_of_range"
    )
    deep = lowest - x.real("h0") > highest - lowest
    return RatingPlausibility(exponent, "h0_too_low" if deep else _PLAUSIBLE)


def _class_limits(run: Callable[..., Values]) -> None:
    levels = [100.0, 150.0, 200.0]
    for b, verdict in (
        (1.0, _PLAUSIBLE),
        (4.0, _PLAUSIBLE),
        (math.nextafter(1.0, 0.0), "b_out_of_range"),
        (math.nextafter(4.0, 5.0), "b_out_of_range"),
    ):
        found = run(water_levels=levels, b=b, h0=50.0).choice("exponent")
        assert found == verdict, f"b = {b!r} is {found}, not {verdict} (ADR-0041)"
    for h0, verdict in ((0.0, _PLAUSIBLE), (-1e-12, "h0_too_low")):
        found = run(water_levels=levels, b=1.62, h0=h0).choice("zero_flow_stage")
        assert found == verdict, f"H0 = {h0!r} is {found}, not {verdict} (ADR-0041)"


def _two_relations(run: Callable[..., Values]) -> None:
    out = run(water_levels=[45.0, 161.0], b=6.5, h0=-88.0)
    found = (out.choice("exponent"), out.choice("zero_flow_stage"))
    assert found == ("b_out_of_range", "h0_too_low"), (
        f"the curve of two relations at 150170070, 1981-1990, is {found} (ADR-0041)"
    )


def _levels_in_metres(run: Callable[..., Values]) -> None:
    for levels, h0 in (([45.0, 161.0], -88.0), ([62.0, 270.0], 52.6)):
        in_cm = run(water_levels=levels, b=1.62, h0=h0)
        in_m = run(
            water_levels=[level / 100.0 for level in levels], b=1.62, h0=h0 / 100.0
        )
        assert dict(in_cm) == dict(in_m), "the verdict depends on the unit of H"


RATING_CURVE_PLAUSIBILITY: Final = FormulaSpec(
    name="rating_curve_plausibility",
    title="Plausibility of a rating curve as the curve of one stage-discharge relation "
    "(Hydrolog's rule of ADR-0041)",
    function="hydrolog.hydrometrics.rating_curve.rating_curve_plausibility",
    family="classification",
    equation=(
        "b_out_of_range unless 1 <= b <= 4; h0_too_low if min(H) - H0 > max(H) - min(H)"
    ),
    latex=(
        r"b \notin [1, 4] \Rightarrow \text{b\_out\_of\_range},\quad"
        r" \min H - H_0 > \max H - \min H \Rightarrow \text{h0\_too\_low}"
    ),
    variables=(
        _levels_variable("The levels of the pairs the curve was fitted to.", 1),
        _exponent_variable("The exponent of the curve."),
        _zero_flow_variable("The gauge height of zero flow of the curve."),
    ),
    outputs=(
        Output(
            name="exponent",
            unit="-",
            kind="choice",
            choices=(_PLAUSIBLE, "b_out_of_range"),
            description="Whether b lies from 1 to 4.",
        ),
        Output(
            name="zero_flow_stage",
            unit="-",
            kind="choice",
            choices=(_PLAUSIBLE, "h0_too_low"),
            description="Whether H0 lies below the lowest level by at most the range "
            "of the levels.",
        ),
    ),
    sources=(_ADR_0041, _SECTION_CONTROLS, _REAL_SECTION_CONTROL),
    constants=(
        Constant(
            name="lowest_exponent",
            value=_LOWEST_EXPONENT,
            unit="-",
            source=_ADR_0041,
        ),
        Constant(
            name="highest_exponent",
            value=_HIGHEST_EXPONENT,
            unit="-",
            source=_ADR_0041,
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="levels",
                inputs={"water_levels": 1, "h0": 1},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the verdicts compare differences of levels, which a power "
                    "of two scales exactly (the generic check compares no choice; "
                    "limit levels_in_metres does)",
                ),
            ),
        ),
        limits=(
            Limit(
                name="class_limits",
                text="b = 1 and b = 4 are plausible, the next floats beyond are not; "
                "H0 exactly the range below the lowest level is plausible, a little "
                "deeper is not",
                check=_class_limits,
                source=_ADR_0041,
            ),
            Limit(
                name="two_relations",
                text="the curve of two relations at IMGW-PIB 150170070, 1981-1990 (b = "
                "6.5, H0 = -88 cm under stages of 45 to 161 cm), fails both",
                check=_two_relations,
                source=_ADR_0041,
            ),
            Limit(
                name="levels_in_metres",
                text="the verdicts of levels in cm and in m are the same",
                check=_levels_in_metres,
            ),
        ),
    ),
    validation=(
        "none: a heuristic of Hydrolog (ADR-0041), checked against no observations; "
        "WMO-No. 1044 shows a real section control whose rating has a slope of about "
        "4.3 below 1.4 m (fig. II.1.5, p. II.1-9), which the rule flags b_out_of_range"
    ),
    formula_version=1,
    status="unreferenced",
    conventions=(
        (
            "b from 1 to 4, bounds included: section controls 1.5 to 2.5 and 2 or "
            "more in natural channels, channel controls usually below 2 (WMO-No. "
            "1044, pp. II.1-2 and II.1-8), compound sections and overbank flow left "
            "in; "
            "a real section control of slope 4.3 (fig. II.1.5) is flagged"
        ),
        (
            "H0 at most the range of the levels below the lowest level, bound "
            "included: Hydrolog's own bound; the levels are those of the pairs given "
            "to the fit, before outliers are removed"
        ),
        "a verdict, not a refusal: the curve is still given (ADR-0041)",
    ),
    assumptions=(
        "a curve fitted to the pairs of two relations (a gauge zero moved, a channel "
        "changed within the period) has a steep b and an H0 far below every level",
    ),
    traps={
        "class_limit": "limit class_limits: b = 1, b = 4 and H0 at the range below "
        "the lowest level, and the next values beyond them",
        "gap_propagation": "type case water_levels-nan_element: a gap is refused",
    },
    base={"water_levels": list(_PAIRS_H), "b": 1.62, "h0": 32.0},
)


def rating_curve_plausibility(
    water_levels: Levels, b: float, h0: float
) -> RatingPlausibility:
    """Return whether a rating curve is one relation, spec rating_curve_plausibility.

    The last input is the curve's gauge height of zero flow H₀, in the unit of the
    levels (its name holds a digit, which the standard's check of this docstring
    allows nowhere, so it stays out of the list below).

    Parameters
    ----------
    water_levels : array_like of float
        The levels of the pairs the curve was fitted to.
    b : float
        The exponent of the curve.

    Returns
    -------
    RatingPlausibility
        ``exponent`` and ``zero_flow_stage``, each ``plausible`` or the reason it is
        not; ``reasons`` lists the reasons.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs (``details.reason``, ``details.option``).

    Warns
    -----
    UnreferencedFormula
        On every result: the rule is Hydrolog's own and no source publishes it.
    """
    x = checked_inputs(RATING_CURVE_PLAUSIBILITY, water_levels=water_levels, b=b, h0=h0)
    verdict = _plausibility(x)
    out = checked_outputs(
        RATING_CURVE_PLAUSIBILITY,
        {"exponent": verdict.exponent, "zero_flow_stage": verdict.zero_flow_stage},
    )
    return RatingPlausibility(out.choice("exponent"), out.choice("zero_flow_stage"))


# ---------------------------------------------------------------------------
# Rybczyński's zones
# ---------------------------------------------------------------------------

_DURATION_LIMIT_PCT: Final = 50.0
_RYBCZYNSKI = Source(
    citation="Rybczyński, M. (1932). Kilka uwag o charakterystyce przepływów. Biuletyn "
    "Towarzystwa Geofizyków w Warszawie 4-5; and his lecture notes of 1923",
    locator="not opened: the names NTW, STW and WTW and the limits of the zones are "
    "not confirmed from the source (research of 2026-11-18, trend-regime sect. 3.12)",
    access="author-provided",
)
_HISTOGRAM_SOURCE = Source(
    citation="Hydrolog's water level data: tests/fixtures/station_daily.csv and the "
    "classes of 5 to 20 cm of the catalog's and the tests' examples",
    locator="1,811 daily stages of 45 to 329 cm: classes of 10 cm hold up to 483 "
    "levels, of 20 cm up to 815",
)


def _zone_limits(
    edges: NDArray[np.float64], counts: NDArray[np.float64]
) -> tuple[float, float]:
    """Return the upper limits of NTW and STW of a histogram of levels.

    NTW ends at the centre of the most frequent class (the first of equal ones), STW
    at the centre of the first class at whose lower edge the duration curve falls
    below 50 %; failing that, at the centre of the class above the most frequent one,
    and one class width above NTW when that is the last class.
    """
    centres = 0.5 * (edges[:-1] + edges[1:])
    frequency = counts / float(counts.sum()) * 100.0
    duration = 100.0 - np.concatenate([[0.0], np.cumsum(frequency)[:-1]])
    peak = int(np.argmax(frequency))
    ntw = float(centres[peak])
    below = np.flatnonzero(duration < _DURATION_LIMIT_PCT)
    above = min(peak + 1, centres.size - 1)
    stw = float(centres[int(below[0]) if below.size else above])
    if stw <= ntw:
        stw = float(centres[above])
        if stw <= ntw:
            stw = ntw + float(edges[peak + 1] - edges[peak])
    return ntw, stw


def _worked_example(run: Callable[..., Values]) -> None:
    out = run(
        bin_edges=[100.0, 110.0, 120.0, 130.0, 140.0, 150.0],
        counts=[12.0, 40.0, 25.0, 15.0, 8.0],
    )
    assert_within(
        [out.real("ntw_upper"), out.real("stw_upper")],
        [115.0, 125.0],
        abs=0.0,
        reason="whole numbers: the most frequent class is 110-120, the duration at "
        "120 is 48 %, below 50 %",
    )


def _fallbacks(run: Callable[..., Values]) -> None:
    for counts, expected in (
        ([1.0, 1.0, 3.0], [25.0, 35.0]),
        ([1.0, 3.0, 2.0], [15.0, 25.0]),
        ([3.0, 1.0, 3.0], [5.0, 25.0]),
    ):
        out = run(bin_edges=[0.0, 10.0, 20.0, 30.0], counts=counts)
        assert_within(
            [out.real("ntw_upper"), out.real("stw_upper")],
            expected,
            abs=0.0,
            reason="whole numbers: the last class most frequent puts STW a class above "
            "it; no duration below 50 % puts STW in the class above the peak; of equal "
            "classes the first is the peak",
        )


def _half_duration(run: Callable[..., Values]) -> None:
    out = run(bin_edges=[0.0, 10.0, 20.0, 30.0, 40.0], counts=[1.0, 1.0, 1.0, 1.0])
    assert_within(
        out.real("stw_upper"),
        35.0,
        abs=0.0,
        reason="the duration at 20 is 50 %, not below it: STW ends in the next class",
    )


RYBCZYNSKI_ZONES: Final = FormulaSpec(
    name="rybczynski_zones",
    title="Rybczyński's zones of low, medium and high background water levels (NTW, "
    "STW, WTW)",
    function="hydrolog.hydrometrics.rating_curve.rybczynski_zones",
    family="classification",
    equation=(
        "NTW ends at the centre of the most frequent class; STW at the centre of the "
        "first class i with D_i < 50 %, D_i = 100 - sum(f_j, j < i), f_j = 100 n_j / "
        "sum(n)"
    ),
    latex=(
        r"H_{NTW} = c_{\arg\max_i f_i},\quad H_{STW} = c_{\min\{i:\, D_i < 50\%\}},"
        r"\quad D_i = 100 - \sum_{j<i} f_j,\quad f_j = \frac{100\,n_j}{\sum n}"
    ),
    variables=(
        Variable(
            name="bin_edges",
            symbol="e",
            unit="cm",
            kind="real_array",
            description="The edges of the classes of levels, increasing.",
            physical=Range(
                test_low=-_LEVEL_TEST, test_high=_LEVEL_TEST, test_reason=_LEVEL_REASON
            ),
            applicability="unstated",
            typical=Range(low=-10.0, high=340.0, source=_LEVELS_SOURCE),
            min_length=2,
        ),
        Variable(
            name="counts",
            symbol="n",
            unit="-",
            kind="real_array",
            description="The number of levels in each class.",
            physical=Range(
                low=0.0,
                test_high=1.0e6,
                test_reason="a million levels in a class, the hourly stages of more "
                "than a century",
            ),
            applicability="unstated",
            typical=Range(low=0.0, high=820.0, source=_HISTOGRAM_SOURCE),
        ),
    ),
    outputs=(
        Output(
            name="ntw_upper",
            unit="cm",
            symbol="H_{NTW}",
            description="The upper limit of the low background water (NTW).",
            physical=Range(),
        ),
        Output(
            name="stw_upper",
            unit="cm",
            symbol="H_{STW}",
            description="The upper limit of the medium background water (STW).",
            physical=Range(),
        ),
    ),
    sources=(_RYBCZYNSKI,),
    constraints=(
        Constraint(
            name="one_count_per_class",
            cls="physical",
            check=lambda x: x.array("bin_edges").size == x.array("counts").size + 1,
            text="one count per class between two edges",
            source=_RYBCZYNSKI,
            satisfied={"counts": [12.0, 40.0, 25.0, 15.0, 8.0]},
            violated={"counts": [12.0, 40.0, 25.0, 15.0]},
        ),
        Constraint(
            name="edges_increasing",
            cls="physical",
            check=lambda x: bool(np.all(np.diff(x.array("bin_edges")) > 0.0)),
            text="e[i+1] > e[i]: classes of positive width, from the lowest level up",
            source=_RYBCZYNSKI,
            satisfied={"bin_edges": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0]},
            violated={"bin_edges": [100.0, 110.0, 120.0, 120.0, 140.0, 150.0]},
        ),
        Constraint(
            name="some_levels",
            cls="precondition",
            check=lambda x: float(np.sum(x.array("counts"))) > 0.0,
            text="sum(n) > 0: the frequencies need levels",
            source=_RYBCZYNSKI,
            satisfied={"counts": [0.0, 1.0, 0.0, 0.0, 0.0]},
            violated={"counts": [0.0, 0.0, 0.0, 0.0, 0.0]},
        ),
    ),
    constants=(
        Constant(
            name="duration_limit_pct",
            value=_DURATION_LIMIT_PCT,
            unit="%",
            source=_RYBCZYNSKI,
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="levels",
                inputs={"bin_edges": 1},
                outputs={"ntw_upper": 1, "stw_upper": 1},
                tolerance=Tolerance(
                    abs=_SMALLEST_NORMAL,
                    reason="centres and widths of doubled edges double exactly, but "
                    "below the smallest normal float",
                ),
            ),
            Scaling(
                name="counts",
                inputs={"counts": 1},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="doubled counts give the same frequencies to the last bit",
                ),
            ),
        ),
        limits=(
            Limit(
                name="worked_example",
                text="the most frequent class and the duration below 50 %",
                check=_worked_example,
            ),
            Limit(
                name="fallbacks",
                text="STW when no duration falls below 50 % and when the most "
                "frequent class is the last; of equal classes, the first",
                check=_fallbacks,
            ),
            Limit(
                name="half_duration",
                text="a duration of exactly 50 % is not below it",
                check=_half_duration,
            ),
        ),
    ),
    validation="none: Rybczyński's source was not opened",
    formula_version=1,
    status="unreferenced",
    conventions=(
        (
            "the limits are class centres: NTW ends at the centre of the most "
            "frequent class (the first of equal ones), STW at the centre of the first "
            "class at whose lower edge the duration (the share of levels at or above "
            "it) is below 50 %"
        ),
        (
            "when no class has a duration below 50 %, or STW would not lie above NTW, "
            "STW ends at the centre of the class above the most frequent one; when "
            "that is the last class, one class width above NTW, beyond the highest "
            "edge (WTW then runs backwards)"
        ),
        (
            "the classes and counts of spec water_level_frequency (Tier B), levels in "
            "cm or m"
        ),
    ),
    assumptions=(
        "the levels of a long series, daily or more often, of one gauge zero",
    ),
    traps={
        "class_limit": "limit half_duration: a duration of exactly 50 %; limit "
        "fallbacks: equal most frequent classes",
        "gap_propagation": "type cases bin_edges-nan_element and counts-nan_element: "
        "a gap is refused",
    },
    base={
        "bin_edges": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0],
        "counts": [12.0, 40.0, 25.0, 15.0, 8.0],
    },
)


def rybczynski_zones(bin_edges: Levels, counts: Levels) -> WaterLevelZones:
    """Return Rybczyński's zones of levels from their histogram, spec rybczynski_zones.

    Parameters
    ----------
    bin_edges : array_like of float
        The edges of the classes of levels, increasing, in the unit of the levels.
    counts : array_like of float
        The number of levels in each class.

    Returns
    -------
    WaterLevelZones
        The upper limits of NTW and STW and the range of each zone, from the lowest
        to the highest edge.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs (``details.reason``, ``details.option`` or
        ``details.constraint``).

    Warns
    -----
    UnreferencedFormula
        On every result: Rybczyński's source was not opened.
    """
    x = checked_inputs(RYBCZYNSKI_ZONES, bin_edges=bin_edges, counts=counts)
    edges = x.array("bin_edges")
    ntw, stw = _zone_limits(edges, x.array("counts"))
    out = checked_outputs(RYBCZYNSKI_ZONES, {"ntw_upper": ntw, "stw_upper": stw})
    ntw, stw = out.real("ntw_upper"), out.real("stw_upper")
    low, high = float(edges[0]), float(edges[-1])
    return WaterLevelZones(
        ntw_upper=ntw,
        stw_upper=stw,
        ntw_range=(low, ntw),
        stw_range=(ntw, stw),
        wtw_range=(stw, high),
    )


SPECS: Final[tuple[FormulaSpec, ...]] = (
    RATING_CURVE,
    RATING_CURVE_FIT,
    RATING_CURVE_PLAUSIBILITY,
    RYBCZYNSKI_ZONES,
)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""

TIER_B: Final = (
    TierBSpec(
        name="water_level_frequency",
        function="hydrolog.hydrometrics.rating_curve.WaterLevelFrequency."
        "frequency_distribution",
        definition="classes of bin_width from the lowest level rounded down to a whole "
        "unit up to the first edge above the highest level rounded up; the count of "
        "each class, its frequency 100 n_i / n %, the cumulative frequency from the "
        "lowest class and the duration D_i = 100 - the cumulative frequency below "
        "class i, the share of levels at or above its lower edge",
        convention="classes [lower, upper) of numpy.histogram, the last one closed; "
        "the first edge a whole unit of the levels (cm or m), so the classes depend on "
        "the unit; duration as the share equalled or exceeded",
        source=Source(
            citation="Searcy, J.K. (1959). Flow-duration curves. Manual of Hydrology: "
            "Part 2, Low-flow techniques. U.S. Geological Survey Water-Supply Paper "
            "1542-A",
            locator="p. 2: the percent of time a value was equalled or exceeded; p. "
            "6: class intervals barely including the extremes of the record",
            url="https://pubs.usgs.gov/wsp/1542a/report.pdf",
        ),
    ),
    TierBSpec(
        name="rating_curve_start",
        function="hydrolog.hydrometrics.rating_curve.RatingCurve.fit",
        definition="without h0_initial the search starts at H0 = min(H) - max(1, "
        "0.1 (max(H) - min(H))), below every level whatever their sign",
        convention="one unit of the levels at least (1 cm or 1 m), so the start "
        "depends on the unit; starts 0.1 to 1 range below the lowest level reached "
        "the same least squares in Hydrolog's benchmark of synthetic curves",
        source=Source(
            citation="Hydrolog, docs/COMPUTATION_PATHS.md",
            locator="sect. 3.8, the H0 starting point (0.8.0); the R oracle of the "
            "research starts there too (tests/oracles/rating_curve/r_rating_oracle.R)",
        ),
        constants=(
            Constant(
                name="start_fraction",
                value=0.1,
                unit="-",
                source=Source(
                    citation="Hydrolog, docs/COMPUTATION_PATHS.md",
                    locator="sect. 3.8, the H0 starting point",
                ),
            ),
        ),
    ),
    TierBSpec(
        name="rating_curve_outlier_screening",
        function="hydrolog.hydrometrics.rating_curve.RatingCurve.fit",
        definition="with remove_outliers, the pairs whose residual from the first fit "
        "exceeds outlier_std standard deviations of the residuals (n - 1) are left out "
        "and the curve is fitted again to the rest, once, when at least 3 remain",
        convention="one pass, |r| > k s left out and |r| = k s kept; the start of the "
        "second fit is that of the first; Hydrolog's own rule, while WMO-No. 1044 "
        "(sect. 1.12.1) checks a gauging that departs from the curve by more than 5 "
        "per cent by a check measurement",
        source=Source(
            citation=_WMO_1044,
            locator="sect. 1.12.1, pp. II.1-19 to II.1-20: a measurement that does not "
            "check the rating by 5 per cent is repeated",
            url=_WMO_URL,
        ),
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""


# ---------------------------------------------------------------------------
# The classes of the library
# ---------------------------------------------------------------------------

_FIT_ARGUMENTS: Final = {
    "discharges_m3s": "discharges",
    "same_length": "discharges",
    "start_below_levels": "h0_initial",
}
"""The argument of ``RatingCurve`` a refusal of the spec rating_curve_fit names when
it differs from the input (or names a constraint)."""
_FIT_HINTS: Final = {
    "start_below_levels": "Give h0_initial lower than every water level, in the same "
    "unit.",
    "least_squares_minimum": "Check the measurement pairs or try another h0_initial.",
}
"""The hints of the refusals of the spec rating_curve_fit that ``RatingCurve`` gives."""


def _fit_error(exc: InvalidParameterError) -> InvalidParameterError:
    """Return a refusal of ``fit_rating_curve`` with the argument of ``RatingCurve``."""
    subject = exc.details.get("variable") or exc.details.get("constraint")
    if not isinstance(subject, str):
        return exc
    argument = _FIT_ARGUMENTS.get(subject)
    hint = _FIT_HINTS.get(subject, exc.hint)
    if argument is None and hint == exc.hint:
        return exc
    named = {"option": argument} if argument is not None else {}
    return InvalidParameterError(str(exc), details={**exc.details, **named}, hint=hint)


def _default_h0_initial(water_levels: object) -> float:
    """Return the start of H0 without ``h0_initial`` (Tier B ``rating_curve_start``).

    ``min(H) - max(1, 0.1 * (max(H) - min(H)))`` of the finite levels, in their unit:
    below every level, whatever their sign. Levels the spec refuses start at 0, as
    the refusal comes first.
    """
    try:
        levels = np.asarray(water_levels, dtype=np.float64)
    except (TypeError, ValueError):
        return 0.0
    finite = levels[np.isfinite(levels)]
    if finite.size == 0:
        return 0.0
    lowest = float(finite.min())
    return lowest - max(1.0, 0.1 * (float(finite.max()) - lowest))


class RatingCurve:
    """
    Fit a power-law rating curve Q = a * (H - H0)^b to paired measurements.

    The fit is spec ``rating_curve_fit`` (:func:`fit_rating_curve`), the curve spec
    ``rating_curve`` (:func:`rating_discharge`); the specs check the measurements when
    ``fit`` and ``predict`` use them.

    Parameters
    ----------
    water_levels : array_like of float
        Observed water levels H, in one unit, e.g. cm (IMGW-PIB stages) or m; the
        unit of ``h0`` and of ``a`` follows it.
    discharges : array_like of float
        Corresponding discharge measurements Q [m³/s].

    Examples
    --------
    Fifteen gaugings with H in cm, the 170 cm one an outlier:

    >>> import numpy as np
    >>> h = np.array([62.0, 75.0, 88.0, 101.0, 115.0, 128.0, 142.0, 155.0,
    ...               170.0, 185.0, 200.0, 218.0, 235.0, 252.0, 270.0])
    >>> q = np.array([1.05, 2.14, 3.40, 4.67, 6.32, 8.27, 10.48, 12.46,
    ...               20.75, 17.72, 20.50, 23.40, 26.63, 31.80, 34.92])
    >>> rc = RatingCurve(h, q)
    >>> result = rc.fit(h0_initial=40.0, remove_outliers=True)
    >>> result.n_outliers_removed, round(result.b, 3), round(result.r_squared, 4)
    (1, 1.513, 0.9991)
    >>> rc.predict(np.array([100.0, 200.0])).round(2).tolist()
    [4.67, 20.3]
    """

    def __init__(self, water_levels: Levels, discharges: Levels) -> None:
        self._h: Levels = water_levels
        self._q: Levels = discharges
        self._result: RatingCurveResult | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(
        self,
        h0_initial: float | None = None,
        remove_outliers: bool = False,
        outlier_std: float = 2.0,
    ) -> RatingCurveResult:
        """
        Fit the rating curve Q = a * (H - H0)^b using non-linear least squares.

        Parameters
        ----------
        h0_initial : float or None, optional
            Initial guess for H0 (zero-flow level), in the unit of the water
            levels. By default (``None``) it is chosen from the data, below the
            lowest water level by a tenth of the range of the levels and by at
            least one unit: ``min(H) - max(1, 0.1 * (max(H) - min(H)))``. Such a
            start is admissible whatever the sign of the levels (stages below the
            gauge zero are normal). A given value must lie below the lowest water
            level (H0 is bounded by it).
        remove_outliers : bool, optional
            If True, remove points whose residuals exceed ``outlier_std``
            standard deviations and fit again (when at least 3 remain), by default
            False.
        outlier_std : float, optional
            Threshold in standard deviations for outlier removal,
            by default 2.0.

        Returns
        -------
        RatingCurveResult
            Fitted parameters and goodness-of-fit statistics.

        Raises
        ------
        InvalidParameterError
            If spec ``rating_curve_fit`` refuses the pairs or the start
            (``details.reason`` of the standard; ``details.option`` ``water_levels``,
            ``discharges`` or ``h0_initial``): values that are not finite, lengths
            that differ, fewer than 3 pairs, levels or discharges all equal, a start
            not below the lowest level (``details.constraint``
            ``start_below_levels``), or least squares on which the search does not
            settle (``least_squares_minimum``).

        Warns
        -----
        OutsideApplicability
            For fewer than 12 gaugings (``parameter`` ``gaugings``, WMO-No. 1044).

        Notes
        -----
        The rating equation is the power-law stage-discharge relation
        ``Q = a (H - H0)^b`` with ``H0`` the stage of zero flow (WMO-No. 1044,
        2010, Vol. II, eq. 1.4). The least-squares problem is not convex in ``H0``:
        the start must be admissible (below every level) and should not be far from
        the solution.

        Versions before 0.8.0 started from ``h0_initial = 0.0``, which is not
        below the lowest level of a gauge with readings at or below zero (stages
        below the gauge zero, e.g. -10 cm, are normal): such a series could not be
        fitted without choosing a start by hand. In a benchmark of synthetic
        rating curves (levels in cm and m, positive and negative, 1-8 % noise,
        6-30 gaugings) starts between 0.1 and 1 range below the lowest level all
        reached the best least-squares solution.
        """
        start = _default_h0_initial(self._h) if h0_initial is None else h0_initial
        try:
            result = fit_rating_curve(self._h, self._q, start)
            if remove_outliers:
                result = self._screened(result, start, outlier_std)
        except InvalidParameterError as exc:
            raise _fit_error(exc) from exc
        self._result = result
        return result

    def predict(self, water_levels: Levels) -> NDArray[np.float64]:
        """
        Predict discharge for given water levels using the fitted curve.

        The curve is spec ``rating_curve`` (:func:`rating_discharge`): no discharge
        at and below H0.

        Parameters
        ----------
        water_levels : array_like of float
            Water levels to predict discharge for, of any shape.

        Returns
        -------
        NDArray[np.float64]
            Predicted discharge values [m³/s], in the shape of the levels.

        Raises
        ------
        RuntimeError
            If ``fit()`` has not been called yet.
        InvalidParameterError
            If the spec refuses the levels (a value that is not finite, a string).
        """
        if self._result is None:
            raise RuntimeError("Call fit() before predict().")
        levels = np.asarray(water_levels)
        curve = rating_discharge(
            levels.reshape(-1), self._result.a, self._result.b, self._result.h0
        )
        return curve.reshape(levels.shape)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _screened(
        self, first: RatingCurveResult, start: float, outlier_std: float
    ) -> RatingCurveResult:
        """Fit again without the pairs of large residuals (Tier B screening)."""
        levels = np.asarray(self._h, dtype=np.float64)
        discharges = np.asarray(self._q, dtype=np.float64)
        residuals = discharges - rating_discharge(levels, first.a, first.b, first.h0)
        spread = float(np.std(residuals, ddof=1))
        keep = np.abs(residuals) <= outlier_std * spread
        removed = int(keep.size - np.count_nonzero(keep))
        if removed == 0 or np.count_nonzero(keep) < 3:
            return first
        again = fit_rating_curve(levels[keep], discharges[keep], start)
        return dataclasses.replace(again, n_outliers_removed=removed)


# ---------------------------------------------------------------------------
# Water level frequency analysis
# ---------------------------------------------------------------------------


class WaterLevelFrequency:
    """
    Frequency and duration analysis of water level time series.

    Builds a histogram of water levels and derives:
    - Relative frequency [%]
    - Cumulative frequency [%]
    - Duration (exceedance) curve [%]
    - Rybczyński water level zones (NTW / STW / WTW), spec ``rybczynski_zones``

    Parameters
    ----------
    water_levels : NDArray[np.float64]
        Time series of water level observations [cm or m].
    bin_width : float, optional
        Width of histogram bins in the same units as water_levels,
        by default 10.0.

    Raises
    ------
    InvalidParameterError
        If ``water_levels`` is empty or ``bin_width`` is not positive.

    Examples
    --------
    >>> import numpy as np
    >>> rng = np.random.default_rng(0)
    >>> levels = rng.uniform(100, 300, size=500)
    >>> wlf = WaterLevelFrequency(levels, bin_width=20.0)
    >>> result = wlf.frequency_distribution()
    >>> round(float(result.frequency_pct.sum()), 1)
    100.0
    >>> import warnings
    >>> with warnings.catch_warnings():
    ...     warnings.simplefilter("ignore")
    ...     zones = WaterLevelFrequency([150.0, 152.0, 155.0, 161.0, 158.0], 10.0)
    ...     zones = zones.rybczynski_zones()
    >>> zones.ntw_upper, zones.stw_upper
    (155.0, 165.0)
    """

    def __init__(
        self,
        water_levels: NDArray[np.float64] | Sequence[float],
        bin_width: float = 10.0,
    ) -> None:
        water_levels = np.asarray(water_levels, dtype=np.float64)

        if water_levels.size == 0:
            raise InvalidParameterError("water_levels must not be empty.")
        if bin_width <= 0.0:
            raise InvalidParameterError(f"bin_width must be positive, got {bin_width}")

        self._h: NDArray[np.float64] = water_levels
        self._bin_width: float = float(bin_width)
        self._freq_result: FrequencyDistributionResult | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def frequency_distribution(self) -> FrequencyDistributionResult:
        """
        Compute histogram-based frequency and duration distribution.

        Tier B ``water_level_frequency``: classes of ``bin_width`` from the lowest
        level rounded down to a whole unit.

        Returns
        -------
        FrequencyDistributionResult
            Bin edges, centres, counts, frequency [%], cumulative
            frequency [%], and duration (exceedance) curve [%].
        """
        h_min = math.floor(float(np.min(self._h)))
        h_max = math.ceil(float(np.max(self._h)))

        # Extend upper edge so the maximum value falls inside the last bin
        bin_edges = np.arange(h_min, h_max + self._bin_width, self._bin_width)
        # Ensure the last edge exceeds the maximum observation
        while bin_edges[-1] <= h_max:
            bin_edges = np.append(bin_edges, bin_edges[-1] + self._bin_width)

        histogram, _ = np.histogram(self._h, bins=bin_edges)
        counts = histogram.astype(np.float64)
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

        total = float(counts.sum())
        frequency_pct = counts / total * 100.0 if total > 0.0 else counts.copy()
        cumulative_frequency_pct = np.cumsum(frequency_pct)

        # Duration (exceedance): share of the levels at or above the lower edge of
        # class i = 100 - cumulative up to (but not including) class i
        duration_pct = 100.0 - np.concatenate([[0.0], cumulative_frequency_pct[:-1]])

        result = FrequencyDistributionResult(
            bin_edges=bin_edges,
            bin_centers=bin_centers,
            counts=counts,
            frequency_pct=frequency_pct,
            cumulative_frequency_pct=cumulative_frequency_pct,
            duration_pct=duration_pct,
        )
        self._freq_result = result
        return result

    def rybczynski_zones(self) -> WaterLevelZones:
        """
        Delimit Rybczyński water level zones from frequency distribution.

        Spec ``rybczynski_zones`` (:func:`rybczynski_zones`) on the classes and counts
        of :meth:`frequency_distribution`.

        Zone definitions
        ----------------
        NTW (Niskie Tło Wodne)
            Low background water: water levels up to the centre of the modal (most
            frequent) class.
        STW (Średnie Tło Wodne)
            Medium background water: water levels from there up to the centre of
            the first class at whose lower edge the duration curve falls below 50 %.
        WTW (Wysokie Tło Wodne)
            High background water: remaining (high) water levels.

        Returns
        -------
        WaterLevelZones
            Boundary values and ranges for each zone.

        Warns
        -----
        UnreferencedFormula
            On every result: Rybczyński's source was not opened.
        """
        result = self._freq_result
        if result is None:
            result = self.frequency_distribution()
        return rybczynski_zones(result.bin_edges, result.counts)
