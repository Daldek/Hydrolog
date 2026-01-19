"""Nash Instantaneous Unit Hydrograph (IUH) generation."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from scipy.special import gamma

from hydrolog.exceptions import InvalidParameterError


@dataclass
class IUHResult:
    """
    Result of Instantaneous Unit Hydrograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_per_min : NDArray[np.float64]
        IUH ordinates [1/min]. These represent the fraction of
        unit input released per minute.
    n : float
        Number of reservoirs (shape parameter).
    k_min : float
        Reservoir storage constant [min].
    time_to_peak_min : float
        Time to peak discharge [min].
    peak_ordinate_per_min : float
        Peak IUH ordinate [1/min].
    """

    times_min: NDArray[np.float64]
    ordinates_per_min: NDArray[np.float64]
    n: float
    k_min: float
    time_to_peak_min: float
    peak_ordinate_per_min: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)

    @property
    def lag_time_min(self) -> float:
        """Lag time (first moment) [min]."""
        return self.n * self.k_min


@dataclass
class NashUHResult:
    """
    Result of Nash Unit Hydrograph (finite duration D).

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
    time_to_peak_min : float
        Time to peak discharge [min].
    peak_discharge_m3s : float
        Peak discharge [m³/s per mm].
    n : float
        Number of reservoirs (shape parameter).
    k_min : float
        Reservoir storage constant [min].
    """

    times_min: NDArray[np.float64]
    ordinates_m3s: NDArray[np.float64]
    duration_min: float
    area_km2: float
    time_to_peak_min: float
    peak_discharge_m3s: float
    n: float
    k_min: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)


class NashIUH:
    """
    Nash Instantaneous Unit Hydrograph (IUH).

    The Nash model represents the watershed as a cascade of n identical
    linear reservoirs, each with storage constant K. The IUH is the
    response to an instantaneous unit input (Dirac delta function).

    Parameters
    ----------
    n : float
        Number of reservoirs (shape parameter). Can be non-integer.
        Must be > 0. Typical range: 1-10.
    k_min : float
        Reservoir storage constant [min]. Must be > 0.
        Typical range: 10-200 min.

    Notes
    -----
    The Nash IUH formula is:

    .. math::
        u(t) = \\frac{1}{K \\cdot \\Gamma(n)} \\cdot \\left(\\frac{t}{K}\\right)^{n-1} \\cdot e^{-t/K}

    Key properties:
    - Lag time (first moment): tlag = n × K
    - Variance (second moment): σ² = n × K²
    - Time to peak: tp = (n-1) × K  (for n > 1)
    - Peak ordinate: up = (n-1)^(n-1) × e^(-(n-1)) / (K × Γ(n))

    The parameters n and K can be estimated from:
    - Time of concentration and lag time
    - Observed hydrograph moments
    - Recession curve analysis

    References
    ----------
    Nash, J.E. (1957). The form of the instantaneous unit hydrograph.
    International Association of Scientific Hydrology, 45(3), 114-121.

    Examples
    --------
    >>> iuh = NashIUH(n=3.0, k_min=30.0)
    >>> result = iuh.generate(timestep_min=5.0, duration_min=300.0)
    >>> print(f"Lag time: {result.lag_time_min:.1f} min")
    Lag time: 90.0 min
    """

    def __init__(self, n: float, k_min: float) -> None:
        """
        Initialize Nash IUH generator.

        Parameters
        ----------
        n : float
            Number of reservoirs (shape parameter). Must be > 0.
        k_min : float
            Reservoir storage constant [min]. Must be > 0.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.
        """
        if n <= 0:
            raise InvalidParameterError(f"n must be positive, got {n}")
        if k_min <= 0:
            raise InvalidParameterError(f"k_min must be positive, got {k_min}")

        self.n = n
        self.k_min = k_min

    @property
    def lag_time_min(self) -> float:
        """
        Lag time (first moment of IUH) [min].

        The lag time is the time from the centroid of rainfall
        to the centroid of runoff.

        Notes
        -----
        Formula: tlag = n × K
        """
        return self.n * self.k_min

    @property
    def time_to_peak_min(self) -> float:
        """
        Time to peak of IUH [min].

        Notes
        -----
        Formula: tp = (n-1) × K for n > 1
        For n <= 1, the peak is at t = 0.
        """
        if self.n <= 1:
            return 0.0
        return (self.n - 1) * self.k_min

    @property
    def peak_ordinate_per_min(self) -> float:
        """
        Peak ordinate of IUH [1/min].

        Notes
        -----
        Formula: up = (n-1)^(n-1) × e^(-(n-1)) / (K × Γ(n)) for n > 1
        For n = 1, up = 1/K (exponential decay).
        """
        if self.n <= 1:
            return 1.0 / self.k_min

        n_minus_1 = self.n - 1
        numerator = (n_minus_1 ** n_minus_1) * np.exp(-n_minus_1)
        denominator = self.k_min * gamma(self.n)
        return float(numerator / denominator)

    def ordinate(self, t_min: float) -> float:
        """
        Calculate IUH ordinate at time t.

        Parameters
        ----------
        t_min : float
            Time [min].

        Returns
        -------
        float
            IUH ordinate u(t) [1/min].
        """
        if t_min <= 0:
            return 0.0

        t_over_k = t_min / self.k_min
        coefficient = 1.0 / (self.k_min * gamma(self.n))
        return float(coefficient * (t_over_k ** (self.n - 1)) * np.exp(-t_over_k))

    def generate(
        self,
        timestep_min: float = 5.0,
        duration_min: Optional[float] = None,
    ) -> IUHResult:
        """
        Generate Nash Instantaneous Unit Hydrograph.

        Parameters
        ----------
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.
        duration_min : float, optional
            Total duration of IUH [min]. If not specified, uses
            5 × lag_time or until ordinate < 0.001 × peak.

        Returns
        -------
        IUHResult
            Generated IUH with times and ordinates.

        Raises
        ------
        InvalidParameterError
            If timestep_min is not positive.

        Examples
        --------
        >>> iuh = NashIUH(n=3.0, k_min=30.0)
        >>> result = iuh.generate(timestep_min=5.0)
        >>> print(f"Peak at {result.time_to_peak_min:.1f} min")
        Peak at 60.0 min
        """
        if timestep_min <= 0:
            raise InvalidParameterError(
                f"timestep_min must be positive, got {timestep_min}"
            )

        # Determine duration
        if duration_min is None:
            # Use 5× lag time or extend until ordinate is negligible
            duration_min = max(5.0 * self.lag_time_min, 10.0 * self.k_min)

        if duration_min <= 0:
            raise InvalidParameterError(
                f"duration_min must be positive, got {duration_min}"
            )

        # Generate time array
        n_steps = int(np.ceil(duration_min / timestep_min)) + 1
        times = np.arange(n_steps, dtype=np.float64) * timestep_min

        # Calculate ordinates using vectorized operations
        ordinates = np.zeros(n_steps, dtype=np.float64)
        mask = times > 0
        t_over_k = times[mask] / self.k_min
        coefficient = 1.0 / (self.k_min * gamma(self.n))
        ordinates[mask] = coefficient * (t_over_k ** (self.n - 1)) * np.exp(-t_over_k)

        return IUHResult(
            times_min=times,
            ordinates_per_min=ordinates,
            n=self.n,
            k_min=self.k_min,
            time_to_peak_min=self.time_to_peak_min,
            peak_ordinate_per_min=self.peak_ordinate_per_min,
        )

    def to_unit_hydrograph(
        self,
        area_km2: float,
        duration_min: float,
        timestep_min: float = 5.0,
        total_duration_min: Optional[float] = None,
    ) -> NashUHResult:
        """
        Convert IUH to D-minute Unit Hydrograph.

        Generates a unit hydrograph for rainfall of duration D
        by integrating the IUH over the rainfall duration.

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
            uses 5 × lag_time + duration.

        Returns
        -------
        NashUHResult
            Unit hydrograph with ordinates in m³/s per mm.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.

        Notes
        -----
        The D-minute unit hydrograph is computed as:

        .. math::
            U(t) = \\frac{1}{D} \\int_0^D u(t - \\tau) d\\tau

        where u(t) is the IUH. This is implemented as the average
        of S-curves shifted by duration D:

        .. math::
            U(t) = \\frac{S(t) - S(t-D)}{D}

        where S(t) is the S-curve (integral of IUH).

        The ordinates are then scaled by area to get m³/s per mm:

        .. math::
            Q(t) = U(t) \\cdot A \\cdot 1000 / 60

        Examples
        --------
        >>> iuh = NashIUH(n=3.0, k_min=30.0)
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
            total_duration_min = 5.0 * self.lag_time_min + duration_min

        # Generate time array
        n_steps = int(np.ceil(total_duration_min / timestep_min)) + 1
        times = np.arange(n_steps, dtype=np.float64) * timestep_min

        # Compute S-curve (cumulative integral of IUH)
        # S(t) = integral from 0 to t of u(τ) dτ
        # For Nash model: S(t) = incomplete gamma function
        s_curve = self._s_curve(times)

        # Compute D-minute UH using S-curve method
        # U(t) = (S(t) - S(t-D)) / D
        s_curve_shifted = self._s_curve(times - duration_min)
        uh_dimensionless = (s_curve - s_curve_shifted) / duration_min

        # Scale to m³/s per mm
        # 1 mm over area_km2 = area_km2 * 1e6 m² * 0.001 m = area_km2 * 1000 m³
        # Distributed over time, with IUH in 1/min:
        # Q [m³/s] = ordinate [1/min] × volume [m³] / 60 [s/min]
        volume_m3_per_mm = area_km2 * 1000.0  # m³ per mm of rainfall
        ordinates_m3s = uh_dimensionless * volume_m3_per_mm / 60.0

        # Find peak
        peak_idx = np.argmax(ordinates_m3s)
        time_to_peak = times[peak_idx]
        peak_discharge = float(ordinates_m3s[peak_idx])

        return NashUHResult(
            times_min=times,
            ordinates_m3s=ordinates_m3s,
            duration_min=duration_min,
            area_km2=area_km2,
            time_to_peak_min=time_to_peak,
            peak_discharge_m3s=peak_discharge,
            n=self.n,
            k_min=self.k_min,
        )

    def _s_curve(self, times: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        Compute S-curve (cumulative IUH).

        The S-curve represents the response to a continuous unit input
        starting at t=0. For the Nash model, it equals the regularized
        incomplete gamma function.

        Parameters
        ----------
        times : NDArray[np.float64]
            Time values [min].

        Returns
        -------
        NDArray[np.float64]
            S-curve values (dimensionless, 0 to 1).
        """
        from scipy.special import gammainc

        result = np.zeros_like(times, dtype=np.float64)
        mask = times > 0
        t_over_k = times[mask] / self.k_min
        # gammainc is the regularized lower incomplete gamma function
        # P(a, x) = γ(a, x) / Γ(a)
        result[mask] = gammainc(self.n, t_over_k)
        return result

    @classmethod
    def from_tc(
        cls,
        tc_min: float,
        n: Optional[float] = None,
        lag_ratio: float = 0.6,
    ) -> "NashIUH":
        """
        Create NashIUH from time of concentration.

        Estimates Nash parameters from the time of concentration
        using empirical relationships.

        Parameters
        ----------
        tc_min : float
            Time of concentration [min].
        n : float, optional
            Number of reservoirs. If not specified, uses n=3
            (common default for natural watersheds).
        lag_ratio : float, optional
            Ratio of lag time to tc, by default 0.6 (SCS relationship).

        Returns
        -------
        NashIUH
            Configured Nash IUH generator.

        Notes
        -----
        The parameters are estimated as:
        - tlag = lag_ratio × tc (default: 0.6 × tc)
        - K = tlag / n

        Common values of n:
        - n = 2-3: Steep, small watersheds
        - n = 3-5: Average natural watersheds
        - n = 5-7: Flat, large watersheds

        Examples
        --------
        >>> iuh = NashIUH.from_tc(tc_min=90.0, n=3.0)
        >>> print(f"K = {iuh.k_min:.1f} min")
        K = 18.0 min
        """
        if tc_min <= 0:
            raise InvalidParameterError(f"tc_min must be positive, got {tc_min}")
        if lag_ratio <= 0 or lag_ratio > 1:
            raise InvalidParameterError(
                f"lag_ratio must be in (0, 1], got {lag_ratio}"
            )

        # Default n if not specified
        if n is None:
            n = 3.0

        if n <= 0:
            raise InvalidParameterError(f"n must be positive, got {n}")

        # Estimate lag time and K
        lag_time = lag_ratio * tc_min
        k_min = lag_time / n

        return cls(n=n, k_min=k_min)

    @classmethod
    def from_moments(
        cls,
        lag_time_min: float,
        variance_min2: float,
    ) -> "NashIUH":
        """
        Create NashIUH from statistical moments.

        Estimates Nash parameters from the first two moments
        of an observed hydrograph.

        Parameters
        ----------
        lag_time_min : float
            First moment (lag time) [min].
        variance_min2 : float
            Second central moment (variance) [min²].

        Returns
        -------
        NashIUH
            Configured Nash IUH generator.

        Notes
        -----
        For the Nash model:
        - First moment (mean): M1 = n × K
        - Second moment (variance): M2 = n × K²

        Solving for n and K:
        - K = M2 / M1
        - n = M1 / K = M1² / M2

        Examples
        --------
        >>> iuh = NashIUH.from_moments(lag_time_min=90.0, variance_min2=2700.0)
        >>> print(f"n = {iuh.n:.2f}, K = {iuh.k_min:.1f} min")
        n = 3.00, K = 30.0 min
        """
        if lag_time_min <= 0:
            raise InvalidParameterError(
                f"lag_time_min must be positive, got {lag_time_min}"
            )
        if variance_min2 <= 0:
            raise InvalidParameterError(
                f"variance_min2 must be positive, got {variance_min2}"
            )

        # Solve for K and n
        k_min = variance_min2 / lag_time_min
        n = lag_time_min / k_min  # = lag_time² / variance

        return cls(n=n, k_min=k_min)
