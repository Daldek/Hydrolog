"""Plan and check the output files of a writing command.

A command that writes a file (``report generate``, ``soil hsg``, ``commands guide``)
never replaces an existing file unless ``force`` is given (AGI-1.3, DEV-19.9) and
offers ``check``, the plan without effects (DEV-19.10). Before it computes or writes
anything it builds the list of its targets with :func:`plan_outputs`:

* a target that does not exist has the action ``write``;
* an existing target has the action ``replace`` with ``force`` and ``conflict``
  without it (:func:`conflict_error` names every such path in ``details.paths``);
* two targets that name the same file are a ``conflict`` of their own
  (``duplicate_output_name``), checked first.

A command that writes several files into a directory (``--output-dir``, DEV-19.1)
plans them with :func:`plan_directory`: the same rules, with names compared without
regard to case (a FAT, exFAT or SMB share would merge them), and one more conflict: a
directory that is, or lies in, a store of another Nogat tool is refused
(``output_in_store``, DEV-19.11), because a store is recognised by its marker file and
holds only what its own tool wrote.

With ``check`` the plan is the result (:func:`plan_output`): a plan that lists a
``conflict`` is still a successful result; only the real run fails. An output that is
also an input file is refused first (:func:`refuse_input_as_output`).
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

from hydrolog.catalog.envelope import OperationOutput
from hydrolog.exceptions import ConflictError, InvalidParameterError

__all__ = [
    "PLAN_SCHEMA",
    "STORE_MARKERS",
    "OutputPlan",
    "PlannedOutput",
    "conflict_error",
    "plan_directory",
    "plan_output",
    "plan_outputs",
    "refuse_input_as_output",
    "store_around",
]

PLAN_SCHEMA: Final = "hydrolog-plan/1"
"""Value of the ``schema`` key of the plan of a ``check`` run."""

STORE_MARKERS: Final = ("kartograf-store.json", "imgw-store.json")
"""Marker files of the versioned stores of the other Nogat tools (DEV-19.12); a store is
recognised by the name of this file alone, nothing is imported from those tools."""

Action = Literal["write", "replace", "conflict"]


@dataclass(frozen=True)
class PlannedOutput:
    """One output file of a command and what would happen to it.

    Attributes
    ----------
    option : str
        Name of the output option that gave the path.
    path : str
        Absolute path of the file.
    action : {"write", "replace", "conflict"}
        ``write`` for a new file, ``replace`` for an existing one with ``force``,
        ``conflict`` for an existing one without it or for a duplicate name.
    reason : str or None
        ``output_exists``, ``duplicate_output_name`` or ``output_in_store`` for a
        ``conflict``.
    """

    option: str
    path: str
    action: Action
    reason: str | None = None


@dataclass(frozen=True)
class OutputPlan:
    """The planned output files of one call.

    Attributes
    ----------
    targets : tuple of PlannedOutput
        One entry per output option that was given.
    """

    targets: tuple[PlannedOutput, ...]

    @property
    def conflicts(self) -> tuple[PlannedOutput, ...]:
        """Tuple of PlannedOutput: the targets whose action is ``conflict``."""
        return tuple(item for item in self.targets if item.action == "conflict")

    @property
    def replaced(self) -> tuple[str, ...]:
        """Tuple of str: the paths of the targets that are replaced."""
        return tuple(item.path for item in self.targets if item.action == "replace")

    def document(self) -> dict[str, Any]:
        """Return the ``hydrolog-plan/1`` document of the plan."""
        targets: list[dict[str, Any]] = []
        for item in self.targets:
            entry: dict[str, Any] = {
                "option": item.option,
                "path": item.path,
                "action": item.action,
            }
            if item.reason is not None:
                entry["reason"] = item.reason
            targets.append(entry)
        return {"schema": PLAN_SCHEMA, "targets": targets}


def plan_outputs(
    targets: Mapping[str, str | os.PathLike[str] | None], *, force: bool
) -> OutputPlan:
    """Plan the output files of a call.

    Parameters
    ----------
    targets : Mapping
        Output option name to the path it was given; options that were not given
        (``None``) are skipped.
    force : bool
        Replace existing files.

    Returns
    -------
    OutputPlan
        The plan; it never raises, so ``check`` can show a ``conflict``.
    """
    seen: dict[str, str] = {}
    planned: list[PlannedOutput] = []
    for option, given in targets.items():
        if given is None:
            continue
        path = str(Path(os.path.abspath(os.fspath(given))))
        if path in seen:
            planned.append(
                PlannedOutput(option, path, "conflict", "duplicate_output_name")
            )
            continue
        seen[path] = option
        if not os.path.lexists(path):
            planned.append(PlannedOutput(option, path, "write"))
        elif force:
            planned.append(PlannedOutput(option, path, "replace"))
        else:
            planned.append(PlannedOutput(option, path, "conflict", "output_exists"))
    return OutputPlan(tuple(planned))


def store_around(directory: str | os.PathLike[str]) -> Path | None:
    """Return the store that holds ``directory``, the directory with its marker.

    Parameters
    ----------
    directory : str or os.PathLike
        A directory, which need not exist; links are followed, so a link into a store
        is in the store.

    Returns
    -------
    pathlib.Path or None
        The nearest directory, ``directory`` itself or one above it, that holds a
        file named in :data:`STORE_MARKERS`; ``None`` when there is none.
    """
    resolved = Path(os.path.realpath(os.fspath(directory)))
    for candidate in (resolved, *resolved.parents):
        if any(os.path.isfile(candidate / marker) for marker in STORE_MARKERS):
            return candidate
    return None


def plan_directory(
    option: str,
    directory: str | os.PathLike[str],
    names: Iterable[str],
    *,
    force: bool,
) -> OutputPlan:
    """Plan the files of a directory of plain output (DEV-19.5, DEV-19.6, DEV-19.11).

    Parameters
    ----------
    option : str
        Name of the output option that gave ``directory``; every target carries it.
    directory : str or os.PathLike
        The output directory, which need not exist.
    names : iterable of str
        File names, one per unit, in the order of the result; the directory is flat.
    force : bool
        Replace existing files.

    Returns
    -------
    OutputPlan
        One target per name: ``conflict`` with ``duplicate_output_name`` for a name
        that an earlier one has (compared without regard to case), ``conflict`` with
        ``output_in_store`` for every other name when the directory is in a store,
        else ``write`` for a new file and ``replace`` or ``conflict`` with
        ``output_exists`` for an existing one. It never raises and creates nothing.
    """
    base = Path(os.path.abspath(os.fspath(directory)))
    in_store = store_around(base) is not None
    seen: set[str] = set()
    planned: list[PlannedOutput] = []
    for name in names:
        path = str(base / name)
        key = name.casefold()
        if key in seen:
            planned.append(
                PlannedOutput(option, path, "conflict", "duplicate_output_name")
            )
            continue
        seen.add(key)
        if in_store:
            planned.append(PlannedOutput(option, path, "conflict", "output_in_store"))
        elif not os.path.lexists(path):
            planned.append(PlannedOutput(option, path, "write"))
        elif force:
            planned.append(PlannedOutput(option, path, "replace"))
        else:
            planned.append(PlannedOutput(option, path, "conflict", "output_exists"))
    return OutputPlan(tuple(planned))


def _listed(paths: list[str]) -> str:
    """Return the paths for a message: the first five, then how many more."""
    shown = ", ".join(paths[:5])
    return shown + (f" and {len(paths) - 5} more" if len(paths) > 5 else "")


def conflict_error(plan: OutputPlan) -> ConflictError | None:
    """Return the error of a plan with conflicts, or ``None`` when there is none.

    Parameters
    ----------
    plan : OutputPlan
        The plan of the call.

    Returns
    -------
    ConflictError or None
        ``conflict`` with ``details.reason`` (``duplicate_output_name`` before
        ``output_in_store`` before ``output_exists``) and every path that has that
        reason in ``details.paths``.
    """
    conflicts = plan.conflicts
    if not conflicts:
        return None
    reason, offending = next(
        (reason, found)
        for reason in ("duplicate_output_name", "output_in_store", "output_exists")
        if (found := [item for item in conflicts if item.reason == reason])
    )
    paths = [item.path for item in offending]
    details: dict[str, Any] = {"reason": reason, "paths": paths}
    if reason == "output_exists":
        message = f"The output file already exists: {_listed(paths)}"
        hint = "Give another path or add --force to replace the file."
    elif reason == "output_in_store":
        store = store_around(Path(paths[0]).parent)
        details["store"] = None if store is None else str(store)
        message = (
            f"The output directory lies in the store {store} of another tool: "
            f"{_listed(paths)}"
        )
        hint = (
            "Give a directory outside the store; the tool that owns a store writes "
            "into it with its own --root."
        )
    else:
        message = f"Two outputs name the same file: {_listed(paths)}"
        hint = "Give a different path for each output."
    return ConflictError(message, details=details, hint=hint)


def plan_output(plan: OutputPlan) -> OperationOutput:
    """Return the result of a ``check`` run: the plan, nothing written.

    Parameters
    ----------
    plan : OutputPlan
        The plan of the call.

    Returns
    -------
    OperationOutput
        ``result`` is the ``hydrolog-plan/1`` document and ``check`` is true.
    """
    return OperationOutput(plan.document(), check=True)


def _is_same_file(first: Path, second: Path) -> bool:
    """Whether two paths name the same file (also when one does not exist yet)."""
    try:
        return first.samefile(second)
    except OSError:
        return first.resolve() == second.resolve()


def refuse_input_as_output(
    output: str | os.PathLike[str],
    inputs: Mapping[str, str | os.PathLike[str] | None],
    *,
    hint: str = "Give another file name for the output.",
    option: str = "output",
) -> None:
    """Refuse an output path that is one of the input files.

    Parameters
    ----------
    output : str or os.PathLike
        The file the command is going to write.
    inputs : Mapping
        Input option name to the path it was given; options that were not given
        (``None``) are skipped.
    hint : str, optional
        Remediation suggestion of the error.
    option : str, optional
        The output option that gave ``output``, by default ``output``.

    Raises
    ------
    InvalidParameterError
        With ``details.option`` the output option, ``details.reason`` ``conflict`` and
        the name of the input option in ``details.input``.
    """
    target = Path(os.fspath(output))
    for name, given in inputs.items():
        if given is not None and _is_same_file(target, Path(os.fspath(given))):
            raise InvalidParameterError(
                f"Option {option!r} must not be the input file of {name!r}: {target}",
                details={"option": option, "reason": "conflict", "input": name},
                hint=hint,
            )
