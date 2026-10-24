"""Group ``commands``: the catalog describing itself.

``commands list`` gives the names and summaries of all commands, ``commands schema``
the full option description (JSON Schema) of one command or of the whole catalog, and
``commands guide`` the guide for AI agents generated from the catalog
(:mod:`hydrolog.agent_guide`; with ``path`` it also writes the file, which is how the
repository ``AGENTS.md`` and ``llms.txt`` are made).
"""

from __future__ import annotations

from dataclasses import replace

from hydrolog.catalog.spec import Command, Option

_LANG = Option(
    name="lang",
    type="choice",
    description="Język opisów w wyniku: pl lub en.",
    description_en="Language of the texts in the result: pl or en.",
    choices=("pl", "en"),
    default="pl",
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="commands list",
        operation_id="commands_list",
        summary="Lista komend katalogu: nazwa, operation_id i krótki opis.",
        summary_en="List the catalog commands: name, operation id and short summary.",
        description=(
            "Zwraca wszystkie komendy katalogu Hydrologa w kolejności grup: nazwę "
            "(`grupa komenda`), `operation_id` (nazwa narzędzia MCP) i jednozdaniowy "
            "opis. To punkt startowy dla agenta; pełny opis opcji wybranej komendy "
            "daje `commands schema`."
        ),
        description_en=(
            "Returns every Hydrolog catalog command in group order: the name "
            "(`group command`), the `operation_id` (MCP tool name) and a one-line "
            "summary. This is the starting point for an agent; `commands schema` "
            "gives the full option description of a chosen command."
        ),
        function="hydrolog.operations:list_commands",
        options=(_LANG,),
        examples=({}, {"lang": "en"}),
    ),
    Command(
        name="commands schema",
        operation_id="commands_schema",
        summary="Opis opcji komend jako JSON Schema (cały katalog albo jedna komenda).",
        summary_en="Command options as JSON Schema (whole catalog or one command).",
        description=(
            "Zwraca dokument `hydrolog-commands/1`: dla każdej komendy nazwę, "
            "`operation_id`, opis oraz `input_schema` -- JSON Schema (2020-12) opcji z "
            "jednostkami, zakresami, wartościami domyślnymi i przykładami. Bez opcji "
            "`command` opisuje cały katalog; z opcją -- jedną komendę (po nazwie albo "
            "po `operation_id`)."
        ),
        description_en=(
            "Returns the `hydrolog-commands/1` document: for each command the name, "
            "`operation_id`, description and `input_schema` -- the JSON Schema "
            "(2020-12) of its options with units, bounds, defaults and examples. "
            "Without `command` it describes the whole catalog; with it, one command "
            "(by name or by `operation_id`)."
        ),
        function="hydrolog.operations:commands_schema",
        options=(
            Option(
                name="command",
                type="string",
                description=(
                    "Nazwa komendy (`tc kirpich`) albo jej operation_id "
                    "(`tc_kirpich`); pominięta -- cały katalog."
                ),
                description_en=(
                    "Command name (`tc kirpich`) or its operation_id (`tc_kirpich`); "
                    "omitted -- the whole catalog."
                ),
            ),
            _LANG,
        ),
        examples=(
            {"command": "commands list"},
            {"command": "commands_schema", "lang": "en"},
        ),
    ),
    Command(
        name="commands guide",
        operation_id="commands_guide",
        summary=(
            "Przewodnik dla agentów (AGENTS.md albo llms.txt) z katalogu komend; "
            "opcjonalnie zapisuje plik."
        ),
        summary_en=(
            "Agent guide (AGENTS.md or llms.txt) from the command catalog; optionally "
            "writes a file."
        ),
        description=(
            "Zwraca przewodnik dla agentów AI wygenerowany z katalogu komend. "
            "`format=agents` daje pełny AGENTS.md: zasady pracy, interfejsy (Python, "
            "CLI, MCP), kopertę wyniku `hydrolog-result/1` i błędy `hydrolog-error/1` "
            "z rejestrem kodów, formaty plików wejściowych, tabele wszystkich komend "
            "z opcjami i skutkami, typowe przepływy jako wywołania CLI i MCP, czego "
            "nie robić oraz pracę nad kodem; `format=llms` daje zwięzły llms.txt (do "
            "150 linii: zasady, grupy komend, przepływy, odnośniki do dokumentacji). "
            "Język przewodnika wybiera `lang`. Wynik (`result`) to tekst Markdown "
            "(UTF-8, końce linii `\\n`); pełny AGENTS.md ma kilkadziesiąt kB, więc "
            "pobierz go raz na sesję. Z opcją `path` ten sam tekst jest dodatkowo "
            "zapisywany do pliku (brakujące katalogi są tworzone, istniejący plik "
            "jest zastępowany), a `files` podaje jego SHA-256 -- tak powstają "
            "`AGENTS.md` i `llms.txt` w korzeniu repozytorium. Treść zależy tylko od "
            "zainstalowanej wersji pakietu (bez dat i lokalnych ścieżek)."
        ),
        description_en=(
            "Returns the guide for AI agents generated from the command catalog. "
            "`format=agents` gives the full AGENTS.md: the rules, the interfaces "
            "(Python, CLI, MCP), the `hydrolog-result/1` envelope and the "
            "`hydrolog-error/1` errors with the code registry, the formats of the "
            "input files, a table of every command with its options and effect, "
            "typical flows as CLI and MCP calls, what not to do and how to work on "
            "the code; `format=llms` gives the concise llms.txt (at most 150 lines: "
            "the rules, the command groups, the flows, links to the documentation). "
            "`lang` selects the language of the guide. The result (`result`) is "
            "Markdown text (UTF-8, `\\n` line ends); the full AGENTS.md is several "
            "dozen kB, so fetch it once per session. With `path` the same text is "
            "also written to a file (missing directories are created, an existing "
            "file is replaced) and `files` gives its SHA-256 -- this is how the "
            "`AGENTS.md` and `llms.txt` in the repository root are made. The text "
            "depends only on the installed version of the package (no dates, no "
            "local paths)."
        ),
        function="hydrolog.operations:commands_guide",
        options=(
            Option(
                name="format",
                type="choice",
                description=(
                    "Rodzaj przewodnika: `agents` (pełny AGENTS.md) albo `llms` "
                    "(zwięzły llms.txt)."
                ),
                description_en=(
                    "Kind of guide: `agents` (the full AGENTS.md) or `llms` (the "
                    "concise llms.txt)."
                ),
                choices=("agents", "llms"),
                default="agents",
            ),
            replace(
                _LANG,
                description="Język przewodnika: pl lub en.",
                description_en="Language of the guide: pl or en.",
            ),
            Option(
                name="path",
                type="path",
                description=(
                    "Plik, do którego zapisać tekst przewodnika; brakujące katalogi "
                    "są tworzone, istniejący plik jest zastępowany. Bez tej opcji "
                    "nic nie jest zapisywane (tekst jest tylko w wyniku)."
                ),
                description_en=(
                    "File to write the guide text to; missing directories are "
                    "created, an existing file is replaced. Without it nothing is "
                    "written (the text is only in the result)."
                ),
                writes=True,
            ),
        ),
        writes=True,
        examples=({"format": "agents"}, {"format": "llms", "lang": "en"}),
    ),
)
