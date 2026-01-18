"""Discrete convolution for rainfall-runoff transformation."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


@dataclass
class HydrographResult:
    """
    Result of hydrograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    discharge_m3s : NDArray[np.float64]
        Discharge values [m³/s].
    peak_discharge_m3s : float
        Peak discharge [m³/s].
    time_to_peak_min : float
        Time to peak discharge [min].
    total_volume_m3 : float
        Total runoff volume [m³].
    timestep_min : float
        Time step [min].
    """

    times_min: NDArray[np.float64]
    discharge_m3s: NDArray[np.float64]
    peak_discharge_m3s: float
    time_to_peak_min: float
    total_volume_m3: float
    timestep_min: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)

    @property
    def duration_min(self) -> float:
        """Total duration [min]."""
        if len(self.times_min) > 0:
            return float(self.times_min[-1])
        return 0.0


def convolve_discrete(
    effective_precip_mm: NDArray[np.float64],
    unit_hydrograph_m3s: NDArray[np.float64],
    timestep_min: float,
) -> HydrographResult:
    """
    Perform discrete convolution of effective precipitation and unit hydrograph.

    The convolution transforms effective rainfall into a direct runoff
    hydrograph using the principle of superposition.

    Parameters
    ----------
    effective_precip_mm : NDArray[np.float64]
        Effective precipitation (runoff depth) for each time step [mm].
    unit_hydrograph_m3s : NDArray[np.float64]
        Unit hydrograph ordinates [m³/s per mm].
    timestep_min : float
        Time step [min].

    Returns
    -------
    HydrographResult
        Resulting hydrograph from convolution.

    Raises
    ------
    InvalidParameterError
        If input arrays are empty or timestep is not positive.

    Notes
    -----
    The discrete convolution formula:
    Q(n) = Σ Pe(m) * UH(n - m + 1) for m = 1 to min(n, M)

    where:
    - Q(n): discharge at time step n
    - Pe(m): effective precipitation at time step m
    - UH(k): unit hydrograph ordinate at time step k
    - M: number of precipitation time steps

    The resulting hydrograph has length = len(Pe) + len(UH) - 1

    Examples
    --------
    >>> pe = np.array([0.0, 5.0, 10.0, 8.0, 3.0])  # mm
    >>> uh = np.array([0.0, 0.5, 1.0, 0.8, 0.4, 0.1])  # m³/s per mm
    >>> result = convolve_discrete(pe, uh, timestep_min=5.0)
    >>> print(f"Qmax = {result.peak_discharge_m3s:.2f} m³/s")
    """
    if timestep_min <= 0:
        raise InvalidParameterError(
            f"timestep_min must be positive, got {timestep_min}"
        )

    pe = np.asarray(effective_precip_mm, dtype=np.float64)
    uh = np.asarray(unit_hydrograph_m3s, dtype=np.float64)

    if len(pe) == 0:
        raise InvalidParameterError("effective_precip_mm cannot be empty")
    if len(uh) == 0:
        raise InvalidParameterError("unit_hydrograph_m3s cannot be empty")

    # Perform convolution
    # The unit hydrograph is in [m³/s per mm], so multiplying by mm gives m³/s
    discharge = np.convolve(pe, uh, mode="full")

    # Generate time array
    n_steps = len(discharge)
    times = np.arange(n_steps, dtype=np.float64) * timestep_min

    # Find peak
    peak_idx = int(np.argmax(discharge))
    peak_discharge = float(discharge[peak_idx])
    time_to_peak = float(times[peak_idx])

    # Calculate total volume
    # Q [m³/s] * dt [min] * 60 [s/min] = volume [m³] per step
    timestep_s = timestep_min * 60.0
    total_volume = float(np.sum(discharge) * timestep_s)

    return HydrographResult(
        times_min=times,
        discharge_m3s=discharge,
        peak_discharge_m3s=peak_discharge,
        time_to_peak_min=time_to_peak,
        total_volume_m3=total_volume,
        timestep_min=timestep_min,
    )
