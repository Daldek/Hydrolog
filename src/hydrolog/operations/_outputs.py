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

With ``check`` the plan is the result (:func:`plan_output`): a plan that lists a
``conflict`` is still a successful result; only the real run fails.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

from hydrolog.catalog.envelope import OperationOutput
from hydrolog.exceptions import ConflictError

__all__ = [
    "PLAN_SCHEMA",
    "OutputPlan",
    "PlannedOutput",
    "conflict_error",
    "plan_output",
    "plan_outputs",
]

PLAN_SCHEMA: Final = "hydrolog-plan/1"
"""Value of the ``schema`` key of the plan of a ``check`` run."""

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
        ``output_exists`` or ``duplicate_output_name`` for a ``conflict``.
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
        ``output_exists``) and every offending path in ``details.paths``.
    """
    conflicts = plan.conflicts
    if not conflicts:
        return None
    duplicates = [item for item in conflicts if item.reason == "duplicate_output_name"]
    reason = "duplicate_output_name" if duplicates else "output_exists"
    offending = duplicates or list(conflicts)
    paths = [item.path for item in offending]
    if reason == "output_exists":
        message = f"The output file already exists: {', '.join(paths)}"
        hint = "Give another path or add --force to replace the file."
    else:
        message = f"Two outputs name the same file: {', '.join(paths)}"
        hint = "Give a different path for each output."
    return ConflictError(
        message,
        details={"reason": reason, "paths": paths},
        hint=hint,
    )


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
