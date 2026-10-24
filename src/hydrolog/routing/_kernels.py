"""Recurrences shared by the routing models and the Clark unit hydrograph.

All routing schemes of this package that march in time are linear first-order
recurrences of the three-point form

.. math::
    O_t = c_0 I_t + c_1 I_{t-1} + c_2 O_{t-1}

(:func:`three_point`). The linear reservoir of the Clark IUH is one member of the family
(:func:`route_linear_reservoir`); the Muskingum scheme is another. They are evaluated
with :func:`scipy.signal.lfilter`, which gives the same values as the explicit loop to
rounding (a few units of 1e-16 relative) and does not loop in Python over long series.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.signal import lfilter

__all__ = [
    "linear_reservoir_coefficients",
    "muskingum_coefficients",
    "route_linear_reservoir",
    "three_point",
]


def three_point(
    inflow: ArrayLike,
    c_current: float,
    c_previous: float,
    c_outflow: float,
    initial_outflow: float,
) -> NDArray[np.float64]:
    """Run the three-point recurrence of a linear routing scheme.

    ``O[t] = c_current I[t] + c_previous I[t-1] + c_outflow O[t-1]`` for ``t >= 1``.

    Parameters
    ----------
    inflow : array_like
        Inflow ordinates ``I[0..n-1]`` at a regular step, at least one.
    c_current, c_previous, c_outflow : float
        Weights of ``I[t]``, ``I[t-1]`` and ``O[t-1]``; ``c_outflow`` must lie in
        ``(-1, 1)`` for the recurrence to be stable.
    initial_outflow : float
        ``O[0]``.

    Returns
    -------
    numpy.ndarray
        ``O[0..n-1]``, ``float64``, the same length as ``inflow``.
    """
    values = np.asarray(inflow, dtype=np.float64)
    state = np.array([initial_outflow - c_current * values[0]], dtype=np.float64)
    outflow, _ = lfilter([c_current, c_previous], [1.0, -c_outflow], values, zi=state)
    return np.asarray(outflow, dtype=np.float64)


def muskingum_coefficients(k: float, x: float, dt: float) -> tuple[float, float, float]:
    """Weights of the Muskingum scheme ``S = K [X I + (1 - X) O]``, trapezoid rule.

    Continuity ``(S_t - S_{t-1}) / dt = (I_t + I_{t-1} - O_t - O_{t-1}) / 2`` with the
    storage above gives the three-point recurrence with ``D = 2K(1 - X) + dt`` and

    * ``c_current = (dt - 2KX) / D``, the weight of ``I_t``;
    * ``c_previous = (dt + 2KX) / D``, the weight of ``I_{t-1}``;
    * ``c_outflow = (2K(1 - X) - dt) / D``, the weight of ``O_{t-1}``.

    The weights sum to 1 (a steady state is kept). They are all non-negative, which
    keeps a non-negative inflow non-negative, when ``|2KX| <= dt <= 2K(1 - X)``.

    Parameters
    ----------
    k : float
        Storage constant ``K`` [same unit as ``dt``], > 0.
    x : float
        Weighting factor ``X``; the classical range is 0 to 0.5, a negative value
        occurs in the Muskingum-Cunge scheme.
    dt : float
        Time step, > 0.

    Returns
    -------
    tuple of float
        ``(c_current, c_previous, c_outflow)``, the weights of ``I_t``, ``I_{t-1}``
        and ``O_{t-1}``.
    """
    total = 2.0 * k * (1.0 - x) + dt
    return (
        (dt - 2.0 * k * x) / total,
        (dt + 2.0 * k * x) / total,
        (2.0 * k * (1.0 - x) - dt) / total,
    )


def linear_reservoir_coefficients(k: float, dt: float) -> tuple[float, float, float]:
    """Weights of the linear reservoir ``S = K O`` with the trapezoid rule.

    ``O_t = O_{t-1} + C (I_t + I_{t-1} - 2 O_{t-1})`` with ``C = dt / (2K + dt)``. It is
    the three-point recurrence with ``c_current = c_previous = C`` and
    ``c_outflow = (2K - dt) / (2K + dt)``, the Muskingum scheme with ``X = 0``
    (:func:`muskingum_coefficients`). The last weight is negative when ``dt > 2K``.

    Parameters
    ----------
    k : float
        Storage constant ``K`` [same unit as ``dt``], > 0.
    dt : float
        Time step, > 0.

    Returns
    -------
    tuple of float
        ``(c_current, c_previous, c_outflow)``.
    """
    return muskingum_coefficients(k, 0.0, dt)


def route_linear_reservoir(
    inflow: ArrayLike, k: float, dt: float, initial_outflow: float = 0.0
) -> NDArray[np.float64]:
    """Route an inflow through one linear reservoir ``S = K O``.

    Parameters
    ----------
    inflow : array_like
        Inflow ordinates at the step ``dt``.
    k : float
        Storage constant ``K`` [same unit as ``dt``], > 0.
    dt : float
        Time step, > 0. The outflow stays non-negative for a non-negative inflow only
        when ``dt <= 2 K``.
    initial_outflow : float, optional
        Outflow at the first ordinate, by default 0.

    Returns
    -------
    numpy.ndarray
        Outflow ordinates, the same length as ``inflow``.
    """
    c_current, c_previous, c_outflow = linear_reservoir_coefficients(k, dt)
    return three_point(inflow, c_current, c_previous, c_outflow, initial_outflow)
