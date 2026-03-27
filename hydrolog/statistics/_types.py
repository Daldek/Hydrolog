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
