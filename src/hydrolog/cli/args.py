"""The outer layer of the command line: general flags, command words and the rest.

``hydrolog [--json] [--schema] [--lang pl|en] [-v | -q] [-V] [-h] <group> <command>``

The general flags may stand before the group, between the words or (read again by the
command parser) after the command. :func:`split_arguments` peels them off the front and
returns the up to two command words and the remaining words; the command parser
(:mod:`hydrolog.cli.parser`) reads those. Doing the lookup of the group and command
here, rather than in argparse, makes an unknown command a ``not_found`` error (with
suggestions) instead of a usage error.

The language is the one thing that must be known *before* parsing (the help is printed
while the command line is being parsed), so it is taken from the last ``--lang``
anywhere in the command line (:func:`peek`) and validated by :func:`resolve_lang`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from hydrolog.catalog.spec import LANGUAGES, Lang
from hydrolog.cli.parser import UsageError
from hydrolog.cli.texts import env_lang
from hydrolog.exceptions import InvalidParameterError

__all__ = ["MCP_WORD", "Flags", "Invocation", "peek", "resolve_lang", "split_arguments"]

MCP_WORD = "mcp"
"""First word of the one subcommand that is not a catalog command."""

_SWITCHES = {
    "--json": "json",
    "--schema": "schema",
    "-V": "version",
    "--version": "version",
    "-v": "verbose",
    "--verbose": "verbose",
    "-q": "quiet",
    "--quiet": "quiet",
    "-h": "help",
    "--help": "help",
}


@dataclass
class Flags:
    """Switches found before the command word(s).

    Attributes
    ----------
    json, schema, version, help, verbose, quiet : bool
        The corresponding flag was given.
    """

    json: bool = False
    schema: bool = False
    version: bool = False
    help: bool = False
    verbose: bool = False
    quiet: bool = False


@dataclass
class Invocation:
    """The command line split into general flags, command words and the rest.

    Attributes
    ----------
    flags : Flags
        Switches found before the last command word.
    words : list of str
        The command words: ``[]``, ``["tc"]``, ``["tc", "kirpich"]`` or ``["mcp"]``.
    rest : list of str
        Everything after the last command word, for the command parser.
    """

    flags: Flags = field(default_factory=Flags)
    words: list[str] = field(default_factory=list)
    rest: list[str] = field(default_factory=list)


def split_arguments(arguments: Sequence[str]) -> Invocation:
    """Split a command line into general flags, command words and the rest.

    Parameters
    ----------
    arguments : sequence of str
        The command line without the program name.

    Returns
    -------
    Invocation
        The switches found before the command words, the words (``mcp`` alone, or group
        and command) and the remaining words. The value of a leading ``--lang`` is
        skipped, not recorded (see :func:`peek`).

    Raises
    ------
    UsageError
        If ``--lang`` has no value or an unknown option stands before the command
        (options follow the command).
    """
    invocation = Invocation()
    flags = invocation.flags
    index = 0
    while index < len(arguments):
        word = arguments[index]
        if word in _SWITCHES:
            setattr(flags, _SWITCHES[word], True)
        elif word == "--lang":
            if index + 1 >= len(arguments):
                raise UsageError("argument --lang: expected one argument")
            index += 1
        elif word.startswith("--lang="):
            pass
        elif word.startswith("-") and len(word) > 1:
            raise UsageError(
                f"Unknown option {word!r} before the command name",
                details={"reason": "unknown_option", "option": word},
                hint=(
                    "Options follow the command: "
                    "hydrolog <group> <command> --option VALUE. "
                    "See 'hydrolog --help'."
                ),
            )
        else:
            invocation.words.append(word)
            if len(invocation.words) == 2 or word == MCP_WORD:
                index += 1
                break
        index += 1
    invocation.rest = list(arguments[index:])
    return invocation


def peek(arguments: Sequence[str]) -> tuple[bool, str | None]:
    """Find ``--json`` and the last ``--lang`` anywhere in a command line.

    The help is printed while the command line is parsed and a failure may occur before
    it is parsed, so both the language and the format of an error must be known first.

    Parameters
    ----------
    arguments : sequence of str
        The command line without the program name.

    Returns
    -------
    tuple
        ``(json_requested, lang_text)``; ``lang_text`` is ``None`` without ``--lang``.
    """
    json_requested = False
    lang: str | None = None
    for index, word in enumerate(arguments):
        if word == "--json":
            json_requested = True
        elif word == "--lang" and index + 1 < len(arguments):
            lang = arguments[index + 1]
        elif word.startswith("--lang="):
            lang = word.partition("=")[2]
    return json_requested, lang


def resolve_lang(explicit: str | None) -> Lang:
    """Return the language of help and messages.

    Parameters
    ----------
    explicit : str or None
        Text of ``--lang``; ``None`` selects the settings (``HYDROLOG_LANG``,
        ``NOGAT_LANG``, ``nogat.toml``) and then Polish.

    Returns
    -------
    {"pl", "en"}
        The language.

    Raises
    ------
    InvalidParameterError
        If ``explicit`` is neither ``pl`` nor ``en`` (``reason="choice"``).
    """
    if explicit is None:
        return env_lang()
    if explicit == "pl":
        return "pl"
    if explicit == "en":
        return "en"
    allowed = ", ".join(LANGUAGES)
    raise InvalidParameterError(
        f"Option 'lang': {explicit!r} is not one of: {allowed}",
        details={
            "option": "lang",
            "reason": "choice",
            "allowed": list(LANGUAGES),
            "value": explicit,
        },
        hint=f"Allowed values: {allowed}.",
    )
