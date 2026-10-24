"""Operations of the group ``report``: the Markdown calculation report.

``report generate`` runs the design hydrograph of :mod:`hydrolog.operations.hydrograph`
(:func:`~hydrolog.operations.hydrograph.compute_hydrograph`: the same inputs as
``hydrograph generate``) and documents the whole calculation with
:class:`~hydrolog.reports.HydrologyReportGenerator`. The function is re-exported by
:mod:`hydrolog.operations`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hydrolog._atomic import atomic_output
from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput, capture_warnings
from hydrolog.exceptions import InvalidParameterError, OutputError
from hydrolog.morphometry.watershed_params import WatershedParameters
from hydrolog.operations.hydrograph import (
    HydrographRun,
    UhModel,
    compute_hydrograph,
)
from hydrolog.operations.precip import HietogramType
from hydrolog.operations.scs import Amc
from hydrolog.operations.tc import TcMethod
from hydrolog.reports import HydrologyReportGenerator, ReportConfig

__all__ = ["ReportResult", "report_generate"]

_TC_GIVEN_LABEL = "wartość zadana"
_SERIES_LABEL = "opad zadany szeregiem"
_SECTION_PREFIX = "## "


@dataclass
class ReportResult(JsonResultMixin):
    """The written report and the key numbers it documents.

    Attributes
    ----------
    output_path : str
        Absolute path of the Markdown file.
    size_bytes : int
        Size of the file [bytes].
    sections : list of str
        Titles of the sections of the report, in order.
    watershed_name : str
        Name used in the report header.
    peak_discharge_m3s : float
        Peak discharge of the hydrograph [m3/s].
    time_to_peak_min : float
        Time of the peak from the start of the precipitation [min].
    total_volume_m3 : float
        Direct runoff volume [m3].
    total_precipitation_mm : float
        Total precipitation [mm].
    total_effective_mm : float
        Total effective precipitation [mm].
    runoff_coefficient : float
        Effective over total precipitation [-].
    cn_used : float
        Curve Number used in the computation (after the AMC adjustment).
    """

    output_path: str
    size_bytes: int
    sections: list[str]
    watershed_name: str
    peak_discharge_m3s: float
    time_to_peak_min: float
    total_volume_m3: float
    total_precipitation_mm: float
    total_effective_mm: float
    runoff_coefficient: float
    cn_used: float


# --- inputs of the report generator ---------------------------------------------------


def _watershed_params(parameters: WatershedParameters) -> dict[str, Any]:
    """Build the watershed section inputs of the report generator.

    Only the keys of ``generate_watershed_section`` that the generator can pass on
    (the area and the CN are passed separately).
    """
    indicators = parameters.to_geometry().get_shape_indicators()
    values: dict[str, Any] = {
        "name": parameters.name,
        "perimeter_km": parameters.perimeter_km,
        "length_km": parameters.length_km,
        "width_km": parameters.width_km,
        "elevation_min_m": parameters.elevation_min_m,
        "elevation_max_m": parameters.elevation_max_m,
        "elevation_mean_m": parameters.elevation_mean_m,
        "relief_m": parameters.relief_m,
        "mean_slope_percent": (
            None
            if parameters.mean_slope_m_per_m is None
            else parameters.mean_slope_m_per_m * 100.0
        ),
        "channel_length_km": parameters.channel_length_km,
        "channel_slope_m_per_m": parameters.channel_slope_m_per_m,
        "form_factor": indicators.form_factor,
        "compactness": indicators.compactness_coefficient,
        "circularity": indicators.circularity_ratio,
        "elongation": indicators.elongation_ratio,
    }
    return {key: value for key, value in values.items() if value is not None}


def _uh_params(run: HydrographRun) -> dict[str, Any]:
    """Collect what the report needs of the unit hydrograph model besides its result.

    The values of the model (Nash n and K, Clark R and tc, Snyder Ct and Cp, the
    SCS lag time) are read by the report from the unit hydrograph the hydrograph was
    computed with; the Snyder stream lengths are not part of that result.
    """
    if run.uh_model == "snyder":
        return {
            key: run.uh_params[key] for key in ("L_km", "Lc_km") if key in run.uh_params
        }
    return {}


def _tc_inputs(run: HydrographRun) -> dict[str, Any] | None:
    """Collect the arguments the time of concentration method was fed with.

    Under the names the report section reads (``TcResult.parameters`` already uses
    them; the NRCS slope is given in percent there). ``None`` when the time of
    concentration was given as a value: there is no formula to show.
    """
    if run.tc_parameters is None:
        return None
    inputs: dict[str, Any] = dict(run.tc_parameters)
    if run.tc_method == "nrcs":
        inputs["slope_percent"] = inputs.pop("slope_m_per_m") * 100.0
    if "cn" in inputs:
        inputs["cn"] = _curve_number(inputs["cn"])
    return inputs


def _curve_number(cn: float) -> Any:
    """Format the CN as the report prints it: an integer without a trailing ``.0``.

    The report generator is typed for integer curve numbers; a weighted (fractional)
    CN is passed on as it is.
    """
    return int(cn) if float(cn).is_integer() else cn


def _is_same_file(first: Path, second: Path) -> bool:
    """Whether two paths name the same file (also when one does not exist yet)."""
    try:
        return first.samefile(second)
    except OSError:
        return first.resolve() == second.resolve()


def _check_output(
    output: Path, inputs: dict[str, str | os.PathLike[str] | None]
) -> None:
    """Refuse an output path that is one of the input files."""
    for option, given in inputs.items():
        if given is not None and _is_same_file(output, Path(os.fspath(given))):
            raise InvalidParameterError(
                f"Option 'output' must not be the input file of {option!r}: {output}",
                details={"option": "output", "reason": "conflict", "input": option},
                hint="Give another file name for the report.",
            )


def _write(content: str, output: Path) -> None:
    """Write the report atomically (written aside, then renamed)."""
    try:
        with atomic_output(output) as temporary:
            temporary.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise OutputError(
            f"Cannot write the report {output}: {exc}", details={"path": str(output)}
        ) from exc


# --- operation ------------------------------------------------------------------------


def report_generate(
    *,
    output: str | os.PathLike[str],
    watershed_name: str | None = None,
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
    clark_r_min: float | None = None,
    clark_r_tc_ratio: float | None = None,
    snyder_length_km: float | None = None,
    snyder_centroid_length_km: float | None = None,
    snyder_ct: float | None = None,
    snyder_cp: float | None = None,
    include_formulas: bool = True,
    include_tables: bool = True,
    max_table_rows: int = 50,
) -> OperationOutput:
    """Markdown calculation report of a design hydrograph (``report generate``).

    Computes the design hydrograph exactly as ``hydrograph generate`` does (the
    parameters from ``watershed`` to ``snyder_cp`` are those of
    :func:`hydrolog.operations.hydrograph.hydrograph_generate`) and writes the
    calculation report (:class:`hydrolog.reports.HydrologyReportGenerator`): header,
    watershed parameters (when a watershed is given), time of concentration,
    hyetograph, SCS-CN effective precipitation, unit hydrograph, convolution, result
    characteristics and water balance, with LaTeX formulas and time series tables.

    The report documents the computation that was performed: the unit hydrograph
    section shows the ordinates and the parameters of the model that was used, the
    initial abstraction formula uses ``ia_coefficient`` and the time of concentration
    section shows the arguments the method was fed with (derived from the watershed).

    Parameters
    ----------
    output : str or os.PathLike
        Markdown file to write; missing directories are created, an existing file is
        replaced. It must not be one of the input files.
    watershed_name : str, optional
        Name in the report header; default: ``name`` of the watershed, else
        ``"Zlewnia"``.
    watershed : dict, optional
        Watershed parameters as an object (the keys of ``WatershedParameters``).
    watershed_file : str, optional
        JSON file with the watershed parameters, instead of ``watershed``.
    area_km2, cn : float, optional
        Catchment area [km2] and Curve Number (AMC II) when no watershed is given;
        ``cn`` also overrides the CN of a watershed.
    tc_min : float, optional
        Time of concentration [min]; computed from the watershed when omitted.
    tc_method : str, optional
        Method that computes the time of concentration from the watershed
        (``kirpich`` by default).
    ia_coefficient : float, optional
        Initial abstraction coefficient λ (Ia = λ·S), by default 0.2.
    amc : {"I", "II", "III"}, optional
        Antecedent moisture condition, by default ``"II"``.
    hietogram_type, total_mm, duration_min, alpha, beta, peak_position : optional
        A design hyetograph: its type, total depth [mm], duration [min] and the shape
        parameters of the type.
    values, input_file, value_column : optional
        A precipitation series instead of the design hyetograph: depths [mm] per
        step, inline or from a file column.
    timestep_min : float, optional
        Time step of the hyetograph or series [min], by default 5.
    uh_model : {"scs", "nash", "clark", "snyder"}, optional
        Unit hydrograph model, by default ``"scs"``.
    nash_n, nash_k_min : float, optional
        Nash model: number of reservoirs and storage constant [min].
    clark_r_min, clark_r_tc_ratio : float, optional
        Clark model: storage coefficient [min], or its ratio to the time of
        concentration.
    snyder_length_km, snyder_centroid_length_km, snyder_ct, snyder_cp : float, optional
        Snyder model: stream length and length to the centroid [km] and the
        coefficients Ct and Cp.
    include_formulas : bool, optional
        Include the LaTeX formulas, by default ``True``.
    include_tables : bool, optional
        Include the time series tables and the shape indicators, by default ``True``.
    max_table_rows : int, optional
        Rows of a table before it is abbreviated, at least 1, by default 50.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`ReportResult`; ``files`` lists the report; the
        notices are those of the hydrograph computation.

    Raises
    ------
    InvalidParameterError
        If the inputs are invalid (see ``hydrograph generate``), ``max_table_rows``
        is below 1, or ``output`` is an input file.
    NotFoundError, InputDataError
        If an input file does not exist or cannot be read.
    OutputError
        If the report cannot be written.
    """
    if max_table_rows < 1:
        raise InvalidParameterError(
            f"Option 'max_table_rows': must be >= 1, got {max_table_rows!r}",
            details={
                "option": "max_table_rows",
                "reason": "minimum",
                "minimum": 1,
                "value": str(max_table_rows),
            },
        )
    target = Path(os.fspath(output))
    _check_output(target, {"watershed_file": watershed_file, "input_file": input_file})

    # compute_hydrograph captures warnings itself: it must not run inside our block
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
        clark_r_min=clark_r_min,
        clark_r_tc_ratio=clark_r_tc_ratio,
        snyder_length_km=snyder_length_km,
        snyder_centroid_length_km=snyder_centroid_length_km,
        snyder_ct=snyder_ct,
        snyder_cp=snyder_cp,
    )
    catchment = run.watershed
    title = watershed_name or (catchment.name if catchment else None) or "Zlewnia"
    method_label = run.tc_method or _TC_GIVEN_LABEL
    series_given = run.hietogram_type is None
    generator = HydrologyReportGenerator(
        ReportConfig(
            tc_method=method_label,
            uh_model=run.uh_model,
            hietogram_type=run.hietogram_type or _SERIES_LABEL,
            include_formulas=include_formulas,
            include_tables=include_tables,
            max_table_rows=max_table_rows,
        )
    )
    with capture_warnings() as warned:
        content = generator.generate(
            result=run.result,
            hietogram=run.hietogram,
            watershed_name=title,
            area_km2=run.area_km2,
            cn_ii=_curve_number(run.cn),
            amc=run.amc,
            tc_min=run.tc_min,
            tc_method=method_label,
            watershed_params=_watershed_params(catchment) if catchment else None,
            uh_params=_uh_params(run),
            ia_coefficient=run.ia_coefficient,
            tc_params=_tc_inputs(run),
        )
    # a given precipitation series has no distribution type: its label is not a warning
    kept: list[Notice] = [
        notice
        for notice in warned
        if not (series_given and "ReportConfig.hietogram_type" in notice.text)
    ]
    _write(content, target)
    result = run.result
    summary = ReportResult(
        output_path=os.path.abspath(target),
        size_bytes=target.stat().st_size,
        sections=[
            line[len(_SECTION_PREFIX) :].strip()
            for line in content.splitlines()
            if line.startswith(_SECTION_PREFIX)
        ],
        watershed_name=title,
        peak_discharge_m3s=result.peak_discharge_m3s,
        time_to_peak_min=result.time_to_peak_min,
        total_volume_m3=result.total_volume_m3,
        total_precipitation_mm=result.total_precip_mm,
        total_effective_mm=result.total_effective_mm,
        runoff_coefficient=result.runoff_coefficient,
        cn_used=result.cn_used,
    )
    return OperationOutput(summary, [*run.notices, *kept], files=(target,))
