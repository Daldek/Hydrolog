"""Lag routing: the outflow is the inflow, a fixed time later.

``O(t) = I(t - lag)``. The hydrograph is translated without any attenuation, which suits
a short reach with a predictable travel time (HEC-HMS "Lag"). Nothing is stored beyond
the water in transit, ``lag`` times the inflow.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from hydrolog.routing._checks import positive
from hydrolog.routing.hydrograph import Hydrograph
from hydrolog.routing.reach import Reach, ReachRun, RoutingNotice

__all__ = ["LagReach"]

_ROUNDING = 1e-9
_SECONDS_PER_MINUTE = 60.0


def _transit_volume(
    times: NDArray[np.float64],
    values: NDArray[np.float64],
    initial: float,
    lag: float,
) -> float:
    """Volume of the inflow over the last ``lag`` minutes of the series [m3].

    The inflow is piecewise linear between the ordinates and equals ``initial`` before
    the first one (the water that was in transit at the start).
    """
    end = float(times[-1])
    begin = end - lag
    first = float(times[0])
    before = initial * max(0.0, first - begin)
    lower = max(begin, first)
    knots = np.concatenate([[lower], times[(times > lower) & (times < end)], [end]])
    levels = np.interp(knots, times, values)
    area = float(np.sum(0.5 * (levels[1:] + levels[:-1]) * np.diff(knots)))
    return (before + area) * _SECONDS_PER_MINUTE


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

    def _run(self, inflow: Hydrograph, initial_outflow_m3s: float) -> ReachRun:
        values = inflow.discharge_m3s
        count = len(values)
        steps = self.lag_min / inflow.timestep_min
        whole = math.floor(steps + _ROUNDING)
        fraction = steps - whole
        if fraction < _ROUNDING:
            fraction = 0.0
        elif fraction > 1.0 - _ROUNDING:
            whole, fraction = whole + 1, 0.0
        # padded[j + 1] is the inflow ``whole`` steps before ordinate j, padded[j] one
        # step earlier; before the first ordinate the inflow is the initial outflow.
        head = min(whole + 1, count + 1)
        padded = np.concatenate([np.full(head, initial_outflow_m3s), values])[
            : count + 1
        ]
        outflow = (1.0 - fraction) * padded[1:] + fraction * padded[:-1]
        notices: list[RoutingNotice] = []
        if fraction > 0.0:
            notices.append(
                RoutingNotice(
                    "lag_interpolated",
                    f"The lag of {self.lag_min:g} min is {steps:g} time steps of "
                    f"{inflow.timestep_min:g} min, not a whole number: the shifted "
                    "ordinates are interpolated linearly, which flattens sharp peaks.",
                )
            )
        return ReachRun(
            outflow_m3s=outflow,
            storage_start_m3=initial_outflow_m3s * self.lag_min * _SECONDS_PER_MINUTE,
            storage_end_m3=_transit_volume(
                inflow.times_min, values, initial_outflow_m3s, self.lag_min
            ),
            storage_steady_m3=float(values[-1]) * self.lag_min * _SECONDS_PER_MINUTE,
            parameters={"lag_min": self.lag_min, "lag_steps": steps},
            notices=tuple(notices),
        )
