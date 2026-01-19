"""Hypsometric curve analysis for watershed characterization."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


@dataclass
class HypsometricResult:
    """
    Result of hypsometric curve analysis.

    Attributes
    ----------
    relative_heights : NDArray[np.float64]
        Relative heights h/H (0 to 1), where h is height above
        minimum and H is total relief.
    relative_areas : NDArray[np.float64]
        Relative cumulative areas a/A (0 to 1), where a is area
        above a given elevation and A is total area.
    hypsometric_integral : float
        Hypsometric integral (area under the curve) [-].
        Indicates erosion stage of the watershed.
    elevation_mean_m : float
        Mean elevation derived from hypsometric curve [m a.s.l.].
    elevation_median_m : float
        Median elevation (50% area above) [m a.s.l.].
    """

    relative_heights: NDArray[np.float64]
    relative_areas: NDArray[np.float64]
    hypsometric_integral: float
    elevation_mean_m: float
    elevation_median_m: float

    @property
    def n_points(self) -> int:
        """Number of points in the hypsometric curve."""
        return len(self.relative_heights)


class HypsometricCurve:
    """
    Generate and analyze hypsometric curves.

    The hypsometric curve shows the relationship between elevation
    and the cumulative area above that elevation. It characterizes
    the distribution of landmass with elevation.

    Parameters
    ----------
    elevations : NDArray[np.float64]
        Array of elevation values from DEM [m a.s.l.].
    cell_areas : NDArray[np.float64], optional
        Area of each DEM cell [km²]. If not provided, assumes
        uniform cell sizes.

    Notes
    -----
    The hypsometric integral (HI) indicates the erosion stage:
    - HI > 0.6: Young (convex curve) - little erosion
    - HI = 0.4-0.6: Mature (S-shaped curve) - moderate erosion
    - HI < 0.4: Old (concave curve) - extensive erosion

    Examples
    --------
    >>> elevations = np.array([100, 150, 200, 250, 300, 350, 400])
    >>> hypso = HypsometricCurve(elevations)
    >>> result = hypso.analyze()
    >>> print(f"Hypsometric integral: {result.hypsometric_integral:.3f}")
    """

    def __init__(
        self,
        elevations: NDArray[np.float64],
        cell_areas: Optional[NDArray[np.float64]] = None,
    ) -> None:
        """
        Initialize hypsometric curve analysis.

        Parameters
        ----------
        elevations : NDArray[np.float64]
            Array of elevation values from DEM [m a.s.l.].
        cell_areas : NDArray[np.float64], optional
            Area of each DEM cell [km²].

        Raises
        ------
        InvalidParameterError
            If elevations array is empty or has invalid values.
        """
        self.elevations = np.asarray(elevations, dtype=np.float64).flatten()

        if len(self.elevations) == 0:
            raise InvalidParameterError("elevations array cannot be empty")

        if cell_areas is not None:
            self.cell_areas = np.asarray(cell_areas, dtype=np.float64).flatten()
            if len(self.cell_areas) != len(self.elevations):
                raise InvalidParameterError(
                    f"cell_areas length ({len(self.cell_areas)}) must match "
                    f"elevations length ({len(self.elevations)})"
                )
            if np.any(self.cell_areas <= 0):
                raise InvalidParameterError("all cell_areas must be positive")
        else:
            # Uniform cell areas
            self.cell_areas = np.ones_like(self.elevations)

        self._total_area = float(np.sum(self.cell_areas))

    @property
    def elevation_min(self) -> float:
        """Minimum elevation [m a.s.l.]."""
        return float(np.min(self.elevations))

    @property
    def elevation_max(self) -> float:
        """Maximum elevation [m a.s.l.]."""
        return float(np.max(self.elevations))

    @property
    def relief(self) -> float:
        """Total relief H = max - min [m]."""
        return self.elevation_max - self.elevation_min

    @property
    def total_area(self) -> float:
        """Total watershed area [km²]."""
        return self._total_area

    def generate_curve(
        self, n_points: int = 101
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Generate hypsometric curve data.

        Parameters
        ----------
        n_points : int, optional
            Number of points for the curve, by default 101.

        Returns
        -------
        tuple[NDArray[np.float64], NDArray[np.float64]]
            (relative_heights, relative_areas) both in range [0, 1].

        Notes
        -----
        relative_height = (elevation - min) / relief
        relative_area = cumulative_area_above / total_area
        """
        if n_points < 2:
            raise InvalidParameterError(f"n_points must be >= 2, got {n_points}")

        # Create elevation thresholds
        elev_thresholds = np.linspace(self.elevation_min, self.elevation_max, n_points)

        # Calculate cumulative area above each threshold
        cumulative_areas = np.zeros(n_points, dtype=np.float64)

        for i, threshold in enumerate(elev_thresholds):
            mask = self.elevations >= threshold
            cumulative_areas[i] = np.sum(self.cell_areas[mask])

        # Convert to relative values
        relative_heights = (elev_thresholds - self.elevation_min) / self.relief
        relative_areas = cumulative_areas / self.total_area

        return relative_heights, relative_areas

    def hypsometric_integral(self, n_points: int = 101) -> float:
        """
        Calculate hypsometric integral.

        The hypsometric integral is the area under the hypsometric
        curve, representing the proportion of upland mass remaining.

        Parameters
        ----------
        n_points : int, optional
            Number of points for integration, by default 101.

        Returns
        -------
        float
            Hypsometric integral (0 to 1).

        Notes
        -----
        Interpretation:
        - HI > 0.6: Youthful stage (convex curve)
        - HI = 0.4-0.6: Mature stage (S-shaped curve)
        - HI < 0.4: Old stage (concave curve)
        """
        rel_heights, rel_areas = self.generate_curve(n_points)

        # Integrate using trapezoidal rule
        # Note: we integrate area (y) against height (x)
        hi: float = float(np.trapezoid(rel_areas, rel_heights))
        return hi

    def elevation_at_percentile(self, percentile: float) -> float:
        """
        Find elevation at a given area percentile.

        Parameters
        ----------
        percentile : float
            Percentile of area (0-100). E.g., 50 means the elevation
            where 50% of the area is above.

        Returns
        -------
        float
            Elevation at the given percentile [m a.s.l.].

        Examples
        --------
        >>> hypso = HypsometricCurve(elevations)
        >>> median_elev = hypso.elevation_at_percentile(50)
        """
        if not 0 <= percentile <= 100:
            raise InvalidParameterError(
                f"percentile must be in range 0-100, got {percentile}"
            )

        # Sort elevations in descending order with their areas
        sorted_indices = np.argsort(self.elevations)[::-1]
        sorted_elevations = self.elevations[sorted_indices]
        sorted_areas = self.cell_areas[sorted_indices]

        # Calculate cumulative area percentage
        cumulative_area = np.cumsum(sorted_areas)
        cumulative_percent = (cumulative_area / self.total_area) * 100.0

        # Find elevation where cumulative percentage reaches target
        target = percentile
        idx = np.searchsorted(cumulative_percent, target)

        if idx >= len(sorted_elevations):
            return float(sorted_elevations[-1])

        return float(sorted_elevations[idx])

    def mean_elevation(self) -> float:
        """
        Calculate area-weighted mean elevation.

        Returns
        -------
        float
            Mean elevation [m a.s.l.].
        """
        mean_elev: float = float(np.average(self.elevations, weights=self.cell_areas))
        return mean_elev

    def analyze(self, n_points: int = 101) -> HypsometricResult:
        """
        Perform complete hypsometric analysis.

        Parameters
        ----------
        n_points : int, optional
            Number of points for the curve, by default 101.

        Returns
        -------
        HypsometricResult
            Complete analysis results.

        Examples
        --------
        >>> elevations = np.linspace(100, 500, 1000)
        >>> hypso = HypsometricCurve(elevations)
        >>> result = hypso.analyze()
        >>> print(f"HI: {result.hypsometric_integral:.3f}")
        >>> print(f"Mean elev: {result.elevation_mean_m:.1f} m")
        """
        rel_heights, rel_areas = self.generate_curve(n_points)
        hi = self.hypsometric_integral(n_points)
        mean_elev = self.mean_elevation()
        median_elev = self.elevation_at_percentile(50)

        return HypsometricResult(
            relative_heights=rel_heights,
            relative_areas=rel_areas,
            hypsometric_integral=hi,
            elevation_mean_m=mean_elev,
            elevation_median_m=median_elev,
        )
