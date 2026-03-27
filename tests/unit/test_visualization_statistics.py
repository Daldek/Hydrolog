"""Smoke tests for statistics visualization functions."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest


class TestStatisticsVisualization:

    def test_plot_frequency_curve(self):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
        from hydrolog.visualization.statistics import plot_frequency_curve
        rng = np.random.default_rng(42)
        data = rng.gumbel(100, 30, size=50)
        ffa = FloodFrequencyAnalysis(data)
        result = ffa.fit_gev()
        fig = plot_frequency_curve(result)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_frequency_comparison(self):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
        from hydrolog.visualization.statistics import plot_frequency_comparison
        rng = np.random.default_rng(42)
        data = rng.gumbel(100, 30, size=50)
        ffa = FloodFrequencyAnalysis(data)
        results = ffa.fit_all()
        fig = plot_frequency_comparison(results)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_non_exceedance_curve(self):
        from hydrolog.statistics.low_flows import LowFlowAnalysis
        from hydrolog.visualization.statistics import plot_non_exceedance_curve
        rng = np.random.default_rng(42)
        dates = np.arange(np.datetime64("2015-11-01"), np.datetime64("2020-10-31"), dtype="datetime64[D]")
        values = rng.uniform(2, 30, size=len(dates))
        lfa = LowFlowAnalysis(values, dates)
        result = lfa.fit_fisher_tippett()
        fig = plot_non_exceedance_curve(result)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_daily_characteristics(self):
        from hydrolog.statistics.characteristic import calculate_daily_statistics
        from hydrolog.visualization.statistics import plot_daily_characteristics
        rng = np.random.default_rng(42)
        dates = np.arange(np.datetime64("2019-11-01"), np.datetime64("2021-10-31"), dtype="datetime64[D]")
        values = rng.uniform(5, 50, size=len(dates))
        stats = calculate_daily_statistics(values, dates)
        fig = plot_daily_characteristics(stats)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_monthly_statistics(self):
        from hydrolog.statistics.characteristic import calculate_monthly_statistics
        from hydrolog.visualization.statistics import plot_monthly_statistics
        rng = np.random.default_rng(42)
        dates = np.arange(np.datetime64("2010-11-01"), np.datetime64("2020-10-31"), dtype="datetime64[D]")
        values = rng.uniform(5, 50, size=len(dates))
        stats = calculate_monthly_statistics(values, dates)
        fig = plot_monthly_statistics(stats)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_annual_hydrographs(self):
        from hydrolog.visualization.statistics import plot_annual_hydrographs
        rng = np.random.default_rng(42)
        dates = np.arange(np.datetime64("2019-11-01"), np.datetime64("2021-10-31"), dtype="datetime64[D]")
        values = rng.uniform(5, 50, size=len(dates))
        fig = plot_annual_hydrographs(values, dates)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_flow_histogram(self):
        from hydrolog.visualization.statistics import plot_flow_histogram
        rng = np.random.default_rng(42)
        fig = plot_flow_histogram(rng.uniform(10, 100, size=100))
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_low_flow_sequences(self):
        from hydrolog.statistics.low_flows import LowFlowAnalysis
        from hydrolog.visualization.statistics import plot_low_flow_sequences
        dates = np.arange(np.datetime64("2020-11-01"), np.datetime64("2021-10-31"), dtype="datetime64[D]")
        values = np.full(len(dates), 50.0)
        values[100:110] = 3.0
        lfa = LowFlowAnalysis(values, dates)
        result = lfa.detect_sequences(threshold=10.0, min_duration_days=5)
        fig = plot_low_flow_sequences(values, result)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_rating_curve(self):
        from hydrolog.hydrometrics.rating_curve import RatingCurve
        from hydrolog.visualization.statistics import plot_rating_curve
        h = np.linspace(60, 200, 30)
        q = 2.0 * (h - 50) ** 1.5
        rc = RatingCurve(h, q)
        result = rc.fit(h0_initial=50.0)
        fig = plot_rating_curve(rc, result)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_water_level_frequency(self):
        from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency
        from hydrolog.visualization.statistics import plot_water_level_frequency
        rng = np.random.default_rng(42)
        levels = rng.uniform(100, 300, size=1000)
        wlf = WaterLevelFrequency(levels, bin_width=10.0)
        freq = wlf.frequency_distribution()
        fig = plot_water_level_frequency(freq)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
