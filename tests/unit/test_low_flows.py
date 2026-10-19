"""Tests for low-flow frequency and drought sequence analysis."""

import numpy as np
import pytest


class TestLowFlowAnalysis:

    @pytest.fixture
    def daily_flow_data(self):
        """Synthetic daily data: 3 complete hydrological years with known minima."""
        rng = np.random.default_rng(42)
        dates = np.arange(
            np.datetime64("2018-11-01"),
            np.datetime64("2021-11-01"),
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
    """Daily series of complete hydrological years with exactly these annual minima.

    Hydrological year ``1901 + k`` (1 November 1900 + k - 31 October 1901 + k) holds
    ``minima[k] + 10`` every day except 15 March, the minimum ``minima[k]``.
    """
    from hydrolog.statistics._hydrological_year import hydrological_year

    first_year = 1901
    minima = np.asarray(minima, dtype=float)
    dates = np.arange(
        np.datetime64(f"{first_year - 1}-11-01"),
        np.datetime64(f"{first_year + len(minima) - 1}-11-01"),
        dtype="datetime64[D]",
    )
    year_index = hydrological_year(dates) - first_year
    values = minima[year_index] + 10.0
    month = dates.astype("datetime64[M]")
    is_15_march = (month.astype(int) % 12 == 2) & ((dates - month).astype(int) == 14)
    values[is_15_march] = minima[year_index[is_15_march]]
    return values, dates


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


def _calendar_year_series(first_year=1991, last_year=2020):
    """Daily series from 1 January ``first_year`` to 31 December ``last_year``.

    A calendar-year export. Baseline 5.0, a dip every 15 September (2.0 + 0.1 * (y % 5))
    and a flood every 15 March (10 + y % 7). Hydrological years ``first_year`` ...
    ``last_year`` hold both, but the first lacks November and December of the year
    before and the year ``last_year + 1`` holds only November and December of
    ``last_year``: baseline, no dip and no flood.
    """
    dates = np.arange(
        np.datetime64(f"{first_year}-01-01"),
        np.datetime64(f"{last_year + 1}-01-01"),
        dtype="datetime64[D]",
    )
    values = np.full(len(dates), 5.0)
    for year in range(first_year, last_year + 1):
        values[dates == np.datetime64(f"{year}-03-15")] = 10.0 + year % 7
        values[dates == np.datetime64(f"{year}-09-15")] = 2.0 + 0.1 * (year % 5)
    return values, dates


class TestAnnualMinimaOfCompleteYears:
    """Only complete hydrological years give annual minima (KZGW 2017; WMO No. 1029).

    Regression: every year present in the dates was used, so the calendar-year series
    1991-2020 gave 31 "years" - the first lacking November and December 1990 and the
    last (2021) holding only November and December 2020, with the baseline 5.0 as its
    "minimum" instead of an annual minimum of 2.0-2.4 - and no word about it.
    """

    EXPECTED = [2.0 + 0.1 * (year % 5) for year in range(1992, 2021)]

    def test_the_stub_years_of_a_calendar_year_series_are_skipped_and_named(self):
        from hydrolog.statistics import LowFlowAnalysis

        values, dates = _calendar_year_series()
        with pytest.warns(UserWarning) as caught:
            minima = LowFlowAnalysis(values, dates).annual_minima()
        np.testing.assert_allclose(minima, self.EXPECTED)
        assert 5.0 not in minima
        texts = [str(warning.message) for warning in caught]
        assert any(
            "2 of 31" in text
            and "1991 (304 of 365 days), 2021 (61 of 365 days)" in text
            for text in texts
        )

    def test_the_fit_equals_the_fit_of_the_complete_years_alone(self):
        import warnings

        from hydrolog.statistics import LowFlowAnalysis

        values, dates = _calendar_year_series()
        complete = (dates >= np.datetime64("1991-11-01")) & (
            dates < np.datetime64("2020-11-01")
        )
        periods = np.array([2.0, 10.0, 100.0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            whole = LowFlowAnalysis(values, dates, periods).fit_fisher_tippett()
            alone = LowFlowAnalysis(
                values[complete], dates[complete], periods
            ).fit_fisher_tippett()
        assert whole.to_dict() == alone.to_dict()

    def test_one_day_without_a_value_costs_the_year(self):
        from hydrolog.statistics import LowFlowAnalysis

        values, dates = _calendar_year_series()
        values[dates == np.datetime64("2005-04-02")] = np.nan
        with pytest.warns(UserWarning, match=r"2005 \(364 of 365 days\)"):
            minima = LowFlowAnalysis(values, dates).annual_minima()
        assert len(minima) == 28
        np.testing.assert_allclose(
            minima,
            [m for m, year in zip(self.EXPECTED, range(1992, 2021)) if year != 2005],
        )

    def test_a_series_without_a_complete_year_has_no_annual_minima(self):
        from hydrolog.exceptions import CalculationError
        from hydrolog.statistics import LowFlowAnalysis

        dates = np.arange(
            np.datetime64("2021-01-01"),
            np.datetime64("2021-07-01"),
            dtype="datetime64[D]",
        )
        analysis = LowFlowAnalysis(np.ones(len(dates)), dates)
        for call in (
            analysis.annual_minima,
            analysis.fit_fisher_tippett,
            analysis.empirical_frequency,
            analysis.empirical_non_exceedance,
        ):
            with pytest.raises(CalculationError) as caught:
                call()
            assert caught.value.code == "calculation_error"
            assert caught.value.details == {"incomplete_years": [2021]}
        # the drought sequences need no whole year
        assert analysis.detect_sequences(threshold=0.5).n_events == 0


class TestEmpiricalNonExceedance:
    """Plotting positions of the annual minima, in the convention of the quantiles.

    Regression: the empirical block of a low-flow analysis was ``empirical_frequency()``
    - values descending with *exceedance* probabilities - so the deepest low flow
    of tests/fixtures/daily_flows_3y.csv (1.66) got the return period 1.33 (exceedance
    probability 0.75), while the Fisher-Tippett quantiles, WMO No. 1029 and Tallaksen
    and van Lanen (2004) count the return period of a low flow with the
    *non-exceedance* probability ``F``: ``F = m / (n + 1) = 0.25``, ``T = 1 / F = 4``.
    """

    MINIMA = [3.0, 1.0, 2.0, 5.0, 4.0]

    def _analysis(self):
        from hydrolog.statistics import LowFlowAnalysis

        values, dates = _series_with_annual_minima(self.MINIMA)
        return LowFlowAnalysis(values, dates)

    def test_weibull_positions_of_the_ascending_minima(self):
        empirical = self._analysis().empirical_non_exceedance()
        assert empirical.values_ascending.tolist() == [1.0, 2.0, 3.0, 4.0, 5.0]
        np.testing.assert_allclose(
            empirical.non_exceedance_probabilities, np.arange(1, 6) / 6
        )
        np.testing.assert_allclose(empirical.return_periods, [6.0, 3.0, 2.0, 1.5, 1.2])

    def test_the_deepest_low_flow_has_the_longest_return_period(self):
        empirical = self._analysis().empirical_non_exceedance()
        assert empirical.values_ascending[0] == min(self.MINIMA)
        assert empirical.return_periods[0] == len(self.MINIMA) + 1
        assert np.all(np.diff(empirical.return_periods) < 0)

    @pytest.mark.parametrize(
        ("method", "expected"),
        [
            ("hazen", [0.1, 0.3, 0.5, 0.7, 0.9]),
            ("cunnane", [0.6 / 5.2, 1.6 / 5.2, 2.6 / 5.2, 3.6 / 5.2, 4.6 / 5.2]),
        ],
    )
    def test_other_plotting_position_formulas(self, method, expected):
        empirical = self._analysis().empirical_non_exceedance(method)
        np.testing.assert_allclose(empirical.non_exceedance_probabilities, expected)
        np.testing.assert_allclose(empirical.return_periods, 1.0 / np.array(expected))

    def test_an_unknown_method_is_an_invalid_parameter(self):
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError, match="gringorten"):
            self._analysis().empirical_non_exceedance("gringorten")

    def test_it_is_the_exceedance_frequency_seen_from_the_other_side(self):
        """The old block stays as it was; ``F = 1 - P`` of the same values."""
        analysis = self._analysis()
        exceedance = analysis.empirical_frequency()
        non_exceedance = analysis.empirical_non_exceedance()
        assert exceedance.values_sorted.tolist() == [5.0, 4.0, 3.0, 2.0, 1.0]
        np.testing.assert_allclose(exceedance.exceedance_prob, np.arange(1, 6) / 6)
        np.testing.assert_allclose(
            non_exceedance.non_exceedance_probabilities,
            1.0 - exceedance.exceedance_prob[::-1],
        )
        assert (
            non_exceedance.values_ascending.tolist()
            == exceedance.values_sorted[::-1].tolist()
        )

    def test_the_empirical_curve_meets_the_fitted_quantiles_at_the_same_return_period(
        self,
    ):
        """Interpolating F = 1/T in the empirical positions gives the fitted Q_T.

        The sample is noise-free (the quantiles of a Weibull minimum distribution), so
        Hazen positions ``(m - 0.5) / n`` are exact. With the exceedance convention of
        before the curve would read the mirror-image quantiles (``Q_90`` for T = 10).
        """
        from scipy.stats import weibull_min

        from hydrolog.statistics import LowFlowAnalysis

        periods = np.array([2.0, 5.0, 10.0])
        truth = weibull_min(2.0, loc=1.0, scale=5.0)
        size = 200
        values, dates = _series_with_annual_minima(
            truth.ppf((np.arange(1, size + 1) - 0.5) / size)
        )
        analysis = LowFlowAnalysis(values, dates, periods)
        fitted = analysis.fit_fisher_tippett()
        empirical = analysis.empirical_non_exceedance("hazen")
        read = np.interp(
            fitted.non_exceedance_probabilities,
            empirical.non_exceedance_probabilities,
            empirical.values_ascending,
        )
        np.testing.assert_allclose(read, fitted.quantiles, rtol=0.03)
        np.testing.assert_allclose(read, truth.ppf(1.0 / periods), rtol=0.03)

    def test_the_result_serializes_with_clear_field_names(self):
        document = self._analysis().empirical_non_exceedance().to_dict()
        assert list(document) == [
            "values_ascending",
            "non_exceedance_probabilities",
            "return_periods",
        ]
