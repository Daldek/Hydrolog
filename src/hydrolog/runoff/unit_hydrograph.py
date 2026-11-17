"""SCS Unit Hydrograph generation."""

import math
import warnings
from dataclasses import dataclass
from typing import cast

import numpy as np
from numpy.typing import NDArray

from hydrolog._ranges import typical_range, warn_if_outside
from hydrolog._serialization import JsonResultMixin
from hydrolog._warnings import UhSubsteps
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

# The longest time step of the unit hydrograph, a share of its time to peak (the typical
# range of hydrolog._ranges): a longer step is computed on sub-steps (see generate)
_STEP_SHARE = cast(float, typical_range("scs", "timestep_min").maximum)


@dataclass
class UnitHydrographResult(JsonResultMixin):
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

        Warns
        -----
        OutsideTypicalRange
            If ``area_km2`` is larger than the watersheds the unit hydrograph is
            applied to without dividing them (method ``scs``; the ranges and their
            sources: :data:`hydrolog._ranges.TYPICAL_RANGES`).
        """
        if area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")
        if tc_min <= 0:
            raise InvalidParameterError(f"tc_min must be positive, got {tc_min}")
        warn_if_outside("scs", "area_km2", area_km2)

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

        The ordinates are the dimensionless unit hydrograph of the duration D =
        ``timestep_min`` sampled at the step times. A step beyond the typical range
        of the time step (``timestep_min`` above a share of tp,
        :data:`hydrolog._ranges.TYPICAL_RANGES`) leaves too few ordinates, and their
        sum loses volume: 0.52 mm instead of 1 mm for tc = 90.7 min at a step of
        1440 min. Such a step is divided into the fewest equal sub-steps inside the
        range: the unit hydrograph of a sub-step, sampled on the sub-steps, takes the
        1 mm of the step spread evenly over them, and the result is read at the step
        times. It keeps the volume of the sub-step's unit hydrograph, while ``tp``,
        ``qp`` and ``tb`` stay the formulas' values for D = ``timestep_min``. A step
        inside the range is sampled as it always was.

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
            If timestep_min is not positive, or the time of concentration is too
            short to divide the step into sub-steps inside its range.

        Warns
        -----
        UhSubsteps
            When the step was computed on sub-steps (notice ``uh_substeps``, info).

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
        substeps = self._substeps(timestep_min)
        if substeps == 1:
            times, ordinates = self._sampled(timestep_min)
        else:
            times, ordinates = self._spread(timestep_min, substeps)
            warnings.warn(
                UhSubsteps(
                    timestep_min=timestep_min,
                    maximum_min=_STEP_SHARE * tp,
                    substeps=substeps,
                    substep_min=timestep_min / substeps,
                ),
                stacklevel=2,
            )

        return UnitHydrographResult(
            times_min=times,
            ordinates_m3s=ordinates,
            time_to_peak_min=tp,
            peak_discharge_m3s=qp,
            time_base_min=tb,
            lag_time_min=self.lag_time_min,
            timestep_min=timestep_min,
        )

    def _substeps(self, timestep_min: float) -> int:
        """Return the fewest equal sub-steps of a step inside its range (1: none)."""
        if timestep_min <= _STEP_SHARE * self.time_to_peak(timestep_min):
            return 1
        # The longest sub-step d inside the range: d <= share * (d / 2 + tlag)
        longest = _STEP_SHARE * self.lag_time_min / (1.0 - _STEP_SHARE / 2.0)
        ratio = timestep_min / longest if longest > 0 else math.inf
        if not math.isfinite(ratio):
            raise InvalidParameterError(
                f"tc_min = {self.tc_min:g} min is too short to divide the time step "
                f"of {timestep_min:g} min into sub-steps of the SCS unit hydrograph"
            )
        substeps = max(2, math.ceil(ratio))
        while timestep_min / substeps > _STEP_SHARE * self.time_to_peak(
            timestep_min / substeps
        ):  # rounding at the bound
            substeps += 1
        return substeps

    def _sampled(
        self, timestep_min: float
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the dimensionless unit hydrograph sampled at the step times."""
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
        return times, q_qp_ratios * qp

    def _spread(
        self, timestep_min: float, substeps: int
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the response to 1 mm spread over the sub-steps, at the step times.

        With u the unit hydrograph of a sub-step d on the sub-steps and n of them in
        a step, the step's 1 mm is 1/n mm in each, so the ordinate at the step time
        k n d is the mean of u over the n sub-steps up to it,
        (u[(k - 1) n + 1] + ... + u[k n]) / n: the discrete convolution on the
        sub-steps read at every n-th of them, from cumulative sums, so that a large n
        costs nothing. The ordinates sum to the sub-steps' ordinates divided by n,
        hence the same volume. The last one is 0.
        """
        _, fine = self._sampled(timestep_min / substeps)
        last = fine.size - 1  # u[last] is 0: t / tp beyond the table
        cumulative = np.concatenate(([0.0], np.cumsum(fine)))
        steps = -(-last // substeps) + 1
        sums = [
            cumulative[min(k * substeps, last) + 1]
            - cumulative[min(max((k - 1) * substeps + 1, 0), last + 1)]
            for k in range(steps + 1)
        ]
        times = np.arange(steps + 1, dtype=np.float64) * timestep_min
        return times, np.asarray(sums, dtype=np.float64) / substeps
