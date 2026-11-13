"""Operations of the group ``commands``: the catalog describing itself.

``commands list`` lists the catalog commands, ``commands schema`` returns the
``hydrolog-commands/1`` description of one command or a page of the whole catalog,
``commands guide`` the English guide for AI agents generated from the catalog
(and, with ``output`` or ``inject``, writes it to a file) and ``commands batch`` runs
the catalog calls of a JSON Lines file in one process. The functions are re-exported
by :mod:`hydrolog.operations`; the conventions of the operation layer are described
there.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, NoReturn

from hydrolog._atomic import atomic_output
from hydrolog._serialization import JsonResultMixin
from hydrolog.agent_guide import GUIDE_FORMATS, GuideFormat, agent_guide, inject_block
from hydrolog.catalog import data_commands
from hydrolog.catalog.dispatch import call_allowed_dirs, get_command, run_command
from hydrolog.catalog.document import (
    catalog_document,
    command_list,
    paginate,
)
from hydrolog.catalog.envelope import Item, OperationOutput
from hydrolog.catalog.inputs import read_json_lines
from hydrolog.catalog.spec import Command
from hydrolog.exceptions import InvalidParameterError, OutputError, error_document
from hydrolog.operations._outputs import (
    conflict_error,
    plan_output,
    plan_outputs,
    refuse_input_as_output,
)

__all__ = [
    "BATCH_REFUSED",
    "BatchFailure",
    "BatchResult",
    "GuideDocument",
    "commands_batch",
    "commands_guide",
    "commands_list",
    "commands_schema",
]

_LOG = logging.getLogger(__name__)

BATCH_REFUSED: Final = frozenset({"commands batch", "gui serve"})
"""Commands that a batch does not run: itself and the server that runs until stopped.

A batch also refuses a call that would go online (``precip pmaxtp``) or write a file
(an output option given, :func:`_refusal`): its plan is then the one file it writes
and its effects those of its catalog entry (offline, one ``output``).
"""


def _refusal(command: Command, options: dict[str, Any]) -> str | None:
    """Return why a batch does not run this call, or ``None`` when it does."""
    if command.name in BATCH_REFUSED:
        return "a batch does not run it"
    if command.network:
        return "it uses the network and a batch runs offline"
    written = [
        option.name
        for option in command.options
        if option.writes and options.get(option.name) not in (None, "")
    ]
    if written:
        return (
            f"it would write a file ({', '.join(written)}) and a batch writes only "
            "its output"
        )
    return None


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
        ``result`` is the ``hydrolog-commands/1`` document; that of one command also
        carries the typical ranges it checks (``typical_ranges``), a page of the
        catalog does not (ADR-0017); ``page`` is set for the whole catalog.

    Raises
    ------
    NotFoundError
        If ``command`` does not exist.
    InvalidParameterError
        If ``cursor`` is not a cursor of this collection.
    """
    if command is not None:
        return OperationOutput(
            catalog_document((get_command(command),), typical_ranges=True)
        )
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


# --- batch ----------------------------------------------------------------------------


@dataclass
class BatchFailure(JsonResultMixin):
    """A call of a batch that failed.

    Attributes
    ----------
    line : int
        Line of the call in the input file, from 1; also the line of its error
        document in the output file.
    command : str or None
        The command of the call: its catalog name, the text of the line when no
        command has it, ``None`` when the line names none.
    code : str
        The ``code`` of the error document.
    """

    line: int
    command: str | None
    code: str


@dataclass
class BatchResult(JsonResultMixin):
    """Summary of a batch (``commands batch``).

    Attributes
    ----------
    n_calls : int
        Calls (lines) of the input file.
    n_ok : int
        Calls whose line in the output file is a ``hydrolog-result/1`` envelope.
    n_failed : int
        Calls whose line is a ``hydrolog-error/1`` document.
    failed : list of BatchFailure
        The failed calls, in the order of the file.
    """

    n_calls: int
    n_ok: int
    n_failed: int
    failed: list[BatchFailure] = field(default_factory=list)


def _bad_line(number: int, problem: str) -> InvalidParameterError:
    """Return the ``validation_error`` of a line that is not a call."""
    return InvalidParameterError(
        f"Line {number} of the batch is not a call: {problem}",
        details={"option": "input_file", "reason": "invalid_call", "line": number},
        hint=(
            'Write each call on one line as {"command": "<group> <verb>", '
            '"options": {...}}.'
        ),
    )


def _call_of(item: object, number: int) -> tuple[Command, dict[str, Any]]:
    """Return the command and the options of the parsed line ``number``.

    Raises
    ------
    InvalidParameterError
        If the line is not ``{"command": str, "options": object}`` (``reason``
        ``invalid_call``) or is a call that a batch does not run (``not_in_batch``):
        ``commands batch``, ``gui serve``, a command that uses the network, a call
        that gives an output option.
    NotFoundError
        If no command has the name.
    """
    if isinstance(item, ValueError):
        raise _bad_line(number, f"not JSON ({item})")
    if not isinstance(item, dict) or set(item) != {"command", "options"}:
        raise _bad_line(
            number, "not a JSON object with exactly the keys command and options"
        )
    name, options = item["command"], item["options"]
    if not isinstance(name, str) or not isinstance(options, dict):
        raise _bad_line(number, "command must be a string and options a JSON object")
    command = get_command(name)
    refusal = _refusal(command, options)
    if refusal is not None:
        raise InvalidParameterError(
            f"Line {number} of the batch calls {command.name!r}, which a batch does "
            f"not run: {refusal}",
            details={"option": "input_file", "reason": "not_in_batch", "line": number},
            hint="Run it on its own.",
        )
    return command, options


def _named(item: object) -> str | None:
    """Return the text a line gives as its command, if any."""
    if isinstance(item, dict) and isinstance(item.get("command"), str):
        return str(item["command"])
    return None


def _against(command: Command, options: dict[str, Any], base: Path) -> dict[str, Any]:
    """Return the options with each relative path option taken under ``base``."""
    resolved = dict(options)
    for option in command.options:
        value = resolved.get(option.name)
        if (
            option.type == "path"
            and isinstance(value, str)
            and value.strip()
            and not Path(os.path.expanduser(value)).is_absolute()
        ):
            resolved[option.name] = str(base / value)
    return resolved


def _line_text(document: dict[str, Any]) -> str:
    """Return a document as the CLI prints it with ``--json``: a line of UTF-8 JSON."""
    return json.dumps(document, ensure_ascii=False, allow_nan=False)


def _run_line(
    item: object, number: int, base: Path, allowed: tuple[str, ...] | None
) -> tuple[str, BatchFailure | None, Item]:
    """Run the call of one line: its output line, its failure and its item."""
    command: Command | None = None
    try:
        command, options = _call_of(item, number)
        envelope = run_command(
            command, _against(command, options, base), allowed_dirs=allowed
        ).to_dict()
        return _line_text(envelope), None, Item(number, "ok")
    except Exception as exc:
        name = None if command is None else command.name
        document = error_document(exc, name)
        if document["code"] == "internal_error":
            _LOG.error(
                "Line %d of the batch failed with an internal error",
                number,
                exc_info=exc,
            )
        details = document["details"]
        reason = details.get("reason") if isinstance(details, dict) else None
        failure = BatchFailure(number, name or _named(item), document["code"])
        outcome = Item(
            number,
            "failed",
            code=document["code"],
            reason=reason if isinstance(reason, str) else None,
            message=document["message"],
        )
        return _line_text(document), failure, outcome


def commands_batch(
    *,
    input_file: str | os.PathLike[str],
    output: str | os.PathLike[str],
    force: bool = False,
    check: bool = False,
) -> OperationOutput:
    r"""Run the catalog calls of a JSON Lines file in one process (``commands batch``).

    Each line of ``input_file`` is one call, ``{"command": "<name or operation id>",
    "options": {...}}``; line i of ``output`` is the result of call i: the
    ``hydrolog-result/1`` envelope of :func:`hydrolog.catalog.run_command`, or the
    ``hydrolog-error/1`` document of its error
    (:func:`hydrolog.exceptions.error_document`), as compact UTF-8 JSON, the very line
    that the command line prints with ``--json`` for the call alone (the envelope on
    stdout, the error document as the last line of stderr). A failing call does not
    stop the batch. A relative path in the options of a call is taken from the
    directory of ``input_file``, and the call runs under the path policy of the batch
    itself (the ``allowed_dirs`` of its own call, MCP's ``--allow-dir``). A line that
    is not such a call gets a ``validation_error`` document, and so does a call that a
    batch does not run (``not_in_batch``): ``commands batch``, ``gui serve``, a
    command that uses the network (``precip pmaxtp``) and a call that gives an output
    option (``output``, ``output_dir``, ``schematic``): a batch runs offline and writes
    only its ``output``, so its plan and its effects are those of its catalog entry.

    Parameters
    ----------
    input_file : str or os.PathLike
        The calls: a UTF-8 JSON Lines file, one call per line (no blank lines).
    output : str or os.PathLike
        The JSON Lines file of the results, written atomically when the last call is
        done (missing directories are created); an existing file is replaced only with
        ``force``.
    force : bool, optional
        Replace an existing ``output`` file, by default ``False``.
    check : bool, optional
        Plan without effects: return the ``hydrolog-plan/1`` document of ``output``,
        run nothing and write nothing.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`BatchResult` (counts and the failed calls) with the
        written file; ``items`` holds the outcome of each line (``id`` the line), so the
        envelope's ``status`` is ``partial`` when some calls failed and ``failed`` when
        all did. With ``check`` the result is the plan.

    Raises
    ------
    InvalidParameterError
        If ``output`` is ``input_file``.
    ConflictError
        If ``output`` exists and ``force`` is not given.
    NotFoundError, InputDataError
        If ``input_file`` does not exist, cannot be read or has no line.
    OutputError
        If ``output`` cannot be written.
    """
    refuse_input_as_output(output, {"input_file": input_file})
    plan = plan_outputs({"output": output}, force=force)
    if check:
        return plan_output(plan)
    if (error := conflict_error(plan)) is not None:
        raise error
    calls = read_json_lines(input_file)
    base = Path(input_file).parent
    allowed = call_allowed_dirs()
    target = Path(plan.targets[0].path)
    failed: list[BatchFailure] = []
    items: list[Item] = []
    try:
        with (
            atomic_output(target) as temporary,
            temporary.open("w", encoding="utf-8", newline="\n") as stream,
        ):
            for number, item in enumerate(calls, start=1):
                line, failure, outcome = _run_line(item, number, base, allowed)
                stream.write(line + "\n")
                items.append(outcome)
                if failure is not None:
                    failed.append(failure)
    except OSError as exc:
        raise OutputError(
            f"Cannot write the results of the batch {target}: {exc}",
            details={"path": str(target), "reason": "output_unwritable"},
        ) from exc
    result = BatchResult(
        n_calls=len(calls),
        n_ok=len(calls) - len(failed),
        n_failed=len(failed),
        failed=failed,
    )
    return OperationOutput(result, files=(target,), replaced=plan.replaced, items=items)
