"""Cascade of linear reservoirs: the Nash and Kalinin-Milyukov routing model.

A reach is a series of ``n`` equal linear reservoirs, each with the storage ``S = K O``
(the Nash model of :class:`~hydrolog.runoff.NashIUH`; with the characteristic reach
length ``Q / (T S0 c)`` it is the Kalinin-Milyukov method). The response to a unit
impulse is the gamma density, whose mean ``n K`` is the delay of the centroid of the
wave (its peak comes at ``(n - 1) K`` for ``n >= 1``) and whose variance is ``n K^2``.
``n`` need not be whole.

The outflow is the exact response to the inflow taken as straight lines between the
ordinates, the formula :func:`~hydrolog.routing.formulas.cascade.cascade_route` (spec
``linear_reservoir_cascade``, whose module derives the weights), so no time step is too
long: there is no window of stable steps (ADR-0008) and no sub-step is added. The
storage constant from the length and the celerity of a reach is this module's Tier B
rule ``cascade_time_scale`` (ADR-0061).

Because the outflow between the ordinates is not a straight line, the trapezoid volume
of the outflow differs from its integral: ``balance_error_m3`` is the quadrature error
of the trapezoid rule, second order in the time step, and negligible when the outflow
is at rest at both ends of the series.
"""

from __future__ import annotations

from typing import Any, Final, cast

import numpy as np
from numpy.typing import NDArray

from hydrolog.nogat_formulas import FormulaSpec, TierBSpec, convert
from hydrolog.routing._checks import one_complete_group, positive, whole_number
from hydrolog.routing.formulas._shared import SECONDS_PER_MINUTE, ponce
from hydrolog.routing.formulas.cascade import cascade_route, hat_weights
from hydrolog.routing.hydrograph import Hydrograph
from hydrolog.routing.parameters import ParameterValue
from hydrolog.routing.reach import REACH_METHODS, Reach, ReachRun

__all__ = ["SPECS", "TIER_B", "CascadeReach", "cascade_weights"]

_STORAGE = ("k_min",)
_REACH = ("length_km", "celerity_m_per_s")


def cascade_weights(n: float, step_ratio: float, count: int) -> NDArray[np.float64]:
    """Return the exact weights of a cascade of linear reservoirs.

    The outflow at ordinate ``j`` is ``sum_m h_m I_(j-m)`` for an inflow that is linear
    between the ordinates; the weights follow from the gamma kernel
    (:func:`~hydrolog.routing.formulas.cascade.hat_weights`, spec
    ``linear_reservoir_cascade``).

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
    return hat_weights(n, step_ratio, count)


@REACH_METHODS.register
class CascadeReach(Reach):
    """Route a hydrograph through a cascade of ``n`` equal linear reservoirs.

    Each reservoir has the storage ``S = K O``; the reach has the mean delay ``n K``,
    the delay of the centroid of the wave, and the variance ``n K^2 = (n K)^2 / n``: at
    the same mean delay a smaller ``n`` attenuates more (``n = 1`` is one reservoir,
    ``n`` below 1 spreads the wave further, a large ``n`` tends to a pure translation).
    The time scale is given either as the storage constant ``k_min`` of one reservoir,
    or as the length and the flood-wave celerity of the reach, which fix the travel
    time ``L / c = n K`` and so ``K = L / (n c)``. Kalinin and Milyukov take ``n`` as
    the reach length over the characteristic length ``Q / (T S0 c)``.

    The outflow is exact for the inflow interpolated linearly between the ordinates
    (spec ``linear_reservoir_cascade``), for any time step, so the routing neither adds
    sub-reaches nor refines the step and never leaves the stable region. The initial
    outflow is the outflow of every reservoir at the first ordinate.

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
    Three reservoirs of 30 min (a mean delay of 90 min) and a time step of 30 min:

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
                convert(self.length_km, "km", "m")
                / self.celerity_m_per_s
                / SECONDS_PER_MINUTE
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
        n, k = self.n, self.k_min
        run = cascade_route(
            inflow.discharge_m3s, inflow.timestep_min, n, k, initial_outflow_m3s
        )
        parameters: dict[str, ParameterValue] = {
            "n": n,
            "k_min": k,
            "lag_min": n * k,
            "timestep_over_k": inflow.timestep_min / k,
        }
        if self.length_km is not None and self.celerity_m_per_s is not None:
            parameters["length_km"] = self.length_km
            parameters["celerity_m_per_s"] = self.celerity_m_per_s
        return ReachRun(
            outflow_m3s=run.outflow_m3s,
            storage_start_m3=run.storage_start_m3,
            storage_end_m3=run.storage_end_m3,
            storage_steady_m3=run.storage_steady_m3,
            parameters=parameters,
        )


SPECS: Final[tuple[FormulaSpec, ...]] = ()
"""The module computes through the spec ``linear_reservoir_cascade``; it declares none
itself."""

TIER_B: Final = (
    TierBSpec(
        name="cascade_time_scale",
        function="hydrolog.routing.cascade.CascadeReach",
        definition="the storage constant of one reservoir from the length L and the "
        "flood-wave celerity c of the reach, K = L / (n c): the travel time L / c is "
        "the mean delay n K of the cascade; L in km and c in m/s through the units "
        "table (1 km = 1000 m, 1 min = 60 s)",
        convention="K is given directly or follows from L and c, never both "
        "(details.reason one_of); Kalinin and Milyukov take n as L over the "
        "characteristic length Q / (T S0 c)",
        source=ponce(
            "the Kalinin-Milyukov method: n = L / L_c reservoirs of K = L_c / c in "
            "series"
        ),
    ),
)
"""The time scale of a cascade from its reach (CMP-2.2)."""
