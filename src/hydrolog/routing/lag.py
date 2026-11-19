"""Lag routing: the outflow is the inflow, a fixed time later.

``O(t) = I(t - lag)``. The hydrograph is translated without any attenuation, which suits
a short reach with a predictable travel time (HEC-HMS "Lag"). Nothing is stored beyond
the water in transit, ``lag`` times the inflow. The shift on the ordinates is the
formula :func:`~hydrolog.routing.formulas.lag.lag_route` (spec ``lag``, ADR-0061).
"""

from __future__ import annotations

from typing import Any

from hydrolog.routing._checks import positive
from hydrolog.routing.formulas.lag import lag_route
from hydrolog.routing.hydrograph import Hydrograph
from hydrolog.routing.reach import REACH_METHODS, Reach, ReachRun, RoutingNotice

__all__ = ["LagReach"]


@REACH_METHODS.register
class LagReach(Reach):
    """Translate a hydrograph in time without changing its shape.

    The outflow at time ``t`` is the inflow at ``t - lag_min``; before the first
    ordinate the inflow is the initial outflow. A lag that is not a whole number of
    time steps is handled by linear interpolation between ordinates, which flattens
    sharp peaks (a notice says so).

    Parameters
    ----------
    lag_min : float
        Lag [min], > 0 and finite.

    Raises
    ------
    InvalidParameterError
        If ``lag_min`` is not a finite number above zero.

    Examples
    --------
    >>> from hydrolog.routing import Hydrograph, LagReach
    >>> inflow = Hydrograph.from_step([0.0, 10.0, 40.0, 20.0, 0.0, 0.0], 30.0)
    >>> result = LagReach(lag_min=60.0).route(inflow)
    >>> result.outflow.discharge_m3s.tolist()
    [0.0, 0.0, 0.0, 10.0, 40.0, 20.0, 0.0]
    """

    model = "lag"

    def __init__(self, lag_min: float) -> None:
        """Create the element."""
        self.lag_min = positive(lag_min, "lag_min")

    def options(self) -> dict[str, Any]:
        """Return ``{"lag_min": ...}``, the argument that rebuilds the element."""
        return {"lag_min": self.lag_min}

    def _run(self, inflow: Hydrograph, initial_outflow_m3s: float) -> ReachRun:
        run = lag_route(
            inflow.discharge_m3s,
            inflow.timestep_min,
            self.lag_min,
            initial_outflow_m3s,
        )
        notices: list[RoutingNotice] = []
        if run.lag_fraction > 0.0:
            notices.append(
                RoutingNotice(
                    "lag_interpolated",
                    f"The lag of {self.lag_min:g} min is {run.lag_steps:g} time steps "
                    f"of {inflow.timestep_min:g} min, not a whole number: the shifted "
                    "ordinates are interpolated linearly, which flattens sharp peaks.",
                )
            )
        return ReachRun(
            outflow_m3s=run.outflow_m3s,
            storage_start_m3=run.storage_start_m3,
            storage_end_m3=run.storage_end_m3,
            storage_steady_m3=run.storage_steady_m3,
            parameters={"lag_min": self.lag_min, "lag_steps": run.lag_steps},
            notices=tuple(notices),
        )
