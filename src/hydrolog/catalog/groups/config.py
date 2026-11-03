"""Group ``config``: the settings of Hydrolog and where each one comes from.

``config show`` reports every setting with its value and source (DEV-18.6), the
credentials Hydrolog reads and its store root. Hydrolog reads no credentials and has
no store, so both are empty.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command

COMMANDS: tuple[Command, ...] = (
    Command(
        name="config show",
        operation_id="hydrolog_config_show",
        summary="Show the effective settings of Hydrolog and the source of each.",
        summary_pl="Pokaż obowiązujące ustawienia Hydrologa i źródło każdego.",
        description=(
            "Reports each setting (`lang`, `log_level`) with its value and source "
            "(command line, environment, nogat.toml or default), the settings file, "
            "the credentials read (none) and the store root (none: Hydrolog has no "
            "store). Use it to explain a language or log level; it changes nothing."
        ),
        description_pl=(
            "Podaje każde ustawienie (`lang`, `log_level`) z wartością i źródłem "
            "(linia poleceń, środowisko, nogat.toml albo domyślne), plik ustawień, "
            "odczytywane dane uwierzytelniające (brak) i katalog magazynu (brak: "
            "Hydrolog nie ma magazynu). Wyjaśnia język lub poziom logów; niczego nie "
            "zmienia."
        ),
        function="hydrolog.operations.config_show",
        options=(),
        examples=({},),
        result_schema="hydrolog-config/1",
        rules=(
            "Read `settings[].source` to see why a value applies.",
            "Hydrolog has no store and no credentials; `store` is null.",
        ),
        rules_pl=(
            "Z `settings[].source` odczytasz, skąd wynika wartość.",
            "Hydrolog nie ma magazynu ani danych uwierzytelniających; `store` to null.",
        ),
        errors=("validation_error",),
        example_results=({"credentials": [], "store": None},),
    ),
)
