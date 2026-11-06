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
    @pytest.mark.parametrize("fit_method", ["moments", "l_moments"])
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
