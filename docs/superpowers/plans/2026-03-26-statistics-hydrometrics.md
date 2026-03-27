# Statistics & Hydrometrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `hydrolog/statistics/` and `hydrolog/hydrometrics/` modules — flood frequency analysis, characteristic values, low-flow analysis, Mann-Kendall stationarity test, rating curves, and visualizations.

**Architecture:** Two new top-level modules (`statistics/`, `hydrometrics/`) plus one new visualization file. All inputs are NumPy arrays. SciPy promoted to required dependency. TDD throughout — tests first, then implementation.

**Tech Stack:** Python 3.12+, NumPy, SciPy (scipy.stats, scipy.optimize), matplotlib/seaborn (visualization), pytest

**Spec:** `docs/superpowers/specs/2026-03-26-statistics-hydrometrics-design.md`

**Branch:** `feature/statistics-hydrometrics` (already created)

**Run tests:** `.venv/bin/python -m pytest tests/ -v`

**Run single test:** `.venv/bin/python -m pytest tests/unit/test_file.py::TestClass::test_name -v`

---

## File Structure

```
CREATE: hydrolog/statistics/__init__.py
CREATE: hydrolog/statistics/_hydrological_year.py
CREATE: hydrolog/statistics/_types.py
CREATE: hydrolog/statistics/characteristic.py
CREATE: hydrolog/statistics/stationarity.py
CREATE: hydrolog/statistics/high_flows.py
CREATE: hydrolog/statistics/low_flows.py
CREATE: hydrolog/hydrometrics/__init__.py
CREATE: hydrolog/hydrometrics/rating_curve.py
CREATE: hydrolog/visualization/statistics.py
CREATE: tests/unit/test_characteristic.py
CREATE: tests/unit/test_stationarity.py
CREATE: tests/unit/test_high_flows.py
CREATE: tests/unit/test_low_flows.py
CREATE: tests/unit/test_rating_curve.py
CREATE: tests/unit/test_visualization_statistics.py
MODIFY: pyproject.toml (scipy to core deps)
MODIFY: hydrolog/visualization/__init__.py (add statistics imports)
```

---

### Task 1: Project setup — SciPy dependency and empty module scaffolding

**Files:**
- Modify: `pyproject.toml`
- Create: `hydrolog/statistics/__init__.py`
- Create: `hydrolog/hydrometrics/__init__.py`

- [ ] **Step 1: Promote SciPy to core dependency in pyproject.toml**

Read `pyproject.toml`, find the `dependencies` list, and add `"scipy>=1.10"`. Remove scipy from `[project.optional-dependencies]` if it appears there standalone (keep it in composite groups like `[full]` that list it).

- [ ] **Step 2: Create empty `hydrolog/statistics/__init__.py`**

```python
"""Statistical analysis module for hydrological data.

Provides:
- Characteristic flow values (Polish system: NNQ–WWQ)
- Flood frequency analysis (GEV, Log-Normal, Pearson III, Weibull)
- Low-flow frequency analysis (Fisher-Tippett, drought sequences)
- Mann-Kendall trend test for series stationarity
"""

__all__: list[str] = []
```

- [ ] **Step 3: Create empty `hydrolog/hydrometrics/__init__.py`**

```python
"""Hydrometrics module for water level and discharge measurements.

Provides:
- Rating curve fitting Q = a × (H - H₀)^b
- Water level frequency and duration analysis
- Rybczyński method for water level zone delimitation
"""

__all__: list[str] = []
```

- [ ] **Step 4: Verify existing tests still pass**

Run: `.venv/bin/python -m pytest tests/ -x -q`
Expected: All 754 tests pass.

- [ ] **Step 5: Commit**

```
feat: scaffold statistics and hydrometrics modules, promote scipy to core dep
```

---

### Task 2: Hydrological year utilities (`_hydrological_year.py`)

**Files:**
- Create: `hydrolog/statistics/_hydrological_year.py`
- Create: `tests/unit/test_characteristic.py` (first batch)

- [ ] **Step 1: Write failing tests for hydrological year functions**

Create `tests/unit/test_characteristic.py`:

```python
"""Tests for hydrological year utilities and characteristic values."""

import numpy as np
import pytest
from numpy.typing import NDArray


class TestHydrologicalYear:
    """Tests for _hydrological_year module."""

    def test_hydrological_year_november_december_next_year(self):
        """Nov-Dec dates belong to the next calendar year's hydro year."""
        from hydrolog.statistics._hydrological_year import hydrological_year

        dates = np.array(
            ["2020-11-01", "2020-12-15", "2021-01-10", "2021-10-31"],
            dtype="datetime64[D]",
        )
        result = hydrological_year(dates)
        np.testing.assert_array_equal(result, [2021, 2021, 2021, 2021])

    def test_hydrological_year_boundary_october_vs_november(self):
        """Oct 31 is last day of current year; Nov 1 is first day of next."""
        from hydrolog.statistics._hydrological_year import hydrological_year

        dates = np.array(
            ["2020-10-31", "2020-11-01"],
            dtype="datetime64[D]",
        )
        result = hydrological_year(dates)
        np.testing.assert_array_equal(result, [2020, 2021])

    def test_hydrological_day_of_year_nov1_is_day1(self):
        """November 1 is day 1 of the hydrological year."""
        from hydrolog.statistics._hydrological_year import hydrological_day_of_year

        dates = np.array(["2020-11-01"], dtype="datetime64[D]")
        result = hydrological_day_of_year(dates)
        assert result[0] == 1

    def test_hydrological_day_of_year_oct31_is_last(self):
        """October 31 is day 366 (leap) or 365 (non-leap)."""
        from hydrolog.statistics._hydrological_year import hydrological_day_of_year

        dates = np.array(["2021-10-31"], dtype="datetime64[D]")
        result = hydrological_day_of_year(dates)
        assert result[0] in (365, 366)

    def test_split_half_years_winter_summer(self):
        """Winter = Nov-Apr, Summer = May-Oct."""
        from hydrolog.statistics._hydrological_year import split_half_years

        dates = np.array(
            ["2021-01-15", "2021-05-15", "2021-11-15", "2021-07-20"],
            dtype="datetime64[D]",
        )
        values = np.array([10.0, 20.0, 30.0, 40.0])
        winter, summer = split_half_years(values, dates)
        np.testing.assert_array_equal(winter, [10.0, 30.0])  # Jan, Nov
        np.testing.assert_array_equal(summer, [20.0, 40.0])  # May, Jul
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/test_characteristic.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `_hydrological_year.py`**

Create `hydrolog/statistics/_hydrological_year.py`:

```python
"""Private utilities for Polish hydrological year (Nov 1 – Oct 31).

Polish hydrological year:
- Starts: November 1 of the previous calendar year
- Ends: October 31 of the current calendar year
- Winter half-year: XI–IV (November–April)
- Summer half-year: V–X (May–October)

Reference: IMGW-PIB; https://pl.wikipedia.org/wiki/Rok_hydrologiczny
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def hydrological_year(dates: NDArray) -> NDArray[np.int_]:
    """Assign hydrological year to each date.

    Parameters
    ----------
    dates : NDArray
        Array of dates (dtype datetime64[D] or similar).

    Returns
    -------
    NDArray[np.int_]
        Hydrological year for each date. Months XI–XII belong to the
        next calendar year's hydrological year.
    """
    months = dates.astype("datetime64[M]").astype(int) % 12 + 1
    years = dates.astype("datetime64[Y]").astype(int) + 1970
    # Nov (11) and Dec (12) → next year's hydro year
    return np.where(months >= 11, years + 1, years)


def hydrological_day_of_year(dates: NDArray) -> NDArray[np.int_]:
    """Compute day-of-year within the hydrological year.

    Parameters
    ----------
    dates : NDArray
        Array of dates (dtype datetime64[D]).

    Returns
    -------
    NDArray[np.int_]
        Day number (1 = Nov 1, up to 365 or 366).
    """
    hydro_years = hydrological_year(dates)
    # Start of each hydrological year is Nov 1 of the previous calendar year
    nov1 = (hydro_years - 1).astype("U4").astype("datetime64[Y]") + np.timedelta64(
        10, "M"
    )  # month index 10 = November (0-based)
    return (dates - nov1).astype(int) + 1


def split_half_years(
    values: NDArray[np.float64], dates: NDArray
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Split values into winter and summer half-years.

    Parameters
    ----------
    values : NDArray[np.float64]
        Data values corresponding to dates.
    dates : NDArray
        Array of dates (dtype datetime64[D]).

    Returns
    -------
    tuple[NDArray[np.float64], NDArray[np.float64]]
        (winter_values, summer_values) where:
        - Winter: months 11, 12, 1, 2, 3, 4
        - Summer: months 5, 6, 7, 8, 9, 10
    """
    months = dates.astype("datetime64[M]").astype(int) % 12 + 1
    winter_mask = (months >= 11) | (months <= 4)
    return values[winter_mask], values[~winter_mask]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_characteristic.py -v`
Expected: All 5 tests pass.

- [ ] **Step 5: Commit**

```
feat(statistics): add hydrological year utilities (_hydrological_year.py)
```

---

### Task 3: Shared types (`_types.py`) and `EmpiricalFrequency`

**Files:**
- Create: `hydrolog/statistics/_types.py`

- [ ] **Step 1: Create `_types.py` with shared dataclasses**

```python
"""Shared dataclasses for statistics module."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass
class EmpiricalFrequency:
    """Empirical frequency (plotting positions).

    Parameters
    ----------
    values_sorted : NDArray[np.float64]
        Values sorted in descending order.
    exceedance_prob : NDArray[np.float64]
        Exceedance probability for each value.
    return_periods : NDArray[np.float64]
        Return period T = 1/P for each value.
    """

    values_sorted: NDArray[np.float64]
    exceedance_prob: NDArray[np.float64]
    return_periods: NDArray[np.float64]


def compute_plotting_positions(
    values: NDArray[np.float64],
    method: str = "weibull",
) -> EmpiricalFrequency:
    """Compute empirical plotting positions.

    Parameters
    ----------
    values : NDArray[np.float64]
        Sample values (will be sorted descending).
    method : str, optional
        Plotting position method, by default "weibull".
        Options: "weibull", "hazen", "cunnane".

    Returns
    -------
    EmpiricalFrequency
        Sorted values with exceedance probabilities and return periods.

    References
    ----------
    Weibull (1939): P_i = i / (n+1)
    Hazen (1930): P_i = (i - 0.5) / n
    Cunnane (1978): P_i = (i - 0.4) / (n + 0.2)
    """
    from hydrolog.exceptions import InvalidParameterError

    sorted_vals = np.sort(values)[::-1]  # descending
    n = len(sorted_vals)
    ranks = np.arange(1, n + 1, dtype=np.float64)

    if method == "weibull":
        exceedance = ranks / (n + 1)
    elif method == "hazen":
        exceedance = (ranks - 0.5) / n
    elif method == "cunnane":
        exceedance = (ranks - 0.4) / (n + 0.2)
    else:
        raise InvalidParameterError(
            f"Unknown plotting position method: {method!r}. "
            f"Use 'weibull', 'hazen', or 'cunnane'."
        )

    return EmpiricalFrequency(
        values_sorted=sorted_vals,
        exceedance_prob=exceedance,
        return_periods=1.0 / exceedance,
    )
```

- [ ] **Step 2: Commit**

```
feat(statistics): add shared types and plotting positions (_types.py)
```

---

### Task 4: Characteristic values (`characteristic.py`)

**Files:**
- Create: `hydrolog/statistics/characteristic.py`
- Modify: `tests/unit/test_characteristic.py` (add tests)

- [ ] **Step 1: Write failing tests for characteristic values**

Append to `tests/unit/test_characteristic.py`:

```python
class TestCharacteristicValues:
    """Tests for characteristic flow values (Polish system)."""

    @pytest.fixture
    def known_daily_data(self):
        """3 hydrological years of daily data with known characteristics."""
        # Year 2021 (Nov 2020 - Oct 2021): max=100, mean=50, min=10
        # Year 2022 (Nov 2021 - Oct 2022): max=80, mean=40, min=5
        # Year 2023 (Nov 2022 - Oct 2023): max=120, mean=60, min=15
        rng = np.random.default_rng(42)
        dates_list = []
        values_list = []
        for year_offset, (mx, mn, avg) in enumerate([
            (100.0, 10.0, 50.0),
            (80.0, 5.0, 40.0),
            (120.0, 15.0, 60.0),
        ]):
            start = np.datetime64(f"{2020 + year_offset}-11-01")
            days = np.arange(365, dtype="timedelta64[D]")
            year_dates = start + days
            # Generate data with known max/min, mean approx avg
            year_values = rng.uniform(mn + 1, mx - 1, size=365)
            year_values[0] = mx   # force max
            year_values[1] = mn   # force min
            dates_list.append(year_dates)
            values_list.append(year_values)

        return np.concatenate(dates_list), np.concatenate(values_list)

    def test_characteristic_values_wwq(self, known_daily_data):
        """WWQ = max of annual maxima."""
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        assert result.wwx == 120.0  # max across years

    def test_characteristic_values_nnq(self, known_daily_data):
        """NNQ = min of annual minima."""
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        assert result.nnx == 5.0  # min across years

    def test_characteristic_values_swq_is_mean_of_annual_maxima(self, known_daily_data):
        """SWQ = mean of annual maxima (NOT mean of half-year maxima)."""
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        expected_swq = np.mean([100.0, 80.0, 120.0])
        assert abs(result.swx - expected_swq) < 0.01

    def test_characteristic_values_zwq_is_median_of_annual_maxima(self, known_daily_data):
        """ZWQ = median of annual maxima."""
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        expected_zwq = np.median([100.0, 80.0, 120.0])
        assert abs(result.zwx - expected_zwq) < 0.01

    def test_characteristic_values_period_years(self, known_daily_data):
        """Period equals number of hydrological years."""
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        assert result.period_years == 3

    def test_empty_input_raises(self):
        """Empty arrays should raise InvalidParameterError."""
        from hydrolog.statistics.characteristic import calculate_characteristic_values
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            calculate_characteristic_values(np.array([]), np.array([]))

    def test_mismatched_lengths_raises(self):
        """Mismatched array lengths should raise InvalidParameterError."""
        from hydrolog.statistics.characteristic import calculate_characteristic_values
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            calculate_characteristic_values(
                np.array([1.0, 2.0]),
                np.array(["2021-01-01"], dtype="datetime64[D]"),
            )


class TestMonthlyStatistics:
    """Tests for monthly statistics with t-Student CI."""

    def test_ci_uses_t_student_not_z(self):
        """CI should use t-Student (wider than z for small n)."""
        from hydrolog.statistics.characteristic import calculate_monthly_statistics

        rng = np.random.default_rng(42)
        # 10 years of daily data (small sample → t-Student matters)
        dates = np.arange(
            np.datetime64("2010-11-01"),
            np.datetime64("2020-10-31"),
            dtype="datetime64[D]",
        )
        values = rng.uniform(5, 50, size=len(dates))
        result = calculate_monthly_statistics(values, dates)

        # For n=10, t(0.975, df=9)=2.262 vs z(0.975)=1.96
        # So CI should be wider than z-based
        assert result.confidence_level == 0.95
        # CI width should be > 0 for all months
        widths = result.ci_upper - result.ci_lower
        assert np.all(widths > 0)

    def test_cv_and_skewness_computed(self):
        """CV and skewness should be present in result."""
        from hydrolog.statistics.characteristic import calculate_monthly_statistics

        rng = np.random.default_rng(42)
        dates = np.arange(
            np.datetime64("2010-11-01"),
            np.datetime64("2020-10-31"),
            dtype="datetime64[D]",
        )
        values = rng.uniform(5, 50, size=len(dates))
        result = calculate_monthly_statistics(values, dates)

        assert len(result.cv_values) == 12
        assert len(result.skewness_values) == 12
        assert np.all(result.cv_values > 0)  # CV always positive for positive data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/test_characteristic.py::TestCharacteristicValues -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `characteristic.py`**

Create `hydrolog/statistics/characteristic.py` with:
- `CharacteristicValues` dataclass (12 fields + period_years + parameter)
- `DailyStatistics` dataclass
- `MonthlyStatistics` dataclass (with cv_values, skewness_values, t-Student CI)
- `calculate_characteristic_values()` — groups by hydro year, computes annual max/mean/min, then max/mean/median/min of each series
- `calculate_daily_statistics()` — groups by hydro day-of-year
- `calculate_monthly_statistics()` — groups by month, uses `scipy.stats.t.ppf(1 - alpha/2, df=n-1)` for CI

Key implementation detail for CI:
```python
from scipy.stats import t as t_dist

t_val = t_dist.ppf(1 - (1 - confidence_level) / 2, df=count - 1)
ci_lower = np.maximum(0.0, mean_vals - t_val * std_vals / np.sqrt(count))
ci_upper = mean_vals + t_val * std_vals / np.sqrt(count)
```

Key implementation for CV and skewness:
```python
cv_values = std_vals / mean_vals  # coefficient of variation
# Fisher-Pearson skewness: n/((n-1)(n-2)) * sum((xi - mean)^3) / std^3
from scipy.stats import skew
skewness_values = np.array([skew(month_data) for month_data in monthly_groups])
```

Input validation:
```python
from hydrolog.exceptions import InvalidParameterError

if len(daily_values) == 0:
    raise InvalidParameterError("daily_values must not be empty")
if len(daily_values) != len(dates):
    raise InvalidParameterError(
        f"Array length mismatch: daily_values ({len(daily_values)}) "
        f"!= dates ({len(dates)})"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_characteristic.py -v`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```
feat(statistics): add characteristic values and monthly statistics
```

---

### Task 5: Mann-Kendall trend test (`stationarity.py`)

**Files:**
- Create: `hydrolog/statistics/stationarity.py`
- Create: `tests/unit/test_stationarity.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_stationarity.py`:

```python
"""Tests for Mann-Kendall trend test."""

import numpy as np
import pytest


class TestMannKendall:
    """Tests for mann_kendall_test function."""

    def test_increasing_trend_detected(self):
        """Clear increasing trend should be detected."""
        from hydrolog.statistics.stationarity import mann_kendall_test

        series = np.arange(1.0, 51.0)  # 1, 2, ..., 50
        result = mann_kendall_test(series)
        assert result.trend_detected is True
        assert result.trend_direction == "increasing"
        assert result.s_statistic > 0

    def test_decreasing_trend_detected(self):
        """Clear decreasing trend should be detected."""
        from hydrolog.statistics.stationarity import mann_kendall_test

        series = np.arange(50.0, 0.0, -1.0)
        result = mann_kendall_test(series)
        assert result.trend_detected is True
        assert result.trend_direction == "decreasing"
        assert result.s_statistic < 0

    def test_no_trend_in_random_data(self):
        """Random stationary data should (usually) not show trend."""
        from hydrolog.statistics.stationarity import mann_kendall_test

        rng = np.random.default_rng(42)
        series = rng.normal(100, 10, size=50)
        result = mann_kendall_test(series)
        assert result.trend_direction == "none"
        assert result.p_value > 0.05

    def test_variance_formula(self):
        """Var(S) = n(n-1)(2n+5)/18 for n=5."""
        from hydrolog.statistics.stationarity import mann_kendall_test

        series = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = mann_kendall_test(series)
        n = 5
        expected_var = n * (n - 1) * (2 * n + 5) / 18
        assert abs(result.var_s - expected_var) < 0.001

    def test_s_statistic_for_known_sequence(self):
        """S = number of concordant - discordant pairs."""
        from hydrolog.statistics.stationarity import mann_kendall_test

        # [1, 2, 3]: all pairs concordant → S = 3
        series = np.array([1.0, 2.0, 3.0])
        result = mann_kendall_test(series)
        assert result.s_statistic == 3.0

    def test_significance_level_stored(self):
        """Result stores the alpha used."""
        from hydrolog.statistics.stationarity import mann_kendall_test

        series = np.arange(1.0, 20.0)
        result = mann_kendall_test(series, alpha=0.01)
        assert result.significance_level == 0.01

    def test_empty_series_raises(self):
        """Empty series should raise InvalidParameterError."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            mann_kendall_test(np.array([]))

    def test_too_short_series_raises(self):
        """Series with < 3 values should raise InvalidParameterError."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            mann_kendall_test(np.array([1.0, 2.0]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/test_stationarity.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `stationarity.py`**

Create `hydrolog/statistics/stationarity.py` implementing `MannKendallResult` dataclass and `mann_kendall_test()` function using the formulas from the spec (Section 3.3):

```python
S = sum(sgn(x_j - x_i) for all i < j)
Var(S) = n*(n-1)*(2*n+5) / 18
U = (S-1)/sqrt(Var(S))  if S > 0, (S+1)/sqrt(Var(S)) if S < 0, 0 if S == 0
p_value = 2 * (1 - norm.cdf(abs(U)))
```

Use `scipy.stats.norm.cdf` for p-value computation.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_stationarity.py -v`
Expected: All 8 tests pass.

- [ ] **Step 5: Commit**

```
feat(statistics): add Mann-Kendall trend test (KZGW stationarity requirement)
```

---

### Task 6: Flood frequency analysis (`high_flows.py`)

**Files:**
- Create: `hydrolog/statistics/high_flows.py`
- Create: `tests/unit/test_high_flows.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_high_flows.py`:

```python
"""Tests for flood frequency analysis."""

import warnings

import numpy as np
import pytest
from scipy.stats import genextreme, lognorm, pearson3, weibull_min


class TestFloodFrequencyAnalysis:
    """Tests for FloodFrequencyAnalysis class."""

    @pytest.fixture
    def synthetic_gev_data(self):
        """Generate synthetic GEV data with known parameters."""
        rng = np.random.default_rng(42)
        return genextreme.rvs(c=-0.1, loc=100, scale=30, size=50, random_state=rng)

    @pytest.fixture
    def synthetic_lognorm_data(self):
        """Generate synthetic log-normal data."""
        rng = np.random.default_rng(42)
        return lognorm.rvs(s=0.5, loc=0, scale=50, size=50, random_state=rng)

    def test_fit_gev_returns_result(self, synthetic_gev_data):
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        ffa = FloodFrequencyAnalysis(synthetic_gev_data)
        result = ffa.fit_gev()
        assert result.distribution_name == "gev"
        assert len(result.quantiles) == len(result.return_periods)
        assert np.all(np.diff(result.quantiles) > 0)  # monotonic increasing

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
        """K-S test should flag as invalid when params estimated from data."""
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
        """fit_all results should be ordered by AIC (best first)."""
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

    def test_small_sample_warning(self):
        """Sample < 30 should emit KZGW warning."""
        from hydrolog.statistics.high_flows import FloodFrequencyAnalysis

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            FloodFrequencyAnalysis(np.arange(1.0, 21.0))  # n=20 < 30
            kzgw_warnings = [x for x in w if "KZGW" in str(x.message)]
            assert len(kzgw_warnings) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/test_high_flows.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `high_flows.py`**

Create `hydrolog/statistics/high_flows.py` with:
- `FrequencyAnalysisResult` dataclass (including ks_*, ad_*, aic fields)
- `FloodFrequencyAnalysis` class with constructor accepting `annual_maxima` and optional `return_periods`
- Methods: `fit_log_normal()`, `fit_gev()`, `fit_pearson3()`, `fit_weibull()`, `empirical_frequency()`, `fit_all()`
- Internal helper `_fit_distribution()` that handles the common pattern: fit → quantiles → K-S → A-D → AIC
- AIC: `2 * n_params - 2 * log_likelihood` where log_likelihood = `np.sum(dist.logpdf(data, *params))`
- Anderson-Darling: `scipy.stats.anderson(data, dist='norm')` — note: scipy.stats.anderson only supports a few named distributions; for others, compute manually or use the formula `A² = -n - Σ[(2i-1)/n * (ln(F(x_i)) + ln(1 - F(x_{n+1-i})))]`
- Warnings: KZGW 30-year, K-S validity

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_high_flows.py -v`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```
feat(statistics): add flood frequency analysis (GEV, LogNormal, Pearson III, Weibull)
```

---

### Task 7: Low-flow analysis (`low_flows.py`)

**Files:**
- Create: `hydrolog/statistics/low_flows.py`
- Create: `tests/unit/test_low_flows.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_low_flows.py`:

```python
"""Tests for low-flow frequency and drought sequence analysis."""

import numpy as np
import pytest


class TestLowFlowAnalysis:
    """Tests for LowFlowAnalysis class."""

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
        # Force known annual minima
        values[30] = 2.0   # year 2019 min
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

    def test_detect_sequences_finds_drought(self):
        """Known low-flow pattern should be detected."""
        from hydrolog.statistics.low_flows import LowFlowAnalysis

        dates = np.arange(
            np.datetime64("2020-11-01"),
            np.datetime64("2021-10-31"),
            dtype="datetime64[D]",
        )
        values = np.full(len(dates), 50.0)
        # Insert a 10-day drought
        values[100:110] = 3.0
        lfa = LowFlowAnalysis(values, dates)
        result = lfa.detect_sequences(threshold=10.0, min_duration_days=5)
        assert result.n_events == 1
        assert result.sequences[0].duration_days == 10

    def test_detect_sequences_merges_close_events(self):
        """Events separated by < max_gap_days should merge."""
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
        result = lfa.detect_sequences(threshold=10.0, min_duration_days=5, max_gap_days=4)
        assert result.n_events == 1  # merged into one event
        assert result.sequences[0].duration_days == 15

    def test_deficit_volume_computed(self):
        """Deficit volume = sum of (threshold - Q) for Q < threshold."""
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
        assert result.sequences[0].deficit_volume == pytest.approx(25.0)  # 5 * (10-5)

    def test_empty_data_raises(self):
        from hydrolog.statistics.low_flows import LowFlowAnalysis
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            LowFlowAnalysis(np.array([]), np.array([]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/test_low_flows.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `low_flows.py`**

Create `hydrolog/statistics/low_flows.py` with:
- `LowFlowFrequencyResult`, `LowFlowSequence`, `LowFlowAnalysisResult` dataclasses
- `LowFlowAnalysis` class with `annual_minima()`, `fit_fisher_tippett()`, `empirical_frequency()`, `detect_sequences()`
- Fisher-Tippett: `genextreme.fit(minima)`, `genextreme.ppf(p, ...)` (p directly, not 1-p)
- Sequence detection: vectorized NumPy — use `below_mask = flows < threshold`, then `np.diff` to find contiguous regions, merge gaps < max_gap_days

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_low_flows.py -v`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```
feat(statistics): add low-flow analysis (Fisher-Tippett, drought sequences)
```

---

### Task 8: Rating curve and water level frequency (`rating_curve.py`)

**Files:**
- Create: `hydrolog/hydrometrics/rating_curve.py`
- Create: `tests/unit/test_rating_curve.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_rating_curve.py`:

```python
"""Tests for rating curve and water level frequency."""

import numpy as np
import pytest


class TestRatingCurve:
    """Tests for RatingCurve class."""

    @pytest.fixture
    def synthetic_rating_data(self):
        """Q = 2.5 * (H - 50)^1.8 with noise."""
        rng = np.random.default_rng(42)
        h = np.linspace(60, 200, 50)
        q = 2.5 * (h - 50) ** 1.8 + rng.normal(0, 5, size=50)
        q = np.maximum(q, 0.1)
        return h, q

    def test_fit_recovers_parameters(self, synthetic_rating_data):
        from hydrolog.hydrometrics.rating_curve import RatingCurve

        h, q = synthetic_rating_data
        rc = RatingCurve(h, q)
        result = rc.fit(h0_initial=50.0)
        assert abs(result.a - 2.5) < 1.0
        assert abs(result.b - 1.8) < 0.3
        assert abs(result.h0 - 50.0) < 10.0
        assert result.r_squared > 0.95

    def test_predict_returns_correct_shape(self, synthetic_rating_data):
        from hydrolog.hydrometrics.rating_curve import RatingCurve

        h, q = synthetic_rating_data
        rc = RatingCurve(h, q)
        rc.fit(h0_initial=50.0)
        predicted = rc.predict(np.array([100.0, 150.0]))
        assert len(predicted) == 2
        assert np.all(predicted > 0)

    def test_outlier_removal(self, synthetic_rating_data):
        from hydrolog.hydrometrics.rating_curve import RatingCurve

        h, q = synthetic_rating_data
        q_with_outlier = q.copy()
        q_with_outlier[25] = q[25] * 10  # extreme outlier
        rc = RatingCurve(h, q_with_outlier)
        result = rc.fit(h0_initial=50.0, remove_outliers=True, outlier_std=2.0)
        assert result.n_outliers_removed >= 1

    def test_mismatched_lengths_raises(self):
        from hydrolog.hydrometrics.rating_curve import RatingCurve
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            RatingCurve(np.array([1.0, 2.0]), np.array([1.0]))

    def test_too_few_points_raises(self):
        from hydrolog.hydrometrics.rating_curve import RatingCurve
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            RatingCurve(np.array([1.0, 2.0]), np.array([1.0, 2.0]))


class TestWaterLevelFrequency:
    """Tests for WaterLevelFrequency class."""

    def test_frequency_distribution(self):
        from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency

        rng = np.random.default_rng(42)
        levels = rng.uniform(100, 300, size=1000)
        wlf = WaterLevelFrequency(levels, bin_width=20.0)
        result = wlf.frequency_distribution()
        assert abs(result.frequency_pct.sum() - 100.0) < 0.1
        assert result.cumulative_frequency_pct[-1] == pytest.approx(100.0, abs=0.1)

    def test_rybczynski_zones(self):
        from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency

        rng = np.random.default_rng(42)
        levels = rng.uniform(100, 300, size=1000)
        wlf = WaterLevelFrequency(levels, bin_width=10.0)
        zones = wlf.rybczynski_zones()
        assert zones.ntw_upper < zones.stw_upper
        assert zones.ntw_range[1] == zones.stw_range[0]
        assert zones.stw_range[1] == zones.wtw_range[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/test_rating_curve.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `rating_curve.py`**

Create `hydrolog/hydrometrics/rating_curve.py` with:
- `RatingCurveResult`, `WaterLevelZones`, `FrequencyDistributionResult` dataclasses
- `RatingCurve` class: `fit()` uses `scipy.optimize.curve_fit` for `Q = a * (H - h0)^b`; `predict()` evaluates fitted curve; outlier removal via residual threshold
- `WaterLevelFrequency` class: `frequency_distribution()` bins water levels; `rybczynski_zones()` finds NTW/STW/WTW boundaries

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_rating_curve.py -v`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```
feat(hydrometrics): add rating curve and water level frequency analysis
```

---

### Task 9: Module `__init__.py` wiring

**Files:**
- Modify: `hydrolog/statistics/__init__.py`
- Modify: `hydrolog/hydrometrics/__init__.py`

- [ ] **Step 1: Wire up `statistics/__init__.py`**

Update `hydrolog/statistics/__init__.py` with all imports and `__all__` as specified in the spec Section 7.2 and 7.4.

- [ ] **Step 2: Wire up `hydrometrics/__init__.py`**

Update `hydrolog/hydrometrics/__init__.py` with all imports and `__all__`.

- [ ] **Step 3: Verify imports work**

Run: `.venv/bin/python -c "from hydrolog.statistics import FloodFrequencyAnalysis, LowFlowAnalysis, mann_kendall_test, calculate_characteristic_values; print('OK')"`

Run: `.venv/bin/python -c "from hydrolog.hydrometrics import RatingCurve, WaterLevelFrequency; print('OK')"`

Expected: Both print "OK".

- [ ] **Step 4: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -x -q`
Expected: All tests pass (754 old + new tests).

- [ ] **Step 5: Commit**

```
feat: wire up statistics and hydrometrics module exports
```

---

### Task 10: Visualization (`visualization/statistics.py`)

**Files:**
- Create: `hydrolog/visualization/statistics.py`
- Modify: `hydrolog/visualization/__init__.py`
- Create: `tests/unit/test_visualization_statistics.py`

- [ ] **Step 1: Write smoke tests**

Create `tests/unit/test_visualization_statistics.py`:

```python
"""Smoke tests for statistics visualization functions."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest


class TestStatisticsVisualization:
    """Smoke tests — verify functions run without error and return Figure."""

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

    def test_plot_flow_histogram(self):
        from hydrolog.visualization.statistics import plot_flow_histogram

        rng = np.random.default_rng(42)
        fig = plot_flow_histogram(rng.uniform(10, 100, size=100))
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_monthly_statistics(self):
        from hydrolog.statistics.characteristic import calculate_monthly_statistics
        from hydrolog.visualization.statistics import plot_monthly_statistics

        rng = np.random.default_rng(42)
        dates = np.arange(
            np.datetime64("2010-11-01"),
            np.datetime64("2020-10-31"),
            dtype="datetime64[D]",
        )
        values = rng.uniform(5, 50, size=len(dates))
        stats = calculate_monthly_statistics(values, dates)
        fig = plot_monthly_statistics(stats)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/test_visualization_statistics.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `visualization/statistics.py`**

Create `hydrolog/visualization/statistics.py` with all 10 plotting functions following the pattern from `visualization/hydrograph.py`:
- Each function accepts `ax`, `figsize`, `title`
- Each returns `plt.Figure`
- Uses `styles.py` for colors and Polish labels

- [ ] **Step 4: Update `visualization/__init__.py`**

Add imports for the new plotting functions.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_visualization_statistics.py -v`
Expected: All smoke tests pass.

- [ ] **Step 6: Commit**

```
feat(visualization): add statistics and hydrometrics plots
```

---

### Task 11: Documentation updates

**Files:**
- Modify: `docs/SCOPE.md`
- Modify: `docs/PRD.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/IMPLEMENTATION_PROMPT.md`
- Modify: `docs/PROGRESS.md`

- [ ] **Step 1: Update SCOPE.md**

Add to Section 2.1:
- `2.1.9 Moduł statistics` — characteristic values, flood frequency, low-flow, Mann-Kendall
- `2.1.10 Moduł hydrometrics` — rating curve, water level frequency

Update module structure (3.1), roadmap (4) with v0.7.0, dependency table (6) — scipy as required.

- [ ] **Step 2: Update PRD.md**

Add user stories:
- US-S01: Calculate characteristic flow values
- US-S02: Flood frequency analysis
- US-S03: Low-flow frequency analysis and drought detection
- US-H01: Rating curve fitting
- US-H02: Water level frequency and Rybczyński zones

Add v0.7.0 to roadmap.

- [ ] **Step 3: Update CHANGELOG.md**

Add `[0.7.0]` section with all new classes, functions, and references.

- [ ] **Step 4: Update IMPLEMENTATION_PROMPT.md**

Add statistics/hydrometrics to module structure section.

- [ ] **Step 5: Update PROGRESS.md**

Add new session entry with completed tasks.

- [ ] **Step 6: Commit**

```
docs: update project docs for v0.7.0 (statistics, hydrometrics)
```

---

### Task 12: Final verification and version bump

**Files:**
- Modify: `hydrolog/__init__.py` (version)
- Modify: `pyproject.toml` (version)

- [ ] **Step 1: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short`
Expected: All tests pass (754 old + ~120 new ≈ 870+).

- [ ] **Step 2: Run coverage check**

Run: `.venv/bin/python -m pytest tests/ --cov=hydrolog --cov-report=term-missing | tail -30`
Expected: Overall coverage > 80%. New modules > 80%.

- [ ] **Step 3: Run Black formatting**

Run: `.venv/bin/python -m black hydrolog/statistics/ hydrolog/hydrometrics/ hydrolog/visualization/statistics.py tests/unit/test_characteristic.py tests/unit/test_stationarity.py tests/unit/test_high_flows.py tests/unit/test_low_flows.py tests/unit/test_rating_curve.py tests/unit/test_visualization_statistics.py`

- [ ] **Step 4: Run mypy**

Run: `.venv/bin/python -m mypy hydrolog/statistics/ hydrolog/hydrometrics/`

Fix any type errors.

- [ ] **Step 5: Bump version to 0.7.0**

Update `hydrolog/__init__.py` and `pyproject.toml` version to `0.7.0`.

- [ ] **Step 6: Commit**

```
chore: bump version to v0.7.0
```
