"""Spatial interpolation methods for precipitation data.

This module provides methods for interpolating point precipitation
measurements to areal values over a watershed.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


@dataclass
class Station:
    """
    Precipitation measurement station.

    Attributes
    ----------
    station_id : str
        Unique identifier for the station.
    x : float
        X coordinate (easting) [m or km].
    y : float
        Y coordinate (northing) [m or km].
    precipitation_mm : float
        Measured precipitation [mm].
    elevation_m : float, optional
        Station elevation [m a.s.l.].
    """

    station_id: str
    x: float
    y: float
    precipitation_mm: float
    elevation_m: Optional[float] = None


@dataclass
class ThiessenResult:
    """
    Result of Thiessen polygon interpolation.

    Attributes
    ----------
    areal_precipitation_mm : float
        Weighted average precipitation [mm].
    station_weights : dict[str, float]
        Weight (fraction of area) for each station.
    station_contributions_mm : dict[str, float]
        Precipitation contribution from each station [mm].
    """

    areal_precipitation_mm: float
    station_weights: dict[str, float]
    station_contributions_mm: dict[str, float]


@dataclass
class IDWResult:
    """
    Result of IDW interpolation.

    Attributes
    ----------
    areal_precipitation_mm : float
        Interpolated precipitation value [mm].
    station_weights : dict[str, float]
        Weight assigned to each station.
    power : float
        Power parameter used for interpolation.
    """

    areal_precipitation_mm: float
    station_weights: dict[str, float]
    power: float


@dataclass
class IsohyetResult:
    """
    Result of isohyet method interpolation.

    Attributes
    ----------
    areal_precipitation_mm : float
        Weighted average precipitation [mm].
    isohyet_values_mm : NDArray[np.float64]
        Isohyet contour values [mm].
    area_fractions : NDArray[np.float64]
        Fraction of area between isohyets.
    """

    areal_precipitation_mm: float
    isohyet_values_mm: NDArray[np.float64]
    area_fractions: NDArray[np.float64]


def thiessen_polygons(
    stations: list[Station],
    polygon_areas_km2: dict[str, float],
) -> ThiessenResult:
    """
    Calculate areal precipitation using Thiessen polygon method.

    The Thiessen method assigns weights to each station based on
    the area of its Voronoi polygon within the watershed.

    Parameters
    ----------
    stations : list[Station]
        List of precipitation stations with measurements.
    polygon_areas_km2 : dict[str, float]
        Area of each station's Thiessen polygon [km²].
        Keys are station IDs.

    Returns
    -------
    ThiessenResult
        Interpolation results with weights and contributions.

    Raises
    ------
    InvalidParameterError
        If stations list is empty or areas don't match stations.

    Notes
    -----
    The Thiessen polygon (Voronoi diagram) for each station includes
    all points closer to that station than any other. The areal
    precipitation is:

    P_areal = sum(P_i * A_i) / sum(A_i)

    where P_i is precipitation at station i and A_i is the polygon area.

    Examples
    --------
    >>> stations = [
    ...     Station("S1", 0, 0, precipitation_mm=25.0),
    ...     Station("S2", 10, 0, precipitation_mm=35.0),
    ...     Station("S3", 5, 8, precipitation_mm=30.0),
    ... ]
    >>> areas = {"S1": 15.0, "S2": 20.0, "S3": 10.0}
    >>> result = thiessen_polygons(stations, areas)
    >>> print(f"Areal P: {result.areal_precipitation_mm:.1f} mm")
    """
    if not stations:
        raise InvalidParameterError("stations list cannot be empty")

    # Validate polygon areas
    station_ids = {s.station_id for s in stations}
    area_ids = set(polygon_areas_km2.keys())

    if not area_ids.issubset(station_ids):
        missing = area_ids - station_ids
        raise InvalidParameterError(
            f"polygon_areas_km2 contains unknown station IDs: {missing}"
        )

    # Calculate total area and weights
    total_area = sum(polygon_areas_km2.values())

    if total_area <= 0:
        raise InvalidParameterError("Total polygon area must be positive")

    weights: dict[str, float] = {}
    contributions: dict[str, float] = {}
    weighted_sum = 0.0

    for station in stations:
        sid = station.station_id
        if sid in polygon_areas_km2:
            area = polygon_areas_km2[sid]
            weight = area / total_area
            weights[sid] = weight
            contribution = station.precipitation_mm * weight
            contributions[sid] = contribution
            weighted_sum += contribution

    return ThiessenResult(
        areal_precipitation_mm=weighted_sum,
        station_weights=weights,
        station_contributions_mm=contributions,
    )


def inverse_distance_weighting(
    stations: list[Station],
    target_x: float,
    target_y: float,
    power: float = 2.0,
    max_distance: Optional[float] = None,
) -> IDWResult:
    """
    Interpolate precipitation using Inverse Distance Weighting (IDW).

    IDW assigns weights inversely proportional to the distance
    raised to a power.

    Parameters
    ----------
    stations : list[Station]
        List of precipitation stations.
    target_x : float
        X coordinate of target point.
    target_y : float
        Y coordinate of target point.
    power : float, optional
        Distance power parameter, by default 2.0.
        Higher values give more weight to nearby stations.
    max_distance : float, optional
        Maximum distance to include stations. If None, all
        stations are used.

    Returns
    -------
    IDWResult
        Interpolation result with weights.

    Raises
    ------
    InvalidParameterError
        If stations list is empty or power is non-positive.

    Notes
    -----
    The IDW formula:

    P(x,y) = sum(w_i * P_i) / sum(w_i)

    where w_i = 1 / d_i^p and d_i is distance to station i.

    If target point coincides with a station, that station's
    value is returned directly.

    Examples
    --------
    >>> stations = [
    ...     Station("S1", 0, 0, precipitation_mm=25.0),
    ...     Station("S2", 10, 0, precipitation_mm=35.0),
    ... ]
    >>> result = inverse_distance_weighting(stations, 3, 0, power=2)
    >>> print(f"P at (3,0): {result.areal_precipitation_mm:.1f} mm")
    """
    if not stations:
        raise InvalidParameterError("stations list cannot be empty")

    if power <= 0:
        raise InvalidParameterError(f"power must be positive, got {power}")

    # Calculate distances
    distances: dict[str, float] = {}
    for station in stations:
        d = np.sqrt((station.x - target_x) ** 2 + (station.y - target_y) ** 2)
        distances[station.station_id] = float(d)

    # Check if target coincides with any station
    for station in stations:
        if distances[station.station_id] < 1e-10:
            return IDWResult(
                areal_precipitation_mm=station.precipitation_mm,
                station_weights={station.station_id: 1.0},
                power=power,
            )

    # Filter by max distance if specified
    valid_stations = stations
    if max_distance is not None:
        valid_stations = [
            s for s in stations if distances[s.station_id] <= max_distance
        ]
        if not valid_stations:
            raise InvalidParameterError(
                f"No stations within max_distance={max_distance}"
            )

    # Calculate weights
    weights: dict[str, float] = {}
    weight_sum = 0.0

    for station in valid_stations:
        d = distances[station.station_id]
        w = 1.0 / (d**power)
        weights[station.station_id] = w
        weight_sum += w

    # Normalize weights
    for sid in weights:
        weights[sid] /= weight_sum

    # Calculate weighted average
    weighted_sum = sum(
        weights[s.station_id] * s.precipitation_mm for s in valid_stations
    )

    return IDWResult(
        areal_precipitation_mm=weighted_sum,
        station_weights=weights,
        power=power,
    )


def areal_precipitation_idw(
    stations: list[Station],
    grid_x: NDArray[np.float64],
    grid_y: NDArray[np.float64],
    power: float = 2.0,
) -> float:
    """
    Calculate areal precipitation by averaging IDW over a grid.

    This function interpolates precipitation to each grid point
    and returns the arithmetic mean.

    Parameters
    ----------
    stations : list[Station]
        List of precipitation stations.
    grid_x : NDArray[np.float64]
        X coordinates of grid points.
    grid_y : NDArray[np.float64]
        Y coordinates of grid points (same shape as grid_x).
    power : float, optional
        IDW power parameter, by default 2.0.

    Returns
    -------
    float
        Mean areal precipitation [mm].

    Examples
    --------
    >>> import numpy as np
    >>> stations = [Station("S1", 0, 0, 25.0), Station("S2", 10, 10, 35.0)]
    >>> x = np.linspace(0, 10, 11)
    >>> y = np.linspace(0, 10, 11)
    >>> xx, yy = np.meshgrid(x, y)
    >>> P_areal = areal_precipitation_idw(stations, xx.flatten(), yy.flatten())
    """
    if len(grid_x) != len(grid_y):
        raise InvalidParameterError(
            f"grid_x and grid_y must have same length, "
            f"got {len(grid_x)} and {len(grid_y)}"
        )

    if len(grid_x) == 0:
        raise InvalidParameterError("Grid cannot be empty")

    interpolated = []
    for x, y in zip(grid_x, grid_y):
        result = inverse_distance_weighting(stations, float(x), float(y), power)
        interpolated.append(result.areal_precipitation_mm)

    return float(np.mean(interpolated))


def isohyet_method(
    isohyet_values_mm: NDArray[np.float64],
    area_fractions: NDArray[np.float64],
) -> IsohyetResult:
    """
    Calculate areal precipitation using the isohyet method.

    The isohyet method uses contour lines of equal precipitation
    (isohyets) and the areas between them to calculate weighted
    average precipitation.

    Parameters
    ----------
    isohyet_values_mm : NDArray[np.float64]
        Precipitation values at isohyet boundaries [mm].
        Array of length n representing n-1 zones.
    area_fractions : NDArray[np.float64]
        Fraction of watershed area between consecutive isohyets.
        Array of length n-1, must sum to 1.0.

    Returns
    -------
    IsohyetResult
        Interpolation results.

    Raises
    ------
    InvalidParameterError
        If arrays have incompatible lengths or fractions don't sum to 1.

    Notes
    -----
    For each zone between isohyets i and i+1, the average
    precipitation is (P_i + P_{i+1}) / 2.

    The areal precipitation is:
    P_areal = sum(((P_i + P_{i+1}) / 2) * f_i)

    where f_i is the area fraction of zone i.

    Examples
    --------
    >>> import numpy as np
    >>> isohyets = np.array([20.0, 30.0, 40.0, 50.0])  # 3 zones
    >>> fractions = np.array([0.3, 0.5, 0.2])  # Must sum to 1
    >>> result = isohyet_method(isohyets, fractions)
    >>> print(f"Areal P: {result.areal_precipitation_mm:.1f} mm")
    """
    isohyet_values_mm = np.asarray(isohyet_values_mm, dtype=np.float64)
    area_fractions = np.asarray(area_fractions, dtype=np.float64)

    if len(isohyet_values_mm) < 2:
        raise InvalidParameterError(
            f"Need at least 2 isohyet values, got {len(isohyet_values_mm)}"
        )

    expected_zones = len(isohyet_values_mm) - 1
    if len(area_fractions) != expected_zones:
        raise InvalidParameterError(
            f"Expected {expected_zones} area fractions for "
            f"{len(isohyet_values_mm)} isohyets, got {len(area_fractions)}"
        )

    fraction_sum = np.sum(area_fractions)
    if not np.isclose(fraction_sum, 1.0, rtol=1e-3):
        raise InvalidParameterError(
            f"area_fractions must sum to 1.0, got {fraction_sum:.4f}"
        )

    if np.any(area_fractions < 0):
        raise InvalidParameterError("area_fractions must be non-negative")

    # Calculate zone averages and weighted sum
    weighted_sum = 0.0
    for i in range(expected_zones):
        zone_avg = (isohyet_values_mm[i] + isohyet_values_mm[i + 1]) / 2.0
        weighted_sum += zone_avg * area_fractions[i]

    return IsohyetResult(
        areal_precipitation_mm=float(weighted_sum),
        isohyet_values_mm=isohyet_values_mm,
        area_fractions=area_fractions,
    )


def arithmetic_mean(stations: list[Station]) -> float:
    """
    Calculate simple arithmetic mean of station precipitation.

    This is the simplest method, appropriate when stations are
    uniformly distributed and topography is relatively flat.

    Parameters
    ----------
    stations : list[Station]
        List of precipitation stations.

    Returns
    -------
    float
        Arithmetic mean precipitation [mm].

    Raises
    ------
    InvalidParameterError
        If stations list is empty.

    Examples
    --------
    >>> stations = [
    ...     Station("S1", 0, 0, 25.0),
    ...     Station("S2", 10, 0, 35.0),
    ...     Station("S3", 5, 8, 30.0),
    ... ]
    >>> P_mean = arithmetic_mean(stations)
    >>> print(f"Mean P: {P_mean:.1f} mm")
    Mean P: 30.0 mm
    """
    if not stations:
        raise InvalidParameterError("stations list cannot be empty")

    total = sum(s.precipitation_mm for s in stations)
    return total / len(stations)
