"""Nash Instantaneous Unit Hydrograph (IUH) generation."""

from dataclasses import dataclass
from typing import Optional, Union

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq
from scipy.special import gamma

from hydrolog.exceptions import InvalidParameterError


@dataclass
class LutzCalculationResult:
    """
    Intermediate calculation results from Lutz method.

    Contains all values computed during Nash parameter estimation,
    useful for detailed reports showing calculation steps.

    Attributes
    ----------
    L_km : float
        Main stream length [km].
    Lc_km : float
        Length to catchment centroid [km].
    slope : float
        Stream slope [-].
    manning_n : float
        Manning's roughness coefficient [-].
    urban_pct : float
        Urbanized area percentage [%].
    forest_pct : float
        Forested area percentage [%].
    P1 : float
        Coefficient P1 = 3.989 * n + 0.028.
    geometric_factor : float
        Geometric factor (L * Lc / Jg^1.5)^0.26.
    urban_factor : float
        Urban factor exp(-0.016 * U).
    forest_factor : float
        Forest factor exp(0.004 * W).
    tp_hours : float
        Time to peak [hours].
    up_per_hour : float
        Peak IUH ordinate [1/hour].
    f_N_target : float
        Target value for f(N) = tp * up.
    n : float
        Number of reservoirs (Nash parameter).
    k_hours : float
        Storage constant [hours].
    k_min : float
        Storage constant [min].
    """

    L_km: float
    Lc_km: float
    slope: float
    manning_n: float
    urban_pct: float
    forest_pct: float
    P1: float
    geometric_factor: float
    urban_factor: float
    forest_factor: float
    tp_hours: float
    up_per_hour: float
    f_N_target: float
    n: float
    k_hours: float
    k_min: float

    @property
    def tp_min(self) -> float:
        """Time to peak [min]."""
        return self.tp_hours * 60.0

    @property
    def lag_time_min(self) -> float:
        """Lag time = n * K [min]."""
        return self.n * self.k_min

    @property
    def tp_iuh_min(self) -> float:
        """Time to peak of IUH = (n-1) * K [min]."""
        return (self.n - 1) * self.k_min


@dataclass
class IUHResult:
    """
    Result of Instantaneous Unit Hydrograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_per_min : NDArray[np.float64]
        IUH ordinates (rzędne) [1/min]. These represent the fraction of
        unit input released per minute.
    n : float
        Number of reservoirs (shape parameter).
    k_min : float
        Reservoir storage constant [min].
    time_to_peak_min : float
        Time to peak discharge [min].
    peak_ordinate_per_min : float
        Peak IUH ordinate (rzędna szczytowa) [1/min].
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

    def __init__(
        self,
        n: float,
        k_min: float,
        area_km2: Optional[float] = None,
        lutz_params: Optional[LutzCalculationResult] = None,
    ) -> None:
        """
        Initialize Nash IUH generator.

        Parameters
        ----------
        n : float
            Number of reservoirs (shape parameter). Must be > 0.
        k_min : float
            Reservoir storage constant [min]. Must be > 0.
        area_km2 : float, optional
            Watershed area [km²]. If provided, generate() returns
            dimensional unit hydrograph [m³/s per mm].
        lutz_params : LutzCalculationResult, optional
            Intermediate calculation results from Lutz method.
            Stored for report generation.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.
        """
        if n <= 0:
            raise InvalidParameterError(f"n must be positive, got {n}")
        if k_min <= 0:
            raise InvalidParameterError(f"k_min must be positive, got {k_min}")
        if area_km2 is not None and area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")

        self.n = n
        self.k_min = k_min
        self.area_km2 = area_km2
        self.lutz_params = lutz_params

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
    ) -> Union[IUHResult, NashUHResult]:
        """
        Generate Nash Unit Hydrograph.

        If area_km2 was provided in constructor, returns dimensional
        unit hydrograph [m³/s per mm]. Otherwise returns IUH [1/min].

        Parameters
        ----------
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.
        duration_min : float, optional
            Total duration [min]. If not specified, uses
            5 × lag_time or until ordinate < 0.001 × peak.

        Returns
        -------
        IUHResult or NashUHResult
            IUHResult if area_km2 not provided (ordinates in 1/min).
            NashUHResult if area_km2 provided (ordinates in m³/s per mm).

        Raises
        ------
        InvalidParameterError
            If timestep_min is not positive.

        Examples
        --------
        >>> # Without area - returns IUH
        >>> iuh = NashIUH(n=3.0, k_min=30.0)
        >>> result = iuh.generate(timestep_min=5.0)
        >>> print(f"Peak at {result.time_to_peak_min:.1f} min")
        Peak at 60.0 min

        >>> # With area - returns dimensional UH
        >>> nash = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)
        >>> result = nash.generate(timestep_min=5.0)
        >>> print(f"Peak: {result.peak_discharge_m3s:.2f} m³/s per mm")
        """
        if self.area_km2 is not None:
            # Return dimensional unit hydrograph
            return self.to_unit_hydrograph(
                area_km2=self.area_km2,
                duration_min=timestep_min,  # D = timestep for UH
                timestep_min=timestep_min,
                total_duration_min=duration_min,
            )
        else:
            # Return IUH
            return self.generate_iuh(
                timestep_min=timestep_min, duration_min=duration_min
            )

    def generate_iuh(
        self,
        timestep_min: float = 5.0,
        duration_min: Optional[float] = None,
    ) -> IUHResult:
        """
        Generate Nash Instantaneous Unit Hydrograph.

        Always returns IUH regardless of area_km2 setting.

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
            Generated IUH with times and ordinates [1/min].

        Raises
        ------
        InvalidParameterError
            If timestep_min is not positive.

        Examples
        --------
        >>> iuh = NashIUH(n=3.0, k_min=30.0)
        >>> result = iuh.generate_iuh(timestep_min=5.0)
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
    def from_lutz(
        cls,
        L_km: float,
        Lc_km: float,
        slope: float,
        manning_n: float,
        urban_pct: float = 0.0,
        forest_pct: float = 0.0,
        area_km2: Optional[float] = None,
    ) -> "NashIUH":
        """
        Create NashIUH using Lutz method for ungauged catchments.

        The Lutz method estimates Nash model parameters from catchment
        physiographic characteristics. Recommended for non-urbanized
        catchments.

        Parameters
        ----------
        L_km : float
            Main stream length from outlet to watershed divide [km].
        Lc_km : float
            Length along main stream from outlet to the point
            nearest to catchment centroid [km].
        slope : float
            Average slope of main stream [-] (e.g., 0.01 for 1%).
        manning_n : float
            Manning's roughness coefficient for main channel [-].
            Typical values: 0.025-0.050 for natural streams.
        urban_pct : float, optional
            Percentage of urbanized area [%], by default 0.0.
        forest_pct : float, optional
            Percentage of forested area [%], by default 0.0.
        area_km2 : float, optional
            Watershed area [km²]. If provided, generate() returns
            dimensional unit hydrograph [m³/s per mm].

        Returns
        -------
        NashIUH
            Configured Nash IUH generator.

        Raises
        ------
        InvalidParameterError
            If any parameter is invalid or if N cannot be determined.

        Notes
        -----
        The Lutz method computes:

        1. Time to peak of unit hydrograph:

        .. math::
            t_p = P_1 \\cdot \\left(\\frac{L \\cdot L_c}{J_g^{1.5}}\\right)^{0.26}
                  \\cdot e^{-0.016 U} \\cdot e^{0.004 W}

        where :math:`P_1 = 3.989 n + 0.028` (n = Manning coefficient).

        2. Peak IUH ordinate:

        .. math::
            u_p = \\frac{0.66}{t_p^{1.04}}

        3. Shape function:

        .. math::
            f(N) = t_p \\cdot u_p

        4. Parameter N is found by solving:

        .. math::
            f(N) = \\frac{(N-1)^N \\cdot e^{-(N-1)}}{\\Gamma(N)}

        5. Storage coefficient:

        .. math::
            K = \\frac{t_p}{N-1}

        References
        ----------
        Lutz, W. (1984). Berechnung von Hochwasserabflüssen unter
        Anwendung von Gebietskenngrößen. Mitteilungen des Instituts
        für Hydrologie und Wasserwirtschaft, H. 24, Universität Karlsruhe.

        KZGW (2017). Aktualizacja metodyki obliczania przepływów
        i opadów maksymalnych. Załącznik 2, Tabela C.2.

        Examples
        --------
        >>> nash = NashIUH.from_lutz(
        ...     L_km=15.0,
        ...     Lc_km=8.0,
        ...     slope=0.02,
        ...     manning_n=0.035,
        ...     forest_pct=40.0
        ... )
        >>> print(f"n = {nash.n:.2f}, K = {nash.k_min:.1f} min")
        """
        # Validate inputs
        if L_km <= 0:
            raise InvalidParameterError(f"L_km must be positive, got {L_km}")
        if Lc_km <= 0:
            raise InvalidParameterError(f"Lc_km must be positive, got {Lc_km}")
        if Lc_km > L_km:
            raise InvalidParameterError(
                f"Lc_km ({Lc_km}) cannot exceed L_km ({L_km})"
            )
        if slope <= 0:
            raise InvalidParameterError(f"slope must be positive, got {slope}")
        if manning_n <= 0:
            raise InvalidParameterError(
                f"manning_n must be positive, got {manning_n}"
            )
        if urban_pct < 0 or urban_pct > 100:
            raise InvalidParameterError(
                f"urban_pct must be in [0, 100], got {urban_pct}"
            )
        if forest_pct < 0 or forest_pct > 100:
            raise InvalidParameterError(
                f"forest_pct must be in [0, 100], got {forest_pct}"
            )
        if area_km2 is not None and area_km2 <= 0:
            raise InvalidParameterError(
                f"area_km2 must be positive, got {area_km2}"
            )

        # Step 1: Calculate P1 parameter
        P1 = 3.989 * manning_n + 0.028

        # Step 2: Calculate time to peak [hours]
        # tp = P1 * (L * Lc / Jg^1.5)^0.26 * exp(-0.016*U) * exp(0.004*W)
        geometric_factor = (L_km * Lc_km / (slope**1.5)) ** 0.26
        urban_factor = np.exp(-0.016 * urban_pct)
        forest_factor = np.exp(0.004 * forest_pct)
        tp_hours = P1 * geometric_factor * urban_factor * forest_factor

        # Step 3: Calculate peak IUH ordinate [1/hour]
        up_per_hour = 0.66 / (tp_hours**1.04)

        # Step 4: Calculate f(N) = tp * up
        f_N_target = tp_hours * up_per_hour

        # Step 5: Find N by solving f(N) = (N-1)^N * e^(-(N-1)) / Gamma(N)
        def f_N_equation(N_val: float) -> float:
            """Calculate f(N) for Nash model."""
            if N_val <= 1:
                return 0.0
            n_minus_1 = N_val - 1
            numerator = (n_minus_1**N_val) * np.exp(-n_minus_1)
            denominator = gamma(N_val)
            return numerator / denominator

        def objective(N_val: float) -> float:
            """Objective function: f(N) - target = 0."""
            return f_N_equation(N_val) - f_N_target

        # f(N) has maximum around N=2-3, then decreases
        # Typical range for f(N): 0.35 - 0.40
        # Search in range N = 1.1 to 20
        try:
            # Check if solution exists in range
            f_low = objective(1.1)
            f_high = objective(20.0)

            if f_low * f_high > 0:
                # No sign change - check if target is achievable
                f_max = max(f_N_equation(N_val) for N_val in np.linspace(1.1, 20, 100))
                if f_N_target > f_max:
                    raise InvalidParameterError(
                        f"f(N) = {f_N_target:.4f} is too high. "
                        f"Maximum achievable f(N) ≈ {f_max:.4f}. "
                        "Check input parameters."
                    )

            N = brentq(objective, 1.1, 20.0, xtol=1e-6)
        except ValueError as e:
            raise InvalidParameterError(
                f"Could not find valid N for f(N) = {f_N_target:.4f}. "
                f"Error: {e}"
            )

        # Step 6: Calculate K [hours], convert to minutes
        K_hours = tp_hours / (N - 1)
        k_min = K_hours * 60.0

        # Store all intermediate calculation results
        lutz_params = LutzCalculationResult(
            L_km=L_km,
            Lc_km=Lc_km,
            slope=slope,
            manning_n=manning_n,
            urban_pct=urban_pct,
            forest_pct=forest_pct,
            P1=P1,
            geometric_factor=geometric_factor,
            urban_factor=urban_factor,
            forest_factor=forest_factor,
            tp_hours=tp_hours,
            up_per_hour=up_per_hour,
            f_N_target=f_N_target,
            n=N,
            k_hours=K_hours,
            k_min=k_min,
        )

        return cls(n=N, k_min=k_min, area_km2=area_km2, lutz_params=lutz_params)
