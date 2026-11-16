"""Group ``config``: the settings of Hydrolog and where each one comes from.

``config show`` reports every setting with its value and source (DEV-18.6), the
credentials Hydrolog reads (whether each variable is set, never its value) and its
store root. Hydrolog has no store, so the root is null.
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
            "Reports each setting (`lang`, `log_level`, `data_dir`, `state_dir`, "
            "`request_limit`, `request_window`) with its value and "
            "source (command line, environment, nogat.toml or default), the settings "
            "file, whether each credential variable is set (the key of the web GUI's "
            "admin page; never its value) and the store root (none: Hydrolog has no "
            "store). Use it to explain a setting; it changes nothing."
        ),
        description_pl=(
            "Podaje każde ustawienie (`lang`, `log_level`, `data_dir`, `state_dir` "
            "oraz `request_limit` i `request_window` GUI) z wartością i "
            "źródłem (linia poleceń, środowisko, nogat.toml albo domyślne), plik "
            "ustawień, czy ustawiono każdą zmienną danych uwierzytelniających (klucz "
            "strony administracyjnej GUI; nigdy jego wartość) i katalog magazynu "
            "(brak: Hydrolog nie ma magazynu). Wyjaśnia ustawienie; niczego nie "
            "zmienia."
        ),
        function="hydrolog.operations.config_show",
        options=(),
        examples=({},),
        result_schema="hydrolog-config/1",
        rules=(
            "Read `settings[].source` to see why a value applies.",
            "Hydrolog has no store: `store` is null. A credential shows `present`, "
            "never its value.",
        ),
        rules_pl=(
            "Z `settings[].source` odczytasz, skąd wynika wartość.",
            "Hydrolog nie ma magazynu: `store` to null. Dane uwierzytelniające mają "
            "tylko `present`, nigdy wartości.",
        ),
        errors=("validation_error",),
        example_results=(
            {
                "credentials": [
                    {"name": "HYDROLOG_ADMIN_API_KEY", "present": False},
                    {"name": "HYDROLOG_ADMIN_API_KEY_FILE", "present": False},
                ],
                "store": None,
            },
        ),
    ),
)
