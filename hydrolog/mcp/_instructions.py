"""Instructions of the MCP server: short rules for the agent, built from the catalog.

The text is the ``instructions`` field of the server; clients load it at the start of
every session, so it stays short (:data:`MAX_CHARS`). Everything that depends on the
catalog -- the command groups, the names of the discovery tools, the file options and
the units in use -- is read from it, never typed here; only the rules are prose. The
tool descriptions do not repeat what is said here once (files, results, errors).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Final

from hydrolog.catalog import Command
from hydrolog.catalog.spec import Lang
from hydrolog.exceptions import NotFoundError

__all__ = ["MAX_CHARS", "build_instructions"]

MAX_CHARS: Final = 2000
"""Upper bound of the length of the instructions (tests keep the text below it)."""

_UNITS_SHOWN: Final = 6

_INTRO: Final[Mapping[Lang, str]] = {
    "pl": (
        "Hydrolog wykonuje obliczenia hydrologiczne lokalnie, bez sieci i bez "
        "pobierania danych. Każde narzędzie to jedna komenda katalogu (nazwa "
        "narzędzia = operation_id, np. {example}); grupy komend: {groups}. Zacznij "
        "od {list_tool} (spis komend); {schema_tool} opisuje opcje komend jako JSON "
        "Schema."
    ),
    "en": (
        "Hydrolog performs hydrological calculations locally, without network access "
        "and without downloading data. Each tool is one catalog command (tool name = "
        "operation_id, e.g. {example}); command groups: {groups}. Start with "
        "{list_tool} (list of commands); {schema_tool} describes the command options "
        "as JSON Schema."
    ),
}
_UNITS: Final[Mapping[Lang, str]] = {
    "pl": (
        "- Jednostki podaje opis każdej opcji (m.in. {units}); nie przeliczaj ich "
        "po cichu i nie zgaduj wartości, których użytkownik nie podał."
    ),
    "en": (
        "- Units are given in the description of each option (among them {units}); "
        "do not convert them silently and do not guess values the user did not give."
    ),
}
_FILES: Final[Mapping[Lang, str]] = {
    "pl": (
        "- Pliki: opcje typu path ({files}) działają tylko w katalogach dozwolonych "
        "serwera: {dirs}. Podawaj ścieżki bezwzględne. Długich serii nie wklejaj "
        "w argumenty: zapisz je do pliku CSV lub JSON i podaj plik."
    ),
    "en": (
        "- Files: path options ({files}) work only inside the directories allowed "
        "by the server: {dirs}. Give absolute paths. Do not paste long series into "
        "arguments: save them to a CSV or JSON file and give the file."
    ),
}
_NO_DIRS: Final[Mapping[Lang, str]] = {
    "pl": (
        "- Pliki: opcje typu path ({files}) są odrzucane (błąd forbidden), bo serwer "
        "działa bez katalogów dozwolonych (--allow-dir DIR); komendy bez plików "
        "działają normalnie."
    ),
    "en": (
        "- Files: path options ({files}) are refused (error forbidden) because the "
        "server runs without allowed directories (--allow-dir DIR); commands without "
        "files work normally."
    ),
}
_READ: Final[Mapping[Lang, str]] = {"pl": "odczyt", "en": "read"}
_WRITE: Final[Mapping[Lang, str]] = {"pl": "zapis", "en": "write"}
_RESULT: Final[Mapping[Lang, str]] = {
    "pl": (
        "- Wynik (structuredContent) to koperta hydrolog-result/1: result -- wartości, "
        "inputs -- opcje po normalizacji, files -- zapisane pliki z SHA-256, "
        "notices -- ostrzeżenia (przekaż je użytkownikowi)."
    ),
    "en": (
        "- A result (structuredContent) is the hydrolog-result/1 envelope: result -- "
        "the values, inputs -- the normalized options, files -- the written files with "
        "SHA-256, notices -- warnings (pass them on to the user)."
    ),
}
_ERRORS: Final[Mapping[Lang, str]] = {
    "pl": (
        "- Błąd (isError) to dokument hydrolog-error/1: code, message, hint, details "
        "(przy validation_error: option i reason). Popraw argumenty według hint "
        "i details i ponów wywołanie; błędu nie przedstawiaj jako wyniku."
    ),
    "en": (
        "- An error (isError) is the hydrolog-error/1 document: code, message, hint, "
        "details (for validation_error: option and reason). Fix the arguments "
        "according to hint and details and call again; never present an error as a "
        "result."
    ),
}
_RULES: Final[Mapping[Lang, str]] = {"pl": "Reguły:", "en": "Rules:"}


def _path_options(commands: Sequence[Command]) -> tuple[list[str], list[str]]:
    """Names of the path options that are read and of those that are written."""
    read: dict[str, None] = {}
    written: dict[str, None] = {}
    for command in commands:
        for option in command.options:
            if option.type == "path":
                (written if option.writes else read)[option.name] = None
    return sorted(read), sorted(written)


def _units(commands: Sequence[Command]) -> str:
    """The units most used by the options, as ``[km], [mm]``."""
    count = Counter(
        option.unit for command in commands for option in command.options if option.unit
    )
    ranked = sorted(count, key=lambda unit: (-count[unit], unit))
    return ", ".join(f"[{unit}]" for unit in ranked[:_UNITS_SHOWN])


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
        The catalog the server serves; it must hold the ``commands list`` and
        ``commands schema`` commands, which the text sends the agent to first.
    lang : {"pl", "en"}
        Language of the text.
    allowed_dirs : sequence of str
        Absolute directories the server allows for files; empty when it allows none.

    Returns
    -------
    str
        Introduction and rules: units, files (only when the catalog has path
        options), results and errors.

    Raises
    ------
    NotFoundError
        If the catalog lacks the ``commands list`` or ``commands schema`` command.
    """
    groups = ", ".join(dict.fromkeys(command.group for command in commands))
    intro = _INTRO[lang].format(
        example=commands[0].operation_id,
        groups=groups,
        list_tool=_operation_id(commands, "commands list"),
        schema_tool=_operation_id(commands, "commands schema"),
    )
    rules = []
    units = _units(commands)
    if units:
        rules.append(_UNITS[lang].format(units=units))
    read, written = _path_options(commands)
    if read or written:
        files = "; ".join(
            f"{label}: {', '.join(names)}"
            for label, names in ((_READ[lang], read), (_WRITE[lang], written))
            if names
        )
        if allowed_dirs:
            rules.append(_FILES[lang].format(files=files, dirs=", ".join(allowed_dirs)))
        else:
            rules.append(_NO_DIRS[lang].format(files=files))
    rules.extend((_RESULT[lang], _ERRORS[lang]))
    return "\n".join([intro, _RULES[lang], *rules])
