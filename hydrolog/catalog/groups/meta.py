"""Group ``commands``: the catalog describing itself.

``commands list`` gives the names and summaries of all commands, ``commands schema``
the full option description (JSON Schema) of one command or of the whole catalog.
(``commands guide`` is declared by the agent-guide module.)
"""

from __future__ import annotations

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
)
