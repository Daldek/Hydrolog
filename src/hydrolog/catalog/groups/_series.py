"""Option declarations shared by the groups that read series.

A series reaches a command either inline (``values``, with ``dates`` when the series is
dated) or from a file (``input_file`` with ``value_column`` and ``date_column``); see
:mod:`hydrolog.catalog.inputs`. The commands that need dated series use
:data:`DATED_OPTIONS` and :data:`DATED_ONE_OF`; commands with other wording derive their
options with :func:`dataclasses.replace`.

This module is not a command group: it is not listed in
:data:`hydrolog.catalog.groups.GROUP_MODULES`.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Option

VALUES = Option(
    name="values",
    type="number_list",
    description_pl=(
        "Wartości szeregu w kolejności czasowej (np. przepływy dobowe Q [m³/s] albo "
        "stany H [cm]). Długie szeregi podawaj w pliku (`input_file`), nie wklejaj ich "
        "tutaj."
    ),
    description=(
        "Series values in time order (e.g. daily discharge Q [m³/s] or stage H [cm]). "
        "Give long series in a file (`input_file`) instead of pasting them here."
    ),
)

DATES = Option(
    name="dates",
    type="string_list",
    description_pl=(
        "Daty kolejnych wartości w formacie ISO `RRRR-MM-DD`, ściśle rosnące; tyle "
        "samo co `values`."
    ),
    description=(
        "Dates of the values in ISO format `YYYY-MM-DD`, strictly increasing; as many "
        "as `values`."
    ),
)

INPUT_FILE = Option(
    name="input_file",
    type="path",
    path_role="input",
    description_pl=(
        "Plik CSV (przecinek lub średnik, wiersz nagłówka) albo JSON z szeregiem, np. "
        "eksport szeregu z IMGWTools. Kolumny wskazują `value_column` i `date_column`."
    ),
    description=(
        "CSV file (comma or semicolon, header row) or JSON file with the series, e.g. "
        "an IMGWTools series export. The columns are named by `value_column` and "
        "`date_column`."
    ),
)

VALUE_COLUMN = Option(
    name="value_column",
    type="string",
    description_pl=(
        "Nazwa kolumny z wartościami w `input_file`; wystarczy nazwa bez jednostki w "
        "nawiasie kwadratowym (`Q` wskazuje kolumnę `Q [m3/s]`)."
    ),
    description=(
        "Name of the value column in `input_file`; the name without the unit in "
        "square brackets is enough (`Q` finds `Q [m3/s]`)."
    ),
)

DATE_COLUMN = Option(
    name="date_column",
    type="string",
    description_pl=(
        "Nazwa kolumny z datami ISO `RRRR-MM-DD` w `input_file` (np. `date`)."
    ),
    description=(
        "Name of the column with ISO dates `YYYY-MM-DD` in `input_file` (e.g. `date`)."
    ),
)

DATED_OPTIONS: tuple[Option, ...] = (
    VALUES,
    DATES,
    INPUT_FILE,
    VALUE_COLUMN,
    DATE_COLUMN,
)
"""Series options of a command that needs dates (inline pair or file triple)."""

DATED_ONE_OF: tuple[tuple[str, ...], ...] = (
    ("values", "dates"),
    ("input_file", "value_column", "date_column"),
)
"""Exactly one of: inline values with dates, or a file with its two columns."""
