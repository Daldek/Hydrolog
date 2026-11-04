"""Time of concentration calculation methods.

A formula warns (:class:`~hydrolog._warnings.OutsideTypicalRange`) for an argument
outside the typical range of its data; the ranges and their sources are those of
:data:`hydrolog._ranges.TYPICAL_RANGES`. The area of the watershed, which only
Giandotti's formula takes, is checked by ``WatershedParameters.calculate_tc``.
"""

from hydrolog._ranges import warn_if_outside
from hydrolog.exceptions import InvalidParameterError

_KERBY_LOW_SLOPE_THRESHOLD = 0.002  # m/m
_KERBY_LOW_SLOPE_OFFSET = 0.0005  # m/m


def _require_positive(value: float, name: str) -> None:
    """Raise if ``value`` is not positive; ``details.option`` names the argument."""
    if value <= 0:
        raise InvalidParameterError(
            f"{name} must be positive, got {value}",
            details={
                "option": name,
                "reason": "exclusive_minimum",
                "exclusive_minimum": 0,
                "value": value,
            },
        )


def _kirpich_min(length_km: float, slope_m_per_m: float) -> float:
    """Kirpich time of concentration [min] of checked arguments."""
    return float(3.981 * (length_km**0.77) * (slope_m_per_m ** (-0.385)))


def _kerby_min(length_km: float, slope_m_per_m: float, retardance: float) -> float:
    """Kerby time of concentration [min] of checked arguments.

    With the low-slope adjustment of Cleveland et al. (2012).
    """
    slope = slope_m_per_m
    if slope < _KERBY_LOW_SLOPE_THRESHOLD:
        slope = slope + _KERBY_LOW_SLOPE_OFFSET
    return float(36.37 * (length_km * retardance) ** 0.467 * slope ** (-0.2335))


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
        OutsideTypicalRange
            If slope_m_per_m is outside the slopes of Kirpich's data (method
            ``kirpich``; the ranges and their sources:
            :data:`hydrolog._ranges.TYPICAL_RANGES`). The area of the data is
            checked by ``WatershedParameters.calculate_tc``.

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
        areas 0.005-0.45 km² (1.25-112 acres), slopes 3-10% (Kirpich 1940; Roussel
        et al. 2005; USDA-NRCS 2010, NEH Part 630, chapter 15).

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
        _require_positive(length_km, "length_km")
        _require_positive(slope_m_per_m, "slope_m_per_m")

        warn_if_outside("kirpich", "slope_m_per_m", slope_m_per_m)

        # Kirpich formula: tc [minutes]
        return _kirpich_min(length_km, slope_m_per_m)

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
            Must be positive.
        slope_m_per_m : float
            Average watershed slope [m/m]. Must be positive.
        cn : int
            SCS Curve Number (1-100). CN=100 means no retention.

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
        OutsideTypicalRange
            If cn is outside the CN that Mockus (1961) allows in the lag equation
            (method ``nrcs``; the ranges and their sources:
            :data:`hydrolog._ranges.TYPICAL_RANGES`). The area of the 24
            watersheds of the equation is checked by
            ``WatershedParameters.calculate_tc``.

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
        _require_positive(length_km, "length_km")
        _require_positive(slope_m_per_m, "slope_m_per_m")
        if not 1 <= cn <= 100:
            raise InvalidParameterError(
                f"cn must be in range 1-100, got {cn}",
                details={
                    "option": "cn",
                    "reason": "range",
                    "minimum": 1,
                    "maximum": 100,
                    "value": cn,
                },
            )

        warn_if_outside("nrcs", "cn", cn)

        # Convert input units to formula units
        length_m = length_km * 1000.0  # km -> m
        slope_percent = slope_m_per_m * 100.0  # m/m -> %

        # Calculate maximum retention S [mm]
        # S = (25400/CN) - 254 (metric version of (1000/CN) - 10 in inches)
        retention_mm = 0.0 if cn == 100 else 25400.0 / cn - 254.0

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

        The Giandotti formula (1934) was derived from large Italian basins
        (Grimaldi et al. 2012).

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
        OutsideTypicalRange
            If area_km2 is outside the areas of Giandotti's basins (method
            ``giandotti``; the ranges and their sources:
            :data:`hydrolog._ranges.TYPICAL_RANGES`).

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
        >>> ConcentrationTime.giandotti(
        ...     area_km2=45.0, length_km=12.0, elevation_diff_m=350.0
        ... )
        179.7...
        """
        _require_positive(area_km2, "area_km2")
        _require_positive(length_km, "length_km")
        _require_positive(elevation_diff_m, "elevation_diff_m")

        warn_if_outside("giandotti", "area_km2", area_km2)

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
        OutsideTypicalRange
            If runoff_coeff is above the coefficients of the method's table (FAA
            1970, AC 150/5320-5B, table I; method ``faa``; the ranges and their
            sources: :data:`hydrolog._ranges.TYPICAL_RANGES`). The FAA gives no
            limit of the length or the slope: its curves end at 800 ft and the
            formula serves longer paths.

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

        Federal Aviation Administration (1970). Airport Drainage. Advisory
        Circular AC 150/5320-5B. US Department of Transportation.

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
        _require_positive(length_km, "length_km")
        _require_positive(slope_m_per_m, "slope_m_per_m")
        if runoff_coeff <= 0 or runoff_coeff > 1.0:
            raise InvalidParameterError(
                f"runoff_coeff must be in range (0, 1.0], got {runoff_coeff}",
                details={
                    "option": "runoff_coeff",
                    "reason": "range",
                    "exclusive_minimum": 0,
                    "maximum": 1.0,
                    "value": runoff_coeff,
                },
            )

        warn_if_outside("faa", "runoff_coeff", runoff_coeff)

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
        OutsideTypicalRange
            If length_km, slope_m_per_m or retardance is outside Kerby's data:
            overland flow up to 1200 ft, slopes below 1%, his table of N (method
            ``kerby``; the ranges and their sources:
            :data:`hydrolog._ranges.TYPICAL_RANGES`). The area of the data, below
            10 acres, is checked by ``WatershedParameters.calculate_tc``. The
            slope is checked before the low-slope adjustment.

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
        >>> ConcentrationTime.kerby(
        ...     length_km=0.10, slope_m_per_m=0.008, retardance=0.40
        ... )
        24.9...
        """
        _require_positive(length_km, "length_km")
        _require_positive(slope_m_per_m, "slope_m_per_m")
        _require_positive(retardance, "retardance")

        warn_if_outside("kerby", "length_km", length_km)
        warn_if_outside("kerby", "slope_m_per_m", slope_m_per_m)
        warn_if_outside("kerby", "retardance", retardance)

        # Kerby formula: tc [minutes], with the low-slope adjustment
        return _kerby_min(length_km, slope_m_per_m, retardance)

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
        OutsideTypicalRange
            If the overland flow length or the retardance is outside Kerby's data,
            or the channel length or slope outside the main channels of the 92
            Texas watersheds the method was verified on (method
            ``kerby_kirpich``; the ranges and their sources:
            :data:`hydrolog._ranges.TYPICAL_RANGES`). The method's guidance gives
            no range of the overland slope; the area of the watersheds is checked
            by ``WatershedParameters.calculate_tc``.

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

        The method was verified by Roussel et al. (2005) on 92 Texas
        watersheds of 0.25-150 mi² with main channels of 1-50 mi.

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
        _require_positive(overland_length_km, "overland_length_km")
        _require_positive(overland_slope_m_per_m, "overland_slope_m_per_m")
        _require_positive(retardance, "retardance")
        _require_positive(channel_length_km, "channel_length_km")
        _require_positive(channel_slope_m_per_m, "channel_slope_m_per_m")

        for name, value in (
            ("overland_length_km", overland_length_km),
            ("retardance", retardance),
            ("channel_length_km", channel_length_km),
            ("channel_slope_m_per_m", channel_slope_m_per_m),
        ):
            warn_if_outside("kerby_kirpich", name, value)

        # Low-slope adjustment for channel slope (Cleveland et al. 2012)
        # Kerby already applies this internally for overland slope
        channel_slope_adj = channel_slope_m_per_m
        if channel_slope_adj < _KERBY_LOW_SLOPE_THRESHOLD:
            channel_slope_adj = channel_slope_adj + _KERBY_LOW_SLOPE_OFFSET

        # Overland flow component (Kerby) and channel flow component (Kirpich),
        # without the warnings of the two methods: those above name the arguments
        # of this one
        t_overland = _kerby_min(overland_length_km, overland_slope_m_per_m, retardance)
        t_channel = _kirpich_min(channel_length_km, channel_slope_adj)

        tc_min: float = t_overland + t_channel

        return tc_min
