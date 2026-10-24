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
The functions are re-exported by :mod:`hydrolog.operations`.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from hydrolog._atomic import atomic_output
from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.catalog.inputs import load_hydrograph
from hydrolog.exceptions import OutputError
from hydrolog.operations._outputs import (
    conflict_error,
    plan_output,
    plan_outputs,
    refuse_input_as_output,
)
from hydrolog.routing import (
    CascadeReach,
    LagReach,
    MuskingumCungeReach,
    MuskingumReach,
    Reach,
    RoutingResult,
)

__all__ = [
    "RouteResult",
    "route_cascade",
    "route_lag",
    "route_muskingum",
    "route_muskingum_cunge",
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


def _route(
    reach: Reach,
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
) -> OperationOutput:
    """Run one element over the loaded hydrograph and deliver the result.

    The order is the one of the writing commands: refuse an output that is an input,
    plan the output, answer a ``check`` with the plan, fail on a conflict, and only
    then read and compute. A ``check`` without ``output`` has no plan: it computes.
    """
    target = None if output is None else Path(os.fspath(output))
    if target is not None:
        refuse_input_as_output(
            target,
            {"input_file": input_file},
            hint="Give another file name for the outflow hydrograph.",
        )
    plan = plan_outputs({"output": target}, force=force)
    if check and target is not None:
        return plan_output(plan)
    if (error := conflict_error(plan)) is not None:
        raise error
    inflow = load_hydrograph(
        times_min=times_min,
        discharge_m3s=discharge_m3s,
        input_file=input_file,
        time_column=time_column,
        value_column=value_column,
    )
    run = reach.route(
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
