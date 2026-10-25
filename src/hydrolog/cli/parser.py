"""The argparse parsers of the command line, generated from the catalog.

Every catalog command gets one parser (:func:`build_command_parser`): each
:class:`~hydrolog.catalog.Option` becomes a ``--kebab-case`` flag whose text is
converted to a JSON-native value by :func:`~hydrolog.cli.values.parse_option_value`.
Required options, ``one_of`` groups, bounds and choices are *not* enforced by argparse
but by the catalog (:func:`~hydrolog.catalog.validate_command`), so that the CLI, the
MCP server and Python callers fail the same way. The parsers of the root
(``hydrolog --help``), of a group (``hydrolog tc --help``) and of ``hydrolog mcp``
complete the set.

Conventions of the command line
-------------------------------
* Options are flags only (``--length-km 8.2`` or ``--length-km=8.2``); there are no
  positional arguments and abbreviations are not accepted (a growing catalog must not
  change what a script means).
* A ``boolean`` option is the pair ``--flag`` (true) and ``--no-flag`` (false); it
  takes no value.
* A negative number is accepted after a flag (``--offset -5``, ``--values -1,2``).
* The global flags ``--json``, ``--schema``, ``--lang``, ``-v/--verbose``,
  ``-q/--quiet`` and ``-V/--version`` are accepted before the group and after the
  command; a command option may not use their names.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shlex
import shutil
import textwrap
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, NoReturn

from hydrolog._serialization import to_jsonable
from hydrolog.catalog.spec import Command, Lang, Option
from hydrolog.cli.texts import text
from hydrolog.cli.values import parse_option_value
from hydrolog.exceptions import InvalidParameterError

__all__ = [
    "GLOBAL_FLAGS",
    "CatalogParser",
    "CommandLine",
    "UsageError",
    "build_command_parser",
    "build_group_parser",
    "build_mcp_parser",
    "build_root_parser",
    "example_arguments",
    "format_example",
    "join_negative_values",
    "parse_command_line",
]

GLOBAL_FLAGS: Final = (
    "--help",
    "--json",
    "--schema",
    "--lang",
    "--verbose",
    "--quiet",
    "--version",
)
"""Flags of every command line; a command option may not use them."""

DEST_JSON: Final = "global:json"
DEST_SCHEMA: Final = "global:schema"
DEST_LANG: Final = "global:lang"
DEST_VERBOSE: Final = "global:verbose"
DEST_QUIET: Final = "global:quiet"
"""Namespace attributes of the flags that are not options of a command."""

_NEGATIVE_VALUE: Final = re.compile(r"-[0-9.]")
_METAVARS: Final = {
    "number": "NUMBER",
    "integer": "INT",
    "string": "TEXT",
    "path": "PATH",
    "number_list": "N1,N2,...",
    "string_list": "S1,S2,...",
    "object": "JSON",
    "object_list": "JSON",
}
_NUMERIC: Final = ("number", "integer", "number_list")
_VALUE_INDENT: Final = 4
_USAGE_HANG: Final = 4


class UsageError(InvalidParameterError):
    """A command line that argparse or the CLI cannot interpret (``validation_error``).

    Parameters
    ----------
    message : str
        What is wrong (English).
    prog : str, optional
        Program name of the parser that reported it (``"hydrolog tc kirpich"``).
    command : str, optional
        Catalog name of the command being parsed, if known.
    details : Mapping[str, object], optional
        Machine-readable context added to ``reason="usage"``.
    hint : str, optional
        Remediation; defaults to a pointer to ``<prog> --help``.

    Attributes
    ----------
    prog : str
        Program name of the parser that reported the error.
    command : str or None
        Catalog name of the command being parsed.
    """

    def __init__(
        self,
        message: str,
        *,
        prog: str = "hydrolog",
        command: str | None = None,
        details: Mapping[str, object] | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(
            message,
            details={"reason": "usage", **(details or {})},
            hint=hint or f"Run '{prog} --help' to see the usage.",
        )
        self.prog = prog
        self.command = command


class CatalogParser(argparse.ArgumentParser):
    """``ArgumentParser`` that reports usage errors as :class:`UsageError`.

    The standard parser prints to stderr and exits with status 2; this one raises, so
    that the entry point reports the error as ``--json`` or as readable text, with the
    exit code of ``validation_error``.

    Parameters
    ----------
    *args, **kwargs
        Passed to :class:`argparse.ArgumentParser`.
    command : Command, optional
        The catalog command this parser reads (``None`` for the root, a group and
        ``mcp``).
    headline : str, optional
        One sentence printed before the usage line (AGI-3.7): what the command does.
    """

    def __init__(
        self,
        *args: Any,
        command: Command | None = None,
        headline: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.command = command
        self.headline = headline

    def format_help(self) -> str:
        """Return the help text; it starts with the headline, if there is one."""
        body = super().format_help()
        return f"{self.headline}\n\n{body}" if self.headline else body

    def error(self, message: str) -> NoReturn:
        """Raise :class:`UsageError` instead of printing and exiting."""
        raise UsageError(
            message,
            prog=self.prog,
            command=self.command.name if self.command else None,
        )


# --- help formatting ------------------------------------------------------------------


class _Formatter(argparse.HelpFormatter):
    """Help formatter: wraps paragraphs, keeps indented lines verbatim."""

    usage_prefix = "usage: "

    def __init__(self, prog: str) -> None:
        super().__init__(prog, max_help_position=30)

    def add_usage(
        self,
        usage: str | None,
        actions: Iterable[argparse.Action],
        groups: Iterable[Any],
        prefix: str | None = None,
    ) -> None:
        super().add_usage(usage, actions, groups, self.usage_prefix)

    def _split_lines(self, text: str, width: int) -> list[str]:
        return textwrap.wrap(
            " ".join(text.split()),
            width,
            break_long_words=False,
            break_on_hyphens=False,
        )

    def _fill_text(self, text: str, width: int, indent: str) -> str:
        lines: list[str] = []
        paragraph: list[str] = []

        def flush() -> None:
            if paragraph:
                joined = " ".join(" ".join(paragraph).split())
                lines.append(
                    textwrap.fill(
                        joined,
                        width,
                        initial_indent=indent,
                        subsequent_indent=indent,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                )
                paragraph.clear()

        for line in text.splitlines():
            if not line.strip():
                flush()
                lines.append("")
            elif line[0].isspace():
                flush()
                lines.append(indent + line)
            else:
                paragraph.append(line)
        flush()
        return "\n".join(lines)


def _formatter_for(lang: Lang) -> type[argparse.HelpFormatter]:
    """Formatter class whose ``usage:`` prefix is in ``lang``."""
    return type(
        "Formatter", (_Formatter,), {"usage_prefix": text("usage_prefix", lang)}
    )


def _escape(value: str) -> str:
    """Escape ``%``: argparse applies ``%``-formatting to help and usage strings."""
    return value.replace("%", "%%")


def _wrap_usage(words: Sequence[str], lang: Lang) -> str:
    """Wrap a usage line with a hanging indent (hyphenated flags stay whole)."""
    lead = text("usage_prefix", lang)
    wrapped = textwrap.fill(
        lead + " ".join(words),
        max(shutil.get_terminal_size().columns - 2, 40),
        subsequent_indent=" " * (len(lead) + _USAGE_HANG),
        break_long_words=False,
        break_on_hyphens=False,
    )
    return wrapped[len(lead) :]


# --- examples -------------------------------------------------------------------------


def _number_text(value: Any) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    rendered = repr(float(value))
    return rendered[:-2] if rendered.endswith(".0") else rendered


def _value_text(option: Option, value: Any) -> str:
    """Command-line text that :func:`parse_option_value` turns back into ``value``."""
    kind = option.type
    if kind in ("number", "integer"):
        return _number_text(value)
    if kind == "number_list":
        return ",".join(_number_text(item) for item in value)
    if kind == "string_list":
        items = [str(item) for item in value]
        if any("," in item or not item.strip() for item in items) or (
            items and items[0].lstrip().startswith("[")
        ):
            return json.dumps(items, ensure_ascii=False)
        return ",".join(items)
    if kind in ("object", "object_list"):
        return json.dumps(to_jsonable(value), ensure_ascii=False, separators=(",", ":"))
    return os.fspath(value) if isinstance(value, os.PathLike) else str(value)


def example_arguments(command: Command, example: Mapping[str, object]) -> list[str]:
    """Return the command-line words that give ``command`` an example's options.

    Parameters
    ----------
    command : Command
        The command.
    example : Mapping[str, object]
        Option values (JSON-native), e.g. an entry of ``Command.examples``; ``None``
        values are skipped.

    Returns
    -------
    list of str
        Words to put after ``hydrolog <group> <command>``: ``--flag value`` pairs
        (``--flag=value`` for a value that starts with ``-``) in catalog order and
        ``--flag``/``--no-flag`` for booleans.
    """
    words: list[str] = []
    for option in command.options:
        value = example.get(option.name)
        if value is None:
            continue
        if option.type == "boolean":
            words.append(option.flag if value else "--no-" + option.flag[2:])
            continue
        rendered = _value_text(option, value)
        if rendered.startswith("-"):
            words.append(f"{option.flag}={rendered}")
        else:
            words.extend((option.flag, rendered))
    return words


def format_example(command: Command, example: Mapping[str, object]) -> str:
    """Return an example as a shell command line (``hydrolog tc kirpich --...``)."""
    words = ["hydrolog", *command.name.split(), *example_arguments(command, example)]
    return shlex.join(words)


# --- general flags --------------------------------------------------------------------


class _BooleanAction(argparse.Action):
    """The pair ``--flag`` / ``--no-flag`` that stores ``True`` / ``False``."""

    def __init__(self, option_strings: Sequence[str], dest: str, **kwargs: Any) -> None:
        strings: list[str] = []
        for flag in option_strings:
            strings.extend((flag, "--no-" + flag[2:]))
        super().__init__(strings, dest, nargs=0, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        setattr(namespace, self.dest, not (option_string or "").startswith("--no-"))


def _add_general_arguments(group: argparse._ArgumentGroup, lang: Lang) -> None:
    """Add ``-h``, ``-V``, ``--json``, ``--schema``, ``--lang``, ``-v`` and ``-q``."""
    import hydrolog

    group.add_argument("-h", "--help", action="help", help=text("help_help", lang))
    group.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"hydrolog {hydrolog.__version__}",
        help=text("help_version", lang),
    )
    group.add_argument(
        "--json",
        dest=DEST_JSON,
        action="store_true",
        default=argparse.SUPPRESS,
        help=text("help_json", lang),
    )
    group.add_argument(
        "--schema",
        dest=DEST_SCHEMA,
        action="store_true",
        default=argparse.SUPPRESS,
        help=text("help_schema", lang),
    )
    group.add_argument(
        "--lang",
        dest=DEST_LANG,
        metavar="{pl,en}",
        default=argparse.SUPPRESS,
        help=_escape(text("help_lang", lang)),
    )
    group.add_argument(
        "-v",
        "--verbose",
        dest=DEST_VERBOSE,
        action="store_true",
        default=argparse.SUPPRESS,
        help=text("help_verbose", lang),
    )
    group.add_argument(
        "-q",
        "--quiet",
        dest=DEST_QUIET,
        action="store_true",
        default=argparse.SUPPRESS,
        help=text("help_quiet", lang),
    )


# --- command parser -------------------------------------------------------------------


def _option_dest(option: Option) -> str:
    """Namespace attribute of an option; the prefix avoids clashes with argparse."""
    return f"option:{option.name}"


def _metavar(option: Option) -> str:
    if option.type == "choice":
        return "{" + ",".join(option.choices) + "}"
    return _METAVARS[option.type]


def _spell(option: Option) -> str:
    """``--flag METAVAR`` (just ``--flag`` for a boolean)."""
    if option.type == "boolean":
        return option.flag
    return f"{option.flag} {_metavar(option)}"


def _default_text(option: Option, lang: Lang) -> str:
    value = option.default
    if isinstance(value, bool):
        return text("yes" if value else "no", lang)
    if isinstance(value, list | tuple):
        return ",".join(str(item) for item in value)
    return str(value)


def _option_help(option: Option, lang: Lang) -> str:
    """Return the description with its unit and its default, as shown in ``--help``."""
    description = str(option.json_schema(lang)["description"])
    if option.default is not None:
        note = text("default_note", lang, value=_default_text(option, lang))
        description = f"{description} ({note})"
    return _escape(description)


def _command_usage(command: Command, lang: Lang) -> str:
    """Usage line: required options spelled out, the rest as ``[options]``."""
    by_name = {option.name: option for option in command.options}
    words = ["hydrolog", *command.name.split()]
    words.extend(_spell(option) for option in command.options if option.required)
    if command.one_of:
        alternatives = (
            " ".join(_spell(by_name[name]) for name in group)
            for group in command.one_of
        )
        words.append("(" + " | ".join(alternatives) + ")")
    words.append("[" + text("options", lang) + "]")
    return _escape(_wrap_usage(words, lang))


def _values_block(command: Command, lang: Lang) -> str:
    """Return the values of the choice options with their meanings (AGI-3.7)."""
    width = max(shutil.get_terminal_size().columns - 2, 40)
    lines = [text("values_title", lang)]
    for option in command.options:
        if option.type != "choice":
            continue
        meanings = option.meanings_pl if lang == "pl" else option.meanings
        lines.append(f"  {option.flag}:")
        pad = max(len(value) for value in option.choices)
        for value in option.choices:
            lead = " " * _VALUE_INDENT + value.ljust(pad) + "  "
            lines.extend(
                textwrap.wrap(
                    meanings[value],
                    width,
                    initial_indent=lead,
                    subsequent_indent=" " * len(lead),
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
    return "\n".join(lines)


def _command_epilog(command: Command, lang: Lang) -> str:
    """Return the notes after the options; the examples come last (AGI-3.7)."""
    blocks: list[str] = []
    if command.one_of:
        by_name = {option.name: option for option in command.options}
        lines = [text("one_of_title", lang)]
        lines.extend(
            "  " + " ".join(_spell(by_name[name]) for name in group)
            for group in command.one_of
        )
        blocks.append("\n".join(lines))
    if any(option.type == "choice" for option in command.options):
        blocks.append(_values_block(command, lang))
    if any(option.type in _NUMERIC for option in command.options):
        blocks.append(text("negative_values", lang))
    if command.examples:
        lines = [text("examples", lang)]
        lines.extend(
            "  " + format_example(command, example) for example in command.examples
        )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_command_parser(command: Command, lang: Lang = "pl") -> CatalogParser:
    """Build the parser of one catalog command.

    Parameters
    ----------
    command : Command
        The command; each option becomes a flag (``--length-km``), a ``boolean``
        option the pair ``--flag``/``--no-flag``.
    lang : {"pl", "en"}, optional
        Language of the help.

    Returns
    -------
    CatalogParser
        A parser whose namespace holds the *text* of the options that were given; use
        :func:`parse_command_line` to read it.

    Raises
    ------
    ValueError
        If an option name collides with a global flag (``json``, ``schema``,
        ``help``, ``version``, ``lang``, ``verbose``, ``quiet``) or with another
        option of the command.
    """
    parser = CatalogParser(
        prog=f"hydrolog {command.name}",
        usage=_command_usage(command, lang),
        description=command.describe(lang),
        epilog=_command_epilog(command, lang),
        formatter_class=_formatter_for(lang),
        add_help=False,
        allow_abbrev=False,
        command=command,
        headline=command.summarize(lang),
    )
    required = parser.add_argument_group(text("required_options", lang))
    optional = parser.add_argument_group(text("options", lang))
    taken: set[str] = set(GLOBAL_FLAGS)
    for option in command.options:
        spellings = {option.flag}
        if option.short_flag is not None:
            spellings.add(option.short_flag)
        if option.type == "boolean":
            spellings.add("--no-" + option.flag[2:])
        clash = sorted(spellings & taken)
        if clash:
            raise ValueError(
                f"Option {option.name!r} of command {command.name!r} collides with "
                f"the flag {clash[0]} (global flags: {', '.join(GLOBAL_FLAGS)})"
            )
        taken |= spellings
        target = required if option.required else optional
        if option.type == "boolean":
            target.add_argument(
                option.flag,
                dest=_option_dest(option),
                action=_BooleanAction,
                default=argparse.SUPPRESS,
                help=_option_help(option, lang),
            )
        else:
            target.add_argument(
                *([option.short_flag] if option.short_flag else []),
                option.flag,
                dest=_option_dest(option),
                metavar=_metavar(option),
                default=argparse.SUPPRESS,
                help=_option_help(option, lang),
            )
    general = parser.add_argument_group(text("general_options", lang))
    _add_general_arguments(general, lang)
    return parser


@dataclass(frozen=True)
class CommandLine:
    """What the words after ``hydrolog <group> <command>`` say.

    Attributes
    ----------
    options : dict
        JSON-native values of the command options that were given (not validated).
    json : bool
        ``--json`` was given.
    schema : bool
        ``--schema`` was given.
    verbose, quiet : bool
        ``-v/--verbose`` and ``-q/--quiet`` were given.

    Notes
    -----
    ``--lang`` is accepted here but not reported: the language is needed before the
    command line is parsed (see :func:`hydrolog.cli.args.peek`).
    """

    options: dict[str, Any]
    json: bool
    schema: bool
    verbose: bool = False
    quiet: bool = False


def join_negative_values(arguments: Sequence[str], command: Command) -> list[str]:
    """Glue ``--flag -5`` into ``--flag=-5``.

    This applies to the flags of ``command`` that take values.

    argparse reads a word that starts with ``-`` as an option unless it is a plain
    negative number, so ``--values -1,2`` and ``--x -1e-3`` would fail. The word after a
    value-taking flag that starts with ``-`` and a digit or a dot is such a value.

    Parameters
    ----------
    arguments : sequence of str
        Words after the command name.
    command : Command
        The command whose flags take values.

    Returns
    -------
    list of str
        The words with each such pair joined by ``=``.
    """
    value_flags = {"--lang"} | {
        option.flag for option in command.options if option.type != "boolean"
    }
    joined: list[str] = []
    index = 0
    while index < len(arguments):
        word = arguments[index]
        following = arguments[index + 1] if index + 1 < len(arguments) else ""
        if word in value_flags and _NEGATIVE_VALUE.match(following):
            joined.append(f"{word}={following}")
            index += 2
        else:
            joined.append(word)
            index += 1
    return joined


def _unrecognized(
    parser: CatalogParser, command: Command, extras: Sequence[str]
) -> UsageError:
    """Build the error for words the parser did not recognize, with a spelling hint."""
    word = extras[0]
    if not word.startswith("-"):
        return UsageError(
            f"Unexpected argument {word!r} for command {command.name!r}",
            prog=parser.prog,
            command=command.name,
            details={"reason": "unexpected_argument", "value": word},
            hint=f"Options start with '--'; see '{parser.prog} --help'.",
        )
    flag = word.split("=", 1)[0]
    known = sorted({option.flag for option in command.options} | set(GLOBAL_FLAGS))
    kebab = flag.replace("_", "-")
    close = [kebab] if kebab in known else difflib.get_close_matches(kebab, known, n=1)
    hint = f"See '{parser.prog} --help'."
    if close:
        hint = f"Did you mean {close[0]}? " + hint
    return UsageError(
        f"Unknown option {flag!r} for command {command.name!r}",
        prog=parser.prog,
        command=command.name,
        details={
            "reason": "unknown_option",
            "option": flag,
            "allowed": [option.flag for option in command.options],
        },
        hint=hint,
    )


def parse_command_line(
    command: Command, arguments: Sequence[str], lang: Lang = "pl"
) -> CommandLine:
    """Parse the words after ``hydrolog <group> <command>``.

    Parameters
    ----------
    command : Command
        The command.
    arguments : sequence of str
        Command-line words, e.g. ``["--length-km", "8.2", "--json"]``.
    lang : {"pl", "en"}, optional
        Language of the help that ``--help`` prints.

    Returns
    -------
    CommandLine
        Option values converted to JSON-native types, and the general flags.

    Raises
    ------
    UsageError
        For an unknown option, a flag without its value or an unexpected word.
    InvalidParameterError
        If the text of an option does not have the syntax of its type
        (``reason="type"``).
    SystemExit
        After ``--help`` or ``--version``, which print to stdout (status 0).
    """
    parser = build_command_parser(command, lang)
    namespace, extras = parser.parse_known_args(
        join_negative_values(arguments, command)
    )
    if extras:
        raise _unrecognized(parser, command, extras)
    given = vars(namespace)
    options: dict[str, Any] = {}
    for option in command.options:
        key = _option_dest(option)
        if key in given:
            options[option.name] = parse_option_value(option, given[key])
    return CommandLine(
        options=options,
        json=bool(given.get(DEST_JSON, False)),
        schema=bool(given.get(DEST_SCHEMA, False)),
        verbose=bool(given.get(DEST_VERBOSE, False)),
        quiet=bool(given.get(DEST_QUIET, False)),
    )


# --- root, group and mcp parsers ------------------------------------------------------


def _help_parser(
    prog: str, usage: str, description: str, epilog: str, lang: Lang
) -> CatalogParser:
    """Return a parser that only prints help (``usage`` is escaped, texts are not).

    The first sentence of ``description`` becomes the headline (AGI-3.7); the rest, if
    any, stays the description.
    """
    first, _, rest = description.strip().partition(". ")
    headline = first.rstrip(".") + "." if first else None
    return CatalogParser(
        prog=prog,
        usage=_escape(usage),
        description=rest or None,
        epilog=epilog or None,
        formatter_class=_formatter_for(lang),
        add_help=False,
        allow_abbrev=False,
        headline=headline,
    )


def _examples_block(commands: Sequence[Command], lang: Lang) -> str:
    """Examples built from the first catalog command that has one."""
    for command in commands:
        if command.examples:
            line = format_example(command, command.examples[0])
            return "\n".join(
                (
                    text("examples", lang),
                    f"  {line}",
                    f"  {line} --json",
                    f"  hydrolog {command.name} --schema",
                )
            )
    return ""


def by_group(commands: Sequence[Command]) -> dict[str, list[Command]]:
    """Group commands by their group, keeping the catalog order."""
    groups: dict[str, list[Command]] = defaultdict(list)
    for command in commands:
        groups[command.group].append(command)
    return dict(groups)


def build_root_parser(commands: Sequence[Command], lang: Lang = "pl") -> CatalogParser:
    """Build the parser that prints ``hydrolog --help`` (it parses nothing).

    Parameters
    ----------
    commands : sequence of Command
        The catalog; the groups are listed in its order, followed by ``mcp``.
    lang : {"pl", "en"}, optional
        Language of the help.

    Returns
    -------
    CatalogParser
        Parser whose help lists the general flags and the command groups.
    """
    lead = " " * len(text("usage_prefix", lang))
    usage = (
        f"hydrolog {text('root_usage_suffix', lang)}\n{lead}"
        "hydrolog mcp [--allow-dir DIR]... [--allow-writes] [--tools FAMILIES]"
    )
    epilog = "\n\n".join(
        block
        for block in (text("root_footer", lang), _examples_block(commands, lang))
        if block
    )
    parser = _help_parser(
        "hydrolog", usage, text("root_description", lang), epilog, lang
    )
    groups = parser.add_argument_group(text("groups_title", lang))
    for group, members in by_group(commands).items():
        names = ", ".join(member.subcommand for member in members)
        groups.add_argument(group, metavar=group, help=_escape(names))
    groups.add_argument("mcp", metavar="mcp", help=text("mcp_group_line", lang))
    general = parser.add_argument_group(text("general_options", lang))
    _add_general_arguments(general, lang)
    return parser


def build_group_parser(
    group: str, commands: Sequence[Command], lang: Lang = "pl"
) -> CatalogParser:
    """Build the parser that prints ``hydrolog <group> --help`` (it parses nothing).

    Parameters
    ----------
    group : str
        Group name (``"tc"``).
    commands : sequence of Command
        The commands of the group.
    lang : {"pl", "en"}, optional
        Language of the help.

    Returns
    -------
    CatalogParser
        Parser whose help lists the commands of the group with their summaries.
    """
    parser = _help_parser(
        f"hydrolog {group}",
        f"hydrolog {group} {text('group_usage_suffix', lang)}",
        text("group_description", lang, group=group),
        text("group_footer", lang, group=group),
        lang,
    )
    listing = parser.add_argument_group(text("group_title", lang, group=group))
    for command in commands:
        listing.add_argument(
            command.subcommand,
            metavar=command.subcommand,
            help=_escape(command.summarize(lang)),
        )
    general = parser.add_argument_group(text("general_options", lang))
    _add_general_arguments(general, lang)
    return parser


def build_mcp_parser(lang: Lang = "pl") -> CatalogParser:
    """Build the parser of ``hydrolog mcp``.

    Parameters
    ----------
    lang : {"pl", "en"}, optional
        Language of the help.

    Returns
    -------
    CatalogParser
        Parser of the server options (:func:`hydrolog.mcp.server.add_arguments`:
        ``--allow-dir DIR`` (repeatable), ``--allow-writes``, ``--tools FAMILIES``)
        and ``-h``. It has no ``--lang``: the MCP output is always English, so the
        option is refused when the server starts (:mod:`hydrolog.cli.main`); it still
        selects the language of this help.
    """
    from hydrolog.mcp.server import add_arguments

    parser = _help_parser(
        "hydrolog mcp",
        "hydrolog mcp [--allow-dir DIR]... [--allow-writes] [--tools FAMILIES]",
        text("mcp_description", lang),
        "",
        lang,
    )
    group = parser.add_argument_group(text("options", lang))
    group.add_argument("-h", "--help", action="help", help=text("help_help", lang))
    add_arguments(
        group,
        {
            "allow_dir": text("mcp_allow_dir", lang),
            "allow_writes": text("mcp_allow_writes", lang),
            "tools": text("mcp_tools", lang),
        },
    )
    return parser
