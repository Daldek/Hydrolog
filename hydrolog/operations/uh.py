"""Operations of the group ``uh``: unit hydrographs (SCS, Nash, Clark, Snyder).

Wrappers over :class:`~hydrolog.runoff.SCSUnitHydrograph`,
:class:`~hydrolog.runoff.NashIUH`, :class:`~hydrolog.runoff.ClarkIUH` and
:class:`~hydrolog.runoff.SnyderUH`. All four return the same :class:`UhResult`: the
unit hydrograph of the catchment in m3/s per mm of effective precipitation.

Nash and Clark parameters can be given in several ways; the group of options that is
given selects the way (``NashIUH.from_tc`` is deliberately not offered: it is
deprecated and not justified for the Nash model).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.operations._common import option_error, select_group
from hydrolog.runoff import (
    ClarkIUH,
    LutzCalculationResult,
    NashIUH,
    SCSUnitHydrograph,
    SnyderUH,
)

__all__ = [
    "UhResult",
    "uh_clark",
    "uh_nash",
    "uh_scs",
    "uh_snyder",
]


@dataclass
class UhResult(JsonResultMixin):
    """Unit hydrograph of a catchment.

    Attributes
    ----------
    model : str
        ``"scs"``, ``"nash"``, ``"clark"`` or ``"snyder"``.
    estimation : str
        How the parameters were obtained: ``"direct"`` (given), ``"lutz"`` or
        ``"urban_regression"`` (Nash), ``"r_tc_ratio"`` (Clark R from R/tc).
    area_km2 : float
        Catchment area [km2].
    timestep_min : float
        Time step [min].
    duration_min : float
        Duration D of the unit rainfall the hydrograph belongs to [min].
    lag_time_min : float
        Lag time [min]: ``0.6 tc`` (SCS), ``n K`` (Nash), approximately
        ``tc / 2 + R`` (Clark), the basin lag ``tL`` (Snyder).
    time_to_peak_min : float
        Time to peak [min].
    peak_discharge_m3s_per_mm : float
        Peak ordinate [m3/s per mm of effective precipitation].
    time_base_min : float or None
        Time base [min] for the models that define one (SCS, Snyder), else ``None``.
    parameters : dict of str to float
        Model parameters used.
    derived : dict of str to float
        Further model-specific results (Snyder: ``standard_duration_min``,
        ``adjusted_lag_time_min``).
    lutz : LutzCalculationResult or None
        Intermediate results of the Lutz method (Nash, ``lutz`` estimation).
    times_min : numpy.ndarray
        Time of each ordinate [min].
    ordinates_m3s_per_mm : numpy.ndarray
        Unit hydrograph ordinates [m3/s per mm].
    """

    model: str
    estimation: str
    area_km2: float
    timestep_min: float
    duration_min: float
    lag_time_min: float
    time_to_peak_min: float
    peak_discharge_m3s_per_mm: float
    time_base_min: float | None
    parameters: dict[str, float]
    derived: dict[str, float] = field(default_factory=dict)
    lutz: LutzCalculationResult | None = None
    times_min: NDArray[np.float64] = field(default_factory=lambda: np.empty(0))
    ordinates_m3s_per_mm: NDArray[np.float64] = field(
        default_factory=lambda: np.empty(0)
    )


def uh_scs(*, area_km2: float, tc_min: float, timestep_min: float = 5.0) -> UhResult:
    """SCS (NRCS) unit hydrograph (``uh scs``).

    Parameters
    ----------
    area_km2 : float
        Catchment area [km2], > 0.
    tc_min : float
        Time of concentration [min], > 0.
    timestep_min : float, optional
        Time step and unit rainfall duration D [min], > 0, by default 5.

    Returns
    -------
    UhResult
        ``tlag = 0.6 tc``, ``tp = D / 2 + tlag``, ``qp = 0.208 A / tp``,
        ``tb = 5 tp`` and the ordinates.

    Raises
    ------
    InvalidParameterError
        If a parameter is not positive.
    """
    shape = SCSUnitHydrograph(area_km2=area_km2, tc_min=tc_min).generate(
        timestep_min=timestep_min
    )
    return UhResult(
        model="scs",
        estimation="direct",
        area_km2=area_km2,
        timestep_min=timestep_min,
        duration_min=timestep_min,
        lag_time_min=shape.lag_time_min,
        time_to_peak_min=shape.time_to_peak_min,
        peak_discharge_m3s_per_mm=shape.peak_discharge_m3s,
        time_base_min=shape.time_base_min,
        parameters={"tc_min": tc_min},
        times_min=shape.times_min,
        ordinates_m3s_per_mm=shape.ordinates_m3s,
    )


def uh_nash(
    *,
    area_km2: float,
    n: float | None = None,
    k_min: float | None = None,
    lutz_length_km: float | None = None,
    lutz_centroid_length_km: float | None = None,
    lutz_slope_m_per_m: float | None = None,
    lutz_manning_n: float | None = None,
    lutz_urban_pct: float | None = None,
    lutz_forest_pct: float | None = None,
    urban_effective_precip_mm: float | None = None,
    urban_duration_h: float | None = None,
    urban_fraction: float | None = None,
    timestep_min: float = 5.0,
    rainfall_duration_min: float | None = None,
    total_duration_min: float | None = None,
) -> UhResult:
    """Nash cascade unit hydrograph (``uh nash``).

    Give exactly one group of parameters: ``n`` with ``k_min`` (direct), the Lutz
    inputs (``lutz_length_km``, ``lutz_centroid_length_km``, ``lutz_slope_m_per_m``,
    ``lutz_manning_n``; optionally ``lutz_urban_pct``, ``lutz_forest_pct``), or the
    urban regression inputs (``urban_effective_precip_mm``, ``urban_duration_h``;
    optionally ``urban_fraction``).

    Parameters
    ----------
    area_km2 : float
        Catchment area [km2], > 0.
    n : float, optional
        Number of reservoirs, > 0.
    k_min : float, optional
        Storage constant of a reservoir [min], > 0.
    lutz_length_km, lutz_centroid_length_km : float, optional
        Main stream length L and length to the centroid Lc [km], Lc <= L.
    lutz_slope_m_per_m : float, optional
        Mean slope of the main stream [m/m], > 0.
    lutz_manning_n : float, optional
        Manning roughness coefficient, > 0.
    lutz_urban_pct, lutz_forest_pct : float, optional
        Urbanized and forested share [%], 0-100, default 0.
    urban_effective_precip_mm : float, optional
        Total effective precipitation [mm], > 0.
    urban_duration_h : float, optional
        Effective rainfall duration [h], > 0.
    urban_fraction : float, optional
        Urbanization index, 0 <= U < 1, default 0.
    timestep_min : float, optional
        Time step [min], > 0, by default 5.
    rainfall_duration_min : float, optional
        Unit rainfall duration D [min]; defaults to ``timestep_min``.
    total_duration_min : float, optional
        Length of the result [min]; defaults to ``5 n K + D``.

    Returns
    -------
    UhResult
        The D-minute unit hydrograph; ``lutz`` holds the intermediate results of the
        Lutz method.

    Raises
    ------
    InvalidParameterError
        If no or several groups of parameters are given, an option of another group
        is given, or a value is invalid (for the Lutz method also when no ``N`` can
        be found for the inputs).
    """
    chosen = select_group(
        {
            "n": n,
            "k_min": k_min,
            "lutz_length_km": lutz_length_km,
            "lutz_centroid_length_km": lutz_centroid_length_km,
            "lutz_slope_m_per_m": lutz_slope_m_per_m,
            "lutz_manning_n": lutz_manning_n,
            "lutz_urban_pct": lutz_urban_pct,
            "lutz_forest_pct": lutz_forest_pct,
            "urban_effective_precip_mm": urban_effective_precip_mm,
            "urban_duration_h": urban_duration_h,
            "urban_fraction": urban_fraction,
        },
        {
            "direct": ("n", "k_min"),
            "lutz": (
                "lutz_length_km",
                "lutz_centroid_length_km",
                "lutz_slope_m_per_m",
                "lutz_manning_n",
            ),
            "urban_regression": ("urban_effective_precip_mm", "urban_duration_h"),
        },
        extra={
            "lutz_urban_pct": "lutz",
            "lutz_forest_pct": "lutz",
            "urban_fraction": "urban_regression",
        },
    )
    cascade: NashIUH
    if chosen == "direct":
        assert n is not None and k_min is not None
        cascade = NashIUH(n=n, k_min=k_min)
    elif chosen == "lutz":
        assert lutz_length_km is not None and lutz_centroid_length_km is not None
        assert lutz_slope_m_per_m is not None and lutz_manning_n is not None
        cascade = NashIUH.from_lutz(
            L_km=lutz_length_km,
            Lc_km=lutz_centroid_length_km,
            slope=lutz_slope_m_per_m,
            manning_n=lutz_manning_n,
            urban_pct=lutz_urban_pct or 0.0,
            forest_pct=lutz_forest_pct or 0.0,
        )
    else:
        assert urban_effective_precip_mm is not None and urban_duration_h is not None
        cascade = NashIUH.from_urban_regression(
            area_km2=area_km2,
            effective_precip_mm=urban_effective_precip_mm,
            duration_h=urban_duration_h,
            urban_fraction=urban_fraction or 0.0,
        )
    duration = timestep_min if rainfall_duration_min is None else rainfall_duration_min
    shape = cascade.to_unit_hydrograph(
        area_km2=area_km2,
        duration_min=duration,
        timestep_min=timestep_min,
        total_duration_min=total_duration_min,
    )
    return UhResult(
        model="nash",
        estimation=chosen,
        area_km2=area_km2,
        timestep_min=timestep_min,
        duration_min=shape.duration_min,
        lag_time_min=cascade.lag_time_min,
        time_to_peak_min=shape.time_to_peak_min,
        peak_discharge_m3s_per_mm=shape.peak_discharge_m3s,
        time_base_min=None,
        parameters={"n": shape.n, "k_min": shape.k_min},
        lutz=cascade.lutz_params,
        times_min=shape.times_min,
        ordinates_m3s_per_mm=shape.ordinates_m3s,
    )


def uh_clark(
    *,
    area_km2: float,
    tc_min: float,
    r_min: float | None = None,
    r_tc_ratio: float | None = None,
    timestep_min: float = 5.0,
    rainfall_duration_min: float | None = None,
    total_duration_min: float | None = None,
) -> UhResult:
    """Clark unit hydrograph (``uh clark``).

    Parameters
    ----------
    area_km2 : float
        Catchment area [km2], > 0.
    tc_min : float
        Time of concentration (translation time) [min], > 0.
    r_min : float, optional
        Storage constant R [min], > 0. Exactly one of ``r_min`` and ``r_tc_ratio``.
    r_tc_ratio : float, optional
        Ratio R / tc, > 0 (``R = r_tc_ratio * tc_min``).
    timestep_min : float, optional
        Time step [min], > 0, by default 5.
    rainfall_duration_min : float, optional
        Unit rainfall duration D [min]; a whole multiple of ``timestep_min``
        (default: ``timestep_min``).
    total_duration_min : float, optional
        Length of the result [min]; defaults to ``tc + 5 R + D``.

    Returns
    -------
    UhResult
        The D-minute unit hydrograph.

    Raises
    ------
    InvalidParameterError
        If both or neither of ``r_min`` and ``r_tc_ratio`` is given, ``D`` is not a
        whole multiple of the time step (``reason = "not_multiple"``), or a value is
        not positive.
    """
    chosen = select_group(
        {"r_min": r_min, "r_tc_ratio": r_tc_ratio},
        {"r_min": ("r_min",), "r_tc_ratio": ("r_tc_ratio",)},
    )
    if chosen == "r_min":
        assert r_min is not None
        reservoir = ClarkIUH(tc_min=tc_min, r_min=r_min)
    else:
        assert r_tc_ratio is not None
        reservoir = ClarkIUH.from_tc_r_ratio(tc_min=tc_min, r_tc_ratio=r_tc_ratio)
    duration = timestep_min if rainfall_duration_min is None else rainfall_duration_min
    steps = duration / timestep_min
    if rainfall_duration_min is not None and (
        round(steps) < 1 or not math.isclose(steps, round(steps), abs_tol=1e-9)
    ):
        raise option_error(
            "rainfall_duration_min",
            "not_multiple",
            f"rainfall_duration_min = {duration:g} must be a whole multiple of "
            f"timestep_min = {timestep_min:g} for the Clark model",
            hint="The S-curve is shifted by a whole number of steps; choose D = k * "
            "timestep_min.",
        )
    shape = reservoir.to_unit_hydrograph(
        area_km2=area_km2,
        duration_min=duration,
        timestep_min=timestep_min,
        total_duration_min=total_duration_min,
    )
    parameters = {"tc_min": reservoir.tc_min, "r_min": reservoir.r_min}
    if r_tc_ratio is not None:
        parameters["r_tc_ratio"] = r_tc_ratio
    return UhResult(
        model="clark",
        estimation="direct" if chosen == "r_min" else chosen,
        area_km2=area_km2,
        timestep_min=timestep_min,
        duration_min=shape.duration_min,
        lag_time_min=reservoir.lag_time_min,
        time_to_peak_min=shape.time_to_peak_min,
        peak_discharge_m3s_per_mm=shape.peak_discharge_m3s,
        time_base_min=None,
        parameters=parameters,
        times_min=shape.times_min,
        ordinates_m3s_per_mm=shape.ordinates_m3s,
    )


def uh_snyder(
    *,
    area_km2: float,
    length_km: float,
    centroid_length_km: float,
    ct: float = 1.5,
    cp: float = 0.6,
    timestep_min: float = 30.0,
    rainfall_duration_min: float | None = None,
    total_duration_min: float | None = None,
) -> UhResult:
    """Snyder synthetic unit hydrograph (``uh snyder``).

    Parameters
    ----------
    area_km2 : float
        Catchment area [km2], > 0.
    length_km : float
        Main stream length L [km], > 0.
    centroid_length_km : float
        Length to the catchment centroid Lc [km], > 0.
    ct : float, optional
        Time coefficient (SI), > 0, by default 1.5.
    cp : float, optional
        Peak coefficient, > 0, by default 0.6.
    timestep_min : float, optional
        Time step [min], > 0, by default 30.
    rainfall_duration_min : float, optional
        Unit rainfall duration D [min]; defaults to the standard duration
        ``tD = tL / 5.5``.
    total_duration_min : float, optional
        Length of the result [min]; defaults to the time base.

    Returns
    -------
    UhResult
        The unit hydrograph with ``derived["standard_duration_min"]`` and
        ``derived["adjusted_lag_time_min"]``.

    Raises
    ------
    InvalidParameterError
        If a parameter is not positive.
    """
    model = SnyderUH(
        area_km2=area_km2,
        L_km=length_km,
        Lc_km=centroid_length_km,
        ct=ct,
        cp=cp,
    )
    shape = model.generate(
        timestep_min=timestep_min,
        duration_min=rainfall_duration_min,
        total_duration_min=total_duration_min,
    )
    return UhResult(
        model="snyder",
        estimation="direct",
        area_km2=area_km2,
        timestep_min=timestep_min,
        duration_min=shape.duration_min,
        lag_time_min=shape.lag_time_min,
        time_to_peak_min=shape.time_to_peak_min,
        peak_discharge_m3s_per_mm=shape.peak_discharge_m3s,
        time_base_min=shape.time_base_min,
        parameters={
            "length_km": length_km,
            "centroid_length_km": centroid_length_km,
            "ct": ct,
            "cp": cp,
        },
        derived={
            "standard_duration_min": shape.standard_duration_min,
            "adjusted_lag_time_min": shape.adjusted_lag_time_min,
        },
        times_min=shape.times_min,
        ordinates_m3s_per_mm=shape.ordinates_m3s,
    )
