"""Standardized watershed parameters for integration with GIS systems."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, cast

from hydrolog._ranges import TC_INPUTS, typical_ranges, warn_if_outside
from hydrolog._warnings import typical_range_fields
from hydrolog.exceptions import InvalidParameterError

if TYPE_CHECKING:
    from hydrolog.morphometry.geometric import WatershedGeometry
    from hydrolog.morphometry.terrain import TerrainAnalysis

TC_METHODS = ("kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich")
"""The methods of :meth:`WatershedParameters.calculate_tc`."""

# Fields that a time of concentration method cannot do without and that have no
# substitute, in the order they are reported. FAA and Kerby are overland flow
# formulas: they get the overland flow length and slope, never the channel's.
# Kirpich, NRCS and Giandotti take what they can from several fields (see
# WatershedParameters._missing_tc_fields).
_TC_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
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
    "kirpich": "Kirpich",
    "nrcs": "NRCS",
    "giandotti": "Giandotti",
    "faa": "FAA",
    "kerby": "Kerby",
    "kerby_kirpich": "Kerby-Kirpich",
}

# The slopes a method takes, first choice first; without them the slope is the
# relief over the length
_TC_SLOPES: dict[str, tuple[str, ...]] = {
    method: TC_INPUTS[method]["slope_m_per_m"] for method in ("kirpich", "nrcs")
}

# The lengths Kirpich, NRCS and Giandotti take, first choice first
_TC_LENGTHS = TC_INPUTS["kirpich"]["length_km"]

_OVERLAND_HINT = (
    "FAA and Kerby time the overland flow, so they need the overland flow length "
    "and slope of the watershed (overland_length_km, overland_slope_m_per_m), not "
    "those of the channel; for a watershed with a channel use kerby_kirpich or "
    "kirpich."
)
_TC_MISSING_HINTS: dict[str, str] = {"faa": _OVERLAND_HINT, "kerby": _OVERLAND_HINT}

# How a missing field of Kirpich, NRCS and Giandotti can be replaced
_SUBSTITUTE_HINTS: dict[str, str] = {
    "channel_length_km": "The length is channel_length_km, else length_km.",
    "channel_slope_m_per_m": (
        "The slope is channel_slope_m_per_m, else mean_slope_m_per_m, else the "
        "relief (elevation_max_m - elevation_min_m) over the length."
    ),
    "mean_slope_m_per_m": (
        "The slope is mean_slope_m_per_m, else channel_slope_m_per_m, else the "
        "relief (elevation_max_m - elevation_min_m) over the length."
    ),
    "elevation_mean_m": (
        "The mean elevation is elevation_mean_m, else the middle of "
        "elevation_min_m and elevation_max_m."
    ),
}

# Field checks of WatershedParameters, in the order they run
_POSITIVE_FIELDS = (
    "area_km2",
    "perimeter_km",
    "length_km",
    "channel_length_km",
    "retardance",
    "overland_length_km",
    "Lc_km",
    "manning_n",
)
_NON_NEGATIVE_FIELDS = (
    "mean_slope_m_per_m",
    "channel_slope_m_per_m",
    "overland_slope_m_per_m",
)
_PERCENT_FIELDS = ("cn", "urban_pct", "forest_pct")


def _field_error(
    name: str, message: str, reason: str, **details: object
) -> InvalidParameterError:
    """Return the error of the field ``name`` (``details.option``)."""
    return InvalidParameterError(
        message, details={"option": name, "reason": reason, **details}
    )


def _missing_error(
    missing: list[str], message: str, hint: str | None = None, **details: object
) -> InvalidParameterError:
    """Return the error of missing fields: ``details.option`` is the first one."""
    return InvalidParameterError(
        message,
        details={
            "option": missing[0],
            "reason": "missing_field",
            **details,
            "missing": missing,
        },
        hint=hint,
    )


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
        Watershed area [km²]. Must be positive. The only required field: a
        calculation that needs another field that is not set raises
        ``InvalidParameterError`` with ``details.reason == "missing_field"`` and
        ``details.option`` the field.
    perimeter_km : float, optional
        Watershed perimeter [km]. Must be positive. Used by the shape indicators
        (:meth:`to_geometry`).
    length_km : float, optional
        Watershed length - distance from outlet to most distant point [km].
        Must be positive. Used by the shape indicators, the terrain analysis and,
        without ``channel_length_km``, by the Kirpich, NRCS and Giandotti
        concentration times.
    elevation_min_m : float, optional
        Minimum elevation at outlet [m a.s.l.].
    elevation_max_m : float, optional
        Maximum elevation in watershed [m a.s.l.]. Must be greater than
        ``elevation_min_m`` when both are given.
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
        Average watershed width = area / length [km]; needs ``length_km``.
    relief_m : float
        Relief = elevation_max - elevation_min [m]; needs both elevations.

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

    # Required parameter
    area_km2: float

    # Optional parameters
    perimeter_km: float | None = None
    length_km: float | None = None
    elevation_min_m: float | None = None
    elevation_max_m: float | None = None

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
        """Validate parameter values.

        Every error names its field in ``details.option``.
        """
        for name in _POSITIVE_FIELDS:
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise _field_error(
                    name,
                    f"{name} must be positive, got {value}",
                    "exclusive_minimum",
                    exclusive_minimum=0,
                    value=value,
                )
        if (
            self.elevation_max_m is not None
            and self.elevation_min_m is not None
            and self.elevation_max_m <= self.elevation_min_m
        ):
            raise _field_error(
                "elevation_max_m",
                f"elevation_max_m ({self.elevation_max_m}) must be greater than "
                f"elevation_min_m ({self.elevation_min_m})",
                "exclusive_minimum",
                exclusive_minimum=self.elevation_min_m,
                value=self.elevation_max_m,
            )
        for name in _NON_NEGATIVE_FIELDS:
            value = getattr(self, name)
            if value is not None and value < 0:
                raise _field_error(
                    name,
                    f"{name} must be non-negative, got {value}",
                    "minimum",
                    minimum=0,
                    value=value,
                )
        for name in _PERCENT_FIELDS:
            value = getattr(self, name)
            if value is not None and not 0 <= value <= 100:
                raise _field_error(
                    name,
                    f"{name} must be 0-100, got {value}",
                    "range",
                    minimum=0,
                    maximum=100,
                    value=value,
                )
        if self.runoff_coeff is not None and not 0 < self.runoff_coeff <= 1.0:
            raise _field_error(
                "runoff_coeff",
                f"runoff_coeff must be in range (0, 1.0], got {self.runoff_coeff}",
                "range",
                exclusive_minimum=0,
                maximum=1.0,
                value=self.runoff_coeff,
            )

    def _require(self, *names: str, needed_for: str) -> None:
        """Raise ``missing_field`` if one of the fields ``names`` is not set."""
        missing = [name for name in names if getattr(self, name) is None]
        if missing:
            plural = len(missing) > 1
            raise _missing_error(
                missing,
                f"{', '.join(missing)} {'are' if plural else 'is'} required for "
                f"{needed_for}, and the watershed has no value",
                hint=f"Add {', '.join(missing)} to the watershed parameters.",
            )

    @property
    def width_km(self) -> float:
        """
        Average watershed width [km].

        Calculated as W = A / L.

        Raises
        ------
        InvalidParameterError
            Without ``length_km`` (``details.reason == "missing_field"``).
        """
        self._require("length_km", needed_for="the width")
        return self.area_km2 / cast(float, self.length_km)

    @property
    def relief_m(self) -> float:
        """
        Relief (elevation difference) [m].

        Calculated as H = elevation_max - elevation_min.

        Raises
        ------
        InvalidParameterError
            Without ``elevation_min_m`` or ``elevation_max_m``
            (``details.reason == "missing_field"``).
        """
        self._require("elevation_min_m", "elevation_max_m", needed_for="the relief")
        return cast(float, self.elevation_max_m) - cast(float, self.elevation_min_m)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatershedParameters:
        """
        Create WatershedParameters from a dictionary.

        This method is designed for easy integration with JSON APIs.
        Unknown keys in the dictionary are ignored.

        Parameters
        ----------
        data : dict
            Dictionary with watershed parameters. Required key: area_km2.
            Optional keys: perimeter_km, length_km, elevation_min_m,
            elevation_max_m, name, elevation_mean_m, mean_slope_m_per_m,
            channel_length_km, channel_slope_m_per_m, cn, source, crs,
            runoff_coeff, retardance, overland_length_km,
            overland_slope_m_per_m, Lc_km, manning_n, urban_pct, forest_pct.

        Returns
        -------
        WatershedParameters
            New instance with values from dictionary.

        Raises
        ------
        TypeError
            If area_km2 is missing.
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

        Raises
        ------
        InvalidParameterError
            Without ``perimeter_km`` or ``length_km``
            (``details.reason == "missing_field"``).

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0)
        >>> geom = params.to_geometry()
        >>> indicators = geom.get_shape_indicators()
        """
        from hydrolog.morphometry.geometric import WatershedGeometry

        self._require("perimeter_km", "length_km", needed_for="the shape indicators")
        return WatershedGeometry(
            area_km2=self.area_km2,
            perimeter_km=cast(float, self.perimeter_km),
            length_km=cast(float, self.length_km),
        )

    def to_terrain(self) -> TerrainAnalysis:
        """
        Convert to TerrainAnalysis object.

        Returns
        -------
        TerrainAnalysis
            Terrain analysis object for slope calculations.

        Raises
        ------
        InvalidParameterError
            Without ``elevation_min_m``, ``elevation_max_m`` or ``length_km``
            (``details.reason == "missing_field"``).

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0)
        >>> terrain = params.to_terrain()
        >>> slopes = terrain.get_slope_parameters()
        """
        from hydrolog.morphometry.terrain import TerrainAnalysis

        self._require(
            "elevation_min_m",
            "elevation_max_m",
            "length_km",
            needed_for="the terrain analysis",
        )
        return TerrainAnalysis(
            elevation_min_m=cast(float, self.elevation_min_m),
            elevation_max_m=cast(float, self.elevation_max_m),
            length_km=cast(float, self.length_km),
            elevation_mean_m=self.elevation_mean_m,
            channel_length_km=self.channel_length_km,
        )

    def _missing_tc_fields(self, method: str) -> list[str]:
        """Fields that ``method`` needs and the watershed does not have.

        A field that has a substitute (the length, the slope, the mean elevation
        of Kirpich, NRCS and Giandotti) is missing only when the substitutes are
        missing too; the first choice is reported.
        """
        if method in _TC_REQUIRED_FIELDS:
            return [
                name
                for name in _TC_REQUIRED_FIELDS[method]
                if getattr(self, name) is None
            ]
        missing = []
        if all(getattr(self, name) is None for name in _TC_LENGTHS):
            missing.append(_TC_LENGTHS[0])
        if method in _TC_SLOPES:
            relief = (
                self.elevation_min_m is not None and self.elevation_max_m is not None
            )
            slopes = _TC_SLOPES[method]
            if not relief and all(getattr(self, name) is None for name in slopes):
                missing.append(slopes[0])
        if method == "nrcs" and self.cn is None:
            missing.append("cn")
        if method == "giandotti":
            if self.elevation_min_m is None:
                missing.append("elevation_min_m")
            if self.elevation_mean_m is None and self.elevation_max_m is None:
                missing.append("elevation_mean_m")
        return missing

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
        missing = self._missing_tc_fields(method)
        if missing:
            names = ", ".join(missing)
            shown = "CN" if missing == ["cn"] else names
            plural = len(missing) > 1
            substitutes = [
                _SUBSTITUTE_HINTS[name]
                for name in missing
                if name in _SUBSTITUTE_HINTS and method not in _TC_REQUIRED_FIELDS
            ]
            raise _missing_error(
                missing,
                f"{shown} {'are' if plural else 'is'} required for "
                f"{_TC_METHOD_LABELS[method]} method. "
                f"Set the {names} parameter{'s' if plural else ''}.",
                hint=" ".join(substitutes) or _TC_MISSING_HINTS.get(method),
                method=method,
            )

    def _tc_inputs(self, method: str) -> tuple[dict[str, float], dict[str, str]]:
        """Arguments of the formula of ``method`` and the field each comes from.

        A value derived from several fields is attributed to the one that is not
        shared by the alternatives: ``elevation_max_m`` for a slope from the
        relief and for the elevation difference from the middle of the elevation
        range.
        """
        self._check_tc_method(method)
        if method == "kerby_kirpich":
            names = _TC_REQUIRED_FIELDS[method]
            return (
                {name: cast(float, getattr(self, name)) for name in names},
                {name: name for name in names},
            )
        if method in ("faa", "kerby"):
            # Overland flow formulas: the overland flow path, not the channel (the
            # area is not an argument: calculate_tc checks it)
            fields = {
                name: sources[0]
                for name, sources in TC_INPUTS[method].items()
                if name != "area_km2"
            }
            return (
                {
                    name: cast(float, getattr(self, field))
                    for name, field in fields.items()
                },
                fields,
            )

        length_field = next(
            name for name in _TC_LENGTHS if getattr(self, name) is not None
        )
        length_km = cast(float, getattr(self, length_field))
        if method == "giandotti":
            # elevation_diff_m = mean elevation - outlet elevation
            outlet = cast(float, self.elevation_min_m)
            if self.elevation_mean_m is not None:
                mean_field, elevation_mean = "elevation_mean_m", self.elevation_mean_m
            else:
                mean_field = "elevation_max_m"
                elevation_mean = (outlet + cast(float, self.elevation_max_m)) / 2
            return (
                {
                    "area_km2": self.area_km2,
                    "length_km": length_km,
                    "elevation_diff_m": elevation_mean - outlet,
                },
                {
                    "area_km2": "area_km2",
                    "length_km": length_field,
                    "elevation_diff_m": mean_field,
                },
            )

        # Kirpich takes the slope of the channel first; NRCS (TR-55) takes the
        # average land slope of the watershed first
        slope_field = next(
            (name for name in _TC_SLOPES[method] if getattr(self, name) is not None),
            None,
        )
        if slope_field is None:
            # Calculate from relief and length
            slope_field = "elevation_max_m"
            slope_m_per_m = self.relief_m / (length_km * 1000)
        else:
            slope_m_per_m = cast(float, getattr(self, slope_field))
        arguments = {"length_km": length_km, "slope_m_per_m": slope_m_per_m}
        fields = {"length_km": length_field, "slope_m_per_m": slope_field}
        if method == "nrcs":
            arguments["cn"] = cast(float, self.cn)
            fields["cn"] = "cn"
        return arguments, fields

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
            "missing_field"``, ``details["option"]`` the first of them,
            ``details["missing"]`` all of them).

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0,
        ...     mean_slope_m_per_m=0.025, channel_length_km=10.0,
        ...     channel_slope_m_per_m=0.02)
        >>> params.tc_parameters("kirpich")
        {'length_km': 10.0, 'slope_m_per_m': 0.02}
        """
        return self._tc_inputs(method)[0]

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
            "missing_field"``, ``details["option"]`` the first of them,
            ``details["missing"]`` all of them) or a value is rejected by the
            formula (``details["option"]`` the field it came from). It is also a
            ``ValueError``, so code that caught the ``ValueError`` of earlier
            versions keeps working.

        Warns
        -----
        OutsideTypicalRange
            For an argument outside the typical range of the formula, and for
            "kirpich", "nrcs", "kerby" and "kerby_kirpich" an area outside the
            areas of the data of the method (parameter ``area_km2``); its
            ``field`` is the field the value came from. The ranges and their
            sources: :data:`hydrolog._ranges.TYPICAL_RANGES`.

        Notes
        -----
        The arguments of the formula come from the fields as follows
        (:meth:`tc_parameters` returns them):

        * "kirpich": the length is ``channel_length_km`` if available, otherwise
          ``length_km``; the slope is ``channel_slope_m_per_m`` if available,
          otherwise ``mean_slope_m_per_m``, otherwise it is calculated from
          relief and length (``elevation_min_m`` and ``elevation_max_m``).
        * "nrcs": ``cn`` must be set. The length is chosen as for "kirpich". The
          slope is the average land slope Y of the watershed, not the slope of
          the flow path (USDA-NRCS 1986, TR-55, chapter 3; USDA-NRCS 2010, NEH
          Part 630, chapter 15): ``mean_slope_m_per_m`` if available, otherwise
          ``channel_slope_m_per_m``, otherwise relief over length.
        * "giandotti": the length is chosen as for "kirpich"; the elevation
          difference is ``elevation_mean_m - elevation_min_m``;
          ``elevation_mean_m`` defaults to the middle of the elevation range (also
          when it is 0 m a.s.l., which is a valid mean elevation), so it needs
          ``elevation_min_m`` and ``elevation_mean_m`` or ``elevation_max_m``.
        * "faa" and "kerby" are overland (sheet) flow formulas (FAA 1966,
          AC 150/5320-5A, and 2013, AC 150/5320-5D; Kerby 1959). Kerby derived his
          formula for flow paths of up to 366 m (1200 ft; Roussel et al. 2005,
          TxDOT Report 0-4696-2; TxDOT Hydraulic Design Manual, chapter 4,
          section 11). They are fed with the overland flow length and slope,
          never with those of the channel: ``overland_length_km`` and
          ``overland_slope_m_per_m`` must be set, and ``runoff_coeff`` ("faa") or
          ``retardance`` ("kerby"). The result is the overland flow time of the
          watershed; for a watershed with a channel "kerby_kirpich" adds the
          channel travel time.
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

        arguments, fields = self._tc_inputs(method)
        formula = getattr(ConcentrationTime, method)
        with typical_range_fields(fields):
            # The area, an argument of Giandotti's formula only, against the data
            # of the other methods
            if "area_km2" not in arguments and any(
                checked.parameter == "area_km2" for checked in typical_ranges(method)
            ):
                warn_if_outside(method, "area_km2", self.area_km2)
            try:
                return float(formula(**arguments))
            except InvalidParameterError as exc:
                parameter = exc.details.get("option")
                field = fields.get(str(parameter), parameter)
                if field == parameter:
                    raise
                raise InvalidParameterError(
                    f"{exc} ({parameter} is {field} of the watershed)",
                    details={**exc.details, "option": field, "parameter": parameter},
                    hint=exc.hint,
                ) from exc
