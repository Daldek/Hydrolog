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
