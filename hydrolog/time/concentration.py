"""Time of concentration calculation methods."""

import warnings

from hydrolog.exceptions import InvalidParameterError

# Typical parameter ranges for validation warnings
_KIRPICH_LENGTH_RANGE = (0.001, 80.0)  # km
_KIRPICH_SLOPE_RANGE = (0.002, 0.15)  # m/m

_NRCS_LENGTH_RANGE = (0.03, 30.0)  # km
_NRCS_SLOPE_RANGE = (0.001, 0.15)  # m/m
_NRCS_CN_RANGE = (50, 95)  # dimensionless

_GIANDOTTI_AREA_RANGE = (100.0, 10000.0)  # km2
_GIANDOTTI_LENGTH_RANGE = (1.0, 300.0)  # km
_GIANDOTTI_ELEVATION_RANGE = (20.0, 3000.0)  # m

_FAA_LENGTH_RANGE = (0.015, 3.0)  # km (50 ft to 10,000 ft)
_FAA_SLOPE_RANGE = (0.005, 0.10)  # m/m (0.5% to 10%)
_FAA_C_RANGE = (0.10, 0.95)  # dimensionless

_KERBY_LENGTH_RANGE = (0.01, 0.366)  # km (approx 30 ft to 1200 ft)
_KERBY_SLOPE_RANGE = (0.001, 0.01)  # m/m (original calibration)
_KERBY_N_RANGE = (0.02, 0.80)  # dimensionless

_KERBY_LOW_SLOPE_THRESHOLD = 0.002  # m/m
_KERBY_LOW_SLOPE_OFFSET = 0.0005  # m/m


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
        _warn_if_out_of_range(length_km, "length_km", *_KIRPICH_LENGTH_RANGE, "kirpich")
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
            tlag[h] = (L[ft]^0.8 * (S[in] + 1)^0.7) / (1900 * Y[%]^0.5)

        Metric conversion (this implementation):
            Lag [h] = (L[m]^0.8 * (S[mm] + 25.4)^0.7) / (7069 * Y[%]^0.5)
            tc = Lag / 0.6

        The constant 7069 = 1900 * 0.3048^0.8 * 25.4^0.7 is derived from:
            L[ft] = L[m] / 0.3048
            (S[in] + 1) = (S[mm] + 25.4) / 25.4

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
            raise InvalidParameterError(f"length_km must be positive, got {length_km}")
        if slope_m_per_m <= 0:
            raise InvalidParameterError(
                f"slope_m_per_m must be positive, got {slope_m_per_m}"
            )
        if not 1 <= cn <= 100:
            raise InvalidParameterError(f"cn must be in range 1-100, got {cn}")

        # Warn if parameters are outside typical range
        _warn_if_out_of_range(length_km, "length_km", *_NRCS_LENGTH_RANGE, "nrcs")
        _warn_if_out_of_range(
            slope_m_per_m, "slope_m_per_m", *_NRCS_SLOPE_RANGE, "nrcs"
        )
        _warn_if_out_of_range(cn, "cn", *_NRCS_CN_RANGE, "nrcs")

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
        tc_min: float = (
            0.01416
            * length_m**0.8
            * (retention_mm + 25.4) ** 0.7
            * slope_percent ** (-0.5)
        )

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
        _warn_if_out_of_range(area_km2, "area_km2", *_GIANDOTTI_AREA_RANGE, "giandotti")
        _warn_if_out_of_range(
            length_km, "length_km", *_GIANDOTTI_LENGTH_RANGE, "giandotti"
        )
        _warn_if_out_of_range(
            elevation_diff_m,
            "elevation_diff_m",
            *_GIANDOTTI_ELEVATION_RANGE,
            "giandotti",
        )

        # Giandotti formula: tc [hours]
        tc_hours = (4.0 * (area_km2**0.5) + 1.5 * length_km) / (
            0.8 * (elevation_diff_m**0.5)
        )

        # Convert to minutes
        tc_min: float = tc_hours * 60.0

        return tc_min

    @staticmethod
    def faa(
        length_km: float,
        slope_m_per_m: float,
        runoff_coeff: float,
    ) -> float:
        """
        Calculate time of concentration using the FAA method.

        The FAA (Federal Aviation Agency) method was originally developed
        for airport drainage design and is suitable for overland flow
        on relatively flat surfaces with short flow paths.

        Parameters
        ----------
        length_km : float
            Overland flow length [km]. Must be positive.
        slope_m_per_m : float
            Average overland slope [m/m]. Must be positive.
        runoff_coeff : float
            Rational method runoff coefficient (0 < C <= 1.0).
            Must be greater than 0 and at most 1.0.

        Returns
        -------
        float
            Time of concentration [min].

        Raises
        ------
        InvalidParameterError
            If length_km <= 0, slope_m_per_m <= 0, or runoff_coeff
            is not in the range (0, 1.0].

        Warns
        -----
        UserWarning
            If parameters are outside typical application ranges:
            length_km outside [0.015, 3.0] km, slope_m_per_m outside
            [0.005, 0.10], or runoff_coeff outside [0.10, 0.95].

        Notes
        -----
        Original formula (US units):

            tc [min] = 1.8 * (1.1 - C) * L[ft]^0.5 / S[%]^(1/3)

        Metric conversion (this implementation):

            tc [min] = 22.213 * (1.1 - C) * L[km]^0.5 / S[m/m]^(1/3)

        Derivation of the metric constant 22.213:

            L[ft] = L[km] * 1000 / 0.3048
            S[%] = S[m/m] * 100

            tc = 1.8 * (1.1 - C) * (L[km] * 1000 / 0.3048)^0.5
                 / (S[m/m] * 100)^(1/3)
            tc = 1.8 * (1/0.3048)^0.5 * 1000^0.5 / 100^(1/3)
                 * (1.1 - C) * L[km]^0.5 / S[m/m]^(1/3)
            1.8 * (1/0.3048)^0.5 * 1000^0.5 / 100^(1/3) = 22.213

        Where:

        - C: rational method runoff coefficient (dimensionless)
        - L: overland flow length
        - S: average overland slope

        References
        ----------
        Federal Aviation Agency (1966). Airport Drainage. Advisory Circular
        AC 150/5320-5A. US Department of Transportation.

        Federal Aviation Administration (2013). Airport Drainage Design.
        Advisory Circular AC 150/5320-5D. US Department of Transportation.

        Chin, D.A. (2000). Water-Resources Engineering. Prentice Hall.

        Chow, V.T., Maidment, D.R. & Mays, L.W. (1988). Applied Hydrology.
        McGraw-Hill.

        Examples
        --------
        >>> ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.02, runoff_coeff=0.6)
        15.8...
        """
        if length_km <= 0:
            raise InvalidParameterError(f"length_km must be positive, got {length_km}")
        if slope_m_per_m <= 0:
            raise InvalidParameterError(
                f"slope_m_per_m must be positive, got {slope_m_per_m}"
            )
        if runoff_coeff <= 0 or runoff_coeff > 1.0:
            raise InvalidParameterError(
                f"runoff_coeff must be in range (0, 1.0], got {runoff_coeff}"
            )

        # Warn if parameters are outside typical range
        _warn_if_out_of_range(length_km, "length_km", *_FAA_LENGTH_RANGE, "faa")
        _warn_if_out_of_range(slope_m_per_m, "slope_m_per_m", *_FAA_SLOPE_RANGE, "faa")
        _warn_if_out_of_range(runoff_coeff, "runoff_coeff", *_FAA_C_RANGE, "faa")

        # FAA formula: tc [minutes]
        tc_min: float = (
            22.213
            * (1.1 - runoff_coeff)
            * (length_km**0.5)
            / (slope_m_per_m ** (1.0 / 3.0))
        )

        return tc_min

    @staticmethod
    def kerby(
        length_km: float,
        slope_m_per_m: float,
        retardance: float,
    ) -> float:
        """
        Calculate time of concentration using the Kerby formula.

        The Kerby formula (1959) estimates tc for shallow overland
        (sheet) flow on small, relatively flat catchments. It is commonly
        used as the overland-flow component in composite tc methods
        (e.g., Kerby-Kirpich).

        Parameters
        ----------
        length_km : float
            Overland flow length [km]. Must be positive.
        slope_m_per_m : float
            Average overland slope [m/m]. Must be positive.
        retardance : float
            Kerby retardance roughness coefficient (dimensionless).
            Must be positive. Typical values:

            ========================================================  =====
            Surface                                                   N
            ========================================================  =====
            Smooth impervious (pavement, asphalt, concrete)           0.02
            Smooth bare packed soil                                    0.10
            Poor grass, cultivated row crops                           0.20
            Pasture, average grass                                     0.40
            Deciduous forest                                           0.60
            Dense grass, coniferous forest, deciduous forest w/ litter 0.80
            ========================================================  =====

        Returns
        -------
        float
            Time of concentration [min].

        Raises
        ------
        InvalidParameterError
            If length_km <= 0, slope_m_per_m <= 0, or retardance <= 0.

        Warns
        -----
        UserWarning
            If parameters are outside typical application ranges:
            length_km outside [0.01, 0.366] km, slope_m_per_m outside
            [0.001, 0.01], or retardance outside [0.02, 0.80].

        Notes
        -----
        Original formula (US units):

            tc [min] = (0.67 * L[ft] * N / sqrt(S))^0.467

        Expanded form:

            tc [min] = 0.67^0.467 * (L[ft] * N)^0.467 * S^(-0.5*0.467)
            tc [min] = 0.8294 * (L[ft] * N)^0.467 * S^(-0.2335)

        Metric conversion (this implementation):

            tc [min] = 36.37 * (L[km] * N)^0.467 * S^(-0.2335)

        Derivation of the metric constant 36.37:

            L[ft] = L[m] / 0.3048
            K_SI = (0.67 / 0.3048)^0.467 = 2.19816^0.467 = 1.4446

            L[m] = L[km] * 1000
            K_km = 1.4446 * 1000^0.467 = 1.4446 * 25.1768 = 36.37

            tc [min] = 36.37 * (L[km] * N)^0.467 * S^(-0.2335)

        Low-slope adjustment (Cleveland et al. 2012):

            For S < 0.002: S_adj = S + 0.0005

        This prevents unreasonably large tc values on very flat terrain.

        References
        ----------
        Kerby, W.S. (1959). Time of concentration for overland flow.
        Civil Engineering, 29(3), 174.

        Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G., and
        Garcia, C.A. (2005). Time-parameter estimation for applicable Texas
        watersheds. TxDOT Research Report 0-4696-2.

        Cleveland, T.G., Thompson, D.B., and Fang, X. (2012). Use of the
        Kerby-Kirpich approach for Texas watersheds. TxDOT Research Report
        0-6544-1.

        Texas Department of Transportation (2019). Hydraulic Design Manual.
        Chapter 4: Time of Concentration.

        Examples
        --------
        >>> ConcentrationTime.kerby(length_km=0.10, slope_m_per_m=0.008, retardance=0.40)
        24.9...
        """
        if length_km <= 0:
            raise InvalidParameterError(f"length_km must be positive, got {length_km}")
        if slope_m_per_m <= 0:
            raise InvalidParameterError(
                f"slope_m_per_m must be positive, got {slope_m_per_m}"
            )
        if retardance <= 0:
            raise InvalidParameterError(
                f"retardance must be positive, got {retardance}"
            )

        # Warn if parameters are outside typical range
        _warn_if_out_of_range(length_km, "length_km", *_KERBY_LENGTH_RANGE, "kerby")
        _warn_if_out_of_range(
            slope_m_per_m, "slope_m_per_m", *_KERBY_SLOPE_RANGE, "kerby"
        )
        _warn_if_out_of_range(retardance, "retardance", *_KERBY_N_RANGE, "kerby")

        # Low-slope adjustment (Cleveland et al. 2012)
        slope = slope_m_per_m
        if slope < _KERBY_LOW_SLOPE_THRESHOLD:
            slope = slope + _KERBY_LOW_SLOPE_OFFSET

        # Kerby formula: tc [minutes]
        tc_min: float = 36.37 * (length_km * retardance) ** 0.467 * slope ** (-0.2335)

        return tc_min

    @staticmethod
    def kerby_kirpich(
        overland_length_km: float,
        overland_slope_m_per_m: float,
        retardance: float,
        channel_length_km: float,
        channel_slope_m_per_m: float,
    ) -> float:
        """
        Calculate time of concentration using the Kerby-Kirpich composite method.

        The Kerby-Kirpich method splits the watershed flow path into two
        segments: overland (sheet) flow estimated with the Kerby equation
        and channel flow estimated with the Kirpich equation. The total
        time of concentration is the sum of both components.

        Parameters
        ----------
        overland_length_km : float
            Overland (sheet) flow length from the hydraulically most distant
            point to the start of a defined channel [km]. Must be positive.
        overland_slope_m_per_m : float
            Average overland slope [m/m]. Must be positive.
        retardance : float
            Kerby retardance roughness coefficient (dimensionless).
            Must be positive. Typical values:

            ========================================================  =====
            Surface                                                   N
            ========================================================  =====
            Smooth impervious (pavement, asphalt, concrete)           0.02
            Smooth bare packed soil                                    0.10
            Poor grass, cultivated row crops                           0.20
            Pasture, average grass                                     0.40
            Deciduous forest                                           0.60
            Dense grass, coniferous forest, deciduous forest w/ litter 0.80
            ========================================================  =====

        channel_length_km : float
            Channel flow length from the start of the defined channel
            to the watershed outlet [km]. Must be positive.
        channel_slope_m_per_m : float
            Average channel slope [m/m]. Must be positive.

        Returns
        -------
        float
            Total time of concentration [min], i.e. t_overland + t_channel.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.

        Warns
        -----
        UserWarning
            If overland parameters are outside Kerby typical ranges
            (length > 0.366 km, slope outside 0.001-0.01, retardance
            outside 0.02-0.80) or channel parameters are outside Kirpich
            typical ranges (length > 80 km, slope outside 0.002-0.15).

        Notes
        -----
        The composite method treats the watershed flow path as two
        consecutive segments:

            tc = t_overland + t_channel

        where t_overland is computed with the Kerby (1959) equation and
        t_channel with the Kirpich (1940) equation.

        **Low-slope adjustment** (Cleveland et al. 2012):

        For slopes below 0.002 m/m, an offset of 0.0005 is added to
        prevent unreasonably large tc values on very flat terrain:

            S_adj = S + 0.0005  (when S < 0.002)

        This adjustment is applied to **both** segments independently.
        The Kerby method applies it internally, while this composite
        method applies it to the channel slope before calling Kirpich.

        The method was validated by Roussel et al. (2005) on 92 Texas
        watersheds ranging from 0.65 to 388 km².

        References
        ----------
        Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G., and
        Garcia, C.A. (2005). Time-parameter estimation for applicable Texas
        watersheds. TxDOT Research Report 0-4696-2.

        Cleveland, T.G., Thompson, D.B., and Fang, X. (2012). Use of the
        Kerby-Kirpich approach for Texas watersheds. TxDOT Research Report
        0-6544-1.

        Texas Department of Transportation (2019). Hydraulic Design Manual.
        Chapter 4: Time of Concentration.

        Kerby, W.S. (1959). Time of concentration for overland flow.
        Civil Engineering, 29(3), 174.

        Kirpich, Z.P. (1940). Time of concentration of small agricultural
        watersheds. Civil Engineering, 10(6), 362.

        Examples
        --------
        >>> tc = ConcentrationTime.kerby_kirpich(
        ...     overland_length_km=0.25,
        ...     overland_slope_m_per_m=0.008,
        ...     retardance=0.40,
        ...     channel_length_km=5.0,
        ...     channel_slope_m_per_m=0.005,
        ... )
        >>> print(f"{tc:.1f}")
        144.0
        """
        # Validate all parameters
        if overland_length_km <= 0:
            raise InvalidParameterError(
                f"overland_length_km must be positive, got {overland_length_km}"
            )
        if overland_slope_m_per_m <= 0:
            raise InvalidParameterError(
                f"overland_slope_m_per_m must be positive, "
                f"got {overland_slope_m_per_m}"
            )
        if retardance <= 0:
            raise InvalidParameterError(
                f"retardance must be positive, got {retardance}"
            )
        if channel_length_km <= 0:
            raise InvalidParameterError(
                f"channel_length_km must be positive, got {channel_length_km}"
            )
        if channel_slope_m_per_m <= 0:
            raise InvalidParameterError(
                f"channel_slope_m_per_m must be positive, "
                f"got {channel_slope_m_per_m}"
            )

        # Warn if overland params are outside Kerby typical ranges
        _warn_if_out_of_range(
            overland_length_km,
            "overland_length_km",
            *_KERBY_LENGTH_RANGE,
            "kerby_kirpich",
        )
        _warn_if_out_of_range(
            overland_slope_m_per_m,
            "overland_slope_m_per_m",
            *_KERBY_SLOPE_RANGE,
            "kerby_kirpich",
        )
        _warn_if_out_of_range(
            retardance,
            "retardance",
            *_KERBY_N_RANGE,
            "kerby_kirpich",
        )

        # Warn if channel params are outside Kirpich typical ranges
        _warn_if_out_of_range(
            channel_length_km,
            "channel_length_km",
            *_KIRPICH_LENGTH_RANGE,
            "kerby_kirpich",
        )
        _warn_if_out_of_range(
            channel_slope_m_per_m,
            "channel_slope_m_per_m",
            *_KIRPICH_SLOPE_RANGE,
            "kerby_kirpich",
        )

        # Low-slope adjustment for channel slope (Cleveland et al. 2012)
        # Kerby already applies this internally for overland slope
        channel_slope_adj = channel_slope_m_per_m
        if channel_slope_adj < _KERBY_LOW_SLOPE_THRESHOLD:
            channel_slope_adj = channel_slope_adj + _KERBY_LOW_SLOPE_OFFSET

        # Overland flow component (Kerby)
        t_overland: float = ConcentrationTime.kerby(
            overland_length_km, overland_slope_m_per_m, retardance
        )

        # Channel flow component (Kirpich)
        t_channel: float = ConcentrationTime.kirpich(
            channel_length_km, channel_slope_adj
        )

        tc_min: float = t_overland + t_channel

        return tc_min
