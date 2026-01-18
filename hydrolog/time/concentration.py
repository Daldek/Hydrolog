"""Time of concentration calculation methods."""

import warnings

from hydrolog.exceptions import InvalidParameterError

# Typical parameter ranges for validation warnings
_KIRPICH_LENGTH_RANGE = (0.001, 80.0)  # km
_KIRPICH_SLOPE_RANGE = (0.002, 0.15)  # m/m

_SCS_LAG_LENGTH_RANGE = (0.03, 30.0)  # km
_SCS_LAG_SLOPE_RANGE = (0.001, 0.15)  # m/m
_SCS_LAG_CN_RANGE = (50, 95)  # dimensionless

_GIANDOTTI_AREA_RANGE = (100.0, 10000.0)  # km2
_GIANDOTTI_LENGTH_RANGE = (1.0, 300.0)  # km
_GIANDOTTI_ELEVATION_RANGE = (20.0, 3000.0)  # m


def _warn_if_out_of_range(
    value: float,
    param_name: str,
    min_val: float,
    max_val: float,
    method_name: str,
) -> None:
    """Issue warning if parameter is outside typical range.

    Parameters
    ----------
    value : float
        The parameter value to check.
    param_name : str
        Name of the parameter for the warning message.
    min_val : float
        Minimum typical value.
    max_val : float
        Maximum typical value.
    method_name : str
        Name of the method for the warning message.
    """
    if value < min_val or value > max_val:
        warnings.warn(
            f"{method_name}: {param_name}={value} is outside typical range "
            f"[{min_val}, {max_val}]. Results may be unreliable.",
            UserWarning,
            stacklevel=3,
        )


class ConcentrationTime:
    """
    Calculate time of concentration using various empirical methods.

    Time of concentration (tc) is the time required for runoff to travel
    from the hydraulically most distant point in the watershed to the outlet.

    All methods use standardized units:
    - Length: km (kilometers)
    - Slope: m/m (dimensionless)
    - Output: min (minutes)

    Examples
    --------
    >>> tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
    >>> print(f"{tc:.1f} min")
    52.3 min

    >>> tc = ConcentrationTime.scs_lag(length_km=8.2, slope_m_per_m=0.023, cn=72)
    >>> print(f"{tc:.1f} min")
    97.5 min
    """

    @staticmethod
    def kirpich(
        length_km: float,
        slope_m_per_m: float,
    ) -> float:
        """
        Calculate time of concentration using Kirpich formula.

        The Kirpich formula (1940) was developed for small agricultural
        watersheds in Tennessee, USA. It is one of the most widely used
        empirical equations for tc estimation.

        Parameters
        ----------
        length_km : float
            Length of the main channel from the watershed divide
            to the outlet [km]. Must be positive.
        slope_m_per_m : float
            Average slope of the main channel [m/m]. Must be positive.

        Returns
        -------
        float
            Time of concentration [min].

        Raises
        ------
        InvalidParameterError
            If length_km <= 0 or slope_m_per_m <= 0.

        Warns
        -----
        UserWarning
            If length_km > 80 km or slope_m_per_m outside 0.002-0.15.
            The Kirpich formula was developed for small agricultural
            watersheds (0.004-0.45 km2) with slopes 3-10%.

        Notes
        -----
        Formula: tc [h] = 0.0663 * L^0.77 * S^(-0.385)

        Where:
        - tc: time of concentration [h] (converted to min)
        - L: channel length [km]
        - S: channel slope [m/m]

        References
        ----------
        Kirpich, Z.P. (1940). Time of concentration of small agricultural
        watersheds. Civil Engineering, 10(6), 362.

        Examples
        --------
        >>> ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
        52.3...
        """
        if length_km <= 0:
            raise InvalidParameterError(f"length_km must be positive, got {length_km}")
        if slope_m_per_m <= 0:
            raise InvalidParameterError(
                f"slope_m_per_m must be positive, got {slope_m_per_m}"
            )

        # Warn if parameters are outside typical range
        _warn_if_out_of_range(
            length_km, "length_km", *_KIRPICH_LENGTH_RANGE, "kirpich"
        )
        _warn_if_out_of_range(
            slope_m_per_m, "slope_m_per_m", *_KIRPICH_SLOPE_RANGE, "kirpich"
        )

        # Kirpich formula: tc [hours]
        tc_hours: float = 0.0663 * (length_km**0.77) * (slope_m_per_m ** (-0.385))

        # Convert to minutes
        tc_min: float = tc_hours * 60.0
        return tc_min

    @staticmethod
    def scs_lag(
        length_km: float,
        slope_m_per_m: float,
        cn: int,
    ) -> float:
        """
        Calculate time of concentration using SCS Lag equation (metric).

        The SCS Lag equation estimates watershed lag time, which is then
        converted to time of concentration using the relationship tc = Lag / 0.6.

        Parameters
        ----------
        length_km : float
            Hydraulic length of the watershed (longest flow path) [km].
            Must be positive. Typical range: 0.03-30 km.
        slope_m_per_m : float
            Average watershed slope [m/m]. Must be positive.
            Typical range: 0.001-0.15.
        cn : int
            SCS Curve Number (1-100). CN=100 means no retention.
            Recommended range for this method: 50-95.

        Returns
        -------
        float
            Time of concentration [min].

        Raises
        ------
        InvalidParameterError
            If length_km <= 0, slope_m_per_m <= 0, or cn not in range 1-100.

        Warns
        -----
        UserWarning
            If parameters are outside typical application range.

        Notes
        -----
        Formula (metric units):
        Lag [h] = (L^0.8 * (S + 25.4)^0.7) / (7182 * Y^0.5)
        tc = Lag / 0.6

        Where:
        - L: hydraulic length [m] (converted internally from km)
        - S: maximum retention = (25400/CN) - 254 [mm]
        - Y: average watershed slope [%] (converted internally from m/m)

        The constant 7182 is derived from the original imperial formula
        (with constant 1900) by converting feet to meters and inches to mm.

        References
        ----------
        USDA-NRCS (1986). Urban Hydrology for Small Watersheds.
        Technical Release 55 (TR-55).

        Examples
        --------
        >>> ConcentrationTime.scs_lag(length_km=8.2, slope_m_per_m=0.023, cn=72)
        97.5...
        """
        if length_km <= 0:
            raise InvalidParameterError(
                f"length_km must be positive, got {length_km}"
            )
        if slope_m_per_m <= 0:
            raise InvalidParameterError(
                f"slope_m_per_m must be positive, got {slope_m_per_m}"
            )
        if not 1 <= cn <= 100:
            raise InvalidParameterError(f"cn must be in range 1-100, got {cn}")

        # Warn if parameters are outside typical range
        _warn_if_out_of_range(
            length_km, "length_km", *_SCS_LAG_LENGTH_RANGE, "scs_lag"
        )
        _warn_if_out_of_range(
            slope_m_per_m, "slope_m_per_m", *_SCS_LAG_SLOPE_RANGE, "scs_lag"
        )
        _warn_if_out_of_range(cn, "cn", *_SCS_LAG_CN_RANGE, "scs_lag")

        # Convert input units to formula units
        length_m = length_km * 1000.0  # km -> m
        slope_percent = slope_m_per_m * 100.0  # m/m -> %

        # Calculate maximum retention S [mm]
        # S = (25400/CN) - 254 (metric version of (1000/CN) - 10 in inches)
        if cn == 100:
            retention_mm = 0.0
        else:
            retention_mm = (25400.0 / cn) - 254.0

        # SCS Lag equation (metric): Lag [hours]
        # Lag = (L^0.8 * (S + 25.4)^0.7) / (7182 * Y^0.5)
        # Constant 7182 = 1900 * 25.4^0.7 / 3.28084^0.8
        lag_hours = ((length_m**0.8) * ((retention_mm + 25.4) ** 0.7)) / (
            7182.0 * (slope_percent**0.5)
        )

        # Convert lag to tc: tc = Lag / 0.6
        tc_hours = lag_hours / 0.6

        # Convert to minutes
        tc_min: float = tc_hours * 60.0

        return tc_min

    @staticmethod
    def giandotti(
        area_km2: float,
        length_km: float,
        elevation_diff_m: float,
    ) -> float:
        """
        Calculate time of concentration using Giandotti formula.

        The Giandotti formula (1934) was developed for Italian watersheds
        and is suitable for larger catchments (> 170 km2).

        Parameters
        ----------
        area_km2 : float
            Watershed area [km2]. Must be positive.
        length_km : float
            Length of the main channel [km]. Must be positive.
        elevation_diff_m : float
            Elevation difference between mean watershed elevation
            and outlet [m]. Must be positive.

        Returns
        -------
        float
            Time of concentration [min].

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.

        Warns
        -----
        UserWarning
            If area_km2 < 100 km2. The Giandotti formula was developed
            for larger Italian mountain watersheds (> 170 km2).

        Notes
        -----
        Formula: tc = (4 * sqrt(A) + 1.5 * L) / (0.8 * sqrt(H))

        Where:
        - tc: time of concentration [hours]
        - A: watershed area [km2]
        - L: main channel length [km]
        - H: elevation difference [m]

        References
        ----------
        Giandotti, M. (1934). Previsione delle piene e delle magre dei
        corsi d'acqua. Ministero LL.PP., Servizio Idrografico Italiano.

        Examples
        --------
        >>> ConcentrationTime.giandotti(area_km2=45.0, length_km=12.0, elevation_diff_m=350.0)
        94.8...
        """
        if area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")
        if length_km <= 0:
            raise InvalidParameterError(f"length_km must be positive, got {length_km}")
        if elevation_diff_m <= 0:
            raise InvalidParameterError(
                f"elevation_diff_m must be positive, got {elevation_diff_m}"
            )

        # Warn if parameters are outside typical range
        _warn_if_out_of_range(
            area_km2, "area_km2", *_GIANDOTTI_AREA_RANGE, "giandotti"
        )
        _warn_if_out_of_range(
            length_km, "length_km", *_GIANDOTTI_LENGTH_RANGE, "giandotti"
        )
        _warn_if_out_of_range(
            elevation_diff_m, "elevation_diff_m", *_GIANDOTTI_ELEVATION_RANGE, "giandotti"
        )

        # Giandotti formula: tc [hours]
        tc_hours = (4.0 * (area_km2**0.5) + 1.5 * length_km) / (
            0.8 * (elevation_diff_m**0.5)
        )

        # Convert to minutes
        tc_min: float = tc_hours * 60.0

        return tc_min
