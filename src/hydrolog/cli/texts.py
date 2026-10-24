"""User-interface texts of the command line (Polish and English).

Catalog texts (summaries, option descriptions) come from the catalog itself; this
module holds only the words the CLI adds around them: help headings, section titles of
the summary, labels of errors. Error *messages* and *hints* are English everywhere (as
in :func:`hydrolog.exceptions.error_document`); only the registry titles are localized.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Final

from hydrolog.catalog.spec import Lang

__all__ = ["DEFAULT_LANG", "LANG_ENV", "env_lang", "text"]

DEFAULT_LANG: Final[Lang] = "pl"
"""Language used when neither ``--lang`` nor ``HYDROLOG_LANG`` selects one."""
LANG_ENV: Final = "HYDROLOG_LANG"
"""Environment variable that selects the language of help and messages."""

_TEXTS: Final[dict[str, tuple[str, str]]] = {
    # --- help ---------------------------------------------------------------------
    "usage_prefix": ("użycie: ", "usage: "),
    "required_options": ("opcje wymagane", "required options"),
    "options": ("opcje", "options"),
    "general_options": ("opcje ogólne", "general options"),
    "help_help": (
        "Pokaż tę pomoc i zakończ.",
        "Show this help and exit.",
    ),
    "help_version": (
        "Pokaż wersję i zakończ.",
        "Show the version and exit.",
    ),
    "help_json": (
        "Wypisz kopertę wyniku (hydrolog-result/1) jako JSON zamiast podsumowania.",
        "Print the result envelope (hydrolog-result/1) as JSON instead of the summary.",
    ),
    "help_schema": (
        "Wypisz schemat opcji (JSON Schema) zamiast uruchamiać.",
        "Print the option schema (JSON Schema) instead of running.",
    ),
    "help_lang": (
        "Język pomocy i komunikatów: pl lub en (domyślnie z HYDROLOG_LANG, "
        "w przeciwnym razie pl).",
        "Language of help and messages: pl or en (default from HYDROLOG_LANG, "
        "otherwise pl).",
    ),
    "default_note": ("domyślnie: {value}", "default: {value}"),
    "one_of_title": (
        "Wymagana dokładnie jedna z grup opcji:",
        "Exactly one of these option groups is required:",
    ),
    "examples": ("Przykłady:", "Examples:"),
    "negative_values": (
        "Wartości ujemne: --opcja -5 i --opcja=-5 są równoważne.",
        "Negative values: --option -5 and --option=-5 are equivalent.",
    ),
    "root_description": (
        "Hydrolog: obliczenia hydrologiczne (czas koncentracji, SCS-CN, hydrogramy "
        "jednostkowe i odpływu, statystyki przepływów, HSG). Komendy są generowane "
        "z katalogu, który zasila też bibliotekę Pythona i serwer MCP.",
        "Hydrolog: hydrological calculations (time of concentration, SCS-CN, unit "
        "hydrographs and runoff hydrographs, flow statistics, HSG). The commands are "
        "generated from the catalog that also drives the Python library and the MCP "
        "server.",
    ),
    "group_usage_suffix": (
        "[opcje ogólne] <komenda> [opcje komendy]",
        "[general options] <command> [command options]",
    ),
    "root_usage_suffix": (
        "[opcje ogólne] <grupa> <komenda> [opcje komendy]",
        "[general options] <group> <command> [command options]",
    ),
    "groups_title": ("grupy komend", "command groups"),
    "mcp_group_line": (
        "uruchom serwer MCP (stdio) dla agentów",
        "start the MCP server (stdio) for agents",
    ),
    "root_footer": (
        "Opcje komendy: hydrolog <grupa> <komenda> --help; "
        "lista komend: hydrolog commands list.",
        "Command options: hydrolog <group> <command> --help; "
        "list of commands: hydrolog commands list.",
    ),
    "group_title": ("komendy grupy {group}", "commands of group {group}"),
    "group_footer": (
        "Opcje komendy: hydrolog {group} <komenda> --help.",
        "Command options: hydrolog {group} <command> --help.",
    ),
    "mcp_description": (
        "Uruchamia serwer MCP (Model Context Protocol) na standardowym "
        "wejściu/wyjściu: każda komenda katalogu jest narzędziem. Wymaga dodatku "
        "hydrolog[mcp]. Na stdout idzie wyłącznie protokół.",
        "Starts the MCP (Model Context Protocol) server on standard input/output: "
        "every catalog command is a tool. Needs the hydrolog[mcp] extra. Only the "
        "protocol goes to stdout.",
    ),
    "mcp_lang": (
        "Język opisów narzędzi: pl lub en (domyślnie z HYDROLOG_LANG, "
        "w przeciwnym razie pl).",
        "Language of the tool descriptions: pl or en (default from HYDROLOG_LANG, "
        "otherwise pl).",
    ),
    "mcp_allow_dir": (
        "Katalog, w którym narzędzia mogą czytać i zapisywać pliki (opcję można "
        "powtarzać); bez niej komendy z opcjami typu path są odrzucane.",
        "Directory in which tools may read and write files (repeatable); without "
        "it commands with path options are refused.",
    ),
    # --- summary of a result -------------------------------------------------------
    "input": ("Wejście", "Input"),
    "result": ("Wynik", "Result"),
    "notices": ("Uwagi", "Notices"),
    "files": ("Pliki", "Files"),
    "none": ("brak", "n/a"),
    "yes": ("tak", "yes"),
    "no": ("nie", "no"),
    "more_items": (
        "… dalsze elementy: {count} (pełne dane: --json)",
        "… more items: {count} (full data: --json)",
    ),
    "level_warning": ("ostrzeżenie", "warning"),
    "level_info": ("informacja", "info"),
    # --- errors --------------------------------------------------------------------
    "error": ("Błąd", "Error"),
    "hint": ("Podpowiedź", "Hint"),
    "interrupted": ("Przerwano.", "Interrupted."),
}


def text(key: str, lang: Lang = DEFAULT_LANG, **values: object) -> str:
    """Return a UI text in ``lang``.

    Parameters
    ----------
    key : str
        Key of the text.
    lang : {"pl", "en"}, optional
        Language, Polish by default.
    **values : object
        Values for the ``{name}`` placeholders of the text.

    Returns
    -------
    str
        The text with its placeholders filled.

    Raises
    ------
    KeyError
        If ``key`` is unknown.
    """
    polish, english = _TEXTS[key]
    chosen = english if lang == "en" else polish
    return chosen.format(**values) if values else chosen


def env_lang(environ: Mapping[str, str] | None = None) -> Lang:
    """Return the language selected by ``HYDROLOG_LANG``.

    The variable is ambient configuration, so it is read leniently: case is ignored and
    a locale form such as ``pl_PL.UTF-8`` or ``en-US`` selects its language. Any other
    value is ignored and Polish is used.

    Parameters
    ----------
    environ : Mapping[str, str], optional
        Environment to read; defaults to ``os.environ``.

    Returns
    -------
    {"pl", "en"}
        The language.
    """
    source = os.environ if environ is None else environ
    value = source.get(LANG_ENV, "").strip().lower()
    language = re.split(r"[_.\-@]", value, maxsplit=1)[0]
    return "en" if language == "en" else DEFAULT_LANG
