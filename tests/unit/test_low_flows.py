"""Tests for low-flow frequency and drought sequence analysis."""

import numpy as np
import pytest


class TestLowFlowAnalysis:

    @pytest.fixture
    def daily_flow_data(self):
        """Synthetic daily data: 3 hydro years with known minima."""
        rng = np.random.default_rng(42)
        dates = np.arange(
            np.datetime64("2018-11-01"),
            np.datetime64("2021-10-31"),
            dtype="datetime64[D]",
        )
        values = rng.uniform(5, 50, size=len(dates))
        values[30] = 2.0  # year 2019 min
        values[400] = 1.0  # year 2020 min
        values[750] = 3.0  # year 2021 min
        return dates, values

    def test_annual_minima_extraction(self, daily_flow_data):
        from hydrolog.statistics.low_flows import LowFlowAnalysis

        dates, values = daily_flow_data
        lfa = LowFlowAnalysis(values, dates)
        minima = lfa.annual_minima()
        assert len(minima) == 3
        assert min(minima) == 1.0

    def test_fit_fisher_tippett(self, daily_flow_data):
        from hydrolog.statistics.low_flows import LowFlowAnalysis

        dates, values = daily_flow_data
        lfa = LowFlowAnalysis(values, dates)
        result = lfa.fit_fisher_tippett()
        assert result.distribution_name == "fisher_tippett"
        assert len(result.quantiles) > 0

    def test_empirical_frequency(self, daily_flow_data):
        from hydrolog.statistics.low_flows import LowFlowAnalysis

        dates, values = daily_flow_data
        lfa = LowFlowAnalysis(values, dates)
        emp = lfa.empirical_frequency()
        assert len(emp.values_sorted) == 3
        assert emp.values_sorted[0] >= emp.values_sorted[-1]

    def test_detect_sequences_finds_drought(self):
        from hydrolog.statistics.low_flows import LowFlowAnalysis

        dates = np.arange(
            np.datetime64("2020-11-01"),
            np.datetime64("2021-10-31"),
            dtype="datetime64[D]",
        )
        values = np.full(len(dates), 50.0)
        values[100:110] = 3.0
        lfa = LowFlowAnalysis(values, dates)
        result = lfa.detect_sequences(threshold=10.0, min_duration_days=5)
        assert result.n_events == 1
        assert result.sequences[0].duration_days == 10

    def test_detect_sequences_merges_close_events(self):
        from hydrolog.statistics.low_flows import LowFlowAnalysis

        dates = np.arange(
            np.datetime64("2020-11-01"),
            np.datetime64("2021-10-31"),
            dtype="datetime64[D]",
        )
        values = np.full(len(dates), 50.0)
        values[100:106] = 3.0  # 6 days low
        values[106:109] = 50.0  # 3 day gap (< max_gap=4)
        values[109:115] = 3.0  # 6 days low
        lfa = LowFlowAnalysis(values, dates)
        result = lfa.detect_sequences(
            threshold=10.0, min_duration_days=5, max_gap_days=4
        )
        assert result.n_events == 1
        assert result.sequences[0].duration_days == 15

    def test_deficit_volume_computed(self):
        from hydrolog.statistics.low_flows import LowFlowAnalysis

        dates = np.arange(
            np.datetime64("2020-11-01"),
            np.datetime64("2021-10-31"),
            dtype="datetime64[D]",
        )
        values = np.full(len(dates), 50.0)
        values[100:105] = 5.0  # 5 days at Q=5, threshold=10
        lfa = LowFlowAnalysis(values, dates)
        result = lfa.detect_sequences(threshold=10.0, min_duration_days=5)
        assert result.sequences[0].deficit_volume == pytest.approx(25.0)

    def test_detect_sequences_negative_threshold_raises(self):
        """Negative threshold should raise InvalidParameterError."""
        from hydrolog.statistics.low_flows import LowFlowAnalysis
        from hydrolog.exceptions import InvalidParameterError

        dates = np.arange(
            np.datetime64("2020-11-01"),
            np.datetime64("2021-10-31"),
            dtype="datetime64[D]",
        )
        values = np.full(len(dates), 50.0)
        lfa = LowFlowAnalysis(values, dates)
        with pytest.raises(InvalidParameterError):
            lfa.detect_sequences(threshold=-5.0)

    def test_detect_sequences_zero_min_duration_raises(self):
        """min_duration_days < 1 should raise InvalidParameterError."""
        from hydrolog.statistics.low_flows import LowFlowAnalysis
        from hydrolog.exceptions import InvalidParameterError

        dates = np.arange(
            np.datetime64("2020-11-01"),
            np.datetime64("2021-10-31"),
            dtype="datetime64[D]",
        )
        values = np.full(len(dates), 50.0)
        lfa = LowFlowAnalysis(values, dates)
        with pytest.raises(InvalidParameterError):
            lfa.detect_sequences(threshold=10.0, min_duration_days=0)

    def test_empty_data_raises(self):
        from hydrolog.statistics.low_flows import LowFlowAnalysis
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            LowFlowAnalysis(np.array([]), np.array([]))

    def test_mismatched_lengths_raises(self):
        from hydrolog.statistics.low_flows import LowFlowAnalysis
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            LowFlowAnalysis(
                np.array([1.0, 2.0]), np.array(["2021-01-01"], dtype="datetime64[D]")
            )


def _series_with_annual_minima(minima):
    """Daily-style series whose annual minima are exactly ``minima``.

    Two observations per hydrological year (15 March: the minimum, 15 July: the
    minimum plus 10), starting with the hydrological year 1901.
    """
    years = np.arange(1901, 1901 + len(minima))
    low_days = np.array([np.datetime64(f"{year}-03-15") for year in years])
    high_days = np.array([np.datetime64(f"{year}-07-15") for year in years])
    dates = np.concatenate([low_days, high_days])
    values = np.concatenate([minima, np.asarray(minima) + 10.0])
    order = np.argsort(dates)
    return values[order], dates[order]


def _quantile_sample(distribution, size):
    """Noise-free sample: the quantiles of ``distribution`` at (i - 0.5) / size."""
    return distribution.ppf((np.arange(1, size + 1) - 0.5) / size)


class TestFisherTippettForMinima:
    """The fit is the GEV *for minima*: quantiles are those of the smallest values.

    Regression of the fit of the maxima-type GEV to the minima, which recovered
    only the bulk of the sample. For the Weibull minimum distribution below (1000
    noise-free annual minima) it gave 1.24 instead of 1.50 at T = 100 years
    (-17 %) and 0.33 instead of 1.16 at T = 1000 years (-71 %); for the Gumbel
    minimum distribution it gave -3800 instead of 13 at T = 100 years.
    """

    RETURN_PERIODS = np.array([2.0, 5.0, 10.0, 20.0, 50.0, 100.0])

    def _fit(self, distribution, size=1000):
        from hydrolog.statistics.low_flows import LowFlowAnalysis

        values, dates = _series_with_annual_minima(_quantile_sample(distribution, size))
        return LowFlowAnalysis(values, dates, self.RETURN_PERIODS).fit_fisher_tippett()

    def test_recovers_the_quantiles_of_a_weibull_minimum_distribution(self):
        from scipy.stats import weibull_min

        truth = weibull_min(2.0, loc=1.0, scale=5.0)
        result = self._fit(truth)
        np.testing.assert_allclose(
            result.quantiles, truth.ppf(1.0 / self.RETURN_PERIODS), rtol=0.02
        )

    def test_parameters_are_those_of_the_minimum_distribution(self):
        """Weibull(k, x0, lam) is the minima GEV with c = 1/k, loc = x0 + lam,
        scale = lam / k (here 0.5, 6, 2.5)."""
        from scipy.stats import weibull_min

        result = self._fit(weibull_min(2.0, loc=1.0, scale=5.0))
        assert result.parameters["shape"] == pytest.approx(0.5, abs=0.02)
        assert result.parameters["loc"] == pytest.approx(6.0, abs=0.1)
        assert result.parameters["scale"] == pytest.approx(2.5, abs=0.05)

    def test_recovers_the_quantiles_of_a_gumbel_minimum_distribution(self):
        from scipy.stats import gumbel_l

        truth = gumbel_l(loc=50.0, scale=8.0)
        result = self._fit(truth)
        assert result.parameters["shape"] == pytest.approx(0.0, abs=0.02)
        assert result.parameters["loc"] == pytest.approx(50.0, abs=0.5)
        assert result.parameters["scale"] == pytest.approx(8.0, abs=0.2)
        np.testing.assert_allclose(
            result.quantiles, truth.ppf(1.0 / self.RETURN_PERIODS), rtol=0.02
        )

    def test_quantiles_follow_the_closed_form_of_the_reported_parameters(self):
        """Q_T = loc + scale / c * ((-ln(1 - 1/T)) ** c - 1), independent of SciPy."""
        from scipy.stats import weibull_min

        result = self._fit(weibull_min(3.0, loc=0.5, scale=8.0), size=60)
        c = result.parameters["shape"]
        p = 1.0 / self.RETURN_PERIODS
        expected = result.parameters["loc"] + result.parameters["scale"] / c * (
            (-np.log1p(-p)) ** c - 1.0
        )
        np.testing.assert_allclose(result.quantiles, expected, rtol=1e-9)

    def test_rarer_droughts_have_lower_flows_and_two_years_is_the_median(self):
        from scipy.stats import weibull_min

        truth = weibull_min(2.0, loc=1.0, scale=5.0)
        result = self._fit(truth)
        assert np.all(np.diff(result.quantiles) < 0)
        assert result.quantiles[0] == pytest.approx(truth.median(), rel=0.01)
        np.testing.assert_allclose(
            result.non_exceedance_probabilities, 1.0 / self.RETURN_PERIODS
        )

    def test_ks_statistic_compares_the_sample_with_the_fitted_minimum_distribution(
        self,
    ):
        from scipy.stats import weibull_min

        result = self._fit(weibull_min(2.0, loc=1.0, scale=5.0))
        assert result.ks_statistic < 0.01
        assert result.ks_valid is False
