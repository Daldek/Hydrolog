r"""Linear reservoirs in series, declared by the spec ``linear_reservoir_cascade``.

:data:`LINEAR_RESERVOIR_CASCADE` declares the routing of a hydrograph through ``n``
equal linear reservoirs in series, each with the storage ``S = K O`` (Nash 1957; the
Kalinin-Milyukov method), and :func:`cascade_route` computes it.
:class:`~hydrolog.routing.CascadeReach` takes ``K`` or the length and celerity of a
reach and extends the time axis (ADR-0008), then routes through it. ``docs/FORMULAS.md``
shows the equation, the ranges and the sources (ADR-0061).

The response to a unit impulse is the gamma density

.. math::
    u(t) = \frac{1}{K \Gamma(n)} \left(\frac{t}{K}\right)^{n-1} e^{-t/K}

with the mean (the delay of the centroid) ``n K`` and the variance ``n K^2``; its peak
comes at ``(n - 1) K`` for ``n >= 1``. ``n`` need not be whole.

The outflow is computed with this kernel and not with a recurrence, so no time step is
too long: there is no window of stable steps and no sub-step. The inflow is linear
between the ordinates, and the outflow at an ordinate is the exact response to it. With
``x = t / K``, ``a = dt / K``, ``P`` the regularised incomplete gamma function and
``Q = 1 - P``, the response to a unit ramp is ``S2(x) = x P(n, x) - n P(n + 1, x)``, so
the weight of the inflow ordinate ``m`` steps earlier is (:func:`hat_weights`)

.. math::
    h_0 = \frac{S2(a)}{a}, \qquad
    h_m = \frac{S2((m+1)a) - 2 S2(m a) + S2((m-1)a)}{a}.

They are not negative and add up to one, so the outflow of a steady inflow is that
inflow. The code works with the integral of ``Q`` instead, ``V(x) = x - S2(x) =
x Q(n, x) + n P(n + 1, x)``, which tends to ``n`` and so loses no digits at large ``x``.
The outflow at the first ordinate is the initial outflow, which every reservoir holds
before the inflow starts. The storage of the cascade follows from continuity: it is the
water of the inflow that has not yet left (``n K I`` at rest).

Because the outflow between the ordinates is not a straight line, the trapezoid volume
of the outflow differs from its integral by the quadrature error of the trapezoid rule,
second order in the time step and negligible when the outflow is at rest at both ends
of the series.

Examples
--------
Two reservoirs of 30 min, a step of 30 min and an inflow of 1 m3/s from the first
ordinate into a dry cascade: the outflow is the step response ``P(2, t / K)``:

>>> run = cascade_route([1.0] * 4, 30.0, 2.0, 30.0, 0.0)
>>> run.outflow_m3s.round(6).tolist()
[0.0, 0.264241, 0.593994, 0.800852]
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import expm
from scipy.signal import oaconvolve
from scipy.special import gammainc, gammaincc

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog.nogat_formulas import (
    Conservation,
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Properties,
    Range,
    Scaling,
    Source,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.routing.formulas._shared import (
    ROUTING_TESTS,
    SECONDS_PER_MINUTE,
    inflow,
    initial_outflow,
    outflow,
    ponce,
    storage,
    timestep,
    volume_m3,
)

__all__ = [
    "LINEAR_RESERVOIR_CASCADE",
    "SPECS",
    "CascadeRoute",
    "cascade_route",
    "hat_weights",
]

_SMALLEST_NORMAL: Final = float(np.finfo(np.float64).tiny)
"""The smallest normal float64, the least scale of a volume in the conservation law."""

_DIRECT_LIMIT = 4_000_000
"""Largest product of the lengths of two series that is convolved directly; a larger one
is convolved in blocks with the FFT."""


@dataclass(frozen=True)
class CascadeRoute:
    """A hydrograph routed by the spec ``linear_reservoir_cascade``.

    Attributes
    ----------
    outflow_m3s : numpy.ndarray
        Outflow of the last reservoir at every inflow ordinate [m3/s].
    storage_start_m3, storage_end_m3 : float
        Water held by all reservoirs at the first and at the last ordinate [m3].
    storage_steady_m3 : float
        What they would hold at rest under the last inflow ordinate, ``n K I`` [m3].
    """

    outflow_m3s: NDArray[np.float64]
    storage_start_m3: float
    storage_end_m3: float
    storage_steady_m3: float


# --- the computation -----------------------------------------------------------------


def _survival_integral(n: float, x: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return ``V(x)``, the integral of ``Q(n, y)`` from 0 to ``x``.

    ``V`` rises like ``x`` near 0 and tends to ``n``, the mean of the gamma density.
    """
    return np.asarray(x * gammaincc(n, x) + n * gammainc(n + 1.0, x), dtype=np.float64)


def _survival_moment(n: float, x: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return ``W(x)``, the integral of ``y Q(n, y)`` from 0 to ``x``.

    It tends to ``n (n + 1) / 2``; ``x (x Q)`` stays finite where ``x^2`` would not.
    """
    return np.asarray(
        0.5 * x * (x * gammaincc(n, x)) + 0.5 * n * (n + 1.0) * gammainc(n + 2.0, x),
        dtype=np.float64,
    )


def _weights(integral: NDArray[np.float64], ratio: float) -> NDArray[np.float64]:
    """Weights from ``V`` at ``0, a, 2a, ..``: there is one fewer than the values."""
    weights = np.empty(len(integral) - 1)
    weights[0] = 1.0 - integral[1] / ratio
    weights[1:] = -(integral[2:] - 2.0 * integral[1:-1] + integral[:-2]) / ratio
    # a weight is not negative; what lies below zero is rounding of the difference
    return np.maximum(weights, 0.0)


def hat_weights(n: float, step_ratio: float, count: int) -> NDArray[np.float64]:
    """Return the weights of the inflow ordinates in the spec linear_reservoir_cascade.

    The outflow at an ordinate is the sum of each earlier inflow ordinate times the
    weight of its age in steps, for an inflow linear between the ordinates (the module
    docstring). The arguments are not checked:
    :func:`hydrolog.routing.cascade_weights` checks them for its callers.

    Parameters
    ----------
    n : float
        Number of reservoirs, above zero; need not be whole.
    step_ratio : float
        Time step over the storage constant of one reservoir.
    count : int
        Number of weights, from the age of no step on.

    Returns
    -------
    numpy.ndarray
        The weights, not negative.
    """
    grid = step_ratio * np.arange(count + 1, dtype=np.float64)
    return _weights(_survival_integral(n, grid), step_ratio)


def _convolve(
    series: NDArray[np.float64], kernel: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Return the full convolution of two series."""
    if len(series) * len(kernel) <= _DIRECT_LIMIT:
        return np.convolve(series, kernel)
    return np.asarray(oaconvolve(series, kernel), dtype=np.float64)


def _representable(x: Values) -> bool:
    """Whether ``n``, the grid ``m dt / K`` and the storages are normal float64."""
    values = x.array("inflow_m3s")
    ratio = x.real("timestep_min") / x.real("k_min")
    largest = max(float(values.max()), x.real("initial_outflow_m3s"))
    held = x.real("n") * x.real("k_min") * largest * SECONDS_PER_MINUTE
    return (
        x.real("n") >= _SMALLEST_NORMAL
        and ratio > 0.0
        and ratio * values.size < math.inf
        and largest / ratio < math.inf
        and held < math.inf
    )


def _route(x: Values) -> dict[str, object]:
    values = x.array("inflow_m3s")
    count = len(values)
    n, k = x.real("n"), x.real("k_min")
    ratio = x.real("timestep_min") / k
    start = x.real("initial_outflow_m3s")

    # V at 0, a, .., N a; the weights and the average of the share that has left
    integral = _survival_integral(n, ratio * np.arange(count + 1, dtype=np.float64))
    weights = _weights(integral, ratio)
    # P <= 1; SciPy's gammainc exceeds it by up to 2e-14 for a shape near zero
    released = np.minimum(
        gammainc(n, ratio * np.arange(count, dtype=np.float64)), 1.0, dtype=np.float64
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
    out = np.empty(count)
    out[0] = start
    out[1:] = (
        start * (1.0 - released[1:])
        # P at the ordinate is not below its mean over the step before: what lies
        # below zero is rounding of the cancelling difference
        + values[0] * np.maximum(released[1:] - average[1:], 0.0)
        + response
    )

    # storage at the last ordinate: the water of the inflow of each age that has not
    # left (survival function Q), segment by segment, plus what the initial state
    # still holds. Every age counts: a segment older than the tail adds nothing, but
    # one whose weights are still nil has released nothing yet
    ages = np.arange(count, dtype=np.float64)
    moment = _survival_moment(n, ratio * ages)
    rise = np.diff(integral[:count])
    newer = values[::-1][:-1]
    older = values[::-1][1:]
    segments = newer * rise + (older - newer) / ratio * (
        np.diff(moment) - ages[:-1] * ratio * rise
    )
    # what a segment holds and V <= n are not negative; below zero is rounding
    held = start * max(n - float(integral[count - 1]), 0.0)
    storage_end = k * (float(np.maximum(segments, 0.0).sum()) + held)

    lag = n * k
    return {
        # every term is a discharge times a non-negative share: what lies below zero
        # is rounding of the share P - average, which cancels, or of the FFT
        "outflow_m3s": np.maximum(out, 0.0),
        "storage_start_m3": lag * start * SECONDS_PER_MINUTE,
        "storage_end_m3": storage_end * SECONDS_PER_MINUTE,
        "storage_steady_m3": lag * float(values[-1]) * SECONDS_PER_MINUTE,
    }


def _quadrature_kept(x: Values, out: Values) -> float:
    """Return the imbalance beyond the bound of the trapezoid's error, over the volume.

    The outflow is the gamma density convolved with the inflow, which is ``O0`` before
    the first ordinate and linear after it; the trapezoid's error is linear in the
    function, so it is the density's mean of the error for the inflow shifted by each
    delay. For one shift, a jump ``J = I[0] - O0`` inside a step errs by at most
    ``|J| dt / 2``, and the kinks of the inflow by ``f (1 - f) dt / 2`` times the change
    of slope across the window (the kinks' errors telescope), at most ``dt / 4`` times
    the largest change of the inflow over a step.
    """
    values = x.array("inflow_m3s")
    step = x.real("timestep_min")
    entered = volume_m3(values, step)
    left = volume_m3(out.array("outflow_m3s"), step)
    start, end = out.real("storage_start_m3"), out.real("storage_end_m3")
    jump = abs(float(values[0]) - x.real("initial_outflow_m3s"))
    change = float(np.max(np.abs(np.diff(values))))
    bound = (0.5 * jump + 0.25 * change) * step * SECONDS_PER_MINUTE
    # the smallest normal number keeps subnormal volumes, which round to fewer digits,
    # from counting as imbalance
    scale = max(entered, left, start, end, bound, _SMALLEST_NORMAL)
    excess = max(abs(entered - left - (end - start)) - bound, 0.0)
    return excess / scale


# --- oracles and limits (CMP-6.2, CMP-6.5) -------------------------------------------

_STEP_POINTS: Final = (
    # n, K, dt, initial outflow, inflow, ordinates
    (2.0, 30.0, 30.0, 0.0, 1.0, 7),
    (3.4, 20.0, 5.0, 2.0, 5.0, 60),
    (0.4, 12.0, 7.0, 9.0, 1.5, 40),
    (25.0, 4.0, 3.0, 1.0, 0.0, 80),
)
"""Steady inflows into a cascade at rest at another outflow."""


def _step_response(run: Callable[..., Values]) -> None:
    for n, k_min, step, start, level, size in _STEP_POINTS:
        out = run(
            inflow_m3s=[level] * size,
            timestep_min=step,
            n=n,
            k_min=k_min,
            initial_outflow_m3s=start,
        ).array("outflow_m3s")
        released = gammainc(n, step * np.arange(size) / k_min)
        assert_within(
            out,
            start + (level - start) * released,
            rel=1e-13,
            abs=1e-14,
            reason="the step response of the cascade is P(n, t / K), SciPy's "
            "gammainc (regularised lower incomplete gamma, same argument order); the "
            "code reaches it through differences of V that telescope to it, a few "
            "roundings of 1e-16 per weight over at most 80 ordinates",
        )


_CHAIN_POINTS: Final = (
    # n, K, dt, initial outflow, seed
    (1, 30.0, 10.0, 0.0, 1),
    (2, 10.0, 30.0, 3.0, 2),
    (3, 40.0, 2.0, 0.0, 3),
    (5, 5.0, 60.0, 3.0, 4),
)
"""Whole cascades for the matrix exponential, with seeded rough inflows."""


def _chain(
    n: int, k_min: float, step: float, values: NDArray[np.float64], start: float
) -> tuple[NDArray[np.float64], float]:
    """Return the outflow and the storage [m3] of the linear ODEs of the chain."""
    size = n + 2
    matrix = np.zeros((size, size))
    for i in range(n):
        matrix[i, i] = -1.0 / k_min
        matrix[i, i - 1 if i else n] = 1.0 / k_min
    state = np.zeros(size)
    state[:n] = start
    out = [start]
    for before, after in zip(values[:-1], values[1:], strict=True):
        propagator = matrix.copy()
        propagator[n, n + 1] = (after - before) / step
        state[n], state[n + 1] = before, 1.0
        state = expm(propagator * step) @ state
        out.append(float(state[n - 1]))
    return np.array(out), k_min * float(state[:n].sum()) * SECONDS_PER_MINUTE


def _matrix_exponential(run: Callable[..., Values]) -> None:
    for n, k_min, step, start, seed in _CHAIN_POINTS:
        values = np.abs(np.random.default_rng(seed).normal(10.0, 6.0, 40))
        got = run(
            inflow_m3s=values,
            timestep_min=step,
            n=float(n),
            k_min=k_min,
            initial_outflow_m3s=start,
        )
        exact, held = _chain(n, k_min, step, values, start)
        assert_within(
            [*got.array("outflow_m3s"), got.real("storage_end_m3")],
            [*exact, held],
            rel=1e-10,
            reason="dO_i/dt = (O_(i-1) - O_i) / K with the inflow linear over a step "
            "solved by SciPy's expm (Pade approximant of order 13, relative error "
            "near 1e-15 per step) over 40 steps against the gamma kernel; the "
            "storage is K times the sum of the states",
        )


_MOMENT_POINTS: Final = ((2.5, 10.0, 1.0), (1.5, 40.0, 4.0), (6.0, 3.0, 0.25))
"""(n, K, dt) of the responses to a unit hat whose moments are checked."""


def _moments(run: Callable[..., Values]) -> None:
    for n, k_min, step in _MOMENT_POINTS:
        size = int((n + 30.0 * math.sqrt(n) + 40.0) * k_min / step)
        hat = np.zeros(size)
        hat[1] = 1.0
        out = run(
            inflow_m3s=hat,
            timestep_min=step,
            n=n,
            k_min=k_min,
            initial_outflow_m3s=0.0,
        ).array("outflow_m3s")
        delay = step * (np.arange(size, dtype=np.float64) - 1.0)
        mass = math.fsum(out.tolist())
        mean = math.fsum((delay * out).tolist()) / mass
        variance = math.fsum(((delay - mean) ** 2 * out).tolist()) / mass
        assert_within(
            [mass, mean],
            [1.0, n * k_min],
            rel=1e-10,
            reason="the weights of the hats add up to one and reproduce a straight "
            "line, so the mass and the mean delay n K of the response to a hat are "
            "exact but for rounding: the second differences of V lose digits like "
            "1e-16 (K / dt)^2 each, over up to 1,433 weights (3e-12 measured); the "
            "tail beyond 30 standard deviations is below 1e-30",
        )
        assert_within(
            variance,
            n * k_min**2 + step**2 / 6.0,
            rel=5e-6,
            reason="the hats add f (1 - f) dt^2 to the second moment of a delay whose "
            "fraction of a step is f; f (1 - f) = 1/6 - sum cos(2 pi j f) / (pi j)^2, "
            "so under the gamma density its mean differs from 1/6 by at most "
            "|phi| / 6, phi = (1 + (2 pi K / dt)^2)^(-n / 2): 2.2e-6 of the variance "
            "at n = 1.5, K = 10 dt (1.05e-6 measured)",
        )


def _bounded(run: Callable[..., Values]) -> None:
    for n, k_min, step, start, seed in _CHAIN_POINTS:
        values = np.abs(np.random.default_rng(seed).normal(10.0, 6.0, 40))
        out = run(
            inflow_m3s=values,
            timestep_min=step,
            n=float(n) + 0.5,
            k_min=k_min,
            initial_outflow_m3s=start,
        ).array("outflow_m3s")
        low = min(float(values.min()), start)
        high = max(float(values.max()), start)
        slack = 64 * np.spacing(high)
        if not ((out >= low - slack).all() and (out <= high + slack).all()):
            raise AssertionError(
                f"linear_reservoir_cascade: outflow {out} leaves [{low}, {high}], the "
                "range of the inflow and the initial outflow, though non-negative "
                "weights that add up to one make every ordinate a weighted mean of them"
            )


# --- the spec ------------------------------------------------------------------------

_NASH = Source(
    citation="Nash, J.E. (1957). The form of the instantaneous unit hydrograph, IAHS "
    "Publication 45, 114-121",
    locator="the cascade of n equal linear reservoirs and its gamma impulse response",
    access="author-provided",
)
_PONCE = ponce(
    "the Nash cascade and the Kalinin-Milyukov method: n reservoirs of S = K O in "
    "series, impulse response of mean n K"
)
_FLOAT64 = Source(
    citation="IEEE 754 binary64, the float64 of NumPy: largest finite number "
    "1.8e308, smallest normal 2.2e-308; SciPy's scipy.special.gammainc and gammaincc "
    "(1.18.1) give P(a, x) = 0 and Q(a, x) <= 0 for a subnormal shape a",
    locator="x = m dt / K on the grid of the ordinates, the inflow over dt / K, the "
    "storage n K I, and n as the shape of P and Q",
)
_EXACT_SCALING = Tolerance(
    rel=0.0,
    abs=1e-300,
    reason="a power of two scales every product, sum and convolution of the kernel "
    "exactly in binary, but for subnormal discharges, which round to fewer digits",
)

LINEAR_RESERVOIR_CASCADE: Final = FormulaSpec(
    name="linear_reservoir_cascade",
    title="Cascade of n equal linear reservoirs, exact for an inflow linear between "
    "the ordinates (Nash)",
    function="hydrolog.routing.formulas.cascade.cascade_route",
    family="scheme",
    equation=(
        "O(t) = O0 Q(n, t/K) + integral from 0 to t of u(t - s) I(s) ds, "
        "u(t) = (t/K)^(n-1) exp(-t/K) / (K Gamma(n)), I linear between the ordinates; "
        "at the ordinates O[j] = O0 (1 - P(n, x_j)) + I[0] (P(n, x_j) - "
        "(1 - (V(x_j) - V(x_(j-1))) / a)) + sum_(m < j) h_m I[j-m], x_j = j a, "
        "a = dt / K, V(x) = x Q(n, x) + n P(n+1, x), h_0 = 1 - V(a) / a, "
        "h_m = -(V((m+1)a) - 2 V(m a) + V((m-1)a)) / a; storage at the end "
        "K [sum over the segments of the water not yet released + O0 (n - V(x_N))] [m3]"
    ),
    latex=(
        r"O(t) = O_0\,Q\!\left(n, \tfrac{t}{K}\right) + \int_0^t u(t-s)\,I(s)\,ds,"
        r"\quad u(t) = \frac{1}{K\,\Gamma(n)}\left(\frac{t}{K}\right)^{n-1}e^{-t/K},"
        r"\quad h_m = -\frac{V((m+1)a) - 2V(ma) + V((m-1)a)}{a},"
        r"\ V(x) = x\,Q(n, x) + n\,P(n+1, x),\ a = \frac{\Delta t}{K}"
    ),
    variables=(
        inflow(),
        timestep(),
        Variable(
            name="n",
            symbol="n",
            unit="-",
            description="Number of equal reservoirs in series; need not be whole.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1.0e6,
                test_reason="the cascade of a million reservoirs of the tests of the "
                "reach, whose delay outlasts the series "
                "(test_a_reach_that_holds_the_water_longer_than_the_series_keeps_the_"
                "start)",
            ),
            applicability="unstated",
            typical=Range(
                low=1.0,
                high=8.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="n of 1 to 8 in tests/unit/test_routing_cascade.py and "
                    "2.5 in docs/USAGE.md (route cascade)",
                ),
            ),
        ),
        Variable(
            name="k_min",
            symbol="K",
            unit="min",
            description="Storage constant of one reservoir.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=12000.0,
                test_reason="ten times the longest storage constant of Hydrolog's "
                "routing tests, the Iowa example's 20 h (1,200 min)",
            ),
            applicability="unstated",
            typical=Range(
                low=5.0,
                high=80.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="K of 5 to 40 min in tests/unit/test_routing_cascade.py "
                    "and 80 min in docs/USAGE.md (route cascade)",
                ),
            ),
        ),
        initial_outflow(),
    ),
    outputs=(
        outflow(),
        storage(
            "storage_start_m3", "Water held by the reservoirs at the first ordinate."
        ),
        storage("storage_end_m3", "Water held by the reservoirs at the last ordinate."),
        storage(
            "storage_steady_m3",
            "Water they would hold at rest under the last inflow, n K I[-1].",
        ),
    ),
    sources=(_NASH, _PONCE),
    constraints=(
        Constraint(
            name="representable",
            cls="precondition",
            check=_representable,
            text="n >= 2.2e-308, 0 < dt / K, and the grid of N dt / K, the largest "
            "discharge over dt / K and the storage n K max(I, O0) are finite in "
            "float64",
            source=_FLOAT64,
            satisfied={"k_min": 30.0},
            violated={"k_min": 1.0e-320},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"inflow_m3s": 1, "initial_outflow_m3s": 1},
        scalings=(
            Scaling(
                name="discharge",
                inputs={"inflow_m3s": 1, "initial_outflow_m3s": 1},
                outputs={
                    "outflow_m3s": 1,
                    "storage_start_m3": 1,
                    "storage_end_m3": 1,
                    "storage_steady_m3": 1,
                },
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="time",
                inputs={"timestep_min": 1, "k_min": 1},
                outputs={
                    "storage_start_m3": 1,
                    "storage_end_m3": 1,
                    "storage_steady_m3": 1,
                },
                tolerance=_EXACT_SCALING,
            ),
        ),
        conservation=(
            Conservation(
                name="volume",
                text="inflow volume - outflow volume - (storage at the end - storage "
                "at the start) lies within the error of the trapezoid rule on the "
                "outflow, (|I[0] - O0| / 2 + max |I[t] - I[t-1]| / 4) dt",
                residual=_quadrature_kept,
                tolerance=Tolerance(
                    abs=1e-9,
                    reason="relative to the largest volume or storage: the storage "
                    "follows from continuity of the exact solution, so only the "
                    "trapezoid's error on the outflow, bounded by the law, separates "
                    "the volumes; the second differences of V divided by dt / K lose "
                    "digits like 1e-16 (K / dt)^2 for a short step",
                ),
            ),
        ),
        limits=(
            Limit(
                name="steady_state",
                text="an inflow equal to the initial outflow passes unchanged: the "
                "weights add up to one",
                inputs={
                    "inflow_m3s": [7.5] * 12,
                    "timestep_min": 15.0,
                    "n": 3.5,
                    "k_min": 25.0,
                    "initial_outflow_m3s": 7.5,
                },
                expected={"outflow_m3s": [7.5] * 12},
                tolerance=Tolerance(
                    rel=1e-14,
                    reason="the coefficients of an ordinate add up to one in exact "
                    "arithmetic; their differences of V round at 1e-16 each",
                ),
            ),
            Limit(
                name="step_response",
                text="a steady inflow into a cascade at rest at another outflow gives "
                "O0 + (I - O0) P(n, t / K), the gamma distribution function",
                check=_step_response,
                source=_PONCE,
            ),
            Limit(
                name="matrix_exponential",
                text="for whole n the outflow and the storage equal the exact solution "
                "of the linear ODEs of the chain of reservoirs",
                check=_matrix_exponential,
            ),
            Limit(
                name="moments",
                text="the response to a unit hat has the mass one and the mean delay "
                "n K exactly, and the variance n K^2 + dt^2 / 6",
                check=_moments,
            ),
            Limit(
                name="bounded_by_its_inputs",
                text="every outflow lies between the least and the largest of the "
                "inflow and the initial outflow",
                check=_bounded,
            ),
        ),
    ),
    validation=(
        "none: n and K are calibrated on observed floods or follow from the reach "
        "(Kalinin-Milyukov); the sources report no agreement of the cascade itself "
        "with observations"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        "SI units: discharge in m3/s, time in min, storage in m3 (K in min times a "
        "discharge in m3/s times the 60 s of a minute of the units table)",
        (
            "the inflow is linear between the ordinates and equal to the initial "
            "outflow before the first one: every reservoir starts at rest with O0, "
            "and the inflow jumps to I[0] at the first ordinate"
        ),
        (
            "the outflow at an ordinate is the exact response to that inflow, not a "
            "trapezoid or Euler step; between the ordinates it is not linear, so the "
            "trapezoid volume of the outflow differs from its integral"
        ),
        (
            "a weight that rounding puts below zero is set to zero, and so are a "
            "remainder n - V and an outflow that rounding puts below zero"
        ),
        "n need not be whole: Gamma(n) and P(n, x) of SciPy's gammainc and gammaincc",
        (
            "only the given ordinates are routed: CascadeReach takes K or K = L / "
            "(n c) from the length and the celerity of a reach, and extends the time "
            "axis (Tier B, ADR-0008)"
        ),
    ),
    assumptions=(
        "each reservoir is linear, S = K O, with K constant over the flood",
        "no backwater: the outflow does not depend on the water downstream",
    ),
    traps={
        "difference_denominator": "the weights divide second differences of V by "
        "dt / K, which underflows for a step far shorter than K: precondition "
        "representable refuses dt / K = 0, an inflow over it that overflows and a "
        "subnormal n, for which SciPy's P and Q fail "
        "(test_a_step_ratio_beyond_float64_is_refused, "
        "test_a_subnormal_number_of_reservoirs_is_refused)",
        "gap_propagation": "type cases inflow_m3s-nan_element and "
        "inflow_m3s-inf_element: a gap is refused, the convolution would carry it to "
        "every later ordinate",
        "many_small_terms": "test_a_long_steady_inflow_stays_steady: 200,000 "
        "ordinates of a steady inflow, convolved by the FFT, stay steady to 1e-12",
    },
    oracles=(
        Oracle(
            kind="established",
            description="the step response P(n, t / K) of SciPy's "
            "scipy.special.gammainc (regularised lower incomplete gamma function)",
            test="tests/unit/test_formulas_cascade.py (limit step_response)",
            conventions=(
                "SciPy: gammainc(a, x) = P(a, x), shape first; the cascade: "
                "P(n, t / K) for an inflow that steps at the first ordinate",
            ),
        ),
        Oracle(
            kind="algorithm",
            description="for whole n, the linear ODEs of the chain solved over each "
            "step by the matrix exponential (scipy.linalg.expm), exact for an inflow "
            "linear over the step",
            test="tests/unit/test_formulas_cascade.py (limit matrix_exponential)",
        ),
        Oracle(
            kind="exact",
            description="the moments of the impulse response, mean n K and variance "
            "n K^2, of the gamma density",
            test="tests/unit/test_formulas_cascade.py (limit moments)",
        ),
    ),
)

SPECS: Final[tuple[FormulaSpec, ...]] = (LINEAR_RESERVOIR_CASCADE,)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""


def cascade_route(
    inflow_m3s: NDArray[np.float64] | Sequence[float],
    timestep_min: float,
    n: float,
    k_min: float,
    initial_outflow_m3s: float,
) -> CascadeRoute:
    """Route a hydrograph through linear reservoirs, spec linear_reservoir_cascade.

    The first input is the inflow at every ordinate and the last the outflow at the
    first one, both in cubic metres per second.

    Parameters
    ----------
    timestep_min : float
        Time step of the ordinates [min].
    n : float
        Number ``n`` of reservoirs; need not be whole.
    k_min : float
        Storage constant ``K`` of one reservoir [min].

    Returns
    -------
    CascadeRoute
        The outflow at every ordinate and the water held at the first and the last
        ordinate and at rest.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, a gap, or a number of reservoirs, step or storage constant
        beyond float (``precondition_failed``, constraint ``representable``).
    """
    values = checked_inputs(
        LINEAR_RESERVOIR_CASCADE,
        inflow_m3s=inflow_m3s,
        timestep_min=timestep_min,
        n=n,
        k_min=k_min,
        initial_outflow_m3s=initial_outflow_m3s,
    )
    out = checked_outputs(LINEAR_RESERVOIR_CASCADE, _route(values))
    return CascadeRoute(
        outflow_m3s=out.array("outflow_m3s"),
        storage_start_m3=out.real("storage_start_m3"),
        storage_end_m3=out.real("storage_end_m3"),
        storage_steady_m3=out.real("storage_steady_m3"),
    )
