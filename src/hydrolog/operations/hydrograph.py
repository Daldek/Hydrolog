"""Operations of the group ``hydrograph``: design runoff hydrograph.

:func:`hydrograph_generate` is the ``hydrograph generate`` operation: it resolves the
catchment, the time of concentration, the precipitation and the unit hydrograph model
from JSON-friendly options, runs :class:`~hydrolog.runoff.HydrographGenerator` and
summarizes the outcome. :func:`compute_hydrograph` does the computation and returns
everything the run was built from (:class:`HydrographRun`); ``report generate`` needs
the same.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Literal, cast, get_args

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput, capture_warnings
from hydrolog.catalog.inputs import load_watershed
from hydrolog.catalog.notices import notice
from hydrolog.morphometry.watershed_params import WatershedParameters
from hydrolog.operations._common import (
    check_choice,
    forbid_options,
    option_error,
    option_names,
    require_option,
    select_group,
)
from hydrolog.operations.precip import (
    HietogramType,
    build_hietogram,
    hietogram_notices,
)
from hydrolog.operations.scs import (
    Amc,
    ia_coefficient_notices,
    load_precipitation_depths,
    to_amc,
)
from hydrolog.operations.tc import TC_METHODS, TcMethod, watershed_concentration_time
from hydrolog.precipitation import HietogramResult
from hydrolog.runoff import (
    HydrographGenerator,
    HydrographGeneratorResult,
    LutzCalculationResult,
    NashIUH,
)

__all__ = [
    "NASH_ESTIMATIONS",
    "UH_MODELS",
    "HydrographGenerateResult",
    "HydrographRun",
    "NashEstimation",
    "UhModel",
    "compute_hydrograph",
    "hydrograph_generate",
]

UhModel = Literal["scs", "nash", "clark", "snyder"]
UH_MODELS: tuple[str, ...] = get_args(UhModel)
NashEstimation = Literal["lutz"]
NASH_ESTIMATIONS: tuple[str, ...] = get_args(NashEstimation)

_TC_MODELS = ("scs", "clark")

# The arguments of the unit hydrographs and the options of the command they come
# from: errors and typical-range notices name the option
_MODEL_OPTIONS: dict[str, dict[str, str]] = {
    "nash": {"n": "nash_n", "k_min": "nash_k_min"},
    "snyder": {
        "L_km": "snyder_length_km",
        "Lc_km": "snyder_centroid_length_km",
        "ct": "snyder_ct",
        "cp": "snyder_cp",
    },
}


def _model_options(model: str, clark_r_tc_ratio: float | None) -> dict[str, str]:
    """Argument of the unit hydrograph of ``model`` to the option it comes from."""
    if model == "clark":
        # R/tc is checked from R: the option that gave R
        given = "clark_r_min" if clark_r_tc_ratio is None else "clark_r_tc_ratio"
        return {"r_tc_ratio": given}
    return _MODEL_OPTIONS.get(model, {})


@dataclass
class HydrographRun:
    """Everything a hydrograph computation was made of and produced.

    Plain container (not a JSON result): the library objects are kept as they are so
    that other operations, such as ``report generate``, can reuse them.

    Attributes
    ----------
    result : HydrographGeneratorResult
        Result of :meth:`HydrographGenerator.generate`.
    hietogram : HietogramResult
        The precipitation used. For a precipitation series it is built from the
        series (``times_min`` = end of each step, ``intensities_mm`` = the depths).
    notices : list of Notice
        Non-fatal observations: library warnings and the notices of the operation.
    area_km2 : float
        Catchment area [km2].
    cn : float
        Curve Number for AMC II as given or taken from the watershed (before the
        AMC adjustment).
    amc : str
        ``"I"``, ``"II"`` or ``"III"``.
    ia_coefficient : float
        Initial abstraction ratio.
    tc_min : float or None
        Time of concentration [min] given or computed; ``None`` when the model does
        not need one and none was given.
    tc_method : str or None
        Method that computed ``tc_min`` from the watershed; ``None`` when ``tc_min``
        was given or not needed.
    tc_parameters : dict of str to float or None
        Arguments the method was fed with (``TcResult.parameters``: what
        ``WatershedParameters.calculate_tc`` derived from the watershed); ``None``
        when ``tc_method`` is ``None``.
    uh_model : str
        ``"scs"``, ``"nash"``, ``"clark"`` or ``"snyder"``.
    uh_params : dict
        ``uh_params`` passed to :class:`HydrographGenerator`: Nash ``n``, ``k``,
        ``k_unit`` (``"min"``) and, for an estimate, ``estimated``; Clark ``r``,
        Snyder ``L_km``, ``Lc_km``, ``ct``, ``cp``; empty for SCS.
    hietogram_type : str or None
        ``"block"``, ``"triangular"``, ``"beta"`` or ``"euler_ii"`` when the
        hyetograph was generated, ``None`` for a precipitation series.
    watershed : WatershedParameters or None
        The watershed parameters when a watershed was given, with the ``cn`` option
        applied (the ``cn`` the runoff and the NRCS time of concentration used).
    nash_estimation : str or None
        How Nash's ``n`` and ``K`` were estimated from the watershed (``"lutz"``);
        ``None`` when they were given or the model is not Nash.
    lutz : LutzCalculationResult or None
        The steps of Lutz's estimation (``NashIUH.lutz_params``) when
        ``nash_estimation`` is ``"lutz"``, else ``None``.
    """

    result: HydrographGeneratorResult
    hietogram: HietogramResult
    notices: list[Notice]
    area_km2: float
    cn: float
    amc: str
    ia_coefficient: float
    tc_min: float | None
    tc_method: str | None
    uh_model: str
    uh_params: dict[str, Any]
    hietogram_type: str | None
    watershed: WatershedParameters | None
    tc_parameters: dict[str, float] | None = None
    nash_estimation: str | None = None
    lutz: LutzCalculationResult | None = None


@dataclass
class HydrographGenerateResult(JsonResultMixin):
    """Summary and series of a design hydrograph.

    Attributes
    ----------
    peak_discharge_m3s : float
        Peak discharge [m3/s].
    time_to_peak_min : float
        Time of the peak from the start of the precipitation [min].
    total_volume_m3 : float
        Direct runoff volume [m3].
    runoff_coefficient : float
        Effective over total precipitation (0 without precipitation).
    total_precipitation_mm : float
        Total precipitation [mm].
    total_effective_mm : float
        Total effective precipitation [mm].
    retention_mm : float
        Maximum retention S [mm].
    initial_abstraction_mm : float
        Initial abstraction Ia [mm].
    cn : float
        Curve Number for AMC II as given.
    cn_adjusted : float
        CN after the AMC adjustment (what the computation used).
    amc : str
        Antecedent moisture condition.
    ia_coefficient : float
        Initial abstraction ratio.
    area_km2 : float
        Catchment area [km2].
    watershed_name : str or None
        Name of the watershed, if it has one.
    tc_min : float or None
        Time of concentration [min] (``None`` when not needed and not given).
    tc_method : str or None
        Method that computed ``tc_min`` from the watershed.
    hietogram_type : str or None
        Type of the generated hyetograph; ``None`` for a precipitation series.
    uh_model : str
        Unit hydrograph model.
    nash_estimation : str or None
        How Nash's n and K were estimated from the watershed (``"lutz"``);
        ``None`` when they were given or the model is not Nash.
    uh_parameters : dict of str to float
        Model parameters (names as in the ``uh`` commands); for Nash the estimated
        ``n`` and ``k_min`` when ``nash_estimation`` is set.
    uh_time_to_peak_min : float
        Time to peak of the unit hydrograph [min]. For the ``snyder`` model it is
        tpR of the unit hydrograph for the duration of the time step.
    uh_peak_discharge_m3s_per_mm : float
        Peak ordinate of the unit hydrograph [m3/s per mm]. For the ``snyder``
        model the unit hydrograph is the one for the duration of the time step.
    timestep_min : float
        Time step [min].
    duration_min : float
        Time of the last ordinate of the hydrograph [min].
    times_min : numpy.ndarray
        Time of each discharge ordinate [min].
    discharge_m3s : numpy.ndarray
        Direct runoff discharge [m3/s].
    precipitation_mm : numpy.ndarray
        Precipitation depth of each input step [mm].
    effective_precipitation_mm : numpy.ndarray
        Effective precipitation of each input step [mm].
    uh_times_min : numpy.ndarray
        Time of each ordinate of the unit hydrograph [min]: 0, ``timestep_min``,
        2 ``timestep_min``... It is the unit hydrograph that the convolution used
        (for ``snyder`` the one for the duration of the time step).
    uh_discharge_m3s_per_mm : numpy.ndarray
        Ordinates of that unit hydrograph [m3/s per mm]: ``discharge_m3s`` is the
        discrete convolution of ``effective_precipitation_mm`` with them. Their
        largest value is ``uh_peak_discharge_m3s_per_mm`` at
        ``uh_time_to_peak_min`` for ``nash`` and ``clark``; the ``scs`` and
        ``snyder`` peak is the analytic one, which may fall between two ordinates.
    """

    peak_discharge_m3s: float
    time_to_peak_min: float
    total_volume_m3: float
    runoff_coefficient: float
    total_precipitation_mm: float
    total_effective_mm: float
    retention_mm: float
    initial_abstraction_mm: float
    cn: float
    cn_adjusted: float
    amc: str
    ia_coefficient: float
    area_km2: float
    watershed_name: str | None
    tc_min: float | None
    tc_method: str | None
    hietogram_type: str | None
    uh_model: str
    nash_estimation: str | None
    uh_parameters: dict[str, float]
    uh_time_to_peak_min: float
    uh_peak_discharge_m3s_per_mm: float
    timestep_min: float
    duration_min: float
    times_min: NDArray[np.float64] = field(default_factory=lambda: np.empty(0))
    discharge_m3s: NDArray[np.float64] = field(default_factory=lambda: np.empty(0))
    precipitation_mm: NDArray[np.float64] = field(default_factory=lambda: np.empty(0))
    effective_precipitation_mm: NDArray[np.float64] = field(
        default_factory=lambda: np.empty(0)
    )
    uh_times_min: NDArray[np.float64] = field(default_factory=lambda: np.empty(0))
    uh_discharge_m3s_per_mm: NDArray[np.float64] = field(
        default_factory=lambda: np.empty(0)
    )


def _uh_parameters(
    model: str,
    tc_min: float | None,
    *,
    nash_n: float | None,
    nash_k_min: float | None,
    estimate: NashIUH | None,
    clark_r_min: float | None,
    clark_r_tc_ratio: float | None,
    snyder_length_km: float | None,
    snyder_centroid_length_km: float | None,
    snyder_ct: float | None,
    snyder_cp: float | None,
) -> dict[str, Any]:
    """``uh_params`` of :class:`HydrographGenerator` for the chosen model.

    ``estimate`` is the Nash cascade that ``nash_estimation`` estimated from the
    watershed, else ``None``.
    """
    given = {
        "nash": {"nash_n": nash_n, "nash_k_min": nash_k_min},
        "clark": {"clark_r_min": clark_r_min, "clark_r_tc_ratio": clark_r_tc_ratio},
        "snyder": {
            "snyder_length_km": snyder_length_km,
            "snyder_centroid_length_km": snyder_centroid_length_km,
            "snyder_ct": snyder_ct,
            "snyder_cp": snyder_cp,
        },
    }
    for other, options in given.items():
        if other != model:
            forbid_options(
                options,
                context=f"uh_model is {model!r}",
                hint=f"These options belong to uh_model {other!r}.",
            )
    when = f"uh_model is {model!r}"
    if model == "nash":
        if estimate is not None:
            # an estimate: the generator does not check it against the ranges of
            # given n and K
            return {
                "n": estimate.n,
                "k": estimate.k_min,
                "k_unit": "min",
                "estimated": True,
            }
        if nash_n is None:
            raise option_error(
                "nash_n",
                "required",
                f"Option 'nash_n' is required when {when}, unless nash_estimation "
                "is given",
                hint="Give nash_n and nash_k_min, or nash_estimation (lutz) to "
                "estimate them from the watershed.",
            )
        return {
            "n": nash_n,
            "k": require_option("nash_k_min", nash_k_min, when=when),
            "k_unit": "min",
        }
    if model == "clark":
        chosen = select_group(
            {"clark_r_min": clark_r_min, "clark_r_tc_ratio": clark_r_tc_ratio},
            {"r_min": ("clark_r_min",), "r_tc_ratio": ("clark_r_tc_ratio",)},
        )
        if chosen == "r_min":
            return {"r": clark_r_min}
        assert tc_min is not None and clark_r_tc_ratio is not None
        # R = R/tc * tc (ClarkIUH.from_tc_r_ratio); the generator's ClarkIUH
        # checks R/tc against its typical range
        return {"r": clark_r_tc_ratio * tc_min}
    if model == "snyder":
        return {
            "L_km": require_option("snyder_length_km", snyder_length_km, when=when),
            "Lc_km": require_option(
                "snyder_centroid_length_km", snyder_centroid_length_km, when=when
            ),
            "ct": 1.5 if snyder_ct is None else snyder_ct,
            "cp": 0.6 if snyder_cp is None else snyder_cp,
        }
    return {}


def _public_uh_parameters(
    model: str, uh_params: dict[str, Any], tc_min: float | None
) -> dict[str, float]:
    """Model parameters under the names of the ``uh`` commands."""
    if model == "nash":
        return {"n": uh_params["n"], "k_min": uh_params["k"]}
    if model == "clark":
        assert tc_min is not None
        return {"tc_min": tc_min, "r_min": uh_params["r"]}
    if model == "snyder":
        return {
            "length_km": uh_params["L_km"],
            "centroid_length_km": uh_params["Lc_km"],
            "ct": uh_params["ct"],
            "cp": uh_params["cp"],
        }
    assert tc_min is not None
    return {"tc_min": tc_min}


def compute_hydrograph(
    *,
    watershed: dict[str, Any] | None = None,
    watershed_file: str | None = None,
    area_km2: float | None = None,
    cn: float | None = None,
    tc_min: float | None = None,
    tc_method: TcMethod | None = None,
    ia_coefficient: float = 0.2,
    amc: Amc = "II",
    hietogram_type: HietogramType | None = None,
    total_mm: float | None = None,
    duration_min: float | None = None,
    alpha: float | None = None,
    beta: float | None = None,
    peak_position: float | None = None,
    values: list[float] | None = None,
    input_file: str | None = None,
    value_column: str | None = None,
    timestep_min: float = 5.0,
    uh_model: UhModel = "scs",
    nash_n: float | None = None,
    nash_k_min: float | None = None,
    nash_estimation: NashEstimation | None = None,
    clark_r_min: float | None = None,
    clark_r_tc_ratio: float | None = None,
    snyder_length_km: float | None = None,
    snyder_centroid_length_km: float | None = None,
    snyder_ct: float | None = None,
    snyder_cp: float | None = None,
) -> HydrographRun:
    """Compute a design hydrograph and return the whole run.

    The parameters are those of :func:`hydrograph_generate`, which documents them.
    Library warnings are captured inside (a ``capture_warnings`` block holds a
    non-reentrant lock: do not call this function from inside another one).

    Returns
    -------
    HydrographRun
        The library result with the inputs it was made from and the notices.

    Raises
    ------
    InvalidParameterError
        If the combination of options is wrong or a value is invalid, see
        :func:`hydrograph_generate`.
    NotFoundError
        If ``watershed_file`` or ``input_file`` does not exist.
    InputDataError
        If a file is malformed.
    """
    model = check_choice("uh_model", uh_model, UH_MODELS)
    moisture = to_amc(amc)
    if tc_method is not None:
        check_choice("tc_method", tc_method, TC_METHODS)
    if nash_estimation is not None:
        check_choice("nash_estimation", nash_estimation, NASH_ESTIMATIONS)

    source = select_group(
        {
            "watershed": watershed,
            "watershed_file": watershed_file,
            "area_km2": area_km2,
            "cn": cn,
        },
        {
            "watershed": ("watershed",),
            "watershed_file": ("watershed_file",),
            "direct": ("area_km2", "cn"),
        },
        extra={"cn": ("watershed", "watershed_file")},
    )
    catchment: WatershedParameters | None = None
    if source == "direct":
        assert area_km2 is not None and cn is not None
        area, curve_number = area_km2, cn
    else:
        catchment = load_watershed(watershed=watershed, watershed_file=watershed_file)
        if cn is not None:
            # The CN given next to a watershed is the CN of the catchment for the
            # whole computation. In particular the retention S of the NRCS lag
            # equation (NEH 630, chapter 15, eq. 15-4) must come from the CN the
            # runoff is computed with, not from the one in the file.
            catchment = replace(catchment, cn=cast(int, cn))
        area = catchment.area_km2
        if catchment.cn is None:
            raise option_error(
                "cn",
                "required",
                "Option 'cn' is required: the watershed has no 'cn'",
                hint="Give cn or add it to the watershed parameters.",
            )
        curve_number = catchment.cn

    needs_tc = model in _TC_MODELS
    if tc_method is not None and catchment is None:
        raise option_error(
            "tc_method",
            "not_applicable",
            "Option 'tc_method' computes tc from a watershed, but none was given",
            hint="Give a watershed (watershed or watershed_file), or tc_min.",
        )
    if tc_method is not None and tc_min is not None:
        raise option_error(
            "tc_method",
            "conflict",
            "Give tc_min or tc_method, not both",
            hint="tc_method computes tc from the watershed; tc_min is a value.",
        )
    if needs_tc and tc_min is None and catchment is None:
        raise option_error(
            "tc_min",
            "required",
            f"Option 'tc_min' is required for the {model} model unless a watershed "
            "is given",
            hint="Give tc_min, or a watershed (with tc_method) to compute it.",
        )
    if nash_estimation is not None:
        if model != "nash":
            raise option_error(
                "nash_estimation",
                "not_applicable",
                f"Option 'nash_estimation' does not apply when uh_model is {model!r}",
                hint="It estimates the n and K of uh_model 'nash'.",
            )
        if nash_n is not None or nash_k_min is not None:
            raise option_error(
                "nash_estimation",
                "conflict",
                "Give nash_n and nash_k_min or nash_estimation, not both",
                hint="nash_estimation estimates n and K from the watershed; nash_n "
                "and nash_k_min are values.",
            )
        if catchment is None:
            raise option_error(
                "nash_estimation",
                "not_applicable",
                "Option 'nash_estimation' estimates n and K from a watershed, but "
                "none was given",
                hint="Give a watershed (watershed or watershed_file), or nash_n and "
                "nash_k_min.",
            )

    chosen = select_group(
        {
            "hietogram_type": hietogram_type,
            "total_mm": total_mm,
            "duration_min": duration_min,
            "alpha": alpha,
            "beta": beta,
            "peak_position": peak_position,
            "values": values,
            "input_file": input_file,
            "value_column": value_column,
        },
        {
            "design": ("hietogram_type", "total_mm", "duration_min"),
            "values": ("values",),
            "file": ("input_file",),
        },
        extra={
            "alpha": "design",
            "beta": "design",
            "peak_position": "design",
            "value_column": "file",
        },
    )

    notices: list[Notice] = []
    tc: float | None = tc_min
    method_used: str | None = None
    tc_parameters: dict[str, float] | None = None
    estimate: NashIUH | None = None
    with capture_warnings() as warned:
        if tc is None and catchment is not None and (needs_tc or tc_method):
            method_used = tc_method or "kirpich"
            concentration = watershed_concentration_time(catchment, method_used)
            tc = concentration.tc_min
            tc_parameters = concentration.parameters
        if tc is not None and not needs_tc:
            notices.append(notice("tc_not_used", tc_min=tc, uh_model=model))
        if nash_estimation is not None:
            assert catchment is not None
            # Lutz from the fields its source defines (NASH_INPUTS); an estimate is
            # never checked against the ranges of given n and K, only its area is
            estimate = NashIUH.from_lutz(**catchment.nash_parameters(nash_estimation))
        uh_params = _uh_parameters(
            model,
            tc,
            nash_n=nash_n,
            nash_k_min=nash_k_min,
            estimate=estimate,
            clark_r_min=clark_r_min,
            clark_r_tc_ratio=clark_r_tc_ratio,
            snyder_length_km=snyder_length_km,
            snyder_centroid_length_km=snyder_centroid_length_km,
            snyder_ct=snyder_ct,
            snyder_cp=snyder_cp,
        )
        if chosen == "design":
            assert (
                hietogram_type is not None
                and total_mm is not None
                and duration_min is not None
            )
            hietogram, _ = build_hietogram(
                hietogram_type,
                total_mm,
                duration_min,
                timestep_min,
                alpha=alpha,
                beta=beta,
                peak_position=peak_position,
            )
            notices.extend(hietogram_notices(hietogram))
            generated: str | None = hietogram_type
        else:
            depths = load_precipitation_depths(
                values=values, input_file=input_file, value_column=value_column
            )
            steps = len(depths)
            hietogram = HietogramResult(
                times_min=np.arange(1, steps + 1, dtype=np.float64) * timestep_min,
                intensities_mm=depths,
                total_mm=float(np.sum(depths)),
                duration_min=steps * timestep_min,
                timestep_min=timestep_min,
            )
            generated = None
        with option_names(_model_options(model, clark_r_tc_ratio)):
            generator = HydrographGenerator(
                area_km2=area,
                cn=cast(int, curve_number),
                tc_min=tc if needs_tc else None,
                ia_coefficient=ia_coefficient,
                uh_model=model,
                uh_params=uh_params,
            )
            result = generator.generate(hietogram, amc=moisture)
    notices.extend(ia_coefficient_notices(ia_coefficient))
    return HydrographRun(
        result=result,
        hietogram=hietogram,
        notices=[*warned, *notices],
        area_km2=area,
        cn=float(curve_number),
        amc=amc,
        ia_coefficient=ia_coefficient,
        tc_min=tc,
        tc_method=method_used,
        uh_model=model,
        uh_params=uh_params,
        hietogram_type=generated,
        watershed=catchment,
        tc_parameters=tc_parameters,
        nash_estimation=nash_estimation,
        lutz=None if estimate is None else estimate.lutz_params,
    )


def hydrograph_generate(
    *,
    watershed: dict[str, Any] | None = None,
    watershed_file: str | None = None,
    area_km2: float | None = None,
    cn: float | None = None,
    tc_min: float | None = None,
    tc_method: TcMethod | None = None,
    ia_coefficient: float = 0.2,
    amc: Amc = "II",
    hietogram_type: HietogramType | None = None,
    total_mm: float | None = None,
    duration_min: float | None = None,
    alpha: float | None = None,
    beta: float | None = None,
    peak_position: float | None = None,
    values: list[float] | None = None,
    input_file: str | None = None,
    value_column: str | None = None,
    timestep_min: float = 5.0,
    uh_model: UhModel = "scs",
    nash_n: float | None = None,
    nash_k_min: float | None = None,
    nash_estimation: NashEstimation | None = None,
    clark_r_min: float | None = None,
    clark_r_tc_ratio: float | None = None,
    snyder_length_km: float | None = None,
    snyder_centroid_length_km: float | None = None,
    snyder_ct: float | None = None,
    snyder_cp: float | None = None,
) -> OperationOutput:
    """Design direct-runoff hydrograph of a catchment (``hydrograph generate``).

    Exactly one catchment source is required: ``watershed``, ``watershed_file`` or
    ``area_km2`` with ``cn``; and exactly one precipitation source: a design
    hyetograph (``hietogram_type``, ``total_mm``, ``duration_min``) or a series
    (``values`` or ``input_file``).

    Parameters
    ----------
    watershed : dict, optional
        Inline ``WatershedParameters`` object (area, ``cn``, data for tc). Only
        ``area_km2`` is required; the fields ``tc_method`` needs are required
        when tc is computed from them.
    watershed_file : str, optional
        JSON file in the ``WatershedParameters.to_json()`` format.
    area_km2 : float, optional
        Catchment area [km2], > 0; with ``cn``, instead of a watershed.
    cn : float, optional
        Curve Number for AMC II, 1-100; with ``area_km2``, or next to a watershed to
        override its ``cn`` (required when the watershed has none). The override
        is the CN of the whole computation, also of the retention S in the lag
        equation of ``tc_method="nrcs"``.
    tc_min : float, optional
        Time of concentration [min], > 0. Required by the ``scs`` and ``clark``
        models unless a watershed lets ``tc_method`` compute it.
    tc_method : str, optional
        Method for tc from the watershed when ``tc_min`` is not given (one of
        ``kirpich``, ``nrcs``, ``giandotti``, ``faa``, ``kerby``, ``kerby_kirpich``;
        default ``kirpich`` for models that need tc).
    ia_coefficient : float, optional
        Initial abstraction ratio, 0 < ratio <= 1, by default 0.2.
    amc : {"I", "II", "III"}, optional
        Antecedent moisture condition, by default ``"II"``.
    hietogram_type : {"block", "triangular", "beta", "euler_ii"}, optional
        Design hyetograph type (see :func:`~hydrolog.operations.precip_hietogram`).
    total_mm : float, optional
        Total precipitation [mm], > 0.
    duration_min : float, optional
        Precipitation duration [min], > 0.
    alpha, beta : float, optional
        Parameters of the ``beta`` hyetograph.
    peak_position : float, optional
        Peak position of the ``triangular`` and ``euler_ii`` hyetographs.
    values : list of float, optional
        Precipitation depths per step [mm], each >= 0.
    input_file : str, optional
        CSV or JSON file with the depths per step.
    value_column : str, optional
        Column of ``input_file`` with the depths.
    timestep_min : float, optional
        Time step [min], > 0, by default 5.
    uh_model : {"scs", "nash", "clark", "snyder"}, optional
        Unit hydrograph model, by default ``"scs"``.
    nash_n, nash_k_min : float, optional
        Nash parameters n and K [min] (for ``nash`` both, or ``nash_estimation``).
    nash_estimation : {"lutz"}, optional
        For ``nash``: estimate n and K from the watershed instead of giving them;
        ``lutz`` is the Lutz method (Lutz 1984, after KZGW 2017,
        :meth:`~hydrolog.runoff.NashIUH.from_lutz`) with the fields
        :meth:`~hydrolog.morphometry.WatershedParameters.nash_parameters` takes:
        L and J of the longest flow path (``flow_path_length_km``,
        ``flow_path_slope_m_per_m``), ``Lc_km``, ``manning_n``, ``urban_pct`` and
        ``forest_pct`` (0 when not set). The estimate is not checked against the
        typical ranges of given n and K; the area is checked against Lutz's.
    clark_r_min : float, optional
        Clark storage constant R [min]; exactly one of ``clark_r_min`` and
        ``clark_r_tc_ratio`` for ``clark``.
    clark_r_tc_ratio : float, optional
        Clark ratio R / tc.
    snyder_length_km, snyder_centroid_length_km : float, optional
        Snyder L and Lc [km] (required for ``snyder``).
    snyder_ct, snyder_cp : float, optional
        Snyder coefficients, defaults 1.5 and 0.6. The unit hydrograph is that
        for rainfall of the duration of the time step (adjusted lag tLR, time to
        peak tpR and peak qpR), as the convolution requires.

    Returns
    -------
    OperationOutput
        :class:`HydrographGenerateResult` with the notices: library warnings about
        parameters outside the typical range (``outside_typical_range``, with
        ``details.field`` the input the value came from: the field of the
        watershed for a tc formula or Lutz's area, else the option, e.g.
        ``snyder_ct``), a non-standard ``ia_coefficient``, a duration that is not
        a multiple of the step, an unused tc. The result holds the ordinates of the
        unit hydrograph that was convolved (``uh_times_min``,
        ``uh_discharge_m3s_per_mm``) next to the hydrograph, and with
        ``nash_estimation`` the estimated n and K in ``uh_parameters``.

    Raises
    ------
    InvalidParameterError
        If the catchment or precipitation source is ambiguous or incomplete
        (``reason = "one_of"``), an option of another hyetograph type or model is
        given (``reason = "not_applicable"``, also ``nash_estimation`` without a
        watershed), ``tc_min`` with ``tc_method`` or ``nash_estimation`` with
        ``nash_n`` or ``nash_k_min`` (``reason = "conflict"``), ``cn``, ``tc_min``
        or a model parameter is missing (``reason = "required"``; Nash without n
        and K or an estimation on ``nash_n``), a watershed lacks the fields of
        ``tc_method`` or ``nash_estimation`` (``reason = "missing_field"``,
        ``details.option`` the first missing field, ``details.missing`` all of
        them; for an estimation also ``details.method``), or a value is invalid
        (``details.option`` the option or the field of the watershed; Lutz's
        ``Lc_km`` longer than ``flow_path_length_km`` is ``"maximum"``).
    NotFoundError
        If ``watershed_file`` or ``input_file`` does not exist.
    InputDataError
        If a file is malformed or a precipitation value is missing or negative.
    """
    run = compute_hydrograph(
        watershed=watershed,
        watershed_file=watershed_file,
        area_km2=area_km2,
        cn=cn,
        tc_min=tc_min,
        tc_method=tc_method,
        ia_coefficient=ia_coefficient,
        amc=amc,
        hietogram_type=hietogram_type,
        total_mm=total_mm,
        duration_min=duration_min,
        alpha=alpha,
        beta=beta,
        peak_position=peak_position,
        values=values,
        input_file=input_file,
        value_column=value_column,
        timestep_min=timestep_min,
        uh_model=uh_model,
        nash_n=nash_n,
        nash_k_min=nash_k_min,
        nash_estimation=nash_estimation,
        clark_r_min=clark_r_min,
        clark_r_tc_ratio=clark_r_tc_ratio,
        snyder_length_km=snyder_length_km,
        snyder_centroid_length_km=snyder_centroid_length_km,
        snyder_ct=snyder_ct,
        snyder_cp=snyder_cp,
    )
    generated = run.result
    hydrograph = generated.hydrograph
    unit = generated.unit_hydrograph_result
    assert unit is not None  # HydrographGenerator.generate always sets it
    summary = HydrographGenerateResult(
        peak_discharge_m3s=hydrograph.peak_discharge_m3s,
        time_to_peak_min=hydrograph.time_to_peak_min,
        total_volume_m3=hydrograph.total_volume_m3,
        runoff_coefficient=generated.runoff_coefficient,
        total_precipitation_mm=generated.total_precip_mm,
        total_effective_mm=generated.total_effective_mm,
        retention_mm=generated.retention_mm,
        initial_abstraction_mm=generated.initial_abstraction_mm,
        cn=run.cn,
        cn_adjusted=generated.cn_used,
        amc=run.amc,
        ia_coefficient=run.ia_coefficient,
        area_km2=run.area_km2,
        watershed_name=None if run.watershed is None else run.watershed.name,
        tc_min=run.tc_min,
        tc_method=run.tc_method,
        hietogram_type=run.hietogram_type,
        uh_model=run.uh_model,
        nash_estimation=run.nash_estimation,
        uh_parameters=_public_uh_parameters(run.uh_model, run.uh_params, run.tc_min),
        uh_time_to_peak_min=unit.time_to_peak_min,
        uh_peak_discharge_m3s_per_mm=unit.peak_discharge_m3s,
        timestep_min=hydrograph.timestep_min,
        duration_min=hydrograph.duration_min,
        times_min=hydrograph.times_min,
        discharge_m3s=hydrograph.discharge_m3s,
        precipitation_mm=run.hietogram.intensities_mm,
        effective_precipitation_mm=generated.effective_precip_mm,
        uh_times_min=np.asarray(unit.times_min, dtype=np.float64),
        uh_discharge_m3s_per_mm=np.asarray(unit.ordinates_m3s, dtype=np.float64),
    )
    return OperationOutput(summary, run.notices)
