"""Tests for flood frequency analysis."""

import warnings

import numpy as np
import pytest
from scipy.stats import genextreme, lognorm, pearson3, skew, weibull_min

# Known parameters in scipy's parametrisation of each distribution.
_DISTRIBUTIONS = {
    "log_normal": (lognorm, (0.5, 0.0, 50.0)),
    "gev": (genextreme, (-0.1, 100.0, 30.0)),
    "pearson3": (pearson3, (1.0, 100.0, 30.0)),
    "weibull": (weibull_min, (1.5, 20.0, 50.0)),
}
# Fitted by all four distributions and both methods; by the L-moments the lower bound
# of Pearson III and of Weibull lies above its smallest value.
_FLOODS = np.array(
    [95.0, 102.0, 110.0, 118.0, 125.0, 133.0, 140.0, 152.0, 170.0, 215.0, 290.0]
)


def _fit(analysis, distribution, fit_method):
    return getattr(analysis, f"fit_{distribution}")(fit_method=fit_method)


def _ranked(analysis, fit_method):
    return list(analysis.fit_all(fit_method=fit_method).values())


class TestFloodFrequencyAnalysis:
    @pytest.fixture
    def synthetic_gev_data(self):
        rng = np.random.default_rng(42)
        return genextreme.rvs(c=-0.1, loc=100, scale=30, size=50, random_state=rng)

    @pytest.fixture
    def synthetic_lognorm_data(self):
        rng = np.random.default_rng(42)
        return lognorm.rvs(s=0.5, loc=0, scale=50, size=50, random_state=rng)

    def test_fit_gev_returns_result(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        result = ffa.fit_gev()
        assert result.distribution_name == "gev"
        assert len(result.quantiles) == len(result.return_periods)
        assert np.all(np.diff(result.quantiles) > 0)

    def test_fit_log_normal_returns_result(self, synthetic_lognorm_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_lognorm_data)
        result = ffa.fit_log_normal()
        assert result.distribution_name == "log_normal"
        assert "shape" in result.parameters

    def test_fit_pearson3_returns_result(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        result = ffa.fit_pearson3()
        assert result.distribution_name == "pearson3"

    def test_fit_weibull_returns_result(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        result = ffa.fit_weibull()
        assert result.distribution_name == "weibull"

    def test_ks_valid_is_false_with_warning(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = ffa.fit_gev()
            assert result.ks_valid is False
            ks_warnings = [x for x in w if "Kolmogorov-Smirnov" in str(x.message)]
            assert len(ks_warnings) >= 1

    def test_anderson_darling_statistic_present(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        result = ffa.fit_gev()
        assert result.ad_statistic >= 0.0
        assert isinstance(result.ad_critical_values, dict)

    def test_aic_present(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        result = ffa.fit_gev()
        assert isinstance(result.aic, float)

    def test_fit_all_returns_all_distributions(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        results = ffa.fit_all()
        assert "gev" in results
        assert "log_normal" in results
        assert "pearson3" in results
        assert "weibull" in results

    def test_fit_all_sorted_by_aic(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        results = ffa.fit_all()
        aics = [r.aic for r in results.values()]
        assert aics == sorted(aics)

    def test_empirical_frequency_weibull(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        emp = ffa.empirical_frequency(method="weibull")
        n = len(synthetic_gev_data)
        assert len(emp.values_sorted) == n
        assert abs(emp.exceedance_prob[0] - 1 / (n + 1)) < 0.001

    def test_custom_return_periods(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(
            synthetic_gev_data,
            return_periods=np.array([10.0, 100.0, 1000.0]),
        )
        result = ffa.fit_gev()
        assert len(result.return_periods) == 3
        assert len(result.quantiles) == 3

    @pytest.mark.parametrize(
        "fit_method", ["mle", "moments", "l_moments", "least_squares"]
    )
    @pytest.mark.parametrize("distribution", list(_DISTRIBUTIONS))
    def test_densities_are_the_pdf_at_the_quantiles(self, distribution, fit_method):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        analysis = FloodFrequencyAnalysis(
            _FLOODS, return_periods=np.array([1.01, 2.0, 10.0, 100.0, 1000.0])
        )
        result = _fit(analysis, distribution, fit_method)
        dist, _ = _DISTRIBUTIONS[distribution]

        expected = dist.pdf(result.quantiles, *result.parameters.values())
        np.testing.assert_allclose(result.densities, expected, rtol=1e-12)
        assert np.all(result.densities > 0.0)

    def test_empirical_frequency_hazen(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        emp = ffa.empirical_frequency(method="hazen")
        n = len(synthetic_gev_data)
        # Hazen: P_i = (i - 0.5) / n
        assert abs(emp.exceedance_prob[0] - 0.5 / n) < 0.001

    def test_empirical_frequency_cunnane(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        emp = ffa.empirical_frequency(method="cunnane")
        n = len(synthetic_gev_data)
        # Cunnane: P_i = (i - 0.4) / (n + 0.2)
        assert abs(emp.exceedance_prob[0] - 0.6 / (n + 0.2)) < 0.001

    def test_empirical_frequency_invalid_method_raises(self, synthetic_gev_data):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        with pytest.raises(InvalidParameterError):
            ffa.empirical_frequency(method="invalid")

    def test_empty_data_raises(self):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        with pytest.raises(InvalidParameterError):
            FloodFrequencyAnalysis(np.array([]))

    def test_nan_in_data_raises(self):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        with pytest.raises(InvalidParameterError):
            FloodFrequencyAnalysis(np.array([1.0, np.nan, 3.0]))

    def test_small_sample_kzgw_warning(self):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            FloodFrequencyAnalysis(np.arange(1.0, 21.0))
            kzgw_warnings = [x for x in w if "KZGW" in str(x.message)]
            assert len(kzgw_warnings) >= 1


class TestFitMethods:
    @pytest.mark.parametrize("fit_method", ["moments", "l_moments", "least_squares"])
    @pytest.mark.parametrize("distribution", list(_DISTRIBUTIONS))
    def test_recovers_the_parameters_of_a_large_sample(self, distribution, fit_method):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        dist, parameters = _DISTRIBUTIONS[distribution]
        # a synthetic sample of the exact distribution: its quantiles at the middles
        # of n equal intervals of probability
        n = 20_000
        sample = dist.ppf((np.arange(n) + 0.5) / n, *parameters)

        result = _fit(FloodFrequencyAnalysis(sample), distribution, fit_method)

        assert tuple(result.parameters.values()) == pytest.approx(
            parameters, rel=0.01, abs=0.01
        )

    def test_sample_l_moments_of_a_case_checked_by_hand(self):
        from hydrolog.statistics.high_flows import _sample_l_moments

        # 1, 2, 3, 4, 10: l1 is the mean, 4; l2 is half the mean difference of the
        # 10 pairs, 40 / (2 * 10) = 2; l3 is the mean of (x_k - 2 x_j + x_i) / 3 over
        # the 10 ordered triples, 30 / (3 * 10) = 1; t3 = l3 / l2 = 0.5
        l1, l2, t3 = _sample_l_moments(np.array([4.0, 10.0, 1.0, 3.0, 2.0]))

        assert (l1, l2, t3) == pytest.approx((4.0, 2.0, 0.5))

    @pytest.mark.parametrize("distribution", list(_DISTRIBUTIONS))
    def test_moments_are_the_unbiased_moments_of_the_sample(self, distribution):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        result = _fit(FloodFrequencyAnalysis(_FLOODS), distribution, "moments")
        dist = _DISTRIBUTIONS[distribution][0]
        mean, variance, skewness = dist.stats(
            *result.parameters.values(), moments="mvs"
        )

        assert float(mean) == pytest.approx(_FLOODS.mean())
        assert float(variance) == pytest.approx(_FLOODS.var(ddof=1))
        if distribution != "log_normal":  # two parameters: the mean and the variance
            assert float(skewness) == pytest.approx(skew(_FLOODS, bias=False))

    @pytest.mark.parametrize("distribution", list(_DISTRIBUTIONS))
    def test_least_squares_bring_the_quantiles_closer_than_the_moments(
        self, distribution
    ):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        analysis = FloodFrequencyAnalysis(_FLOODS)
        dist = _DISTRIBUTIONS[distribution][0]
        # the Weibull plotting positions of the ascending sample
        probabilities = np.arange(1, _FLOODS.size + 1) / (_FLOODS.size + 1)

        def squares(fit_method):
            fitted = _fit(analysis, distribution, fit_method).parameters.values()
            quantiles = dist.ppf(probabilities, *fitted)
            return np.sum((np.sort(_FLOODS) - quantiles) ** 2)

        assert squares("least_squares") < squares("moments")

    def test_a_fit_without_density_at_an_annual_maximum_ranks_last(self):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ranked = FloodFrequencyAnalysis(_FLOODS).fit_all(fit_method="l_moments")

        assert list(ranked)[2:] == ["pearson3", "weibull"]
        assert all(np.isfinite(ranked[name].aic) for name in list(ranked)[:2])
        for name, dist in (("pearson3", pearson3), ("weibull", weibull_min)):
            result = ranked[name]
            assert result.aic == np.inf
            parameters = result.parameters.values()
            assert dist.logpdf(_FLOODS.min(), *parameters) == -np.inf
            assert np.all(np.isfinite(result.quantiles))

    @pytest.mark.parametrize(
        ("distribution", "fit_method", "sample", "reason"),
        [
            ("weibull", "moments", [0.0, *[10.0] * 8, 10.5], "out_of_range"),
            ("weibull", "l_moments", [0.0, *[10.0] * 8, 10.5], "out_of_range"),
            (
                "weibull",
                "least_squares",
                [0.0, *[10.0] * 8, 10.5],
                "out_of_range",
            ),
            ("log_normal", "l_moments", [0.0, 5.0, 6.0, 7.0], "non_positive_values"),
            ("gev", "moments", [5.0, 5.0, 5.0, 5.0], "constant_values"),
            ("pearson3", "l_moments", [1.0, 2.0], "too_few_values"),
        ],
    )
    def test_no_parameters_is_a_calculation_error(
        self, distribution, fit_method, sample, reason
    ):
        from hydrolog.exceptions import CalculationError
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        analysis = FloodFrequencyAnalysis(np.array(sample))

        with pytest.raises(CalculationError) as caught:
            _fit(analysis, distribution, fit_method)
        assert caught.value.details["reason"] == reason
        assert caught.value.details["distribution"] == distribution
        assert caught.value.details["fit_method"] == fit_method

    def test_unknown_fit_method_raises(self):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        analysis = FloodFrequencyAnalysis(_FLOODS)

        with pytest.raises(InvalidParameterError):
            analysis.fit_gev(fit_method="median")


class TestEveryFitMethod:
    """``fit_all(fit_method="all")``: each distribution by each method."""

    def test_fits_each_distribution_by_each_method(self):
        from hydrolog.statistics.high_flows import FIT_METHODS, FloodFrequencyAnalysis

        ranked = FloodFrequencyAnalysis(_FLOODS).fit_all(fit_method="all")

        assert len(ranked) == 16
        assert set(ranked) == {
            f"{distribution}/{method}"
            for distribution in _DISTRIBUTIONS
            for method in FIT_METHODS
        }

    def test_each_item_is_the_fit_of_its_own_method(self):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ranked = FloodFrequencyAnalysis(_FLOODS).fit_all(fit_method="all")

        for key, result in ranked.items():
            assert key == f"{result.distribution_name}/{result.fit_method}"
            single = _fit(
                FloodFrequencyAnalysis(_FLOODS),
                result.distribution_name,
                result.fit_method,
            )
            assert result.to_dict() == single.to_dict()

    def test_ranks_every_item_by_aic(self):
        from hydrolog.statistics.high_flows import FIT_METHODS, FloodFrequencyAnalysis

        analysis = FloodFrequencyAnalysis(_FLOODS)
        ranked = analysis.fit_all(fit_method="all")

        aics = [result.aic for result in ranked.values()]
        assert aics == sorted(aics)
        # one ranking over all items: the first item is the lowest AIC of any method,
        # and each method's items keep the order of that method's own ranking
        best = min(
            (result for method in FIT_METHODS for result in _ranked(analysis, method)),
            key=lambda result: result.aic,
        )
        assert next(iter(ranked.values())).to_dict() == best.to_dict()
        for method in FIT_METHODS:
            names = [
                result.distribution_name
                for result in ranked.values()
                if result.fit_method == method
            ]
            assert names == [r.distribution_name for r in _ranked(analysis, method)]

    def test_a_combination_without_parameters_is_left_out(self):
        from hydrolog._warnings import DistributionLeftOut
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        # skewness and L-skewness below the Weibull's (the Gumbel's) limit
        analysis = FloodFrequencyAnalysis(np.array([1.0, *[10.0] * 8, 10.5]))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ranked = analysis.fit_all(fit_method="all")

        left_out = {"weibull/moments", "weibull/l_moments", "weibull/least_squares"}
        assert len(ranked) == 13
        assert "weibull/mle" in ranked
        assert left_out.isdisjoint(ranked)
        notices = [
            w.message for w in caught if isinstance(w.message, DistributionLeftOut)
        ]
        assert {
            f"{notice.details['distribution']}/{notice.details['fit_method']}"
            for notice in notices
        } == left_out
        assert {notice.details["reason"] for notice in notices} == {"out_of_range"}

    def test_one_method_keeps_the_distribution_keys(self):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ranked = FloodFrequencyAnalysis(_FLOODS).fit_all(fit_method="moments")

        assert set(ranked) == set(_DISTRIBUTIONS)
        assert {result.fit_method for result in ranked.values()} == {"moments"}

    def test_one_distribution_by_each_method(self):
        from hydrolog.statistics.high_flows import FIT_METHODS, FloodFrequencyAnalysis

        analysis = FloodFrequencyAnalysis(_FLOODS)
        ranked = analysis.fit_all(fit_method="all", distribution="gev")

        assert set(ranked) == {f"gev/{method}" for method in FIT_METHODS}
        every = analysis.fit_all(fit_method="all")
        assert list(ranked) == [key for key in every if key.startswith("gev/")]

    def test_one_combination_raises_its_own_error(self):
        from hydrolog._warnings import DistributionLeftOut
        from hydrolog.exceptions import CalculationError
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        analysis = FloodFrequencyAnalysis(np.array([1.0, *[10.0] * 8, 10.5]))
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always")
            with pytest.raises(CalculationError) as caught:
                analysis.fit_all(fit_method="moments", distribution="weibull")
        assert caught.value.details["reason"] == "out_of_range"
        assert caught.value.details["distribution"] == "weibull"
        assert not [w for w in seen if isinstance(w.message, DistributionLeftOut)]

    def test_unknown_distribution_raises(self):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        with pytest.raises(InvalidParameterError) as caught:
            FloodFrequencyAnalysis(_FLOODS).fit_all(distribution="gumbel")
        assert caught.value.details["option"] == "distribution"


def test_the_default_fit_method_is_l_moments():
    from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

    analysis = FloodFrequencyAnalysis(_FLOODS)

    for distribution in _DISTRIBUTIONS:
        default = getattr(analysis, f"fit_{distribution}")()
        assert default.fit_method == "l_moments"
        assert default.to_dict() == _fit(analysis, distribution, "l_moments").to_dict()
    ranked = analysis.fit_all()
    assert {result.fit_method for result in ranked.values()} == {"l_moments"}
