"""Clark Instantaneous Unit Hydrograph (IUH) generation.

The Clark method models watershed runoff using:
1. Translation via time-area histogram
2. Attenuation via linear reservoir routing

Reference:
    Clark, C.O. (1945). Storage and the Unit Hydrograph.
    Transactions of the American Society of Civil Engineers, 110, 1419-1446.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


@dataclass
class ClarkIUHResult:
    """
    Result of Clark Instantaneous Unit Hydrograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_per_min : NDArray[np.float64]
        IUH ordinates [1/min]. These represent the fraction of
        unit input released per minute.
    tc_min : float
        Time of concentration [min].
    r_min : float
        Storage coefficient [min].
    time_to_peak_min : float
        Time to peak discharge [min].
    peak_ordinate_per_min : float
        Peak IUH ordinate [1/min].
    """

    times_min: NDArray[np.float64]
    ordinates_per_min: NDArray[np.float64]
    tc_min: float
    r_min: float
    time_to_peak_min: float
    peak_ordinate_per_min: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)


@dataclass
class ClarkUHResult:
    """
    Result of Clark Unit Hydrograph (finite duration D).

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_m3s : NDArray[np.float64]
        Unit hydrograph ordinates [m³/s per mm].
    duration_min : float
        Rainfall duration D [min].
    area_km2 : float
        Watershed area [km²].
    tc_min : float
        Time of concentration [min].
    r_min : float
        Storage coefficient [min].
    time_to_peak_min : float
        Time to peak discharge [min].
    peak_discharge_m3s : float
        Peak discharge [m³/s per mm].
    """

    times_min: NDArray[np.float64]
    ordinates_m3s: NDArray[np.float64]
    duration_min: float
    area_km2: float
    tc_min: float
    r_min: float
    time_to_peak_min: float
    peak_discharge_m3s: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)


class ClarkIUH:
    """
    Clark Instantaneous Unit Hydrograph (IUH).

    The Clark model represents watershed response through two processes:
    1. Translation: Excess rainfall is routed through the watershed using
       a time-area histogram that represents the fraction of area
       contributing to runoff at each time.
    2. Attenuation: The translation hydrograph is routed through a
       linear reservoir to account for storage effects.

    Parameters
    ----------
    tc_min : float
        Time of concentration [min]. The time for water to travel from
        the most remote point in the watershed to the outlet.
        Must be positive.
    r_min : float
        Storage coefficient [min]. Represents the linear reservoir
        storage-discharge relationship (S = R * O).
        Must be positive.

    Notes
    -----
    The Clark IUH uses a simplified time-area curve derived from an
    elliptically-shaped watershed (HEC-HMS standard):

    .. math::
        A_{cum}(t) = 1.414 \\cdot (t/T_c)^{0.5} - 0.414 \\cdot (t/T_c)^{1.5}

    for t <= Tc, where A_cum is the cumulative fraction of watershed area.

    The linear reservoir routing uses the Muskingum-Cunge equation:

    .. math::
        O_t = O_{t-1} + C_1 \\cdot (I_t + I_{t-1} - 2 \\cdot O_{t-1})

    where C1 = dt / (2R + dt).

    Key properties:
    - Lag time: approximately Tc/2 + R (depends on time-area shape)
    - Larger R values produce broader, flatter hydrographs
    - Larger Tc values shift the peak later

    References
    ----------
    Clark, C.O. (1945). Storage and the Unit Hydrograph.
    US Army Corps of Engineers, HEC-HMS Technical Reference Manual.

    Examples
    --------
    >>> iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
    >>> result = iuh.generate(timestep_min=5.0)
    >>> print(f"Peak at {result.time_to_peak_min:.1f} min")
    """

    def __init__(self, tc_min: float, r_min: float) -> None:
        """
        Initialize Clark IUH generator.

        Parameters
        ----------
        tc_min : float
            Time of concentration [min]. Must be positive.
        r_min : float
            Storage coefficient [min]. Must be positive.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.
        """
        if tc_min <= 0:
            raise InvalidParameterError(f"tc_min must be positive, got {tc_min}")
        if r_min <= 0:
            raise InvalidParameterError(f"r_min must be positive, got {r_min}")

        self.tc_min = tc_min
        self.r_min = r_min

    @property
    def lag_time_min(self) -> float:
        """
        Approximate lag time [min].

        Notes
        -----
        For the standard elliptical time-area curve, the centroid
        of area is approximately at 0.5 * Tc. Combined with reservoir
        routing, the total lag is approximately Tc/2 + R.
        """
        return self.tc_min / 2.0 + self.r_min

    def cumulative_time_area(self, t_min: float) -> float:
        """
        Calculate cumulative time-area fraction at time t.

        Uses the HEC-HMS standard elliptical watershed approximation.

        Parameters
        ----------
        t_min : float
            Time since start of rainfall [min].

        Returns
        -------
        float
            Cumulative fraction of watershed area contributing (0 to 1).

        Notes
        -----
        Formula for elliptical watershed:
        A_cum(t) = 1.414 * (t/Tc)^0.5 - 0.414 * (t/Tc)^1.5

        This produces a symmetric time-area histogram with peak
        contribution rate at t = Tc/3.
        """
        if t_min <= 0:
            return 0.0
        if t_min >= self.tc_min:
            return 1.0

        t_ratio = t_min / self.tc_min
        return 1.414 * (t_ratio**0.5) - 0.414 * (t_ratio**1.5)

    def incremental_time_area(
        self, times_min: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """
        Calculate incremental time-area histogram.

        Parameters
        ----------
        times_min : NDArray[np.float64]
            Array of time values [min].

        Returns
        -------
        NDArray[np.float64]
            Incremental area fractions for each time interval.
        """
        # Calculate cumulative fractions
        cumulative = np.array(
            [self.cumulative_time_area(t) for t in times_min], dtype=np.float64
        )

        # Calculate incremental (difference)
        incremental = np.diff(cumulative, prepend=0.0)

        return incremental

    def _route_linear_reservoir(
        self, inflow: NDArray[np.float64], timestep_min: float
    ) -> NDArray[np.float64]:
        """
        Route inflow through linear reservoir.

        Parameters
        ----------
        inflow : NDArray[np.float64]
            Inflow hydrograph (translation hydrograph).
        timestep_min : float
            Time step [min].

        Returns
        -------
        NDArray[np.float64]
            Routed outflow hydrograph.
        """
        # Routing coefficient
        c1 = timestep_min / (2.0 * self.r_min + timestep_min)

        # Initialize output array
        outflow = np.zeros_like(inflow)

        # Route through reservoir
        for i in range(1, len(inflow)):
            outflow[i] = outflow[i - 1] + c1 * (
                inflow[i] + inflow[i - 1] - 2.0 * outflow[i - 1]
            )

        return outflow

    def generate(
        self,
        timestep_min: float = 5.0,
        duration_min: Optional[float] = None,
    ) -> ClarkIUHResult:
        """
        Generate Clark Instantaneous Unit Hydrograph.

        Parameters
        ----------
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.
        duration_min : float, optional
            Total duration of IUH [min]. If not specified, uses
            Tc + 5*R or until ordinate < 0.001 * peak.

        Returns
        -------
        ClarkIUHResult
            Generated IUH with times and ordinates.

        Raises
        ------
        InvalidParameterError
            If timestep_min is not positive.

        Examples
        --------
        >>> iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        >>> result = iuh.generate(timestep_min=5.0)
        >>> print(f"Steps: {result.n_steps}")
        """
        if timestep_min <= 0:
            raise InvalidParameterError(
                f"timestep_min must be positive, got {timestep_min}"
            )

        # Determine duration
        if duration_min is None:
            duration_min = self.tc_min + 5.0 * self.r_min

        if duration_min <= 0:
            raise InvalidParameterError(
                f"duration_min must be positive, got {duration_min}"
            )

        # Generate time array
        n_steps = int(np.ceil(duration_min / timestep_min)) + 1
        times = np.arange(n_steps, dtype=np.float64) * timestep_min

        # Calculate translation hydrograph (time-area histogram)
        translation = self.incremental_time_area(times)

        # Route through linear reservoir
        ordinates = self._route_linear_reservoir(translation, timestep_min)

        # Normalize to sum to 1 (IUH property)
        total = np.sum(ordinates) * timestep_min
        if total > 0:
            ordinates = ordinates / total

        # Find peak
        peak_idx = np.argmax(ordinates)
        time_to_peak = times[peak_idx]
        peak_ordinate = float(ordinates[peak_idx])

        return ClarkIUHResult(
            times_min=times,
            ordinates_per_min=ordinates,
            tc_min=self.tc_min,
            r_min=self.r_min,
            time_to_peak_min=time_to_peak,
            peak_ordinate_per_min=peak_ordinate,
        )

    def to_unit_hydrograph(
        self,
        area_km2: float,
        duration_min: float,
        timestep_min: float = 5.0,
        total_duration_min: Optional[float] = None,
    ) -> ClarkUHResult:
        """
        Convert IUH to D-minute Unit Hydrograph.

        Generates a unit hydrograph for rainfall of duration D
        by convolving the IUH with a rectangular pulse.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²].
        duration_min : float
            Rainfall duration D [min].
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.
        total_duration_min : float, optional
            Total duration of output UH [min]. If not specified,
            uses Tc + 5*R + duration.

        Returns
        -------
        ClarkUHResult
            Unit hydrograph with ordinates in m³/s per mm.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.

        Examples
        --------
        >>> iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        >>> uh = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=30.0)
        >>> print(f"Peak: {uh.peak_discharge_m3s:.2f} m³/s per mm")
        """
        if area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")
        if duration_min <= 0:
            raise InvalidParameterError(
                f"duration_min must be positive, got {duration_min}"
            )
        if timestep_min <= 0:
            raise InvalidParameterError(
                f"timestep_min must be positive, got {timestep_min}"
            )

        # Determine total duration
        if total_duration_min is None:
            total_duration_min = self.tc_min + 5.0 * self.r_min + duration_min

        # Generate IUH
        iuh_result = self.generate(timestep_min=timestep_min, duration_min=total_duration_min)

        # Create S-curve by cumulative sum of IUH
        s_curve = np.cumsum(iuh_result.ordinates_per_min) * timestep_min

        # Shift S-curve by duration D
        shift_steps = int(np.round(duration_min / timestep_min))
        s_curve_shifted = np.zeros_like(s_curve)
        if shift_steps < len(s_curve):
            s_curve_shifted[shift_steps:] = s_curve[:-shift_steps]

        # D-minute UH = (S(t) - S(t-D)) / D
        uh_dimensionless = (s_curve - s_curve_shifted) / duration_min

        # Scale to m³/s per mm
        # 1 mm over area_km2 = area_km2 * 1e6 m² * 0.001 m = area_km2 * 1000 m³
        volume_m3_per_mm = area_km2 * 1000.0
        ordinates_m3s = uh_dimensionless * volume_m3_per_mm / 60.0

        # Find peak
        peak_idx = np.argmax(ordinates_m3s)
        time_to_peak = iuh_result.times_min[peak_idx]
        peak_discharge = float(ordinates_m3s[peak_idx])

        return ClarkUHResult(
            times_min=iuh_result.times_min,
            ordinates_m3s=ordinates_m3s,
            duration_min=duration_min,
            area_km2=area_km2,
            tc_min=self.tc_min,
            r_min=self.r_min,
            time_to_peak_min=time_to_peak,
            peak_discharge_m3s=peak_discharge,
        )

    @classmethod
    def from_recession(
        cls,
        tc_min: float,
        recession_constant: float,
    ) -> "ClarkIUH":
        """
        Create ClarkIUH from recession analysis.

        Estimates the storage coefficient R from an observed
        recession constant.

        Parameters
        ----------
        tc_min : float
            Time of concentration [min].
        recession_constant : float
            Recession constant from hydrograph analysis.
            Ratio of flow at time t to flow at time t + dt.

        Returns
        -------
        ClarkIUH
            Configured Clark IUH generator.

        Notes
        -----
        For a linear reservoir, the recession constant K_r is related
        to R by: R = -dt / ln(K_r), where dt is the time interval
        used in recession analysis.

        For typical daily analysis (dt = 1440 min):
        R = -1440 / ln(K_r)

        Examples
        --------
        >>> # Recession constant of 0.9 (90% of flow remains after 1 day)
        >>> iuh = ClarkIUH.from_recession(tc_min=60.0, recession_constant=0.9)
        """
        if tc_min <= 0:
            raise InvalidParameterError(f"tc_min must be positive, got {tc_min}")
        if not 0 < recession_constant < 1:
            raise InvalidParameterError(
                f"recession_constant must be in (0, 1), got {recession_constant}"
            )

        # Assume daily time step for recession analysis
        dt = 1440.0  # minutes in a day
        r_min = -dt / np.log(recession_constant)

        return cls(tc_min=tc_min, r_min=r_min)

    @classmethod
    def from_tc_r_ratio(
        cls,
        tc_min: float,
        r_tc_ratio: float = 0.5,
    ) -> "ClarkIUH":
        """
        Create ClarkIUH from time of concentration and R/Tc ratio.

        Parameters
        ----------
        tc_min : float
            Time of concentration [min].
        r_tc_ratio : float, optional
            Ratio of R to Tc, by default 0.5.
            Typical range: 0.2 to 1.5.

        Returns
        -------
        ClarkIUH
            Configured Clark IUH generator.

        Notes
        -----
        The R/Tc ratio characterizes watershed storage:
        - Low values (0.2-0.4): Steep, urban watersheds with little storage
        - Medium values (0.4-0.8): Average natural watersheds
        - High values (0.8-1.5): Flat, swampy watersheds with high storage

        Examples
        --------
        >>> iuh = ClarkIUH.from_tc_r_ratio(tc_min=90.0, r_tc_ratio=0.5)
        >>> print(f"R = {iuh.r_min:.1f} min")
        R = 45.0 min
        """
        if tc_min <= 0:
            raise InvalidParameterError(f"tc_min must be positive, got {tc_min}")
        if r_tc_ratio <= 0:
            raise InvalidParameterError(
                f"r_tc_ratio must be positive, got {r_tc_ratio}"
            )

        r_min = r_tc_ratio * tc_min

        return cls(tc_min=tc_min, r_min=r_min)
