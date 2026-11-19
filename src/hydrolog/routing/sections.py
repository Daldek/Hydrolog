"""Channel sections and their Manning rating: depth, area, top width and celerity.

The Muskingum-Cunge method needs the flood wave celerity and the top width of the
water surface at a reference discharge. A prismatic section (rectangle, trapezoid or
triangle) gives them from Manning's equation and the celerity of a kinematic wave,
``c = dQ / dA`` (HEC-HMS; NEH-630 chapter 17 writes it ``c = m Q / A`` with ``m`` the
local log-log slope of the rating, where its example 17-4 takes a discharge-weighted
slope of a rating table, 2 % higher): the formula
:func:`~hydrolog.routing.formulas.manning.normal_flow` (spec ``manning_normal_flow``,
ADR-0061). Section shapes that are not prismatic (compound sections with a
floodplain, tabular sections) are not modelled: give the celerity and the top width
instead.
"""

from __future__ import annotations

from dataclasses import dataclass

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._checks import in_range, positive
from hydrolog.routing.formulas.manning import normal_flow

__all__ = ["FlowState", "TrapezoidalSection"]


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

    def flow(self, discharge_m3s: float, slope_m_per_m: float) -> FlowState:
        """Return the flow at the normal depth of a discharge.

        The depth, the area, the top width, the velocity and the celerity are those
        of the formula :func:`~hydrolog.routing.formulas.manning.normal_flow`.

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
            If the discharge or the slope is not a positive number, or the formula
            refuses the flow (``details.reason`` ``precondition_failed``: a depth,
            area or velocity that a float cannot hold).
        """
        flow = normal_flow(
            positive(discharge_m3s, "discharge_m3s"),
            positive(slope_m_per_m, "slope_m_per_m"),
            self.bottom_width_m,
            self.side_slope_m_per_m,
            self.manning_n,
        )
        return FlowState(
            depth_m=flow.depth_m,
            area_m2=flow.area_m2,
            top_width_m=flow.top_width_m,
            velocity_m_per_s=flow.velocity_m_per_s,
            celerity_m_per_s=flow.celerity_m_per_s,
        )
