"""Instructions of the MCP server: the rules of the agent guide, in short.

The text is the ``instructions`` field of the server; clients load it at the start of
every session, so it stays short (:data:`MAX_CHARS`). The rules are those of the agent
guide (:func:`hydrolog.agent_guide.principles`), the same text as in ``AGENTS.md`` and
``llms.txt``; what depends on the catalog and on the server -- the names of the
discovery tools and the allowed directories -- is read from them, never typed here. The
tool descriptions do not repeat what is said here once (rules, result, errors); the
full guide is one tool call away (``commands_guide``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Final

from hydrolog.agent_guide import principles
from hydrolog.catalog import Command
from hydrolog.catalog.spec import Lang
from hydrolog.exceptions import NotFoundError

__all__ = ["MAX_BYTES", "build_instructions"]

MAX_BYTES: Final = 1536
"""Upper bound of the length of the instructions in UTF-8 bytes (1.5 KiB). The text of
the real catalog stays below it; every allowed directory adds its path (tests check
the bound for a server without directories)."""

_INTRO: Final[Mapping[Lang, str]] = {
    "pl": (
        "Narzędzie = komenda katalogu (nazwa = operation_id, np. {example}): "
        "{list_tool} — spis, {schema_tool} — opcje, {guide_tool} — pełny przewodnik. "
        "Wynik to koperta hydrolog-result/1 (result, inputs, files, notices — "
        "ostrzeżenia przekaż użytkownikowi)."
    ),
    "en": (
        "A tool = a catalog command (name = operation_id, e.g. {example}): "
        "{list_tool} — the list, {schema_tool} — the options, {guide_tool} — the full "
        "guide. A result is the hydrolog-result/1 envelope (result, inputs, files, "
        "notices — pass warnings on to the user)."
    ),
}
_RULES: Final[Mapping[Lang, str]] = {"pl": "Zasady:", "en": "Rules:"}
_DIRS: Final[Mapping[Lang, str]] = {
    "pl": "Katalogi dozwolone: {dirs}.",
    "en": "Allowed directories: {dirs}.",
}
_NO_DIRS: Final[Mapping[Lang, str]] = {
    "pl": (
        "Brak katalogów dozwolonych (--allow-dir): opcje typu path są odrzucane "
        "(forbidden), komendy bez plików działają."
    ),
    "en": (
        "No allowed directories (--allow-dir): path options are refused (forbidden), "
        "commands without files work."
    ),
}


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
    commands: Sequence[Command], *, lang: Lang, allowed_dirs: Sequence[str]
) -> str:
    """Build the ``instructions`` text of the server.

    Parameters
    ----------
    commands : sequence of Command
        The catalog the server serves; it must hold the ``commands list``,
        ``commands schema`` and ``commands guide`` commands, which the text sends the
        agent to.
    lang : {"pl", "en"}
        Language of the text.
    allowed_dirs : sequence of str
        Absolute directories the server allows for files; empty when it allows none.

    Returns
    -------
    str
        An introduction (what a tool is, the discovery tools, the result envelope),
        the rules of the agent guide (:func:`hydrolog.agent_guide.principles`) and a
        line on the allowed directories.

    Raises
    ------
    NotFoundError
        If the catalog lacks the ``commands list``, ``commands schema`` or
        ``commands guide`` command.
    """
    intro = _INTRO[lang].format(
        example=commands[0].operation_id,
        list_tool=_operation_id(commands, "commands list"),
        schema_tool=_operation_id(commands, "commands schema"),
        guide_tool=_operation_id(commands, "commands guide"),
    )
    rules = [
        f"{number}. {rule}" for number, rule in enumerate(principles(lang), start=1)
    ]
    if allowed_dirs:
        files = _DIRS[lang].format(dirs=", ".join(allowed_dirs))
    else:
        files = _NO_DIRS[lang]
    return "\n".join([intro, _RULES[lang], *rules, files])
