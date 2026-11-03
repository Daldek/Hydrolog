"""Group ``gui``: the web GUI of Hydrolog (ADR-0014).

``gui serve`` starts the web server of :mod:`hydrolog.gui` (extra ``gui``) and serves
the page until it is stopped. A person starts it, so it is no tool of an agent
(``agent_tool=False``): no MCP tool and no line of the command index of the agent
guides, but it is in ``commands list`` and ``commands schema``, which the platform of
Nogat reads (HUB-2.9). ``check`` plans without serving, so its example runs in the
contract tests. The operation is in :mod:`hydrolog.operations.gui`.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

COMMANDS: tuple[Command, ...] = (
    Command(
        name="gui serve",
        operation_id="hydrolog_gui_serve",
        summary="Serve the web GUI of Hydrolog on this computer until it is stopped.",
        summary_pl="Uruchom przeglądarkowy interfejs Hydrologa na tym komputerze.",
        description=(
            "Starts the web server of the GUI (extra `gui`) on `host` and `port`, "
            "127.0.0.1:8070 by default, opens the page in a browser and serves until "
            "Ctrl+C or SIGTERM. For a person: an agent runs the commands themselves. "
            "There is no sign-in: on an address beyond this computer anyone who "
            "reaches it can use it."
        ),
        description_pl=(
            "Uruchamia serwer interfejsu (dodatek `gui`) pod adresem `host` i portem "
            "`port`, domyślnie 127.0.0.1:8070, otwiera stronę w przeglądarce i działa "
            "do Ctrl+C albo SIGTERM. Dla człowieka: agent wywołuje polecenia sam. Nie "
            "ma logowania: pod adresem dostępnym spoza tego komputera może z niego "
            "korzystać każdy, kto do niego dotrze."
        ),
        function="hydrolog.operations.gui_serve",
        options=(
            Option(
                name="host",
                type="string",
                description=(
                    "Address to listen on; by default 127.0.0.1, this computer only. "
                    "Another address (0.0.0.0, an address in a network) lets others "
                    "in without a sign-in: put the server behind an authenticating "
                    "proxy."
                ),
                description_pl=(
                    "Adres, na którym serwer nasłuchuje; domyślnie 127.0.0.1, tylko "
                    "ten komputer. Inny adres (0.0.0.0, adres w sieci) wpuszcza "
                    "innych bez logowania: postaw serwer za pośrednikiem z "
                    "uwierzytelnianiem."
                ),
                default="127.0.0.1",
            ),
            Option(
                name="port",
                type="integer",
                description="TCP port to listen on.",
                description_pl="Port TCP, na którym serwer nasłuchuje.",
                default=8070,
                minimum=1,
                maximum=65535,
            ),
            Option(
                name="no_browser",
                type="boolean",
                description=(
                    "Do not open the page in a web browser (a service, a remote "
                    "computer); the address is printed on stderr."
                ),
                description_pl=(
                    "Nie otwieraj strony w przeglądarce (usługa, zdalny komputer); "
                    "adres jest wypisywany na stderr."
                ),
                default=False,
            ),
            Option(
                name="check",
                type="boolean",
                description=(
                    "Plan without serving: return the address (`url`) and whether "
                    "the port is free (`port_free`)."
                ),
                description_pl=(
                    "Plan bez uruchamiania: zwróć adres (`url`) i to, czy port jest "
                    "wolny (`port_free`)."
                ),
                default=False,
            ),
        ),
        examples=({"check": True},),
        result_schema="hydrolog-gui-serve/1",
        rules=(
            "It blocks until stopped; `check` gives the address and `port_free`.",
            "Beyond 127.0.0.1 expose it only behind an authenticating proxy.",
        ),
        rules_pl=(
            "Działa do zatrzymania; `check` podaje adres i `port_free`.",
            "Poza 127.0.0.1 udostępniaj go tylko za pośrednikiem z uwierzytelnianiem.",
        ),
        errors=("validation_error", "conflict", "missing_dependency"),
        agent_tool=False,
        example_results=({"targets": [], "url": "http://127.0.0.1:8070/"},),
    ),
)
