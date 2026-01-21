"""Geometric parameters and shape indicators for watershed analysis."""

from dataclasses import dataclass
import math

from hydrolog.exceptions import InvalidParameterError


@dataclass
class ShapeIndicators:
    """
    Shape indicators for a watershed.

    Attributes
    ----------
    form_factor : float
        Form factor Cf = A / L² [-].
        Lower values indicate elongated watersheds.
    compactness_coefficient : float
        Gravelius compactness coefficient Cz = P / (2 * sqrt(π * A)) [-].
        Value of 1.0 indicates a circular watershed.
    circularity_ratio : float
        Miller's circularity ratio Ck = 4πA / P² [-].
        Value of 1.0 indicates a circular watershed.
    elongation_ratio : float
        Schumm's elongation ratio Ce = (2/L) * sqrt(A/π) [-].
        Value of 1.0 indicates a circular watershed.
    lemniscate_ratio : float
        Chorley's lemniscate ratio Cl = L² / (4A) [-].
        Value of 0.79 indicates a circular watershed.
    """

    form_factor: float
    compactness_coefficient: float
    circularity_ratio: float
    elongation_ratio: float
    lemniscate_ratio: float


@dataclass
class GeometricParameters:
    """
    Basic geometric parameters of a watershed.

    Attributes
    ----------
    area_km2 : float
        Watershed area [km²].
    perimeter_km : float
        Watershed perimeter [km].
    length_km : float
        Watershed length (longest dimension) [km].
    width_km : float
        Average watershed width = A / L [km].
    """

    area_km2: float
    perimeter_km: float
    length_km: float
    width_km: float


class WatershedGeometry:
    """
    Calculate geometric parameters and shape indicators for a watershed.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²].
    perimeter_km : float
        Watershed perimeter [km].
    length_km : float
        Watershed length - the longest dimension from outlet
        to the most distant point on the divide [km].

    Examples
    --------
    >>> geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)
    >>> params = geom.get_parameters()
    >>> print(f"Area: {params.area_km2} km², Width: {params.width_km:.2f} km")
    Area: 45.0 km², Width: 3.75 km

    >>> indicators = geom.get_shape_indicators()
    >>> print(f"Form factor: {indicators.form_factor:.3f}")
    Form factor: 0.312

    Create from dictionary (e.g., API response):

    >>> data = {"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 12.0}
    >>> geom = WatershedGeometry.from_dict(data)
    """

    @classmethod
    def from_dict(cls, data: dict) -> "WatershedGeometry":
        """
        Create WatershedGeometry from a dictionary.

        This method is designed for easy integration with JSON APIs
        and external data sources like Hydrograf.

        Parameters
        ----------
        data : dict
            Dictionary with watershed parameters. Required keys:
            area_km2, perimeter_km, length_km.

        Returns
        -------
        WatershedGeometry
            New instance with values from dictionary.

        Raises
        ------
        KeyError
            If required keys are missing.
        InvalidParameterError
            If parameter values are invalid.

        Examples
        --------
        >>> data = {"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 12.0}
        >>> geom = WatershedGeometry.from_dict(data)
        >>> print(f"Area: {geom.area_km2} km²")
        Area: 45.0 km²

        Extra keys in the dictionary are ignored:

        >>> data = {"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 12.0,
        ...         "elevation_min_m": 150.0, "source": "Hydrograf"}
        >>> geom = WatershedGeometry.from_dict(data)
        """
        return cls(
            area_km2=data["area_km2"],
            perimeter_km=data["perimeter_km"],
            length_km=data["length_km"],
        )

    def __init__(
        self,
        area_km2: float,
        perimeter_km: float,
        length_km: float,
    ) -> None:
        """
        Initialize watershed geometry calculator.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²]. Must be positive.
        perimeter_km : float
            Watershed perimeter [km]. Must be positive.
        length_km : float
            Watershed length [km]. Must be positive.

        Raises
        ------
        InvalidParameterError
            If any parameter is not positive.
        """
        if area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")
        if perimeter_km <= 0:
            raise InvalidParameterError(
                f"perimeter_km must be positive, got {perimeter_km}"
            )
        if length_km <= 0:
            raise InvalidParameterError(f"length_km must be positive, got {length_km}")

        self.area_km2 = area_km2
        self.perimeter_km = perimeter_km
        self.length_km = length_km

    @property
    def width_km(self) -> float:
        """
        Average watershed width [km].

        Calculated as W = A / L.
        """
        return self.area_km2 / self.length_km

    def get_parameters(self) -> GeometricParameters:
        """
        Get basic geometric parameters.

        Returns
        -------
        GeometricParameters
            Dataclass with area, perimeter, length, and width.
        """
        return GeometricParameters(
            area_km2=self.area_km2,
            perimeter_km=self.perimeter_km,
            length_km=self.length_km,
            width_km=self.width_km,
        )

    def form_factor(self) -> float:
        """
        Calculate Horton's form factor.

        Returns
        -------
        float
            Form factor Cf = A / L² [-].

        Notes
        -----
        The form factor indicates watershed shape:
        - Cf < 0.5: Elongated watershed
        - Cf ≈ 0.5-0.75: Intermediate shape
        - Cf > 0.75: Compact/circular watershed

        Higher form factors indicate higher peak flows
        for similar rainfall events.
        """
        cf: float = self.area_km2 / (self.length_km**2)
        return cf

    def compactness_coefficient(self) -> float:
        """
        Calculate Gravelius compactness coefficient.

        Returns
        -------
        float
            Compactness coefficient Cz = P / (2 * sqrt(π * A)) [-].

        Notes
        -----
        The Gravelius coefficient compares the watershed perimeter
        to the circumference of a circle with the same area:
        - Cz = 1.0: Circular watershed
        - Cz > 1.0: More irregular shape
        - Cz = 1.12: Square watershed
        - Cz > 1.5: Very elongated watershed
        """
        # Circumference of a circle with area A: C = 2 * sqrt(π * A)
        circle_circumference = 2.0 * math.sqrt(math.pi * self.area_km2)
        cz: float = self.perimeter_km / circle_circumference
        return cz

    def circularity_ratio(self) -> float:
        """
        Calculate Miller's circularity ratio.

        Returns
        -------
        float
            Circularity ratio Ck = 4πA / P² [-].

        Notes
        -----
        The circularity ratio compares the watershed area
        to the area of a circle with the same perimeter:
        - Ck = 1.0: Circular watershed
        - Ck < 1.0: More elongated shape
        - Ck ≈ 0.785: Square watershed
        """
        ck: float = (4.0 * math.pi * self.area_km2) / (self.perimeter_km**2)
        return ck

    def elongation_ratio(self) -> float:
        """
        Calculate Schumm's elongation ratio.

        Returns
        -------
        float
            Elongation ratio Ce = (2/L) * sqrt(A/π) [-].

        Notes
        -----
        The elongation ratio compares the diameter of a circle
        with the same area as the watershed to the watershed length:
        - Ce = 1.0: Circular watershed
        - Ce = 0.6-0.8: Elongated watershed
        - Ce < 0.6: Very elongated watershed
        """
        # Diameter of circle with area A: D = 2 * sqrt(A/π)
        circle_diameter = 2.0 * math.sqrt(self.area_km2 / math.pi)
        ce: float = circle_diameter / self.length_km
        return ce

    def lemniscate_ratio(self) -> float:
        """
        Calculate Chorley's lemniscate ratio.

        Returns
        -------
        float
            Lemniscate ratio Cl = L² / (4A) [-].

        Notes
        -----
        The lemniscate ratio indicates watershed shape:
        - Cl = π/4 ≈ 0.785: Circular watershed
        - Cl > 1.0: Elongated watershed
        - Cl < 0.785: Compact watershed
        """
        cl: float = (self.length_km**2) / (4.0 * self.area_km2)
        return cl

    def get_shape_indicators(self) -> ShapeIndicators:
        """
        Calculate all shape indicators.

        Returns
        -------
        ShapeIndicators
            Dataclass with all shape indicators.

        Examples
        --------
        >>> geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)
        >>> indicators = geom.get_shape_indicators()
        >>> print(f"Compactness: {indicators.compactness_coefficient:.2f}")
        """
        return ShapeIndicators(
            form_factor=self.form_factor(),
            compactness_coefficient=self.compactness_coefficient(),
            circularity_ratio=self.circularity_ratio(),
            elongation_ratio=self.elongation_ratio(),
            lemniscate_ratio=self.lemniscate_ratio(),
        )
