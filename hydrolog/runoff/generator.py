"""Hydrograph generator combining SCS-CN, unit hydrograph, and convolution."""

from dataclasses import dataclass
from typing import Union

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError
from hydrolog.precipitation.hietogram import HietogramResult
from hydrolog.runoff.convolution import HydrographResult, convolve_discrete
from hydrolog.runoff.scs_cn import AMC, SCSCN
from hydrolog.runoff.unit_hydrograph import SCSUnitHydrograph


@dataclass
class HydrographGeneratorResult:
    """
    Complete result of hydrograph generation.

    Attributes
    ----------
    hydrograph : HydrographResult
        The resulting direct runoff hydrograph.
    effective_precip_mm : NDArray[np.float64]
        Effective precipitation for each time step [mm].
    total_precip_mm : float
        Total gross precipitation [mm].
    total_effective_mm : float
        Total effective precipitation (runoff depth) [mm].
    runoff_coefficient : float
        Runoff coefficient C = Pe_total / P_total [-].
    cn_used : int
        Curve Number used (adjusted for AMC).
    retention_mm : float
        Maximum retention S [mm].
    initial_abstraction_mm : float
        Initial abstraction Ia [mm].
    """

    hydrograph: HydrographResult
    effective_precip_mm: NDArray[np.float64]
    total_precip_mm: float
    total_effective_mm: float
    runoff_coefficient: float
    cn_used: int
    retention_mm: float
    initial_abstraction_mm: float

    @property
    def peak_discharge_m3s(self) -> float:
        """Peak discharge [m³/s]."""
        return self.hydrograph.peak_discharge_m3s

    @property
    def time_to_peak_min(self) -> float:
        """Time to peak discharge [min]."""
        return self.hydrograph.time_to_peak_min

    @property
    def total_volume_m3(self) -> float:
        """Total runoff volume [m³]."""
        return self.hydrograph.total_volume_m3


class HydrographGenerator:
    """
    Generate direct runoff hydrograph using SCS-CN method.

    Combines the SCS Curve Number method for rainfall abstraction,
    the SCS dimensionless unit hydrograph, and discrete convolution
    to produce a direct runoff hydrograph from a precipitation event.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²].
    cn : int
        SCS Curve Number (1-100) for AMC-II conditions.
    tc_min : float
        Time of concentration [min].
    ia_coefficient : float, optional
        Initial abstraction coefficient, by default 0.2.

    Examples
    --------
    >>> from hydrolog.runoff import HydrographGenerator
    >>> from hydrolog.precipitation import BetaHietogram
    >>>
    >>> # Create hyetograph
    >>> hietogram = BetaHietogram(alpha=2.0, beta=5.0)
    >>> precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)
    >>>
    >>> # Generate hydrograph
    >>> generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
    >>> result = generator.generate(precip)
    >>>
    >>> print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
    >>> print(f"Time to peak: {result.time_to_peak_min:.0f} min")
    """

    def __init__(
        self,
        area_km2: float,
        cn: int,
        tc_min: float,
        ia_coefficient: float = 0.2,
    ) -> None:
        """
        Initialize hydrograph generator.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²]. Must be positive.
        cn : int
            SCS Curve Number (1-100).
        tc_min : float
            Time of concentration [min]. Must be positive.
        ia_coefficient : float, optional
            Initial abstraction coefficient, by default 0.2.

        Raises
        ------
        InvalidParameterError
            If any parameter is invalid.
        """
        if area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")
        if tc_min <= 0:
            raise InvalidParameterError(f"tc_min must be positive, got {tc_min}")

        self.area_km2 = area_km2
        self.tc_min = tc_min

        # Initialize components
        self.scs_cn = SCSCN(cn=cn, ia_coefficient=ia_coefficient)
        self.unit_hydrograph = SCSUnitHydrograph(area_km2=area_km2, tc_min=tc_min)

    @property
    def cn(self) -> int:
        """Curve Number (AMC-II)."""
        return self.scs_cn.cn

    def generate(
        self,
        precipitation: Union[HietogramResult, NDArray[np.float64], list],
        timestep_min: float = 5.0,
        amc: AMC = AMC.II,
    ) -> HydrographGeneratorResult:
        """
        Generate direct runoff hydrograph.

        Parameters
        ----------
        precipitation : HietogramResult | NDArray[np.float64] | list
            Precipitation input. Can be:
            - HietogramResult: from hyetograph generation
            - Array: precipitation depths for each time step [mm]
        timestep_min : float, optional
            Time step [min], by default 5.0.
            Ignored if precipitation is HietogramResult (uses its timestep).
        amc : AMC, optional
            Antecedent Moisture Condition, by default AMC.II.

        Returns
        -------
        HydrographGeneratorResult
            Complete result including hydrograph and water balance.

        Raises
        ------
        InvalidParameterError
            If precipitation data is invalid.

        Examples
        --------
        >>> generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        >>> result = generator.generate(
        ...     precipitation=[5.0, 10.0, 15.0, 10.0, 5.0, 3.0],
        ...     timestep_min=10.0
        ... )
        >>> print(f"Qmax = {result.peak_discharge_m3s:.2f} m³/s")
        """
        # Extract precipitation array and timestep
        if isinstance(precipitation, HietogramResult):
            precip_mm = precipitation.intensities_mm
            dt = precipitation.timestep_min
            total_precip = precipitation.total_mm
        else:
            precip_mm = np.asarray(precipitation, dtype=np.float64)
            dt = timestep_min
            total_precip = float(np.sum(precip_mm))

        if len(precip_mm) == 0:
            raise InvalidParameterError("Precipitation array cannot be empty")

        if dt <= 0:
            raise InvalidParameterError(f"timestep_min must be positive, got {dt}")

        # Calculate effective precipitation
        eff_result = self.scs_cn.effective_precipitation(precip_mm, amc=amc)
        effective_mm = np.asarray(eff_result.effective_mm, dtype=np.float64)

        # Generate unit hydrograph
        uh_result = self.unit_hydrograph.generate(timestep_min=dt)

        # Perform convolution
        hydrograph = convolve_discrete(
            effective_precip_mm=effective_mm,
            unit_hydrograph_m3s=uh_result.ordinates_m3s,
            timestep_min=dt,
        )

        # Calculate runoff coefficient
        if total_precip > 0:
            runoff_coef = eff_result.total_effective_mm / total_precip
        else:
            runoff_coef = 0.0

        return HydrographGeneratorResult(
            hydrograph=hydrograph,
            effective_precip_mm=effective_mm,
            total_precip_mm=total_precip,
            total_effective_mm=eff_result.total_effective_mm,
            runoff_coefficient=runoff_coef,
            cn_used=eff_result.cn_adjusted,
            retention_mm=eff_result.retention_mm,
            initial_abstraction_mm=eff_result.initial_abstraction_mm,
        )
