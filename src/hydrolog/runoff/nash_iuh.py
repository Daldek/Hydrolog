"""Nash Instantaneous Unit Hydrograph (IUH) generation.

The Nash model represents the watershed as a cascade of n identical
linear reservoirs, each with storage constant K. The IUH is the
response to an instantaneous unit input (Dirac delta function).

References
----------
Nash, J.E. (1957). The form of the instantaneous unit hydrograph.
International Association of Scientific Hydrology, 45(3), 114-121.

Lutz, W. (1984). Berechnung von Hochwasserabflüssen unter Anwendung
von Gebietskenngrößen. Mitteilungen des Instituts für Hydrologie
und Wasserwirtschaft, H. 24, Universität Karlsruhe.

Rosso, R. (1984). Nash model relation to Horton order ratios.
Water Resources Research, 20(7), 914-920.

KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów
maksymalnych. Załącznik 2, Tabela C.2.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Final, NamedTuple

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq
from scipy.special import gamma

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._ranges import warn_if_outside
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Constant,
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    Tolerance,
    Values,
    Variable,
    assert_within,
    convert,
)


@dataclass
class LutzCalculationResult(JsonResultMixin):
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
        Equal-area slope Jg of the main stream's longitudinal profile [m/m].
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


@dataclass
class IUHResult(JsonResultMixin):
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
class NashUHResult(JsonResultMixin):
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
    r"""
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
        u(t) = \frac{1}{K \cdot \Gamma(n)}
            \cdot \left(\frac{t}{K}\right)^{n-1} \cdot e^{-t/K}

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
        area_km2: float | None = None,
        lutz_params: LutzCalculationResult | None = None,
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

        Warns
        -----
        OutsideUnverifiedRange
            If ``n`` or ``k_min`` is outside its typical range (method ``nash``;
            the ranges: :data:`hydrolog._ranges.TYPICAL_RANGES`). The ranges have
            no published source and are kept as to be verified, so the warning is
            this subclass of ``OutsideTypicalRange``. The estimating constructors
            (``from_lutz``, ``from_urban_regression``) do not warn
            about them: the ranges are those of given parameters.
        """
        self._set(n, k_min, area_km2, lutz_params)
        warn_if_outside("nash", "n", n)
        warn_if_outside("nash", "k_min", k_min)

    def _set(
        self,
        n: float,
        k_min: float,
        area_km2: float | None,
        lutz_params: LutzCalculationResult | None,
    ) -> None:
        """Check and keep the parameters (see ``__init__``)."""
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

    @classmethod
    def _estimated(
        cls,
        n: float,
        k_min: float,
        area_km2: float | None = None,
        lutz_params: LutzCalculationResult | None = None,
    ) -> "NashIUH":
        """Return a cascade a method estimated: checked, without range warnings."""
        cascade = cls.__new__(cls)
        cascade._set(n, k_min, area_km2, lutz_params)
        return cascade

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
        numerator = (n_minus_1**n_minus_1) * np.exp(-n_minus_1)
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
        duration_min: float | None = None,
    ) -> IUHResult | NashUHResult:
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
        Peak: 6.75 m³/s per mm
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
        duration_min: float | None = None,
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
        total_duration_min: float | None = None,
    ) -> NashUHResult:
        r"""
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
            U(t) = \frac{1}{D} \int_0^D u(t - \tau) d\tau

        where u(t) is the IUH. This is implemented as the average
        of S-curves shifted by duration D:

        .. math::
            U(t) = \frac{S(t) - S(t-D)}{D}

        where S(t) is the S-curve (integral of IUH).

        The ordinates are then scaled by area to get m³/s per mm:

        .. math::
            Q(t) = U(t) \cdot A \cdot 1000 / 60

        Examples
        --------
        >>> iuh = NashIUH(n=3.0, k_min=30.0)
        >>> uh = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=30.0)
        >>> print(f"Peak: {uh.peak_discharge_m3s:.2f} m³/s per mm")
        Peak: 6.63 m³/s per mm
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
    def from_lutz(
        cls,
        L_km: float,
        Lc_km: float,
        slope: float,
        manning_n: float,
        urban_pct: float = 0.0,
        forest_pct: float = 0.0,
        area_km2: float | None = None,
    ) -> "NashIUH":
        """
        Create NashIUH using Lutz method for ungauged catchments.

        The Lutz method estimates Nash model parameters from catchment
        physiographic characteristics. Recommended for non-urbanized
        catchments. Computes with :func:`lutz_parameters` (spec ``lutz``, whose
        equations, constants, ranges and sources ``docs/FORMULAS.md`` shows).

        Parameters
        ----------
        L_km : float
            Main stream length from outlet to watershed divide [km].
        Lc_km : float
            Length along main stream from outlet to the point
            nearest to catchment centroid [km].
        slope : float
            Equal-area slope Jg of the main stream's longitudinal profile [m/m]: the
            slope of the line from the outlet with equal areas of the profile above
            and below it (:func:`hydrolog.morphometry.equal_area_slope`), not the
            slope between the stream's ends.
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
            If the spec ``lutz`` refuses the inputs (``details.reason`` of the
            standard, ``details.option`` the argument of this method), or if
            ``area_km2`` is not positive.

        Warns
        -----
        OutsideTypicalRange
            If ``area_km2`` is larger than the watersheds KZGW (2017) recommends
            the method for (method ``lutz``; the ranges and their sources:
            :data:`hydrolog._ranges.TYPICAL_RANGES`).

        Notes
        -----
        The peak of the IUH follows Lutz's relation for an infinitesimal step
        (KZGW 2017, eq. 6.19); :meth:`to_unit_hydrograph` averages the IUH over the
        step exactly. KZGW's Ex. 6.2 uses a relation fitted for a step of 1 h
        instead and gets a lower, later peak (spec ``lutz``, its conventions).

        References
        ----------
        Lutz, W. (1984). Berechnung von Hochwasserabflüssen unter
        Anwendung von Gebietskenngrößen. Mitteilungen des Instituts
        für Hydrologie und Wasserwirtschaft, H. 24, Universität Karlsruhe.

        KZGW (2017). Aktualizacja metodyki obliczania przepływów
        i opadów maksymalnych. Załącznik 2, pp. 97-100, Tabela C.2.

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
        n = 3.66, K = 70.9 min
        """
        try:
            estimate = lutz_parameters(
                length_km=L_km,
                centroid_length_km=Lc_km,
                slope_m_per_m=slope,
                manning_n=manning_n,
                urban_pct=urban_pct,
                forest_pct=forest_pct,
            )
        except InvalidParameterError as exc:
            raise _from_lutz_error(exc) from exc
        if area_km2 is not None and area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")
        if area_km2 is not None:
            warn_if_outside("lutz", "area_km2", area_km2)

        lutz_params = LutzCalculationResult(
            L_km=L_km,
            Lc_km=Lc_km,
            slope=slope,
            manning_n=manning_n,
            urban_pct=urban_pct,
            forest_pct=forest_pct,
            P1=estimate.p1,
            geometric_factor=estimate.geometric_factor,
            urban_factor=estimate.urban_factor,
            forest_factor=estimate.forest_factor,
            tp_hours=estimate.time_to_peak_h,
            up_per_hour=estimate.peak_ordinate_per_h,
            f_N_target=estimate.peak_product,
            n=estimate.n,
            k_hours=estimate.k_h,
            k_min=estimate.k_min,
        )
        return cls._estimated(
            n=estimate.n,
            k_min=estimate.k_min,
            area_km2=area_km2,
            lutz_params=lutz_params,
        )

    @classmethod
    def from_urban_regression(
        cls,
        area_km2: float,
        effective_precip_mm: float,
        duration_h: float,
        urban_fraction: float = 0.0,
    ) -> "NashIUH":
        r"""
        Create NashIUH using empirical regression for urbanized catchments.

        Estimates Nash model parameters (N, k) from catchment area,
        effective precipitation, rainfall duration, and urbanization
        index using power-law regression equations developed for
        urbanized and partially urbanized catchments.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²]. Must be positive.
        effective_precip_mm : float
            Total effective precipitation depth [mm]. Must be positive.
        duration_h : float
            Effective rainfall duration [h]. Must be positive.
        urban_fraction : float, optional
            Urbanization index [-], by default 0.0.
            Range [0, 1), where 0 = natural, 0.5 = 50% urbanized.
            Defined as ratio of built-up area to total watershed area.

        Returns
        -------
        NashIUH
            Configured Nash IUH generator with area_km2 set.

        Raises
        ------
        InvalidParameterError
            If any parameter is invalid.

        Notes
        -----
        The method uses power-law regression equations in metric units:

        1. Lag time:

        .. math::
            t_L = 1.28 \cdot A^{0.46} \cdot (1+U)^{-1.66}
                  \cdot H^{-0.27} \cdot D^{0.37}

        2. Storage coefficient:

        .. math::
            k = 0.56 \cdot A^{0.39} \cdot (1+U)^{-0.62}
                \cdot H^{-0.11} \cdot D^{0.22}

        3. Number of reservoirs:

        .. math::
            N = t_L / k

        where A is catchment area [km²], U is urbanization index [-],
        H is effective precipitation [mm], and D is rainfall duration [h].

        **Imperial origin and metric conversion:**

        The original regression (Sarma, Delleur, Rao 1969 [2]) was
        developed at Purdue University on watersheds near Indianapolis,
        Indiana ("between 5 and 20 square miles"). The original
        imperial constants are 0.831 (tL) and ~0.569 (k) for inputs
        in mi² and inches.

        The metric constants 1.28 and 0.56 already incorporate the
        unit conversions and appear in the 1972 ASCE paper [1]::

            c_tL = 0.831 × (1/2.58999)^0.46 × (25.4)^0.27 = 1.285 ≈ 1.28
            c_k  = 0.569 × (1/2.58999)^0.39 × (25.4)^0.11 = 0.560 ≈ 0.56

        Verification: for the same physical watershed, the imperial
        formula (0.831, mi², in) and the metric formula (1.28, km², mm)
        produce identical lag times (difference < 0.4%).

        These metric constants are consistent with Polish hydrological
        literature — see e.g. Kołodziejczyk (2017) [3], Banasik (2009)
        [4].

        The regression was derived from analysis of ~200 storms on
        watersheds with varying degrees of urbanization, relating
        Nash model parameters to meteorological and physiographic
        factors including the urbanization factor.

        References
        ----------
        [1] Rao, R.A.; Delleur, J.W.; Sarma, B.S.P. (1972). Conceptual
        Hydrologic Models for Urbanizing Basins. Journal of the
        Hydraulics Division, ASCE, 98(HY7), 1205-1220.
        TRID record: https://trid.trb.org/view/103282

        [2] Sarma, P.B.S.; Delleur, J.W.; Rao, A.R. (1969). A Program
        in Urban Hydrology, Part II. Purdue University Water Resources
        Research Center, Technical Report No. 9.
        Full text (PDF): https://docs.lib.purdue.edu/watertech/8/

        [3] Kołodziejczyk, K. (2017). Assessment of the impact of
        a parameter estimation method for the Nash Model on selected
        parameters of a catchment discharge hydrograph. E3S Web of
        Conferences, 17, 00041.
        Full text (PDF): https://www.e3s-conferences.org/articles/e3sconf/pdf/2017/05/e3sconf_eko2017_00041.pdf

        [4] Banasik, K. (2009). Wyznaczanie wezbrań powodziowych
        w małych zlewniach zurbanizowanych. Wyd. SGGW, Warszawa.

        Examples
        --------
        >>> nash = NashIUH.from_urban_regression(
        ...     area_km2=1.3,
        ...     effective_precip_mm=1.305,
        ...     duration_h=0.167,
        ...     urban_fraction=0.05,
        ... )
        >>> print(f"N = {nash.n:.3f}, k = {nash.k_min:.1f} min")
        N = 1.621, k = 23.7 min
        """
        estimate = urban_regression_parameters(
            area_km2=area_km2,
            effective_precip_mm=effective_precip_mm,
            duration_h=duration_h,
            urban_fraction=urban_fraction,
        )
        return cls._estimated(n=estimate.n, k_min=estimate.k_min, area_km2=area_km2)


# --- Lutz's estimation of n and K: the spec lutz -------------------------------------

_KZGW_CITATION = (
    "KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o "
    "określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i "
    "niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona)"
)
_KZGW_URL = (
    "https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/"
    "zal-2-do-OPZ-ujednolicony-1.pdf"
)
_SIKORSKA_CITATION = (
    "Sikorska, A.E., Scheidegger, A., Banasik, K., Rieckermann, J. (2012). Bayesian "
    "uncertainty assessment of flood predictions in ungauged urban basins for "
    "conceptual rainfall-runoff models. Hydrology and Earth System Sciences 16, "
    "1221-1236"
)
_SIKORSKA_URL = (
    "https://hess.copernicus.org/articles/16/1221/2012/hess-16-1221-2012.pdf"
)
_HANDOFFS = (
    "Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November "
    "2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa "
    "(134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, "
    "and the guide's Kamiennik to Świerzawa (37.22 km2)"
)
_HANDOFF_FILES = (
    "tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json"
)


def _kzgw(locator: str) -> Source:
    return Source(citation=_KZGW_CITATION, locator=locator, url=_KZGW_URL)


def _sikorska(locator: str) -> Source:
    return Source(citation=_SIKORSKA_CITATION, locator=locator, url=_SIKORSKA_URL)


def _from_handoffs(what: str) -> Source:
    return Source(citation=_HANDOFFS, locator=f"{_HANDOFF_FILES}: {what}")


_N_LOW: Final = 1.1
"""Lower end of the bracket of N: the first row of KZGW's Table C.2."""
_N_HIGH: Final = 20.0
"""Upper end of the bracket of N, far beyond the last row of Table C.2 (7.99)."""
_N_XTOL: Final = 1e-6
"""Absolute tolerance of the root N (scipy.optimize.brentq's ``xtol``)."""


def _peak_product(n: float) -> float:
    """Return f(N) = (N-1)^N e^-(N-1) / Gamma(N), the product tp up of a cascade."""
    n_minus_1 = n - 1
    return float((n_minus_1**n) * np.exp(-n_minus_1) / gamma(n))


class _Steps(NamedTuple):
    """The steps of Lutz's equations before N, as the function computes them."""

    p1: float
    geometric_factor: float
    urban_factor: float
    forest_factor: float
    time_to_peak_h: float
    peak_ordinate_per_h: float
    peak_product: float


def _steps(x: Values) -> _Steps:
    """Return P1, the factors of tp, tp, up and tp up of checked inputs (eqs 6.17-6.20).

    Raises ZeroDivisionError or OverflowError where float64 cannot hold a step, which
    the precondition ``root_in_bracket`` refuses before the formula computes.
    """
    p1 = LUTZ.constant("p1_slope") * x.real("manning_n") + LUTZ.constant("p1_intercept")
    geometric = (
        x.real("length_km")
        * x.real("centroid_length_km")
        / (x.real("slope_m_per_m") ** LUTZ.constant("slope_exponent"))
    ) ** LUTZ.constant("geometric_exponent")
    urban = np.exp(LUTZ.constant("urban_coefficient") * x.real("urban_pct"))
    forest = np.exp(LUTZ.constant("forest_coefficient") * x.real("forest_pct"))
    tp = p1 * geometric * urban * forest
    up = LUTZ.constant("peak_coefficient") / (tp ** LUTZ.constant("peak_exponent"))
    return _Steps(
        p1=p1,
        geometric_factor=geometric,
        urban_factor=urban,
        forest_factor=forest,
        time_to_peak_h=tp,
        peak_ordinate_per_h=up,
        peak_product=tp * up,
    )


def _root_in_bracket(x: Values) -> bool:
    """f(1.1) <= tp up <= f(20): brentq's sign change on the bracket of N."""
    try:
        with np.errstate(all="ignore"):
            target = float(_steps(x).peak_product)
    except (ZeroDivisionError, OverflowError):
        return False
    return _peak_product(_N_LOW) <= target <= _peak_product(_N_HIGH)


# --- oracles and limits (CMP-6.2, CMP-6.5) -------------------------------------------

_ORACLE_POINTS: Final[tuple[dict[str, float], ...]] = (
    # KZGW (2017) Ex. 6.2, the Niedźwiadka at km 3+450
    {
        "length_km": 4.3,
        "centroid_length_km": 2.7,
        "slope_m_per_m": 0.03,
        "manning_n": 0.025,
        "urban_pct": 0.0,
        "forest_pct": 33.6,
    },
    # the guide's Kamiennik to Świerzawa, Jg the equal-area slope of its profile
    {
        "length_km": 15.88,
        "centroid_length_km": 6.76,
        "slope_m_per_m": 0.00848,
        "manning_n": 0.035,
        "urban_pct": 1.0,
        "forest_pct": 57.4,
    },
    # the catalog's example of uh nash
    {
        "length_km": 8.2,
        "centroid_length_km": 4.5,
        "slope_m_per_m": 0.023,
        "manning_n": 0.035,
        "urban_pct": 5.0,
        "forest_pct": 30.0,
    },
    # the shortest and the longest flow path of the hand-offs
    {
        "length_km": 0.0566,
        "centroid_length_km": 0.0042,
        "slope_m_per_m": 0.105,
        "manning_n": 0.025,
        "urban_pct": 0.0,
        "forest_pct": 100.0,
    },
    {
        "length_km": 28.88,
        "centroid_length_km": 14.49,
        "slope_m_per_m": 0.002,
        "manning_n": 0.05,
        "urban_pct": 9.0,
        "forest_pct": 0.0,
    },
)
"""Inputs of the oracles, inside the typical ranges or at their ends."""

_DIGITS = 50
"""Precision of the decimal oracle: far beyond float64's 16 digits."""


def _decimal_steps(point: dict[str, float]) -> tuple[Decimal, Decimal]:
    """Tp and up of the published equations at 50 digits, from the exact inputs."""
    with localcontext(prec=_DIGITS):
        length, centroid, slope, roughness, urban, forest = (
            Decimal(point[name])
            for name in (
                "length_km",
                "centroid_length_km",
                "slope_m_per_m",
                "manning_n",
                "urban_pct",
                "forest_pct",
            )
        )
        p1 = Decimal("3.989") * roughness + Decimal("0.028")
        geometric = (length * centroid / slope ** Decimal("1.5")) ** Decimal("0.26")
        tp = (
            p1
            * geometric
            * (Decimal("-0.016") * urban).exp()
            * (Decimal("0.004") * forest).exp()
        )
        up = Decimal("0.66") / tp ** Decimal("1.04")
        return tp, up


def _decimal_oracle(run: Callable[..., Values]) -> None:
    for point in _ORACLE_POINTS:
        result = run(**point)
        tp, up = _decimal_steps(point)
        assert_within(
            result.real("time_to_peak_h"),
            float(tp),
            rel=1e-13,
            reason="float64 products, powers and exponentials of the inputs against "
            "eq. 6.17 in decimal arithmetic at 50 digits: a few units in the last "
            "place of each step, the constants 3.989, 0.028 and -0.016 one rounding "
            "from their decimal values",
        )
        assert_within(
            result.real("peak_ordinate_per_h"),
            float(up),
            rel=1e-13,
            reason="eq. 6.19 on the tp above: tp's error times 1.04 plus a few units "
            "in the last place of the power and the quotient",
        )


def _cascade_peak(run: Callable[..., Values]) -> None:
    from scipy import stats

    for point in _ORACLE_POINTS:
        result = run(**point)
        tp = result.real("time_to_peak_h")
        n = result.real("n")
        k_h = convert(result.real("k_min"), "min", "h")
        assert_within(
            (n - 1.0) * k_h,
            tp,
            rel=1e-15,
            reason="K = tp / (N - 1) converted to minutes and back: a quotient, a "
            "product by 60, a quotient by 60 and the product (N - 1) K, each one "
            "rounding of float64",
        )
        assert_within(
            float(stats.gamma.pdf(tp, a=n, scale=k_h)),
            result.real("peak_ordinate_per_h"),
            rel=1e-6,
            reason="brentq stops within 1e-6 of the root N (xtol); f'/f <= 0.58 for "
            "N >= 2, as all these points give, so the density at tp, f(N)/tp, is "
            "within 6e-7 of up = (tp up)/tp relative; scipy.stats evaluates the "
            "density through logarithms, a few units in the last place",
        )


def _power_law(run: Callable[..., Values]) -> None:
    base = dict(_ORACLE_POINTS[1])  # Kamiennik: 2 Lc < L, and U + W + 10 < 100
    once = run(**base).real("time_to_peak_h")
    for name, factor, ratio in (
        ("length_km", 2.0, 2.0**0.26),
        ("centroid_length_km", 2.0, 2.0**0.26),
        ("slope_m_per_m", 2.0, 2.0 ** (-1.5 * 0.26)),
    ):
        moved = run(**{**base, name: factor * base[name]}).real("time_to_peak_h")
        assert_within(
            moved / once,
            ratio,
            rel=1e-14,
            reason=f"tp is proportional to {name} to a fixed power: the ratio of two "
            "float64 evaluations, each within a few units in the last place",
        )
    for name, step, coefficient in (
        ("urban_pct", 10.0, -0.016),
        ("forest_pct", 10.0, 0.004),
    ):
        moved = run(**{**base, name: base[name] + step}).real("time_to_peak_h")
        assert_within(
            moved / once,
            math.exp(coefficient * step),
            rel=1e-14,
            reason=f"{name} enters through exp(c {name}): adding 10 multiplies tp by "
            "exp(10 c), within a few units in the last place of the two evaluations",
        )


# --- the spec ------------------------------------------------------------------------

_LENGTH_REASON = (
    "1,000 km, about the length of the Vistula, the longest river of Poland: no main "
    "stream of a Polish watershed is longer"
)

LUTZ: Final = FormulaSpec(
    name="lutz",
    title="Nash's n and K of an ungauged watershed by Lutz's method (KZGW 2017)",
    function="hydrolog.runoff.nash_iuh.lutz_parameters",
    family="empirical",
    equation=(
        "tp = P1 * (L * Lc / Jg**1.5)**0.26 * exp(-0.016 * U) * exp(0.004 * W) [h], "
        "P1 = 3.989 * nM + 0.028; up = 0.66 / tp**1.04 [1/h] (dt -> 0); N solves "
        "(N - 1)**N * exp(-(N - 1)) / Gamma(N) = tp * up; K = tp / (N - 1)"
    ),
    latex=(
        r"t_p = P_1 \left(\frac{L\,L_c}{J_g^{1.5}}\right)^{0.26} e^{-0.016\,U}"
        r" e^{0.004\,W},\quad P_1 = 3.989\,n_M + 0.028,\quad"
        r" u_p = \frac{0.66}{t_p^{1.04}},\quad"
        r" \frac{(N-1)^N e^{-(N-1)}}{\Gamma(N)} = t_p\,u_p,\quad K = \frac{t_p}{N-1}"
    ),
    variables=(
        Variable(
            name="length_km",
            symbol="L",
            unit="km",
            description="Length along the main stream from the outlet to the divide: "
            "the longest flow path.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1000.0,
                test_reason=_LENGTH_REASON,
            ),
            applicability="unstated",
            typical=Range(
                low=0.05,
                high=30.0,
                source=_from_handoffs("flow paths of 0.0566 to 28.88 km"),
            ),
        ),
        Variable(
            name="centroid_length_km",
            symbol="Lc",
            unit="km",
            description="Length along the main stream from the outlet to its point "
            "nearest the watershed's centroid.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1000.0,
                test_reason=_LENGTH_REASON,
            ),
            applicability="unstated",
            typical=Range(
                low=0.004,
                high=15.0,
                source=_from_handoffs("Lc of 0.0042 to 14.49 km"),
            ),
        ),
        Variable(
            name="slope_m_per_m",
            symbol="Jg",
            unit="m/m",
            description="Equal-area slope of the main stream's longitudinal profile "
            "(spec equal_area_slope), not the slope between its ends.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1.0,
                test_reason="a mean slope of 1 m/m (45 degrees), steeper than any "
                "main stream on average",
            ),
            applicability="unstated",
            typical=Range(
                low=0.002,
                high=0.11,
                source=_from_handoffs(
                    "slopes between the ends of the flow paths, 0.00244 to 0.1055 "
                    "m/m, which bound their equal-area slopes on concave profiles "
                    "(Kamiennik: 0.00848 against 0.0114)"
                ),
            ),
        ),
        Variable(
            name="manning_n",
            symbol="nM",
            unit="s m^-1/3",
            description="Manning's roughness coefficient of the main channel.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=0.8,
                test_reason="0.80, the roughness of overland flow through woods with "
                "dense underbrush, rougher than any channel (USDA-NRCS 1986, TR-55, "
                "table 3-1)",
            ),
            applicability="unstated",
            typical=Range(
                low=0.025,
                high=0.035,
                source=Source(
                    citation=f"{_KZGW_CITATION}; and {_HANDOFFS}",
                    locator="KZGW Ex. 6.2, p. 99: n = 0.025 for the Niedźwiadka; "
                    "tests/fixtures/kamiennik.json: n = 0.035",
                    url=_KZGW_URL,
                ),
            ),
        ),
        Variable(
            name="urban_pct",
            symbol="U",
            unit="%",
            description="Share of urbanized land in the watershed's area.",
            physical=Range(low=0.0, high=100.0),
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=10.0,
                source=_from_handoffs("urbanized shares of 0 to 9 %"),
            ),
        ),
        Variable(
            name="forest_pct",
            symbol="W",
            unit="%",
            description="Share of forest in the watershed's area.",
            physical=Range(low=0.0, high=100.0),
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=100.0,
                source=_from_handoffs("forest shares of 0 to 100 %"),
            ),
        ),
    ),
    outputs=(
        Output(
            name="time_to_peak_h",
            unit="h",
            symbol="tp",
            description="Time to the peak of the instantaneous unit hydrograph.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="peak_ordinate_per_h",
            unit="1/h",
            symbol="up",
            description="Peak ordinate of the instantaneous unit hydrograph (dt -> 0).",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="n",
            unit="-",
            symbol="N",
            description="Number of reservoirs of Nash's cascade.",
            physical=Range(low=1.0, low_inclusive=False),
        ),
        Output(
            name="k_min",
            unit="min",
            symbol="K",
            description="Storage constant of each reservoir.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="p1",
            unit="h km^-0.52",
            symbol="P1",
            description="Lutz's roughness parameter of tp.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
    ),
    sources=(
        _kzgw(
            "annex 2, section 3.1.2, pp. 97-98: eqs. 6.17-6.21, Fig. 6.3 and the "
            "definitions of L, Lc, Jg, U and W; Ex. 6.2, pp. 99-100; Table C.2, "
            "pp. 132-133 (N against f(N))"
        ),
        _sikorska(
            "Table 1, p. 1226: Lutz's tp with the exponent 0.26 and up = P2 / tp**P3, "
            "P2 = 0.64 and P3 = 1.04, 'dependent on the interval of estimation'"
        ),
    ),
    constants=(
        Constant(
            name="p1_slope",
            value=3.989,
            unit="h km^-0.52 s^-1 m^1/3",
            symbol="3.989",
            source=_kzgw(
                "eq. 6.18, p. 97; Fig. 6.3, p. 98: P1 = 3.9886 n + 0.0284 (R2 = "
                "0.9974), after Lutz (1984)"
            ),
        ),
        Constant(
            name="p1_intercept",
            value=0.028,
            unit="h km^-0.52",
            symbol="0.028",
            source=_kzgw(
                "Fig. 6.3, p. 98 (+0.0284) and Ex. 6.2, p. 99 (P1 = 0.128 for n = "
                "0.025); eq. 6.18, p. 97, prints '- 0,028', a misprint"
            ),
        ),
        Constant(
            name="slope_exponent",
            value=1.5,
            unit="-",
            symbol="1.5",
            source=_kzgw("eq. 6.17, p. 97; the same in Sikorska et al. 2012, Table 1"),
        ),
        Constant(
            name="geometric_exponent",
            value=0.26,
            unit="-",
            symbol="0.26",
            source=_kzgw("eq. 6.17, p. 97; the same in Sikorska et al. 2012, Table 1"),
        ),
        Constant(
            name="urban_coefficient",
            value=-0.016,
            unit="1/%",
            symbol="-0.016",
            source=_kzgw("eq. 6.17, p. 97; the same in Sikorska et al. 2012, Table 1"),
        ),
        Constant(
            name="forest_coefficient",
            value=0.004,
            unit="1/%",
            symbol="0.004",
            source=_kzgw("eq. 6.17, p. 97; the same in Sikorska et al. 2012, Table 1"),
        ),
        Constant(
            name="peak_coefficient",
            value=0.66,
            unit="h^0.04",
            symbol="0.66",
            source=_kzgw(
                "eq. 6.19, p. 98, for dt -> 0; Sikorska et al. 2012, Table 1, give "
                "P2 = 0.64"
            ),
        ),
        Constant(
            name="peak_exponent",
            value=1.04,
            unit="-",
            symbol="1.04",
            source=_kzgw("eq. 6.19, p. 98; the same in Sikorska et al. 2012, Table 1"),
        ),
    ),
    constraints=(
        Constraint(
            name="centroid_within_length",
            cls="physical",
            check=lambda x: x.real("centroid_length_km") <= x.real("length_km"),
            text="Lc <= L: both run along the main stream from the outlet, Lc to its "
            "point nearest the centroid, L to the divide",
            source=_kzgw("p. 97, the definitions of L and Lc under eq. 6.17"),
            satisfied={"length_km": 4.3, "centroid_length_km": 2.7},
            boundary={"length_km": 4.3, "centroid_length_km": 4.3},
            violated={"length_km": 4.3, "centroid_length_km": 4.4},
        ),
        Constraint(
            name="shares_within_catchment",
            cls="physical",
            check=lambda x: x.real("urban_pct") + x.real("forest_pct") <= 100.0,
            text="U + W <= 100: the urbanized and the forest land are shares of the "
            "same watershed's area that do not overlap",
            source=_kzgw("p. 97, the definitions of U and W under eq. 6.17"),
            satisfied={"urban_pct": 5.0, "forest_pct": 57.4},
            boundary={"urban_pct": 40.0, "forest_pct": 60.0},
            violated={"urban_pct": 40.0, "forest_pct": 61.0},
        ),
        Constraint(
            name="root_in_bracket",
            cls="precondition",
            check=_root_in_bracket,
            text="f(1.1) <= tp up <= f(20), tp from about 3.4e-11 to 3.4e23 h: the "
            "root N of f(N) = tp up lies in the bracket searched, from the first "
            "row of Table C.2, and float64 holds every step",
            source=_kzgw("eq. 6.20, p. 98, and Table C.2, pp. 132-133, from N = 1.10"),
            satisfied={"length_km": 4.3, "centroid_length_km": 2.7},
            violated={"length_km": 1e-30, "centroid_length_km": 1e-30},
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={
            "length_km": 1,
            "centroid_length_km": 1,
            "slope_m_per_m": -1,
            "manning_n": 1,
            "urban_pct": -1,
            "forest_pct": 1,
        },
        limits=(
            Limit(
                name="decimal_steps",
                text="tp and up equal eqs. 6.17-6.19 evaluated in decimal arithmetic "
                "at 50 digits",
                check=_decimal_oracle,
            ),
            Limit(
                name="cascade_peak",
                text="the gamma density of shape N and scale K, Nash's IUH, peaks at "
                "(N - 1) K = tp with the ordinate up (scipy.stats.gamma)",
                check=_cascade_peak,
            ),
            Limit(
                name="power_law",
                text="doubling L or Lc multiplies tp by 2^0.26, doubling Jg by "
                "2^-0.39; adding 10 to U or W multiplies it by exp(-0.16) or "
                "exp(0.04)",
                check=_power_law,
            ),
        ),
    ),
    validation=(
        "Lutz (1984) fitted the relations to 75 watersheds of south-west Germany of up "
        "to 250 km2 (Sikorska et al. 2012, p. 1225); KZGW (2017, Fig. 6.3) gives R2 = "
        "0.9974 for P1 against Manning's n; no source open to Hydrolog reports the "
        "errors of tp, up or the peak flows against observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "up = 0.66 / tp**1.04 is Lutz's relation for dt -> 0 (KZGW 2017, eq. "
            "6.19, p. 98), the peak of the instantaneous unit hydrograph; the unit "
            "hydrograph of a step dt averages that IUH exactly over dt "
            "(NashIUH.to_unit_hydrograph). KZGW's Ex. 6.2 (p. 100) takes instead the "
            "relation of dt = 1 h, up = 0.464 / tp**0.824, and Sikorska et al. (2012, "
            "Table 1) state that P2 and P3 depend on the interval: that route gives "
            "N 2.55 and k 0.70 h where this one gives N 3.88 and K 0.377 h (case "
            "kzgw2017-ex6-2-n-k, a discrepancy)"
        ),
        (
            "P1 = 3.989 nM + 0.028: eq. 6.18 (KZGW 2017, p. 97) prints '- 0,028', a "
            "misprint, as Fig. 6.3 (P1 = 3.9886 n + 0.0284) and Ex. 6.2 (P1 = 0.128 "
            "for n = 0.025) show"
        ),
        (
            "0.66 of KZGW eq. 6.19, not the 0.64 of Sikorska et al. (2012, Table 1), "
            "who cite the same Lutz (1984)"
        ),
        (
            "L and Lc in km, Jg in m/m, the equal-area slope of the main stream's "
            "profile (KZGW 2017, p. 97; spec equal_area_slope), nM in s m^-1/3, U "
            "and W in percent of the watershed's area; tp in h, up in 1/h, K returned "
            "in min by the exact 60 min/h"
        ),
        (
            "N solves f(N) = tp up on [1.1, 20] by Brent's method "
            "(scipy.optimize.brentq, xtol 1e-6) where KZGW reads it from Table C.2 "
            "(pp. 132-133); f increases strictly there, from 0.0755 to 1.731, and "
            "matches the table's 13 rows from N = 1.10 to 7.99 within half its "
            "printed digit"
        ),
    ),
    assumptions=(
        (
            "watersheds of up to 236 km2 with development spread fairly evenly (KZGW "
            "2017, p. 97); NashIUH.from_lutz warns of a larger area; Lutz's data were "
            "75 watersheds of up to 250 km2 (Sikorska et al. 2012, p. 1225)"
        ),
        (
            "a near-natural watershed: KZGW (2017, p. 96) uses Nash's model with "
            "Lutz's parameters for imperviousness below 5 %"
        ),
    ),
    traps={
        "singular_at_bound": "range cases slope_m_per_m-physical_low_*: tp grows "
        "without bound as Jg tends to 0 (Jg^-0.39), and as tp tends to 0 the target "
        "tp up = 0.66 tp^-0.04 grows; beyond the bracket of N the precondition "
        "root_in_bracket refuses, as for the smallest positive Jg, whose Jg^1.5 "
        "underflows",
        "exp_overflow": "range cases urban_pct-physical_high and "
        "forest_pct-physical_high: exp(-0.016 U) and exp(0.004 W) at 100 % are "
        "0.2019 and 1.4918",
    },
    reference_cases=("tests/fixtures/formulas/lutz-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="tp and up of eqs. 6.17-6.19 with the decimal constants, "
            "evaluated with the decimal module at 50 digits",
            test="tests/unit/test_formulas_lutz.py (limit decimal_steps)",
        ),
        Oracle(
            kind="established",
            description="scipy.stats.gamma (SciPy 1.18.1): the density of shape N "
            "and scale K, Nash's IUH, at its mode (N - 1) K",
            test="tests/unit/test_formulas_lutz.py (limit cascade_peak)",
            conventions=(
                "scale K in h, the density in 1/h; its mode (N - 1) K is tp and its "
                "value there up, by eqs. 6.14 and 6.16 of KZGW (2017, p. 96)",
            ),
        ),
    ),
    base={"urban_pct": 0.0, "forest_pct": 0.0},
)

# --- the urban regression of Rao, Delleur and Sarma: the spec nash_urban_regression ---

_URBAN_POINTS: Final[tuple[dict[str, float], ...]] = (
    # the catalog's example of uh nash (urban regression)
    {
        "area_km2": 1.3,
        "effective_precip_mm": 1.305,
        "duration_h": 0.167,
        "urban_fraction": 0.05,
    },
    # the Służew Creek of Sikorska et al. (2012, p. 1227): 26.9 km2, 32 % impervious
    {
        "area_km2": 26.9,
        "effective_precip_mm": 10.0,
        "duration_h": 1.0,
        "urban_fraction": 0.32,
    },
    # KZGW's largest urbanized watershed, a long and heavy storm
    {
        "area_km2": 52.0,
        "effective_precip_mm": 80.0,
        "duration_h": 6.0,
        "urban_fraction": 0.6,
    },
)
"""Inputs of the decimal oracle, inside the typical ranges or at their ends."""


def _urban(x: Values) -> dict[str, object]:
    area, depth = x.real("area_km2"), x.real("effective_precip_mm")
    duration, urban = x.real("duration_h"), 1.0 + x.real("urban_fraction")

    def power_law(prefix: str) -> float:
        return float(
            URBAN.constant(f"{prefix}_coefficient")
            * area ** URBAN.constant(f"{prefix}_area_exponent")
            * urban ** URBAN.constant(f"{prefix}_urban_exponent")
            * depth ** URBAN.constant(f"{prefix}_depth_exponent")
            * duration ** URBAN.constant(f"{prefix}_duration_exponent")
        )

    lag_h, k_h = power_law("lag"), power_law("k")
    return {"lag_time_h": lag_h, "n": lag_h / k_h, "k_min": convert(k_h, "h", "min")}


def _urban_decimal(point: dict[str, float]) -> tuple[Decimal, Decimal]:
    """LAG and k of eqs. 6.26-6.27 at 50 digits, from the exact inputs [h]."""
    with localcontext(prec=_DIGITS):
        area, depth, duration = (
            Decimal(point[name])
            for name in ("area_km2", "effective_precip_mm", "duration_h")
        )
        urban = 1 + Decimal(point["urban_fraction"])
        lag = (
            Decimal("1.28")
            * area ** Decimal("0.46")
            * urban ** Decimal("-1.66")
            * depth ** Decimal("-0.27")
            * duration ** Decimal("0.37")
        )
        k = (
            Decimal("0.56")
            * area ** Decimal("0.39")
            * urban ** Decimal("-0.62")
            * depth ** Decimal("-0.11")
            * duration ** Decimal("0.22")
        )
        return lag, k


def _urban_oracle(run: Callable[..., Values]) -> None:
    for point in _URBAN_POINTS:
        result = run(**point)
        lag, k = _urban_decimal(point)
        assert_within(
            result.real("lag_time_h"),
            float(lag),
            rel=1e-13,
            reason="float64 powers and products against eq. 6.26 in decimal arithmetic "
            "at 50 digits: a few units in the last place of each factor, the "
            "constants one rounding from their decimal values",
        )
        assert_within(
            result.real("k_min"),
            float(k * 60),
            rel=1e-13,
            reason="eq. 6.27 likewise, and the exact 60 min/h",
        )
        assert_within(
            result.real("n"),
            float(lag / k),
            rel=1e-13,
            reason="eq. 6.28, the quotient of the two above",
        )


def _urban_source(locator: str) -> Source:
    return _kzgw(f"eqs. 6.26-6.28, p. 107{locator}; the same in Sikorska et al. 2012")


def _urban_constant(name: str, value: float, unit: str) -> Constant:
    return Constant(
        name=name,
        value=value,
        unit=unit,
        symbol=f"{value:g}",
        source=_urban_source("; Sikorska et al. (2012), Table 1, p. 1226"),
    )


URBAN: Final = FormulaSpec(
    name="nash_urban_regression",
    title="Nash's n and K of an urbanized watershed by the regression of Rao, Delleur "
    "and Sarma (1972)",
    function="hydrolog.runoff.nash_iuh.urban_regression_parameters",
    family="empirical",
    equation=(
        "LAG = 1.28 * A**0.46 * (1 + U)**-1.66 * H**-0.27 * D**0.37 [h]; k = 0.56 * "
        "A**0.39 * (1 + U)**-0.62 * H**-0.11 * D**0.22 [h]; N = LAG / k"
    ),
    latex=(
        r"LAG = 1.28\,A^{0.46}(1+U)^{-1.66}H^{-0.27}D^{0.37},\quad k = 0.56\,A^{0.39}"
        r"(1+U)^{-0.62}H^{-0.11}D^{0.22},\quad N = \frac{LAG}{k}"
    ),
    variables=(
        Variable(
            name="area_km2",
            symbol="A",
            unit="km2",
            description="Area of the watershed.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1.49e8,
                test_reason="the land area of the Earth, about 149 million km2",
            ),
            applicability=Range(
                low=0.0,
                high=52.0,
                source=_kzgw(
                    "p. 107: the relations for urbanized watersheds of up to 52 km2"
                ),
            ),
            typical=Range(
                low=1.3,
                high=52.0,
                source=Source(
                    citation=f"{_KZGW_CITATION}; {_SIKORSKA_CITATION}; Hydrolog's "
                    "catalog example of uh nash (urban regression)",
                    locator="KZGW p. 107 (up to 52 km2); Sikorska et al. p. 1227 (the "
                    "Służew Creek, 26.9 km2); src/hydrolog/catalog/groups/uh.py "
                    "(1.3 km2)",
                    url=_KZGW_URL,
                ),
            ),
        ),
        Variable(
            name="effective_precip_mm",
            symbol="H",
            unit="mm",
            description="Depth of the effective (excess) rainfall of the storm.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1825.0,
                test_reason="the world's largest daily rainfall, 1,825 mm at Foc-Foc, "
                "La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate "
                "Extremes)",
            ),
            applicability="unstated",
            typical=Range(
                low=1.0,
                high=100.0,
                source=Source(
                    citation=f"{_KZGW_CITATION}; Hydrolog's catalog example of uh nash",
                    locator="KZGW Ex. 6.4, p. 109: effective depths of steps of 1.4 to "
                    "2.1 mm; Ex. 6.1, p. 93: 15.3 mm in an hour; "
                    "the catalog's 1.305 mm",
                    url=_KZGW_URL,
                ),
            ),
        ),
        Variable(
            name="duration_h",
            symbol="D",
            unit="h",
            description="Duration of the effective rainfall.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=72.0,
                test_reason="72 h, the longest duration of the PMAXTP tables",
            ),
            applicability="unstated",
            typical=Range(
                low=0.167,
                high=24.0,
                source=Source(
                    citation=f"{_KZGW_CITATION}; Hydrolog's catalog example of uh nash",
                    locator="KZGW ch. II.3, p. 25: a daily design storm split into "
                    "hours; the catalog's 10 min (0.167 h)",
                    url=_KZGW_URL,
                ),
            ),
        ),
        Variable(
            name="urban_fraction",
            symbol="U",
            unit="-",
            description="Fraction of impervious area of the watershed.",
            physical=Range(low=0.0, high=1.0, high_inclusive=False),
            applicability=Range(
                low=0.05,
                high=1.0,
                source=_kzgw(
                    "p. 102 (zlewnia zurbanizowana: more than 5 % impervious) and p. "
                    "107 (the relations for urbanized watersheds)"
                ),
            ),
            typical=Range(
                low=0.05,
                high=0.32,
                source=Source(
                    citation=f"{_SIKORSKA_CITATION}; Hydrolog's catalog example",
                    locator="p. 1227: 32 % impervious in the Służew Creek; the "
                    "catalog's 0.05",
                    url=_SIKORSKA_URL,
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="lag_time_h",
            unit="h",
            symbol="LAG",
            description="Lag time of the instantaneous unit hydrograph, N K.",
            physical=Range(low=0.0),
        ),
        Output(
            name="n",
            unit="-",
            symbol="N",
            description="Number of reservoirs of Nash's cascade.",
            physical=Range(low=0.0),
        ),
        Output(
            name="k_min",
            unit="min",
            symbol="k",
            description="Storage constant of each reservoir.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        _urban_source(" (U the fraction of impervious area, dimensionless)"),
        _sikorska(
            "Table 1, p. 1226: the same equations, U the fraction of the impervious "
            "area, Lag and k in h"
        ),
        Source(
            citation="Rao, A.R., Delleur, J.W. and Sarma, B.S.P. (1972). Conceptual "
            "hydrologic models for urbanizing basins. Journal of the Hydraulics "
            "Division, ASCE 98(HY7), 1205-1220",
            access="author-provided",
        ),
    ),
    constants=(
        _urban_constant("lag_coefficient", 1.28, "h km^-0.92 mm^0.27 h^-0.37"),
        _urban_constant("lag_area_exponent", 0.46, "-"),
        _urban_constant("lag_urban_exponent", -1.66, "-"),
        _urban_constant("lag_depth_exponent", -0.27, "-"),
        _urban_constant("lag_duration_exponent", 0.37, "-"),
        _urban_constant("k_coefficient", 0.56, "h km^-0.78 mm^0.11 h^-0.22"),
        _urban_constant("k_area_exponent", 0.39, "-"),
        _urban_constant("k_urban_exponent", -0.62, "-"),
        _urban_constant("k_depth_exponent", -0.11, "-"),
        _urban_constant("k_duration_exponent", 0.22, "-"),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={
            "area_km2": 1,
            "effective_precip_mm": -1,
            "duration_h": 1,
            "urban_fraction": -1,
        },
        scalings=(
            Scaling(
                name="area",
                inputs={"area_km2": 1},
                outputs={"lag_time_h": 0.46, "k_min": 0.39, "n": 0.07},
                tolerance=Tolerance(
                    rel=1e-14,
                    reason="a product of powers: doubling A multiplies LAG by 2^0.46 "
                    "and k by 2^0.39 but for a few units in the last place of the "
                    "powers",
                ),
            ),
            Scaling(
                name="rainfall",
                inputs={"effective_precip_mm": 1, "duration_h": 1},
                outputs={"lag_time_h": 0.1, "k_min": 0.11, "n": -0.01},
                tolerance=Tolerance(
                    rel=1e-14,
                    reason="doubling H and D multiplies LAG by 2^(0.37 - 0.27) and k "
                    "by 2^(0.22 - 0.11) but for a few units in the last place",
                ),
            ),
        ),
        limits=(
            Limit(
                name="decimal_equations",
                text="LAG, k and N equal eqs. 6.26-6.28 evaluated in decimal "
                "arithmetic at 50 digits",
                check=_urban_oracle,
            ),
        ),
    ),
    validation=(
        "Rao et al. (1972) fitted the relations to storms on urbanizing watersheds "
        "near "
        "Indianapolis (as KZGW and Sikorska et al. 2012 report them, without error "
        "statistics); KZGW (2017, p. 107) recommends them only where the parameters "
        "cannot be fitted to measured rainfall and runoff"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        (
            "A in km2, H in mm, D in h, U dimensionless; LAG and k in h, K returned in "
            "min by the exact 60 min/h: the constants 1.28 and 0.56 hold for these "
            "units only (KZGW 2017, p. 107)"
        ),
        (
            "U is the fraction of impervious area (KZGW 2017, p. 107; Sikorska et al. "
            "2012, Table 1), not the share of built-up land"
        ),
        (
            "a product of powers of A, H and D: the scalings state it, and the "
            "constants carry the units (the property is not dimensional homogeneity)"
        ),
        "H and D are those of the storm: the parameters change with every storm",
    ),
    assumptions=(
        (
            "urbanized watersheds of up to 52 km2 whose parameters cannot be fitted to "
            "measured rainfall and runoff (KZGW 2017, p. 107)"
        ),
    ),
    traps={
        "singular_at_bound": "range cases effective_precip_mm-physical_low_* and "
        "duration_h-physical_low_*: H^-0.27 grows without bound as H tends to 0 and "
        "stays finite at the smallest positive float",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="LAG, k and N of eqs. 6.26-6.28 with the decimal constants, "
            "evaluated with the decimal module at 50 digits",
            test="tests/unit/test_formulas_lutz.py (limit decimal_equations of "
            "test_urban_limits_and_oracles)",
        ),
    ),
    base={"urban_fraction": 0.2},
)


@dataclass(frozen=True)
class UrbanEstimate(JsonResultMixin):
    """Nash's n and K of an urbanized watershed, spec nash_urban_regression.

    Attributes
    ----------
    lag_time_h : float
        Lag time of the instantaneous unit hydrograph, LAG [h].
    n : float
        Number of reservoirs, N [-].
    k_min : float
        Storage constant of each reservoir, K [min].
    """

    lag_time_h: float
    n: float
    k_min: float


def urban_regression_parameters(
    area_km2: float,
    effective_precip_mm: float,
    duration_h: float,
    urban_fraction: float,
) -> UrbanEstimate:
    """Return Nash's n and K of an urbanized watershed, spec nash_urban_regression.

    The first input is the area of the watershed in square kilometres (its name
    carries the unit, so the standard's check of this docstring, which allows no
    digit, keeps it out of the list below).

    Parameters
    ----------
    effective_precip_mm : float
        Depth of the effective rainfall of the storm [mm].
    duration_h : float
        Duration of the effective rainfall [h].
    urban_fraction : float
        Fraction of impervious area of the watershed.

    Returns
    -------
    UrbanEstimate
        LAG, N and K.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.

    Warns
    -----
    OutsideTypicalRange
        If the area or the impervious fraction is outside the watersheds the
        relations are for.
    """
    x = checked_inputs(
        URBAN,
        area_km2=area_km2,
        effective_precip_mm=effective_precip_mm,
        duration_h=duration_h,
        urban_fraction=urban_fraction,
    )
    out = checked_outputs(URBAN, _urban(x))
    return UrbanEstimate(
        lag_time_h=out.real("lag_time_h"), n=out.real("n"), k_min=out.real("k_min")
    )


SPECS: Final[tuple[FormulaSpec, ...]] = (LUTZ, URBAN)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""


@dataclass(frozen=True)
class LutzEstimate(JsonResultMixin):
    """Nash's n and K estimated by Lutz's method, spec lutz, with its steps.

    Attributes
    ----------
    time_to_peak_h : float
        Time to the peak of the instantaneous unit hydrograph, tp [h].
    peak_ordinate_per_h : float
        Its peak ordinate, up [1/h].
    n : float
        Number of reservoirs, N [-].
    k_min : float
        Storage constant of each reservoir, K [min].
    p1 : float
        Lutz's roughness parameter of tp.
    geometric_factor, urban_factor, forest_factor : float
        The factors of tp after P1: of the lengths and the slope, of U and of W.
    peak_product : float
        tp up, the value of f(N) the root solves.
    k_h : float
        K [h].
    """

    time_to_peak_h: float
    peak_ordinate_per_h: float
    n: float
    k_min: float
    p1: float
    geometric_factor: float
    urban_factor: float
    forest_factor: float
    peak_product: float
    k_h: float


def lutz_parameters(
    length_km: float,
    centroid_length_km: float,
    slope_m_per_m: float,
    manning_n: float,
    urban_pct: float,
    forest_pct: float,
) -> LutzEstimate:
    """Return Nash's n and K of an ungauged watershed by Lutz's method, spec lutz.

    Parameters
    ----------
    length_km : float
        Length along the main stream from the outlet to the divide [km].
    centroid_length_km : float
        Length along the main stream from the outlet to its point nearest the
        watershed's centroid [km].
    slope_m_per_m : float
        Equal-area slope of the main stream's longitudinal profile [m/m]
        (:func:`hydrolog.morphometry.equal_area_slope`).
    manning_n : float
        Manning's roughness coefficient of the main channel.
    urban_pct : float
        Share of urbanized land in the watershed [%].
    forest_pct : float
        Share of forest in the watershed [%].

    Returns
    -------
    LutzEstimate
        tp, up, N, K and Lutz's roughness parameter, with the steps between them.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs (``details.reason``, ``details.option`` or
        ``details.constraint``): a value outside its physical range, Lc longer than
        L, shares of urbanized and forest land above the whole area, or a tp whose
        N lies outside the bracket the root is searched in.
    """
    x = checked_inputs(
        LUTZ,
        length_km=length_km,
        centroid_length_km=centroid_length_km,
        slope_m_per_m=slope_m_per_m,
        manning_n=manning_n,
        urban_pct=urban_pct,
        forest_pct=forest_pct,
    )
    steps = _steps(x)
    target = steps.peak_product
    n = brentq(
        lambda value: float(_peak_product(value) - target),
        _N_LOW,
        _N_HIGH,
        xtol=_N_XTOL,
    )
    k_h = steps.time_to_peak_h / (n - 1)
    outputs = checked_outputs(
        LUTZ,
        {
            "time_to_peak_h": float(steps.time_to_peak_h),
            "peak_ordinate_per_h": float(steps.peak_ordinate_per_h),
            "n": float(n),
            "k_min": convert(float(k_h), "h", "min"),
            "p1": float(steps.p1),
        },
    )
    return LutzEstimate(
        time_to_peak_h=outputs.real("time_to_peak_h"),
        peak_ordinate_per_h=outputs.real("peak_ordinate_per_h"),
        n=outputs.real("n"),
        k_min=outputs.real("k_min"),
        p1=outputs.real("p1"),
        geometric_factor=float(steps.geometric_factor),
        urban_factor=float(steps.urban_factor),
        forest_factor=float(steps.forest_factor),
        peak_product=float(target),
        k_h=float(k_h),
    )


_FROM_LUTZ_ARGUMENTS: Final = {
    "length_km": "L_km",
    "centroid_length_km": "Lc_km",
    "slope_m_per_m": "slope",
    "manning_n": "manning_n",
    "urban_pct": "urban_pct",
    "forest_pct": "forest_pct",
    "centroid_within_length": "Lc_km",
    "shares_within_catchment": "forest_pct",
}
"""The argument of ``NashIUH.from_lutz`` a refusal of the spec lutz names: that of the
input, or of a constraint the input that breaks it (the precondition names none)."""


def _from_lutz_error(exc: InvalidParameterError) -> InvalidParameterError:
    """Return a refusal of ``lutz_parameters`` with the argument of ``from_lutz``."""
    subject = exc.details.get("variable") or exc.details.get("constraint")
    argument = _FROM_LUTZ_ARGUMENTS.get(subject) if isinstance(subject, str) else None
    if argument is None:
        return InvalidParameterError(str(exc), details=exc.details, hint=exc.hint)
    return InvalidParameterError(
        f"{exc} (argument {argument} of NashIUH.from_lutz)",
        details={**exc.details, "option": argument},
        hint=exc.hint,
    )
