"""Homogeneity tests of a series of annual values: Mann-Whitney, K-S and Pettitt.

A flood frequency analysis takes the annual maxima as a sample of one
distribution; a change of the catchment or of the gauge (a reservoir, a
regulated reach, a moved station) breaks that. The Mann-Whitney U test and the
two-sample Kolmogorov-Smirnov test compare the values before and after a split
year; Pettitt's test finds the most probable change point itself (ADR-0022).

References
----------
Mann, H.B., Whitney, D.R. (1947). On a test of whether one of two random
    variables is stochastically larger than the other. Annals of
    Mathematical Statistics, 18, 50–60.
Smirnov, N.V. (1939). On the estimation of the discrepancy between empirical
    curves of distribution for two independent samples. Bulletin
    Mathématique de l'Université de Moscou, 2(2).
Pettitt, A.N. (1979). A non-parametric approach to the change-point problem.
    Applied Statistics, 28, 126–135.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.stats import ks_2samp, mannwhitneyu, rankdata

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import CalculationError, InvalidParameterError

_MIN_VALUES = 3
"""Fewest values the tests take (as the Mann-Kendall test)."""


@dataclass
class TwoSampleTestResult(JsonResultMixin):
    """Result of a test that compares the two parts of the split series.

    Attributes
    ----------
    statistic : float
        Statistic of the test.
    p_value : float
        Two-sided p-value of the null hypothesis that both parts come from one
        distribution.
    homogeneous : bool
        True when ``p_value`` is not below the significance level (the test
        does not reject homogeneity).
    """

    statistic: float
    p_value: float
    homogeneous: bool


@dataclass
class PettittResult(JsonResultMixin):
    """Result of Pettitt's change-point test.

    Attributes
    ----------
    statistic : float
        K, the largest ``|U_t|`` over the splits ``t = 1, ..., n - 1``.
    p_value : float
        Approximate two-sided p-value ``2·exp(−6K²/(n³ + n²))``, at most 1.
    homogeneous : bool
        True when ``p_value`` is not below the significance level (the test
        does not reject homogeneity).
    change_point_index : int
        The split ``t`` of K (the first if several give K): the number of values
        before the change, i.e. the 0-based index of the first value after it.
    change_point_year : int or None
        Year of the first value after the change; ``None`` without years.
    """

    statistic: float
    p_value: float
    homogeneous: bool
    change_point_index: int
    change_point_year: int | None


@dataclass
class HomogeneityResult(JsonResultMixin):
    """Result of the homogeneity tests of a series.

    Attributes
    ----------
    n_years : int
        Number of values of the series (one a year).
    split_index : int
        Number of values of the first part, i.e. the 0-based index of the first
        value of the second part.
    split_year : int or None
        Year of the first value of the second part; ``None`` without years.
    mann_whitney : TwoSampleTestResult
        Mann-Whitney U test of the two parts; the statistic is U of the first
        part (about ``n1·n2/2`` under homogeneity, 0 when every value of the
        first part is smaller than every value of the second).
    kolmogorov_smirnov : TwoSampleTestResult
        Two-sample Kolmogorov-Smirnov test of the two parts; the statistic is the
        largest distance D between their empirical distribution functions.
    pettitt : PettittResult
        Pettitt's change-point test of the whole series.
    significance_level : float
        Alpha level used for the decisions ``homogeneous``.
    """

    n_years: int
    split_index: int
    split_year: int | None
    mann_whitney: TwoSampleTestResult
    kolmogorov_smirnov: TwoSampleTestResult
    pettitt: PettittResult
    significance_level: float


def homogeneity_tests(
    series: NDArray[np.floating],
    years: NDArray[np.integer] | None = None,
    *,
    split_year: int | None = None,
    alpha: float = 0.05,
) -> HomogeneityResult:
    """Test a series of annual values for homogeneity.

    Splits the series in two and compares the parts with the Mann-Whitney U
    test and the two-sample Kolmogorov-Smirnov test (both two-sided, scipy's
    ``mannwhitneyu`` and ``ks_2samp``), and looks for the most probable change
    point with Pettitt's test (ADR-0022).

    Parameters
    ----------
    series : NDArray[np.floating]
        1-D array of the values in time order, e.g. annual maxima [m3/s]; at
        least 3, not all equal.
    years : NDArray[np.integer] or None, optional
        Year of every value: integers, strictly increasing (gaps allowed).
        Needed for ``split_year``; without them the result gives no years.
    split_year : int or None, optional
        First year of the second part: the values of the years before it form
        the first part. It need not be a year of the series but must leave a
        value in each part. By default the first part is the first ``n // 2``
        values.
    alpha : float, optional
        Significance level of the decisions ``homogeneous`` (default 0.05).

    Returns
    -------
    HomogeneityResult
        The split and the statistic, p-value and decision of each test.

    Raises
    ------
    InvalidParameterError
        If a value is not a finite number (``details.reason`` ``not_finite``);
        if ``years`` are not integers, not one per value or not strictly
        increasing (``type``, ``length_mismatch``, ``not_increasing``); if
        ``split_year`` is given without ``years`` (``option`` ``years``,
        ``required``) or leaves a part empty (``option`` ``split_year``,
        ``range``, with ``minimum`` and ``maximum``).
    CalculationError
        If there are fewer than 3 values (``too_few_values``, with ``count`` and
        ``minimum``) or all values are equal (``constant_values``).

    Notes
    -----
    Mann-Whitney's p-value is exact when a part has at most 8 values and there
    are no ties, otherwise it comes from the normal approximation with the
    corrections for ties and continuity. Pettitt's statistic is
    ``K = max |U_t|`` with ``U_t = Σ_{i≤t} Σ_{j>t} sgn(x_i − x_j)``, computed
    from the ranks ``r_i`` (mid-ranks for ties) as
    ``U_t = 2 Σ_{i≤t} r_i − t(n + 1)``; its p-value
    ``2·exp(−6K²/(n³ + n²))`` is good for ``p ≤ 0.5`` and is capped at 1. The
    change point is given like the split, by the first value after the
    change, so ``split_year=result.pettitt.change_point_year`` makes the
    two-sample tests compare the parts Pettitt's test found.
    A test is ``homogeneous`` when ``p_value >= alpha``.

    Examples
    --------
    >>> import numpy as np
    >>> from hydrolog.statistics import homogeneity_tests
    >>> maxima = np.array([52.0, 48.0, 55.0, 50.0, 47.0, 81.0, 86.0, 79.0, 90.0, 84.0])
    >>> result = homogeneity_tests(maxima, np.arange(2001, 2011))
    >>> result.split_year, result.pettitt.change_point_year
    (2006, 2006)
    >>> result.mann_whitney.homogeneous, result.pettitt.homogeneous
    (False, True)
    """
    values = np.asarray(series, dtype=float)
    broken = ~np.isfinite(values)
    if broken.any():
        index = int(np.argmax(broken))
        raise InvalidParameterError(
            f"series[{index}] is not a finite number",
            details={"option": "series", "reason": "not_finite", "index": index},
        )
    n = int(values.size)
    labels = _checked_years(years, n)
    if n < _MIN_VALUES:
        raise CalculationError(
            f"The homogeneity tests need at least {_MIN_VALUES} values, got {n}",
            details={"reason": "too_few_values", "count": n, "minimum": _MIN_VALUES},
            hint="Provide a longer series.",
        )
    split = _split_index(labels, n, split_year)
    if values.min() == values.max():
        raise CalculationError(
            f"All {n} values of the series are equal: the homogeneity tests have "
            "nothing to compare",
            details={"reason": "constant_values"},
        )

    first, second = values[:split], values[split:]
    mann_whitney = mannwhitneyu(first, second, alternative="two-sided")
    kolmogorov_smirnov = ks_2samp(first, second, alternative="two-sided")
    k, p_value, change = _pettitt(values)
    return HomogeneityResult(
        n_years=n,
        split_index=split,
        split_year=None if labels is None else int(labels[split]),
        mann_whitney=_decided(
            float(mann_whitney.statistic), float(mann_whitney.pvalue), alpha
        ),
        kolmogorov_smirnov=_decided(
            float(kolmogorov_smirnov.statistic),
            float(kolmogorov_smirnov.pvalue),
            alpha,
        ),
        pettitt=PettittResult(
            statistic=k,
            p_value=p_value,
            homogeneous=p_value >= alpha,
            change_point_index=change,
            change_point_year=None if labels is None else int(labels[change]),
        ),
        significance_level=alpha,
    )


def _checked_years(
    years: NDArray[np.integer] | None, n: int
) -> NDArray[np.integer] | None:
    """Check the years: integers, one per value, strictly increasing."""
    if years is None:
        return None
    labels = np.asarray(years)
    if not np.issubdtype(labels.dtype, np.integer):
        raise InvalidParameterError(
            f"years must be integers, got {labels.dtype} values",
            details={"option": "years", "reason": "type", "expected": "integer"},
        )
    if labels.shape != (n,):
        raise InvalidParameterError(
            f"{labels.size} years for {n} values",
            details={
                "option": "years",
                "reason": "length_mismatch",
                "years": int(labels.size),
                "values": n,
            },
        )
    backwards = np.diff(labels) <= 0
    if backwards.any():
        index = int(np.argmax(backwards)) + 1
        raise InvalidParameterError(
            f"years must increase strictly; years[{index}] = {labels[index]} does "
            f"not follow {labels[index - 1]}",
            details={"option": "years", "reason": "not_increasing", "index": index},
        )
    return labels


def _split_index(
    labels: NDArray[np.integer] | None, n: int, split_year: int | None
) -> int:
    """Count the values of the first part: the halves or the years before the split."""
    if split_year is None:
        return n // 2
    if labels is None:
        raise InvalidParameterError(
            "split_year needs the years of the values",
            details={"option": "years", "reason": "required"},
            hint=(
                "Give the years, or leave out split_year to split the series into "
                "halves."
            ),
        )
    split = int(np.count_nonzero(labels < split_year))
    if 0 < split < n:
        return split
    first, last = int(labels[0]), int(labels[-1])
    part = "first" if split == 0 else "second"
    raise InvalidParameterError(
        f"split_year {split_year} leaves the {part} part empty: the years run from "
        f"{first} to {last}",
        details={
            "option": "split_year",
            "reason": "range",
            "value": str(split_year),
            "minimum": first + 1,
            "maximum": last,
        },
        hint=f"Give a split_year from {first + 1} to {last}.",
    )


def _pettitt(values: NDArray[np.float64]) -> tuple[float, float, int]:
    """Compute Pettitt's K, its approximate p-value and the change point ``t`` of K."""
    n = values.size
    t = np.arange(1, n)
    u = 2.0 * np.cumsum(rankdata(values))[:-1] - t * (n + 1.0)
    best = int(np.argmax(np.abs(u)))
    k = float(abs(u[best]))
    p_value = min(1.0, 2.0 * math.exp(-6.0 * k * k / (float(n) ** 3 + float(n) ** 2)))
    return k, p_value, best + 1


def _decided(statistic: float, p_value: float, alpha: float) -> TwoSampleTestResult:
    """Decide a two-sample test at ``alpha``."""
    return TwoSampleTestResult(
        statistic=statistic, p_value=p_value, homogeneous=p_value >= alpha
    )
