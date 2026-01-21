"""SCS Unit Hydrograph generation."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError

# SCS dimensionless unit hydrograph ratios (t/tp vs q/qp)
# Standard NRCS tabulated values
SCS_DIMENSIONLESS_UH = np.array(
    [
        [0.0, 0.000],
        [0.1, 0.030],
        [0.2, 0.100],
        [0.3, 0.190],
        [0.4, 0.310],
        [0.5, 0.470],
        [0.6, 0.660],
        [0.7, 0.820],
        [0.8, 0.930],
        [0.9, 0.990],
        [1.0, 1.000],
        [1.1, 0.990],
        [1.2, 0.930],
        [1.3, 0.860],
        [1.4, 0.780],
        [1.5, 0.680],
        [1.6, 0.560],
        [1.7, 0.460],
        [1.8, 0.390],
        [1.9, 0.330],
        [2.0, 0.280],
        [2.2, 0.207],
        [2.4, 0.147],
        [2.6, 0.107],
        [2.8, 0.077],
        [3.0, 0.055],
        [3.2, 0.040],
        [3.4, 0.029],
        [3.6, 0.021],
        [3.8, 0.015],
        [4.0, 0.011],
        [4.5, 0.005],
        [5.0, 0.000],
    ],
    dtype=np.float64,
)


@dataclass
class UnitHydrographResult:
    """
    Result of unit hydrograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_m3s : NDArray[np.float64]
        Unit hydrograph ordinates [m³/s per mm].
    time_to_peak_min : float
        Time to peak discharge tp [min].
    peak_discharge_m3s : float
        Peak discharge qp [m³/s per mm].
    time_base_min : float
        Time base of the hydrograph tb [min].
    lag_time_min : float
        Lag time tlag [min].
    timestep_min : float
        Time step [min].
    """

    times_min: NDArray[np.float64]
    ordinates_m3s: NDArray[np.float64]
    time_to_peak_min: float
    peak_discharge_m3s: float
    time_base_min: float
    lag_time_min: float
    timestep_min: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)


class SCSUnitHydrograph:
    """
    SCS (NRCS) Dimensionless Unit Hydrograph.

    Generates a unit hydrograph based on the SCS dimensionless
    unit hydrograph methodology. The shape is defined by standard
    NRCS ratios and scaled by watershed parameters.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²].
    tc_min : float
        Time of concentration [min].

    Notes
    -----
    Key relationships:
    - Lag time: tlag = 0.6 * tc
    - Time to peak: tp = D/2 + tlag (D = rainfall duration/timestep)
    - Peak discharge: qp = 0.208 * A / tp (A in km², tp in hours)
    - Time base: tb ≈ 2.67 * tp (triangular approximation)

    The unit hydrograph represents the runoff response to 1 mm
    of effective precipitation uniformly distributed over the
    watershed during one time step.

    References
    ----------
    USDA-NRCS (1986). Urban Hydrology for Small Watersheds.
    Technical Release 55 (TR-55).

    Examples
    --------
    >>> uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
    >>> result = uh.generate(timestep_min=5.0)
    >>> print(f"Peak: {result.peak_discharge_m3s:.2f} m³/s per mm")
    """

    def __init__(self, area_km2: float, tc_min: float) -> None:
        """
        Initialize SCS Unit Hydrograph generator.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²]. Must be positive.
        tc_min : float
            Time of concentration [min]. Must be positive.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.
        """
        if area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")
        if tc_min <= 0:
            raise InvalidParameterError(f"tc_min must be positive, got {tc_min}")

        self.area_km2 = area_km2
        self.tc_min = tc_min

    @property
    def lag_time_min(self) -> float:
        """
        Lag time tlag [min].

        Lag time is the time from the centroid of rainfall excess
        to the peak of the unit hydrograph.

        Notes
        -----
        Formula: tlag = 0.6 * tc
        """
        return 0.6 * self.tc_min

    def time_to_peak(self, timestep_min: float) -> float:
        """
        Calculate time to peak tp.

        Parameters
        ----------
        timestep_min : float
            Rainfall duration / time step [min].

        Returns
        -------
        float
            Time to peak tp [min].

        Notes
        -----
        Formula: tp = D/2 + tlag
        where D is the effective rainfall duration (timestep).
        """
        return (timestep_min / 2.0) + self.lag_time_min

    def peak_discharge(self, timestep_min: float) -> float:
        """
        Calculate peak discharge of unit hydrograph.

        Parameters
        ----------
        timestep_min : float
            Time step [min].

        Returns
        -------
        float
            Peak discharge qp [m³/s per mm of effective rainfall].

        Notes
        -----
        Formula (metric): qp = 0.208 * A / tp
        - A: area [km²]
        - tp: time to peak [hours]
        - qp: peak discharge [m³/s per mm]

        The constant 0.208 comes from the triangular unit hydrograph
        approximation where the volume under the hydrograph equals 1 mm
        of runoff over the watershed:
        V = 1 mm * A km² = 0.001 m * A * 10⁶ m² = A * 1000 m³
        For a triangle: V = 0.5 * qp * tb, with tb ≈ 2.67 * tp
        Solving: qp = 2V / (2.67 * tp) = 2 * A * 1000 / (2.67 * tp * 3600)
                 qp ≈ 0.208 * A / tp [m³/s per mm]
        """
        tp_min = self.time_to_peak(timestep_min)
        tp_hours = tp_min / 60.0
        qp: float = 0.208 * self.area_km2 / tp_hours
        return qp

    def time_base(self, timestep_min: float) -> float:
        """
        Calculate time base of unit hydrograph.

        Parameters
        ----------
        timestep_min : float
            Time step [min].

        Returns
        -------
        float
            Time base tb [min].

        Notes
        -----
        For the SCS dimensionless unit hydrograph, the time base
        extends to approximately 5 * tp (where q/qp ≈ 0).
        The triangular approximation uses tb = 2.67 * tp.
        """
        tp = self.time_to_peak(timestep_min)
        # Use the full dimensionless UH extent (5 * tp)
        return 5.0 * tp

    def generate(self, timestep_min: float = 5.0) -> UnitHydrographResult:
        """
        Generate SCS unit hydrograph.

        Parameters
        ----------
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.

        Returns
        -------
        UnitHydrographResult
            Generated unit hydrograph with times and ordinates.

        Raises
        ------
        InvalidParameterError
            If timestep_min is not positive.

        Examples
        --------
        >>> uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
        >>> result = uh.generate(timestep_min=5.0)
        >>> print(f"Steps: {result.n_steps}, Peak: {result.peak_discharge_m3s:.2f}")
        """
        if timestep_min <= 0:
            raise InvalidParameterError(
                f"timestep_min must be positive, got {timestep_min}"
            )

        tp = self.time_to_peak(timestep_min)
        qp = self.peak_discharge(timestep_min)
        tb = self.time_base(timestep_min)

        # Generate time array
        n_steps = int(np.ceil(tb / timestep_min)) + 1
        times = np.arange(n_steps, dtype=np.float64) * timestep_min

        # Calculate t/tp ratios
        t_tp_ratios = times / tp

        # Interpolate q/qp ratios from dimensionless UH
        q_qp_ratios = np.interp(
            t_tp_ratios,
            SCS_DIMENSIONLESS_UH[:, 0],
            SCS_DIMENSIONLESS_UH[:, 1],
            left=0.0,
            right=0.0,
        )

        # Scale to actual discharge
        ordinates = q_qp_ratios * qp

        return UnitHydrographResult(
            times_min=times,
            ordinates_m3s=ordinates,
            time_to_peak_min=tp,
            peak_discharge_m3s=qp,
            time_base_min=tb,
            lag_time_min=self.lag_time_min,
            timestep_min=timestep_min,
        )
