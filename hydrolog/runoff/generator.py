"""Hydrograph generator combining SCS-CN, unit hydrograph, and convolution."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError
from hydrolog.precipitation.hietogram import HietogramResult
from hydrolog.runoff.convolution import HydrographResult, convolve_discrete
from hydrolog.runoff.scs_cn import AMC, SCSCN
from hydrolog.runoff.unit_hydrograph import SCSUnitHydrograph
from hydrolog.runoff.nash_iuh import NashIUH
from hydrolog.runoff.clark_iuh import ClarkIUH
from hydrolog.runoff.snyder_uh import SnyderUH


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
    configurable unit hydrograph models, and discrete convolution
    to produce a direct runoff hydrograph from a precipitation event.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²].
    cn : int
        SCS Curve Number (1-100) for AMC-II conditions.
    tc_min : float, optional
        Time of concentration [min]. Required for SCS and Clark models.
    ia_coefficient : float, optional
        Initial abstraction coefficient, by default 0.2.
    uh_model : str, optional
        Unit hydrograph model: "scs" (default), "nash", "clark", "snyder".
    uh_params : dict, optional
        Model-specific parameters. See Notes for details.

    Notes
    -----
    Model-specific parameters (uh_params):

    **SCS model (default):** No additional parameters required.
    Uses tc_min from constructor.

    **Nash model:**
    - n : float - Number of reservoirs (shape parameter)
    - k : float - Storage constant [hours or minutes, see k_unit]
    - k_unit : str - Unit for k: "hours" (default) or "min"

    Example: ``uh_params={"n": 3.0, "k": 0.8, "k_unit": "hours"}``

    **Clark model:**
    - r : float - Storage coefficient [min]

    Uses tc_min from constructor.
    Example: ``uh_params={"r": 30.0}``

    **Snyder model:**
    - L_km : float - Main stream length [km]
    - Lc_km : float - Length to watershed centroid [km]
    - ct : float, optional - Empirical coefficient (default 1.5)
    - cp : float, optional - Empirical coefficient (default 0.6)

    Example: ``uh_params={"L_km": 15.0, "Lc_km": 8.0}``

    Examples
    --------
    >>> from hydrolog.runoff import HydrographGenerator
    >>> from hydrolog.precipitation import BetaHietogram
    >>>
    >>> # Create hyetograph
    >>> hietogram = BetaHietogram(alpha=2.0, beta=5.0)
    >>> precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)
    >>>
    >>> # SCS model (default)
    >>> generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
    >>> result = generator.generate(precip)
    >>>
    >>> # Nash model
    >>> generator_nash = HydrographGenerator(
    ...     area_km2=45.0, cn=72,
    ...     uh_model="nash",
    ...     uh_params={"n": 3.0, "k": 0.8}
    ... )
    >>>
    >>> print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
    """

    # Supported unit hydrograph models
    SUPPORTED_MODELS = ("scs", "nash", "clark", "snyder")

    def __init__(
        self,
        area_km2: float,
        cn: int,
        tc_min: Optional[float] = None,
        ia_coefficient: float = 0.2,
        uh_model: str = "scs",
        uh_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize hydrograph generator.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²]. Must be positive.
        cn : int
            SCS Curve Number (1-100).
        tc_min : float, optional
            Time of concentration [min]. Required for SCS and Clark models.
        ia_coefficient : float, optional
            Initial abstraction coefficient, by default 0.2.
        uh_model : str, optional
            Unit hydrograph model name, by default "scs".
        uh_params : dict, optional
            Model-specific parameters.

        Raises
        ------
        InvalidParameterError
            If any parameter is invalid.
        """
        if area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")

        uh_model = uh_model.lower()
        if uh_model not in self.SUPPORTED_MODELS:
            raise InvalidParameterError(
                f"uh_model must be one of {self.SUPPORTED_MODELS}, got '{uh_model}'"
            )

        # tc_min required for SCS and Clark
        if uh_model in ("scs", "clark") and tc_min is None:
            raise InvalidParameterError(
                f"tc_min is required for '{uh_model}' model"
            )
        if tc_min is not None and tc_min <= 0:
            raise InvalidParameterError(f"tc_min must be positive, got {tc_min}")

        self.area_km2 = area_km2
        self.tc_min = tc_min
        self.uh_model = uh_model
        self.uh_params = uh_params or {}

        # Initialize SCS-CN component
        self.scs_cn = SCSCN(cn=cn, ia_coefficient=ia_coefficient)

        # Initialize unit hydrograph model
        self.unit_hydrograph = self._create_unit_hydrograph()

    def _create_unit_hydrograph(self) -> Any:
        """
        Create unit hydrograph model based on uh_model setting.

        Returns
        -------
        Unit hydrograph model instance.
        """
        if self.uh_model == "scs":
            return SCSUnitHydrograph(area_km2=self.area_km2, tc_min=self.tc_min)

        elif self.uh_model == "nash":
            n = self.uh_params.get("n")
            k = self.uh_params.get("k")
            k_unit = self.uh_params.get("k_unit", "hours")

            if n is None:
                raise InvalidParameterError(
                    "Nash model requires 'n' parameter in uh_params"
                )
            if k is None:
                raise InvalidParameterError(
                    "Nash model requires 'k' parameter in uh_params"
                )

            # Convert k to minutes if in hours
            if k_unit == "hours":
                k_min = k * 60.0
            else:
                k_min = k

            return NashIUH(n=n, k_min=k_min, area_km2=self.area_km2)

        elif self.uh_model == "clark":
            r = self.uh_params.get("r")
            if r is None:
                raise InvalidParameterError(
                    "Clark model requires 'r' parameter in uh_params"
                )

            return ClarkIUH(tc_min=self.tc_min, r_min=r, area_km2=self.area_km2)

        elif self.uh_model == "snyder":
            L_km = self.uh_params.get("L_km")
            Lc_km = self.uh_params.get("Lc_km")
            ct = self.uh_params.get("ct", 1.5)
            cp = self.uh_params.get("cp", 0.6)

            if L_km is None:
                raise InvalidParameterError(
                    "Snyder model requires 'L_km' parameter in uh_params"
                )
            if Lc_km is None:
                raise InvalidParameterError(
                    "Snyder model requires 'Lc_km' parameter in uh_params"
                )

            return SnyderUH(
                area_km2=self.area_km2,
                L_km=L_km,
                Lc_km=Lc_km,
                ct=ct,
                cp=cp,
            )

        else:
            raise InvalidParameterError(f"Unknown uh_model: {self.uh_model}")

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
