"""Operations of the group ``commands``: the catalog describing itself.

``commands list`` lists the catalog commands, ``commands schema`` returns the JSON
Schema of the options of one command or of the whole catalog and ``commands guide``
the guide for AI agents generated from the catalog (and, with ``path``, writes it to
a file). The functions are re-exported by :mod:`hydrolog.operations`; the
conventions of the operation layer are described there.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hydrolog._atomic import atomic_output
from hydrolog._serialization import JsonResultMixin
from hydrolog.agent_guide import GuideFormat, agent_guide
from hydrolog.catalog import command_schema, data_commands
from hydrolog.catalog.envelope import OperationOutput
from hydrolog.catalog.spec import Lang
from hydrolog.exceptions import OutputError

__all__ = [
    "CommandSummary",
    "commands_guide",
    "commands_schema",
    "list_commands",
]


@dataclass
class CommandSummary(JsonResultMixin):
    """Name and summary of one catalog command.

    Attributes
    ----------
    name : str
        Command name, ``"<group> <command>"``.
    operation_id : str
        MCP tool name and Python identifier of the command.
    summary : str
        One-line summary in the requested language.
    """

    name: str
    operation_id: str
    summary: str


def list_commands(*, lang: Lang = "pl") -> list[CommandSummary]:
    """List the catalog commands (``commands list``).

    Parameters
    ----------
    lang : {"pl", "en"}, optional
        Language of the summaries, by default ``"pl"``.

    Returns
    -------
    list of CommandSummary
        All commands ordered by group, then by name.
    """
    return [
        CommandSummary(
            name=command.name,
            operation_id=command.operation_id,
            summary=command.summarize(lang),
        )
        for command in data_commands()
    ]


def commands_schema(*, command: str | None = None, lang: Lang = "pl") -> dict[str, Any]:
    """Describe command options as JSON Schema (``commands schema``).

    Parameters
    ----------
    command : str, optional
        Command name (``"tc kirpich"``) or ``operation_id`` (``"tc_kirpich"``);
        ``None`` describes the whole catalog.
    lang : {"pl", "en"}, optional
        Language of the descriptions, by default ``"pl"``.

    Returns
    -------
    dict
        The ``hydrolog-commands/1`` document, see
        :func:`hydrolog.catalog.command_schema`.

    Raises
    ------
    NotFoundError
        If ``command`` does not exist.
    """
    return command_schema(command, lang=lang)


def _write_text(text: str, target: Path) -> None:
    """Write ``text`` to ``target`` atomically (written aside, then renamed).

    The file is UTF-8 with ``"\\n"`` line ends on every platform; missing directories
    are created and an existing file is replaced.
    """
    try:
        with atomic_output(target) as temporary:
            temporary.write_text(text, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise OutputError(
            f"Cannot write the guide {target}: {exc}", details={"path": str(target)}
        ) from exc


def commands_guide(
    *,
    format: GuideFormat = "agents",
    lang: Lang = "pl",
    path: str | os.PathLike[str] | None = None,
) -> str | OperationOutput:
    """Guide for AI agents generated from the catalog (``commands guide``).

    Renders ``AGENTS.md`` or ``llms.txt`` (:func:`hydrolog.agent_guide.agent_guide`):
    the rules, the interfaces, the result envelope and the error registry, the input
    files, every command with its options and effect, typical flows as CLI lines and
    MCP calls. The text depends only on the installed package, so the files of the
    repository root are exactly what this operation writes with ``lang="pl"``.

    Parameters
    ----------
    format : {"agents", "llms"}, optional
        ``"agents"`` for the full ``AGENTS.md`` (default), ``"llms"`` for the concise
        ``llms.txt`` (at most 150 lines).
    lang : {"pl", "en"}, optional
        Language of the guide, by default ``"pl"``.
    path : str or os.PathLike, optional
        File to write the text to (UTF-8, ``"\\n"`` line ends); missing directories
        are created and an existing file is replaced. ``None`` writes nothing.

    Returns
    -------
    str or OperationOutput
        The guide text; with ``path`` an :class:`OperationOutput` whose ``result`` is
        that text and whose ``files`` lists the written file.

    Raises
    ------
    InvalidParameterError
        If ``format`` or ``lang`` is not allowed.
    OutputError
        If the file cannot be written.

    Examples
    --------
    >>> text = commands_guide(format="llms", lang="en")
    >>> text.splitlines()[0]
    '# Hydrolog'
    """
    text = agent_guide(format, lang)
    if path is None:
        return text
    target = Path(os.fspath(path))
    _write_text(text, target)
    return OperationOutput(text, files=(target,))
