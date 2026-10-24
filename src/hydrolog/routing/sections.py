"""Channel sections and their Manning rating: depth, area, top width and celerity.

The Muskingum-Cunge method needs the flood wave celerity and the top width of the
water surface at a reference discharge. A prismatic section (rectangle, trapezoid or
triangle) gives them from Manning's equation, ``Q = A R^(2/3) S^(1/2) / n``, and the
celerity of a kinematic wave, ``c = dQ / dA`` (HEC-HMS; NEH-630 chapter 17 writes it
``c = m Q / A`` with ``m`` the log-log slope of the rating curve). Section shapes that
are not prismatic (compound sections with a floodplain, tabular sections) are not
modelled: give the celerity and the top width instead.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.optimize import brentq

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._checks import in_range, positive

__all__ = ["FlowState", "TrapezoidalSection"]

_MAX_DEPTH_DOUBLINGS = 80


@dataclass(frozen=True)
class FlowState:
    """The flow in a section at the normal depth of a discharge.

    Attributes
    ----------
    depth_m : float
        Normal depth [m].
    area_m2 : float
        Flow area [m2].
    top_width_m : float
        Width of the water surface [m].
    velocity_m_per_s : float
        Mean velocity ``Q / A`` [m/s].
    celerity_m_per_s : float
        Celerity of a flood wave, ``dQ / dA`` at constant slope [m/s].
    """

    depth_m: float
    area_m2: float
    top_width_m: float
    velocity_m_per_s: float
    celerity_m_per_s: float


class TrapezoidalSection:
    """A prismatic channel section: rectangle, trapezoid or triangle.

    Parameters
    ----------
    bottom_width_m : float
        Width of the bottom [m], >= 0; 0 gives a triangle.
    side_slope_m_per_m : float
        Horizontal metres per vertical metre of both banks, >= 0; 0 gives a
        rectangle (a 2:1 bank is 2).
    manning_n : float
        Manning's roughness coefficient [s/m^(1/3)], > 0.

    Raises
    ------
    InvalidParameterError
        If a value is not valid, or the section has neither a bottom nor sides
        (``details.reason`` ``degenerate_section``).

    Examples
    --------
    >>> section = TrapezoidalSection(bottom_width_m=4.0, side_slope_m_per_m=2.0,
    ...                              manning_n=0.035)
    >>> state = section.flow(discharge_m3s=10.0, slope_m_per_m=0.001)
    >>> round(state.depth_m, 3), round(state.top_width_m, 3)
    (1.551, 10.204)
    """

    def __init__(
        self, bottom_width_m: float, side_slope_m_per_m: float, manning_n: float
    ) -> None:
        """Create the section."""
        self.bottom_width_m = in_range(bottom_width_m, "bottom_width_m", minimum=0.0)
        self.side_slope_m_per_m = in_range(
            side_slope_m_per_m, "side_slope_m_per_m", minimum=0.0
        )
        self.manning_n = positive(manning_n, "manning_n")
        if self.bottom_width_m == 0.0 and self.side_slope_m_per_m == 0.0:
            raise InvalidParameterError(
                "Option 'bottom_width_m': a section needs a bottom width or a side "
                "slope above zero, otherwise it has no area",
                details={
                    "option": "bottom_width_m",
                    "reason": "degenerate_section",
                    "value": 0.0,
                },
            )

    def _area(self, depth: float) -> float:
        return (self.bottom_width_m + self.side_slope_m_per_m * depth) * depth

    def _top_width(self, depth: float) -> float:
        return self.bottom_width_m + 2.0 * self.side_slope_m_per_m * depth

    def _slant(self) -> float:
        """Length of a bank per metre of depth."""
        return math.sqrt(1.0 + self.side_slope_m_per_m**2)

    def _wetted_perimeter(self, depth: float) -> float:
        return self.bottom_width_m + 2.0 * depth * self._slant()

    def _manning(self, depth: float, slope: float) -> float:
        """Discharge at normal flow of ``depth`` [m3/s]."""
        if depth <= 0.0:
            return 0.0
        area = self._area(depth)
        hydraulic_radius = area / self._wetted_perimeter(depth)
        conveyance = area * math.pow(hydraulic_radius, 2.0 / 3.0)
        return conveyance * math.sqrt(slope) / self.manning_n

    def flow(self, discharge_m3s: float, slope_m_per_m: float) -> FlowState:
        """Return the flow at the normal depth of a discharge.

        Parameters
        ----------
        discharge_m3s : float
            Discharge [m3/s], > 0.
        slope_m_per_m : float
            Bed (friction) slope [m/m], > 0.

        Returns
        -------
        FlowState
            Depth, area, top width, velocity and celerity.

        Raises
        ------
        InvalidParameterError
            If the discharge or the slope is not a positive number.
        """
        discharge = positive(discharge_m3s, "discharge_m3s")
        slope = positive(slope_m_per_m, "slope_m_per_m")
        upper = 1.0
        for _ in range(_MAX_DEPTH_DOUBLINGS):
            if self._manning(upper, slope) >= discharge:
                break
            upper *= 2.0
        depth = float(
            brentq(
                lambda y: self._manning(y, slope) - discharge,
                0.0,
                upper,
                xtol=1e-14,
                rtol=1e-15,
            )
        )
        area = self._area(depth)
        top = self._top_width(depth)
        perimeter = self._wetted_perimeter(depth)
        # Q ~ A^(5/3) P^(-2/3): d ln Q / dy = 5/3 T/A - 2/3 (dP/dy)/P, and c = dQ/dA
        rating_slope = (5.0 / 3.0) * top / area - (2.0 / 3.0) * (
            2.0 * self._slant() / perimeter
        )
        return FlowState(
            depth_m=depth,
            area_m2=area,
            top_width_m=top,
            velocity_m_per_s=discharge / area,
            celerity_m_per_s=discharge * rating_slope / top,
        )
