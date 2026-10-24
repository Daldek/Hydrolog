"""Operations of the group ``commands``: the catalog describing itself.

``commands list`` lists the catalog commands, ``commands schema`` returns the
``hydrolog-commands/1`` description of one command or a page of the whole catalog
and ``commands guide`` the English guide for AI agents generated from the catalog
(and, with ``output`` or ``inject``, writes it to a file). The functions are
re-exported by :mod:`hydrolog.operations`; the conventions of the operation layer are
described there.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from hydrolog._atomic import atomic_output
from hydrolog._serialization import JsonResultMixin
from hydrolog.agent_guide import GUIDE_FORMATS, GuideFormat, agent_guide, inject_block
from hydrolog.catalog import data_commands
from hydrolog.catalog.dispatch import get_command
from hydrolog.catalog.document import (
    catalog_document,
    command_list,
    paginate,
)
from hydrolog.catalog.envelope import OperationOutput
from hydrolog.exceptions import InvalidParameterError, OutputError
from hydrolog.operations._outputs import conflict_error, plan_output, plan_outputs

__all__ = [
    "GuideDocument",
    "commands_guide",
    "commands_list",
    "commands_schema",
]


def commands_list(*, limit: int = 100, cursor: str | None = None) -> OperationOutput:
    """List the catalog commands (``commands list``).

    Parameters
    ----------
    limit : int, optional
        Commands per page, by default 100.
    cursor : str, optional
        ``page.next_cursor`` of the previous page.

    Returns
    -------
    OperationOutput
        ``result`` is the ``hydrolog-command-list/1`` document (name,
        ``operation_id``, summary, families and ``read_only`` of each command on the
        page); ``page`` carries ``total``, ``next_cursor`` and ``truncated``.

    Raises
    ------
    InvalidParameterError
        If ``cursor`` is not a cursor of this collection.
    """
    selected, page = paginate(data_commands(), limit, cursor)
    return OperationOutput(command_list(selected), page=page)


def commands_schema(
    *, command: str | None = None, limit: int = 5, cursor: str | None = None
) -> OperationOutput:
    """Describe one command, or a page of the catalog (``commands schema``).

    Parameters
    ----------
    command : str, optional
        Command name (``"tc kirpich"``) or ``operation_id``
        (``"hydrolog_tc_kirpich"``); ``None`` describes a page of the whole catalog.
    limit : int, optional
        Commands per page of the whole catalog, by default 5.
    cursor : str, optional
        ``page.next_cursor`` of the previous page.

    Returns
    -------
    OperationOutput
        ``result`` is the ``hydrolog-commands/1`` document; ``page`` is set for the
        whole catalog.

    Raises
    ------
    NotFoundError
        If ``command`` does not exist.
    InvalidParameterError
        If ``cursor`` is not a cursor of this collection.
    """
    if command is not None:
        return OperationOutput(catalog_document((get_command(command),)))
    selected, page = paginate(data_commands(), limit, cursor)
    return OperationOutput(catalog_document(selected), page=page)


@dataclass
class GuideDocument(JsonResultMixin):
    """The rendered guide.

    Attributes
    ----------
    format : str
        ``agents``, ``llms`` or ``agents-md-block``.
    text : str
        The Markdown text.
    """

    format: str
    text: str


def _write_text(text: str, target: Path) -> None:
    r"""Write ``text`` to ``target`` atomically (written aside, then renamed).

    The file is UTF-8 with ``"\n"`` line ends on every platform; missing directories
    are created and an existing file is replaced.
    """
    try:
        with atomic_output(target) as temporary:
            temporary.write_text(text, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise OutputError(
            f"Cannot write the guide {target}: {exc}",
            details={"path": str(target), "reason": "output_unwritable"},
        ) from exc


def _option_error(option: str, reason: str, message: str, hint: str) -> NoReturn:
    raise InvalidParameterError(
        message,
        details={"option": option, "reason": reason},
        hint=hint,
    )


def commands_guide(
    *,
    format: GuideFormat = "agents",
    output: str | os.PathLike[str] | None = None,
    inject: str | os.PathLike[str] | None = None,
    force: bool = False,
    check: bool = False,
) -> OperationOutput:
    r"""Guide for AI agents generated from the catalog (``commands guide``).

    Renders ``AGENTS.md``, ``llms.txt`` or the block for the ``AGENTS.md`` of a
    consumer repository (:func:`hydrolog.agent_guide.agent_guide`): always English,
    generated from the catalog, the error registry and the typical flows. The text
    depends only on the installed package, so the files of the repository root are
    exactly what this operation writes.

    Parameters
    ----------
    format : {"agents", "llms", "agents-md-block"}, optional
        ``"agents"`` for the full ``AGENTS.md`` (default), ``"llms"`` for ``llms.txt``,
        ``"agents-md-block"`` for the compact block between ``<!-- BEGIN hydrolog -->``
        and ``<!-- END hydrolog -->``.
    output : str or os.PathLike, optional
        File to write the text to (UTF-8, ``"\n"`` line ends); missing directories are
        created. An existing file is replaced only with ``force``.
    inject : str or os.PathLike, optional
        Only with ``format="agents-md-block"``: the ``AGENTS.md`` of a consumer
        repository whose block is replaced (appended when it has none); running it
        again changes nothing. An existing file is always edited, so ``force`` is not
        needed.
    force : bool, optional
        Replace an existing ``output`` file, by default ``False``.
    check : bool, optional
        Plan without effects: return the ``hydrolog-plan/1`` document of the target
        (an empty plan when there is no ``output`` or ``inject``) and write nothing.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`GuideDocument` (``format`` and ``text``); with a target
        ``files`` lists the file. With ``check`` the result is the plan.

    Raises
    ------
    InvalidParameterError
        If ``format`` is not allowed, ``output`` and ``inject`` are both given, or
        ``inject`` is given without ``format="agents-md-block"``.
    ConflictError
        If ``output`` exists and ``force`` is not given.
    OutputError
        If the file cannot be written.

    Examples
    --------
    >>> text = commands_guide(format="llms").result.text
    >>> text.splitlines()[0]
    '# Hydrolog'
    """
    if format not in GUIDE_FORMATS:
        allowed = ", ".join(GUIDE_FORMATS)
        raise InvalidParameterError(
            f"Option 'format': {format!r} is not one of: {allowed}",
            details={
                "option": "format",
                "reason": "choice",
                "allowed": list(GUIDE_FORMATS),
                "value": str(format),
            },
            hint=f"Allowed values: {allowed}.",
        )
    if output is not None and inject is not None:
        _option_error(
            "inject",
            "one_of",
            "Options 'output' and 'inject' are alternatives: give one of them",
            "Use 'output' to write a whole file, 'inject' to update a block.",
        )
    if inject is not None and format != "agents-md-block":
        _option_error(
            "inject",
            "not_applicable",
            "Option 'inject' needs format 'agents-md-block'",
            "Add --format agents-md-block.",
        )
    if output is None and inject is None:
        if check:
            return plan_output(plan_outputs({}, force=force))
        return OperationOutput(GuideDocument(format, agent_guide(format)))
    document = GuideDocument(format, agent_guide(format))
    if inject is not None:
        plan = plan_outputs({"inject": inject}, force=True)
    else:
        plan = plan_outputs({"output": output}, force=force)
    if check:
        return plan_output(plan)
    if (error := conflict_error(plan)) is not None:
        raise error
    target = Path(plan.targets[0].path)
    text = document.text
    if inject is not None:
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        text = inject_block(existing, document.text)
    _write_text(text, target)
    return OperationOutput(document, files=(target,), replaced=plan.replaced)
