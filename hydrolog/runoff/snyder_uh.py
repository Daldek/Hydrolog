"""Snyder Synthetic Unit Hydrograph generation.

The Snyder method is an empirical approach to synthetic unit hydrograph
generation based on watershed characteristics.

Reference:
    Snyder, F.F. (1938). Synthetic unit-graphs.
    Transactions of the American Geophysical Union, 19, 447-454.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


@dataclass
class SnyderUHResult:
    """
    Result of Snyder Unit Hydrograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_m3s : NDArray[np.float64]
        Unit hydrograph ordinates [m³/s per mm].
    area_km2 : float
        Watershed area [km²].
    lag_time_min : float
        Basin lag time tL [min] (original, unadjusted).
    adjusted_lag_time_min : float
        Adjusted lag time tLR [min] for non-standard duration.
    time_to_peak_min : float
        Time to peak discharge tp or tpR [min].
    peak_discharge_m3s : float
        Peak discharge qp or qpR [m³/s per mm].
    time_base_min : float
        Time base of the hydrograph tb [min].
    duration_min : float
        Actual rainfall duration Δt used for generation [min].
    standard_duration_min : float
        Standard rainfall duration tD = tL/5.5 [min].
    ct : float
        Time coefficient Ct.
    cp : float
        Peak coefficient Cp.
    """

    times_min: NDArray[np.float64]
    ordinates_m3s: NDArray[np.float64]
    area_km2: float
    lag_time_min: float
    adjusted_lag_time_min: float
    time_to_peak_min: float
    peak_discharge_m3s: float
    time_base_min: float
    duration_min: float
    standard_duration_min: float
    ct: float
    cp: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)


class SnyderUH:
    """
    Snyder Synthetic Unit Hydrograph.

    Generates a synthetic unit hydrograph based on empirical relationships
    developed by Snyder (1938) for ungauged watersheds.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²]. Must be positive.
    L_km : float
        Length of main stream from outlet to divide [km]. Must be positive.
    Lc_km : float
        Length along main stream from outlet to centroid of watershed [km].
        Must be positive.
    ct : float, optional
        Time coefficient, by default 1.5.
        Typical range for SI units: 1.35-1.65.
    cp : float, optional
        Peak coefficient, by default 0.6.
        Typical range: 0.4-0.8.

    Notes
    -----
    Key relationships (SI/metric units):

    **Basin lag time:**
        tL = Ct × (L × Lc)^0.3  [hours]

    where L and Lc are in km, Ct typically 1.35-1.65 for SI.

    **Standard rainfall duration:**
        tD = tL / 5.5  [hours]

    **For standard duration (Δt = tD):**
        tp = tL + tD/2  [hours]
        qp = 0.275 × Cp × A / tL  [m³/s per mm]

    **For non-standard duration (Δt ≠ tD):**
        tLR = tL + 0.25 × (Δt - tD)  [hours]  (adjusted lag time)
        tpR = tLR + Δt/2  [hours]  (adjusted time to peak)
        qpR = qp × (tL / tLR)  [m³/s per mm]  (adjusted peak discharge)

    **Time base (from water balance):**
        tb = 0.556 × A / qpR  [hours]

    **Hydrograph widths at 50% and 75% of peak:**
        W50 = 5.87 / (qp/A)^1.08  [hours]
        W75 = 3.35 / (qp/A)^1.08  [hours]

    The coefficients Ct and Cp characterize the watershed:
    - Ct: Related to watershed slope and storage (SI: 1.35-1.65)
      - Lower values: Steep, mountainous areas
      - Higher values: Flat, swampy areas
    - Cp: Related to retention and storage (0.4-0.8)
      - Lower values (0.4-0.5): High storage, rural areas
      - Higher values (0.6-0.8): Low storage, urban areas
      - Inversely related to Ct

    References
    ----------
    Snyder, F.F. (1938). Synthetic unit-graphs.
    Bedient, P.B. & Huber, W.C. (1992). Hydrology and Floodplain Analysis.

    Examples
    --------
    >>> uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
    >>> result = uh.generate(timestep_min=30.0)
    >>> print(f"Peak: {result.peak_discharge_m3s:.2f} m³/s per mm")
    """

    def __init__(
        self,
        area_km2: float,
        L_km: float,
        Lc_km: float,
        ct: float = 1.5,
        cp: float = 0.6,
    ) -> None:
        """
        Initialize Snyder Unit Hydrograph generator.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²]. Must be positive.
        L_km : float
            Length of main stream [km]. Must be positive.
        Lc_km : float
            Length to centroid [km]. Must be positive.
        ct : float, optional
            Time coefficient (SI), by default 1.5.
            Typical range: 1.35-1.65.
        cp : float, optional
            Peak coefficient, by default 0.6.
            Typical range: 0.4-0.8.

        Raises
        ------
        InvalidParameterError
            If any parameter is invalid.
        """
        if area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")
        if L_km <= 0:
            raise InvalidParameterError(f"L_km must be positive, got {L_km}")
        if Lc_km <= 0:
            raise InvalidParameterError(f"Lc_km must be positive, got {Lc_km}")
        if ct <= 0:
            raise InvalidParameterError(f"ct must be positive, got {ct}")
        if cp <= 0:
            raise InvalidParameterError(f"cp must be positive, got {cp}")

        self.area_km2 = area_km2
        self.L_km = L_km
        self.Lc_km = Lc_km
        self.ct = ct
        self.cp = cp

    @property
    def lag_time_hours(self) -> float:
        """
        Basin lag time tL [hours].

        Notes
        -----
        Formula: tL = Ct * (L * Lc)^0.3
        """
        return self.ct * ((self.L_km * self.Lc_km) ** 0.3)

    @property
    def lag_time_min(self) -> float:
        """Basin lag time tL [min]."""
        return self.lag_time_hours * 60.0

    @property
    def standard_duration_hours(self) -> float:
        """
        Standard rainfall duration tD [hours].

        Notes
        -----
        Formula: tD = tL / 5.5

        This is the duration for which the standard Snyder
        parameters (tp, qp) apply directly without adjustment.
        """
        return self.lag_time_hours / 5.5

    @property
    def standard_duration_min(self) -> float:
        """Standard rainfall duration tD [min]."""
        return self.standard_duration_hours * 60.0

    def time_to_peak_hours(self, duration_hours: Optional[float] = None) -> float:
        """
        Calculate time to peak [hours].

        Parameters
        ----------
        duration_hours : float, optional
            Rainfall duration Δt [hours]. If not specified, uses
            standard duration tD.

        Returns
        -------
        float
            Time to peak [hours].

        Notes
        -----
        For standard duration (Δt = tD):
            tp = tL + tD/2

        For non-standard duration (Δt ≠ tD):
            tpR = tLR + Δt/2

        where tLR is the adjusted lag time.
        """
        if duration_hours is None:
            duration_hours = self.standard_duration_hours

        tL_adj = self.adjusted_lag_time_hours(duration_hours)

        return tL_adj + duration_hours / 2.0

    def time_to_peak_min(self, duration_min: Optional[float] = None) -> float:
        """
        Calculate time to peak [min].

        Parameters
        ----------
        duration_min : float, optional
            Rainfall duration Δt [min]. If not specified, uses
            standard duration tD.

        Returns
        -------
        float
            Time to peak tp (or tpR for non-standard duration) [min].
        """
        duration_hours = None
        if duration_min is not None:
            duration_hours = duration_min / 60.0
        return self.time_to_peak_hours(duration_hours) * 60.0

    def adjusted_lag_time_hours(
        self, duration_hours: Optional[float] = None
    ) -> float:
        """
        Calculate adjusted lag time tLR [hours].

        Parameters
        ----------
        duration_hours : float, optional
            Rainfall duration Δt [hours]. If not specified, uses
            standard duration tD (returns tL unchanged).

        Returns
        -------
        float
            Adjusted lag time tLR [hours].

        Notes
        -----
        Formula: tLR = tL + 0.25 × (Δt - tD)

        When Δt = tD, tLR = tL (no adjustment needed).
        """
        if duration_hours is None:
            duration_hours = self.standard_duration_hours

        tD = self.standard_duration_hours
        tLR = self.lag_time_hours + 0.25 * (duration_hours - tD)

        # Ensure positive lag time
        return max(tLR, 0.1 * self.lag_time_hours)

    def peak_discharge(self, duration_min: Optional[float] = None) -> float:
        """
        Calculate peak discharge [m³/s per mm].

        Parameters
        ----------
        duration_min : float, optional
            Rainfall duration Δt [min]. If not specified, uses
            standard duration tD.

        Returns
        -------
        float
            Peak discharge qp (or qpR for non-standard duration) [m³/s per mm].

        Notes
        -----
        For standard duration (Δt = tD):
            qp = 0.275 × Cp × A / tL  [m³/s per mm]

        For non-standard duration (Δt ≠ tD):
            qpR = qp × (tL / tLR)  [m³/s per mm]

        Which simplifies to:
            qpR = 0.275 × Cp × A / tLR
        """
        duration_hours = None
        if duration_min is not None:
            duration_hours = duration_min / 60.0

        tLR = self.adjusted_lag_time_hours(duration_hours)

        return 0.275 * self.cp * self.area_km2 / tLR

    def time_base_hours(self, duration_min: Optional[float] = None) -> float:
        """
        Calculate time base tb [hours].

        Parameters
        ----------
        duration_min : float, optional
            Rainfall duration Δt [min]. If not specified, uses
            standard duration tD.

        Returns
        -------
        float
            Time base tb [hours].

        Notes
        -----
        Formula based on water balance:

            tb = 0.556 × A / qpR  [hours]

        where:
        - A is watershed area [km²]
        - qpR is peak discharge [m³/s per mm]

        Derivation:
        - Volume for 1 mm over A km² = A × 1000 m³
        - For triangular UH: V = 0.5 × qp × tb × 3600
        - Solving: tb = 2 × A × 1000 / (qp × 3600) = 0.556 × A / qp
        """
        qpR = self.peak_discharge(duration_min)
        return 0.556 * self.area_km2 / qpR

    def time_base_min(self, duration_min: Optional[float] = None) -> float:
        """
        Calculate time base tb [min].

        Parameters
        ----------
        duration_min : float, optional
            Rainfall duration Δt [min]. If not specified, uses
            standard duration tD.

        Returns
        -------
        float
            Time base tb [min].
        """
        return self.time_base_hours(duration_min) * 60.0

    def width_at_percent(self, percent: float) -> float:
        """
        Calculate hydrograph width at given percent of peak [hours].

        Parameters
        ----------
        percent : float
            Percentage of peak discharge (0-100).

        Returns
        -------
        float
            Width of hydrograph at specified percentage [hours].

        Notes
        -----
        Formulas:
            W50 = 5.87 / (qp/A)^1.08
            W75 = 3.35 / (qp/A)^1.08

        For other percentages, linear interpolation is used.
        """
        if not 0 < percent <= 100:
            raise InvalidParameterError(
                f"percent must be in (0, 100], got {percent}"
            )

        qp = self.peak_discharge()
        qp_per_area = qp / self.area_km2

        # Base widths at 50% and 75%
        w50 = 5.87 / (qp_per_area**1.08)
        w75 = 3.35 / (qp_per_area**1.08)

        if abs(percent - 50.0) < 0.01:
            return w50
        elif abs(percent - 75.0) < 0.01:
            return w75
        elif percent < 50.0:
            # Extrapolate below 50%
            # Assume linear relationship in log space
            ratio = percent / 50.0
            return w50 / ratio
        elif percent < 75.0:
            # Interpolate between 50% and 75%
            t = (percent - 50.0) / 25.0
            return w50 + t * (w75 - w50)
        else:
            # Extrapolate above 75%
            ratio = percent / 75.0
            return w75 * (1.0 / ratio)

    def _generate_shape(
        self, times_min: NDArray[np.float64], duration_min: Optional[float] = None
    ) -> NDArray[np.float64]:
        """
        Generate hydrograph shape using gamma distribution approximation.

        The Snyder hydrograph shape is approximated using a gamma
        distribution which provides a smooth, physically realistic curve.
        """
        tp_min = self.time_to_peak_min(duration_min)
        qp = self.peak_discharge(duration_min)

        # Use gamma distribution approximation
        # Shape parameter chosen to match Snyder widths
        # n ≈ 3.7 gives good agreement with W50/W75 ratios
        n = 3.7
        k_min = tp_min / (n - 1) if n > 1 else tp_min

        # Gamma distribution scaled to peak
        ordinates = np.zeros_like(times_min)
        mask = times_min > 0

        t_over_k = times_min[mask] / k_min
        # Gamma PDF: f(t) = (t/k)^(n-1) * exp(-t/k) / (k * Gamma(n))
        # Normalized to peak at qp
        ordinates[mask] = qp * (
            (t_over_k ** (n - 1)) * np.exp(-(t_over_k - (n - 1)))
        )

        return ordinates

    def generate(
        self,
        timestep_min: float = 30.0,
        duration_min: Optional[float] = None,
        total_duration_min: Optional[float] = None,
    ) -> SnyderUHResult:
        """
        Generate Snyder Unit Hydrograph.

        Parameters
        ----------
        timestep_min : float, optional
            Time step for discretization [min], by default 30.0.
        duration_min : float, optional
            Rainfall duration Δt [min]. If not specified, uses
            standard duration tD = tL/5.5.
        total_duration_min : float, optional
            Total duration of output UH [min]. If not specified,
            uses time_base tb.

        Returns
        -------
        SnyderUHResult
            Generated unit hydrograph with times and ordinates.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.

        Examples
        --------
        >>> uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        >>> result = uh.generate(timestep_min=30.0)
        >>> print(f"Peak: {result.peak_discharge_m3s:.2f} m³/s per mm")
        """
        if timestep_min <= 0:
            raise InvalidParameterError(
                f"timestep_min must be positive, got {timestep_min}"
            )

        # Use standard duration if not specified
        if duration_min is None:
            duration_min = self.standard_duration_min

        if duration_min <= 0:
            raise InvalidParameterError(
                f"duration_min must be positive, got {duration_min}"
            )

        # Determine total duration
        if total_duration_min is None:
            total_duration_min = self.time_base_min(duration_min)

        if total_duration_min <= 0:
            raise InvalidParameterError(
                f"total_duration_min must be positive, got {total_duration_min}"
            )

        # Generate time array
        n_steps = int(np.ceil(total_duration_min / timestep_min)) + 1
        times = np.arange(n_steps, dtype=np.float64) * timestep_min

        # Generate hydrograph shape
        ordinates = self._generate_shape(times, duration_min)

        # Normalize to conserve water volume
        # Volume = sum of ordinates * timestep_seconds
        # Should equal area_km2 * 1000 m³ (for 1 mm of rainfall)
        volume_actual = np.sum(ordinates) * timestep_min * 60.0
        volume_expected = self.area_km2 * 1000.0
        if volume_actual > 0:
            ordinates = ordinates * (volume_expected / volume_actual)

        # Calculate peak parameters
        tp_min = self.time_to_peak_min(duration_min)
        peak_idx = np.argmax(ordinates)
        peak_discharge = float(ordinates[peak_idx])

        # Calculate adjusted lag time for non-standard duration
        adjusted_lag_time = self.adjusted_lag_time_hours(duration_min / 60.0) * 60.0

        return SnyderUHResult(
            times_min=times,
            ordinates_m3s=ordinates,
            area_km2=self.area_km2,
            lag_time_min=self.lag_time_min,
            adjusted_lag_time_min=adjusted_lag_time,
            time_to_peak_min=tp_min,
            peak_discharge_m3s=peak_discharge,
            time_base_min=self.time_base_min(duration_min),
            duration_min=duration_min,
            standard_duration_min=self.standard_duration_min,
            ct=self.ct,
            cp=self.cp,
        )
