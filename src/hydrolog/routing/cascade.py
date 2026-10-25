r"""Cascade of linear reservoirs: the Nash and Kalinin-Milyukov routing model.

A reach is a series of ``n`` equal linear reservoirs, each with the storage ``S = K O``
(the Nash model of :class:`~hydrolog.runoff.NashIUH`; with the characteristic reach
length ``Q / (T S0 c)`` it is the Kalinin-Milyukov method). The response to a unit
impulse is the gamma density

.. math::
    u(t) = \frac{1}{K \Gamma(n)} \left(\frac{t}{K}\right)^{n-1} e^{-t/K}

with the mean delay ``n K`` and the variance ``n K^2``. ``n`` need not be whole.

The outflow is computed with this kernel and not with a recurrence, so no time step is
too long: there is no window of stable steps (ADR-0008) and no sub-step is added. The
inflow is its piecewise-linear interpolation between the ordinates, and the outflow at
an ordinate is the exact response to that inflow. With ``x = t / K``, ``a = dt / K``,
``P`` the regularised incomplete gamma function and ``Q = 1 - P``, the response to a
unit ramp is ``S2(x) = x P(n, x) - n P(n + 1, x)``, so the weight of the inflow ordinate
``m`` steps earlier is (:func:`cascade_weights`)

.. math::
    h_0 = \frac{S2(a)}{a}, \qquad
    h_m = \frac{S2((m+1)a) - 2 S2(m a) + S2((m-1)a)}{a}.

They are not negative and add up to one, so the outflow of a steady inflow is that
inflow. The code works with the integral of ``Q`` instead, ``V(x) = x - S2(x) =
x Q(n, x) + n P(n + 1, x)``, which tends to ``n`` and so loses no digits at large ``x``.
The outflow at the first ordinate is the initial outflow, which every reservoir holds
before the inflow starts. The storage of the cascade follows from continuity: it is the
water of the inflow that has not yet left (``K n I`` at rest).

Because the outflow between the ordinates is not a straight line, the trapezoid volume
of the outflow differs from its integral: ``balance_error_m3`` is the quadrature error
of the trapezoid rule, second order in the time step, and negligible when the outflow
is at rest at both ends of the series.
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from scipy.signal import oaconvolve
from scipy.special import gammainc, gammaincc

from hydrolog.routing._checks import one_complete_group, positive, whole_number
from hydrolog.routing.hydrograph import Hydrograph
from hydrolog.routing.reach import REACH_METHODS, Reach, ReachRun

__all__ = ["CascadeReach", "cascade_weights"]

_SECONDS_PER_MINUTE = 60.0
_METRES_PER_KM = 1000.0
_DIRECT_LIMIT = 4_000_000
"""Largest product of the lengths of two series that is convolved directly; a larger one
is convolved in blocks with the FFT."""

_STORAGE = ("k_min",)
_REACH = ("length_km", "celerity_m_per_s")


def _survival_integral(n: float, x: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return ``V(x)``, the integral of ``Q(n, y)`` from 0 to ``x``.

    ``V`` rises like ``x`` near 0 and tends to ``n``, the mean of the gamma density.
    """
    return np.asarray(x * gammaincc(n, x) + n * gammainc(n + 1.0, x), dtype=np.float64)


def _survival_moment(n: float, x: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return ``W(x)``, the integral of ``y Q(n, y)`` from 0 to ``x``.

    It tends to ``n (n + 1) / 2``.
    """
    return np.asarray(
        0.5 * x * x * gammaincc(n, x) + 0.5 * n * (n + 1.0) * gammainc(n + 2.0, x),
        dtype=np.float64,
    )


def _weights(integral: NDArray[np.float64], ratio: float) -> NDArray[np.float64]:
    """Weights from ``V`` at ``0, a, 2a, ..``: there is one fewer than the values."""
    weights = np.empty(len(integral) - 1)
    weights[0] = 1.0 - integral[1] / ratio
    weights[1:] = -(integral[2:] - 2.0 * integral[1:-1] + integral[:-2]) / ratio
    # a weight is not negative; what lies below zero is rounding of the difference
    return np.maximum(weights, 0.0)


def cascade_weights(n: float, step_ratio: float, count: int) -> NDArray[np.float64]:
    """Return the exact weights of a cascade of linear reservoirs.

    The outflow at ordinate ``j`` is ``sum_m h_m I_(j-m)`` for an inflow that is linear
    between the ordinates and held at the first one before it; the weights follow from
    the gamma kernel (see the module docstring).

    Parameters
    ----------
    n : float
        Number of reservoirs, > 0; need not be whole.
    step_ratio : float
        Time step over the storage constant of one reservoir, ``dt / K``, > 0.
    count : int
        Number of weights ``h_0 .. h_(count-1)``, at least 1.

    Returns
    -------
    numpy.ndarray
        The weights, not negative. They add up to 1 once ``count`` reaches past the
        tail of the kernel; ``sum(m h_m)`` is ``n / step_ratio`` then (the mean delay).

    Raises
    ------
    InvalidParameterError
        If an argument is out of range.

    Examples
    --------
    One reservoir and a step equal to its storage constant (``a = 1``): the first
    weights are ``1/e``, ``(1 - 1/e)^2`` and ``(1 - 1/e)^2 / e``:

    >>> cascade_weights(1.0, 1.0, 3).round(4).tolist()
    [0.3679, 0.3996, 0.147]
    """
    n = positive(n, "n")
    step_ratio = positive(step_ratio, "step_ratio")
    count = whole_number(count, "count")
    grid = step_ratio * np.arange(count + 1, dtype=np.float64)
    return _weights(_survival_integral(n, grid), step_ratio)


def _convolve(
    series: NDArray[np.float64], kernel: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Return the full convolution of two series."""
    if len(series) * len(kernel) <= _DIRECT_LIMIT:
        return np.convolve(series, kernel)
    return np.asarray(oaconvolve(series, kernel), dtype=np.float64)


@REACH_METHODS.register
class CascadeReach(Reach):
    """Route a hydrograph through a cascade of ``n`` equal linear reservoirs.

    Each reservoir has the storage ``S = K O``; the reach has the mean delay ``n K`` and
    the attenuation of its ``n`` (``n = 1`` is one reservoir, a large ``n`` a pure
    translation). The time scale is given either as the storage constant ``k_min`` of
    one reservoir, or as the length and the flood-wave celerity of the reach, which fix
    the travel time ``L / c = n K`` and so ``K = L / (n c)``. Kalinin and Milyukov take
    ``n`` as the reach length over the characteristic length ``Q / (T S0 c)``.

    The outflow is exact for the inflow interpolated linearly between the ordinates (the
    module docstring), for any time step, so the routing neither adds sub-reaches nor
    refines the step and never leaves the stable region. The initial outflow is the
    outflow of every reservoir at the first ordinate.

    Parameters
    ----------
    n : float
        Number of reservoirs, > 0; need not be whole.
    k_min : float, optional
        Storage constant of one reservoir [min], > 0.
    length_km : float, optional
        Length of the reach [km], > 0; with ``celerity_m_per_s``, instead of ``k_min``.
    celerity_m_per_s : float, optional
        Celerity of the flood wave [m/s], > 0; with ``length_km``.

    Raises
    ------
    InvalidParameterError
        If a value is not valid, or not exactly one of ``k_min`` and the pair
        ``length_km`` with ``celerity_m_per_s`` is given (``details.reason``
        ``one_of``).

    Examples
    --------
    Three reservoirs of 30 min (a delay of 90 min) and a time step of 30 min:

    >>> from hydrolog.routing import CascadeReach, Hydrograph
    >>> inflow = Hydrograph.from_step([0.0, 10.0, 40.0, 20.0, 0.0], 30.0)
    >>> result = CascadeReach(n=3, k_min=30.0).route(inflow)
    >>> result.parameters["lag_min"]
    90.0
    """

    model = "cascade"

    def __init__(
        self,
        n: float,
        *,
        k_min: float | None = None,
        length_km: float | None = None,
        celerity_m_per_s: float | None = None,
    ) -> None:
        """Create the element."""
        self.n = positive(n, "n")
        values = {
            "k_min": k_min,
            "length_km": length_km,
            "celerity_m_per_s": celerity_m_per_s,
        }
        given = [name for name, value in values.items() if value is not None]
        group = one_complete_group(given, (_STORAGE, _REACH), "The cascade")
        # the group check has shown which options are given: the casts only tell mypy
        self.length_km: float | None = None
        self.celerity_m_per_s: float | None = None
        if group == 0:
            self.k_min = positive(cast(float, k_min), "k_min")
        else:
            self.length_km = positive(cast(float, length_km), "length_km")
            self.celerity_m_per_s = positive(
                cast(float, celerity_m_per_s), "celerity_m_per_s"
            )
            travel_min = (
                self.length_km
                * _METRES_PER_KM
                / self.celerity_m_per_s
                / _SECONDS_PER_MINUTE
            )
            self.k_min = travel_min / self.n

    def options(self) -> dict[str, Any]:
        """Return the arguments that rebuild the element.

        The time scale is ``k_min``, or the ``length_km`` and ``celerity_m_per_s`` of
        the reach that fix it; the storage constant that follows from the latter is
        not an option.
        """
        options: dict[str, Any] = {"n": self.n}
        if self.length_km is not None and self.celerity_m_per_s is not None:
            options["length_km"] = self.length_km
            options["celerity_m_per_s"] = self.celerity_m_per_s
        else:
            options["k_min"] = self.k_min
        return options

    def _run(self, inflow: Hydrograph, initial_outflow_m3s: float) -> ReachRun:
        values = inflow.discharge_m3s
        count = len(values)
        n, k = self.n, self.k_min
        ratio = inflow.timestep_min / k
        start = initial_outflow_m3s

        # V at 0, a, .., N a; the weights and the average of the share that has left
        integral = _survival_integral(n, ratio * np.arange(count + 1, dtype=np.float64))
        weights = _weights(integral, ratio)
        released = np.asarray(
            gammainc(n, ratio * np.arange(count, dtype=np.float64)), dtype=np.float64
        )
        average = np.ones(count)
        average[1:] = 1.0 - np.diff(integral[:count]) / ratio

        # the kernel is nil beyond its tail: only the weights up to there are convolved
        # (and none when the water has not reached the end within the series)
        nonzero = np.flatnonzero(weights)
        support = int(nonzero[-1]) + 1 if len(nonzero) else 0
        response = np.zeros(count - 1)
        if support:
            response = _convolve(values[1:], weights[:support])[: count - 1]
        outflow = np.empty(count)
        outflow[0] = start
        outflow[1:] = (
            start * (1.0 - released[1:])
            + values[0] * (released[1:] - average[1:])
            + response
        )

        # storage at the last ordinate: the water of the inflow of each age that has not
        # left (survival function Q), segment by segment, plus what the initial state
        # still holds; V and W are constant beyond the tail, so older segments add
        # nothing
        limit = min(count, support + 3)
        ages = np.arange(limit, dtype=np.float64)
        moment = _survival_moment(n, ratio * ages)
        rise = np.diff(integral[:limit])
        newer = values[::-1][: limit - 1]
        older = values[::-1][1:limit]
        segments = newer * rise + (older - newer) / ratio * (
            np.diff(moment) - ages[:-1] * ratio * rise
        )
        held = start * (n - integral[count - 1])
        storage_end = k * (float(segments.sum()) + held)

        lag = n * k
        parameters = {
            "n": n,
            "k_min": k,
            "lag_min": lag,
            "timestep_over_k": ratio,
        }
        if self.length_km is not None and self.celerity_m_per_s is not None:
            parameters["length_km"] = self.length_km
            parameters["celerity_m_per_s"] = self.celerity_m_per_s
        return ReachRun(
            outflow_m3s=outflow,
            storage_start_m3=lag * start * _SECONDS_PER_MINUTE,
            storage_end_m3=storage_end * _SECONDS_PER_MINUTE,
            storage_steady_m3=lag * float(values[-1]) * _SECONDS_PER_MINUTE,
            parameters=parameters,
        )
