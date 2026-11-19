"""Maximum likelihood of the frequency analyses (the fix of 2026-11-18, Nogat CMP-9.2).

``fit_method="mle"`` of :class:`FloodFrequencyAnalysis` (GEV, Pearson III, Weibull) and
the Fisher-Tippett fit of annual minima (``fit_fisher_tippett_minima``, ``stats
low-flow``) search the maximum of the likelihood on the standardised sample from the
L-moments' estimate, over the shapes short of the limit where the density is infinite
at a bound (Smith 1985). Up to 0.8.1 they called scipy's ``fit``, which starts from the
scale 1 and stopped far from the maximum on samples of hundreds of m³/s (Hydrolog's
sample FLOODS11: Q100 2.5e12 m³/s) and on the minima of small streams (a negative
10-year low flow). The evidence (Nogat CMP-6): the frozen R oracle of ``tests/oracles``
(evd, extRemes, ismev, lmomco), the research's cases (Coles' Port Pirie, FLOODS11, the
minima of a small stream), SciPy's sign of the GEV shape (CMP-6.3), the preconditions,
and two seeded samples of 30 fits against an independent search (Powell's method on the
raw values). Each tolerance gives its reason.
"""

import csv
import warnings
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from scipy.optimize import minimize
from scipy.stats import genextreme, norm, pearson3, weibull_min

from hydrolog._warnings import NegativeQuantiles
from hydrolog.catalog import run_command
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
from hydrolog.statistics.low_flows import fit_fisher_tippett_minima

ORACLES = Path(__file__).resolve().parents[1] / "oracles"
RETURN_PERIODS = np.array([2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0])
_SCIPY = {"gev": genextreme, "pearson3": pearson3, "weibull": weibull_min}
# Annual minima [m3/s] of a small stream (case LOWFLOW-FT-ML-FAILURE-SMALL-STREAM of
# the research of 2026-11-18): 20 draws of Weibull (shape 1.5, loc 0, scale 0.05),
# numpy default_rng(2026), rounded to 0.1 l/s.
SMALL_STREAM = np.array(
    [0.0562, 0.0261, 0.0226, 0.0567, 0.0203, 0.0386, 0.0455, 0.0176, 0.06, 0.0429]
    + [0.049, 0.03, 0.0334, 0.0388, 0.0369, 0.0541, 0.0452, 0.0331, 0.0007, 0.0678]
)


def _oracle(name: str) -> list[dict[str, str]]:
    """Rows of a frozen-oracle CSV of tests/oracles, without its comment header."""
    with (ORACLES / name).open(encoding="utf-8") as stream:
        return list(csv.DictReader(row for row in stream if not row.startswith("#")))


def _samples() -> dict[str, NDArray[np.float64]]:
    values: dict[str, list[float]] = {}
    for row in _oracle("frequency_ml_samples.csv"):
        values.setdefault(row["dataset"], []).append(float(row["value"]))
    return {dataset: np.array(sample) for dataset, sample in values.items()}


SAMPLES = _samples()
R_FITS = _oracle("frequency_ml_r.csv")


def _r_parameters(row: dict[str, str]) -> tuple[float, float, float]:
    """Scipy's ``(shape, loc, scale)`` of a row of frequency_ml_r.csv.

    A GEV row holds Coles' xi, which is scipy's -c
    (:func:`test_scipy_gev_shape_is_minus_coles_xi`); the Pearson III and Weibull rows
    are written in scipy's parameters.
    """
    shape = float(row["shape"])
    if row["distribution"] == "gev":
        shape = -shape
    return shape, float(row["loc"]), float(row["scale"])


def _log_likelihood(distribution, sample, shape, loc, scale) -> float:
    return float(
        np.sum(_SCIPY[distribution].logpdf(sample, shape, loc=loc, scale=scale))
    )


def _fit(distribution, sample, return_periods=RETURN_PERIODS):
    """The maximum-likelihood fit of ``distribution`` and its log-likelihood."""
    with warnings.catch_warnings():
        # small_sample, short_record, ks_test_approximate
        warnings.simplefilter("ignore")
        analysis = FloodFrequencyAnalysis(sample, return_periods)
        result = getattr(analysis, f"fit_{distribution}")(fit_method="mle")
    shape = result.parameters.get("shape", result.parameters.get("skew"))
    loc, scale = result.parameters["loc"], result.parameters["scale"]
    return result, _log_likelihood(distribution, sample, shape, loc, scale)


def _coles_gev_cdf(z, mu, sigma, xi):
    """Coles (2001, eq. 3.2): G(z) = exp{-[1 + xi (z - mu) / sigma]^(-1/xi)}, xi ≠ 0."""
    return np.exp(-np.power(1.0 + xi * (z - mu) / sigma, -1.0 / xi))


@pytest.mark.parametrize("xi", [-0.43, -0.05, 0.05, 0.43])
def test_scipy_gev_shape_is_minus_coles_xi(xi):
    """Scipy's ``genextreme`` with c = -xi is the GEV of Coles and of R (CMP-6.3).

    evd, extRemes and ismev (and the oracle CSV) give Coles' xi, Hydrolog's ``shape``
    is scipy's c: every comparison below turns one into the other by this sign.
    """
    mu, sigma = 120.0, 26.7
    z = mu + sigma * np.linspace(-2.0, 2.0, 9)  # inside the support for |xi| < 0.5
    # one function written in two forms: equal to rounding
    np.testing.assert_allclose(
        genextreme.cdf(z, -xi, loc=mu, scale=sigma),
        _coles_gev_cdf(z, mu, sigma, xi),
        rtol=1e-12,
        atol=0.0,
    )


# --- the frozen R oracle (tests/oracles) ----------------------------------------------

_GEV_DATASETS = sorted(
    {row["dataset"] for row in R_FITS if row["distribution"] == "gev"}
)


def _regular(row: dict[str, str]) -> bool:
    """Whether lmomco's shape lies short of the limit where the likelihood is unbounded.

    Pearson III with |skewness| < 2 and Weibull with a shape above 1 (Smith 1985).
    """
    shape = _r_parameters(row)[0]
    return abs(shape) < 2.0 if row["distribution"] == "pearson3" else shape > 1.0


_LMOMCO = [row for row in R_FITS if row["source"] == "lmomco::mle2par"]
_LMOMCO_REGULAR = [
    pytest.param(row, id=f"{row['dataset']}-{row['distribution']}")
    for row in _LMOMCO
    if _regular(row)
]
_LMOMCO_SINGULAR = [
    pytest.param(row, id=f"{row['dataset']}-{row['distribution']}")
    for row in _LMOMCO
    if not _regular(row)
]


@pytest.mark.parametrize("dataset", _GEV_DATASETS)
def test_gev_reaches_the_maximum_of_three_r_packages(dataset):
    """No R implementation finds a more likely GEV, and the quantiles agree.

    The log-likelihood may fall short of the best of evd, extRemes and ismev by 1e-6
    (it lies above it on every sample, by up to 2.5e-6). The likelihood is flat along
    a ridge: on floods11 the three, within 3e-5 of one another, differ by up to 1.2 %
    in the quantiles, so those agree with the most likely R fit within 0.5 %
    (Hydrolog's differ by 0.17 % at most, at T = 1000 on floods11).
    """
    sample = SAMPLES[dataset]
    rows = [r for r in R_FITS if r["dataset"] == dataset and r["distribution"] == "gev"]
    best = max(rows, key=lambda row: float(row["loglik"]))
    shape, loc, scale = _r_parameters(best)

    result, log_likelihood = _fit("gev", sample)

    assert log_likelihood >= float(best["loglik"]) - 1e-6
    np.testing.assert_allclose(
        result.quantiles,
        genextreme.isf(1.0 / RETURN_PERIODS, shape, loc=loc, scale=scale),
        rtol=5e-3,
        atol=0.0,
    )


@pytest.mark.parametrize("row", _LMOMCO_REGULAR)
def test_pearson3_and_weibull_reach_the_maximum_of_lmomco(row):
    """Where lmomco's maximum is regular, Hydrolog's is at least as likely.

    Tolerances as for the GEV: 1e-6 of log-likelihood (Hydrolog's lies above
    lmomco's on every sample, by up to 1.2e-5) and 0.5 % of the quantiles (Hydrolog's
    differ by 0.05 % at most).
    """
    sample = SAMPLES[row["dataset"]]
    shape, loc, scale = _r_parameters(row)

    result, log_likelihood = _fit(row["distribution"], sample)

    assert log_likelihood >= float(row["loglik"]) - 1e-6
    np.testing.assert_allclose(
        result.quantiles,
        _SCIPY[row["distribution"]].isf(
            1.0 / RETURN_PERIODS, shape, loc=loc, scale=scale
        ),
        rtol=5e-3,
        atol=0.0,
    )


@pytest.mark.parametrize("row", _LMOMCO_SINGULAR)
def test_a_singular_maximum_of_lmomco_is_refused(row):
    """lmomco stops at the singularity, where the likelihood grows without limit.

    Its Pearson III of skewness 2.62 (floods11) and 2.50 (gev_c-0.1_n30) and its
    Weibull of shape 0.87 (floods11) put the lower bound at the smallest value, where
    their density is infinite (scipy's log-likelihood of that Weibull is infinite,
    lmomco reports 658): there is no maximum to report.
    """
    sample = SAMPLES[row["dataset"]]

    with pytest.raises(InvalidParameterError) as caught:
        _fit(row["distribution"], sample)

    assert caught.value.code == "validation_error"
    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "likelihood_has_a_maximum"
    assert caught.value.details["fit_method"] == "mle"


# --- the research's cases -------------------------------------------------------------


def test_port_pirie_is_coles_fit():
    """Coles (2001, sect. 3.4.1): the annual maximum sea levels at Port Pirie [m].

    Coles prints (mu, sigma, xi) = (3.87, 0.198, -0.050) and a log-likelihood of 4.34;
    the OpenTURNS 1.28 example of the same fit prints mu 3.875, sigma 0.198, xi -0.050,
    the log-likelihood 4.339056652316124 and the 10- and 100-year return levels 4.29617
    and 4.68814 m (case COLES-PORTPIRIE-GEV-ML). Tolerances: half a unit of the last
    printed digit of the parameters (CMP-6.1); 1e-5 of log-likelihood and 2e-4 of the
    return levels, the agreement of two independent optimisers on this optimum.
    """
    result, log_likelihood = _fit("gev", SAMPLES["portpirie"], np.array([10.0, 100.0]))

    parameters = result.parameters
    assert parameters["shape"] > 0.0  # c = -xi: an upper bound, a light tail
    assert -parameters["shape"] == pytest.approx(-0.050, abs=5e-4)
    assert parameters["loc"] == pytest.approx(3.875, abs=5e-4)
    assert parameters["scale"] == pytest.approx(0.198, abs=5e-4)
    assert log_likelihood == pytest.approx(4.339056652316124, abs=1e-5)
    np.testing.assert_allclose(result.quantiles, [4.29617, 4.68814], rtol=2e-4, atol=0)


def test_floods11_gev_is_the_maximum_of_r():
    """Hydrolog's own sample of 11 annual maxima [m3/s] (case FLOODS11-GEV-ML-FAILURE).

    Up to 0.8.1 scipy's ``fit`` stopped at c = -6.26 with the log-likelihood -61.547 and
    Q100 = 2.5e12, Q1000 = 4.7e18 m³/s. evd, extRemes and ismev agree on xi 0.428,
    loc 120.2, scale 26.7 and the log-likelihood -56.13304, and extRemes gives the
    quantiles below (printed to 0.001). Tolerances: 1e-5 of log-likelihood (its printed
    precision), 1 % of parameters and quantiles (the three R fits differ by up to 1.2 %
    at T = 1000). Pearson III and Weibull have no maximum here and are left out of the
    ranking, which they led with AIC 102.3 and 107.8 at their singularity.
    """
    sample = SAMPLES["floods11"]

    result, log_likelihood = _fit("gev", sample)

    parameters = result.parameters
    assert log_likelihood == pytest.approx(-56.13304, abs=1e-5)
    assert -parameters["shape"] == pytest.approx(0.428, rel=1e-2)
    assert parameters["loc"] == pytest.approx(120.2, rel=1e-2)
    assert parameters["scale"] == pytest.approx(26.7, rel=1e-2)
    extremes = [130.835, 176.449, 221.394, 280.422, 389.502, 505.015, 949.825, 1258.095]
    np.testing.assert_allclose(result.quantiles, extremes, rtol=1e-2, atol=0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ranked = FloodFrequencyAnalysis(sample).fit_all(fit_method="mle")
    assert list(ranked) == ["gev", "log_normal"]


def _zero_return_period(parameters: dict[str, float]) -> float:
    """1 / F(0) of the Fisher-Tippett distribution of minima, written out.

    F(x) = 1 - exp{-[1 + c (x - loc) / scale]^(1/c)} for c > 0 (lower bound
    loc - scale / c), the distribution of X when -X is scipy's GEV (c, -loc, scale).
    """
    c, loc, scale = parameters["shape"], parameters["loc"], parameters["scale"]
    return 1.0 / (1.0 - np.exp(-np.power(1.0 - c * loc / scale, 1.0 / c)))


def test_small_stream_low_flows_are_the_maximum_and_never_negative():
    """The case LOWFLOW-FT-ML-FAILURE-SMALL-STREAM: 20 annual minima of a small stream.

    Up to 0.8.1 the fit stopped at c = -0.718 with the log-likelihood 48.41 and gave
    Q10 = -0.0470 and Q100 = -0.586 m³/s. R's evd and extRemes on the negated minima:
    xi -0.1766 (c 0.1766), log-likelihood 54.537, Q10 0.017422, Q100 -0.001879 m³/s.
    The fit reaches below zero flow once in 77 years, so Q100 is left out (null) with
    the warning ``negative_quantiles``; for a variable without that limit (a stage) it
    stays. Tolerances: 1 % of the shape and of Q10, as evd and extRemes agree (case);
    5e-4 of log-likelihood, half a unit of R's print; Q100 within 1e-4 m³/s, the
    rounding of the minima (relative to its own size it is 5 %).
    """
    periods = np.array([10.0, 100.0])
    with pytest.warns(NegativeQuantiles) as caught:
        result = fit_fisher_tippett_minima(SMALL_STREAM, periods)

    parameters = result.parameters
    log_likelihood = _log_likelihood(
        "gev",
        -SMALL_STREAM,
        parameters["shape"],
        -parameters["loc"],
        parameters["scale"],
    )
    assert log_likelihood == pytest.approx(54.537, abs=5e-4)
    assert parameters["shape"] == pytest.approx(0.1766, rel=1e-2)
    assert result.quantiles[0] == pytest.approx(0.017422, rel=1e-2)
    assert np.isnan(result.quantiles[1])
    [warning] = [w.message for w in caught if isinstance(w.message, NegativeQuantiles)]
    assert warning.details["return_periods"] == [100.0]
    # between the periods of the positive and of the negative quantile; to rounding
    assert 10.0 < warning.details["zero_return_period"] < 100.0
    assert warning.details["zero_return_period"] == pytest.approx(
        _zero_return_period(parameters), rel=1e-12
    )

    stage = fit_fisher_tippett_minima(SMALL_STREAM, periods, discharge=False)
    assert stage.parameters == parameters
    assert stage.quantiles[0] == result.quantiles[0]
    assert stage.quantiles[1] == pytest.approx(-0.001879, abs=1e-4)


def _half_year_file(path: Path, minima: NDArray[np.float64]) -> Path:
    """A half-year file whose summer minima of Q and of H are ``minima``, from 2001."""
    rows = ["year,period,Q_min,Q_mean,Q_max,H_min,H_mean,H_max"]
    for year, low in enumerate(minima.tolist(), start=2001):
        winter = f"{low + 0.1:.4f},{low + 1:.4f},{low + 5:.4f}"
        summer = f"{low:.4f},{low + 1:.4f},{low + 5:.4f}"
        rows += [f"{year},winter,{winter},{winter}", f"{year},summer,{summer},{summer}"]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_stats_low_flow_leaves_out_negative_discharges_not_stages(tmp_path):
    """``stats low-flow`` nulls the negative quantiles of Q only.

    The same minima as Q give the null and the notice, as H (a stage, whose zero is the
    gauge's) the negative quantile itself, each as the library gives it (to 1e-12, the
    rounding of the JSON round trip).
    """
    path = _half_year_file(tmp_path / "half_years.csv", SMALL_STREAM)
    periods = np.array([10.0, 100.0])
    outputs = {
        parameter: run_command(
            "stats low-flow",
            {
                "half_year_file": str(path),
                "parameter": parameter,
                "return_periods": [10, 100],
            },
        ).to_dict()
        for parameter in ("Q", "H")
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # negative_quantiles of the call for Q
        library = {
            "Q": fit_fisher_tippett_minima(SMALL_STREAM, periods),
            "H": fit_fisher_tippett_minima(SMALL_STREAM, periods, discharge=False),
        }

    discharge = outputs["Q"]["result"]["fisher_tippett"]["quantiles"]
    assert discharge == [pytest.approx(library["Q"].quantiles[0], rel=1e-12), None]
    [notice] = outputs["Q"]["notices"]
    assert (notice["code"], notice["level"]) == ("negative_quantiles", "warning")
    assert notice["details"]["return_periods"] == [100.0]
    stage = outputs["H"]["result"]["fisher_tippett"]["quantiles"]
    assert outputs["H"]["notices"] == []
    assert stage == pytest.approx(library["H"].quantiles.tolist(), rel=1e-12)
    assert stage[1] < 0.0


# --- preconditions ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("distribution", "count", "minimum"),
    [("gev", 3, 4), ("pearson3", 3, 4), ("weibull", 3, 4), ("log_normal", 2, 3)],
)
def test_maximum_likelihood_needs_more_values_than_parameters(
    distribution, count, minimum
):
    """Up to 0.8.1 three maxima [95, 150, 290] gave a GEV with Q100 = 1.7e21 m³/s."""
    with pytest.raises(InvalidParameterError) as caught:
        _fit(distribution, np.array([95.0, 150.0, 290.0])[:count])

    details = caught.value.details
    assert (details["reason"], details["constraint"]) == (
        "precondition_failed",
        "enough_values",
    )
    assert (details["distribution"], details["fit_method"]) == (distribution, "mle")
    assert f">= {minimum}" in details["text"]


@pytest.mark.parametrize("distribution", ["log_normal", "gev", "pearson3", "weibull"])
def test_maximum_likelihood_needs_values_not_all_equal(distribution):
    """Up to 0.8.1 [100] * 4 gave a GEV of scale 1e-24 and a Weibull Q100 of 7e30."""
    with pytest.raises(InvalidParameterError) as caught:
        _fit(distribution, np.full(4, 100.0))

    assert caught.value.details["constraint"] == "values_not_all_equal"


def test_the_log_normal_by_maximum_likelihood_needs_values_above_zero():
    with pytest.raises(InvalidParameterError) as caught:
        _fit("log_normal", np.array([0.0, 95.0, 150.0, 290.0]))

    assert caught.value.details["constraint"] == "positive_values"


def test_stats_flood_frequency_fits_what_three_maxima_allow():
    """Three maxima fit the two-parameter log-normal only; the others are named."""
    output = run_command(
        "stats flood-frequency",
        {"values": [95.0, 150.0, 290.0], "fit_method": "mle", "return_periods": [100]},
    ).to_dict()

    result = output["result"]
    assert [d["distribution_name"] for d in result["distributions"]] == ["log_normal"]
    assert result["best_distribution"] == "log_normal"
    # the closed form, to rounding: exp(mean of ln x + z(0.99) · sd of ln x, divisor n)
    logs = np.log([95.0, 150.0, 290.0])
    q100 = np.exp(logs.mean() + norm.ppf(0.99) * logs.std())
    assert result["distributions"][0]["quantiles"] == [pytest.approx(q100, rel=1e-9)]
    left_out = {
        notice["details"]["distribution"]: notice["details"]["reason"]
        for notice in output["notices"]
        if notice["code"] == "distribution_left_out"
    }
    assert left_out == dict.fromkeys(("gev", "pearson3", "weibull"), "too_few_values")


def test_stats_flood_frequency_refuses_constant_maxima_by_maximum_likelihood():
    with pytest.raises(CalculationError) as caught:
        run_command(
            "stats flood-frequency", {"values": [100.0] * 4, "fit_method": "mle"}
        )

    assert caught.value.details == {
        "fit_method": "mle",
        "reasons": dict.fromkeys(
            ("log_normal", "gev", "pearson3", "weibull"), "constant_values"
        ),
    }


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_a_value_that_is_not_finite_is_refused(bad):
    """Infinity gave a NaN L-skewness or a raw scipy error up to 0.8.1."""
    values = np.array([95.0, 102.0, bad, 118.0, 125.0])

    with pytest.raises(InvalidParameterError) as flood:
        FloodFrequencyAnalysis(values)
    with pytest.raises(InvalidParameterError) as low:
        fit_fisher_tippett_minima(values)

    assert flood.value.details == {"option": "annual_maxima", "reason": "not_finite"}
    assert low.value.details == {"option": "minima", "reason": "not_finite"}


def test_low_flow_minima_all_equal_are_refused():
    """A stream dry every year: its minima are all 0, with no distribution to fit.

    Up to 0.8.1 scipy's ``fit`` returned a scale of 5e-23 and quantiles of -2e-21.
    """
    with pytest.raises(InvalidParameterError) as caught:
        fit_fisher_tippett_minima(np.zeros(12))

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "values_not_all_equal"


# --- seeded samples against an independent search -----------------------------------

# Powell's method on the raw values: another algorithm, another parametrisation and
# another start than Hydrolog's Nelder-Mead on the standardised sample.
_POWELL = {"xtol": 1e-8, "ftol": 1e-10, "maxiter": 50_000, "maxfev": 100_000}


def _powell_gev(sample: NDArray[np.float64]) -> tuple[float, float]:
    """``(c, log-likelihood)`` of the GEV's maximum likelihood by Powell's method.

    From the L-moments' estimate with its shape held below 0.9 and its location moved
    so that the sample lies 5 % of its standard deviation inside the bound; the shape
    stays below 1, beyond which the likelihood is unbounded.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        start = FloodFrequencyAnalysis(sample).fit_gev(fit_method="l_moments")
    c, loc, scale = (start.parameters[key] for key in ("shape", "loc", "scale"))
    c = min(c, 0.9)
    margin = 0.05 * float(np.std(sample))
    if c > 0.0:  # upper bound loc + scale / c
        loc = max(loc, float(sample.max()) + margin - scale / c)
    elif c < 0.0:  # lower bound loc + scale / c
        loc = min(loc, float(sample.min()) - margin - scale / c)

    def minus_log_likelihood(point: NDArray[np.float64]) -> float:
        if point[0] >= 1.0:
            return 1e300
        with np.errstate(all="ignore"):
            value = -_log_likelihood(
                "gev", sample, point[0], point[1], np.exp(point[2])
            )
        return value if np.isfinite(value) else 1e300

    found = minimize(
        minus_log_likelihood,
        np.array([c, loc, np.log(scale)]),
        method="Powell",
        options=_POWELL,
    )
    return float(found.x[0]), -float(found.fun)


@pytest.mark.slow
def test_seeded_gev_samples_reach_the_maximum_of_an_independent_search():
    """30 samples of 30 GEV maxima (c -0.1, loc 1000, scale 400 m³/s).

    Of such samples scipy's ``fit`` stopped short of the maximum in 72 of 100 (Q100 up
    to 1.2e19 m³/s). Every one now fits, at least as likely as Powell's maximum
    (tolerance 1e-6 of log-likelihood; the gaps are below 1e-12).
    """
    rng = np.random.default_rng(20261118)
    short = []
    for draw in range(30):
        sample = genextreme.rvs(
            -0.1, loc=1000.0, scale=400.0, size=30, random_state=rng
        )
        _, log_likelihood = _fit("gev", sample)
        _, powell = _powell_gev(sample)
        if log_likelihood < powell - 1e-6:
            short.append((draw, powell - log_likelihood))
    assert short == []


@pytest.mark.slow
def test_seeded_low_flow_samples_reach_the_maximum_or_refuse_the_limit():
    """30 samples of 20 minima of a small stream (Weibull 1.5, loc 0, scale 0.05 m³/s).

    A fit is at least as likely as Powell's maximum of the negated minima (1e-6 of
    log-likelihood); a refusal (``unbounded_likelihood``: six of the 30) is where
    Powell's search, too, runs to the limit c = 1 (within Hydrolog's 1e-3 of it).
    """
    rng = np.random.default_rng(20261118)
    short = []
    inconsistent = []
    refused = 0
    for draw in range(30):
        minima = weibull_min.rvs(1.5, loc=0.0, scale=0.05, size=20, random_state=rng)
        c, powell = _powell_gev(-minima)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # negative_quantiles
            try:
                result = fit_fisher_tippett_minima(minima)
            except InvalidParameterError as exc:
                assert exc.details["constraint"] == "likelihood_has_a_maximum"
                refused += 1
                if c < 1.0 - 1e-3:
                    inconsistent.append((draw, c))
                continue
        parameters = result.parameters
        log_likelihood = _log_likelihood(
            "gev", -minima, parameters["shape"], -parameters["loc"], parameters["scale"]
        )
        if log_likelihood < powell - 1e-6:
            short.append((draw, powell - log_likelihood))
    assert (short, inconsistent) == ([], [])
    assert 0 < refused < 30
