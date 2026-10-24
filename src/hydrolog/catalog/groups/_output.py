"""Options shared by the commands that write a file (AGI-1.3, DEV-19.9, DEV-19.10)."""

from __future__ import annotations

from hydrolog.catalog.spec import Option

FORCE = Option(
    name="force",
    type="boolean",
    description=(
        "Replace the `output` file if it exists; without it nothing is overwritten."
    ),
    description_pl=(
        "Zastąp plik `output`, jeśli istnieje; bez tej opcji nic nie jest nadpisywane."
    ),
    default=False,
)
CHECK = Option(
    name="check",
    type="boolean",
    description=(
        "Plan without effects: return the target file and its action (`write`, "
        "`replace` or `conflict`) and write nothing."
    ),
    description_pl=(
        "Plan bez skutków: zwróć plik docelowy i jego akcję (`write`, `replace` lub "
        "`conflict`), niczego nie zapisując."
    ),
    default=False,
)
