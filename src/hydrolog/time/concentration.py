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

    With the low-slope offset of Cleveland et al. (2012), TxDOT 0-6382-P1.
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
            Length of the longest flow path, along the watercourse from the outlet
            to the most remote point on the watershed divide [km]. Must be
            positive.
        slope_m_per_m : float
            Slope of that path: the elevation of the most remote point minus the
            elevation of the outlet, over the length [m/m]. Must be positive.

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

        L and S are those of Fang et al. (2005, eq. 3.14): "The channel slope Sc
        was defined as the difference in elevation ... between the most remote
        point in the watershed and the outlet divided by the channel length Lc".
        Kirpich (1940) gave a graph of tc against L/sqrt(S) with L measured along
        the watercourse from the outlet to the highest point of the basin and S
        the drop between the two points over L (Mota and Kobiyama 2015). From a
        DEM: the longest flow path and the elevation of its upstream end.

        References
        ----------
        Kirpich, Z.P. (1940). Time of concentration of small agricultural
        watersheds. Civil Engineering, 10(6), 362.

        Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B., and Malla, R.
        (2005). Literature review on timing parameters for hydrographs. TxDOT
        Research Report 0-4696-1, eq. 3.14.

        Mota, A.A. and Kobiyama, M. (2015). Reconsiderações sobre a fórmula de
        Kirpich para o cálculo de tempo de concentração. Revista Brasileira de
        Recursos Hídricos, 20(1), 55-59.

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
            Flow length: the longest path along which water flows from the
            hydraulically most distant point of the watershed to the outlet [km].
            Must be positive.
        slope_m_per_m : float
            Average land slope of the watershed Y [m/m], not the slope of the flow
            path. Must be positive.
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
        Original formula (US units; USDA-NRCS 2010, NEH Part 630, chapter 15,
        eq. 15-4a, with tc = lag / 0.6 of eq. 15-3):
            tlag[h] = (L[ft]^0.8 * (S[in] + 1)^0.7) / (1900 * Y[%]^0.5)

        Metric conversion (this implementation):
            Lag [h] = (L[m]^0.8 * (S[mm] + 25.4)^0.7) / (7069 * Y[%]^0.5)
            tc = Lag / 0.6

        The constant 7069 = 1900 * 0.3048^0.8 * 25.4^0.7 is derived from:
            L[ft] = L[m] / 0.3048
            (S[in] + 1) = (S[mm] + 25.4) / 25.4

        Where:
        - L: flow length, the longest flow path [m] (converted internally from km)
        - S: maximum retention = (25400/CN) - 254 [mm]
        - Y: average land slope of the watershed [%] (converted internally from
          m/m), "not to be confused with the slope of the flow path" (NEH 630,
          p. 15-5)

        **Important distinction:**
        - tc (time of concentration) = time for runoff to travel from the
          most distant point to the outlet
        - tlag = 0.6 * tc = time from centroid of rainfall to peak flow

        This method calculates tc, not tp. For unit hydrograph calculations,
        use tp = D/2 + 0.6*tc.

        References
        ----------
        USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology,
        Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eq. 15-4.
        https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf

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
            Overland flow length, from the most remote point of the drainage area
            to the inlet [km]. Must be positive.
        slope_m_per_m : float
            Slope of the overland flow surface [m/m]. Must be positive.
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
        Original formula (US units; FAA 1970, AC 150/5320-5B, fig. 7 "Surface
        flow time curves", whose curves are labelled with the slope in percent):

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

        - C: rational method runoff coefficient (dimensionless), from table I of
          the circular
        - L: overland flow length, the distance the "inlet time" covers "from the
          most remote point in the drainage subarea to the inlet"
        - S: slope of the overland flow surface

        The later circulars AC 150/5320-5C (2006) and 5D (2013) do not have the
        formula: they time the flow with the NRCS segment method.

        References
        ----------
        Federal Aviation Administration (1970). Airport Drainage. Advisory
        Circular AC 150/5320-5B, fig. 7 and table I. US Department of
        Transportation.

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
            Overland flow length, from the most distant point until a defined
            channel is reached [km]. Must be positive.
        slope_m_per_m : float
            Slope of the terrain the overland flow runs on [m/m]. Must be
            positive.
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

        Low-slope adjustment (Cleveland et al. 2012, TxDOT 0-6382-P1):

            For S < 0.002: S_adj = S + 0.0005

        This prevents unreasonably large tc values on very flat terrain.

        References
        ----------
        Kerby, W.S. (1959). Time of concentration for overland flow.
        Civil Engineering, 29(3), 174.

        Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G., and
        Garcia, C.A. (2005). Time-parameter estimation for applicable Texas
        watersheds. TxDOT Research Report 0-4696-2.

        Cleveland, T.G., Thompson, D.B., Fang, X., and Li, M.-H. (2012). Guidance
        for estimation of time of concentration in Texas for low-slope
        conditions. TxDOT Product 0-6382-P1, Texas Tech University.

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
        flow_path_length_km: float,
        flow_path_slope_m_per_m: float,
    ) -> float:
        """
        Calculate time of concentration using the Kerby-Kirpich composite method.

        The Kerby-Kirpich method splits the longest flow path into two segments:
        overland (sheet) flow estimated with the Kerby equation and channel flow
        estimated with the Kirpich equation. The total time of concentration is
        the sum of both components.

        Parameters
        ----------
        overland_length_km : float
            Overland (sheet) flow length from the hydraulically most distant
            point to the start of a defined channel [km]. Must be positive.
        overland_slope_m_per_m : float
            Slope of the terrain the overland flow runs on [m/m]. Must be
            positive.
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

        flow_path_length_km : float
            Length of the main channel as the method defines it: the primary
            (longest) flow path from the hydraulically most distant point of the
            watershed (usually on the divide) to the outlet, the
            overland segment included [km]. Must be greater than
            ``overland_length_km``: the channel segment is the difference.
        flow_path_slope_m_per_m : float
            Slope of that path: the elevation of its head minus the elevation at
            the outlet, over ``flow_path_length_km`` [m/m]. Must be positive.

        Returns
        -------
        float
            Total time of concentration [min], i.e. t_overland + t_channel.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive, or ``flow_path_length_km`` is not
            greater than ``overland_length_km`` (``details.option``
            ``flow_path_length_km``, ``details.reason`` ``exclusive_minimum``).

        Warns
        -----
        OutsideTypicalRange
            If the overland flow length or the retardance is outside Kerby's data,
            or the flow path length or slope outside the main channels of the 92
            Texas watersheds the method was verified on (method
            ``kerby_kirpich``; the ranges and their sources:
            :data:`hydrolog._ranges.TYPICAL_RANGES`). The method's guidance gives
            no range of the overland slope; the area of the watersheds is checked
            by ``WatershedParameters.calculate_tc``.

        Notes
        -----
        The composite method treats the longest flow path as two consecutive
        segments:

            tc = t_overland + t_channel
            t_overland = Kerby(L_ov, S_ov, N)
            t_channel = Kirpich(L_fp - L_ov, S_fp)

        where L_fp and S_fp are the length and the slope of the main channel as
        Roussel et al. (2005, supplement) define them: "Main channel slope is
        computed as the change in elevation from the watershed divide to the
        watershed outlet divided by the curvilinear distance of the main channel
        (primary flow path) between the watershed divide and the outlet", and in
        their example "the subtraction of the overland flow length from the
        overall main-channel length (watershed divide to outlet) is necessary".

        **Low-slope adjustment** (Cleveland et al. 2012, TxDOT 0-6382-P1):

        For slopes below 0.002 m/m, an offset of 0.0005 is added to
        prevent unreasonably large tc values on very flat terrain:

            S_adj = S + 0.0005  (when S < 0.002)

        This adjustment is applied to **both** segments independently.
        The Kerby method applies it internally, while this composite
        method applies it to the flow path slope before calling Kirpich.

        The method was verified by Roussel et al. (2005) on 92 Texas
        watersheds of 0.25-150 mi² with main channels of 1-50 mi.

        References
        ----------
        Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G., and
        Garcia, C.A. (2005). Time-parameter estimation for applicable Texas
        watersheds. TxDOT Research Report 0-4696-2, supplement.

        Cleveland, T.G., Thompson, D.B., Fang, X., and Li, M.-H. (2012). Guidance
        for estimation of time of concentration in Texas for low-slope
        conditions. TxDOT Product 0-6382-P1, Texas Tech University.

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
        ...     flow_path_length_km=5.25,
        ...     flow_path_slope_m_per_m=0.005,
        ... )
        >>> print(f"{tc:.1f}")
        144.0
        """
        # Validate all parameters
        _require_positive(overland_length_km, "overland_length_km")
        _require_positive(overland_slope_m_per_m, "overland_slope_m_per_m")
        _require_positive(retardance, "retardance")
        _require_positive(flow_path_length_km, "flow_path_length_km")
        _require_positive(flow_path_slope_m_per_m, "flow_path_slope_m_per_m")
        if flow_path_length_km <= overland_length_km:
            raise InvalidParameterError(
                f"flow_path_length_km ({flow_path_length_km}) must be greater than "
                f"overland_length_km ({overland_length_km}): the channel segment is "
                "the flow path minus the overland segment",
                details={
                    "option": "flow_path_length_km",
                    "reason": "exclusive_minimum",
                    "exclusive_minimum": overland_length_km,
                    "value": flow_path_length_km,
                },
                hint=(
                    "Give the whole longest flow path, from the watershed divide to "
                    "the outlet, overland segment included."
                ),
            )

        for name, value in (
            ("overland_length_km", overland_length_km),
            ("retardance", retardance),
            ("flow_path_length_km", flow_path_length_km),
            ("flow_path_slope_m_per_m", flow_path_slope_m_per_m),
        ):
            warn_if_outside("kerby_kirpich", name, value)

        # Low-slope adjustment of the main channel slope (Cleveland et al. 2012);
        # Kerby already applies it to the overland slope
        channel_slope = flow_path_slope_m_per_m
        if channel_slope < _KERBY_LOW_SLOPE_THRESHOLD:
            channel_slope = channel_slope + _KERBY_LOW_SLOPE_OFFSET

        # Overland flow component (Kerby) and channel flow component (Kirpich) on
        # the rest of the flow path, without the warnings of the two methods: those
        # above name the arguments of this one
        t_overland = _kerby_min(overland_length_km, overland_slope_m_per_m, retardance)
        t_channel = _kirpich_min(
            flow_path_length_km - overland_length_km, channel_slope
        )

        tc_min: float = t_overland + t_channel

        return tc_min
