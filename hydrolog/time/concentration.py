"""Time of concentration calculation methods."""

from hydrolog.exceptions import InvalidParameterError


class ConcentrationTime:
    """
    Calculate time of concentration using various empirical methods.

    Time of concentration (tc) is the time required for runoff to travel
    from the hydraulically most distant point in the watershed to the outlet.

    Examples
    --------
    >>> tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
    >>> print(f"{tc:.1f} min")
    52.3 min

    >>> tc = ConcentrationTime.scs_lag(length_m=8200, slope_percent=2.3, cn=72)
    >>> print(f"{tc:.1f} min")
    368.7 min
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

        # Kirpich formula: tc [hours]
        tc_hours: float = 0.0663 * (length_km**0.77) * (slope_m_per_m ** (-0.385))

        # Convert to minutes
        tc_min: float = tc_hours * 60.0
        return tc_min

    @staticmethod
    def scs_lag(
        length_m: float,
        slope_percent: float,
        cn: int,
    ) -> float:
        """
        Calculate time of concentration using SCS Lag equation.

        The SCS Lag equation estimates watershed lag time, which is then
        converted to time of concentration using the relationship tc = L / 0.6,
        where L is the lag time.

        Parameters
        ----------
        length_m : float
            Hydraulic length of the watershed (longest flow path) [m].
            Must be positive.
        slope_percent : float
            Average watershed slope [%]. Must be positive.
        cn : int
            SCS Curve Number (1-100). CN=100 means no retention.

        Returns
        -------
        float
            Time of concentration [min].

        Raises
        ------
        InvalidParameterError
            If length_m <= 0, slope_percent <= 0, or cn not in range 1-100.

        Notes
        -----
        Formula:
        Lag [h] = (L^0.8 * (S + 1)^0.7) / (1900 * Y^0.5)
        tc = Lag / 0.6

        Where:
        - L: hydraulic length [ft] (converted from meters)
        - S: maximum retention = (1000/CN) - 10 [in]
        - Y: average watershed slope [%]

        References
        ----------
        USDA-NRCS (1986). Urban Hydrology for Small Watersheds.
        Technical Release 55 (TR-55).

        Examples
        --------
        >>> ConcentrationTime.scs_lag(length_m=8200, slope_percent=2.3, cn=72)
        75.2...
        """
        if length_m <= 0:
            raise InvalidParameterError(f"length_m must be positive, got {length_m}")
        if slope_percent <= 0:
            raise InvalidParameterError(
                f"slope_percent must be positive, got {slope_percent}"
            )
        if not 1 <= cn <= 100:
            raise InvalidParameterError(f"cn must be in range 1-100, got {cn}")

        # Convert meters to feet (1 m = 3.28084 ft)
        length_ft = length_m * 3.28084

        # Calculate maximum retention S [inches]
        # For CN=100, S=0 (no retention)
        if cn == 100:
            retention_in = 0.0
        else:
            retention_in = (1000.0 / cn) - 10.0

        # SCS Lag equation: Lag [hours]
        # Lag = (L^0.8 * (S + 1)^0.7) / (1900 * Y^0.5)
        lag_hours = ((length_ft**0.8) * ((retention_in + 1) ** 0.7)) / (
            1900.0 * (slope_percent**0.5)
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

        # Giandotti formula: tc [hours]
        tc_hours = (4.0 * (area_km2**0.5) + 1.5 * length_km) / (
            0.8 * (elevation_diff_m**0.5)
        )

        # Convert to minutes
        tc_min: float = tc_hours * 60.0

        return tc_min

    @staticmethod
    def nrcs(
        length_m: float,
        slope_percent: float,
        cn: int,
    ) -> float:
        """
        Calculate time of concentration using NRCS (NEH-4) method.

        The NRCS method from National Engineering Handbook Part 630,
        Chapter 15 estimates time of concentration based on watershed
        lag time.

        Parameters
        ----------
        length_m : float
            Hydraulic length of the watershed (longest flow path) [m].
            Must be positive.
        slope_percent : float
            Average watershed slope [%]. Must be positive.
        cn : int
            SCS Curve Number (1-100). CN=100 means no retention.

        Returns
        -------
        float
            Time of concentration [min].

        Raises
        ------
        InvalidParameterError
            If length_m <= 0, slope_percent <= 0, or cn not in range 1-100.

        Notes
        -----
        Formula:
        Lag [h] = (L^0.8 * ((1000/CN) - 9)^0.7) / (1140 * Y^0.5)
        tc = 5/3 * Lag

        Where:
        - L: hydraulic length [ft] (converted from meters)
        - CN: Curve Number
        - Y: average watershed slope [%]

        The relationship tc = 5/3 * Lag comes from the assumption that
        Lag = 0.6 * tc for the SCS dimensionless unit hydrograph.

        References
        ----------
        USDA-NRCS (2010). National Engineering Handbook, Part 630,
        Chapter 15: Time of Concentration.

        Examples
        --------
        >>> ConcentrationTime.nrcs(length_m=8200, slope_percent=2.3, cn=72)
        195.6...
        """
        if length_m <= 0:
            raise InvalidParameterError(f"length_m must be positive, got {length_m}")
        if slope_percent <= 0:
            raise InvalidParameterError(
                f"slope_percent must be positive, got {slope_percent}"
            )
        if not 1 <= cn <= 100:
            raise InvalidParameterError(f"cn must be in range 1-100, got {cn}")

        # Convert meters to feet (1 m = 3.28084 ft)
        length_ft = length_m * 3.28084

        # Calculate retention term: (1000/CN) - 9
        # For CN=100, this becomes -9, but we'll handle it
        if cn == 100:
            retention_term = 1.0  # Minimum value to avoid negative
        else:
            retention_term = (1000.0 / cn) - 9.0
            if retention_term < 1.0:
                retention_term = 1.0

        # NRCS Lag equation: Lag [hours]
        # Lag = (L^0.8 * ((1000/CN) - 9)^0.7) / (1140 * Y^0.5)
        lag_hours = ((length_ft**0.8) * (retention_term**0.7)) / (
            1140.0 * (slope_percent**0.5)
        )

        # Convert lag to tc: tc = Lag * (5/3) = Lag / 0.6
        tc_hours = lag_hours * (5.0 / 3.0)

        # Convert to minutes
        tc_min: float = tc_hours * 60.0

        return tc_min
