"""Shared dataclasses for statistics module."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin


@dataclass
class EmpiricalFrequency(JsonResultMixin):
    """Empirical frequency (plotting positions).

    For high flows: the values are sorted in descending order and the positions
    are *exceedance* probabilities (the largest value has the smallest one). For
    low flows use :class:`LowFlowEmpiricalFrequency`, whose positions are
    non-exceedance probabilities.

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


@dataclass
class LowFlowEmpiricalFrequency(JsonResultMixin):
    """Empirical non-exceedance frequency of low flows (plotting positions).

    The counterpart of :class:`EmpiricalFrequency` for a sample of minima. In a
    low-flow analysis the return period *T* belongs to the *non-exceedance*
    probability ``F = 1 / T`` (the flow is equalled or undercut once in *T*
    years; WMO No. 1029, 2009; Tallaksen and van Lanen, 2004), the convention of
    the fitted distribution (:class:`~hydrolog.statistics.LowFlowFrequencyResult`).
    So the values are sorted ascending and the smallest value, the deepest low
    flow, has the smallest probability and the longest return period.

    Parameters
    ----------
    values_ascending : NDArray[np.float64]
        Values sorted in ascending order (the smallest first).
    non_exceedance_probabilities : NDArray[np.float64]
        Non-exceedance probability *F* of each value: the share of years whose
        minimum is equal to or lower than the value. For the Weibull plotting
        position ``F = m / (n + 1)`` with rank ``m = 1`` for the smallest value.
    return_periods : NDArray[np.float64]
        Return period ``T = 1 / F`` [years] of each value, in the same sense as
        ``LowFlowFrequencyResult.return_periods``.
    """

    values_ascending: NDArray[np.float64]
    non_exceedance_probabilities: NDArray[np.float64]
    return_periods: NDArray[np.float64]


def _plotting_probabilities(n: int, method: str) -> NDArray[np.float64]:
    """Plotting-position probability of the ranks ``1 ... n`` (rank 1 = most extreme).

    Raises
    ------
    InvalidParameterError
        If ``method`` is not one of ``"weibull"``, ``"hazen"``, ``"cunnane"``.
    """
    from hydrolog.exceptions import InvalidParameterError

    ranks = np.arange(1, n + 1, dtype=np.float64)

    if method == "weibull":
        return ranks / (n + 1)
    if method == "hazen":
        return (ranks - 0.5) / n
    if method == "cunnane":
        return (ranks - 0.4) / (n + 0.2)
    raise InvalidParameterError(
        f"Unknown plotting position method: {method!r}. "
        f"Use 'weibull', 'hazen', or 'cunnane'."
    )


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

    Raises
    ------
    InvalidParameterError
        If method is not one of the supported options.

    References
    ----------
    Weibull (1939): P_i = i / (n+1)
    Hazen (1930): P_i = (i - 0.5) / n
    Cunnane (1978): P_i = (i - 0.4) / (n + 0.2)
    """
    sorted_vals = np.sort(values)[::-1]  # descending
    exceedance = _plotting_probabilities(len(sorted_vals), method)

    return EmpiricalFrequency(
        values_sorted=sorted_vals,
        exceedance_prob=exceedance,
        return_periods=1.0 / exceedance,
    )


def compute_non_exceedance_positions(
    values: NDArray[np.float64],
    method: str = "weibull",
) -> LowFlowEmpiricalFrequency:
    """Compute empirical non-exceedance plotting positions of a sample of minima.

    The values are sorted ascending and the ``m``-th smallest gets the
    non-exceedance probability ``F_m`` of the plotting position formula (the
    mirror image of :func:`compute_plotting_positions`, where the ``i``-th
    largest value gets the exceedance probability ``P_i``), and the return period
    ``T_m = 1 / F_m``.

    Parameters
    ----------
    values : NDArray[np.float64]
        Sample values (will be sorted ascending).
    method : str, optional
        Plotting position method, by default "weibull".
        Options: "weibull", "hazen", "cunnane".

    Returns
    -------
    LowFlowEmpiricalFrequency
        Ascending values with non-exceedance probabilities and return periods.

    Raises
    ------
    InvalidParameterError
        If method is not one of the supported options.

    References
    ----------
    Weibull (1939): F_m = m / (n+1)
    Hazen (1930): F_m = (m - 0.5) / n
    Cunnane (1978): F_m = (m - 0.4) / (n + 0.2)
    """
    ascending = np.sort(values)
    non_exceedance = _plotting_probabilities(len(ascending), method)

    return LowFlowEmpiricalFrequency(
        values_ascending=ascending,
        non_exceedance_probabilities=non_exceedance,
        return_periods=1.0 / non_exceedance,
    )
