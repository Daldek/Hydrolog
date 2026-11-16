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

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.signal import lfilter

__all__ = [
    "CascadeRun",
    "linear_reservoir_coefficients",
    "muskingum_coefficients",
    "route_linear_reservoir",
    "route_muskingum_cascade",
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


@dataclass(frozen=True)
class CascadeRun:
    """A hydrograph routed through equal Muskingum sub-reaches in series.

    Attributes
    ----------
    outflow : numpy.ndarray
        Outflow of the last sub-reach at every inflow ordinate.
    storage_start, storage_end : float
        Water held by all sub-reaches at the first and at the last ordinate, in the
        unit of ``flow * k`` (multiply by the seconds of the time unit for m3).
    storage_steady : float
        What they would hold at rest under the final inflow: ``count * k * I_last``.
    weights : tuple of float
        ``(c_current, c_previous, c_outflow)`` of one sub-reach.
    """

    outflow: NDArray[np.float64]
    storage_start: float
    storage_end: float
    storage_steady: float
    weights: tuple[float, float, float]


def route_muskingum_cascade(
    inflow: ArrayLike,
    k: float,
    x: float,
    dt: float,
    count: int,
    initial_outflow: float,
) -> CascadeRun:
    """Route an inflow through ``count`` equal Muskingum sub-reaches in series.

    Every sub-reach has the storage ``S = k [x I + (1 - x) O]`` with its own inflow
    ``I`` (the outflow of the one before it) and starts with ``initial_outflow``, so at
    the first ordinate all but the first are fed by it. The trapezoid continuity holds
    in every sub-reach, so the volume balance of the whole closes to rounding.

    Parameters
    ----------
    inflow : array_like
        Inflow ordinates at the step ``dt``, at least one.
    k : float
        Storage constant of ONE sub-reach, > 0 [same unit as ``dt``].
    x : float
        Weighting factor ``X``.
    dt : float
        Time step, > 0.
    count : int
        Number of sub-reaches, at least 1.
    initial_outflow : float
        Outflow of every sub-reach at the first ordinate.

    Returns
    -------
    CascadeRun
        The outflow, the storage at both ends and at rest, and the weights used.
    """
    values = np.asarray(inflow, dtype=np.float64)
    weights = muskingum_coefficients(k, x, dt)
    # junction[j] is the flow at the last ordinate entering sub-reach j + 1 (0: the
    # inflow itself), so sub-reach j + 1 holds k [x junction[j] + (1 - x) junction[j+1]]
    junction = np.empty(count + 1)
    junction[0] = values[-1]
    series = values
    for index in range(1, count + 1):
        series = three_point(series, *weights, initial_outflow)
        junction[index] = series[-1]
    # at the first ordinate every sub-reach but the first is fed by the initial outflow
    held = x * float(values[0]) + (1.0 - x) * initial_outflow
    first = k * (held + (count - 1) * initial_outflow)
    last = k * float(np.sum(x * junction[:-1] + (1.0 - x) * junction[1:]))
    return CascadeRun(series, first, last, count * k * float(values[-1]), weights)
