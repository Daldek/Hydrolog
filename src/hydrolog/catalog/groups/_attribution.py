"""The option shared by the commands that compute with data of a provider (ADR-0028).

A command that takes a provider's data inline (the PMAXTP depth as ``total_mm``, a
station's values) cannot see where they came from: ``attribution`` gives it the lines
the providers' terms require (Nogat DEV-20), which its result and the files it writes
then carry (:mod:`hydrolog._attribution`). The lines of an input file are read without
it.

This module is not a command group: it is not listed in
:data:`hydrolog.catalog.groups.GROUP_MODULES`.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Option

ATTRIBUTION = Option(
    name="attribution",
    type="string_list",
    description=(
        "Attribution lines of the providers of the data in the other options (Nogat "
        "DEV-20), e.g. the `attribution` and `terms_notice` of the `precip pmaxtp` "
        "result whose depth is given, or of the hand-off a series came from; on the "
        "command line a JSON array. The result's `attribution` and `terms_notice` and "
        "the files the command writes carry them, with the lines the providers' terms "
        "add once data are processed. An input file's lines are read without it."
    ),
    description_pl=(
        "Wiersze przypisania dostawców danych podanych w innych opcjach (Nogat "
        "DEV-20), np. `attribution` i `terms_notice` wyniku `precip pmaxtp`, którego "
        "wysokość podajesz, albo przekazania, z którego pochodzi szereg; w wierszu "
        "poleceń tablica JSON. Przenoszą je pola `attribution` i `terms_notice` "
        "wyniku oraz pliki zapisane przez polecenie, z wierszami, które regulaminy "
        "dostawców dodają po przetworzeniu danych. Wiersze pliku wejściowego Hydrolog "
        "czyta sam."
    ),
)
