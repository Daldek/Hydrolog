"""Operations of the group ``precip``: design hyetographs and areal precipitation.

Wrappers over the hyetograph generators of :mod:`hydrolog.precipitation.hietogram`
and the interpolation functions of :mod:`hydrolog.precipitation.interpolation`.
:func:`build_hietogram` and :func:`hietogram_notices` are shared with
``hydrograph generate``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal, get_args

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.catalog.inputs import load_stations
from hydrolog.operations._common import (
    check_choice,
    forbid_options,
    option_error,
    real_number,
    require_option,
    select_group,
)
from hydrolog.precipitation import (
    BetaHietogram,
    BlockHietogram,
    EulerIIHietogram,
    HietogramResult,
    TriangularHietogram,
    areal_precipitation_idw,
    arithmetic_mean,
    inverse_distance_weighting,
    isohyet_method,
    thiessen_polygons,
)

__all__ = [
    "AREAL_METHODS",
    "HIETOGRAM_TYPES",
    "ArealMethod",
    "ArealPrecipitationResult",
    "HietogramType",
    "PrecipHietogramResult",
    "build_hietogram",
    "hietogram_notices",
    "precip_areal",
    "precip_hietogram",
]

HietogramType = Literal["block", "triangular", "beta", "euler_ii"]
ArealMethod = Literal["arithmetic", "thiessen", "idw", "isohyet"]
HIETOGRAM_TYPES: tuple[str, ...] = get_args(HietogramType)
AREAL_METHODS: tuple[str, ...] = get_args(ArealMethod)


@dataclass
class PrecipHietogramResult(JsonResultMixin):
    """Design hyetograph.

    Attributes
    ----------
    hietogram_type : str
        ``"block"``, ``"triangular"``, ``"beta"`` or ``"euler_ii"``.
    total_mm : float
        Total precipitation depth [mm].
    duration_min : float
        Requested duration [min].
    timestep_min : float
        Time step [min].
    n_steps : int
        Number of steps, ``int(duration_min / timestep_min)``.
    parameters : dict of str to float
        Shape parameters used: ``alpha`` and ``beta`` (beta type) or
        ``peak_position`` (triangular and Euler II types); empty for ``block``.
    peak_intensity_mm_per_h : float
        Highest intensity [mm/h].
    times_min : numpy.ndarray
        End of each step [min].
    depths_mm : numpy.ndarray
        Precipitation depth of each step [mm] (``HietogramResult.intensities_mm``).
    intensities_mm_per_h : numpy.ndarray
        Intensity of each step [mm/h].
    """

    hietogram_type: str
    total_mm: float
    duration_min: float
    timestep_min: float
    n_steps: int
    parameters: dict[str, float]
    peak_intensity_mm_per_h: float
    times_min: NDArray[np.float64]
    depths_mm: NDArray[np.float64]
    intensities_mm_per_h: NDArray[np.float64]


@dataclass
class ArealPrecipitationResult(JsonResultMixin):
    """Areal precipitation.

    Attributes
    ----------
    method : str
        ``"arithmetic"``, ``"thiessen"``, ``"idw"`` or ``"isohyet"``.
    areal_precipitation_mm : float
        Areal precipitation [mm].
    n_stations : int or None
        Number of gauges given (``None`` for ``isohyet``).
    station_weights : dict of str to float or None
        Weight of each gauge (``thiessen`` and ``idw`` at a point).
    station_contributions_mm : dict of str to float or None
        ``precipitation * weight`` of each gauge (``thiessen``).
    power : float or None
        IDW distance exponent.
    n_grid_points : int or None
        Number of grid points (``idw`` over a grid).
    isohyet_values_mm : numpy.ndarray or None
        Isohyet values [mm] (``isohyet``).
    area_fractions : numpy.ndarray or None
        Area fractions of the zones between the isohyets (``isohyet``).
    """

    method: str
    areal_precipitation_mm: float
    n_stations: int | None = None
    station_weights: dict[str, float] | None = None
    station_contributions_mm: dict[str, float] | None = None
    power: float | None = None
    n_grid_points: int | None = None
    isohyet_values_mm: NDArray[np.float64] | None = None
    area_fractions: NDArray[np.float64] | None = None


def build_hietogram(
    hietogram_type: str,
    total_mm: float,
    duration_min: float,
    timestep_min: float = 5.0,
    *,
    alpha: float | None = None,
    beta: float | None = None,
    peak_position: float | None = None,
) -> tuple[HietogramResult, dict[str, float]]:
    """Generate a hyetograph with the generator of the chosen type.

    Parameters
    ----------
    hietogram_type : {"block", "triangular", "beta", "euler_ii"}
        Distribution.
    total_mm : float
        Total depth [mm], > 0.
    duration_min : float
        Duration [min], > 0.
    timestep_min : float, optional
        Time step [min], by default 5.
    alpha, beta : float, optional
        Beta distribution parameters (``beta`` type only; library defaults 2 and 5).
    peak_position : float, optional
        Relative peak position (``triangular`` and ``euler_ii`` only; library
        defaults 0.5 and 0.33).

    Returns
    -------
    HietogramResult
        The hyetograph.
    dict of str to float
        The shape parameters actually used.

    Raises
    ------
    InvalidParameterError
        If the type is unknown, a parameter of another type is given, or a value is
        out of range.
    """
    kind = check_choice("hietogram_type", hietogram_type, HIETOGRAM_TYPES)
    parameters: dict[str, float] = {}
    if kind == "block":
        forbid_options(
            {"alpha": alpha, "beta": beta, "peak_position": peak_position},
            context="hietogram_type is 'block'",
            hint="The block hyetograph has no shape parameters.",
        )
        generator: Any = BlockHietogram()
    elif kind == "beta":
        forbid_options(
            {"peak_position": peak_position},
            context="hietogram_type is 'beta'",
            hint="Use alpha and beta to shape the Beta hyetograph.",
        )
        shape = {"alpha": alpha, "beta": beta}
        generator = BetaHietogram(
            **{name: value for name, value in shape.items() if value is not None}
        )
        parameters = {"alpha": generator.alpha, "beta": generator.beta}
    else:
        forbid_options(
            {"alpha": alpha, "beta": beta},
            context=f"hietogram_type is {kind!r}",
            hint="Use peak_position to shape this hyetograph.",
        )
        generator = (TriangularHietogram if kind == "triangular" else EulerIIHietogram)(
            **({} if peak_position is None else {"peak_position": peak_position})
        )
        parameters = {"peak_position": generator.peak_position}
    result = generator.generate(
        total_mm=total_mm, duration_min=duration_min, timestep_min=timestep_min
    )
    return result, parameters


def hietogram_notices(hietogram: HietogramResult) -> list[Notice]:
    """Notice for a duration that is not a multiple of the time step.

    The generators use ``int(duration_min / timestep_min)`` steps, so the
    hyetograph then ends before ``duration_min``.

    Parameters
    ----------
    hietogram : HietogramResult
        Generated hyetograph.

    Returns
    -------
    list of Notice
        One warning notice when the steps do not cover the requested duration.
    """
    covered = hietogram.n_steps * hietogram.timestep_min
    if math.isclose(covered, hietogram.duration_min, rel_tol=1e-9, abs_tol=1e-9):
        return []
    return [
        Notice(
            "warning",
            "duration_not_covered",
            f"duration_min = {hietogram.duration_min:g} is not a multiple of "
            f"timestep_min = {hietogram.timestep_min:g}: the hyetograph has "
            f"{hietogram.n_steps} steps and covers {covered:g} min.",
        )
    ]


def precip_hietogram(
    *,
    hietogram_type: HietogramType,
    total_mm: float,
    duration_min: float,
    timestep_min: float = 5.0,
    alpha: float | None = None,
    beta: float | None = None,
    peak_position: float | None = None,
) -> OperationOutput:
    """Design hyetograph (``precip hietogram``).

    Parameters
    ----------
    hietogram_type : {"block", "triangular", "beta", "euler_ii"}
        Temporal distribution.
    total_mm : float
        Total precipitation depth [mm], > 0.
    duration_min : float
        Storm duration [min], > 0 and >= ``timestep_min``.
    timestep_min : float, optional
        Time step [min], > 0, by default 5.
    alpha : float, optional
        Beta distribution parameter (``beta`` type), > 0, default 2.
    beta : float, optional
        Beta distribution parameter (``beta`` type), > 0, default 5.
    peak_position : float, optional
        Relative peak position in (0, 1) (``triangular`` default 0.5, ``euler_ii``
        default 0.33).

    Returns
    -------
    OperationOutput
        :class:`PrecipHietogramResult` and a notice when the duration is not a
        multiple of the step.

    Raises
    ------
    InvalidParameterError
        If a parameter is out of range or does not apply to the chosen type.
    """
    hietogram, parameters = build_hietogram(
        hietogram_type,
        total_mm,
        duration_min,
        timestep_min,
        alpha=alpha,
        beta=beta,
        peak_position=peak_position,
    )
    rates = hietogram.intensity_mm_per_h
    result = PrecipHietogramResult(
        hietogram_type=hietogram_type,
        total_mm=hietogram.total_mm,
        duration_min=hietogram.duration_min,
        timestep_min=hietogram.timestep_min,
        n_steps=hietogram.n_steps,
        parameters=parameters,
        peak_intensity_mm_per_h=float(np.max(rates)),
        times_min=hietogram.times_min,
        depths_mm=hietogram.intensities_mm,
        intensities_mm_per_h=rates,
    )
    return OperationOutput(result, hietogram_notices(hietogram))


_STATION_METHODS = ("arithmetic", "thiessen", "idw")


def _areas_by_station(areas: dict[str, Any]) -> dict[str, float]:
    parsed: dict[str, float] = {}
    for name, value in areas.items():
        area = real_number("polygon_areas_km2", value)
        if area < 0:
            raise option_error(
                "polygon_areas_km2",
                "minimum",
                f"Area of {name!r} must be non-negative, got {area}",
                station=name,
                value=area,
            )
        parsed[str(name)] = area
    return parsed


def precip_areal(
    *,
    method: ArealMethod,
    stations: list[dict[str, Any]] | None = None,
    stations_file: str | None = None,
    polygon_areas_km2: dict[str, Any] | None = None,
    target_x: float | None = None,
    target_y: float | None = None,
    grid_x: list[float] | None = None,
    grid_y: list[float] | None = None,
    power: float | None = None,
    max_distance: float | None = None,
    isohyet_values_mm: list[float] | None = None,
    area_fractions: list[float] | None = None,
) -> OperationOutput:
    """Areal precipitation from point data or isohyets (``precip areal``).

    Parameters
    ----------
    method : {"arithmetic", "thiessen", "idw", "isohyet"}
        Method. ``arithmetic``, ``thiessen`` and ``idw`` need gauges (exactly one
        of ``stations`` and ``stations_file``); ``thiessen`` also needs
        ``polygon_areas_km2``; ``idw`` needs a target point (``target_x`` and
        ``target_y``) or a grid (``grid_x`` and ``grid_y``); ``isohyet`` needs
        ``isohyet_values_mm`` and ``area_fractions``.
    stations : list of dict, optional
        Gauges ``{"name", "x", "y", "precipitation_mm"[, "elevation_m"]}``.
    stations_file : str, optional
        CSV or JSON file with the gauges.
    polygon_areas_km2 : dict, optional
        Thiessen polygon area [km2] by gauge name.
    target_x, target_y : float, optional
        IDW target point (coordinate unit of the gauges).
    grid_x, grid_y : list of float, optional
        IDW grid points; the result is the mean of their IDW values.
    power : float, optional
        IDW distance exponent, > 0, default 2.
    max_distance : float, optional
        IDW maximum gauge distance at a target point.
    isohyet_values_mm : list of float, optional
        Isohyet values [mm], at least two.
    area_fractions : list of float, optional
        Area fraction of each zone between isohyets, summing to 1.

    Returns
    -------
    OperationOutput
        :class:`ArealPrecipitationResult`; for ``thiessen`` a warning notice names
        the gauges without a polygon area (they are not used).

    Raises
    ------
    InvalidParameterError
        If an option the method needs is missing or an option of another method is
        given (``reason`` ``required`` or ``not_applicable``), or a value is
        invalid.
    NotFoundError
        If ``stations_file`` does not exist.
    InputDataError
        If ``stations_file`` is malformed.
    """
    kind = check_choice("method", method, AREAL_METHODS)
    station_options = {"stations": stations, "stations_file": stations_file}
    if kind == "isohyet":
        forbid_options(
            {
                **station_options,
                "polygon_areas_km2": polygon_areas_km2,
                "target_x": target_x,
                "target_y": target_y,
                "grid_x": grid_x,
                "grid_y": grid_y,
                "power": power,
                "max_distance": max_distance,
            },
            context="method is 'isohyet'",
            hint="The isohyet method takes isohyet_values_mm and area_fractions.",
        )
        values = require_option(
            "isohyet_values_mm", isohyet_values_mm, when="method is 'isohyet'"
        )
        fractions = require_option(
            "area_fractions", area_fractions, when="method is 'isohyet'"
        )
        zones = isohyet_method(np.asarray(values), np.asarray(fractions))
        return OperationOutput(
            ArealPrecipitationResult(
                method=kind,
                areal_precipitation_mm=zones.areal_precipitation_mm,
                isohyet_values_mm=zones.isohyet_values_mm,
                area_fractions=zones.area_fractions,
            )
        )
    forbid_options(
        {"isohyet_values_mm": isohyet_values_mm, "area_fractions": area_fractions},
        context=f"method is {kind!r}",
        hint="isohyet_values_mm and area_fractions belong to method 'isohyet'.",
    )
    gauges = load_stations(stations=stations, stations_file=stations_file)
    notices: list[Notice] = []
    if kind == "arithmetic":
        forbid_options(
            {
                "polygon_areas_km2": polygon_areas_km2,
                "target_x": target_x,
                "target_y": target_y,
                "grid_x": grid_x,
                "grid_y": grid_y,
                "power": power,
                "max_distance": max_distance,
            },
            context="method is 'arithmetic'",
        )
        return OperationOutput(
            ArealPrecipitationResult(
                method=kind,
                areal_precipitation_mm=arithmetic_mean(gauges),
                n_stations=len(gauges),
            )
        )
    if kind == "thiessen":
        forbid_options(
            {
                "target_x": target_x,
                "target_y": target_y,
                "grid_x": grid_x,
                "grid_y": grid_y,
                "power": power,
                "max_distance": max_distance,
            },
            context="method is 'thiessen'",
        )
        areas = _areas_by_station(
            require_option(
                "polygon_areas_km2", polygon_areas_km2, when="method is 'thiessen'"
            )
        )
        polygons = thiessen_polygons(gauges, areas)
        skipped = [
            gauge.station_id for gauge in gauges if gauge.station_id not in areas
        ]
        if skipped:
            notices.append(
                Notice(
                    "warning",
                    "stations_without_polygon",
                    "Gauges without a polygon area were not used: "
                    f"{', '.join(skipped)}.",
                )
            )
        return OperationOutput(
            ArealPrecipitationResult(
                method=kind,
                areal_precipitation_mm=polygons.areal_precipitation_mm,
                n_stations=len(gauges),
                station_weights=polygons.station_weights,
                station_contributions_mm=polygons.station_contributions_mm,
            ),
            notices,
        )
    forbid_options(
        {"polygon_areas_km2": polygon_areas_km2},
        context="method is 'idw'",
        hint="polygon_areas_km2 belongs to method 'thiessen'.",
    )
    exponent = 2.0 if power is None else power
    chosen = select_group(
        {
            "target_x": target_x,
            "target_y": target_y,
            "grid_x": grid_x,
            "grid_y": grid_y,
            "max_distance": max_distance,
        },
        {"point": ("target_x", "target_y"), "grid": ("grid_x", "grid_y")},
        extra={"max_distance": "point"},
    )
    if chosen == "grid":
        assert grid_x is not None and grid_y is not None
        mean = areal_precipitation_idw(
            gauges, np.asarray(grid_x, dtype=np.float64), np.asarray(grid_y), exponent
        )
        return OperationOutput(
            ArealPrecipitationResult(
                method=kind,
                areal_precipitation_mm=mean,
                n_stations=len(gauges),
                power=exponent,
                n_grid_points=len(grid_x),
            )
        )
    assert target_x is not None and target_y is not None
    interpolated = inverse_distance_weighting(
        gauges, target_x, target_y, power=exponent, max_distance=max_distance
    )
    return OperationOutput(
        ArealPrecipitationResult(
            method=kind,
            areal_precipitation_mm=interpolated.areal_precipitation_mm,
            n_stations=len(gauges),
            station_weights=interpolated.station_weights,
            power=interpolated.power,
        )
    )
