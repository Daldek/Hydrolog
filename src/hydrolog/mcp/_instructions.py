"""Instructions of the MCP server (AGI-5.10): how the tools fit together, in short.

The text is the ``instructions`` field of the server; clients load it at the start of
every session and truncate it at 4,096 characters (DOC-1.7, :data:`MAX_CHARS`). It
states what the tool descriptions cannot: the relations between the tools, the order
discover -> check -> run -> read, the limits of this server (offline, files only in the
allowed directories, write mode, active families) and where the input data come from.
The rules are those of the agent guide (:func:`hydrolog.agent_guide.principles`), the
same text as in ``AGENTS.md`` and ``llms.txt``; the names of the tools are read from
the catalog, never typed here.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from hydrolog.agent_guide import principles
from hydrolog.catalog import Command
from hydrolog.exceptions import NotFoundError

__all__ = ["MAX_CHARS", "build_instructions"]

MAX_CHARS: Final = 4096
"""Upper bound of the length of the instructions in characters (DOC-1.7). Every allowed
directory adds its path; the text of the real catalog stays well below it."""

_FLOW: Final = (
    "Tools are the commands of the Hydrolog catalog, named `hydrolog_<group>_<verb>` "
    "(hydrological calculations: runoff, hydrographs, flood routing, time of "
    "concentration, statistics of flows, morphometry). Work in this order: discover "
    "(`{list_tool}`, then `{schema_tool}` for one command) -> check (a tool that "
    "writes a file plans with `check`) -> run -> read (`result`, `notices`, "
    "`result.files`)."
)
_PROVENANCE: Final = (
    "Input data come from files you are given, usually produced by Kartograf "
    "(terrain, land cover, soil rasters) or IMGWTools (IMGW series and stations). "
    "Their licences and provenance stay with those sources: name them when you "
    "report a result."
)
_DIRS: Final = "Allowed directories (`--allow-dir`): {dirs}."
_NO_DIRS: Final = (
    "No allowed directory (`--allow-dir`): every path option is refused (`forbidden`); "
    "commands that take values work."
)
_WRITES: Final = (
    "Writes are enabled (`--allow-writes`): a writing tool writes inside the allowed "
    "directories; an existing file is replaced only with `force`."
)
_READ_ONLY: Final = (
    "Read-only (no `--allow-writes`): tools that write files run as `check` "
    "(`check` is forced to true, `force` is ignored) and return a plan; nothing is "
    "written."
)
_FAMILIES: Final = (
    "Exposed families (`--tools`): {families}; other tools are not listed."
)


def _operation_id(commands: Sequence[Command], name: str) -> str:
    """``operation_id`` of the command called ``name``."""
    for command in commands:
        if command.name == name:
            return command.operation_id
    raise NotFoundError(
        f"The catalog of the server has no {name!r} command",
        details={"command": name},
    )


def build_instructions(
    commands: Sequence[Command],
    *,
    allowed_dirs: Sequence[str],
    allow_writes: bool,
    families: Sequence[str] | None = None,
) -> str:
    """Build the ``instructions`` text of the server.

    Parameters
    ----------
    commands : sequence of Command
        The full catalog; it must hold the ``commands list`` and ``commands schema``
        commands, which the text sends the agent to.
    allowed_dirs : sequence of str
        Absolute directories the server allows for files; empty when it allows none.
    allow_writes : bool
        Whether the server writes files.
    families : sequence of str, optional
        The families selected with ``--tools``; ``None`` when all tools are exposed.

    Returns
    -------
    str
        The workflow, the rules of the agent guide, the provenance of the data and
        the lines of this server's state (directories, write mode, families).

    Raises
    ------
    NotFoundError
        If the catalog lacks the ``commands list`` or ``commands schema`` command.
    """
    flow = _FLOW.format(
        list_tool=_operation_id(commands, "commands list"),
        schema_tool=_operation_id(commands, "commands schema"),
    )
    rules = [f"{number}. {rule}" for number, rule in enumerate(principles(), start=1)]
    state = [
        _DIRS.format(dirs=", ".join(allowed_dirs)) if allowed_dirs else _NO_DIRS,
        _WRITES if allow_writes else _READ_ONLY,
    ]
    if families is not None:
        state.append(_FAMILIES.format(families=", ".join(families)))
    return "\n".join([flow, "Rules:", *rules, _PROVENANCE, *state])
