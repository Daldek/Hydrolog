"""Standardized watershed parameters for integration with GIS systems."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, cast

from hydrolog._ranges import NASH_INPUTS, TC_INPUTS, typical_ranges, warn_if_outside
from hydrolog._warnings import typical_range_fields
from hydrolog.exceptions import InvalidParameterError

if TYPE_CHECKING:
    from hydrolog.morphometry.geometric import WatershedGeometry
    from hydrolog.morphometry.terrain import TerrainAnalysis

TC_METHODS = ("kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich")
"""The methods of :meth:`WatershedParameters.calculate_tc`."""

NASH_ESTIMATIONS = ("lutz",)
"""The estimations of Nash's n and K of :meth:`WatershedParameters.nash_parameters`."""

# The fields of each time of concentration method, in the order they are reported
# when missing: the fields TC_INPUTS names for the arguments of its formula, which its
# source defines, without substitutes (the area is always set). FAA and Kerby are
# overland flow formulas: they get the overland flow length and slope, never the
# channel's.
_TC_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "kirpich": ("flow_path_length_km", "flow_path_slope_m_per_m"),
    "nrcs": ("flow_path_length_km", "mean_slope_m_per_m", "cn"),
    "giandotti": ("channel_length_km", "elevation_min_m", "elevation_mean_m"),
    "faa": ("runoff_coeff", "overland_length_km", "overland_slope_m_per_m"),
    "kerby": ("retardance", "overland_length_km", "overland_slope_m_per_m"),
    "kerby_kirpich": (
        "retardance",
        "overland_length_km",
        "overland_slope_m_per_m",
        "flow_path_length_km",
        "flow_path_slope_m_per_m",
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

_OVERLAND_HINT = (
    "FAA and Kerby time the overland flow, so they need the overland flow length "
    "and slope of the watershed (overland_length_km, overland_slope_m_per_m), not "
    "those of the channel; for a watershed with a channel use kerby_kirpich or "
    "kirpich."
)
_TC_MISSING_HINTS: dict[str, str] = {"faa": _OVERLAND_HINT, "kerby": _OVERLAND_HINT}

_FLOW_PATH_FIELDS = ("flow_path_length_km", "flow_path_slope_m_per_m")
_FLOW_PATH_HINT = (
    "The longest flow path runs from the hydraulically most distant point of the "
    "watershed (usually on the divide, possibly on a ridge inside the watershed) to "
    "the outlet: flow_path_length_km is its length [km], flow_path_slope_m_per_m the "
    "elevation of that point minus the outlet elevation, over that length [m/m]."
)

# The fields each estimation of Nash's n and K needs, in the order they are reported
# when missing; the others it reads, the shares of urban and forest areas, are 0 when
# the watershed has none (by the argument of the estimating constructor)
_NASH_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "lutz": ("flow_path_length_km", "Lc_km", "flow_path_slope_m_per_m", "manning_n"),
}
_NASH_DEFAULTS: dict[str, float] = {"urban_pct": 0.0, "forest_pct": 0.0}
_NASH_METHOD_LABELS = {"lutz": "the Lutz estimation of Nash's n and K"}

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
    "flow_path_length_km",
)
_NON_NEGATIVE_FIELDS = (
    "mean_slope_m_per_m",
    "channel_slope_m_per_m",
    "overland_slope_m_per_m",
    "flow_path_slope_m_per_m",
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
        Must be positive. Used by the shape indicators and the terrain analysis;
        no time of concentration method takes it.
    elevation_min_m : float, optional
        Minimum elevation at outlet [m a.s.l.].
    elevation_max_m : float, optional
        Maximum elevation in watershed [m a.s.l.]. Must be greater than
        ``elevation_min_m`` when both are given.
    name : str, optional
        Watershed name for identification.
    elevation_mean_m : float, optional
        Area-weighted mean elevation [m a.s.l.]. Giandotti's elevation difference
        is it minus ``elevation_min_m``.
    mean_slope_m_per_m : float, optional
        Area-weighted mean slope of the watershed [m/m]: the average land slope Y
        of the NRCS lag method (USDA-NRCS 2010, NEH Part 630, chapter 15), not the
        slope of a flow path.
    channel_length_km : float, optional
        Main channel length [km]: the length of Giandotti's formula.
    channel_slope_m_per_m : float, optional
        Main channel slope [m/m]. No calculation takes it: Kirpich and
        Kerby-Kirpich take the slope of the longest flow path,
        ``flow_path_slope_m_per_m``, and so does Lutz's estimation of Nash's n and K
        (:meth:`nash_parameters`), whose stream runs to the divide.
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
        Overland (sheet) flow length, from the most remote point to a defined
        channel [km]. Used by the FAA, Kerby and Kerby-Kirpich methods (typically
        up to 0.366 km for Kerby).
    overland_slope_m_per_m : float, optional
        Slope of the terrain the overland flow runs on [m/m]. Used by the FAA,
        Kerby and Kerby-Kirpich methods.
    Lc_km : float, optional
        Length along main stream from outlet to the point nearest
        to catchment centroid [km]. Lutz's Lc (:meth:`nash_parameters`).
    manning_n : float, optional
        Manning's roughness coefficient for main channel.
        Typical values: 0.025-0.050 for natural streams.
        Lutz's n_M (:meth:`nash_parameters`).
    urban_pct : float, optional
        Percentage of urbanized area [%] (0-100).
        Lutz's U (:meth:`nash_parameters`; 0 when not set).
    forest_pct : float, optional
        Percentage of forested area [%] (0-100).
        Lutz's W (:meth:`nash_parameters`; 0 when not set).
    flow_path_length_km : float, optional
        Length of the longest flow path, from the hydraulically most distant
        point of the watershed (the cell with the greatest flow distance to the
        outlet; usually on the divide, possibly on a ridge inside the watershed) to
        the outlet, along the flow [km]. Must be positive. The flow length of the
        NRCS lag method, Kirpich's length, the main channel length of
        Kerby-Kirpich (whose channel segment is this length minus
        ``overland_length_km``) and Lutz's L, the main stream from the divide
        (:meth:`nash_parameters`).
    flow_path_slope_m_per_m : float, optional
        Slope of the longest flow path [m/m]: the elevation of its head (that
        most distant point) minus the outlet elevation, over
        ``flow_path_length_km``. Kirpich's slope, the main channel slope of
        Kerby-Kirpich and Lutz's J (:meth:`nash_parameters`).

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
    ...     "flow_path_length_km": 13.4,
    ...     "flow_path_slope_m_per_m": 0.026,
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

    # Longest flow path (Kirpich, NRCS lag, Kerby-Kirpich concentration time)
    flow_path_length_km: float | None = None
    flow_path_slope_m_per_m: float | None = None

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
            overland_slope_m_per_m, Lc_km, manning_n, urban_pct, forest_pct,
            flow_path_length_km, flow_path_slope_m_per_m.

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
            "flow_path_length_km",
            "flow_path_slope_m_per_m",
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

    def _check_tc_method(self, method: str) -> None:
        """Raise if ``method`` is unknown or a field it needs is missing."""
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
            name for name in _TC_REQUIRED_FIELDS[method] if getattr(self, name) is None
        ]
        if missing:
            names = ", ".join(missing)
            shown = "CN" if missing == ["cn"] else names
            plural = len(missing) > 1
            hints = [_TC_MISSING_HINTS[method]] if method in _TC_MISSING_HINTS else []
            if any(name in _FLOW_PATH_FIELDS for name in missing):
                hints.append(_FLOW_PATH_HINT)
            raise _missing_error(
                missing,
                f"{shown} {'are' if plural else 'is'} required for "
                f"{_TC_METHOD_LABELS[method]} method. "
                f"Set the {names} parameter{'s' if plural else ''}.",
                hint=" ".join(hints) or None,
                method=method,
            )

    def _tc_inputs(self, method: str) -> tuple[dict[str, float], dict[str, str]]:
        """Arguments of the formula of ``method`` and the field each comes from.

        Each argument is the field :data:`~hydrolog._ranges.TC_INPUTS` names for
        it. Giandotti's elevation difference, the one argument made of two fields,
        is the mean elevation minus the outlet elevation and is attributed to
        ``elevation_mean_m``. The area is an argument of Giandotti's formula only;
        :meth:`calculate_tc` checks it against the data of the other methods.
        """
        self._check_tc_method(method)
        arguments: dict[str, float] = {}
        fields: dict[str, str] = {}
        for name, sources in TC_INPUTS[method].items():
            if name == "area_km2" and method != "giandotti":
                continue
            if name == "elevation_diff_m":
                mean_m, outlet_m = (
                    cast(float, getattr(self, source)) for source in sources
                )
                arguments[name] = mean_m - outlet_m
            else:
                arguments[name] = cast(float, getattr(self, sources[0]))
            fields[name] = sources[0]
        return arguments, fields

    def tc_parameters(self, method: str = "kirpich") -> dict[str, float]:
        """
        Arguments of a concentration time formula derived from the fields.

        These are exactly the keyword arguments :meth:`calculate_tc` passes to
        the static method of :class:`hydrolog.time.ConcentrationTime` named like
        ``method``, so ``ConcentrationTime.<method>(**params.tc_parameters(method))``
        equals ``params.calculate_tc(method)``. They show what a concentration
        time was computed from; the fields of each method are listed in the notes
        of :meth:`calculate_tc`.

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
        ...     channel_slope_m_per_m=0.02, flow_path_length_km=11.0,
        ...     flow_path_slope_m_per_m=0.021)
        >>> params.tc_parameters("kirpich")
        {'length_km': 11.0, 'slope_m_per_m': 0.021}
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
        Each argument of the formula is the watershed field its source defines,
        with no substitute (:data:`hydrolog._ranges.TC_INPUTS`;
        :meth:`tc_parameters` returns them): a missing field is
        ``missing_field``, whatever other fields the watershed has.

        * "kirpich": the length and the slope of the longest flow path,
          ``flow_path_length_km`` and ``flow_path_slope_m_per_m``: the length
          along the watercourse from the outlet to the most remote point on the
          divide, and the elevation of that point above the outlet over that
          length (Fang et al. 2005, TxDOT Report 0-4696-1, eq. 3.14; Mota and
          Kobiyama 2015 on Kirpich's data).
        * "nrcs": the flow length, the longest path from the hydraulically most
          distant point of the watershed to the outlet, ``flow_path_length_km``;
          the average land slope Y of the watershed, not the slope of the flow
          path, ``mean_slope_m_per_m``; and ``cn`` (USDA-NRCS 2010, NEH Part 630,
          chapter 15, eq. 15-4).
        * "giandotti": the length of the main channel, ``channel_length_km``, and
          the mean elevation of the watershed above the outlet,
          ``elevation_mean_m - elevation_min_m`` (Grimaldi et al. 2012).
        * "faa" and "kerby" are overland (sheet) flow formulas (FAA 1970,
          AC 150/5320-5B, fig. 7; Kerby 1959). Kerby derived his formula for flow
          paths of up to 366 m (1200 ft; Roussel et al. 2005, TxDOT Report
          0-4696-2; TxDOT Hydraulic Design Manual, chapter 4, section 11). They
          take the overland flow length and slope, never those of the channel:
          ``overland_length_km`` and ``overland_slope_m_per_m``, and
          ``runoff_coeff`` ("faa") or ``retardance`` ("kerby"). The result is the
          overland flow time of the watershed; for a watershed with a channel
          "kerby_kirpich" adds the channel travel time.
        * "kerby_kirpich": the overland segment, ``retardance``,
          ``overland_length_km`` and ``overland_slope_m_per_m``, and the whole
          longest flow path, ``flow_path_length_km`` and
          ``flow_path_slope_m_per_m``: its channel segment is the flow path minus
          the overland one, timed at the slope of the whole path (Roussel et al.
          2005, supplement).

        .. versionchanged:: 1.0.0
            Every method takes the fields its source defines, without
            substitutes. Kirpich and NRCS took the channel length, else the
            watershed length, and Kirpich the channel slope, else the mean slope,
            else the relief over the length (NRCS the mean slope first); they now
            take the longest flow path. Giandotti took the watershed length
            without a channel and the middle of the elevation range without a
            mean elevation. Kerby-Kirpich took the channel length and slope; it
            now takes the flow path. "faa" and "kerby" take the overland flow
            length and slope: they took the length and slope of the channel, so a
            watershed with a 10 km channel was timed as a 10 km sheet flow path,
            far outside the range of the formulas.

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0,
        ...     flow_path_length_km=13.4, flow_path_slope_m_per_m=0.026)
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

    def nash_parameters(self, method: str = "lutz") -> dict[str, float]:
        """
        Arguments of an estimation of Nash's n and K derived from the fields.

        These are exactly the keyword arguments of the estimating constructor of
        :class:`hydrolog.runoff.NashIUH` named after ``method``:
        ``NashIUH.from_lutz(**params.nash_parameters("lutz"))`` is the cascade Lutz
        estimates for the watershed, the one the ``nash_estimation`` of
        ``hydrograph generate``, ``report generate`` and the ``curve-number`` runoff
        of a network uses. Each argument is the watershed field its source defines
        for it (:data:`hydrolog._ranges.NASH_INPUTS`), with no substitute.

        Parameters
        ----------
        method : str, optional
            The estimation: "lutz" (Lutz 1984, after KZGW 2017), the default.

        Returns
        -------
        dict of str to float
            ``L_km`` (``flow_path_length_km``), ``Lc_km``, ``slope``
            (``flow_path_slope_m_per_m``), ``manning_n``, ``urban_pct`` and
            ``forest_pct`` (0 when the watershed has none) and ``area_km2``.

        Raises
        ------
        InvalidParameterError
            If the method is unknown (``details["reason"] == "choice"``), a field
            the method requires is missing (``details["reason"] ==
            "missing_field"``, ``details["option"]`` the first of them,
            ``details["missing"]`` all of them, ``details["method"]`` the method),
            ``Lc_km`` is longer than ``flow_path_length_km`` (``"maximum"`` on
            ``Lc_km``) or ``flow_path_slope_m_per_m`` is 0 (``"exclusive_minimum"``
            on it): Lutz's formula needs Lc <= L and J > 0.

        Notes
        -----
        Lutz takes the main stream from the divide to the outlet (KZGW 2017,
        annex 2, table C.2): its length L and its mean slope J are the length and
        the slope of the longest flow path, ``flow_path_length_km`` and
        ``flow_path_slope_m_per_m``, as Kirpich's are (ADR-0019, ADR-0024), not
        the channel's, which ends at the channel head. Lc is ``Lc_km``, the
        Manning coefficient of the channel n_M ``manning_n``, the urbanized and
        forested shares U and W ``urban_pct`` and ``forest_pct``.

        Examples
        --------
        >>> params = WatershedParameters(area_km2=37.22, flow_path_length_km=15.88,
        ...     flow_path_slope_m_per_m=0.0114, Lc_km=6.76, manning_n=0.035,
        ...     forest_pct=57.4, urban_pct=1.0)
        >>> params.nash_parameters("lutz")["L_km"]
        15.88
        """
        if method not in NASH_ESTIMATIONS:
            raise InvalidParameterError(
                f"Unknown estimation of Nash's n and K: '{method}'. Use 'lutz'.",
                details={
                    "option": "method",
                    "reason": "choice",
                    "allowed": list(NASH_ESTIMATIONS),
                    "value": method,
                },
            )
        missing = [
            name
            for name in _NASH_REQUIRED_FIELDS[method]
            if getattr(self, name) is None
        ]
        if missing:
            names = ", ".join(missing)
            plural = len(missing) > 1
            hints = [_FLOW_PATH_HINT] if set(missing) & set(_FLOW_PATH_FIELDS) else []
            raise _missing_error(
                missing,
                f"{names} {'are' if plural else 'is'} required for "
                f"{_NASH_METHOD_LABELS[method]}. "
                f"Set the {names} parameter{'s' if plural else ''}.",
                hint=" ".join(
                    [
                        "Lutz takes the main stream from the divide to the outlet: "
                        "its length and slope are those of the longest flow path.",
                        *hints,
                    ]
                ),
                method=method,
            )
        arguments: dict[str, float] = {}
        for name, sources in NASH_INPUTS[method].items():
            value = getattr(self, sources[0])
            arguments[name] = _NASH_DEFAULTS[name] if value is None else float(value)
        length, centroid = arguments["L_km"], arguments["Lc_km"]
        if centroid > length:
            raise _field_error(
                "Lc_km",
                f"Lc_km ({centroid:g}) cannot exceed flow_path_length_km "
                f"({length:g}): Lutz's Lc runs along the main stream, whose length "
                "is L",
                "maximum",
                maximum=length,
                value=centroid,
            )
        if arguments["slope"] <= 0:
            raise _field_error(
                "flow_path_slope_m_per_m",
                "flow_path_slope_m_per_m must be positive for Lutz's estimation, "
                f"got {arguments['slope']:g}",
                "exclusive_minimum",
                exclusive_minimum=0,
                value=arguments["slope"],
            )
        return arguments
