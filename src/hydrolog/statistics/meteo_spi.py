"""Standardized precipitation index and relative precipitation of months and years.

The SPI of a month for a scale of k months is the standard normal quantile of the sum
of the k months that end in it under the distribution of such sums of the same
calendar month: a gamma distribution fitted by Thom's approximation of maximum
likelihood to the positive sums, mixed with the probability of a zero sum (McKee et
al., 1993; Edwards and McKee, 1997; WMO, 2012). The formulas are declared by their
specs (Nogat's computation standard, ADR-0050 and ADR-0059): :data:`GAMMA_FIT`
(``spi_gamma_fit``), :data:`SPI` (``spi``), :data:`YEAR_CLASS` (``kaczorowska_class``)
and :data:`MONTH_CLASS` (``month_precipitation_class``); ``docs/FORMULAS.md`` shows
their equations, constants, ranges and sources.

A calendar month is fitted when its sums are known in at least 80 % of the years of
the reference period (WMO-No. 1203, 4.4.2) and the spec of the fit accepts them (enough
positive sums, not all equal). The distributions are fitted to the k-month sums of a
reference period (``reference_first_year`` to ``reference_last_year``, by default the
analysed years), and the SPI of each analysed month is that of its own sum: the SPI
compares a total with the totals of the same months in the years on record (WMO,
2012, 5.1.1 and 5.1.2), which should be at least 30 years (WMO, 2012, chapter 2: 20-30
years at least, 50-60 preferred, after Guttman, 1994); the Copernicus European Drought
Observatory fits its gridded SPI on the baseline 1991-2020 and that of its synop
stations on 1981-2010 (EDO, 2025). The k-month sums of each period stay within its own
years.

The relative precipitation is the sum in % of its normal, the mean of the reference
period for a month and the sum of the twelve monthly normals for a year (WMO-No. 1203,
4.3.3). A year is classed by Kaczorowska (1962), whose classes are ranges of whole
percents: the percentage counts in the class of its whole-number rounding, a half
rounded up. Kaczorowska gave no classes of months; a month is classed by the limits
used for months in Polish practice (Tomaszewska, 1994, after Kosiba, 1948, as given by
Gąsiorek and Musiał, 2011).

References
----------
McKee, T. B., Doesken, N. J. & Kleist, J. (1993): The relationship of drought frequency
    and duration to time scales. 8th Conference on Applied Climatology, Anaheim,
    179-184.
Edwards, D. C. & McKee, T. B. (1997): Characteristics of 20th century drought in the
    United States at multiple time scales. Climatology Report 97-2, Colorado State
    University.
Thom, H. C. S. (1958): A note on the gamma distribution. Monthly Weather Review 86(4),
    117.
Guttman, N. B. (1994): On the sensitivity of sample L moments to sample size. Journal
    of Climate 7(6), 1026-1029.
WMO (2012): Standardized Precipitation Index User Guide. WMO-No. 1090, Geneva.
WMO (2017): WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203.
EDO (2025): Standardized Precipitation Index (SPI). EDO and GDO indicator factsheet,
    Copernicus European and Global Drought Observatories.
Kaczorowska, Z. (1962): Opady w Polsce w przekroju wieloletnim. Prace Geograficzne
    IG PAN 33.
Gąsiorek, E. & Musiał, E. (2011): Porównanie i klasyfikacja warunków opadowych na
    podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu.
    Woda-Środowisko-Obszary Wiejskie 11(4), 107-119 (Table 1 and p. 108).

Examples
--------
>>> fit = fit_gamma([0.0, 10.0, 20.0, 40.0, 30.0])
>>> round(fit.alpha, 4), round(fit.beta_mm, 4), fit.zero_probability
(4.2663, 5.8599, 0.2)
>>> spi_values(np.array([0.0, 25.0, np.nan]), *fit).round(4)
array([-0.8416,  0.3895,     nan])
>>> year_precipitation_class(74.5), month_precipitation_class(74.5)
('dry', 'dry')
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from statistics import NormalDist
from typing import Final, NamedTuple

import numpy as np
from numpy.typing import NDArray
from scipy.special import gammainc, gammaincc, ndtri

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
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._climate import (
    WMO_NORMAL_SHARE,
    finite,
    monthly_normals,
    multimonth_normal,
    precipitation_periods,
    rolling_sum,
    round_sums,
)

__all__ = [
    "DEFAULT_SCALES_MONTHS",
    "GAMMA_FIT",
    "GammaFit",
    "KACZOROWSKA_CLASSES",
    "MONTH_CLASS",
    "SPECS",
    "SPI",
    "SPI_LIMIT",
    "SpiMonth",
    "SpiPeriod",
    "SpiScale",
    "SpiYear",
    "StandardizedPrecipitation",
    "TIER_B",
    "YEAR_CLASS",
    "fit_gamma",
    "month_precipitation_class",
    "spi_values",
    "standardized_precipitation_index",
    "year_precipitation_class",
]

DEFAULT_SCALES_MONTHS: tuple[int, ...] = (1, 3, 6, 12)
"""Scales of the SPI [months] (McKee et al., 1993; WMO-No. 1090)."""
KACZOROWSKA_CLASSES: tuple[str, ...] = (
    "extremely_dry",
    "very_dry",
    "dry",
    "normal",
    "wet",
    "very_wet",
    "extremely_wet",
)
"""The classes of relative precipitation, driest first."""


@dataclass
class GammaFit(JsonResultMixin):
    """The gamma distribution of the k-month sums of one calendar month.

    Attributes
    ----------
    month : int
        Calendar month the sums end in.
    alpha : float or None
        Shape of the gamma distribution; ``None`` without a fit.
    beta : float or None
        Its scale [mm].
    zero_probability : float or None
        q, the share of zero sums.
    n_values : int
        Sums of the reference period the fit is made from.
    """

    month: int
    alpha: float | None
    beta: float | None
    zero_probability: float | None
    n_values: int


# --- sources -------------------------------------------------------------------------

_KUMAR = (
    "Naresh Kumar, M., Murthy, C. S., Sesha Sai, M. V. R. and Roy, P. S. (2009). On "
    "the use of Standardized Precipitation Index (SPI) for drought intensity "
    "assessment. Meteorological Applications 16(3), 381-389; open preprint "
    "arXiv:1509.04808"
)
_KUMAR_URL = "https://arxiv.org/pdf/1509.04808"
_MCSWEENEY = Source(
    citation="McSweeney, C. F. (2007). Daily rainfall variability at point and areal "
    "scales: evaluating simulations of present and future climate. PhD thesis, "
    "University of East Anglia, Norwich",
    locator="chapter 4, p. 93, eqs. 4-3 and 4-4: Thom's approximation of the maximum "
    "likelihood estimate of the shape",
    url="https://crudata.uea.ac.uk/cru/pubs/thesis/2007-mcsweeney/4.Gamma.pdf",
)
_THOM = Source(
    citation="Thom, H. C. S. (1958). A note on the gamma distribution. Monthly Weather "
    "Review 86(4), 117",
    locator="the approximation of the maximum likelihood estimate of the shape; not "
    "opened here: its equations as McSweeney (2007) and Naresh Kumar et al. (2009) "
    "print them",
    access="author-provided",
)
_WMO_1090 = Source(
    citation="WMO (2012). Standardized Precipitation Index User Guide. WMO-No. 1090, "
    "Geneva",
    locator="chapter 2 and section 6.1: the gamma distribution of the sums of each "
    "calendar month transformed to the standard normal (McKee et al. 1993)",
    url="https://library.wmo.int/idurl/4/39629",
)
_CLIMATE_INDICES = Source(
    citation="climate_indices 3.2.0 (J. Adams), Python package of climate indices",
    locator="indices.spi: Thom's estimates, zero_handling 'classic' (H(0) = q), the "
    "SPI held within the valid range of a fitted index, -3.09 to 3.09",
    url="https://pypi.org/project/climate-indices/3.2.0/",
)
_ADR_0032 = Source(
    citation="Hydrolog ADR-0032 (2026-11-13): meteorological statistics of a station, "
    "the group meteo",
    locator="point 5: a calendar month is fitted when 3 of its sums are positive",
    url="https://github.com/Daldek/Hydrolog/blob/develop/docs/decisions/"
    "0032-meteorological-statistics-of-a-station-the-group-meteo.md",
)
_ADR_0059 = (
    "Hydrolog ADR-0059 (2026-11-19): the meteorological indices declared by specs"
)
_ADR_0059_URL = (
    "https://github.com/Daldek/Hydrolog/blob/develop/docs/decisions/"
    "0059-the-meteorological-indices-by-specs.md"
)
_KACZOROWSKA = (
    "Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace "
    "Geograficzne IG PAN 33"
)
_KACZOROWSKA_URL = (
    "https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf"
)
_GASIOREK = (
    "Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych "
    "na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. "
    "Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994)"
)
_GASIOREK_URL = (
    "https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/"
    "Gasiorek%20Musial.pdf"
)
_WARSZAWA = (
    "Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the "
    "daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020"
)
_SUMS_RECORD = (
    "four times the world's greatest 12-month rainfall, 26,470 mm at Cherrapunji, "
    "1 August 1860 - 31 July 1861 (WMO Archive of Weather and Climate Extremes): a sum "
    "of the longest scale, 48 months"
)
_SUMS = Range(low=0.0, test_high=105_880.0, test_reason=_SUMS_RECORD)
_SUMS_TYPICAL = Range(
    low=0.0,
    high=872.3,
    source=Source(
        citation=_WARSZAWA,
        locator="the k-month sums of the default scales 1, 3, 6 and 12: 0.4 to 872.3 "
        "mm (a month without precipitation gives 0)",
    ),
)


# --- the gamma distribution of the sums (Thom) ---------------------------------------


class _Fit(NamedTuple):
    alpha: float
    beta_mm: float
    zero_probability: float


def _thom_a(sums: NDArray[np.float64]) -> float:
    """Return Thom's A = ln(mean) - mean(ln x) of the positive sums, cancellation-free.

    A is the mean of d - ln(1 + d) with d = x / mean - 1: every term is positive, the
    rounding of the mean enters only squared, and doubling the sums leaves it as it
    is; a sum below half the mean takes ln x - ln(mean) instead of ln(1 + d).
    """
    positive = sums[sums > 0.0]
    if positive.size == 0:
        return 0.0
    mean = float(np.sum(positive)) / positive.size
    ratio = (positive - mean) / mean
    near = ratio > -0.5
    with np.errstate(divide="ignore"):
        logs = np.where(
            near,
            np.log1p(np.where(near, ratio, 0.0)),
            np.log(positive) - math.log(mean),
        )
    return float(np.sum(ratio - logs)) / positive.size


def _gamma_parameters(x: Values) -> dict[str, float]:
    sums = x.array("sums_mm")
    positive = sums[sums > 0.0]
    mean = float(np.sum(positive)) / positive.size
    a = _thom_a(sums)
    alpha = (1.0 + math.sqrt(1.0 + GAMMA_FIT.constant("thom_ratio") * a)) / (
        GAMMA_FIT.constant("thom_denominator") * a
    )
    zeros = int(np.count_nonzero(sums == 0.0))
    return {
        "alpha": alpha,
        "beta_mm": mean / alpha,
        "zero_probability": zeros / sums.size,
    }


def _decimal_fit(sums: Sequence[float]) -> tuple[float, float, float]:
    """Thom's estimates from ln(mean) - mean(ln x) in 50-digit decimal arithmetic."""
    with localcontext() as context:
        context.prec = 50
        values = [Decimal(value) for value in sums]
        positive = [value for value in values if value > 0]
        mean = sum(positive, Decimal(0)) / len(positive)
        logs = sum((value.ln() for value in positive), Decimal(0))
        a = mean.ln() - logs / len(positive)
        alpha = (1 + (1 + 4 * a / 3).sqrt()) / (4 * a)
        zeros = Decimal(len(values) - len(positive)) / len(values)
        return float(alpha), float(mean / alpha), float(zeros)


def _fit_oracle(run: Callable[..., Values]) -> None:
    samples = (
        (0.0, 10.0, 20.0, 40.0, 30.0),
        (31.0, 29.8, 29.0, 35.1, 55.5, 63.9, 82.2, 60.6, 50.4, 40.2, 36.0, 36.1),
        (0.4, 0.0, 295.0, 12.7, 88.8, 151.3, 3.1, 47.0, 0.0, 9.9),
        (343.5, 872.3, 512.0, 604.4, 455.1, 701.9),
    )
    for sample in samples:
        out = run(sums_mm=list(sample))
        alpha, beta, zeros = _decimal_fit(sample)
        assert_within(
            [out.real("alpha"), out.real("beta_mm"), out.real("zero_probability")],
            [alpha, beta, zeros],
            rel=1e-13,
            reason="Thom's equations in 50-digit decimals from ln(mean) - mean(ln x); "
            "float64 rounds A, a difference of logarithms near 4 to 7, to about 1e-15",
        )


def _nearly_equal_sums(run: Callable[..., Values]) -> None:
    sample = (1000.0, 1000.000001, 999.999999, 1000.000002, 999.999998)
    out = run(sums_mm=list(sample))
    alpha, beta, _ = _decimal_fit(sample)
    assert_within(
        [out.real("alpha"), out.real("beta_mm")],
        [alpha, beta],
        rel=1e-6,
        reason="sums equal to 2e-9 of their mean: A is near 1e-18, which "
        "ln(mean) - mean(ln x) loses entirely in float64; d - ln(1 + d) keeps it to "
        "the rounding of ln(1 + d), 2e-16 of d against d squared over 2",
    )


GAMMA_FIT: Final = FormulaSpec(
    name="spi_gamma_fit",
    title="Gamma distribution of precipitation sums by Thom's approximation",
    function="hydrolog.statistics.meteo_spi.fit_gamma",
    family="statistic",
    equation=(
        "A = ln(mean x) - mean(ln x) over the positive sums x; alpha = (1 + sqrt(1 + "
        "4A/3)) / (4A); beta = mean x / alpha; q = m / n, m sums of zero among n"
    ),
    latex=(
        r"A = \ln\bar{x} - \overline{\ln x},\quad \hat{\alpha} = \frac{1 + \sqrt{1 + "
        r"4A/3}}{4A},\quad \hat{\beta} = \frac{\bar{x}}{\hat{\alpha}},\quad q = "
        r"\frac{m}{n}"
    ),
    variables=(
        Variable(
            name="sums_mm",
            symbol="x_i",
            unit="mm",
            kind="real_array",
            description="Precipitation sums of one calendar month and scale, one per "
            "year of the reference period.",
            physical=_SUMS,
            applicability="unstated",
            typical=_SUMS_TYPICAL,
        ),
    ),
    outputs=(
        Output(
            name="alpha",
            unit="-",
            symbol=r"\hat{\alpha}",
            description="Shape of the gamma distribution of the positive sums.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="beta_mm",
            unit="mm",
            symbol=r"\hat{\beta}",
            description="Its scale.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="zero_probability",
            unit="-",
            symbol="q",
            description="The share of the sums that are zero.",
            physical=Range(low=0.0, high=1.0, high_inclusive=False),
        ),
    ),
    sources=(
        _THOM,
        _MCSWEENEY,
        Source(
            citation=_KUMAR,
            locator="appendix, eqs. A4-A8 (Thom's estimates) and A9 (q = m / n)",
            url=_KUMAR_URL,
        ),
        _WMO_1090,
    ),
    constraints=(
        Constraint(
            name="three_positive_sums",
            cls="precondition",
            check=lambda x: np.count_nonzero(x.array("sums_mm") > 0.0) >= 3,
            text="at least three of the sums are positive",
            source=_ADR_0032,
            satisfied={"sums_mm": [0.0, 10.0, 20.0, 30.0]},
            violated={"sums_mm": [0.0, 10.0, 20.0, 0.0]},
        ),
        Constraint(
            name="positive_sums_differ",
            cls="precondition",
            check=lambda x: _thom_a(x.array("sums_mm")) > 0.0,
            text="the positive sums are not all equal (A > 0)",
            source=_MCSWEENEY,
            satisfied={"sums_mm": [0.0, 10.0, 10.0, 10.5]},
            violated={"sums_mm": [0.0, 10.0, 10.0, 10.0]},
        ),
    ),
    constants=(
        Constant(
            name="thom_ratio",
            value=Fraction(4, 3),
            unit="-",
            symbol="4/3",
            source=_MCSWEENEY,
        ),
        Constant(
            name="thom_denominator",
            value=4.0,
            unit="-",
            symbol="4",
            source=_MCSWEENEY,
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="sums_in_another_unit",
                inputs={"sums_mm": 1.0},
                outputs={"beta_mm": 1.0},
                tolerance=Tolerance(
                    rel=1e-9,
                    abs=1e-300,
                    reason="doubling the sums leaves d and A exact; only ln x - "
                    "ln(mean) of a sum below half the mean, up to 745 in magnitude, is "
                    "rounded anew in a term of at least 0.19; a subnormal scale keeps "
                    "fewer digits",
                ),
            ),
        ),
        limits=(
            Limit(
                name="decimal_oracle",
                text="alpha, beta and q equal Thom's equations evaluated from ln(mean) "
                "- mean(ln x) in 50-digit decimal arithmetic",
                check=_fit_oracle,
            ),
            Limit(
                name="nearly_equal_sums",
                text="sums equal to two parts in a billion keep their estimates (A as "
                "the mean of d - ln(1 + d))",
                check=_nearly_equal_sums,
            ),
            Limit(
                name="share_of_zeros",
                text="q is the share of zero sums",
                inputs={"sums_mm": [0.0, 0.0, 10.0, 20.0, 30.0]},
                expected={"zero_probability": 0.4},
                tolerance=Tolerance(abs=0.0, reason="2 / 5 is the float nearest 0.4"),
            ),
        ),
    ),
    validation=(
        "Thom's estimate approximates the maximum likelihood shape: its relative "
        "error is 1e-4 at A = 0.1 (alpha near 5), 2e-3 at A = 0.3 and 2.7 % at A = 1 "
        "(alpha 0.62), against ln(alpha) - digamma(alpha) = A solved exactly (the "
        "audit of 2026-11-18); the sources give no test of the fit against "
        "observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "the sums of one calendar month and scale over the years of the reference "
        "period; the caller leaves out the years without a sum",
        "q = m / n, the zero sums among all n sums (Edwards and McKee 1997, as Naresh "
        "Kumar et al. 2009 eq. A9 restate it); the shape and scale from the positive "
        "sums only",
        "Thom's approximation, not the exact maximum likelihood estimate, as "
        "climate_indices 3.2.0 and xclim 1.0.0 (method APP)",
        "A computed as the mean of d - ln(1 + d), d = x / mean x - 1, which equals ln("
        "mean x) - mean(ln x) without its cancellation (ln x - ln(mean x) for a sum "
        "below half the mean)",
    ),
    traps={
        "singular_at_bound": "preconditions three_positive_sums and "
        "positive_sums_differ: A = 0 for equal sums would divide by zero; a zero sum "
        "never reaches a logarithm",
        "moment_cancellation": "limit nearly_equal_sums: A, a difference of nearly "
        "equal logarithms, is the mean of d - ln(1 + d)",
        "many_small_terms": "the mean and A are pairwise sums of at most one term per "
        "year; limit decimal_oracle checks them to 1e-13",
        "gap_propagation": "type case sums_mm-nan_element: a gap is refused; the "
        "caller passes the known sums only",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="Thom's equations from ln(mean) - mean(ln x) in 50-digit "
            "decimal arithmetic (decimal)",
            test="tests/unit/test_formulas_meteo_spi.py (limit decimal_oracle)",
        ),
        Oracle(
            kind="frozen",
            description="climate_indices 3.2.0 indices.spi on the monthly sums of "
            "Warszawa-Okęcie 1991-2020, scales 1, 3, 6 and 12",
            test="tests/oracles/spi_climate_indices_warszawa.csv, compared by "
            "tests/unit/test_formulas_meteo_spi.py",
            conventions=(
                "both: Thom's estimates, q = m / n, H(0) = q, the SPI within -3.09 and "
                "3.09, calibration 1991-2020 = the analysed years",
            ),
        ),
    ),
)


def fit_gamma(sums_mm: NDArray[np.float64] | Sequence[float]) -> _Fit:
    """Fit the gamma distribution of the SPI to precipitation sums, spec spi_gamma_fit.

    Parameters
    ----------
    sums_mm : array_like of float
        Precipitation sums of one calendar month and scale [mm], one per year.

    Returns
    -------
    tuple of (alpha, beta_mm, zero_probability)
        The shape, the scale [mm] and the share of zero sums.

    Raises
    ------
    InvalidParameterError
        If the sums are refused by the spec: a negative or missing sum, fewer positive
        sums than its precondition asks or positive sums all equal
        (``precondition_failed``).
    """
    x = checked_inputs(GAMMA_FIT, sums_mm=sums_mm)
    out = checked_outputs(GAMMA_FIT, _gamma_parameters(x))
    return _Fit(out.real("alpha"), out.real("beta_mm"), out.real("zero_probability"))


# --- the SPI of a sum -----------------------------------------------------------------


def _spi(x: Values) -> NDArray[np.float64]:
    sums = x.array("sums_mm")
    known = ~np.isnan(sums)
    q = x.real("zero_probability")
    alpha = x.real("alpha")
    z = np.where(known & (sums > 0.0), sums, 0.0) / x.real("beta_mm")
    wet = z > 0.0
    # scipy's gammainc and gammaincc leave [0, 1] at a subnormal shape (0, or a
    # negative survival, where Q is a few subnormal units): held in it, Q decides
    # the tail, and the lower tail is taken only where H <= 0.5, which needs Q >= 0.5
    survival = np.clip(gammaincc(alpha, z), 0.0, 1.0)
    lower = np.where(wet, q + (1.0 - q) * np.clip(gammainc(alpha, z), 0.0, 1.0), q)
    upper = np.where(wet, (1.0 - q) * survival, 1.0 - q)
    below = (lower <= 0.5) & (~wet | (survival >= 0.5))
    limit = SPI.constant("spi_limit")
    with np.errstate(divide="ignore", invalid="ignore"):
        index = np.where(below, ndtri(lower), -ndtri(upper))
    out: NDArray[np.float64] = np.where(known, np.clip(index, -limit, limit), np.nan)
    return out


def _decimal_gamma(alpha: float, z: float) -> float:
    """P(alpha, z) by its power series in 40-digit decimals, the oracle of the SPI."""
    if z == 0.0:
        return 0.0
    with localcontext() as context:
        context.prec = 40
        a, x = Decimal(alpha), Decimal(z)
        term = 1 / a
        total = term
        k = 0
        while term > total * Decimal("1e-38"):
            k += 1
            term = term * x / (a + k)
            total += term
        front = (a * x.ln() - x - Decimal(math.lgamma(alpha))).exp()
        return float(total * front)


def _series_oracle(run: Callable[..., Values]) -> None:
    normal = NormalDist()
    limit = SPI.constant("spi_limit")
    sums = [0.0, 0.4, 10.0, 60.0, 250.0, 872.3]
    for alpha in (1.7, 6.5, 42.6):
        for beta in (5.8, 31.7):
            for q in (0.0, 0.05):
                out = run(sums_mm=sums, alpha=alpha, beta_mm=beta, zero_probability=q)
                expected = []
                for value in sums:
                    h = q + (1.0 - q) * _decimal_gamma(alpha, value / beta)
                    inside = min(max(h, 1e-300), 1.0 - 1e-16)
                    expected.append(min(max(normal.inv_cdf(inside), -limit), limit))
                assert_within(
                    out.array("spi"),
                    expected,
                    abs=1e-10,
                    reason="P(alpha, z) by its series in 40-digit decimals with "
                    "math.lgamma (relative 1e-14 at alpha 42.6) and the normal "
                    "quantile of the standard library (Wichura's AS241), against "
                    "scipy's gammainc and ndtri; 1 / phi(3.09) = 297 multiplies the "
                    "error of H",
                )


def _zero_sum(run: Callable[..., Values]) -> None:
    out = run(sums_mm=[0.0], zero_probability=0.3)
    assert_within(
        out.array("spi"),
        [NormalDist().inv_cdf(0.3)],
        abs=1e-15,
        reason="H(0) = q: scipy's ndtri against the standard library's quantile",
    )


def _clipped(run: Callable[..., Values]) -> None:
    limit = SPI.constant("spi_limit")
    dry = run(sums_mm=[0.0], zero_probability=0.0)
    wet = run(sums_mm=[1.0e5], alpha=2.0, beta_mm=10.0, zero_probability=0.0)
    assert_within(
        [dry.array("spi")[0], wet.array("spi")[0]],
        [-limit, limit],
        abs=0.0,
        reason="H = 0 and H = 1 are held at the limits exactly",
    )


SPI: Final = FormulaSpec(
    name="spi",
    title="Standardized precipitation index of precipitation sums",
    function="hydrolog.statistics.meteo_spi.spi_values",
    family="index",
    equation=(
        "H(x) = q + (1 - q) G(x; alpha, beta) for x > 0, H(0) = q, G the gamma "
        "distribution function; SPI = Phi^-1(H(x)) held within -3.09 and 3.09"
    ),
    latex=(
        r"H(x) = q + (1 - q)\,P\!\left(\alpha, \frac{x}{\beta}\right),\quad H(0) = q,"
        r"\quad \mathrm{SPI} = \max\!\left(-3.09, \min\!\left(3.09, "
        r"\Phi^{-1}(H(x))\right)\right)"
    ),
    variables=(
        Variable(
            name="sums_mm",
            symbol="x",
            unit="mm",
            kind="real_array",
            description="Precipitation sums of the calendar month and scale of the "
            "distribution; NaN stays NaN.",
            physical=_SUMS,
            applicability="unstated",
            typical=_SUMS_TYPICAL,
            gaps_allowed=True,
        ),
        Variable(
            name="alpha",
            symbol=r"\alpha",
            unit="-",
            description="Shape of the gamma distribution (spi_gamma_fit).",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1.0e4,
                test_reason="a shape of 1e4 is a coefficient of variation of 1 % of "
                "the sums, beyond the 213.6 of 48-month sums at Warszawa-Okęcie",
            ),
            applicability="unstated",
            typical=Range(
                low=1.7,
                high=42.6,
                source=Source(
                    citation=_WARSZAWA,
                    locator="the fits of the default scales 1, 3, 6 and 12: shapes "
                    "1.72 to 42.60",
                ),
            ),
        ),
        Variable(
            name="beta_mm",
            symbol=r"\beta",
            unit="mm",
            description="Scale of the gamma distribution (spi_gamma_fit).",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=105_880.0,
                test_reason=_SUMS_RECORD,
            ),
            applicability="unstated",
            typical=Range(
                low=5.8,
                high=31.7,
                source=Source(
                    citation=_WARSZAWA,
                    locator="the fits of the default scales 1, 3, 6 and 12: scales "
                    "5.81 to 31.71 mm",
                ),
            ),
        ),
        Variable(
            name="zero_probability",
            symbol="q",
            unit="-",
            description="Probability of a zero sum (spi_gamma_fit).",
            physical=Range(low=0.0, high=1.0, high_inclusive=False),
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=0.0,
                source=Source(
                    citation=_WARSZAWA,
                    locator="no month without precipitation in 1991-2020: q = 0 in "
                    "every fit of the default scales",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="spi",
            unit="-",
            kind="real_array",
            symbol=r"\mathrm{SPI}",
            description="The SPI of each sum.",
            physical=Range(low=-3.09, high=3.09),
            gaps_allowed=True,
            gaps_from="sums_mm",
        ),
    ),
    sources=(
        _WMO_1090,
        Source(
            citation=_KUMAR,
            locator="appendix, eq. A9 (H(x) = q + (1 - q) G(x), after Edwards and "
            "McKee 1997) and eqs. A10-A12 (the normal quantile)",
            url=_KUMAR_URL,
        ),
        _CLIMATE_INDICES,
    ),
    constants=(
        Constant(
            name="spi_limit",
            value=3.09,
            unit="-",
            symbol="3.09",
            source=_CLIMATE_INDICES,
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"sums_mm": 1, "alpha": -1, "beta_mm": -1, "zero_probability": 1},
        scalings=(
            Scaling(
                name="sums_and_scale_in_another_unit",
                inputs={"sums_mm": 1.0, "beta_mm": 1.0},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="x / beta is the same number when both are doubled",
                ),
            ),
        ),
        limits=(
            Limit(
                name="zero_sum",
                text="a zero sum has H = q (the classic zero handling)",
                check=_zero_sum,
            ),
            Limit(
                name="held_within_limits",
                text="H = 0 and H = 1 give -3.09 and 3.09",
                check=_clipped,
            ),
            Limit(
                name="series_oracle",
                text="the SPI equals the normal quantile of H from the power series of "
                "the incomplete gamma function in decimal arithmetic",
                check=_series_oracle,
            ),
        ),
    ),
    validation="none: the SPI is a transformation of the fitted distribution",
    formula_version=1,
    status="referenced",
    conventions=(
        "classic zero handling, H(0) = q (Edwards and McKee 1997; climate_indices "
        "zero_handling 'classic'); the centre of the zero mass, Phi^-1(q / 2), is not "
        "used",
        "held within -3.09 and 3.09, the quantiles of 0.001 and 0.999, as "
        "climate_indices; WMO-No. 1090 and xclim set no limit",
        "the upper tail from 1 - H = (1 - q) Q(alpha, x / beta), Q the regularized "
        "upper incomplete gamma function, where H > 0.5",
        "the SPI is not classed (WMO-No. 1090 table 1 gives classes from -2 to 2)",
    ),
    traps={
        "singular_at_bound": "limit held_within_limits: Phi^-1(0) and Phi^-1(1) are "
        "infinite and held at the limits; at a subnormal shape scipy's gammainc gives "
        "0 and its gammaincc may go negative: both are held in [0, 1] and the tail is "
        "chosen by gammaincc (the pinned examples of test_spi_properties)",
        "gap_propagation": "type case sums_mm-nan_element: a missing sum gives a "
        "missing SPI and no other",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="P(alpha, x / beta) by its power series in 40-digit decimals "
            "(decimal) and the normal quantile of statistics.NormalDist (AS241)",
            test="tests/unit/test_formulas_meteo_spi.py (limit series_oracle)",
        ),
        Oracle(
            kind="frozen",
            description="climate_indices 3.2.0 indices.spi on the monthly sums of "
            "Warszawa-Okęcie 1991-2020, scales 1, 3, 6 and 12",
            test="tests/oracles/spi_climate_indices_warszawa.csv, compared by "
            "tests/unit/test_formulas_meteo_spi.py",
            conventions=(
                "both: Thom's estimates, q = m / n, H(0) = q, the SPI within -3.09 and "
                "3.09, calibration 1991-2020 = the analysed years",
            ),
        ),
    ),
)
SPI_LIMIT: Final = SPI.constant("spi_limit")
"""The SPI is held within plus and minus this (the spec ``spi``)."""


def spi_values(
    sums_mm: NDArray[np.float64] | Sequence[float],
    alpha: float,
    beta_mm: float,
    zero_probability: float,
) -> NDArray[np.float64]:
    """Return the SPI of precipitation sums under a fitted distribution, spec spi.

    Parameters
    ----------
    sums_mm : array_like of float
        Precipitation sums [mm]; ``NaN`` stays ``NaN``.
    alpha, beta_mm, zero_probability : float
        The fitted distribution: its shape, its scale [mm] and the probability of a
        zero sum.

    Returns
    -------
    numpy.ndarray
        The SPI of each sum.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec (a negative sum among them).
    """
    x = checked_inputs(
        SPI,
        sums_mm=sums_mm,
        alpha=alpha,
        beta_mm=beta_mm,
        zero_probability=zero_probability,
    )
    return checked_outputs(SPI, {"spi": _spi(x)}, inputs=x).array("spi")


# --- classes of relative precipitation ------------------------------------------------


def _percent(
    least_typical: float, most_typical: float, locator: str, test_high: float
) -> Variable:
    return Variable(
        name="percent_of_normal",
        symbol="P/N",
        unit="%",
        description="Precipitation in % of its normal.",
        physical=Range(
            low=0.0,
            test_high=test_high,
            test_reason="ten times the largest percentage of the project's data "
            f"({most_typical} % at Warszawa-Okęcie)",
        ),
        applicability="unstated",
        typical=Range(
            low=least_typical,
            high=most_typical,
            source=Source(citation=_WARSZAWA, locator=locator),
        ),
    )


def _ordered(
    names: Sequence[str], top: float
) -> Callable[[Callable[..., Values]], None]:
    def check(run: Callable[..., Values]) -> None:
        ranks = [
            names.index(run(percent_of_normal=step / 2).choice("precipitation_class"))
            for step in range(round(top * 2) + 1)
        ]
        assert ranks == sorted(ranks), "a larger percentage gave a drier class"

    return check


_YEAR_FROM = ("very_dry", "dry", "normal", "wet", "very_wet", "extremely_wet")


def _year_class(x: Values) -> str:
    percent = x.real("percent_of_normal")
    half = YEAR_CLASS.constant("rounding_half")
    found = KACZOROWSKA_CLASSES[0]
    for name in _YEAR_FROM:
        if percent >= YEAR_CLASS.constant(f"{name}_from") - half:
            found = name
    return found


def _kaczorowska_constant(name: str, value: float) -> Constant:
    return Constant(
        name=f"{name}_from",
        value=value,
        unit="%",
        symbol=f"{value:g}",
        source=Source(
            citation=_KACZOROWSKA,
            locator=f"p. 72: the least whole percent of the class {name}",
            url=_KACZOROWSKA_URL,
        ),
    )


YEAR_CLASS: Final = FormulaSpec(
    name="kaczorowska_class",
    title="Kaczorowska's class of a year's precipitation in % of its normal",
    function="hydrolog.statistics.meteo_spi.year_precipitation_class",
    family="classification",
    equation=(
        "P/N rounded to a whole percent, a half up: below 50 extremely dry, 50-74 very "
        "dry, 75-89 dry, 90-110 normal, 111-125 wet, 126-150 very wet, above 150 "
        "extremely wet"
    ),
    latex=(
        r"r = \left\lfloor \frac{100\,P}{N} + \frac{1}{2} \right\rfloor:\ r < 50,\ "
        r"50 \le r \le 74,\ 75 \le r \le 89,\ 90 \le r \le 110,\ 111 \le r \le 125,\ "
        r"126 \le r \le 150,\ r > 150"
    ),
    variables=(
        _percent(
            71.0,
            145.2,
            "the annual sums of 1991-2020 in % of their normal: 71.0 to 145.2 %",
            1452.0,
        ),
    ),
    outputs=(
        Output(
            name="precipitation_class",
            unit="-",
            kind="choice",
            description="The class, driest first.",
            choices=KACZOROWSKA_CLASSES,
        ),
    ),
    sources=(
        Source(
            citation=_KACZOROWSKA,
            locator="p. 72: the classes of a year (or a season) in % of the normal",
            url=_KACZOROWSKA_URL,
        ),
        Source(
            citation="IMGW-PIB (2023). Rocznik Meteorologiczny 2022",
            locator="Tab. 5, p. 14 (the same classes, „normalny” for „przeciętny”) "
            "and Tab. 9, p. 22 (annual sums in % of the normal 1991-2020, whole "
            "percents)",
            url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/"
            "Roczniki/Rocznik%20meteorologiczny/Rocznik%20Meteorologiczny%202022.pdf",
        ),
    ),
    constants=(
        *(
            _kaczorowska_constant(name, value)
            for name, value in zip(
                _YEAR_FROM, (50.0, 75.0, 90.0, 111.0, 126.0, 151.0), strict=True
            )
        ),
        Constant(
            name="rounding_half",
            value=0.5,
            unit="%",
            symbol="1/2",
            source=Source(
                citation=_ADR_0059,
                locator="the classes are ranges of whole percents: a percentage "
                "counts in the class of its rounding, a half up",
                url=_ADR_0059_URL,
            ),
        ),
    ),
    properties=Properties(
        units="unit_specific",
        limits=(
            Limit(
                name="ordered_classes",
                text="a larger percentage never gives a drier class",
                check=_ordered(KACZOROWSKA_CLASSES, 200.0),
            ),
        ),
    ),
    validation="none: a classification",
    formula_version=1,
    status="referenced",
    conventions=(
        "a percentage counts in the class of its whole-number rounding, a half rounded "
        "up: 74.5 % is dry, 110.5 % wet, 150.5 % extremely wet (Python's rounding of a "
        "half to even, used up to 0.8.1, made them very dry, normal and very wet)",
        "Łabędzki and Bąk (2004, Acta Agrophysica 3(1), Tab. 2) read the classes with "
        "decimal bounds (75.0-89.9 dry): 89.6 % is normal here and dry there",
        "the normal of the reference period, by default the analysed years",
    ),
    traps={
        "class_limit": "reference cases kaczorowska-boundary-*: each limit, a half "
        "below it and above it",
        "gap_propagation": "type case percent_of_normal-nan: NaN is refused; a year "
        "without a percentage has no class",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
)


def year_precipitation_class(percent_of_normal: float) -> str:
    """Return Kaczorowska's class of a year's precipitation, spec kaczorowska_class.

    Parameters
    ----------
    percent_of_normal : float
        The year's precipitation in % of its normal.

    Returns
    -------
    str
        The class (:data:`KACZOROWSKA_CLASSES`).

    Raises
    ------
    InvalidParameterError
        If the percentage is refused by the spec.
    """
    x = checked_inputs(YEAR_CLASS, percent_of_normal=percent_of_normal)
    out = checked_outputs(YEAR_CLASS, {"precipitation_class": _year_class(x)})
    return out.choice("precipitation_class")


def _month_class(x: Values) -> str:
    percent = x.real("percent_of_normal")
    names = KACZOROWSKA_CLASSES
    for name in names[:3]:
        if percent < MONTH_CLASS.constant(f"{name}_below"):
            return name
    for name in names[3:6]:
        if percent <= MONTH_CLASS.constant(f"{name}_to"):
            return name
    return names[6]


def _month_constant(name: str, value: float, side: str) -> Constant:
    return Constant(
        name=f"{name}_{side}",
        value=value,
        unit="%",
        symbol=f"{value:g}",
        source=Source(
            citation=_GASIOREK,
            locator=f"Table 1, p. 109: the {'upper' if side == 'to' else 'open upper'} "
            f"limit of the class {name}",
            url=_GASIOREK_URL,
        ),
    )


MONTH_CLASS: Final = FormulaSpec(
    name="month_precipitation_class",
    title="Class of a month's precipitation in % of its normal",
    function="hydrolog.statistics.meteo_spi.month_precipitation_class",
    family="classification",
    equation=(
        "P/N below 25 extremely dry, [25, 50) very dry, [50, 75) dry, [75, 125] "
        "normal, (125, 150] wet, (150, 200] very wet, above 200 extremely wet"
    ),
    latex=(
        r"\frac{100\,P}{N} < 25,\ [25, 50),\ [50, 75),\ [75, 125],\ (125, 150],\ "
        r"(150, 200],\ > 200"
    ),
    variables=(
        _percent(
            1.1,
            358.9,
            "the monthly sums of 1991-2020 in % of their normals: 1.1 to 358.9 %",
            3589.0,
        ),
    ),
    outputs=(
        Output(
            name="precipitation_class",
            unit="-",
            kind="choice",
            description="The class, driest first.",
            choices=KACZOROWSKA_CLASSES,
        ),
    ),
    sources=(
        Source(
            citation=_GASIOREK,
            locator="Table 1, p. 109: the classes of the relative precipitation index "
            "of a month (source line: Tomaszewska 1994); eq. 1, p. 109 (RPI = 100 P / "
            "N)",
            url=_GASIOREK_URL,
        ),
    ),
    constants=(
        *(
            _month_constant(name, value, "below")
            for name, value in zip(
                KACZOROWSKA_CLASSES[:3], (25.0, 50.0, 75.0), strict=True
            )
        ),
        *(
            _month_constant(name, value, "to")
            for name, value in zip(
                KACZOROWSKA_CLASSES[3:6], (125.0, 150.0, 200.0), strict=True
            )
        ),
    ),
    properties=Properties(
        units="unit_specific",
        limits=(
            Limit(
                name="ordered_classes",
                text="a larger percentage never gives a drier class",
                check=_ordered(KACZOROWSKA_CLASSES, 400.0),
            ),
        ),
    ),
    validation="none: a classification",
    formula_version=1,
    status="referenced",
    conventions=(
        "the interval closures of Table 1 as printed: the lower three classes closed "
        "below, the upper ones closed above",
        "Kaczorowska (1962) classes years and seasons only; IMGW-PIB's monitoring "
        "labels this monthly table after her, which the source line of Gąsiorek and "
        "Musiał (2011) does not",
    ),
    traps={
        "class_limit": "reference cases month-class-boundary-*: each limit and just "
        "beyond it",
        "gap_propagation": "type case percent_of_normal-nan: NaN is refused; a month "
        "without a percentage has no class",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
)


def month_precipitation_class(percent_of_normal: float) -> str:
    """Return the class of a month's precipitation, spec month_precipitation_class.

    Parameters
    ----------
    percent_of_normal : float
        The month's precipitation in % of its normal.

    Returns
    -------
    str
        The class (:data:`KACZOROWSKA_CLASSES`).

    Raises
    ------
    InvalidParameterError
        If the percentage is refused by the spec.
    """
    x = checked_inputs(MONTH_CLASS, percent_of_normal=percent_of_normal)
    out = checked_outputs(MONTH_CLASS, {"precipitation_class": _month_class(x)})
    return out.choice("precipitation_class")


SPECS: Final = (GAMMA_FIT, SPI, YEAR_CLASS, MONTH_CLASS)
"""The Tier A formulas of the module."""

_WMO_1203_NORMALS = Source(
    citation="WMO (2017). WMO Guidelines on the Calculation of Climate Normals. "
    "WMO-No. 1203, Geneva",
    locator="section 4.4.2, pp. 8-9: values in at least 80 % of the years of the "
    "period; section 4.3.3, p. 6: the normal of several months from the monthly "
    "normals",
    url="https://library.wmo.int/idurl/4/55797",
)

TIER_B: Final = (
    TierBSpec(
        name="spi_k_month_sums",
        function="hydrolog.statistics.meteo_spi.standardized_precipitation_index",
        definition="the k-month sum of a month is the sum of the monthly sums of the "
        "k months that end in it, missing unless all k are known; the sums of each "
        "calendar month over the reference period are fitted (spi_gamma_fit) when "
        "they are known in at least 80 % of its years, those without data counted",
        convention="the k-month sums of the reference period stay within its years "
        "(climate_indices 3.2.0 lets those of its first k - 1 months reach before "
        "it); every analysed month gets the SPI of its own sum under the fit of its "
        "calendar month; a month whose sums the fit refuses has no SPI (notice "
        "spi_not_fitted)",
        source=_WMO_1090,
        constants=(
            Constant(
                name="normal_share",
                value=Fraction(4, 5),
                unit="-",
                symbol="80 %",
                source=_WMO_1203_NORMALS,
            ),
        ),
    ),
    TierBSpec(
        name="relative_precipitation",
        function="hydrolog.statistics.meteo_spi.standardized_precipitation_index",
        definition="100 P / N: a month's sum in % of the normal of its calendar "
        "month, a year's in % of the sum of the twelve monthly normals (classed by "
        "month_precipitation_class and kaczorowska_class)",
        convention="the normals of the reference period; no percentage without a "
        "normal or with a normal of 0",
        source=Source(
            citation=_GASIOREK,
            locator="eq. 1, p. 109: RPI = P / P-bar 100 %",
            url=_GASIOREK_URL,
        ),
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""


@dataclass
class SpiScale(JsonResultMixin):
    """The fits of one scale.

    Attributes
    ----------
    scale_months : int
        k, the months summed.
    fits : list of GammaFit
        One per calendar month, January first.
    """

    scale_months: int
    fits: list[GammaFit]


@dataclass
class SpiMonth(JsonResultMixin):
    """One month of the analysed years.

    Attributes
    ----------
    year : int
        The year of ``year_type`` the month belongs to, as in ``years`` (November and
        December belong to the hydrological year that ends in the next calendar year).
    month : int
        Calendar month (1-12).
    total_mm : float or None
        Its precipitation [mm] (WMO-No. 1203, 4.4.1 c).
    percent_of_normal : float or None
        In % of the normal of the calendar month (of the reference period).
    precipitation_class : str or None
        Its class (:data:`KACZOROWSKA_CLASSES`, the limits of months).
    spi : list of float or None
        The SPI of each of ``scales_months``, under the fits of the reference period.
    """

    year: int
    month: int
    total_mm: float | None
    percent_of_normal: float | None
    precipitation_class: str | None
    spi: list[float | None]


@dataclass
class SpiYear(JsonResultMixin):
    """One analysed year.

    Attributes
    ----------
    year : int
        The year.
    total_mm : float or None
        Its precipitation [mm]; ``None`` without its twelve monthly sums.
    percent_of_normal : float or None
        In % of the annual normal (of the reference period).
    precipitation_class : str or None
        Kaczorowska's (1962) class (:data:`KACZOROWSKA_CLASSES`).
    """

    year: int
    total_mm: float | None
    percent_of_normal: float | None
    precipitation_class: str | None


@dataclass
class SpiPeriod(JsonResultMixin):
    """The normals and the fits of the reference period.

    Attributes
    ----------
    normal_mm : float or None
        Annual normal [mm]: the sum of the twelve monthly normals, ``None`` when one
        is missing (WMO-No. 1203, 4.3.3).
    normal_years : int
        The fewest years of the reference period with a sum among the twelve months;
        every monthly normal needs 80 % of its years (WMO-No. 1203, 4.4.2).
    months_normal_mm : list of float or None
        Normals of the calendar months, January first [mm].
    scales : list of SpiScale
        The fits of each scale.
    """

    normal_mm: float | None
    normal_years: int
    months_normal_mm: list[float | None]
    scales: list[SpiScale]


@dataclass
class StandardizedPrecipitation(JsonResultMixin):
    """SPI of several scales and the relative precipitation of months and years (M8).

    Attributes
    ----------
    scales_months : list of int
        The scales [months] of ``months[].spi``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``: the years of ``years``.
    first_year, last_year, period_years : int
        The analysed years: first and last year with a value, years with a value.
    reference_first_year, reference_last_year : int
        The reference period of the fits and the normals, as given or by default the
        analysed years.
    reference_period_years : int
        Its years with a value.
    months : list of SpiMonth
        Every month from the first to the last with a value.
    years : list of SpiYear
        Every analysed year with a value.
    period : SpiPeriod
        The normals and the fits.
    """

    scales_months: list[int]
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    reference_first_year: int
    reference_last_year: int
    reference_period_years: int
    months: list[SpiMonth]
    years: list[SpiYear]
    period: SpiPeriod


def _scales(scales_months: Sequence[int]) -> list[int]:
    chosen: list[int] = []
    for item in scales_months:
        if isinstance(item, bool) or int(item) != item or not 1 <= item <= 48:
            raise InvalidParameterError(
                f"scales_months must be whole numbers from 1 to 48, got {item!r}"
            )
        if int(item) not in chosen:
            chosen.append(int(item))
    if not chosen:
        raise InvalidParameterError("scales_months must not be empty")
    return chosen


def _fitted(sample: NDArray[np.float64]) -> _Fit | None:
    """Return the fit of a calendar month's sums, ``None`` if a precondition fails."""
    try:
        return fit_gamma(sample)
    except InvalidParameterError as refused:
        if refused.details.get("reason") == "precondition_failed":
            return None
        raise


def standardized_precipitation_index(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    scales_months: Sequence[int] = DEFAULT_SCALES_MONTHS,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
    first_year: int | None = None,
    last_year: int | None = None,
    reference_first_year: int | None = None,
    reference_last_year: int | None = None,
) -> StandardizedPrecipitation:
    """SPI of each scale and the relative precipitation of each month and year (M8).

    The k-month sums of each calendar month of the reference period are fitted; the
    SPI of an analysed month is that of its own k-month sum under the fit, and its
    precipitation is in % of the normals of the reference period. A fit needs the
    sums in at least 80 % of the years of the reference period, those without data
    too; the k-month sums of each period stay within its own years.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    scales_months : sequence of int, optional
        Scales [months], each from 1 to 48, by default 1, 3, 6 and 12.
    accumulated : array_like of bool, optional
        Accumulated totals of the missing days before them (they stand for them in
        the monthly sums, WMO-No. 1203, 4.4.1 c).
    year_type : {"calendar", "hydrological"}, optional
        The kind of year of ``years`` and of the periods.
    first_year, last_year : int, optional
        The analysed years (of ``year_type``), by default those of the record.
    reference_first_year, reference_last_year : int, optional
        The reference period of the fits and the normals, each by default that of
        the analysed years as resolved; WMO-No. 1090 asks for at least 30 years.

    Returns
    -------
    StandardizedPrecipitation
        The SPI and the relative precipitation of the months, the years and the
        fits.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid, a value is negative, no day has a value,
        ``year_type`` is unknown, a scale is not a whole number from 1 to 48 or a
        period starts after its last year (``details.reason`` ``range``).
    CalculationError
        If a period has no value (``details.reason`` ``no_values_in_period``).
    """
    scales = _scales(scales_months)
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
    flat = table.reshape(-1)
    calendar = np.array(grid.months * grid.n_years, dtype=np.int64)
    base = periods.reference
    same = base is data
    base_table = table if same else base.monthly()
    base_calendar = (
        calendar
        if same
        else np.array(base.grid.months * base.grid.n_years, dtype=np.int64)
    )
    month_with_value = (
        grid.per_month(np.isfinite(data.raw).astype(np.float64)).reshape(-1) > 0
    )
    have = np.flatnonzero(month_with_value)
    first, last = int(have[0]), int(have[-1])
    span = periods.period.n_years
    month_normals, normal_years = monthly_normals(base_table, span)
    normals = dict(zip(grid.months, month_normals, strict=True))
    annual = round_sums(table.sum(axis=1))
    normal_mm = multimonth_normal(month_normals)
    spi_table = np.full((len(scales), flat.size), np.nan)
    scale_fits: list[SpiScale] = []
    for number, scale in enumerate(scales):
        sums = rolling_sum(flat, scale)
        base_sums = sums if same else rolling_sum(base_table.reshape(-1), scale)
        fits: list[GammaFit] = []
        for month in range(1, 13):
            sample = base_sums[base_calendar == month]
            sample = sample[np.isfinite(sample)]
            fitted = _fitted(sample) if sample.size >= WMO_NORMAL_SHARE * span else None
            if fitted is None:
                fits.append(GammaFit(month, None, None, None, int(sample.size)))
                continue
            fits.append(
                GammaFit(
                    month,
                    fitted.alpha,
                    fitted.beta_mm,
                    fitted.zero_probability,
                    int(sample.size),
                )
            )
            where = calendar == month
            spi_table[number, where] = spi_values(sums[where], *fitted)
        scale_fits.append(SpiScale(scale, fits))
    months: list[SpiMonth] = []
    for cell in range(first, last + 1):
        row, slot = divmod(cell, 12)
        month = int(grid.months[slot])
        total = finite(flat[cell])
        reference = normals[month]
        percent = 100.0 * total / reference if total is not None and reference else None
        months.append(
            SpiMonth(
                year=grid.first_year + row,
                month=month,
                total_mm=total,
                percent_of_normal=percent,
                precipitation_class=None
                if percent is None
                else month_precipitation_class(percent),
                spi=[finite(spi_table[number, cell]) for number in range(len(scales))],
            )
        )
    years: list[SpiYear] = []
    for row in np.flatnonzero(data.present).tolist():
        total = finite(annual[row])
        percent = 100.0 * total / normal_mm if total is not None and normal_mm else None
        years.append(
            SpiYear(
                grid.first_year + row,
                total,
                percent,
                None if percent is None else year_precipitation_class(percent),
            )
        )
    return StandardizedPrecipitation(
        scales_months=scales,
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        reference_first_year=periods.period.first_year,
        reference_last_year=periods.period.last_year,
        reference_period_years=periods.reference_period_years,
        months=months,
        years=years,
        period=SpiPeriod(
            normal_mm=normal_mm,
            normal_years=normal_years,
            months_normal_mm=[normals[month] for month in range(1, 13)],
            scales=scale_fits,
        ),
    )
