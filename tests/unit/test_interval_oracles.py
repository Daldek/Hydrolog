"""The oracles of the interval specs: the bootstrap and the delta method of quantiles.

Frozen oracles (Nogat CMP-6.4), run once by the R scripts beside them in
``tests/oracles/``: lmomco's ``qua2ci.simple`` for the parametric bootstrap
(``interval_lmomco_r.csv``) and extRemes's ``ci.fevd(method = "normal")`` for the
delta method of the GEV (``interval_extremes_r.csv``). Exact oracles (CMP-6.2): the
standard errors of the delta method in mpmath at 50 digits, each in another form than
the code's: Pearson III by KZGW's phi(p, lambda) of eq. 3.27, the Weibull and the
log-normal by the inverse of their expected information, the GEV by mpmath's
derivatives of its log-likelihood. Each comparison names the conventions of both sides
(CMP-6.3) and each tolerance its reason (CMP-6.8).
"""

import csv
import math
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import mpmath
import numpy as np
import pytest
from numpy.typing import NDArray
from scipy.stats import gamma as gamma_distribution
from scipy.stats import lognorm, pearson3, rv_continuous, weibull_min

from hydrolog.nogat_formulas import assert_within, read_frozen_oracle
from hydrolog.statistics import frequency, low_flows
from hydrolog.statistics.frequency import (
    fit_l_moments,
    gev_quantiles,
    log_normal_quantiles,
    pearson3_quantiles,
    weibull_quantiles,
)
from hydrolog.statistics.intervals import (
    quantile_interval_bootstrap,
    quantile_interval_delta,
)

pytestmark = pytest.mark.formula

ORACLES = Path(__file__).parents[1] / "oracles"
LMOMCO = read_frozen_oracle(ORACLES / "interval_lmomco_r.csv")
EXTREMES = read_frozen_oracle(ORACLES / "interval_extremes_r.csv")
LEVELS = (0.95, 0.68)
"""The levels of the oracles, those Obserwator stores."""
DISTRIBUTIONS = ("gev", "pearson3", "log_normal", "weibull")
POLANA = list(frequency._POLANA)
DIGITS = 50
"""The working precision of the exact oracles [decimal digits]."""


def _table(rows: Sequence[Mapping[str, str]], column: str) -> NDArray[np.float64]:
    """Return a column of oracle rows as (levels of LEVELS, ascending periods)."""
    periods = _periods(rows)
    out = np.full((len(LEVELS), len(periods)), np.nan)
    for row in rows:
        level = LEVELS.index(float(row["confidence_level"]))
        out[level, periods.index(float(row["return_period"]))] = float(row[column])
    return out


def _periods(rows: Sequence[Mapping[str, str]]) -> list[float]:
    return sorted({float(row["return_period"]) for row in rows})


def _z(level: float) -> float:
    """z = Phi^-1((1 + c)/2) = sqrt(2) erfinv(c), at 50 digits."""
    with mpmath.workdps(DIGITS):
        return float(mpmath.sqrt(2) * mpmath.erfinv(mpmath.mpf(level)))


Z = np.array([_z(level) for level in LEVELS])[:, None]
"""z of each level of LEVELS, a column."""


# --- the parametric bootstrap: lmomco's qua2ci.simple (frozen) ----------------------

SCIPY_OF_LMOMCO: Mapping[str, Callable[[float, float, float], tuple[float, ...]]] = {
    "gev": lambda xi, alpha, kappa: (kappa, xi, alpha),
    "pe3": lambda mu, sigma, gamma: (gamma, mu, sigma),
    "ln3": lambda zeta, mulog, sigmalog: (sigmalog, zeta, math.exp(mulog)),
    "wei": lambda zeta, beta, delta: (delta, -zeta, beta),
}
"""scipy's (shape, loc, scale) of lmomco's para, by the conventions of the oracle's
header: Hosking's GEV kappa is scipy's c; Pearson III (mu, sigma, gamma) is (loc, scale,
skew); ln3 with zeta = 0 is lognorm(s = sigmalog, scale = exp(mulog)); lmomco's Weibull
(zeta, beta, delta) is weibull_min(delta, loc = -zeta, scale = beta)."""
QUANTILES = {
    "gev": gev_quantiles,
    "pearson3": pearson3_quantiles,
    "log_normal": log_normal_quantiles,
    "weibull": weibull_quantiles,
}
Z_BRACKET = 4.0
"""Binomial standard deviations of the Monte Carlo bracket of a bootstrap bound."""


def _lmomco_rows(distribution: str) -> list[Mapping[str, str]]:
    return [row for row in LMOMCO.rows if row["distribution"] == distribution]


def _parent(row: Mapping[str, str]) -> tuple[float, ...]:
    """scipy's (shape, loc, scale) of the parent of an lmomco row."""
    para = (float(row["para1"]), float(row["para2"]), float(row["para3"]))
    return SCIPY_OF_LMOMCO[row["lmomco_type"]](*para)


@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
def test_lmomcos_parents_are_hydrologs_l_moment_fits_of_polana(distribution):
    """CMP-6.3: the oracle's parents, in scipy's parameters, are fit_l_moments's.

    lmomco 2.5.8 fits lmoms(polana) by pargev (useHosking = FALSE), parpe3, parln3
    (zeta = 0) and parwei; Hydrolog by fit_l_moments, scipy's (shape, loc, scale) by the
    conventions of SCIPY_OF_LMOMCO. lmomco's quantiles of its parent (``true``, its
    par2qua) are Hydrolog's quantile functions at the converted parameters.
    """
    rows = _lmomco_rows(distribution)
    parent = _parent(rows[0])

    assert_within(
        parent,
        list(fit_l_moments(POLANA, distribution)),
        rel=1e-6,
        abs=1e-300,
        reason="pargev's uniroot (tol 1.5e-8 of kappa) against Hydrolog's brentq; "
        "parwei takes the reversed GEV's kappa from Hosking's rational approximation, "
        "within 2e-7 of the exact one; parpe3 and Hydrolog use the same approximations "
        "of alpha; R prints 17 significant digits",
    )
    assert_within(
        QUANTILES[distribution](*parent, _periods(rows)),
        _table(rows, "true")[0],
        rel=1e-10,
        reason="the same quantile function of the same parameters: lmomco's "
        "par2qua (R's qgamma, qnorm, the reversed GEV of quawei) and scipy's agree "
        "to about 12 significant digits",
    )


@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
def test_the_bootstrap_bounds_hold_lmomcos_empirical_limits(distribution):
    """CMP-6.4: lmomco 2.5.8's empirical limits lie in Hydrolog's Monte Carlo bracket.

    Two conventions of lmomco's qua2ci.simple (n = 34 values drawn nsim = 20000 times
    from the parent, each refitted by L-moments, a sample it cannot fit redrawn): its
    ``lwr``/``upr`` are the quantiles (1 -+ c)/2 of the generalized normal (edist "gno")
    fitted by L-moments to the simulated quantiles; its ``empdist`` limits are their
    empirical quantiles by R's quantile type 6, positions i/(nsim + 1). Hydrolog's spec
    is the second convention on its own B refits of 999 samples (numpy's method
    "weibull", type 6; a sample it cannot fit left out, none here), so the empirical
    limits are its oracle. The gno limits differ from them by at most 2.9 % of a limit
    (the GEV's lower limit at T = 1000, c = 0.95: 95.29 against 92.64) and 2.1 % of a
    half-width: within this bracket too, below the Monte Carlo error of 999 refits.

    Different generators give different samples, so the check is statistical: lmomco's
    limit at the tail probability q = (1 -+ c)/2 lies between Hydrolog's quantiles of
    its refits at q -+ w, w = z sqrt(q (1 - q) (1/B + 1/nsim)), i.e. between its order
    statistics B q -+ z sqrt(B q (1 - q) (1 + B/nsim)): the count of Hydrolog's refit
    quantiles below lmomco's limit is binomial (B, q), and lmomco's limit has its own
    Monte Carlo spread of q (1 - q)/nsim. Hydrolog gives those quantiles as the bounds
    at the levels c -+ 2 w of the same refits. The largest of the 128 limits reaches
    0.86 of its bracket (Pearson III, T = 2, c = 0.68, where lmomco's run lies two of
    its standard deviations below four reruns with other seeds). Mutants measured
    against the bracket: the GEV's c of the other sign 44 times it, refits by moments
    1.9 to 5.3, a bound read at c instead of (1 + c)/2 2.1 to 2.3, n = 24 1.2 to 1.7;
    n = 30 instead of 34 stays inside (0.94), a difference of the Monte Carlo order.
    """
    rows = _lmomco_rows(distribution)
    shape, loc, scale = _parent(rows[0])
    size, nsim = int(rows[0]["n"]), int(rows[0]["nsim"])
    periods = _periods(rows)
    kept = quantile_interval_bootstrap(
        distribution, shape, loc, scale, size, periods, list(LEVELS), "stage"
    ).samples
    widths = [
        Z_BRACKET * math.sqrt(q * (1.0 - q) * (1.0 / kept + 1.0 / nsim))
        for q in ((1.0 - c) / 2.0 for c in LEVELS)
    ]
    wider = [c + 2.0 * w for c, w in zip(LEVELS, widths, strict=True)]
    narrower = [c - 2.0 * w for c, w in zip(LEVELS, widths, strict=True)]

    found = quantile_interval_bootstrap(
        distribution, shape, loc, scale, size, periods, wider + narrower, "stage"
    )

    count = len(LEVELS)
    brackets = {
        "empirical_lwr": (found.lower[:count], found.lower[count:]),
        "empirical_upr": (found.upper[count:], found.upper[:count]),
    }
    for column, (low, high) in brackets.items():
        middle, half = (low + high) / 2.0, (high - low) / 2.0
        assert_within(
            (_table(rows, column) - middle) / half,
            np.zeros((count, len(periods))),
            abs=1.0,
            reason=f"{column} of lmomco within Hydrolog's quantiles at q -+ w, z = "
            f"{Z_BRACKET:g}: a right implementation lands outside with probability "
            "6e-5 per limit (normal approximation of the binomial count), under 1 % "
            "over the 128 limits of the four distributions; a wrong parent, refit "
            "method or tail of a level moves limits beyond it",
        )


# --- the delta method of the GEV: extRemes's ci.fevd (frozen) and mpmath (exact) ----


def _ml_samples() -> dict[str, list[float]]:
    """The samples of frequency_ml_samples.csv by dataset, and the minima of 223207."""
    found: dict[str, list[float]] = {}
    with (ORACLES / "frequency_ml_samples.csv").open(encoding="utf-8") as stream:
        lines = (line for line in stream if not line.startswith("#"))
        for row in csv.DictReader(lines):
            found.setdefault(row["dataset"], []).append(float(row["value"]))
    found["station_223207"] = list(low_flows._STATION_223207)
    return found


SAMPLES = _ml_samples()
EXTREMES_DATASETS = sorted({row["dataset"] for row in EXTREMES.rows})


def _extremes_case(
    dataset: str,
) -> tuple[list[Mapping[str, str]], str, tuple[float, float, float]]:
    """The rows of a dataset, its extremes and Hydrolog's (shape, loc, scale) of them.

    extRemes's (location, scale, shape) is the GEV (mu, sigma, xi) of the sample it
    fitted: scipy's c = -xi; for minima that sample is the negated minima, whose
    location fisher_tippett_minima gives negated.
    """
    rows = [row for row in EXTREMES.rows if row["dataset"] == dataset]
    first = rows[0]
    location, scale, xi = (float(first[k]) for k in ("location", "scale", "shape"))
    extremes = first["extremes"]
    loc = -location if extremes == "minima" else location
    return rows, extremes, (-xi, loc, scale)


@pytest.mark.parametrize("dataset", EXTREMES_DATASETS)
def test_the_gev_interval_is_extremes_normal_interval(dataset):
    """CMP-6.4: extRemes 2.2.1's ci.fevd(method = "normal") at its own estimates.

    extRemes: the GEV (mu, sigma, xi) of the sample it fits (minima: the negated
    minima), rl -+ z se, se from the inverse of optimHess (central differences, step
    1e-3, of its analytic gradient of the negative log-likelihood) and the analytic
    gradient of the return level. Hydrolog: scipy's c = -xi (minima: loc = -mu, the
    bounds of the T-year minimum -upper and -lower), the observed information by
    central differences (steps 1e-4) of the log-likelihood. Evaluated at extRemes's
    estimates, the difference of the two searches (extRemes stops short of the
    maximum of pe3_g1.0_n50) drops out; the points and the half-widths compare apart.
    """
    rows, extremes, (shape, loc, scale) = _extremes_case(dataset)
    lower, estimate, upper = (_table(rows, k) for k in ("lower", "estimate", "upper"))
    if extremes == "minima":
        lower, estimate, upper = -upper, -estimate, -lower

    found = quantile_interval_delta(
        SAMPLES[dataset],
        "gev",
        shape,
        loc,
        scale,
        _periods(rows),
        LEVELS,
        "stage",
        extremes,
    )

    assert_within(
        (found.lower + found.upper) / 2.0,
        estimate,
        rel=1e-12,
        reason="the same return level of the same parameters, extRemes's rlevd and "
        "scipy's genextreme.isf in other orders of operations: 5e-15 measured, (1 - "
        "y**-xi)/xi losing digits as xi -> 0 (|xi| = 0.016 here)",
    )
    assert_within(
        (found.upper - found.lower) / 2.0,
        (upper - lower) / 2.0,
        rel=5e-4,
        reason="two finite-difference Hessians: against the information mpmath "
        "differentiates at 50 digits, extRemes's optimHess (step 1e-3 in the units of "
        "each parameter) is off by up to 1.7e-4 of se (station 223207, xi = -0.45) "
        "and Hydrolog's by up to 2.2e-6",
    )


def _gev_log_likelihood(
    sample: Sequence[mpmath.mpf], mu: mpmath.mpf, sigma: mpmath.mpf, xi: mpmath.mpf
) -> mpmath.mpf:
    """Coles's (2001) eq. 3.7: the GEV log-likelihood for xi != 0."""
    total = -len(sample) * mpmath.log(sigma)
    for value in sample:
        t = 1 + xi * (value - mu) / sigma
        total -= (1 + 1 / xi) * mpmath.log(t) + t ** (-1 / xi)
    return total


def _return_level(period: float) -> Callable[..., object]:
    """The GEV's return level of T years, a function of (mu, sigma, xi): Coles 3.10."""
    y = -mpmath.log(1 - 1 / mpmath.mpf(period))
    return lambda mu, sigma, xi: mu - sigma / xi * (1 - y ** (-xi))


def _gev_sigma(
    sample: Sequence[float], point: tuple[float, float, float], periods: Sequence[float]
) -> NDArray[np.float64]:
    """sigma of the GEV's return levels, the observed information by mpmath.diff."""
    with mpmath.workdps(DIGITS):
        values = [mpmath.mpf(value) for value in sample]
        at = [mpmath.mpf(value) for value in point]

        def log_likelihood(mu: object, sigma: object, xi: object) -> object:
            return _gev_log_likelihood(values, mu, sigma, xi)

        hessian = mpmath.matrix(3, 3)
        for i in range(3):
            for j in range(i, 3):
                order = [0, 0, 0]
                order[i] += 1
                order[j] += 1
                hessian[i, j] = mpmath.diff(log_likelihood, at, tuple(order))
                hessian[j, i] = hessian[i, j]
        covariance = (-hessian) ** -1
        units = [tuple(int(k == i) for k in range(3)) for i in range(3)]
        sigmas = []
        for period in periods:
            level = _return_level(period)
            gradient = mpmath.matrix([mpmath.diff(level, at, unit) for unit in units])
            sigmas.append(mpmath.sqrt((gradient.T * covariance * gradient)[0, 0]))
        return np.array([float(s) for s in sigmas])


@pytest.mark.parametrize("dataset", ["floods11", "portpirie", "station_223207"])
def test_the_gev_observed_information_is_mpmaths(dataset):
    """CMP-6.2: se of the GEV's return levels by mpmath's derivatives at 50 digits.

    The oracle: Coles's log-likelihood of the sample extRemes fitted, its Hessian and
    the gradient of the return level by mpmath.diff at extRemes's estimates (xi 0.43,
    -0.05 and -0.45 for the negated minima: the heavy tail, the Gumbel and the bound
    near the irregular xi = -0.5); Hydrolog: central differences (steps 1e-4) of the
    standardised log-likelihood and the analytic gradient. Half-widths compared, as
    z se.
    """
    rows, extremes, (shape, loc, scale) = _extremes_case(dataset)
    periods = _periods(rows)
    minima = extremes == "minima"
    fitted = [-value for value in SAMPLES[dataset]] if minima else SAMPLES[dataset]
    sigma = _gev_sigma(fitted, (-loc if minima else loc, scale, -shape), periods)

    found = quantile_interval_delta(
        SAMPLES[dataset], "gev", shape, loc, scale, periods, LEVELS, "stage", extremes
    )

    assert_within(
        (found.upper - found.lower) / 2.0,
        Z * sigma,
        rel=1e-5,
        reason="Hydrolog's Hessian by central differences of step 1e-4 of the "
        "standardised parameters: the rounding of a log-likelihood of order 1e2 over "
        "a step squared of 1e-8 leaves about 2e-6 of the information",
    )


# --- the delta method's closed forms: mpmath at 50 digits (exact) -------------------

PERIODS = (1.25, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0)
SIZE = 34
"""N of the exact oracles, the Polana record's."""


def _inside(law: rv_continuous, *parameters: float) -> list[float]:
    """N values inside the support: the quantiles at i/(N + 1)."""
    positions = np.arange(1, SIZE + 1) / (SIZE + 1)
    return [float(value) for value in law.ppf(positions, *parameters)]


def _gamma_density(shape: mpmath.mpf, t: mpmath.mpf) -> mpmath.mpf:
    return mpmath.exp((shape - 1) * mpmath.log(t) - t - mpmath.loggamma(shape))


def _gamma_quantile(shape: mpmath.mpf, probability: mpmath.mpf) -> mpmath.mpf:
    """The standard gamma quantile t, P(shape, t) = probability, by Newton's method."""
    t = mpmath.mpf(float(gamma_distribution.ppf(float(probability), float(shape))))
    for _ in range(10):
        lower = mpmath.gammainc(shape, 0, t, regularized=True)
        step = (lower - probability) / _gamma_density(shape, t)
        t -= step
        if abs(step) <= abs(t) * mpmath.mpf(10) ** (5 - DIGITS):
            return t
    raise AssertionError(f"no gamma quantile of shape {shape} at {probability}")


def _pearson3_exact(
    skew: float, loc: float, scale: float, period: float
) -> tuple[float, float]:
    """KZGW eq. 3.3 and 3.27: Q_T and sigma(Q_T) = phi(p, lambda) / (alpha sqrt(N)).

    phi**2 = (lambda t'**2 - 2 t' t + psi'(lambda) t**2) / (lambda psi'(lambda) - 1), t
    the standard gamma quantile of shape lambda = 4 / G**2 at the gamma's
    non-exceedance (1 - p above the bound, p below it for G < 0, the mirror), t' = dt/
    dlambda = -(dP/dlambda) / (dP/dt) by mpmath.diff of the regularized incomplete
    gamma P; alpha = 2 / (scale |G|), the bound loc - 2 scale / G.
    """
    with mpmath.workdps(DIGITS):
        g = mpmath.mpf(skew)
        shape = 4 / g**2
        alpha = 2 / (mpmath.mpf(scale) * abs(g))
        exceedance = 1 / mpmath.mpf(period)
        t = _gamma_quantile(shape, 1 - exceedance if g > 0 else exceedance)
        slope = mpmath.diff(lambda a: mpmath.gammainc(a, 0, t, regularized=True), shape)
        t_prime = -slope / _gamma_density(shape, t)
        trigamma = mpmath.psi(1, shape)
        phi = mpmath.sqrt(
            (shape * t_prime**2 - 2 * t_prime * t + trigamma * t**2)
            / (shape * trigamma - 1)
        )
        bound = mpmath.mpf(loc) - 2 * mpmath.mpf(scale) / g
        quantile = bound + mpmath.sign(g) * t / alpha
        return float(quantile), float(phi / (alpha * mpmath.sqrt(SIZE)))


@pytest.mark.parametrize(
    "skew",
    [
        sign * skew
        for skew in (0.009, 0.1, 0.4, 0.7, 1.0, 1.3, 1.6, 1.9)
        for sign in (1.0, -1.0)
    ],
)
def test_pearson3_sigma_is_kzgw_phi_in_mpmath(skew):
    """CMP-6.2: Pearson III's interval is Q_T -+ z phi(p, lambda) / (alpha sqrt(N)).

    The oracle: eq. 3.27's phi of KZGW (2017) at 50 digits, t and t' by mpmath (the
    function of table A.4, computed); Hydrolog: the same variance rearranged as scale**2
    / N [(1 + G K / 2)**2 + (K + G dK/dG)**2 / (4 lambda (lambda psi'(lambda) - 1))]
    with dK/dG by Richardson-extrapolated central differences, the Cornish-Fisher
    expansion below |G| = 0.01 and lambda's asymptotic series above lambda = 10, so
    the skews reach every branch (0.009 the expansion near its end, where it is
    least accurate). A negative G is the mirror of the gamma.
    """
    loc, scale = 33.9, 27.0
    exact = [_pearson3_exact(skew, loc, scale, period) for period in PERIODS]
    quantiles = np.array([quantile for quantile, _ in exact])
    sigmas = np.array([sigma for _, sigma in exact])

    found = quantile_interval_delta(
        _inside(pearson3, skew, loc, scale),
        "pearson3",
        skew,
        loc,
        scale,
        PERIODS,
        LEVELS,
        "stage",
        "maxima",
    )

    assert_within(
        (found.lower + found.upper) / 2.0,
        np.broadcast_to(quantiles, found.lower.shape),
        rel=1e-12,
        reason="scipy's pearson3.isf (Boost's gamma quantile) against mpmath's at 50 "
        "digits, and the mean of the two bounds: 7e-14 measured",
    )
    if abs(skew) < 0.01:
        assert_within(
            (found.upper - found.lower) / 2.0,
            Z * sigmas,
            rel=3e-10,
            reason="the Cornish-Fisher expansion of the gamma quantile to G**3 leaves "
            "a term of order G**4: 1.25e-10 of sigma at |G| = 0.009, 1.8e-10 at the "
            "end of the expansion, |G| = 0.01",
        )
    else:
        assert_within(
            (found.upper - found.lower) / 2.0,
            Z * sigmas,
            rel=5e-11,
            reason="dK/dG by central differences of steps 1e-3 and 5e-4 extrapolated "
            "by Richardson, of scipy's pearson3.isf: 1.1e-11 of sigma at G = -1.9, "
            "where the gamma quantile at 1/T is smallest, 1.3e-12 elsewhere",
        )


def _weibull_exact(
    shape: float, loc: float, scale: float, period: float
) -> tuple[float, float]:
    """Q_T and sigma(Q_T) of the Weibull above its bound, its expected information.

    ln f = ln k - ln beta + (k - 1) ln(w / beta) - u, u = (w / beta)**k ~ Exp(1),
    w = x - loc: the scores are k (u - 1) / beta and (1 + ln u - u ln u) / k, whose
    products' expectations are moments E[u**a ln(u)**m] = Gamma^(m)(a + 1) of the
    unit exponential (mpmath.diff of Gamma); sigma**2 = g' (N I)**-1 g, g the gradient
    of w_T = beta (ln T)**(1/k) in (beta, k) by mpmath.diff. KZGW's eq. 3.57 is its
    closed form.
    """
    with mpmath.workdps(DIGITS):
        k, beta = mpmath.mpf(shape), mpmath.mpf(scale)

        def moment(a: int, m: int) -> mpmath.mpf:
            return mpmath.diff(mpmath.gamma, a + 1, m)

        cross = moment(1, 0) - 1 + 2 * moment(1, 1) - moment(2, 1) - moment(0, 1)
        square = (
            1
            + moment(0, 2)
            + moment(2, 2)
            + 2 * moment(0, 1)
            - 2 * moment(1, 1)
            - 2 * moment(1, 2)
        )
        unit = moment(2, 0) - 2 * moment(1, 0) + 1
        information = SIZE * mpmath.matrix(
            [[(k / beta) ** 2 * unit, cross / beta], [cross / beta, square / k**2]]
        )
        reduced = mpmath.log(mpmath.mpf(period))  # -ln p, p = 1/T

        def excess(b: mpmath.mpf, kk: mpmath.mpf) -> mpmath.mpf:
            return b * reduced ** (1 / kk)

        gradient = mpmath.matrix(
            [
                mpmath.diff(lambda b: excess(b, k), beta),
                mpmath.diff(lambda kk: excess(beta, kk), k),
            ]
        )
        variance = (gradient.T * information**-1 * gradient)[0, 0]
        return float(loc + excess(beta, k)), float(mpmath.sqrt(variance))


@pytest.mark.parametrize("shape", [1.05, 1.2, 1.5, 2.0, 3.0, 5.0, 20.0])
def test_weibull_sigma_is_the_delta_method_of_its_expected_information(shape):
    """CMP-6.2: the Weibull's eq. 3.57, Q_T -+ z (Q_T - loc)/(k sqrt(N)) sqrt(...).

    The oracle: the delta method of the two-parameter Weibull above its bound, held,
    with the inverse of its expected information computed at 50 digits (not eq. 3.57's
    closed form); Hydrolog: eq. 3.57 of KZGW (2017) on Q_T - loc, p = 1/T.
    """
    loc, scale = 4.0, 31.1
    exact = [_weibull_exact(shape, loc, scale, period) for period in PERIODS]
    quantiles = np.array([quantile for quantile, _ in exact])
    sigmas = np.array([sigma for _, sigma in exact])

    found = quantile_interval_delta(
        _inside(weibull_min, shape, loc, scale),
        "weibull",
        shape,
        loc,
        scale,
        PERIODS,
        LEVELS,
        "stage",
        "maxima",
    )

    assert_within(
        np.stack([found.lower, found.upper]),
        np.stack([quantiles - Z * sigmas, quantiles + Z * sigmas]),
        rel=1e-13,
        reason="the closed form in double precision: scipy's weibull_min.isf, the "
        "logarithms and the square root round to a few ulp; 1.2e-14 of the half-width "
        "at k = 20, where (ln T)**(1/k) is near 1",
    )


@pytest.mark.parametrize("shape", [0.1, 0.3, 0.6, 1.0, 1.5])
def test_log_normal_interval_is_eq_3_41_in_mpmath(shape):
    """CMP-6.2: the log-normal's interval, exp(ln Q_T -+ z s / sqrt(N) sqrt(...)).

    The oracle: ln Q_T = mu + s u_p, u_p = sqrt(2) erfinv(1 - 2p) at 50 digits, and
    the variance g' V g of (mu, s), V the inverse expected information of the normal
    with the divisor N of maximum likelihood, diag(s**2/N, s**2/(2N)), g = (1, u_p);
    Hydrolog: KZGW's eq. 3.41 (and 2.9) on Q_T of scipy's lognorm (loc 0).
    """
    scale = 24.5
    with mpmath.workdps(DIGITS):
        s, mu = mpmath.mpf(shape), mpmath.log(mpmath.mpf(scale))
        bounds = []
        for level in LEVELS:
            z = mpmath.sqrt(2) * mpmath.erfinv(mpmath.mpf(level))
            row = []
            for period in PERIODS:
                u = mpmath.sqrt(2) * mpmath.erfinv(1 - 2 / mpmath.mpf(period))
                gradient = mpmath.matrix([1, u])
                covariance = mpmath.diag([s**2 / SIZE, s**2 / (2 * SIZE)])
                spread = z * mpmath.sqrt((gradient.T * covariance * gradient)[0, 0])
                row.append(
                    [mpmath.exp(mu + s * u - spread), mpmath.exp(mu + s * u + spread)]
                )
            bounds.append(row)
        expected = np.array(
            [[[float(b) for b in pair] for pair in row] for row in bounds]
        )

    found = quantile_interval_delta(
        _inside(lognorm, shape, 0.0, scale),
        "log_normal",
        shape,
        0.0,
        scale,
        PERIODS,
        LEVELS,
        "stage",
        "maxima",
    )

    assert_within(
        np.stack([found.lower, found.upper], axis=-1),
        expected,
        rel=1e-14,
        reason="the closed form in double precision: ndtri, exp and the products "
        "round to a few ulp (9e-16 measured)",
    )
