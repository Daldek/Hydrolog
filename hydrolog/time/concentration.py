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
    86.0 min

    >>> tc = ConcentrationTime.nrcs(length_km=8.2, slope_m_per_m=0.023, cn=72)
    >>> print(f"{tc:.1f} min")
    369.0 min
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
            watersheds (0.004-0.45 km2) with slopes 3-10% (0.03-0.10 m/m).

        Notes
        -----
        Original formula (US units):
            tc[min] = 0.0078 * L[ft]^0.77 * S^(-0.385)
        Metric conversion (this implementation):
            tc[min] = 0.0195 * L[m]^0.77 * S^(-0.385)
        or
            tc[min] = 3.981 * L[km]^0.77 * S^(-0.385)
        or
            tc[h] = 0.0663 * L[km]^0.77 * S^(-0.385)

        The original formula outputs time in **minutes**. Slope is dimensionless
        (m/m or ft/ft), not in percent. The constant 0.0663 is derived from
        the original 0.0078 by converting feet to kilometers and minutes to hours:
            tc = 0.0078 * L[ft]^0.77 * S^(-0.385)
            L[ft] = L[m] * 3.281
            tc = 0.0078 * (3.281 * L[m])^0.77 * S^(-0.385)
            tc = 0.0078 * 3.281^0.77 *L[m]^0.77 * S^(-0.385)
            0.0078 * 3.281^0.77 ≈ 0.0195
            tc = 0.0195 * L[m]^0.77 * S^(-0.385)
            
        Converting to kilometers:
            L[m] = L[km] * 1000
            tc = 0.0195 * (1000 * L[km])^0.77 * S^(-0.385)
            tc = 0.0195 * 1000^0.77 * L[km]^0.77 * S^(-0.385)
            0.0195 * 1000^0.77 ≈ 3.981
            tc[min] = 3.981 * L[km]^0.77 * S^(-0.385)
            
        Converting minutes to hours:
            tc[h] = (3.981 / 60) * L[km]^0.77 * S^(-0.385)
            3.981 / 60 ≈ 0.0663
            tc[h] = 0.0663 * L[km]^0.77 * S^(-0.385)

        Original calibration data: 7 small agricultural watersheds in Tennessee,
        areas 0.004-0.45 km² (1.25-112 acres), slopes 3-10%.

        References
        ----------
        Kirpich, Z.P. (1940). Time of concentration of small agricultural
        watersheds. Civil Engineering, 10(6), 362.

        Ponce, V.M. (2014). Engineering Hydrology: Principles and Practices.
        Online: https://ponce.sdsu.edu/kirpich.php

        CivilWeb (2023). Kirpich Formula - Time of Concentration.
        https://civilweb-spreadsheets.com/drainage-design-spreadsheets/

        Examples
        --------
        >>> ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
        85.9...
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

        # Kirpich formula: tc [minutes]
        tc_min: float = 3.981 * (length_km**0.77) * (slope_m_per_m ** (-0.385))

        return tc_min

    @staticmethod
    def nrcs(
        length_km: float,
        slope_m_per_m: float,
        cn: int,
    ) -> float:
        """
        Calculate time of concentration (tc) using NRCS equation (metric).

        The NRCS method equation estimates watershed lag time, which is then
        converted to concentration time using the relationship tc = tlag / 0.6.

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
        Original formula (US units):
            tlag[h] = (L[ft]^0.8 * ((1000/CN) - 9)^0.7) / (1900 * Y[%]^0.5)
        where CN is the Curve Number and S[in] = (1000/CN) - 10 [inches]
        thus
            tlag[h] = (L[ft]^0.8 * (S[in] + 1)^0.7) / (1900 * Y[%]^0.5)
        or
            tlag[h] = 0.000526 * (S[in] + 1)^0.7 * L[ft]^0.8 * Y[%]^(-0.5)
        
        Metric conversion (this implementation):
            L[ft] = 3.28 * L[m]
            
            S[mm] = 25.4 * ((1000/CN) - 10) [mm]
            thus
            (S[in] + 1) = (S[mm] + 25.4) / 25.4
            
            tlag[h] = (3.28^0.8 * L[m]^0.8 * (S[mm] + 25.4)^0.7) / (1900 * 25.4^0.7 * Y[%]^0.5)
            
            3.28^0.8 / (1900 * 25.4^0.7) ≈ 0.000141
            
            tlag[h] = 0.000141 * L[m]^0.8 * (S[mm] + 25.4)^0.7 * Y[%]^(-0.5)
            
            tc[h] = tlag / 0.6
            tc[h] = 0.000236 * L[m]^0.8 * (S[mm] + 25.4)^0.7 * Y[%]^(-0.5)
            
            tc[min] = 0.000236 * 60 * L[m]^0.8 * (S[mm] + 25.4)^0.7 * Y[%]^(-0.5)
            tc[min] = 0.01416 * L[m]^0.8 * (S[mm] + 25.4)^0.7 * Y[%]^(-0.5)

        Where:
        - L: hydraulic length [m] (converted internally from km)
        - S: maximum retention = (25400/CN) - 254 [mm]
        - Y: average watershed slope [%] (converted internally from m/m)

        **Important distinction:**
        - tc (time of concentration) = time for runoff to travel from the
          most distant point to the outlet
        - tlag = 0.6 * tc = time from centroid of rainfall to peak flow

        This method calculates tc, not tp. For unit hydrograph calculations,
        use tp = D/2 + 0.6*tc.

        References
        ----------
        USDA-NRCS (1986). Urban Hydrology for Small Watersheds.
        Technical Release 55 (TR-55). Chapter 3.
        https://www.hydrocad.net/pdf/TR-55%20Manual.pdf

        USACE HEC-HMS (2024). Technical Reference Manual - SCS Unit Hydrograph.
        https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/

        Examples
        --------
        >>> ConcentrationTime.nrcs(length_km=8.2, slope_m_per_m=0.023, cn=72)
        369.0...
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
            length_km, "length_km", *_SCS_LAG_LENGTH_RANGE, "nrcs"
        )
        _warn_if_out_of_range(
            slope_m_per_m, "slope_m_per_m", *_SCS_LAG_SLOPE_RANGE, "nrcs"
        )
        _warn_if_out_of_range(cn, "cn", *_SCS_LAG_CN_RANGE, "nrcs")

        # Convert input units to formula units
        length_m = length_km * 1000.0  # km -> m
        slope_percent = slope_m_per_m * 100.0  # m/m -> %

        # Calculate maximum retention S [mm]
        # S = (25400/CN) - 254 (metric version of (1000/CN) - 10 in inches)
        if cn == 100:
            retention_mm = 0.0
        else:
            retention_mm = (25400.0 / cn) - 254.0

        # tc formula (from tlag / 0.6): tc [min]
        tc_min = 0.01416 * length_m**0.8 * (retention_mm + 25.4)**0.7 * slope_percent**(-0.5)

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
        Formula:
            tc [h] = (4 * sqrt(A) + 1.5 * L) / (0.8 * sqrt(H))

        Where:
        - tc: time of concentration [hours] (converted to minutes internally)
        - A: watershed area [km²]
        - L: main channel length [km]
        - H: elevation difference between mean elevation and outlet [m]

        The original formula outputs time in **hours**. This implementation
        converts the result to minutes for consistency with other methods.

        References
        ----------
        Giandotti, M. (1934). Previsione delle piene e delle magre dei
        corsi d'acqua. Memorie e Studi Idrografici, Vol. 8.
        Ministero dei Lavori Pubblici, Servizio Idrografico Italiano, Roma.

        Grimaldi, S. et al. (2012). Time of concentration: a paradox in
        modern hydrology. Hydrological Sciences Journal, 57(2), 217-228.
        https://doi.org/10.1080/02626667.2011.644244

        Michailidi, E.M. et al. (2018). Timing the time of concentration:
        shedding light on a paradox. Hydrological Sciences Journal, 63(5).
        https://doi.org/10.1080/02626667.2018.1450985

        Examples
        --------
        >>> ConcentrationTime.giandotti(area_km2=45.0, length_km=12.0, elevation_diff_m=350.0)
        179.7...
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
