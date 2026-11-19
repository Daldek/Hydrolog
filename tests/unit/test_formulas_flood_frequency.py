"""The formulas of the frequency analyses against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/flood-frequency-cases.json`` (CMP-6.1);
the limits hold the exact rational oracles (CMP-6.2); NumPy and SciPy are compared in
the tests (CMP-6.3), R's lmom and lmomco through the frozen oracle
``tests/oracles/frequency_lmom_r.csv`` (CMP-6.4). The functions are given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

import csv
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from hypothesis import example, given
from scipy.optimize import minimize
from scipy.stats import (
    anderson,
    genextreme,
    gumbel_r,
    kstest,
    lognorm,
    pearson3,
    skew,
    uniform,
    weibull_min,
)
from scipy.stats.mstats import plotting_positions

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    ReferenceCase,
    assert_case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    assert_within,
    load_cases,
    range_cases,
    read_frozen_oracle,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.statistics import frequency
from hydrolog.statistics._types import (
    NON_EXCEEDANCE_POSITIONS,
    PLOTTING_POSITIONS,
    compute_non_exceedance_positions,
    compute_plotting_positions,
)
from hydrolog.statistics.frequency import (
    AKAIKE,
    ANDERSON_DARLING,
    FIT_L_MOMENTS,
    FIT_LEAST_SQUARES,
    FIT_MAXIMUM_LIKELIHOOD,
    FIT_MOMENTS,
    GEV_QUANTILES,
    L_MOMENTS,
    LOG_NORMAL_QUANTILES,
    MOMENTS,
    PEARSON3_QUANTILES,
    WEIBULL_QUANTILES,
    akaike_information_criterion,
    anderson_darling,
    fit_l_moments,
    fit_least_squares,
    fit_maximum_likelihood,
    fit_moments,
    gev_quantiles,
    log_normal_quantiles,
    pearson3_quantiles,
    sample_l_moments,
    sample_moments,
    weibull_quantiles,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

TESTS = Path(__file__).parents[1]
CASES = TESTS / "fixtures" / "formulas" / "flood-frequency-cases.json"
LMOM = read_frozen_oracle(TESTS / "oracles" / "frequency_lmom_r.csv")
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (MOMENTS, sample_moments),
    (L_MOMENTS, sample_l_moments),
    (GEV_QUANTILES, gev_quantiles),
    (LOG_NORMAL_QUANTILES, log_normal_quantiles),
    (PEARSON3_QUANTILES, pearson3_quantiles),
    (WEIBULL_QUANTILES, weibull_quantiles),
    (FIT_L_MOMENTS, fit_l_moments),
    (FIT_MOMENTS, fit_moments),
    (FIT_MAXIMUM_LIKELIHOOD, fit_maximum_likelihood),
    (FIT_LEAST_SQUARES, fit_least_squares),
    (ANDERSON_DARLING, anderson_darling),
    (AKAIKE, akaike_information_criterion),
    (PLOTTING_POSITIONS, compute_plotting_positions),
    (NON_EXCEEDANCE_POSITIONS, compute_non_exceedance_positions),
)
DISTRIBUTIONS = ("log_normal", "gev", "pearson3", "weibull")
POLANA = list(frequency._POLANA)
RETURN_PERIODS = [2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0]
"""The return periods of the frozen oracles' quantiles."""


def _samples() -> dict[str, list[float]]:
    """The samples of the frozen R oracles, by dataset."""
    found: dict[str, list[float]] = {}
    path = TESTS / "oracles" / "frequency_ml_samples.csv"
    with path.open(encoding="utf-8") as stream:
        for row in csv.DictReader(line for line in stream if not line.startswith("#")):
            found.setdefault(row["dataset"], []).append(float(row["value"]))
    return found


SAMPLES = _samples()


def _lmom(dataset: str, function: str) -> dict[str, float]:
    """The outputs of an R function on a dataset in the frozen oracle."""
    return {
        row["output"]: float(row["value"])
        for row in LMOM.rows
        if row["dataset"] == dataset and row["function"] == function
    }


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


def _published() -> list[object]:
    return [
        pytest.param(spec, function, case, id=f"{spec.name}-{case.case_id}")
        for spec, function in FAMILY
        for case in load_cases(CASES, spec.name)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function", "case"), _published())
def test_reference_cases(spec: FormulaSpec, function, case: ReferenceCase):
    assert_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=lambda x: str(x))
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


@given(inputs=strategies(MOMENTS))
def test_moments_properties(inputs):
    assert_property_contract(MOMENTS, as_standard(sample_moments), inputs, ERRORS)
    assert_properties(MOMENTS, as_standard(sample_moments), inputs, ERRORS)


@given(inputs=strategies(L_MOMENTS))
@example(inputs={"values": np.array([0.8125, *[0.0] * 23])}).via(
    "discovered failure: t3 of values all equal but the largest rounded 5 ulp above 1"
)
@example(inputs={"values": np.array([-999600.0, 0.81, 999595.0, *[1.0] * 18])}).via(
    "discovered failure: the mean of the sorted deviations was not the negated mean of "
    "the negated sample"
)
def test_l_moments_properties(inputs):
    assert_property_contract(L_MOMENTS, as_standard(sample_l_moments), inputs, ERRORS)
    assert_properties(L_MOMENTS, as_standard(sample_l_moments), inputs, ERRORS)


@given(inputs=strategies(GEV_QUANTILES))
def test_gev_quantiles_properties(inputs):
    function = as_standard(gev_quantiles)
    assert_property_contract(GEV_QUANTILES, function, inputs, ERRORS)
    assert_properties(GEV_QUANTILES, function, inputs, ERRORS)


@given(inputs=strategies(LOG_NORMAL_QUANTILES))
def test_log_normal_quantiles_properties(inputs):
    function = as_standard(log_normal_quantiles)
    assert_property_contract(LOG_NORMAL_QUANTILES, function, inputs, ERRORS)
    assert_properties(LOG_NORMAL_QUANTILES, function, inputs, ERRORS)


@given(inputs=strategies(PEARSON3_QUANTILES))
def test_pearson3_quantiles_properties(inputs):
    function = as_standard(pearson3_quantiles)
    assert_property_contract(PEARSON3_QUANTILES, function, inputs, ERRORS)
    assert_properties(PEARSON3_QUANTILES, function, inputs, ERRORS)


@given(inputs=strategies(WEIBULL_QUANTILES))
def test_weibull_quantiles_properties(inputs):
    function = as_standard(weibull_quantiles)
    assert_property_contract(WEIBULL_QUANTILES, function, inputs, ERRORS)
    assert_properties(WEIBULL_QUANTILES, function, inputs, ERRORS)


def _lmom_quantiles(dataset: str) -> dict[str, tuple[object, ...]]:
    """lmom's parameters of a dataset, as the arguments of the quantile functions."""
    gev = _lmom(dataset, "lmom::pelgev")
    pe3 = _lmom(dataset, "lmom::pelpe3")
    ln3 = _lmom(dataset, "lmom::pelln3(bound=0)")
    wei = _lmom(dataset, "lmom::pelwei")
    return {
        "lmom::quagev": (gev_quantiles, gev["k"], gev["xi"], gev["alpha"]),
        "lmom::quape3": (pearson3_quantiles, pe3["gamma"], pe3["mu"], pe3["sigma"]),
        "lmom::qualn3": (
            log_normal_quantiles,
            ln3["sigma"],
            ln3["zeta"],
            math.exp(ln3["mu"]),
        ),
        "lmom::quawei": (weibull_quantiles, wei["delta"], wei["zeta"], wei["beta"]),
    }


@pytest.mark.parametrize("dataset", sorted(SAMPLES))
@pytest.mark.parametrize(
    "function", ["lmom::quagev", "lmom::quape3", "lmom::qualn3", "lmom::quawei"]
)
def test_the_quantiles_are_lmoms(dataset, function):
    """CMP-6.4: lmom's quantiles at its own parameters (frozen, R 4.5.3)."""
    quantile, *parameters = _lmom_quantiles(dataset)[function]
    oracle = _lmom(dataset, function)

    found = quantile(*parameters, RETURN_PERIODS)  # type: ignore[operator]

    assert_within(
        found,
        [oracle[f"T{period:g}"] for period in RETURN_PERIODS],
        rel=1e-10,
        reason="R prints the parameters and quantiles to 15 significant digits; "
        "lmom's quantile functions (R's qgamma, qnorm) and scipy's agree to about 12",
    )


@pytest.mark.parametrize("dataset", sorted(SAMPLES))
def test_the_moments_are_numpys_and_scipys(dataset):
    """CMP-6.3: NumPy's mean and std (ddof 1) and SciPy's skew (bias False, G1)."""
    values = np.array(SAMPLES[dataset])

    found = sample_moments(values)

    assert_within(
        [found.mean, found.std, found.skewness],
        [np.mean(values), np.std(values, ddof=1), skew(values, bias=False)],
        rel=1e-13,
        reason="the same two-pass moments in another order of operations",
    )


@pytest.mark.parametrize("dataset", sorted(SAMPLES))
@pytest.mark.parametrize("function", ["lmom::samlmu", "lmomco::lmoms"])
def test_the_l_moments_are_those_of_r(dataset, function):
    """CMP-6.4: Hosking's samlmu and Asquith's lmoms (frozen, R 4.5.3)."""
    oracle = _lmom(dataset, function)

    found = sample_l_moments(SAMPLES[dataset])

    assert_within(
        [found.l1, found.l2, found.t3],
        [oracle["l1"], oracle["l2"], oracle["t3"]],
        rel=1e-13,
        reason="R prints 15 significant digits; both sides sum the same unbiased "
        "probability-weighted moments",
    )


def test_long_samples_keep_their_moments():
    """Trap many_small_terms: 20,000 values against rational arithmetic."""
    rng = np.random.default_rng(20261119)
    values = 1000.0 + 100.0 * rng.standard_normal(20_000)
    exact = [Fraction(float(value)) for value in values]
    n = len(exact)
    mean = sum(exact, Fraction(0)) / n
    m2 = sum(((value - mean) ** 2 for value in exact), Fraction(0)) / n
    ascending = sorted(exact)
    b1 = sum((j * x for j, x in enumerate(ascending)), Fraction(0)) / (n * (n - 1))

    moments = sample_moments(values)
    l_moments = sample_l_moments(values)

    assert_within(
        [moments.mean, moments.std, l_moments.l1, l_moments.l2],
        [
            float(mean),
            math.sqrt(float(m2 * n / (n - 1))),
            float(mean),
            float(2 * b1 - mean),
        ],
        rel=1e-13,
        reason="NumPy's pairwise sums of 20,000 terms round within about log2(n) ulp; "
        "a naive running sum would lose about n ulp",
    )


def test_the_formulas_record_their_versions():
    with recording() as used:
        sample_moments([1.0, 2.0, 4.0])
        sample_l_moments([1.0, 2.0, 4.0])
        gev_quantiles(0.1, 10.0, 2.0, [100.0])
        log_normal_quantiles(0.5, 0.0, 10.0, [100.0])
        pearson3_quantiles(1.0, 10.0, 2.0, [100.0])
        weibull_quantiles(1.5, 1.0, 10.0, [100.0])
        for fit in (fit_l_moments, fit_moments, fit_maximum_likelihood):
            fit(POLANA, "gev")
        fit_least_squares(POLANA, "gev")
        compute_plotting_positions(POLANA, "weibull")
        compute_non_exceedance_positions(POLANA, "weibull")
        anderson_darling(POLANA, "gev", -0.18, 20.9, 16.4)
        akaike_information_criterion(POLANA, "gev", -0.18, 20.9, 16.4)

    assert used == {spec.name: spec.formula_version for spec, _ in FAMILY}


@given(inputs=strategies(FIT_L_MOMENTS))
def test_fit_l_moments_properties(inputs):
    assert_property_contract(FIT_L_MOMENTS, as_standard(fit_l_moments), inputs, ERRORS)
    assert_properties(FIT_L_MOMENTS, as_standard(fit_l_moments), inputs, ERRORS)


@given(inputs=strategies(FIT_MOMENTS))
def test_fit_moments_properties(inputs):
    assert_property_contract(FIT_MOMENTS, as_standard(fit_moments), inputs, ERRORS)
    assert_properties(FIT_MOMENTS, as_standard(fit_moments), inputs, ERRORS)


@given(inputs=strategies(FIT_MAXIMUM_LIKELIHOOD))
def test_fit_maximum_likelihood_properties(inputs):
    function = as_standard(fit_maximum_likelihood)
    assert_property_contract(FIT_MAXIMUM_LIKELIHOOD, function, inputs, ERRORS)
    assert_properties(FIT_MAXIMUM_LIKELIHOOD, function, inputs, ERRORS)


@given(inputs=strategies(FIT_LEAST_SQUARES))
def test_fit_least_squares_properties(inputs):
    function = as_standard(fit_least_squares)
    assert_property_contract(FIT_LEAST_SQUARES, function, inputs, ERRORS)
    assert_properties(FIT_LEAST_SQUARES, function, inputs, ERRORS)


@given(inputs=strategies(PLOTTING_POSITIONS))
def test_plotting_positions_properties(inputs):
    function = as_standard(compute_plotting_positions)
    assert_property_contract(PLOTTING_POSITIONS, function, inputs, ERRORS)
    assert_properties(PLOTTING_POSITIONS, function, inputs, ERRORS)


@given(inputs=strategies(NON_EXCEEDANCE_POSITIONS))
def test_non_exceedance_positions_properties(inputs):
    function = as_standard(compute_non_exceedance_positions)
    assert_property_contract(NON_EXCEEDANCE_POSITIONS, function, inputs, ERRORS)
    assert_properties(NON_EXCEEDANCE_POSITIONS, function, inputs, ERRORS)


@pytest.mark.parametrize(
    ("method", "a"), [("weibull", 0.0), ("hazen", 0.5), ("cunnane", 0.4)]
)
@pytest.mark.parametrize("sample", [POLANA, list(frequency._FLOODS11)])
def test_the_plotting_positions_are_scipys(sample, method, a):
    """CMP-6.3: scipy's (i - alpha) / (n + 1 - alpha - beta), alpha = beta = a."""
    minima = compute_non_exceedance_positions(sample, method)
    maxima = compute_plotting_positions(sample, method)
    ascending = np.sort(plotting_positions(np.array(sample), alpha=a, beta=a))
    of_the_negated = np.sort(plotting_positions(-np.array(sample), alpha=a, beta=a))

    assert_within(
        [minima.non_exceedance_probabilities, maxima.exceedance_prob],
        [ascending, of_the_negated],
        rel=4.5e-16,
        reason="scipy rounds (i - a) / (n + 1 - 2a) as the code does, with alpha + "
        "beta for 2a: the same value within an ulp or two",
    )


@given(inputs=strategies(ANDERSON_DARLING))
def test_anderson_darling_properties(inputs):
    function = as_standard(anderson_darling)
    assert_property_contract(ANDERSON_DARLING, function, inputs, ERRORS)
    assert_properties(ANDERSON_DARLING, function, inputs, ERRORS)


@given(inputs=strategies(AKAIKE))
def test_akaike_information_criterion_properties(inputs):
    function = as_standard(akaike_information_criterion)
    assert_property_contract(AKAIKE, function, inputs, ERRORS)
    assert_properties(AKAIKE, function, inputs, ERRORS)


@pytest.mark.parametrize("sample", [POLANA, list(frequency._FLOODS11)])
def test_the_a_squared_is_scipys(sample):
    """CMP-6.3: scipy's A² of the normal and Gumbel distributions it estimates."""
    data = np.array(sample)
    normal = anderson(data, dist="norm", method="interpolate")
    gumbel = anderson(data, dist="gumbel_r", method="interpolate")
    loc, scale = gumbel_r.fit(data)
    mean, std = float(np.mean(data)), float(np.std(data, ddof=1))

    assert_within(
        [
            anderson_darling(sample, "pearson3", 0.0, mean, std),
            anderson_darling(sample, "gev", 0.0, float(loc), float(scale)),
        ],
        [normal.statistic, gumbel.statistic],
        rel=1e-12,
        reason="scipy sums ln F and ln(1 - F) as logcdf and logsf; the code takes the "
        "logarithms of F, rounded within an ulp, whose logarithms differ by an ulp "
        "over 1 - F",
    )


def test_the_delegated_ks_test_gives_the_exact_statistic_and_p():
    """DELEGATED kolmogorov_smirnov_test: D and the exact p of three values."""
    found = kstest([0.05, 0.1, 0.2], uniform.cdf)

    assert_within(
        [found.statistic, found.pvalue],
        [0.8, 2.0 * 0.2**3],
        rel=1e-12,
        reason="D = 1 - 0.2 by hand; p = 2 (1 - D)**3, the exact distribution of D of "
        "three values for D >= 2/3, which scipy computes for small samples",
    )


def test_the_delegated_distribution_functions_are_the_closed_forms():
    """DELEGATED distribution_functions: F of the four distributions at one point."""
    found = [
        genextreme.cdf(1.0, 0.5),
        lognorm.cdf(math.e, 1.0),
        pearson3.cdf(1.0, 2.0),
        weibull_min.cdf(1.0, 2.0),
    ]

    assert_within(
        found,
        [
            math.exp(-0.25),
            0.5 * (1.0 + math.erf(1.0 / math.sqrt(2.0))),
            -math.expm1(-2.0),
            -math.expm1(-1.0),
        ],
        rel=1e-14,
        reason="exp(-(1 - c x)**(1/c)), Phi(ln x / s), the exponential distribution "
        "from -1 (gamma shape 1) and 1 - exp(-x**k) by hand, each within a few ulp",
    )


def test_the_delegated_densities_are_the_closed_forms():
    """DELEGATED densities: f and ln f of the four distributions at one point."""
    points = [
        (genextreme, 0.5, 1.0),
        (lognorm, 1.0, math.e),
        (pearson3, 2.0, 1.0),
        (weibull_min, 2.0, 1.0),
    ]
    exact = [
        math.exp(-0.25) / 2.0,
        math.exp(-1.5) / math.sqrt(2.0 * math.pi),
        math.exp(-2.0),
        2.0 * math.exp(-1.0),
    ]

    assert_within(
        [d.pdf(x, shape) for d, shape, x in points]
        + [d.logpdf(x, shape) for d, shape, x in points],
        exact + [math.log(value) for value in exact],
        rel=1e-14,
        reason="the densities written out at the point by hand, each within a few ulp",
    )


@pytest.mark.parametrize("dataset", sorted(SAMPLES))
@pytest.mark.parametrize(
    ("distribution", "function", "names", "rel"),
    [
        ("gev", "lmomco::pargev(useHosking=FALSE)", ("k", "xi", "alpha"), 1e-7),
        ("gev", "lmom::pelgev", ("k", "xi", "alpha"), 1e-5),
        ("pearson3", "lmom::pelpe3", ("gamma", "mu", "sigma"), 1e-7),
        ("weibull", "lmom::pelwei", ("delta", "zeta", "beta"), 1e-5),
    ],
)
def test_the_l_moment_fits_are_those_of_r(dataset, distribution, function, names, rel):
    """CMP-6.4: Hosking's pel* and Asquith's pargev (frozen, R 4.5.3)."""
    oracle = _lmom(dataset, function)

    found = fit_l_moments(SAMPLES[dataset], distribution)

    assert_within(
        list(found),
        [oracle[name] for name in names],
        rel=rel,
        abs=1e-6,
        reason="pargev solves the GEV shape exactly, as Hydrolog; pelgev and pelwei "
        "take it from Donaldson's approximation, within 2e-7 of it; pelpe3 uses the "
        "same rational approximations of alpha, but its Gamma(alpha) / Gamma(alpha + "
        "1/2) of sigma agrees with scipy's gammaln within 3e-8; R prints 15 digits",
    )


@pytest.mark.parametrize("dataset", sorted(SAMPLES))
def test_the_log_normal_l_moment_fit_is_lmoms(dataset):
    """CMP-6.4: pelln3 with bound 0 is the log-normal of location 0 (frozen)."""
    oracle = _lmom(dataset, "lmom::pelln3(bound=0)")

    found = fit_l_moments(SAMPLES[dataset], "log_normal")

    assert_within(
        list(found),
        [oracle["sigma"], oracle["zeta"], math.exp(oracle["mu"])],
        rel=1e-12,
        abs=1e-300,
        reason="sigma = sqrt(2) Phi^-1((1 + l2 / l1) / 2) in lmom and 2 erfinv(l2 / "
        "l1) in Hydrolog, the same number; R prints 15 significant digits",
    )


@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
@pytest.mark.parametrize("sample", [POLANA, list(frequency._FLOODS11)])
def test_powell_finds_no_smaller_squares(sample, distribution):
    """Oracle of fit_least_squares: Powell's method from the estimate gains nothing."""
    found = fit_least_squares(sample, distribution)
    ascending = np.sort(sample)
    positions = np.arange(1, ascending.size + 1) / (ascending.size + 1)
    law = frequency._DISTRIBUTIONS[distribution]
    fixed = distribution == "log_normal"

    def squares(point):
        shape, loc, log_scale = point
        with np.errstate(all="ignore"):
            quantiles = law.ppf(
                positions, shape, 0.0 if fixed else loc, np.exp(log_scale)
            )
        total = math.fsum((ascending - quantiles) ** 2)
        return total if math.isfinite(total) else math.inf

    start = [found.shape, found.loc, math.log(found.scale)]
    least = squares(start)
    powell = minimize(
        squares, start, method="Powell", options={"xtol": 1e-10, "ftol": 1e-15}
    )

    assert_within(
        max(least - powell.fun, 0.0),
        0.0,
        abs=1e-8 * least,
        reason="the search settles when a run of Nelder-Mead gains at most 1e-9 of "
        "the sum of squares of the standardised sample",
    )


def test_l_skewness_near_one_clamps_the_gev_shape():
    """Traps singular_at_bound, unbounded_iteration: t3 beyond the bracket's end."""
    low = frequency._GEV_SHAPES_BY_L_SKEWNESS[0]
    sample = [0.0] * 40 + [1e-12, 1.0]
    t3 = sample_l_moments(sample).t3
    assert frequency._gev_l_skewness(low) < t3 < 1.0

    found = fit_l_moments(sample, "gev")

    assert found.shape == low
    assert all(math.isfinite(value) for value in found)


def test_a_skewness_beyond_the_bracket_clamps():
    """Trap unbounded_iteration of fit_moments: brentq needs a change of sign."""
    bracket = frequency._GEV_SHAPES_BY_SKEWNESS

    found = frequency._gev_from_moments(0.0, 1.0, 1e9, bracket)

    assert found[0] == bracket[0]
    assert all(math.isfinite(value) for value in found)


@pytest.mark.parametrize(
    ("fit", "constraint"),
    [
        (fit_maximum_likelihood, "likelihood_has_a_maximum"),
        (fit_least_squares, "squares_have_a_minimum"),
    ],
)
def test_a_search_that_does_not_settle_is_refused(fit, constraint, monkeypatch):
    """Trap unbounded_iteration: no run after the first, so no search settles."""
    monkeypatch.setattr(frequency, "_SEARCH_RUNS", 0)
    frequency._likelihood_search.cache_clear()
    frequency._squares_search.cache_clear()
    try:
        with pytest.raises(InvalidParameterError) as caught:
            fit(POLANA, "gev")
    finally:
        frequency._likelihood_search.cache_clear()
        frequency._squares_search.cache_clear()

    assert caught.value.details["constraint"] == constraint


@pytest.mark.parametrize("distribution", ["gev", "pearson3", "weibull"])
@pytest.mark.parametrize(
    ("fit", "rel"),
    [
        (fit_l_moments, 1e-9),
        (fit_moments, 1e-9),
        (fit_maximum_likelihood, 1e-4),
        (fit_least_squares, 1e-4),
    ],
)
def test_a_large_mean_shifts_the_fits(fit, rel, distribution):
    """Trap moment_cancellation: a mean of 1e9 and a spread of 0.1 m3/s."""
    shifted = 1.0e9 + np.array(POLANA) / 1000.0
    exact = shifted - 1.0e9  # the spread the floats hold, without rounding

    far = fit(shifted, distribution)
    near = fit(exact, distribution)

    assert_within(
        [far.shape, far.loc - 1.0e9, far.scale],
        [near.shape, near.loc, near.scale],
        rel=rel,
        abs=1e-6,
        reason="the statistics of the shifted sample keep the digits of its spread "
        "(double centring on the sample divided by a power of two); loc + 1e9 rounds "
        "to 1.2e-7; a search settles within 1e-9 of its objective, so its parameters "
        "within about 1e-4",
    )
