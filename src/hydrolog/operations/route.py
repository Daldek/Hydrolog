"""Operations of the group ``route``: lumped hydrologic flood routing (ADR-0007).

Every command of the group takes a discharge hydrograph at a regular time step
(:func:`~hydrolog.catalog.inputs.load_hydrograph`), routes it through one element of
:mod:`hydrolog.routing` and returns the same :class:`RouteResult`: the parameters the
model used, peaks, volumes, the storage at both ends, the balance error and the
extension of the time axis (ADR-0008). The outflow series is in the result unless
``output`` names a file; the file holds the same series as a hydrograph table
(``time_min``, ``discharge_m3s``), a valid input of every ``route`` command.

Without ``output`` a command has nothing to plan, so ``check`` computes as usual: a
read-only MCP server, which runs every writing tool with ``check``, can still route.

:func:`route_network` routes the hydrographs of many subcatchments down a river network
(the document ``hydrolog-network/1``, read by :mod:`hydrolog.operations._network_input`)
and returns a :class:`NetworkRouteResult`, the summary of every node. The hydrograph of
each node is in the result or, with ``output_dir``, in its own table ``<id>.csv``; the
tables are written through a staging directory (DEV-19.7, ADR-0010).
The functions are re-exported by :mod:`hydrolog.operations`.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from hydrolog._atomic import atomic_output, staging_directory
from hydrolog._serialization import JsonResultMixin, to_jsonable
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.catalog.inputs import load_hydrograph, load_rating
from hydrolog.exceptions import InvalidParameterError, OutputError
from hydrolog.operations._network_input import load_network
from hydrolog.operations._outputs import (
    conflict_error,
    plan_directory,
    plan_output,
    plan_outputs,
    refuse_input_as_output,
)
from hydrolog.routing import (
    CascadeReach,
    LagReach,
    LevelPoolReach,
    MuskingumCungeReach,
    MuskingumReach,
    Reach,
    RoutingNetwork,
    RoutingResult,
)

__all__ = [
    "NetworkRouteResult",
    "RouteResult",
    "route_cascade",
    "route_lag",
    "route_level_pool",
    "route_muskingum",
    "route_muskingum_cunge",
    "route_network",
]


@dataclass
class RouteResult(JsonResultMixin):
    """Outcome of routing a hydrograph through one element.

    Volumes are trapezoid sums. The inflow ones are those of the hydrograph as given;
    the outflow volume is that of the outflow on the extended time axis, and the
    balance error compares it with the inflow held at its last value over the
    extension.

    Attributes
    ----------
    model : str
        ``"lag"``, ``"muskingum"``...
    parameters : dict of str to float
        The parameters the model used, including the ones it derived (lag in steps,
        coefficients, number of sub-reaches...).
    timestep_min : float
        Time step of the hydrograph [min].
    extension_min : float
        Time added after the last inflow ordinate [min]; 0 when none was needed.
    inflow_peak_m3s, inflow_time_to_peak_min : float
        Peak of the inflow [m3/s] and its time [min].
    outflow_peak_m3s, outflow_time_to_peak_min : float
        Peak of the outflow [m3/s] and its time [min].
    peak_attenuation_pct : float
        Reduction of the peak, in percent of the inflow peak.
    peak_delay_min : float
        Time of the outflow peak minus time of the inflow peak [min].
    inflow_volume_m3, outflow_volume_m3 : float
        Volume of the inflow and of the outflow [m3].
    storage_start_m3, storage_end_m3 : float
        Water stored in the element at the first and at the last ordinate [m3].
    balance_error_m3 : float
        Inflow volume - outflow volume - change of storage [m3]; zero to rounding
        unless the scheme ran on a refined time step.
    times_min : numpy.ndarray or None
        Times of the outflow ordinates [min]; ``None`` when ``output`` was given.
    outflow_m3s : numpy.ndarray or None
        Outflow ordinates [m3/s]; ``None`` when ``output`` was given.
    """

    model: str
    parameters: dict[str, float]
    timestep_min: float
    extension_min: float
    inflow_peak_m3s: float
    inflow_time_to_peak_min: float
    outflow_peak_m3s: float
    outflow_time_to_peak_min: float
    peak_attenuation_pct: float
    peak_delay_min: float
    inflow_volume_m3: float
    outflow_volume_m3: float
    storage_start_m3: float
    storage_end_m3: float
    balance_error_m3: float
    times_min: NDArray[np.float64] | None = None
    outflow_m3s: NDArray[np.float64] | None = None

    @classmethod
    def from_routing(cls, run: RoutingResult, *, with_series: bool) -> RouteResult:
        """Summarize a library result.

        Parameters
        ----------
        run : RoutingResult
            What :meth:`hydrolog.routing.Reach.route` returned.
        with_series : bool
            Put the outflow series into the result (no ``output`` file).

        Returns
        -------
        RouteResult
            The summary.
        """
        return cls(
            model=run.model,
            parameters=run.parameters,
            timestep_min=run.inflow.timestep_min,
            extension_min=run.extension_min,
            inflow_peak_m3s=run.inflow.peak_discharge_m3s,
            inflow_time_to_peak_min=run.inflow.time_to_peak_min,
            outflow_peak_m3s=run.outflow.peak_discharge_m3s,
            outflow_time_to_peak_min=run.outflow.time_to_peak_min,
            peak_attenuation_pct=run.peak_attenuation_pct,
            peak_delay_min=run.peak_delay_min,
            inflow_volume_m3=run.volume_in_m3,
            outflow_volume_m3=run.volume_out_m3,
            storage_start_m3=run.storage_start_m3,
            storage_end_m3=run.storage_end_m3,
            balance_error_m3=run.balance_error_m3,
            times_min=run.outflow.times_min if with_series else None,
            outflow_m3s=run.outflow.discharge_m3s if with_series else None,
        )


@dataclass
class NetworkRouteResult(JsonResultMixin):
    """Outcome of routing a network.

    Attributes
    ----------
    name : str or None
        The name of the network, when its document has one.
    timestep_min : float
        The time step of every hydrograph of the network [min].
    outlet : str
        The id of the outlet node.
    order : list of str
        The ids in the order of evaluation: headwaters first, the smallest id first
        among the nodes that are ready, whatever the order of the document.
    nodes : list of dict
        One entry per node, in that order. Every entry has ``id``, ``type``, ``from``
        (the ids of the nodes upstream), and ``peak_m3s``, ``time_to_peak_min`` and
        ``volume_m3`` of the hydrograph that leaves the node (a trapezoid sum). The
        entry of a ``reach`` or ``reservoir`` adds what :class:`RouteResult` reports of
        its run: ``model``, ``parameters``, ``peak_attenuation_pct``,
        ``peak_delay_min`` and ``balance_error_m3``. Without ``output_dir`` the entry
        of a selected node adds its hydrograph as ``times_min`` [min] and
        ``discharge_m3s`` [m3/s].
    """

    name: str | None
    timestep_min: float
    outlet: str
    order: list[str]
    nodes: list[dict[str, Any]]


PAGE_CHARS = 20_000
"""Characters of a result that a client reads whole: the default page of DOC-1.7."""


def _json_chars(result: object) -> int:
    """Return the length of ``result`` as the single-line JSON the envelope writes."""
    return len(json.dumps(to_jsonable(result), ensure_ascii=False, allow_nan=False))


def _write_table(text: str, output: Path) -> None:
    """Write the hydrograph table atomically (written aside, then renamed)."""
    try:
        with atomic_output(output) as temporary:
            temporary.write_text(text, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise OutputError(
            f"Cannot write the outflow hydrograph {output}: {exc}",
            details={"path": str(output), "reason": "output_unwritable"},
        ) from exc


def _write_directory(
    directory: Path, tables: Mapping[str, str], *, force: bool
) -> None:
    """Write the tables into ``directory`` through a staging directory (DEV-19.7).

    Every table is written into the staging directory of
    :func:`~hydrolog._atomic.staging_directory` first, so a failure before the moves
    leaves no partial target. The targets are planned again just before the moves: a
    file that appeared during the computation is a conflict, not silently replaced. A
    move is ``os.replace`` on one file system, one file at a time; the staging
    directory is removed whatever the outcome.
    """
    placed: list[str] = []
    try:
        with staging_directory(directory) as staging:
            for name, text in tables.items():
                (staging / name).write_text(text, encoding="utf-8", newline="\n")
            again = plan_directory("output_dir", directory, tables, force=force)
            if (error := conflict_error(again)) is not None:
                raise error
            for name in tables:
                os.replace(staging / name, directory / name)
                placed.append(str(directory / name))
    except OSError as exc:
        details: dict[str, Any] = {
            "path": str(directory),
            "reason": "output_unwritable",
        }
        if placed:
            details["written"] = placed
        raise OutputError(
            f"Cannot write the hydrograph tables into {directory}: {exc}",
            details=details,
            hint="The tables listed in details.written were already moved into place."
            if placed
            else None,
        ) from exc


def _route(
    reach: Reach | Callable[[], Reach],
    *,
    times_min: Sequence[float] | None,
    discharge_m3s: Sequence[float] | None,
    input_file: str | os.PathLike[str] | None,
    time_column: str | None,
    value_column: str | None,
    initial_outflow_m3s: float | None,
    extend_min: float | None,
    output: str | os.PathLike[str] | None,
    force: bool,
    check: bool,
    other_inputs: Mapping[str, str | os.PathLike[str] | None] | None = None,
) -> OperationOutput:
    """Run one element over the loaded hydrograph and deliver the result.

    ``reach`` is the element, or a function that builds it when it reads a file (the
    storage-outflow table of a reservoir): the file is read, like the hydrograph, after
    the output has been planned. ``other_inputs`` are further input files that
    ``output`` must not be.

    The order is the one of the writing commands: refuse an output that is an input,
    plan the output, answer a ``check`` with the plan, fail on a conflict, and only
    then read and compute. A ``check`` without ``output`` has no plan: it computes.
    """
    target = None if output is None else Path(os.fspath(output))
    if target is not None:
        refuse_input_as_output(
            target,
            {"input_file": input_file, **(other_inputs or {})},
            hint="Give another file name for the outflow hydrograph.",
        )
    plan = plan_outputs({"output": target}, force=force)
    if check and target is not None:
        return plan_output(plan)
    if (error := conflict_error(plan)) is not None:
        raise error
    element = reach() if callable(reach) else reach
    inflow = load_hydrograph(
        times_min=times_min,
        discharge_m3s=discharge_m3s,
        input_file=input_file,
        time_column=time_column,
        value_column=value_column,
    )
    run = element.route(
        inflow, initial_outflow_m3s=initial_outflow_m3s, extend_min=extend_min
    )
    notices = tuple(Notice(item.level, item.code, item.message) for item in run.notices)
    result = RouteResult.from_routing(run, with_series=target is None)
    if target is None:
        return OperationOutput(result, notices)
    _write_table(run.outflow.to_table(), target)
    return OperationOutput(result, notices, files=(target,), replaced=plan.replaced)


def route_lag(
    *,
    lag_min: float,
    times_min: Sequence[float] | None = None,
    discharge_m3s: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    time_column: str | None = None,
    value_column: str | None = None,
    initial_outflow_m3s: float | None = None,
    extend_min: float | None = None,
    output: str | os.PathLike[str] | None = None,
    force: bool = False,
    check: bool = False,
) -> OperationOutput:
    """Lag routing of a hydrograph (``route lag``).

    The outflow is the inflow ``lag_min`` later, with no attenuation
    (:class:`hydrolog.routing.LagReach`). A lag that is not a whole number of time
    steps is interpolated linearly (notice ``lag_interpolated``). The time axis is
    extended after the last inflow ordinate until the outflow has settled (notice
    ``tail_extended``).

    Parameters
    ----------
    lag_min : float
        Lag [min], > 0.
    times_min, discharge_m3s : sequence of float, optional
        The inflow hydrograph inline: times [min] at a regular step and discharges
        [m3/s], not negative.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the hydrograph, instead of the inline lists.
    time_column, value_column : str, optional
        Columns of ``input_file``; default ``time_min`` and ``discharge_m3s``.
    initial_outflow_m3s : float, optional
        Outflow at the first ordinate [m3/s], >= 0; default the first inflow ordinate.
    extend_min : float, optional
        Time added after the last inflow ordinate [min], >= 0; ``0`` adds nothing.
        Default: until the outflow has settled.
    output : str or os.PathLike, optional
        CSV file to write with the outflow hydrograph (``time_min``,
        ``discharge_m3s``); an existing file is replaced only with ``force``. It must
        not be ``input_file``. Without it the series is in the result.
    force : bool, optional
        Replace an existing ``output`` file, by default ``False``.
    check : bool, optional
        With ``output``: plan without effects and return the ``hydrolog-plan/1``
        document of the target. Without ``output`` there is nothing to plan and the
        result is computed as usual.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`RouteResult`; the written file is listed in
        ``files``. With ``check`` and ``output`` the result is the plan.

    Raises
    ------
    InvalidParameterError
        If a parameter or the inline hydrograph is not valid, both or neither source
        of the hydrograph is given, or ``output`` is ``input_file``.
    NotFoundError
        If ``input_file`` does not exist.
    InputDataError
        If ``input_file`` cannot be read or its hydrograph breaks a rule (irregular
        step, a negative discharge...).
    ConflictError
        If ``output`` exists and ``force`` is not given (``details.reason``
        ``output_exists``).
    OutputError
        If the output cannot be written.
    """
    return _route(
        LagReach(lag_min=lag_min),
        times_min=times_min,
        discharge_m3s=discharge_m3s,
        input_file=input_file,
        time_column=time_column,
        value_column=value_column,
        initial_outflow_m3s=initial_outflow_m3s,
        extend_min=extend_min,
        output=output,
        force=force,
        check=check,
    )


def route_muskingum(
    *,
    k_min: float,
    x: float,
    subreaches: int | None = None,
    times_min: Sequence[float] | None = None,
    discharge_m3s: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    time_column: str | None = None,
    value_column: str | None = None,
    initial_outflow_m3s: float | None = None,
    extend_min: float | None = None,
    output: str | os.PathLike[str] | None = None,
    force: bool = False,
    check: bool = False,
) -> OperationOutput:
    """Muskingum routing of a hydrograph (``route muskingum``).

    The storage of the reach is ``K [X I + (1 - X) O]`` and the reach is divided into
    ``subreaches`` equal sub-reaches of ``K / N`` in series
    (:class:`hydrolog.routing.MuskingumReach`). The weights of a sub-reach are
    non-negative only when ``|2KX| <= dt <= 2K(1 - X)``. Without ``subreaches`` the
    number is ``K / dt`` rounded, which is inside that window whenever it holds a
    whole number; when it holds none every step is divided into sub-steps (notice
    ``substeps_added``). The time axis is extended after the last inflow ordinate
    until the outflow has settled (notice ``tail_extended``).

    Parameters
    ----------
    k_min : float
        Travel time ``K`` of the reach [min], > 0.
    x : float
        Weighting factor ``X``, 0 (linear reservoir, maximum attenuation) to 0.5 (no
        attenuation).
    subreaches : int, optional
        Number of equal sub-reaches, >= 1; default ``K / dt`` rounded. A number outside
        the window of the time step is refused.
    times_min, discharge_m3s : sequence of float, optional
        The inflow hydrograph inline: times [min] at a regular step and discharges
        [m3/s], not negative.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the hydrograph, instead of the inline lists.
    time_column, value_column : str, optional
        Columns of ``input_file``; default ``time_min`` and ``discharge_m3s``.
    initial_outflow_m3s : float, optional
        Outflow at the first ordinate [m3/s], >= 0, the same in every sub-reach;
        default the first inflow ordinate.
    extend_min : float, optional
        Time added after the last inflow ordinate [min], >= 0; ``0`` adds nothing.
        Default: until the outflow has settled.
    output : str or os.PathLike, optional
        CSV file to write with the outflow hydrograph (``time_min``,
        ``discharge_m3s``); an existing file is replaced only with ``force``. It must
        not be ``input_file``. Without it the series is in the result.
    force : bool, optional
        Replace an existing ``output`` file, by default ``False``.
    check : bool, optional
        With ``output``: plan without effects and return the ``hydrolog-plan/1``
        document of the target. Without ``output`` there is nothing to plan and the
        result is computed as usual.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`RouteResult`; the written file is listed in
        ``files``. With ``check`` and ``output`` the result is the plan.

    Raises
    ------
    InvalidParameterError
        If a parameter or the inline hydrograph is not valid, both or neither source
        of the hydrograph is given, ``output`` is ``input_file``, ``subreaches`` is
        outside the window of the time step (``details.reason`` ``unstable_timestep``,
        with the window) or ``k_min`` is too short for the time step to be divided
        into 100 sub-steps.
    NotFoundError
        If ``input_file`` does not exist.
    InputDataError
        If ``input_file`` cannot be read or its hydrograph breaks a rule (irregular
        step, a negative discharge...).
    ConflictError
        If ``output`` exists and ``force`` is not given (``details.reason``
        ``output_exists``).
    OutputError
        If the output cannot be written.
    """
    return _route(
        MuskingumReach(k_min=k_min, x=x, subreaches=subreaches),
        times_min=times_min,
        discharge_m3s=discharge_m3s,
        input_file=input_file,
        time_column=time_column,
        value_column=value_column,
        initial_outflow_m3s=initial_outflow_m3s,
        extend_min=extend_min,
        output=output,
        force=force,
        check=check,
    )


def route_muskingum_cunge(
    *,
    length_km: float,
    slope_m_per_m: float,
    manning_n: float | None = None,
    bottom_width_m: float | None = None,
    side_slope_m_per_m: float = 0.0,
    celerity_m_per_s: float | None = None,
    top_width_m: float | None = None,
    reference_discharge_m3s: float | None = None,
    times_min: Sequence[float] | None = None,
    discharge_m3s: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    time_column: str | None = None,
    value_column: str | None = None,
    initial_outflow_m3s: float | None = None,
    extend_min: float | None = None,
    output: str | os.PathLike[str] | None = None,
    force: bool = False,
    check: bool = False,
) -> OperationOutput:
    """Muskingum-Cunge routing of a hydrograph (``route muskingum-cunge``).

    The Muskingum parameters follow from the hydraulics of the reach, ``K = dx / c`` and
    ``X = (1 - Q / (T S0 c dx)) / 2`` per routing distance step ``dx`` (NEH-630
    chapter 17), and are constant for the run
    (:class:`hydrolog.routing.MuskingumCungeReach`). The hydraulics are given by a
    channel section (``manning_n`` with ``bottom_width_m`` and ``side_slope_m_per_m``:
    Manning's equation gives the celerity and the top width at the reference
    discharge) or directly by ``celerity_m_per_s`` with ``top_width_m``; exactly one
    of the two groups. The reference discharge is the inflow peak unless
    ``reference_discharge_m3s`` is given. The reach is divided into ``L / dx_c`` steps
    with ``dx_c = (c dt + Q / (T S0 c)) / 2``, changed (notice ``subreaches_adjusted``)
    where its weights would be negative; a rise from 5 % of the peak to the peak in
    fewer than 10 time steps divides the time step (notice ``timestep_refined``); the
    notice ``accuracy_limit`` says that the NRCS grid was beyond the accuracy limit of
    NEH-630 and was replaced.

    Parameters
    ----------
    length_km : float
        Length of the reach [km], > 0.
    slope_m_per_m : float
        Friction (bed) slope [m/m], > 0.
    manning_n : float, optional
        Manning's roughness [s/m^(1/3)], > 0; with ``bottom_width_m``.
    bottom_width_m : float, optional
        Bottom width of the section [m], >= 0 (0: a triangle); with ``manning_n``.
    side_slope_m_per_m : float, optional
        Horizontal metres per vertical metre of the banks, >= 0 (0: a rectangle), by
        default 0; part of the section, ignored with ``celerity_m_per_s``.
    celerity_m_per_s : float, optional
        Celerity of the flood wave at the reference discharge [m/s], > 0; with
        ``top_width_m``, instead of the section.
    top_width_m : float, optional
        Width of the water surface at the reference discharge [m], > 0; with
        ``celerity_m_per_s``.
    reference_discharge_m3s : float, optional
        Reference discharge [m3/s], > 0; default the inflow peak.
    times_min, discharge_m3s : sequence of float, optional
        The inflow hydrograph inline: times [min] at a regular step and discharges
        [m3/s], not negative.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the hydrograph, instead of the inline lists.
    time_column, value_column : str, optional
        Columns of ``input_file``; default ``time_min`` and ``discharge_m3s``.
    initial_outflow_m3s : float, optional
        Outflow at the first ordinate [m3/s], >= 0, the same in every step of the
        reach; default the first inflow ordinate.
    extend_min : float, optional
        Time added after the last inflow ordinate [min], >= 0; ``0`` adds nothing.
        Default: until the outflow has settled.
    output : str or os.PathLike, optional
        CSV file to write with the outflow hydrograph (``time_min``,
        ``discharge_m3s``); an existing file is replaced only with ``force``. It must
        not be ``input_file``. Without it the series is in the result.
    force : bool, optional
        Replace an existing ``output`` file, by default ``False``.
    check : bool, optional
        With ``output``: plan without effects and return the ``hydrolog-plan/1``
        document of the target. Without ``output`` there is nothing to plan and the
        result is computed as usual.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`RouteResult`; the written file is listed in
        ``files``. With ``check`` and ``output`` the result is the plan.

    Raises
    ------
    InvalidParameterError
        If a parameter or the inline hydrograph is not valid, both or neither source
        of the hydrograph is given, not exactly one group of hydraulics options is
        given (``details.reason`` ``one_of``), ``output`` is ``input_file``, the
        inflow is zero everywhere and no ``reference_discharge_m3s`` is given, or no
        division of the reach keeps the weights non-negative (``details.reason``
        ``unstable_timestep``; a short or flat reach is storage: ``route level-pool``).
    NotFoundError
        If ``input_file`` does not exist.
    InputDataError
        If ``input_file`` cannot be read or its hydrograph breaks a rule (irregular
        step, a negative discharge...).
    ConflictError
        If ``output`` exists and ``force`` is not given (``details.reason``
        ``output_exists``).
    OutputError
        If the output cannot be written.
    """
    return _route(
        MuskingumCungeReach(
            length_km=length_km,
            slope_m_per_m=slope_m_per_m,
            manning_n=manning_n,
            bottom_width_m=bottom_width_m,
            side_slope_m_per_m=side_slope_m_per_m,
            celerity_m_per_s=celerity_m_per_s,
            top_width_m=top_width_m,
            reference_discharge_m3s=reference_discharge_m3s,
        ),
        times_min=times_min,
        discharge_m3s=discharge_m3s,
        input_file=input_file,
        time_column=time_column,
        value_column=value_column,
        initial_outflow_m3s=initial_outflow_m3s,
        extend_min=extend_min,
        output=output,
        force=force,
        check=check,
    )


def route_cascade(
    *,
    n: float,
    k_min: float | None = None,
    length_km: float | None = None,
    celerity_m_per_s: float | None = None,
    times_min: Sequence[float] | None = None,
    discharge_m3s: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    time_column: str | None = None,
    value_column: str | None = None,
    initial_outflow_m3s: float | None = None,
    extend_min: float | None = None,
    output: str | os.PathLike[str] | None = None,
    force: bool = False,
    check: bool = False,
) -> OperationOutput:
    """Cascade-of-reservoirs routing of a hydrograph (``route cascade``).

    The reach is ``n`` equal linear reservoirs in series, each with the storage
    ``S = K O`` (the Nash model; the Kalinin-Milyukov method for ``n`` equal to the
    reach length over ``Q / (T S0 c)``), and the outflow is the exact response to the
    inflow interpolated linearly between its ordinates
    (:class:`hydrolog.routing.CascadeReach`). The weights follow from the incomplete
    gamma function, so every time step is allowed: there is no window of stable steps,
    no sub-reach and no sub-step, and ``n`` need not be whole. The time scale is the
    storage constant ``k_min`` of one reservoir, or the length and celerity of the
    reach, whose travel time ``L / c`` is the delay ``n K``; exactly one of the two. The
    time axis is extended after the last inflow ordinate until the outflow has settled
    (notice ``tail_extended``).

    Parameters
    ----------
    n : float
        Number of reservoirs, > 0; need not be whole.
    k_min : float, optional
        Storage constant ``K`` of one reservoir [min], > 0.
    length_km : float, optional
        Length of the reach [km], > 0; with ``celerity_m_per_s``, instead of ``k_min``.
    celerity_m_per_s : float, optional
        Celerity of the flood wave [m/s], > 0; with ``length_km``.
    times_min, discharge_m3s : sequence of float, optional
        The inflow hydrograph inline: times [min] at a regular step and discharges
        [m3/s], not negative.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the hydrograph, instead of the inline lists.
    time_column, value_column : str, optional
        Columns of ``input_file``; default ``time_min`` and ``discharge_m3s``.
    initial_outflow_m3s : float, optional
        Outflow at the first ordinate [m3/s], >= 0, held by every reservoir; default
        the first inflow ordinate.
    extend_min : float, optional
        Time added after the last inflow ordinate [min], >= 0; ``0`` adds nothing.
        Default: until the outflow has settled.
    output : str or os.PathLike, optional
        CSV file to write with the outflow hydrograph (``time_min``,
        ``discharge_m3s``); an existing file is replaced only with ``force``. It must
        not be ``input_file``. Without it the series is in the result.
    force : bool, optional
        Replace an existing ``output`` file, by default ``False``.
    check : bool, optional
        With ``output``: plan without effects and return the ``hydrolog-plan/1``
        document of the target. Without ``output`` there is nothing to plan and the
        result is computed as usual.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`RouteResult`; the written file is listed in
        ``files``. With ``check`` and ``output`` the result is the plan.

    Raises
    ------
    InvalidParameterError
        If a parameter or the inline hydrograph is not valid, both or neither source
        of the hydrograph is given, not exactly one of ``k_min`` and the pair
        ``length_km`` with ``celerity_m_per_s`` is given (``details.reason``
        ``one_of``), or ``output`` is ``input_file``.
    NotFoundError
        If ``input_file`` does not exist.
    InputDataError
        If ``input_file`` cannot be read or its hydrograph breaks a rule (irregular
        step, a negative discharge...).
    ConflictError
        If ``output`` exists and ``force`` is not given (``details.reason``
        ``output_exists``).
    OutputError
        If the output cannot be written.
    """
    return _route(
        CascadeReach(
            n=n,
            k_min=k_min,
            length_km=length_km,
            celerity_m_per_s=celerity_m_per_s,
        ),
        times_min=times_min,
        discharge_m3s=discharge_m3s,
        input_file=input_file,
        time_column=time_column,
        value_column=value_column,
        initial_outflow_m3s=initial_outflow_m3s,
        extend_min=extend_min,
        output=output,
        force=force,
        check=check,
    )


def route_level_pool(
    *,
    storage_m3: Sequence[float] | None = None,
    outflow_m3s: Sequence[float] | None = None,
    stage_m: Sequence[float] | None = None,
    rating_file: str | os.PathLike[str] | None = None,
    subreaches: int = 1,
    times_min: Sequence[float] | None = None,
    discharge_m3s: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    time_column: str | None = None,
    value_column: str | None = None,
    initial_outflow_m3s: float | None = None,
    extend_min: float | None = None,
    output: str | os.PathLike[str] | None = None,
    force: bool = False,
    check: bool = False,
) -> OperationOutput:
    """Level-pool routing of a hydrograph (``route level-pool``).

    A reservoir, a pond or a reach with a tabulated storage curve is given by its
    storage-outflow table, and the outflow follows from storage indication, the
    modified Puls method of NEH-630 chapter 17: the working curve ``S / dt + O / 2`` is
    read by linear interpolation (:class:`hydrolog.routing.LevelPoolReach`). Between
    the lowest and the highest flow of the run the time step must not exceed twice the
    shortest storage constant ``dS / dO`` of the table over the number of sub-reaches;
    a longer step is divided into the fewest equal sub-steps that meet the rule
    (notice ``timestep_refined``) and more than 100 parts are refused. A flood that
    fills the reservoir beyond its table is an error, never an extrapolation. The time
    axis is extended after the last inflow ordinate until the outflow has settled
    (notice ``tail_extended``).

    Parameters
    ----------
    storage_m3 : sequence of float, optional
        Storage of each row of the table [m3], not decreasing, not negative; with
        ``outflow_m3s``, instead of ``rating_file``.
    outflow_m3s : sequence of float, optional
        Outflow of each row [m3/s], not decreasing, not negative; ``0`` below a crest.
    stage_m : sequence of float, optional
        Water level of each row [m], not decreasing; with the inline table only (a
        ``rating_file`` brings its own column), it is reported at the peak.
    rating_file : str or os.PathLike, optional
        CSV or JSON file with the columns ``storage_m3``, ``outflow_m3s`` and
        optionally ``stage_m``, one row per state of the reservoir, instead of the
        inline table.
    subreaches : int, optional
        Number of sub-reaches in series, each holding ``S / N`` of the storage for the
        same outflow; at least 1, by default 1 (a pond or a reservoir).
    times_min, discharge_m3s : sequence of float, optional
        The inflow hydrograph inline: times [min] at a regular step and discharges
        [m3/s], not negative.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the hydrograph, instead of the inline lists.
    time_column, value_column : str, optional
        Columns of ``input_file``; default ``time_min`` and ``discharge_m3s``.
    initial_outflow_m3s : float, optional
        Outflow at the first ordinate [m3/s], >= 0, inside the table; the reservoir
        starts at rest with it. Default the first inflow ordinate.
    extend_min : float, optional
        Time added after the last inflow ordinate [min], >= 0; ``0`` adds nothing.
        Default: until the outflow has settled.
    output : str or os.PathLike, optional
        CSV file to write with the outflow hydrograph (``time_min``,
        ``discharge_m3s``); an existing file is replaced only with ``force``. It must
        not be ``input_file`` or ``rating_file``. Without it the series is in the
        result.
    force : bool, optional
        Replace an existing ``output`` file, by default ``False``.
    check : bool, optional
        With ``output``: plan without effects and return the ``hydrolog-plan/1``
        document of the target. Without ``output`` there is nothing to plan and the
        result is computed as usual.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`RouteResult`, whose ``parameters`` hold the numbers of
        sub-reaches and sub-steps, the longest step that meets the rule, the peak
        storage and its time and, with a stage, the peak stage and its time; the
        written file is listed in ``files``. With ``check`` and ``output`` the result
        is the plan.

    Raises
    ------
    InvalidParameterError
        If a parameter or the inline hydrograph is not valid, both or neither source
        of the hydrograph is given, not exactly one of the inline table and
        ``rating_file`` is given (``details.reason`` ``one_of``), ``stage_m`` is given
        with ``rating_file`` (``details.reason`` ``conflict``), the inline table breaks
        a rule (``details.option`` the column), ``output`` is ``input_file`` or
        ``rating_file``, the initial outflow is outside the table, or the time step is
        so long for the table that more than 100 parts would be needed
        (``details.reason`` ``unstable_timestep``).
    NotFoundError
        If ``input_file`` or ``rating_file`` does not exist.
    InputDataError
        If ``input_file`` or ``rating_file`` cannot be read or its table breaks a rule
        (``details.reason``, ``details.column``, ``details.row``).
    CalculationError
        If the flood fills the reservoir beyond the last row of the table or empties
        it below the first (``details.reason`` ``table_exceeded`` or
        ``table_emptied``).
    ConflictError
        If ``output`` exists and ``force`` is not given (``details.reason``
        ``output_exists``).
    OutputError
        If the output cannot be written.
    """

    def build() -> Reach:
        rating = load_rating(
            storage_m3=storage_m3,
            outflow_m3s=outflow_m3s,
            stage_m=stage_m,
            rating_file=rating_file,
        )
        return LevelPoolReach(
            storage_m3=rating.storage_m3,
            outflow_m3s=rating.outflow_m3s,
            stage_m=rating.stage_m,
            subreaches=subreaches,
        )

    return _route(
        build,
        times_min=times_min,
        discharge_m3s=discharge_m3s,
        input_file=input_file,
        time_column=time_column,
        value_column=value_column,
        initial_outflow_m3s=initial_outflow_m3s,
        extend_min=extend_min,
        output=output,
        force=force,
        check=check,
        other_inputs={"rating_file": rating_file},
    )


def _selection(network: RoutingNetwork, nodes: Sequence[str] | None) -> list[str]:
    """Return the ids of the nodes whose hydrographs are returned, in the order given.

    Without ``nodes`` that is every node in the order of evaluation. An id may be
    repeated here: planning the files names it ``duplicate_output_name``.
    """
    if nodes is None:
        return list(network.order)
    if isinstance(nodes, str) or not all(isinstance(item, str) for item in nodes):
        raise InvalidParameterError(
            "Option 'nodes' must be a list of node ids",
            details={
                "option": "nodes",
                "reason": "type",
                "expected": "array of strings",
            },
        )
    if not nodes:
        raise InvalidParameterError(
            "Option 'nodes' must not be an empty list",
            details={"option": "nodes", "reason": "empty"},
            hint="Leave 'nodes' out to return every node.",
        )
    known = set(network.order)
    for item in nodes:
        if item not in known:
            shown = ", ".join(network.order[:20]) + (
                ", ..." if len(network.order) > 20 else ""
            )
            raise InvalidParameterError(
                f"Option 'nodes': the network has no node {item[:64]!r}",
                details={
                    "option": "nodes",
                    "reason": "unknown_node",
                    "node_id": item[:64],
                    "n_nodes": len(network.order),
                },
                hint=f"The ids are {shown}.",
            )
    return list(nodes)


def _refuse_inputs(
    directory: Path,
    names: Sequence[str],
    network_file: str | os.PathLike[str] | None,
    inflows_file: str | os.PathLike[str] | None,
    rating_files: Mapping[str, Path],
) -> None:
    """Refuse a table that would overwrite a file the network is read from."""
    inputs: dict[str, str | os.PathLike[str] | None] = {
        "network_file": network_file,
        "inflows_file": inflows_file,
    }
    for node_id, path in rating_files.items():
        inputs[f"rating_file of node {node_id!r}"] = path
    for name in names:
        refuse_input_as_output(
            directory / name,
            inputs,
            hint="Give another output directory: the tables of the nodes must not "
            "replace the files the network is read from.",
            option="output_dir",
        )


def route_network(
    *,
    network: Mapping[str, Any] | None = None,
    network_file: str | os.PathLike[str] | None = None,
    inflows_file: str | os.PathLike[str] | None = None,
    time_column: str | None = None,
    nodes: Sequence[str] | None = None,
    output_dir: str | os.PathLike[str] | None = None,
    force: bool = False,
    check: bool = False,
) -> OperationOutput:
    """Route hydrographs down a river network (``route network``).

    The network is a document ``hydrolog-network/1`` (see
    :mod:`hydrolog.operations._network_input`): subcatchments that bring a source
    hydrograph, reaches that route the hydrograph of the node upstream by a method of
    this group with the options of ``route <method>``, reservoirs (level pool),
    junctions that add the hydrographs flowing into them and one outlet, linked by the
    ids of the nodes upstream (:class:`hydrolog.routing.RoutingNetwork`). All sources
    share one time step and nothing is resampled. The nodes are evaluated headwaters
    first, so the order of the nodes in the document changes nothing; every reach and
    reservoir extends its time axis until its outflow has settled (ADR-0008) and a
    junction holds the shorter hydrographs at their last value.

    The hydrograph that leaves each node is a table (``time_min``, ``discharge_m3s``)
    that every ``route`` command reads: ``output_dir`` receives one file ``<id>.csv``
    per selected node, which is also the hand-off to a hydraulic model; without it the
    hydrographs of the selected nodes are in the result (``nodes`` limits them).

    Parameters
    ----------
    network : Mapping, optional
        The document inline (JSON-native values). It cannot name files: a node that
        reads a ``rating_file`` needs ``network_file``.
    network_file : str or os.PathLike, optional
        JSON file with the document, instead of ``network``. The ``rating_file`` of a
        node is relative to the directory of this file and must lie inside it.
    inflows_file : str or os.PathLike, optional
        CSV or JSON file with a time column and one discharge column [m3/s] per
        subcatchment that has no inline discharges; the column is named by the
        ``value_column`` of the node or else by its ``id``.
    time_column : str, optional
        Time column [min] of ``inflows_file``; default ``time_min``.
    nodes : sequence of str, optional
        Ids of the nodes whose hydrographs are returned; default all of them.
    output_dir : str or os.PathLike, optional
        Directory for the tables ``<id>.csv`` (created if missing). An existing table
        is replaced only with ``force``; no table may be an input file and the
        directory must not be, or lie in, the store of another Nogat tool.
    force : bool, optional
        Replace existing tables in ``output_dir``, by default ``False``.
    check : bool, optional
        With ``output_dir``: plan without effects and return the ``hydrolog-plan/1``
        document of the tables. Without it there is nothing to plan and the result is
        computed as usual.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`NetworkRouteResult`; the written tables are listed in
        ``files`` and every notice of a reach starts with the id of its node. With
        ``check`` and ``output_dir`` the result is the plan. Without ``output_dir`` a
        result of more than :data:`PAGE_CHARS` characters (all the hydrographs of a
        large network) carries the warning ``large_result``, which suggests ``nodes``
        and ``output_dir``.

    Raises
    ------
    InvalidParameterError
        If both or neither of ``network`` and ``network_file`` are given
        (``details.reason`` ``one_of``), an inline document is wrong
        (``details.option`` ``network``, ``details.reason`` and ``details.node_id``;
        see :mod:`hydrolog.operations._network_input`), the sources have different
        time axes (``timestep_mismatch``, ``start_mismatch``), a reach cannot be
        routed (``unstable_timestep``, an initial outflow outside a table...;
        ``details.node_id``), ``nodes`` names a node the network does not have
        (``unknown_node``), or a table would overwrite an input file
        (``details.option`` ``output_dir``).
    NotFoundError
        If a file does not exist.
    InputDataError
        If a file cannot be read, or the document in ``network_file``, a table of
        ``inflows_file`` or a rating file is wrong (``details.path``).
    CalculationError
        If a flood fills a reservoir beyond its table or empties it below
        (``details.reason`` ``table_exceeded`` or ``table_emptied``, with
        ``details.node_id``).
    ConflictError
        If a table exists and ``force`` is not given (``details.reason``
        ``output_exists``), ``nodes`` repeats an id (``duplicate_output_name``) or
        ``output_dir`` lies in the store of another tool (``output_in_store``);
        ``details.paths`` lists every path with that reason.
    OutputError
        If the tables cannot be written.
    """
    loaded = load_network(
        network=network,
        network_file=network_file,
        inflows_file=inflows_file,
        time_column=time_column,
    )
    graph = loaded.network
    selected = _selection(graph, nodes)
    directory = None if output_dir is None else Path(os.fspath(output_dir))
    plan = None
    if directory is not None:
        names = [f"{node_id}.csv" for node_id in selected]
        _refuse_inputs(
            directory, names, network_file, inflows_file, loaded.rating_files
        )
        plan = plan_directory("output_dir", directory, names, force=force)
        if check:
            return plan_output(plan)
        if (error := conflict_error(plan)) is not None:
            raise error
    run = graph.route()
    returned = set(selected) if directory is None else set()
    summaries: list[dict[str, Any]] = []
    notices: list[Notice] = []
    for node in graph.nodes:
        hydrograph = run.hydrographs[node.id]
        entry: dict[str, Any] = {
            "id": node.id,
            "type": node.kind,
            "from": list(node.upstream),
            "peak_m3s": hydrograph.peak_discharge_m3s,
            "time_to_peak_min": hydrograph.time_to_peak_min,
            "volume_m3": hydrograph.volume_m3,
        }
        routed = run.runs.get(node.id)
        if routed is not None:
            entry["model"] = routed.model
            entry["parameters"] = routed.parameters
            entry["peak_attenuation_pct"] = routed.peak_attenuation_pct
            entry["peak_delay_min"] = routed.peak_delay_min
            entry["balance_error_m3"] = routed.balance_error_m3
            notices.extend(
                Notice(item.level, item.code, f"{node.id}: {item.message}")
                for item in routed.notices
            )
        if node.id in returned:
            entry["times_min"] = hydrograph.times_min
            entry["discharge_m3s"] = hydrograph.discharge_m3s
        summaries.append(entry)
    result = NetworkRouteResult(
        name=graph.name,
        timestep_min=graph.timestep_min,
        outlet=graph.outlet,
        order=list(graph.order),
        nodes=summaries,
    )
    if directory is None or plan is None:
        size = _json_chars(result)
        if returned and size > PAGE_CHARS:
            notices.append(
                Notice(
                    "warning",
                    "large_result",
                    f"the result is {size:,} characters, over the {PAGE_CHARS:,} of "
                    "a page that a client reads whole: give `nodes` to return fewer "
                    "hydrographs, or `output_dir` to write one table per node",
                )
            )
        return OperationOutput(result, tuple(notices))
    tables = {
        f"{node_id}.csv": run.hydrographs[node_id].to_table() for node_id in selected
    }
    _write_directory(directory, tables, force=force)
    return OperationOutput(
        result,
        tuple(notices),
        files=tuple(directory / name for name in tables),
        replaced=plan.replaced,
    )
