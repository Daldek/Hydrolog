"""User-interface texts of the command line (Polish and English).

Catalog texts (summaries, option descriptions) come from the catalog itself; this
module holds only the words the CLI adds around them: help headings, section titles of
the summary, labels of errors. Machine output is English (AGI-9.2), so error
*messages* and *hints* in the error document stay English; the readable explanation
before it follows ``--lang`` (registry title, the explanation of a conflict).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from hydrolog._settings import resolve_setting
from hydrolog.catalog.spec import Lang

__all__ = ["DEFAULT_LANG", "LANG_ENV", "env_lang", "text"]

DEFAULT_LANG: Final[Lang] = "pl"
"""Language used when neither ``--lang`` nor the settings select one."""
LANG_ENV: Final = "HYDROLOG_LANG"
"""Environment variable that selects the language of human-readable output."""

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
        "Wypisz kopertę wyniku (hydrolog-result/1) jako jedyny dokument JSON na "
        "stdout, zamiast podsumowania.",
        "Print the result envelope (hydrolog-result/1) as the only JSON document on "
        "stdout, instead of the summary.",
    ),
    "help_schema": (
        "Wypisz opis komendy (hydrolog-commands/1) zamiast ją uruchamiać.",
        "Print the description of the command (hydrolog-commands/1) instead of "
        "running it.",
    ),
    "help_lang": (
        "Język pomocy i podsumowań: pl lub en (domyślnie z HYDROLOG_LANG, NOGAT_LANG "
        "lub nogat.toml, w przeciwnym razie pl). Wyjście JSON jest zawsze po "
        "angielsku.",
        "Language of help and summaries: pl or en (default from HYDROLOG_LANG, "
        "NOGAT_LANG or nogat.toml, otherwise pl). JSON output is always English.",
    ),
    "help_verbose": (
        "Pokaż komunikaty diagnostyczne (poziom debug) na stderr.",
        "Show diagnostic messages (debug level) on stderr.",
    ),
    "help_quiet": (
        "Pokaż na stderr tylko błędy (poziom error).",
        "Show only errors on stderr (error level).",
    ),
    "default_note": ("domyślnie: {value}", "default: {value}"),
    "one_of_title": (
        "Wymagana dokładnie jedna z grup opcji:",
        "Exactly one of these option groups is required:",
    ),
    "values_title": ("Wartości opcji:", "Option values:"),
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
    "group_description": (
        "Komendy grupy {group} katalogu Hydrologa.",
        "Commands of the group {group} of the Hydrolog catalog.",
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
    "mcp_allow_dir": (
        "Katalog, z którego narzędzia mogą czytać pliki, a z --allow-writes także "
        "zapisywać (opcję można powtarzać); bez niej komendy z opcjami typu path "
        "są odrzucane.",
        "Directory from which tools may read files and, with --allow-writes, write "
        "them (repeatable); without it commands with path options are refused.",
    ),
    "mcp_allow_writes": (
        "Pozwól narzędziom zapisywać pliki w katalogach z --allow-dir; bez tej "
        "opcji serwer tylko czyta.",
        "Let tools write files in the directories of --allow-dir; without it the "
        "server only reads.",
    ),
    "mcp_tools": (
        "Rodziny narzędzi do udostępnienia, rozdzielone przecinkami: grupy komend "
        "i core.",
        "Tool families to expose, comma-separated: command groups and core.",
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
    "file_written": ("zapisano", "written"),
    "file_replaced": ("zastąpiono", "replaced"),
    "file_bytes": ("{size} B", "{size} B"),
    # --- plan (--check) ------------------------------------------------------------
    "plan_title": (
        "Plan (--check): nic nie zostało zapisane.",
        "Plan (--check): nothing was written.",
    ),
    "plan_option": ("opcja", "option"),
    "plan_action": ("działanie", "action"),
    "plan_path": ("plik", "file"),
    "plan_note": ("uwaga", "note"),
    "plan_write": ("zapis", "write"),
    "plan_replace": ("zastąpienie", "replace"),
    "plan_conflict": ("konflikt", "conflict"),
    "plan_output_exists": (
        "plik istnieje; dodaj --force, aby go zastąpić",
        "the file exists; add --force to replace it",
    ),
    "plan_duplicate_output_name": (
        "ta sama nazwa pliku w kilku wyjściach",
        "the same file name in several outputs",
    ),
    "plan_blocked": (
        "Uruchomienie bez --check zakończyłoby się błędem conflict (kod wyjścia 4).",
        "Running without --check would fail with the error conflict (exit code 4).",
    ),
    "plan_empty": ("Brak plików do zapisu.", "No files would be written."),
    # --- commands list and schema ---------------------------------------------------
    "command": ("komenda", "command"),
    "summary": ("opis", "summary"),
    "page_total": ("Razem komend: {total}.", "Commands in total: {total}."),
    "page_shown": (
        "Pokazano {shown} z {total}.",
        "Showing {shown} of {total}.",
    ),
    "page_next": (
        "Następna strona: --cursor {cursor}",
        "Next page: --cursor {cursor}",
    ),
    "schema_options": ("Opcje", "Options"),
    "schema_name": ("opcja", "option"),
    "schema_type": ("typ", "type"),
    "schema_required": ("wymagana", "required"),
    "schema_default": ("domyślnie", "default"),
    "schema_description": ("opis", "description"),
    "schema_one_of": (
        "Dokładnie jedna z grup opcji: {groups}",
        "Exactly one of these option groups: {groups}",
    ),
    "schema_rules": ("Zasady", "Rules"),
    "schema_examples": ("Przykłady", "Examples"),
    "schema_effects_read_only": ("Tylko odczyt.", "Read-only."),
    "schema_effects_writes": (
        "Zapisuje pliki (--check pokazuje plan, --force zastępuje istniejące).",
        "Writes files (--check shows the plan, --force replaces existing files).",
    ),
    "schema_errors": ("Możliwe błędy", "Possible errors"),
    # --- config show ---------------------------------------------------------------
    "config_setting": ("ustawienie", "setting"),
    "config_value": ("wartość", "value"),
    "config_source": ("źródło", "source"),
    "config_file": (
        "Plik ustawień: {path} ({state})",
        "Settings file: {path} ({state})",
    ),
    "config_file_exists": ("istnieje", "exists"),
    "config_file_absent": ("brak pliku", "no such file"),
    "config_credentials": ("Dane uwierzytelniające", "Credentials"),
    "config_store": ("Magazyn danych", "Data store"),
    "config_present": ("ustawione", "set"),
    "config_missing": ("brak", "missing"),
    "source_option": ("opcja", "option"),
    "source_environment": ("zmienna środowiskowa", "environment variable"),
    "source_file": ("plik ustawień", "settings file"),
    "source_default": ("wartość domyślna", "default"),
    # --- errors --------------------------------------------------------------------
    "error": ("Błąd", "Error"),
    "hint": ("Podpowiedź", "Hint"),
    "interrupted": ("Przerwano.", "Interrupted."),
    "conflict_output_exists": (
        "Plik wyjściowy już istnieje, nic nie zapisano:",
        "The output file already exists; nothing was written:",
    ),
    "conflict_output_exists_hint": (
        "Podaj inną ścieżkę albo dodaj --force, aby zastąpić plik.",
        "Give another path or add --force to replace the file.",
    ),
    "conflict_duplicate_output_name": (
        "Kilka wyjść wskazuje ten sam plik, nic nie zapisano:",
        "Several outputs name the same file; nothing was written:",
    ),
    "conflict_duplicate_output_name_hint": (
        "Podaj osobną ścieżkę dla każdego wyjścia.",
        "Give a different path for each output.",
    ),
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
    """Return the language of human-readable output from the shared settings.

    The order is ``HYDROLOG_LANG``, ``NOGAT_LANG``, ``nogat.toml`` (``[hydrolog]``
    before ``[nogat]``) and Polish (DEV-18.1). The settings are ambient configuration,
    so they are read leniently: case is ignored, a locale form such as ``pl_PL.UTF-8``
    or ``en-US`` selects its language and an invalid value is ignored.

    Parameters
    ----------
    environ : Mapping[str, str], optional
        Environment to read; defaults to ``os.environ``.

    Returns
    -------
    {"pl", "en"}
        The language.
    """
    value = resolve_setting("lang", environ=environ).value
    return "en" if value == "en" else DEFAULT_LANG
