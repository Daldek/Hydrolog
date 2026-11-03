"""Group ``commands``: the catalog describing itself.

``commands list`` gives the names and summaries of all commands, ``commands schema``
the ``hydrolog-commands/1`` description of one command or a page of the whole
catalog, and ``commands guide`` the guide for AI agents generated from the catalog
(:mod:`hydrolog.agent_guide`; with ``output`` it also writes the file, which is how
the repository ``AGENTS.md`` and ``llms.txt`` are made).
"""

from __future__ import annotations

from hydrolog.catalog.groups._output import CHECK, FORCE
from hydrolog.catalog.spec import Command, Option

_LIMIT = "Number of commands on one page."
_CURSOR = (
    "The `page.next_cursor` of the previous page, unchanged; omitted for the first "
    "page."
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="commands list",
        operation_id="hydrolog_commands_list",
        summary="List the catalog commands: name, operation id and summary.",
        summary_pl="Wylistuj komendy katalogu: nazwa, operation_id i opis.",
        description=(
            "Lists every Hydrolog command with name, `operation_id`, summary, MCP "
            "families and whether it is read-only. Use it first to find a command; "
            "use `commands schema` for the options of one command and "
            "`commands guide` for the whole guide."
        ),
        description_pl=(
            "Wylicza komendy Hydrologa: nazwę, `operation_id`, opis, rodziny narzędzi "
            "MCP i informację, czy komenda tylko czyta. Użyj jej najpierw, by znaleźć "
            "komendę; opcje jednej komendy daje `commands schema`, cały przewodnik "
            "`commands guide`."
        ),
        function="hydrolog.operations.commands_list",
        options=(
            Option(
                name="limit",
                type="integer",
                description=_LIMIT,
                description_pl="Liczba komend na jednej stronie.",
                default=100,
                minimum=1,
                maximum=500,
            ),
            Option(
                name="cursor",
                type="string",
                description=_CURSOR,
                description_pl=(
                    "`page.next_cursor` poprzedniej strony, bez zmian; pominięty dla "
                    "pierwszej strony."
                ),
            ),
        ),
        examples=({}, {"limit": 5}),
        result_schema="hydrolog-command-list/1",
        cardinality="bounded",
        rules=(
            "Call it first to pick a command.",
            "Then call `commands schema` with `command` for its options.",
            "Follow `page.next_cursor` while `page.truncated` is true.",
        ),
        rules_pl=(
            "Wywołaj ją najpierw, by wybrać komendę.",
            "Potem wywołaj `commands schema` z `command`, by poznać opcje.",
            "Idź za `page.next_cursor`, dopóki `page.truncated` jest prawdą.",
        ),
        errors=("validation_error",),
        core=True,
        example_results=({"tool": "hydrolog"}, {"tool": "hydrolog"}),
    ),
    Command(
        name="commands schema",
        operation_id="hydrolog_commands_schema",
        summary="Return options, result and rules of one command or a catalog page.",
        summary_pl="Zwróć opcje, wynik i zasady jednej komendy albo strony katalogu.",
        description=(
            "Returns the `hydrolog-commands/1` document: options with types, units, "
            "bounds and enum meanings, result schema, effects, rules, examples and "
            "errors. Give `command` for one command; without it the catalog is paged "
            "(`limit`, `cursor`). Not for choosing a command: use `commands list`."
        ),
        description_pl=(
            "Zwraca dokument `hydrolog-commands/1`: opcje z typami, jednostkami, "
            "zakresami i znaczeniami wartości, schemat wyniku, skutki, zasady, "
            "przykłady i błędy. Z `command` dotyczy jednej komendy; bez niego katalog "
            "jest podzielony na strony (`limit`, `cursor`). Do wyboru komendy służy "
            "`commands list`."
        ),
        function="hydrolog.operations.commands_schema",
        options=(
            Option(
                name="command",
                type="string",
                description=(
                    "Command name (`tc kirpich`) or its operation_id "
                    "(`hydrolog_tc_kirpich`); omitted: a page of the whole catalog."
                ),
                description_pl=(
                    "Nazwa komendy (`tc kirpich`) albo jej operation_id "
                    "(`hydrolog_tc_kirpich`); pominięta: strona całego katalogu."
                ),
            ),
            Option(
                name="limit",
                type="integer",
                description=_LIMIT,
                description_pl="Liczba komend na jednej stronie.",
                default=5,
                minimum=1,
                maximum=50,
            ),
            Option(
                name="cursor",
                type="string",
                description=_CURSOR,
                description_pl=(
                    "`page.next_cursor` poprzedniej strony, bez zmian; pominięty dla "
                    "pierwszej strony."
                ),
            ),
        ),
        examples=({"command": "commands list"}, {"command": "tc kirpich"}),
        result_schema="hydrolog-commands/1",
        cardinality="bounded",
        rules=(
            "Give `command` to get one command instead of a page of the catalog.",
            "Take option names, units, bounds and enum meanings from `options`.",
        ),
        rules_pl=(
            "Podaj `command`, by dostać jedną komendę zamiast strony katalogu.",
            "Nazwy opcji, jednostki, zakresy i znaczenia wartości czytaj z `options`.",
        ),
        errors=("validation_error", "not_found"),
        core=True,
        example_results=({"tool": "hydrolog"}, {"tool": "hydrolog"}),
    ),
    Command(
        name="commands guide",
        operation_id="hydrolog_commands_guide",
        summary="Render the agent guide (AGENTS.md, llms.txt, block) from the catalog.",
        summary_pl=(
            "Wygeneruj z katalogu przewodnik (AGENTS.md, llms.txt, blok) dla agentów."
        ),
        description=(
            "Renders the English agent guide from the catalog: `agents` is AGENTS.md, "
            "`llms` llms.txt, `agents-md-block` the compact block that `inject` puts "
            "into a consumer's AGENTS.md. `output` or `inject` write a file; not for "
            "the options of one command: use `commands schema`."
        ),
        description_pl=(
            "Generuje z katalogu angielski przewodnik dla agentów: `agents` to "
            "AGENTS.md, `llms` to llms.txt, `agents-md-block` to zwarty blok, który "
            "`inject` wstawia do AGENTS.md projektu korzystającego. `output` lub "
            "`inject` zapisują plik; opcje jednej komendy daje `commands schema`."
        ),
        function="hydrolog.operations.commands_guide",
        options=(
            Option(
                name="format",
                type="choice",
                description="Kind of guide.",
                description_pl="Rodzaj przewodnika.",
                choices=("agents", "llms", "agents-md-block"),
                meanings={
                    "agents": "Full AGENTS.md: rules, interfaces, index, flows.",
                    "llms": "Concise llms.txt: a link list in the llms.txt format.",
                    "agents-md-block": (
                        "Compact block between BEGIN/END markers for a consumer's "
                        "AGENTS.md."
                    ),
                },
                meanings_pl={
                    "agents": "Pełny AGENTS.md: zasady, interfejsy, indeks, przepływy.",
                    "llms": "Zwięzły llms.txt: lista odnośników w formacie llms.txt.",
                    "agents-md-block": (
                        "Zwarty blok między znacznikami BEGIN/END do AGENTS.md "
                        "projektu korzystającego."
                    ),
                },
                default="agents",
            ),
            Option(
                name="output",
                type="path",
                description=(
                    "File to write the guide to; missing directories are created. An "
                    "existing file is replaced only with `force`."
                ),
                description_pl=(
                    "Plik, do którego zapisać przewodnik; brakujące katalogi są "
                    "tworzone. Istniejący plik jest zastępowany tylko z `force`."
                ),
                path_role="output",
            ),
            Option(
                name="inject",
                type="path",
                description=(
                    "AGENTS.md of a consumer repository: its block between "
                    "`<!-- BEGIN hydrolog -->` and `<!-- END hydrolog -->` is "
                    "replaced, or appended when missing. Only with "
                    "`format=agents-md-block`; repeating the call changes nothing."
                ),
                description_pl=(
                    "AGENTS.md projektu korzystającego: jego blok między "
                    "`<!-- BEGIN hydrolog -->` a `<!-- END hydrolog -->` jest "
                    "zastępowany albo dopisywany. Tylko z `format=agents-md-block`; "
                    "powtórzenie wywołania niczego nie zmienia."
                ),
                path_role="output",
            ),
            FORCE,
            CHECK,
        ),
        examples=({"format": "llms"}, {"format": "agents-md-block"}),
        result_schema="hydrolog-guide/1",
        cardinality="bounded",
        rules=(
            "Fetch the guide once per session; `agents` is large.",
            "Use `format=llms` for a short overview.",
            "Run with `check` before writing a file.",
        ),
        rules_pl=(
            "Pobierz przewodnik raz na sesję; `agents` jest duży.",
            "Dla krótkiego przeglądu użyj `format=llms`.",
            "Przed zapisem pliku uruchom z `check`.",
        ),
        errors=(
            "validation_error",
            "forbidden",
            "io_error",
            "conflict",
        ),
        example_results=({"format": "llms"}, {"format": "agents-md-block"}),
    ),
)
