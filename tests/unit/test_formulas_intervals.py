"""The intervals of the quantiles against their specs (Nogat CMP §6, CMP-6.11).

Range, type and property tests are generated from the specs
``quantile_interval_bootstrap`` and ``quantile_interval_delta`` (CMP-6.5), with the
generated properties of an interval, lower <= upper and the interval of a smaller level
inside that of a larger one (``assert_interval_properties``, CMP-6.11); the reference
cases of KZGW (2017), the frozen oracles of R and the exact oracles have their own
modules (``test_interval_reference_cases.py``, ``test_interval_oracles.py``), and the
simulated coverage runs nightly (``test_coverage_quantiles.py``). The tests below pin
what the analyses do with the intervals: the samples shared with the critical values
of A², the empirical quantile of type 6, the levels in the order asked and the notice
``interval_not_computed`` of each reason.
"""

import math
import warnings

import numpy as np
import pytest
from hypothesis import given
from scipy.stats import genextreme, weibull_min

from hydrolog._formulas import ERRORS
from hydrolog._warnings import IntervalNotComputed
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    assert_interval_properties,
    assert_limits,
    assert_properties,
    assert_property_contract,
    assert_within,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.statistics import (
    FloodFrequencyAnalysis,
    fit_fisher_tippett_minima,
)
from hydrolog.statistics.frequency import (
    _DISTRIBUTIONS,
    _POLANA,
    _a_squared,
    _by_l_moments,
    _within_l_moments,
    fit_l_moments,
    fit_maximum_likelihood,
)
from hydrolog.statistics.high_flows import _ad_critical_values
from hydrolog.statistics.intervals import (
    QUANTILE_INTERVAL_BOOTSTRAP,
    QUANTILE_INTERVAL_DELTA,
    confidence_levels,
    quantile_interval_bootstrap,
    quantile_interval_delta,
)
from hydrolog.statistics.low_flows import _STATION_223207

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (QUANTILE_INTERVAL_BOOTSTRAP, quantile_interval_bootstrap),
    (QUANTILE_INTERVAL_DELTA, quantile_interval_delta),
)
NAMES = [spec.name for spec, _ in FAMILY]
POLANA = np.array(_POLANA)
PERIODS = [2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0]
LEVELS = (0.95, 0.68)


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=NAMES)
def test_limits(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


def _interval_properties(spec: FormulaSpec, function, inputs: dict) -> None:
    """Assert lower <= upper and the nesting of the levels at accepted inputs."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            function(**inputs)
    except InvalidParameterError:
        return
    fixed = {k: v for k, v in inputs.items() if k != "confidence_levels"}

    def interval(_sample: np.ndarray, levels: tuple[float, ...]) -> list:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            found = function(**fixed, confidence_levels=list(levels))
        return list(zip(found.lower, found.upper, strict=True))

    assert_interval_properties(interval, np.zeros(1), (0.99, 0.95, 0.68, 0.5))


@given(inputs=strategies(QUANTILE_INTERVAL_BOOTSTRAP))
def test_bootstrap_properties(inputs):
    function = as_standard(quantile_interval_bootstrap)
    assert_property_contract(QUANTILE_INTERVAL_BOOTSTRAP, function, inputs, ERRORS)
    assert_properties(QUANTILE_INTERVAL_BOOTSTRAP, function, inputs, ERRORS)
    _interval_properties(
        QUANTILE_INTERVAL_BOOTSTRAP, quantile_interval_bootstrap, inputs
    )


@given(inputs=strategies(QUANTILE_INTERVAL_DELTA))
def test_delta_properties(inputs):
    function = as_standard(quantile_interval_delta)
    assert_property_contract(QUANTILE_INTERVAL_DELTA, function, inputs, ERRORS)
    assert_properties(QUANTILE_INTERVAL_DELTA, function, inputs, ERRORS)
    _interval_properties(QUANTILE_INTERVAL_DELTA, quantile_interval_delta, inputs)


# --- the bootstrap: the samples of the critical values of A², type 6 --------------


def _refit_quantiles(name: str, parameters, size: int) -> tuple[np.ndarray, int]:
    """The quantiles of the refits of the bootstrap, drawn and refitted by hand."""
    rng = np.random.default_rng(20261118)
    samples = np.sort(
        _DISTRIBUTIONS[name].rvs(*parameters, size=(999, size), random_state=rng),
        axis=1,
    )
    kept = [sample for sample in samples if _within_l_moments(name, sample)]
    rows = [
        _DISTRIBUTIONS[name].isf(1.0 / np.array(PERIODS), *_by_l_moments(name, sample))
        for sample in kept
    ]
    return np.sort(np.array(rows), axis=0), len(kept)


@pytest.mark.parametrize("name", ["log_normal", "gev", "pearson3", "weibull"])
def test_the_bootstrap_bounds_are_the_order_statistics_of_type_6(name):
    parameters = fit_l_moments(POLANA, name)
    ordered, kept = _refit_quantiles(name, parameters, POLANA.size)
    found = quantile_interval_bootstrap(
        name, *parameters, POLANA.size, PERIODS, LEVELS, "stage"
    )
    assert found.samples == kept == 999
    # (K + 1)(1 - c) / 2 of K = 999: the 25th refit from each end at 0.95 and the
    # 160th at 0.68 (Efron and Tibshirani's ((B + 1) alpha)th value)
    assert_within(
        found.lower,
        [ordered[24], ordered[159]],
        rel=1e-14,
        abs=1e-12,
        reason="the same draws and refits; type 6 at an integer position is the "
        "order statistic itself",
    )
    assert_within(
        found.upper,
        [ordered[974], ordered[839]],
        rel=1e-14,
        abs=1e-12,
        reason="the same draws and refits; type 6 at an integer position is the "
        "order statistic itself",
    )


def test_the_bootstrap_reads_the_samples_of_the_critical_values_of_a_squared():
    name, size = "gev", POLANA.size
    parameters = tuple(fit_l_moments(POLANA, name))
    rng = np.random.default_rng(20261118)
    samples = np.sort(
        _DISTRIBUTIONS[name].rvs(*parameters, size=(999, size), random_state=rng),
        axis=1,
    )
    refits = np.array([_by_l_moments(name, sample) for sample in samples])
    statistics = _a_squared(
        _DISTRIBUTIONS[name].cdf(
            samples, refits[:, 0, None], refits[:, 1, None], refits[:, 2, None]
        )
    )
    expected = {
        label: float(np.quantile(statistics, 1.0 - level))
        for label, level in {"15%": 0.15, "5%": 0.05, "1%": 0.01}.items()
    }
    found = _ad_critical_values(name, parameters, size)
    assert found is not None
    for label, value in expected.items():
        assert_within(
            found[label],
            value,
            rel=1e-14,
            abs=0.0,
            reason="ADR-0048's bootstrap drawn again by hand: the samples, seed and "
            "refits the interval reads are the same",
        )
    result = FloodFrequencyAnalysis(POLANA, confidence_level=0.95).fit_gev()
    assert result.ad_critical_values == found
    [interval] = result.intervals
    assert interval.ci_samples == 999


def test_too_few_refits_give_no_interval_and_say_why():
    plotted = weibull_min.ppf(np.arange(1, 31) / 31, 5.0) * 10.0 + 5.0
    parameters = fit_l_moments(plotted, "weibull")
    with pytest.raises(InvalidParameterError) as refused:
        quantile_interval_bootstrap(
            "weibull", *parameters, plotted.size, PERIODS, LEVELS, "discharge"
        )
    assert refused.value.details["constraint"] == "enough_refits"
    with pytest.warns(IntervalNotComputed) as caught:
        result = FloodFrequencyAnalysis(plotted, confidence_level=LEVELS).fit_weibull()
    [notice] = [w.message for w in caught if isinstance(w.message, IntervalNotComputed)]
    assert notice.details["reason"] == "bootstrap_failures"
    assert notice.details["confidence_levels"] == list(LEVELS)
    assert [e.to_dict() for e in result.intervals] == [
        {
            "confidence_level": c,
            "ci_method": None,
            "ci_lower": None,
            "ci_upper": None,
            "ci_samples": None,
        }
        for c in LEVELS
    ]


# --- the analyses: methods, levels and notices --------------------------------------


@pytest.mark.parametrize("method", ["moments", "least_squares"])
def test_the_moments_and_least_squares_have_no_interval(method):
    with pytest.warns(IntervalNotComputed) as caught:
        result = FloodFrequencyAnalysis(POLANA).fit_gev(fit_method=method)
    [notice] = [w.message for w in caught if isinstance(w.message, IntervalNotComputed)]
    assert notice.details == {
        "reason": "fit_method",
        "confidence_levels": [0.95],
        "distribution": "gev",
        "fit_method": method,
        "return_periods": None,
        "complete_years": None,
        "required_years": None,
    }
    assert result.intervals[0].ci_method is None


def test_levels_come_in_the_order_asked_from_one_computation():
    analysis = FloodFrequencyAnalysis(POLANA, confidence_level=[0.68, 0.95, 0.9])
    result = analysis.fit_pearson3()
    assert [e.confidence_level for e in result.intervals] == [0.68, 0.95, 0.9]
    assert {e.ci_method for e in result.intervals} == {"parametric_bootstrap"}
    single = FloodFrequencyAnalysis(POLANA, confidence_level=0.95).fit_pearson3()
    assert_within(
        result.intervals[1].ci_upper,
        single.intervals[0].ci_upper,
        abs=0.0,
        reason="a level reads the same refits whatever the other levels asked",
    )


@pytest.mark.parametrize(
    ("value", "reason"),
    [(1.0, "range"), ([0.95, 0.95], "duplicate_level"), ([], "empty"), (True, "type")],
)
def test_a_level_outside_the_open_unit_interval_or_twice_is_refused(value, reason):
    with pytest.raises(InvalidParameterError) as refused:
        FloodFrequencyAnalysis(POLANA, confidence_level=value)
    assert refused.value.details["reason"] == reason
    assert refused.value.details["option"] == "confidence_level"
    with pytest.raises(InvalidParameterError):
        fit_fisher_tippett_minima(np.array(_STATION_223207), confidence_level=value)
    assert confidence_levels((0.5,)) == (0.5,)


def test_a_bound_of_a_discharge_below_zero_is_left_out_with_its_periods():
    # the GEV of the Polana maxima by maximum likelihood has a heavy upper tail
    # (c = -0.41): its symmetric delta interval reaches below 0 at long T
    with pytest.warns(IntervalNotComputed) as caught:
        result = FloodFrequencyAnalysis(POLANA, confidence_level=LEVELS).fit_gev(
            fit_method="mle"
        )
    [notice] = [w.message for w in caught if isinstance(w.message, IntervalNotComputed)]
    assert notice.details["reason"] == "below_physical_range"
    assert notice.details["confidence_levels"] == [0.95]
    assert notice.details["return_periods"] == [100.0, 500.0, 1000.0]
    lower = result.intervals[0].ci_lower
    assert lower is not None
    assert np.isnan(lower[-3:]).all() and np.isfinite(lower[:-3]).all()
    assert np.isfinite(result.intervals[0].ci_upper).all()
    stage = FloodFrequencyAnalysis(
        POLANA, confidence_level=LEVELS, discharge=False
    ).fit_gev(fit_method="mle")
    kept = stage.intervals[0].ci_lower
    assert kept is not None and (kept[-3:] < 0.0).all()


def test_a_gev_whose_likelihood_is_not_regular_has_no_delta_interval():
    plotted = genextreme.ppf(np.arange(1, 31) / 31, 0.6, loc=10.0, scale=3.0)
    shape = fit_maximum_likelihood(plotted, "gev").shape
    assert 0.5 <= shape < 1.0
    with pytest.warns(IntervalNotComputed) as caught:
        result = FloodFrequencyAnalysis(plotted).fit_gev(fit_method="mle")
    [notice] = [w.message for w in caught if isinstance(w.message, IntervalNotComputed)]
    assert notice.details["reason"] == "nonregular_fit"
    assert notice.details["fit_method"] == "mle"
    assert result.intervals[0].ci_method is None


def test_the_low_flow_interval_is_the_delta_of_the_negated_minima():
    minima = np.array(_STATION_223207)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = fit_fisher_tippett_minima(
            minima, PERIODS, discharge=False, confidence_level=LEVELS
        )
    shape, loc, scale = (result.parameters[k] for k in ("shape", "loc", "scale"))
    negated = quantile_interval_delta(
        -minima, "gev", shape, -loc, scale, PERIODS, LEVELS, "stage", "maxima"
    )
    for row, entry in enumerate(result.intervals):
        assert entry.ci_method == "delta"
        assert_within(
            entry.ci_lower,
            -negated.upper[row],
            rel=1e-15,
            abs=1e-12,
            reason="the bounds of the minima are those of the negated minima, "
            "negated and swapped",
        )
        assert_within(
            entry.ci_upper,
            -negated.lower[row],
            rel=1e-15,
            abs=1e-12,
            reason="the bounds of the minima are those of the negated minima, "
            "negated and swapped",
        )


def test_a_low_flow_bound_below_zero_is_left_out():
    with pytest.warns(IntervalNotComputed) as caught:
        result = fit_fisher_tippett_minima(
            np.array(_STATION_223207), PERIODS, confidence_level=LEVELS
        )
    notices = [w.message for w in caught if isinstance(w.message, IntervalNotComputed)]
    assert [n.details["reason"] for n in notices] == ["below_physical_range"]
    assert notices[0].details["distribution"] == "fisher_tippett"
    lower = result.intervals[0].ci_lower
    assert lower is not None and np.isnan(lower[4:]).all()


def test_the_weibull_interval_is_eq_3_57_of_the_quantile_above_its_bound():
    shape, loc, scale = 1.2, 5.0, 30.0
    found = quantile_interval_delta(
        POLANA, "weibull", shape, loc, scale, PERIODS, [0.68], "stage", "maxima"
    )
    periods = np.array(PERIODS)
    excess = scale * np.log(periods) ** (1.0 / shape)
    reduced = np.log(np.log(periods))
    sigma = (
        excess
        / (shape * math.sqrt(POLANA.size))
        * np.sqrt(1.0 + (1.0 - np.euler_gamma - reduced) ** 2 / (math.pi**2 / 6.0))
    )
    z = 0.994457883209753  # Phi^-1(0.84)
    assert_within(
        found.upper[0],
        loc + excess + z * sigma,
        rel=1e-13,
        abs=1e-12,
        reason="KZGW's eq. 3.57 written out with numpy; z of c = 0.68 to 15 digits",
    )


def test_the_json_of_a_fit_carries_its_intervals_with_null_bounds():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = FloodFrequencyAnalysis(POLANA, confidence_level=LEVELS).fit_gev(
            fit_method="mle"
        )
    entries = result.to_dict()["intervals"]
    assert [list(entry) for entry in entries] == [
        ["confidence_level", "ci_method", "ci_lower", "ci_upper", "ci_samples"]
    ] * 2
    assert entries[0]["ci_lower"][-1] is None
    assert entries[1]["ci_samples"] is None
