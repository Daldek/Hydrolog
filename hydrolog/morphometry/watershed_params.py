"""Standardized watershed parameters for integration with GIS systems."""

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from hydrolog.exceptions import InvalidParameterError


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
        Area-weighted mean slope [m/m].
    channel_length_km : float, optional
        Main channel length [km].
    channel_slope_m_per_m : float, optional
        Main channel slope [m/m].
    cn : int, optional
        SCS Curve Number (0-100).
    source : str, optional
        Data source identifier (e.g., "Hydrograf", "QGIS", "manual").
    crs : str, optional
        Coordinate reference system (e.g., "EPSG:2180").

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
    name: Optional[str] = None
    elevation_mean_m: Optional[float] = None
    mean_slope_m_per_m: Optional[float] = None
    channel_length_km: Optional[float] = None
    channel_slope_m_per_m: Optional[float] = None
    cn: Optional[int] = None
    source: Optional[str] = None
    crs: Optional[str] = None

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
                f"mean_slope_m_per_m must be non-negative, got {self.mean_slope_m_per_m}"
            )
        if self.channel_length_km is not None and self.channel_length_km <= 0:
            raise InvalidParameterError(
                f"channel_length_km must be positive, got {self.channel_length_km}"
            )
        if self.channel_slope_m_per_m is not None and self.channel_slope_m_per_m < 0:
            raise InvalidParameterError(
                f"channel_slope_m_per_m must be non-negative, got {self.channel_slope_m_per_m}"
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
    def from_dict(cls, data: dict[str, Any]) -> "WatershedParameters":
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
            channel_length_km, channel_slope_m_per_m, cn, source, crs.

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
        # Extract only known fields
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
        }
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)

    @classmethod
    def from_json(cls, json_str: str) -> "WatershedParameters":
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

    def to_json(self, indent: Optional[int] = None) -> str:
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

    def to_geometry(self) -> "WatershedGeometry":
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

    def to_terrain(self) -> "TerrainAnalysis":
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

    def calculate_tc(self, method: str = "kirpich") -> float:
        """
        Calculate concentration time using specified method.

        Parameters
        ----------
        method : str, optional
            Calculation method: "kirpich", "scs_lag", or "giandotti".
            Default is "kirpich".

        Returns
        -------
        float
            Concentration time [min].

        Raises
        ------
        InvalidParameterError
            If required parameters for the method are missing.
        ValueError
            If method is unknown.

        Notes
        -----
        For "kirpich" and "scs_lag", uses channel_length_km if available,
        otherwise falls back to length_km.

        For slope, uses channel_slope_m_per_m if available, otherwise
        mean_slope_m_per_m, otherwise calculates from relief/length.

        Examples
        --------
        >>> params = WatershedParameters(area_km2=45.0, perimeter_km=32.0,
        ...     length_km=12.0, elevation_min_m=150.0, elevation_max_m=520.0,
        ...     mean_slope_m_per_m=0.025)
        >>> tc = params.calculate_tc(method="kirpich")
        """
        from hydrolog.time import ConcentrationTime

        # Determine length to use
        length_km = self.channel_length_km or self.length_km

        # Determine slope to use
        if self.channel_slope_m_per_m is not None:
            slope_m_per_m = self.channel_slope_m_per_m
        elif self.mean_slope_m_per_m is not None:
            slope_m_per_m = self.mean_slope_m_per_m
        else:
            # Calculate from relief and length
            slope_m_per_m = self.relief_m / (length_km * 1000)

        if method == "kirpich":
            return ConcentrationTime.kirpich(
                length_km=length_km,
                slope_m_per_m=slope_m_per_m,
            )
        elif method == "scs_lag":
            if self.cn is None:
                raise InvalidParameterError(
                    "CN is required for SCS Lag method. Set cn parameter."
                )
            return ConcentrationTime.scs_lag(
                length_km=length_km,
                slope_m_per_m=slope_m_per_m,
                cn=self.cn,
            )
        elif method == "giandotti":
            # elevation_diff_m = mean elevation - outlet elevation
            elevation_mean = self.elevation_mean_m or (
                (self.elevation_min_m + self.elevation_max_m) / 2
            )
            elevation_diff_m = elevation_mean - self.elevation_min_m
            return ConcentrationTime.giandotti(
                area_km2=self.area_km2,
                length_km=length_km,
                elevation_diff_m=elevation_diff_m,
            )
        else:
            raise ValueError(
                f"Unknown method: '{method}'. Use 'kirpich', 'scs_lag', or 'giandotti'."
            )
