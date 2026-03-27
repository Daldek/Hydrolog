"""Tests for flood frequency analysis."""

import warnings

import numpy as np
import pytest
from scipy.stats import genextreme, lognorm, pearson3, weibull_min


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

    def test_empty_data_raises(self):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            FloodFrequencyAnalysis(np.array([]))

    def test_nan_in_data_raises(self):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            FloodFrequencyAnalysis(np.array([1.0, np.nan, 3.0]))

    def test_small_sample_kzgw_warning(self):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            FloodFrequencyAnalysis(np.arange(1.0, 21.0))
            kzgw_warnings = [x for x in w if "KZGW" in str(x.message)]
            assert len(kzgw_warnings) >= 1
