"""Terrain parameters for watershed analysis."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


@dataclass
class ElevationParameters:
    """
    Elevation parameters of a watershed.

    Attributes
    ----------
    elevation_min_m : float
        Minimum elevation (outlet) [m a.s.l.].
    elevation_max_m : float
        Maximum elevation [m a.s.l.].
    elevation_mean_m : float
        Mean elevation [m a.s.l.].
    relief_m : float
        Relief (elevation difference) H = max - min [m].
    relief_ratio : float
        Relief ratio Rh = H / L [-].
    """

    elevation_min_m: float
    elevation_max_m: float
    elevation_mean_m: float
    relief_m: float
    relief_ratio: float


@dataclass
class SlopeParameters:
    """
    Slope parameters of a watershed.

    Attributes
    ----------
    watershed_slope_percent : float
        Average watershed slope [%].
    watershed_slope_m_per_m : float
        Average watershed slope [m/m].
    channel_slope_percent : float
        Main channel slope [%].
    channel_slope_m_per_m : float
        Main channel slope [m/m].
    """

    watershed_slope_percent: float
    watershed_slope_m_per_m: float
    channel_slope_percent: float
    channel_slope_m_per_m: float


class TerrainAnalysis:
    """
    Analyze terrain parameters of a watershed.

    Provides methods to calculate elevation statistics and slope
    parameters from watershed data.

    Parameters
    ----------
    elevation_min_m : float
        Minimum elevation at outlet [m a.s.l.].
    elevation_max_m : float
        Maximum elevation in watershed [m a.s.l.].
    elevation_mean_m : float, optional
        Mean elevation [m a.s.l.]. If not provided, calculated as
        (min + max) / 2 (rough approximation).
    length_km : float
        Watershed length [km]. Used for relief ratio.
    channel_length_km : float, optional
        Main channel length [km]. If not provided, uses watershed length.

    Examples
    --------
    >>> terrain = TerrainAnalysis(
    ...     elevation_min_m=150.0,
    ...     elevation_max_m=520.0,
    ...     elevation_mean_m=340.0,
    ...     length_km=12.0,
    ...     channel_length_km=15.0
    ... )
    >>> elev = terrain.get_elevation_parameters()
    >>> print(f"Relief: {elev.relief_m} m")
    Relief: 370.0 m
    """

    def __init__(
        self,
        elevation_min_m: float,
        elevation_max_m: float,
        length_km: float,
        elevation_mean_m: Optional[float] = None,
        channel_length_km: Optional[float] = None,
    ) -> None:
        """
        Initialize terrain analysis.

        Parameters
        ----------
        elevation_min_m : float
            Minimum elevation at outlet [m a.s.l.].
        elevation_max_m : float
            Maximum elevation in watershed [m a.s.l.].
        length_km : float
            Watershed length [km].
        elevation_mean_m : float, optional
            Mean elevation [m a.s.l.].
        channel_length_km : float, optional
            Main channel length [km].

        Raises
        ------
        InvalidParameterError
            If parameters are invalid.
        """
        if elevation_max_m <= elevation_min_m:
            raise InvalidParameterError(
                f"elevation_max_m ({elevation_max_m}) must be greater than "
                f"elevation_min_m ({elevation_min_m})"
            )
        if length_km <= 0:
            raise InvalidParameterError(f"length_km must be positive, got {length_km}")

        self.elevation_min_m = elevation_min_m
        self.elevation_max_m = elevation_max_m
        self.length_km = length_km

        # Default mean elevation as midpoint if not provided
        if elevation_mean_m is None:
            self.elevation_mean_m = (elevation_min_m + elevation_max_m) / 2.0
        else:
            if not elevation_min_m <= elevation_mean_m <= elevation_max_m:
                raise InvalidParameterError(
                    f"elevation_mean_m ({elevation_mean_m}) must be between "
                    f"min ({elevation_min_m}) and max ({elevation_max_m})"
                )
            self.elevation_mean_m = elevation_mean_m

        # Default channel length to watershed length if not provided
        if channel_length_km is None:
            self.channel_length_km = length_km
        else:
            if channel_length_km <= 0:
                raise InvalidParameterError(
                    f"channel_length_km must be positive, got {channel_length_km}"
                )
            self.channel_length_km = channel_length_km

    @property
    def relief_m(self) -> float:
        """Relief (elevation difference) [m]."""
        return self.elevation_max_m - self.elevation_min_m

    @property
    def relief_ratio(self) -> float:
        """
        Relief ratio Rh = H / L [-].

        The relief ratio is the ratio of total relief to
        watershed length, indicating overall steepness.
        """
        # Convert length to meters for dimensionless ratio
        length_m = self.length_km * 1000.0
        rh: float = self.relief_m / length_m
        return rh

    def watershed_slope(self) -> tuple[float, float]:
        """
        Calculate average watershed slope.

        Uses the relief ratio as an approximation of average slope.

        Returns
        -------
        tuple[float, float]
            (slope_percent, slope_m_per_m)

        Notes
        -----
        This is a simplified calculation. For more accurate slope,
        use DEM-based analysis with actual slope distribution.
        """
        slope_m_per_m = self.relief_ratio
        slope_percent = slope_m_per_m * 100.0
        return slope_percent, slope_m_per_m

    def channel_slope(self) -> tuple[float, float]:
        """
        Calculate main channel slope.

        Uses elevation difference divided by channel length.

        Returns
        -------
        tuple[float, float]
            (slope_percent, slope_m_per_m)
        """
        channel_length_m = self.channel_length_km * 1000.0
        slope_m_per_m: float = self.relief_m / channel_length_m
        slope_percent = slope_m_per_m * 100.0
        return slope_percent, slope_m_per_m

    def get_elevation_parameters(self) -> ElevationParameters:
        """
        Get all elevation parameters.

        Returns
        -------
        ElevationParameters
            Dataclass with elevation statistics.
        """
        return ElevationParameters(
            elevation_min_m=self.elevation_min_m,
            elevation_max_m=self.elevation_max_m,
            elevation_mean_m=self.elevation_mean_m,
            relief_m=self.relief_m,
            relief_ratio=self.relief_ratio,
        )

    def get_slope_parameters(self) -> SlopeParameters:
        """
        Get all slope parameters.

        Returns
        -------
        SlopeParameters
            Dataclass with slope statistics.
        """
        ws_pct, ws_m = self.watershed_slope()
        ch_pct, ch_m = self.channel_slope()

        return SlopeParameters(
            watershed_slope_percent=ws_pct,
            watershed_slope_m_per_m=ws_m,
            channel_slope_percent=ch_pct,
            channel_slope_m_per_m=ch_m,
        )

    @staticmethod
    def mean_elevation_from_dem(
        elevations: NDArray[np.float64],
        weights: Optional[NDArray[np.float64]] = None,
    ) -> float:
        """
        Calculate mean elevation from DEM data.

        Parameters
        ----------
        elevations : NDArray[np.float64]
            Array of elevation values [m].
        weights : NDArray[np.float64], optional
            Weights for each elevation (e.g., cell areas).
            If not provided, uses uniform weights.

        Returns
        -------
        float
            Weighted mean elevation [m].

        Examples
        --------
        >>> elevations = np.array([100, 150, 200, 250, 300])
        >>> mean_elev = TerrainAnalysis.mean_elevation_from_dem(elevations)
        >>> print(f"Mean elevation: {mean_elev} m")
        Mean elevation: 200.0 m
        """
        elevations = np.asarray(elevations, dtype=np.float64)

        if len(elevations) == 0:
            raise InvalidParameterError("elevations array cannot be empty")

        if weights is None:
            mean_elev: float = float(np.mean(elevations))
        else:
            weights = np.asarray(weights, dtype=np.float64)
            if len(weights) != len(elevations):
                raise InvalidParameterError(
                    f"weights length ({len(weights)}) must match "
                    f"elevations length ({len(elevations)})"
                )
            mean_elev = float(np.average(elevations, weights=weights))

        return mean_elev
