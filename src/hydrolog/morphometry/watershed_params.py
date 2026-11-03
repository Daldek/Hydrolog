"""Standardized watershed parameters for integration with GIS systems."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, cast

from hydrolog.exceptions import InvalidParameterError

if TYPE_CHECKING:
    from hydrolog.morphometry.geometric import WatershedGeometry
    from hydrolog.morphometry.terrain import TerrainAnalysis

TC_METHODS = ("kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich")
"""The methods of :meth:`WatershedParameters.calculate_tc`."""

# Fields besides the always present ones that a time of concentration method cannot
# do without, in the order they are reported. FAA and Kerby are overland flow
# formulas: they get the overland flow length and slope, never the channel's.
_TC_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "nrcs": ("cn",),
    "faa": ("runoff_coeff", "overland_length_km", "overland_slope_m_per_m"),
    "kerby": ("retardance", "overland_length_km", "overland_slope_m_per_m"),
    "kerby_kirpich": (
        "retardance",
        "overland_length_km",
        "overland_slope_m_per_m",
        "channel_length_km",
        "channel_slope_m_per_m",
    ),
}

_TC_METHOD_LABELS = {
    "nrcs": "NRCS",
    "faa": "FAA",
    "kerby": "Kerby",
    "kerby_kirpich": "Kerby-Kirpich",
}

_OVERLAND_HINT = (
    "FAA and Kerby time the overland flow, so they need the overland flow length "
    "and slope of the watershed (overland_length_km, overland_slope_m_per_m), not "
    "those of the channel; for a watershed with a channel use kerby_kirpich or "
    "kirpich."
)
_TC_MISSING_HINTS: dict[str, str] = {"faa": _OVERLAND_HINT, "kerby": _OVERLAND_HINT}


@dataclass
class WatershedParameters:
    """
    Standardized watershed parameters for hydrological calculations.

    This dataclass serves as the interface for data exchange between GIS systems
    (Hydrograf, QGIS, ArcGIS) and the Hydrolog library. It provides a consistent
    format for watershed parameters that can be serialized to/from JSON.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²]. Must be positive.
    perimeter_km : float
        Watershed perimeter [km]. Must be positive.
    length_km : float
        Watershed length - distance from outlet to most distant point [km].
        Must be positive.
    elevation_min_m : float
        Minimum elevation at outlet [m a.s.l.].
    elevation_max_m : float
        Maximum elevation in watershed [m a.s.l.].
    name : str, optional
        Watershed name for identification.
    elevation_mean_m : float, optional
        Area-weighted mean elevation [m a.s.l.].
    mean_slope_m_per_m : float, optional
        Area-weighted mean slope of the watershed [m/m]. The average land slope
        Y of the NRCS concentration time method (TR-55); Kirpich falls back to it
        when there is no channel slope.
    channel_length_km : float, optional
        Main channel length [km].
    channel_slope_m_per_m : float, optional
        Main channel slope [m/m]. Used by the Kirpich method and by the channel
        segment of Kerby-Kirpich; NRCS falls back to it when there is no mean
        slope.
    cn : int, optional
        SCS Curve Number (0-100).
    source : str, optional
        Data source identifier (e.g., "Hydrograf", "QGIS", "manual").
    crs : str, optional
        Coordinate reference system (e.g., "EPSG:2180").
    runoff_coeff : float, optional
        Rational method runoff coefficient C (0 < C <= 1.0).
        Used by FAA concentration time method.
    retardance : float, optional
        Kerby retardance roughness coefficient (0.02-0.80).
        Used by Kerby and Kerby-Kirpich concentration time methods.
    overland_length_km : float, optional
        Overland (sheet) flow length [km]. Used by the FAA, Kerby and
        Kerby-Kirpich methods (typically up to 0.366 km for Kerby).
    overland_slope_m_per_m : float, optional
        Average overland slope [m/m]. Used by the FAA, Kerby and Kerby-Kirpich
        methods.
    Lc_km : float, optional
        Length along main stream from outlet to the point nearest
        to catchment centroid [km]. Used by Nash Lutz and Snyder methods.
    manning_n : float, optional
        Manning's roughness coefficient for main channel.
        Typical values: 0.025-0.050 for natural streams.
        Used by Nash Lutz method.
    urban_pct : float, optional
        Percentage of urbanized area [%] (0-100).
        Used by Nash Lutz method.
    forest_pct : float, optional
        Percentage of forested area [%] (0-100).
        Used by Nash Lutz method.

    Attributes
    ----------
    width_km : float
        Average watershed width = area / length [km].
    relief_m : float
        Relief = elevation_max - elevation_min [m].

    Examples
    --------
    Create from dictionary (e.g., API response):

    >>> data = {
    ...     "area_km2": 45.3,
    ...     "perimeter_km": 32.1,
    ...     "length_km": 12.5,
    ...     "elevation_min_m": 150.0,
    ...     "elevation_max_m": 520.0,
    ...     "cn": 72,
    ...     "source": "Hydrograf"
    ... }
    >>> params = WatershedParameters.from_dict(data)
    >>> print(f"Area: {params.area_km2} km², Relief: {params.relief_m} m")
    Area: 45.3 km², Relief: 370.0 m

    Convert to Hydrolog objects:

    >>> geom = params.to_geometry()
    >>> terrain = params.to_terrain()

    Calculate concentration time:

    >>> tc_min = params.calculate_tc(method="kirpich")
    """

    # Required parameters
    area_km2: float
    perimeter_km: float
    length_km: float
    elevation_min_m: float
    elevation_max_m: float

    # Optional parameters
    name: str | None = None
    elevation_mean_m: float | None = None
    mean_slope_m_per_m: float | None = None
    channel_length_km: float | None = None
    channel_slope_m_per_m: float | None = None
    cn: int | None = None
    source: str | None = None
    crs: str | None = None

    # FAA concentration time
    runoff_coeff: float | None = None

    # Kerby / Kerby-Kirpich concentration time
    retardance: float | None = None
    overland_length_km: float | None = None
    overland_slope_m_per_m: float | None = None

    # Nash Lutz / Snyder unit hydrograph
    Lc_km: float | None = None
    manning_n: float | None = None
    urban_pct: float | None = None
    forest_pct: float | None = None

    def __post_init__(self) -> None:
        """Validate parameters after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate parameter values."""
        if self.area_km2 <= 0:
            raise InvalidParameterError(
                f"area_km2 must be positive, got {self.area_km2}"
            )
        if self.perimeter_km <= 0:
            raise InvalidParameterError(
                f"perimeter_km must be positive, got {self.perimeter_km}"
            )
        if self.length_km <= 0:
            raise InvalidParameterError(
                f"length_km must be positive, got {self.length_km}"
            )
        if self.elevation_max_m <= self.elevation_min_m:
            raise InvalidParameterError(
                f"elevation_max_m ({self.elevation_max_m}) must be greater than "
                f"elevation_min_m ({self.elevation_min_m})"
            )
        if self.cn is not None and not 0 <= self.cn <= 100:
            raise InvalidParameterError(f"cn must be 0-100, got {self.cn}")
        if self.mean_slope_m_per_m is not None and self.mean_slope_m_per_m < 0:
            raise InvalidParameterError(
                f"mean_slope_m_per_m must be non-negative, got "
                f"{self.mean_slope_m_per_m}"
            )
        if self.channel_length_km is not None and self.channel_length_km <= 0:
            raise InvalidParameterError(
                f"channel_length_km must be positive, got {self.channel_length_km}"
            )
        if self.channel_slope_m_per_m is not None and self.channel_slope_m_per_m < 0:
            raise InvalidParameterError(
                f"channel_slope_m_per_m must be non-negative, got "
                f"{self.channel_slope_m_per_m}"
            )
        if self.runoff_coeff is not None and (
            self.runoff_coeff <= 0 or self.runoff_coeff > 1.0
        ):
            raise InvalidParameterError(
                f"runoff_coeff must be in range (0, 1.0], got {self.runoff_coeff}"
            )
        if self.retardance is not None and self.retardance <= 0:
            raise InvalidParameterError(
                f"retardance must be positive, got {self.retardance}"
            )
        if self.overland_length_km is not None and self.overland_length_km <= 0:
            raise InvalidParameterError(
                f"overland_length_km must be positive, got {self.overland_length_km}"
            )
        if self.overland_slope_m_per_m is not None and self.overland_slope_m_per_m < 0:
            raise InvalidParameterError(
                f"overland_slope_m_per_m must be non-negative, "
                f"got {self.overland_slope_m_per_m}"
            )
        if self.Lc_km is not None and self.Lc_km <= 0:
            raise InvalidParameterError(f"Lc_km must be positive, got {self.Lc_km}")
        if self.manning_n is not None and self.manning_n <= 0:
            raise InvalidParameterError(
                f"manning_n must be positive, got {self.manning_n}"
            )
        if self.urban_pct is not None and not 0 <= self.urban_pct <= 100:
            raise InvalidParameterError(
                f"urban_pct must be 0-100, got {self.urban_pct}"
            )
        if self.forest_pct is not None and not 0 <= self.forest_pct <= 100:
            raise InvalidParameterError(
                f"forest_pct must be 0-100, got {self.forest_pct}"
            )

    @property
    def width_km(self) -> float:
        """
        Average watershed width [km].

        Calculated as W = A / L.
        """
        return self.area_km2 / self.length_km

    @property
    def relief_m(self) -> float:
        """
        Relief (elevation difference) [m].

        Calculated as H = elevation_max - elevation_min.
        """
        return self.elevation_max_m - self.elevation_min_m

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatershedParameters:
        """
        Create WatershedParameters from a dictionary.

        This method is designed for easy integration with JSON APIs.
        Unknown keys in the dictionary are ignored.

        Parameters
        ----------
        data : dict
            Dictionary with watershed parameters. Required keys:
            area_km2, perimeter_km, length_km, elevation_min_m, elevation_max_m.
            Optional keys: name, elevation_mean_m, mean_slope_m_per_m,
            channel_length_km, channel_slope_m_per_m, cn, source, crs,
            runoff_coeff, retardance, overland_length_km,
            overland_slope_m_per_m, Lc_km, manning_n, urban_pct, forest_pct.

        Returns
        -------
        WatershedParameters
            New instance with values from dictionary.

        Raises
        ------
        KeyError
            If required keys are missing.
        InvalidParameterError
            If parameter values are invalid.

        Examples
        --------
        >>> data = {"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 12.0,
        ...         "elevation_min_m": 150.0, "elevation_max_m": 520.0}
        >>> params = WatershedParameters.from_dict(data)
        """
        # Extract only known fields (this also ignores a top-level "schema"
        # marker such as "hydrolog-catchment/1" written by catalog tooling)
        known_fields = {
            "area_km2",
            "perimeter_km",
            "length_km",
            "elevation_min_m",
            "elevation_max_m",
            "name",
            "elevation_mean_m",
            "mean_slope_m_per_m",
            "channel_length_km",
            "channel_slope_m_per_m",
            "cn",
            "source",
            "crs",
            "runoff_coeff",
            "retardance",
            "overland_length_km",
            "overland_slope_m_per_m",
            "Lc_km",
            "manning_n",
            "urban_pct",
            "forest_pct",
        }
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)

    @classmethod
    def from_json(cls, json_str: str) -> WatershedParameters:
        """
        Create WatershedParameters from a JSON string.

        Parameters
        ----------
        json_str : str
            JSON string with watershed parameters.

        Returns
        -------
        WatershedParameters
            New instance with values from JSON.

        Examples
        --------
        >>> json_str = '{"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 12.0, '
        >>> json_str += '"elevation_min_m": 150.0, "elevation_max_m": 520.0}'
        >>> params = WatershedParameters.from_json(json_str)
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """
        Export to dictionary.

        Returns
        -------
        dict
            Dictionary with all parameters. None values are excluded.

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0)
        >>> d = params.to_dict()
        >>> print(d["area_km2"])
        45.0
        """
        result = asdict(self)
        # Remove None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}

    def to_json(self, indent: int | None = None) -> str:
        """
        Export to JSON string.

        Parameters
        ----------
        indent : int, optional
            Indentation level for pretty printing.

        Returns
        -------
        str
            JSON string with parameters.

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0)
        >>> json_str = params.to_json(indent=2)
        """
        return json.dumps(self.to_dict(), indent=indent)

    def to_geometry(self) -> WatershedGeometry:
        """
        Convert to WatershedGeometry object.

        Returns
        -------
        WatershedGeometry
            Geometry object for shape indicator calculations.

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0)
        >>> geom = params.to_geometry()
        >>> indicators = geom.get_shape_indicators()
        """
        from hydrolog.morphometry.geometric import WatershedGeometry

        return WatershedGeometry(
            area_km2=self.area_km2,
            perimeter_km=self.perimeter_km,
            length_km=self.length_km,
        )

    def to_terrain(self) -> TerrainAnalysis:
        """
        Convert to TerrainAnalysis object.

        Returns
        -------
        TerrainAnalysis
            Terrain analysis object for slope calculations.

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0)
        >>> terrain = params.to_terrain()
        >>> slopes = terrain.get_slope_parameters()
        """
        from hydrolog.morphometry.terrain import TerrainAnalysis

        return TerrainAnalysis(
            elevation_min_m=self.elevation_min_m,
            elevation_max_m=self.elevation_max_m,
            length_km=self.length_km,
            elevation_mean_m=self.elevation_mean_m,
            channel_length_km=self.channel_length_km,
        )

    def _check_tc_method(self, method: str) -> None:
        """Raise if ``method`` is unknown or a field it cannot do without is missing."""
        if method not in TC_METHODS:
            raise InvalidParameterError(
                f"Unknown method: '{method}'. Use 'kirpich', 'nrcs', "
                f"'giandotti', 'faa', 'kerby', or 'kerby_kirpich'.",
                details={
                    "option": "method",
                    "reason": "choice",
                    "allowed": list(TC_METHODS),
                    "value": method,
                },
            )
        missing = [
            name
            for name in _TC_REQUIRED_FIELDS.get(method, ())
            if getattr(self, name) is None
        ]
        if missing:
            names = ", ".join(missing)
            shown = "CN" if missing == ["cn"] else names
            plural = len(missing) > 1
            raise InvalidParameterError(
                f"{shown} {'are' if plural else 'is'} required for "
                f"{_TC_METHOD_LABELS[method]} method. "
                f"Set the {names} parameter{'s' if plural else ''}.",
                details={
                    "reason": "missing_field",
                    "method": method,
                    "missing": missing,
                },
                hint=_TC_MISSING_HINTS.get(method),
            )

    def tc_parameters(self, method: str = "kirpich") -> dict[str, float]:
        """
        Arguments of a concentration time formula derived from the fields.

        These are exactly the keyword arguments :meth:`calculate_tc` passes to
        the static method of :class:`hydrolog.time.ConcentrationTime` named like
        ``method``, so ``ConcentrationTime.<method>(**params.tc_parameters(method))``
        equals ``params.calculate_tc(method)``. They show what a concentration
        time was computed from; the selection rules are described in the notes of
        :meth:`calculate_tc`.

        Parameters
        ----------
        method : str, optional
            Calculation method: "kirpich", "nrcs", "giandotti", "faa",
            "kerby", or "kerby_kirpich". Default is "kirpich".

        Returns
        -------
        dict of str to float
            Argument name and value, in the units of the formula (km, m/m, m).
            For example ``{"length_km": 10.0, "slope_m_per_m": 0.02}`` for
            "kirpich".

        Raises
        ------
        InvalidParameterError
            If the method is unknown (``details["reason"] == "choice"``) or a
            parameter the method requires is missing (``details["reason"] ==
            "missing_field"``, ``details["missing"]`` lists all of them).

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0,
        ...     mean_slope_m_per_m=0.025, channel_length_km=10.0,
        ...     channel_slope_m_per_m=0.02)
        >>> params.tc_parameters("kirpich")
        {'length_km': 10.0, 'slope_m_per_m': 0.02}
        """
        self._check_tc_method(method)
        if method == "kerby_kirpich":
            return {
                "overland_length_km": cast(float, self.overland_length_km),
                "overland_slope_m_per_m": cast(float, self.overland_slope_m_per_m),
                "retardance": cast(float, self.retardance),
                "channel_length_km": cast(float, self.channel_length_km),
                "channel_slope_m_per_m": cast(float, self.channel_slope_m_per_m),
            }
        if method in ("faa", "kerby"):
            # Overland flow formulas: the overland flow path, not the channel
            overland = {
                "length_km": cast(float, self.overland_length_km),
                "slope_m_per_m": cast(float, self.overland_slope_m_per_m),
            }
            if method == "faa":
                return {**overland, "runoff_coeff": cast(float, self.runoff_coeff)}
            return {**overland, "retardance": cast(float, self.retardance)}

        length_km = self.channel_length_km or self.length_km
        if method == "giandotti":
            # elevation_diff_m = mean elevation - outlet elevation
            elevation_mean = (
                self.elevation_mean_m
                if self.elevation_mean_m is not None
                else (self.elevation_min_m + self.elevation_max_m) / 2
            )
            return {
                "area_km2": self.area_km2,
                "length_km": length_km,
                "elevation_diff_m": elevation_mean - self.elevation_min_m,
            }

        # Kirpich takes the slope of the channel first; NRCS (TR-55) takes the
        # average land slope of the watershed first
        slopes = (
            (self.mean_slope_m_per_m, self.channel_slope_m_per_m)
            if method == "nrcs"
            else (self.channel_slope_m_per_m, self.mean_slope_m_per_m)
        )
        slope_m_per_m = next((value for value in slopes if value is not None), None)
        if slope_m_per_m is None:
            # Calculate from relief and length
            slope_m_per_m = self.relief_m / (length_km * 1000)
        parameters = {"length_km": length_km, "slope_m_per_m": slope_m_per_m}
        if method == "nrcs":
            parameters["cn"] = cast(float, self.cn)
        return parameters

    def calculate_tc(self, method: str = "kirpich") -> float:
        """
        Calculate concentration time using specified method.

        Parameters
        ----------
        method : str, optional
            Calculation method: "kirpich", "nrcs", "giandotti", "faa",
            "kerby", or "kerby_kirpich". Default is "kirpich".

        Returns
        -------
        float
            Concentration time [min].

        Raises
        ------
        InvalidParameterError
            If the method is unknown (``details["reason"] == "choice"``), a
            parameter the method requires is missing (``details["reason"] ==
            "missing_field"``, ``details["missing"]`` lists all of them) or a
            value is rejected by the formula. It is also a ``ValueError``, so
            code that caught the ``ValueError`` of earlier versions keeps
            working.

        Notes
        -----
        The arguments of the formula come from the fields as follows
        (:meth:`tc_parameters` returns them):

        * "kirpich": the length is ``channel_length_km`` if available, otherwise
          ``length_km``; the slope is ``channel_slope_m_per_m`` if available,
          otherwise ``mean_slope_m_per_m``, otherwise it is calculated from
          relief and length.
        * "nrcs": ``cn`` must be set. The length is chosen as for "kirpich". The
          slope is the average land slope Y of the watershed, not the slope of
          the flow path (USDA-NRCS 1986, TR-55, chapter 3; USDA-NRCS 2010, NEH
          Part 630, chapter 15): ``mean_slope_m_per_m`` if available, otherwise
          ``channel_slope_m_per_m``, otherwise relief over length.
        * "giandotti": the length is chosen as for "kirpich"; the elevation
          difference is ``elevation_mean_m - elevation_min_m``;
          ``elevation_mean_m`` defaults to the middle of the elevation range (also
          when it is 0 m a.s.l., which is a valid mean elevation).
        * "faa" and "kerby" are overland (sheet) flow formulas (FAA 1966,
          AC 150/5320-5A, and 2013, AC 150/5320-5D; Kerby 1959). Kerby derived his
          formula for flow paths of up to 366 m (1200 ft; Roussel et al. 2005,
          TxDOT Report 0-4696-2; TxDOT Hydraulic Design Manual, chapter 4,
          section 11) and the library warns for FAA outside 0.015-3 km. They are
          fed with the overland flow length and slope, never with those of the
          channel: ``overland_length_km`` and ``overland_slope_m_per_m`` must be
          set, and ``runoff_coeff`` ("faa") or ``retardance`` ("kerby"). The
          result is the overland flow time of the watershed; for a watershed with
          a channel "kerby_kirpich" adds the channel travel time.
        * "kerby_kirpich": ``retardance``, ``overland_length_km``,
          ``overland_slope_m_per_m``, ``channel_length_km`` and
          ``channel_slope_m_per_m`` must be set.

        .. versionchanged:: 1.0.0
            "faa" and "kerby" use the overland flow length and slope and
            require them. They used the length and slope of the channel, so a
            watershed with a 10 km channel was timed as a 10 km sheet flow path,
            far outside the range of the formulas. "nrcs" takes the mean slope
            of the watershed before the slope of the channel (it was the other
            way round).

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0,
        ...     mean_slope_m_per_m=0.025)
        >>> tc = params.calculate_tc(method="kirpich")
        """
        from hydrolog.time import ConcentrationTime

        arguments = self.tc_parameters(method)
        formula = getattr(ConcentrationTime, method)
        return float(formula(**arguments))
