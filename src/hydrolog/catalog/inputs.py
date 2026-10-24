"""Inputs from files or inline JSON: series, hydrographs, watersheds, stations.

Long data must not be pasted by agents, so every operation that takes a series, a set
of stations or a watershed accepts either inline values or a file. This module turns
both into the objects the library works with:

* :func:`load_series` -- ``values``/``dates`` inline *or* ``input_file`` +
  ``value_column`` (+ ``date_column``) -> :class:`Series` (NumPy arrays; dates as
  ``datetime64[D]``);
* :func:`load_watershed` -- an inline ``watershed`` object *or* a ``watershed_file``
  (``WatershedParameters`` JSON) -> :class:`~hydrolog.morphometry.WatershedParameters`;
* :func:`load_stations` -- inline records *or* a ``stations_file`` (columns ``name``,
  ``x``, ``y``, ``precipitation_mm``, optional ``elevation_m``) -> list of
  :class:`~hydrolog.precipitation.Station`;
* :func:`load_hydrograph` -- inline ``times_min`` + ``discharge_m3s`` *or* an
  ``input_file`` with a ``time_column`` and a ``value_column`` (defaults ``time_min``
  and ``discharge_m3s``) -> :class:`~hydrolog.routing.Hydrograph`, the regular-step
  table that the ``route`` commands take;
* :func:`read_table` / :func:`load_records` -- the generic file reader behind them,
  for operations that need other columns (rating curve pairs, network segments...).

Files
-----
CSV (comma or semicolon, detected from the header; UTF-8 with or without BOM; a header
row; quoted fields; CRLF or LF; rows without any content are skipped) and JSON. The CSV
written by IMGWTools ``export_series``
(``date,year,Q [m3/s],Q_flag,...,attribution_source,attribution_processed``) loads
without preprocessing. JSON may be a list of records, an object of equal-length
columns, or a plain list of numbers (one column called ``values``); a missing JSON
value is ``null`` (``NaN`` is not JSON and is rejected).

Numbers are read from ``12.5`` or ``12,5`` (decimal comma); an empty cell, ``NaN``,
``NA``, ``N/A``, ``null`` and ``none`` are missing values (``NaN``). A column name is
matched exactly or, when unique, by its name without the ``[unit]`` suffix (``Q``
finds ``Q [m3/s]``). Dates are ISO ``YYYY-MM-DD`` (a midnight time part is ignored)
and must be strictly increasing in a series.

Errors
------
A missing file is :class:`~hydrolog.exceptions.NotFoundError`; an unreadable or
malformed file (encoding, syntax, missing column, bad number or date) is
:class:`~hydrolog.exceptions.InputDataError` with ``details`` ``path`` and ``reason``
(and ``column``, ``row`` -- the 1-based data row -- ``value``, ``available`` where they
apply). A wrong combination of inline arguments is
:class:`~hydrolog.exceptions.InvalidParameterError` with ``details.option``.
"""

from __future__ import annotations

import csv
import datetime as dt
import functools
import io
import json
import math
import numbers
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import MISSING, dataclass, fields
from pathlib import Path
from typing import Any, NoReturn, get_args, get_type_hints

import numpy as np
from numpy.typing import ArrayLike, NDArray

from hydrolog.exceptions import InputDataError, InvalidParameterError, NotFoundError
from hydrolog.morphometry.watershed_params import WatershedParameters
from hydrolog.precipitation.interpolation import Station
from hydrolog.routing.hydrograph import Hydrograph, check_table

__all__ = [
    "DISCHARGE_COLUMN",
    "TIME_COLUMN",
    "Series",
    "Table",
    "load_hydrograph",
    "load_records",
    "load_series",
    "load_stations",
    "load_watershed",
    "read_table",
]

_NUMBER = re.compile(r"[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?")
_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:[T ]00:00(?::00(?:\.0+)?)?)?")
_UNIT_SUFFIX = re.compile(r"\s*\[[^\]]*\]\s*$")
_MISSING_TOKENS = frozenset({"", "nan", "na", "n/a", "null", "none"})
_MAX_LISTED = 20
_SHOWN_CHARS = 60


@dataclass(frozen=True)
class _Source:
    """Where a value came from; decides the error class of a failure.

    A file gives :class:`InputDataError` (``details.path``); an inline option gives
    :class:`InvalidParameterError` (``details.option``).
    """

    path: Path | None = None
    option: str | None = None

    def fail(
        self, message: str, *, reason: str, hint: str | None = None, **details: object
    ) -> NoReturn:
        if self.path is not None:
            raise InputDataError(
                f"{self.path}: {message}",
                details={"path": str(self.path), "reason": reason, **details},
                hint=hint,
            )
        raise InvalidParameterError(
            f"Option {self.option!r}: {message}",
            details={"option": self.option, "reason": reason, **details},
            hint=hint,
        )


def _shown(value: object) -> str:
    text = str(value)
    return text if len(text) <= _SHOWN_CHARS else text[: _SHOWN_CHARS - 1] + "…"


def _listed(names: Sequence[str]) -> str:
    shown = ", ".join(names[:_MAX_LISTED])
    return shown + (", ..." if len(names) > _MAX_LISTED else "")


# --- reading files --------------------------------------------------------------------


def _file_path(path: str | os.PathLike[str], option: str | None = None) -> Path:
    text = os.fspath(path)
    if not text.strip():
        raise InvalidParameterError(
            "The input file path must not be empty",
            details={"option": option or "input_file", "reason": "empty"},
        )
    return Path(text).expanduser()


def _read_text(path: Path) -> str:
    """Text of a file; UTF-8, a leading BOM is dropped."""
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            return stream.read()
    except FileNotFoundError as exc:
        raise NotFoundError(
            f"Input file not found: {path}",
            details={"path": str(path)},
            hint="Check the path; a relative path is resolved against the working "
            "directory.",
        ) from exc
    except (IsADirectoryError, NotADirectoryError) as exc:
        raise InputDataError(
            f"{path} is not a file",
            details={"path": str(path), "reason": "not_a_file"},
        ) from exc
    except UnicodeDecodeError as exc:
        raise InputDataError(
            f"{path}: not valid UTF-8 text (byte {exc.start})",
            details={"path": str(path), "reason": "encoding", "position": exc.start},
            hint="Save the file as UTF-8 (with or without BOM).",
        ) from exc
    except OSError as exc:
        raise InputDataError(
            f"{path} cannot be read: {exc.strerror or exc}",
            details={"path": str(path), "reason": "unreadable"},
        ) from exc


def _reject_constant(name: str) -> NoReturn:
    raise ValueError(f"{name} is not valid JSON; use null for a missing value")


def _parse_json(path: Path, text: str) -> Any:
    try:
        return json.loads(text, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise InputDataError(
            f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            details={
                "path": str(path),
                "reason": "invalid_json",
                "line": exc.lineno,
                "column": exc.colno,
            },
        ) from exc
    except ValueError as exc:
        raise InputDataError(
            f"{path}: {exc}", details={"path": str(path), "reason": "invalid_json"}
        ) from exc


def _is_json(path: Path, text: str) -> bool:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return True
    if suffix == ".csv":
        return False
    return text.lstrip()[:1] in ("[", "{")


def _detect_delimiter(header: str) -> str:
    """``,`` or ``;``: the one that splits the header line into more fields."""
    best, best_count = ",", 1
    for candidate in (",", ";"):
        rows = list(csv.reader([header], delimiter=candidate, skipinitialspace=True))
        count = len(rows[0]) if rows else 0
        if count > best_count:
            best, best_count = candidate, count
    return best


@dataclass(frozen=True)
class Table:
    """Columns of a CSV or JSON file.

    Attributes
    ----------
    source : pathlib.Path
        The file the table was read from.
    columns : tuple of str
        Column names in file order (names with surrounding whitespace stripped).
    data : dict
        Cells by column name: strings for CSV, JSON values for JSON files. All lists
        have the same length.
    """

    source: Path
    columns: tuple[str, ...]
    data: dict[str, list[Any]]

    @property
    def n_rows(self) -> int:
        """int: number of data rows."""
        return len(next(iter(self.data.values()), []))

    def resolve_column(self, name: str, *, option: str | None = None) -> str:
        """Find a column by name.

        The name matches a column exactly or, when exactly one column matches, as the
        column name without its ``[unit]`` suffix (``"Q"`` finds ``"Q [m3/s]"``).

        Parameters
        ----------
        name : str
            Requested column name.
        option : str, optional
            Name of the option that gave ``name`` (reported in ``details``).

        Returns
        -------
        str
            The name of the column as it appears in the file.

        Raises
        ------
        InputDataError
            If no column or several columns match; ``details.available`` lists the
            columns.
        """
        if name in self.data:
            return name
        wanted = name.strip()
        matches = [
            column
            for column in self.columns
            if column == wanted or _UNIT_SUFFIX.sub("", column) == wanted
        ]
        if len(matches) == 1:
            return matches[0]
        extra: dict[str, object] = {"column": name, "available": list(self.columns)}
        if option is not None:
            extra["option"] = option
        if matches:
            raise InputDataError(
                f"{self.source}: column {name!r} is ambiguous: {_listed(matches)}",
                details={
                    "path": str(self.source),
                    "reason": "ambiguous_column",
                    **extra,
                },
                hint="Use the full column name.",
            )
        raise InputDataError(
            f"{self.source}: no column {name!r}",
            details={"path": str(self.source), "reason": "missing_column", **extra},
            hint=f"Available columns: {_listed(self.columns)}.",
        )

    def numbers(self, name: str, *, option: str | None = None) -> NDArray[np.float64]:
        """Read a column as numbers.

        Parameters
        ----------
        name : str
            Column name (see :meth:`resolve_column`).
        option : str, optional
            Name of the option that gave ``name``.

        Returns
        -------
        numpy.ndarray
            ``float64`` values; ``NaN`` where the cell is empty or a missing-value
            token.

        Raises
        ------
        InputDataError
            If the column is missing or a cell is not a finite number
            (``details.row``, ``details.value``).
        """
        column = self.resolve_column(name, option=option)
        values = np.empty(self.n_rows, dtype=np.float64)
        for row, cell in enumerate(self.data[column]):
            try:
                values[row] = _to_float(cell)
            except ValueError:
                raise InputDataError(
                    f"{self.source}: row {row + 1}, column {column!r}: "
                    f"{_shown(cell)!r} is not a number",
                    details={
                        "path": str(self.source),
                        "reason": "bad_number",
                        "column": column,
                        "row": row + 1,
                        "value": _shown(cell),
                    },
                ) from None
        return values

    def dates(self, name: str, *, option: str | None = None) -> NDArray[np.datetime64]:
        """Read a column as ISO dates.

        Parameters
        ----------
        name : str
            Column name (see :meth:`resolve_column`).
        option : str, optional
            Name of the option that gave ``name``.

        Returns
        -------
        numpy.ndarray
            ``datetime64[D]`` values.

        Raises
        ------
        InputDataError
            If the column is missing or a cell is not an ISO date ``YYYY-MM-DD``
            (``details.row``, ``details.value``).
        """
        column = self.resolve_column(name, option=option)
        return _to_dates(self.data[column], _Source(path=self.source), column)

    def records(self) -> list[dict[str, Any]]:
        """Return the rows as dictionaries keyed by column name."""
        return [
            {column: self.data[column][row] for column in self.columns}
            for row in range(self.n_rows)
        ]


def _table_from_csv(path: Path, text: str) -> Table:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise InputDataError(
            f"{path}: the file is empty",
            details={"path": str(path), "reason": "empty"},
        )
    delimiter = _detect_delimiter(lines[0])
    try:
        rows = [
            row
            for row in csv.reader(
                io.StringIO(text, newline=""),
                delimiter=delimiter,
                skipinitialspace=True,
            )
            if any(cell.strip() for cell in row)
        ]
    except csv.Error as exc:
        raise InputDataError(
            f"{path}: invalid CSV: {exc}",
            details={"path": str(path), "reason": "invalid_csv"},
        ) from exc
    header = [cell.strip() for cell in rows[0]]
    named = [name for name in header if name]
    duplicates = sorted({name for name in named if named.count(name) > 1})
    if duplicates:
        raise InputDataError(
            f"{path}: duplicate column names: {', '.join(duplicates)}",
            details={
                "path": str(path),
                "reason": "duplicate_column",
                "columns": duplicates,
            },
            hint="Make the column names unique.",
        )
    keep = [index for index, name in enumerate(header) if name]
    data: dict[str, list[Any]] = {header[index]: [] for index in keep}
    for number, row in enumerate(rows[1:], start=1):
        if len(row) < len(header) or any(cell.strip() for cell in row[len(header) :]):
            raise InputDataError(
                f"{path}: row {number} has {len(row)} cells, the header has "
                f"{len(header)}",
                details={
                    "path": str(path),
                    "reason": "ragged_row",
                    "row": number,
                    "cells": len(row),
                    "expected": len(header),
                },
            )
        for index in keep:
            data[header[index]].append(row[index].strip())
    return Table(source=path, columns=tuple(header[index] for index in keep), data=data)


def _table_from_json(path: Path, document: Any) -> Table:
    source = _Source(path=path)
    shapes = "a list of records, an object of equal-length columns or a list of numbers"
    if isinstance(document, list):
        if not document:
            source.fail("the JSON list is empty", reason="empty")
        if all(isinstance(item, Mapping) for item in document):
            columns = tuple(dict.fromkeys(key for item in document for key in item))
            data = {c: [item.get(c) for item in document] for c in columns}
            return Table(source=path, columns=columns, data=data)
        if all(
            item is None or isinstance(item, int | float | str) for item in document
        ) and not any(isinstance(item, bool) for item in document):
            return Table(
                source=path, columns=("values",), data={"values": list(document)}
            )
        source.fail(f"unsupported list content; expected {shapes}", reason="shape")
    if (
        isinstance(document, Mapping)
        and document
        and all(isinstance(value, list) for value in document.values())
    ):
        lengths = {len(value) for value in document.values()}
        if len(lengths) != 1:
            source.fail("the columns have different lengths", reason="ragged_columns")
        columns = tuple(str(key) for key in document)
        data = {str(key): list(value) for key, value in document.items()}
        return Table(source=path, columns=columns, data=data)
    source.fail(f"unsupported JSON structure; expected {shapes}", reason="shape")


def read_table(path: str | os.PathLike[str]) -> Table:
    """Read a CSV or JSON file into a :class:`Table`.

    Parameters
    ----------
    path : str or os.PathLike
        File to read. ``.json`` is JSON, ``.csv`` is CSV; other suffixes are
        recognized by their first character (``[`` or ``{`` -> JSON).

    Returns
    -------
    Table
        The columns of the file (see the module docstring for the accepted shapes).

    Raises
    ------
    NotFoundError
        If the file does not exist.
    InputDataError
        If the file cannot be read or parsed, is empty, or has duplicate column names
        or ragged rows.
    """
    resolved = _file_path(path)
    text = _read_text(resolved)
    if _is_json(resolved, text):
        return _table_from_json(resolved, _parse_json(resolved, text))
    return _table_from_csv(resolved, text)


def load_records(path: str | os.PathLike[str]) -> list[dict[str, Any]]:
    """Read a CSV or JSON file as a list of records.

    Parameters
    ----------
    path : str or os.PathLike
        File to read (see :func:`read_table`).

    Returns
    -------
    list of dict
        One dictionary per row; CSV cells are strings, JSON values keep their type.

    Raises
    ------
    NotFoundError
        If the file does not exist.
    InputDataError
        If the file cannot be read or parsed.
    """
    return read_table(path).records()


# --- cell conversion ------------------------------------------------------------------


def _to_float(cell: object) -> float:
    """Parse the number of a cell (``NaN`` if missing); ``ValueError`` if malformed."""
    if cell is None:
        return math.nan
    if isinstance(cell, bool):
        raise ValueError("boolean is not a number")
    if isinstance(cell, numbers.Real):
        try:
            value = float(cell)
        except OverflowError as exc:
            raise ValueError("number out of range") from exc
        if math.isinf(value):
            raise ValueError("infinite number")
        return value
    if isinstance(cell, str):
        text = cell.strip()
        if text.lower() in _MISSING_TOKENS:
            return math.nan
        if not _NUMBER.fullmatch(text):
            raise ValueError("not a number")
        value = float(text.replace(",", "."))
        if math.isinf(value):
            raise ValueError("number out of range")
        return value
    raise ValueError("not a number")


def _to_dates(
    cells: Sequence[object], source: _Source, column: str | None
) -> NDArray[np.datetime64]:
    """``datetime64[D]`` array of ISO date cells (strings or ``datetime.date``)."""
    iso: list[str] = []
    for row, cell in enumerate(cells):
        text: str | None = None
        if isinstance(cell, dt.datetime):
            if cell.time() == dt.time(0):
                text = cell.date().isoformat()
        elif isinstance(cell, dt.date):
            text = cell.isoformat()
        elif isinstance(cell, np.datetime64):
            text = str(cell.astype("datetime64[D]"))
        elif isinstance(cell, str):
            match = _DATE.fullmatch(cell.strip())
            if match:
                try:
                    dt.date(*(int(part) for part in match.groups()))
                except ValueError:
                    match = None
            text = cell.strip()[:10] if match else None
        if text is None:
            where = f"row {row + 1}" + (f", column {column!r}" if column else "")
            source.fail(
                f"{where}: {_shown(cell)!r} is not an ISO date YYYY-MM-DD",
                reason="bad_date",
                hint="Dates must look like 2024-02-29.",
                row=row + 1,
                value=_shown(cell),
                **({"column": column} if column else {}),
            )
        iso.append(text)
    return np.array(iso, dtype="datetime64[D]")


def _check_increasing(dates: NDArray[np.datetime64], source: _Source) -> None:
    if len(dates) < 2:
        return
    bad = np.flatnonzero(dates[1:] <= dates[:-1])
    if bad.size:
        row = int(bad[0]) + 2
        source.fail(
            f"row {row}: date {dates[row - 1]} does not come after {dates[row - 2]}",
            reason="dates_not_increasing",
            hint="Dates of a series must be strictly increasing (sorted, unique).",
            row=row,
            value=str(dates[row - 1]),
        )


# --- series ---------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class Series:
    """A series of values with optional dates.

    Attributes
    ----------
    values : numpy.ndarray
        ``float64`` values; ``NaN`` marks a missing value.
    dates : numpy.ndarray or None
        ``datetime64[D]`` dates (strictly increasing), same length as ``values``.
    source : str
        ``"inline"`` or the path of the file the series was read from.
    """

    values: NDArray[np.float64]
    dates: NDArray[np.datetime64] | None
    source: str

    def __len__(self) -> int:
        """Return the number of values."""
        return len(self.values)

    @property
    def n_missing(self) -> int:
        """int: number of missing (``NaN``) values."""
        return int(np.isnan(self.values).sum())

    def without_missing(self) -> Series:
        """Return the series without its missing values (dates stay aligned)."""
        keep = ~np.isnan(self.values)
        dates = None if self.dates is None else self.dates[keep]
        return Series(values=self.values[keep], dates=dates, source=self.source)


def _inline_numbers(values: Sequence[object] | NDArray[Any]) -> NDArray[np.float64]:
    source = _Source(option="values")
    if isinstance(values, str) or not isinstance(values, Sequence | np.ndarray):
        source.fail("must be a list of numbers", reason="type")
    if isinstance(values, np.ndarray):
        if values.ndim != 1:
            source.fail("must be a one-dimensional array", reason="type")
        values = values.tolist()
    out = np.empty(len(values), dtype=np.float64)
    for index, item in enumerate(values):
        try:
            out[index] = _to_float(item)
        except ValueError:
            source.fail(
                f"item {index} is not a number: {_shown(item)!r}",
                reason="type",
                index=index,
                value=_shown(item),
            )
    return out


def _series_from_table(
    table: Table, value_column: str | None, date_column: str | None, require_dates: bool
) -> Series:
    source = _Source(path=table.source)
    if value_column is None:
        if len(table.columns) != 1:
            raise InvalidParameterError(
                "Option 'value_column' is required: the file has several columns",
                details={
                    "option": "value_column",
                    "reason": "required",
                    "available": list(table.columns),
                },
                hint=f"Available columns: {_listed(table.columns)}.",
            )
        value_column = table.columns[0]
    values = table.numbers(value_column, option="value_column")
    dates: NDArray[np.datetime64] | None = None
    if date_column is not None:
        dates = table.dates(date_column, option="date_column")
        _check_increasing(dates, source)
    elif require_dates:
        raise InvalidParameterError(
            "Option 'date_column' is required: this command needs dates",
            details={"option": "date_column", "reason": "required"},
            hint=f"Available columns: {_listed(table.columns)}.",
        )
    if len(values) == 0:
        source.fail("the file has no data rows", reason="empty")
    return Series(values=values, dates=dates, source=str(table.source))


def load_series(
    *,
    values: Sequence[object] | NDArray[Any] | None = None,
    dates: Sequence[object] | NDArray[Any] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    require_dates: bool = False,
) -> Series:
    """Load a series from inline values or from a file.

    Exactly one source is used: inline ``values`` (with optional ``dates``), or
    ``input_file`` (with ``value_column`` and optional ``date_column``).

    Parameters
    ----------
    values : sequence of float, optional
        Inline values (``None`` items are missing values).
    dates : sequence of str, optional
        Inline ISO dates ``YYYY-MM-DD`` (``datetime.date`` objects and ``datetime64``
        arrays are accepted too), one per value.
    input_file : str or os.PathLike, optional
        CSV or JSON file (see :func:`read_table`).
    value_column : str, optional
        Column with the values; may be omitted when the file has one column.
    date_column : str, optional
        Column with ISO dates.
    require_dates : bool, optional
        Raise when no dates are given.

    Returns
    -------
    Series
        Values, dates (``None`` when not given) and the source.

    Raises
    ------
    InvalidParameterError
        If the source is ambiguous or missing, file options are mixed with inline
        values, the lengths differ, or dates are required but absent.
    NotFoundError
        If ``input_file`` does not exist.
    InputDataError
        If the file is malformed, has no data, a bad number or date, or dates that
        are not strictly increasing.
    """
    inline = values is not None or dates is not None
    if inline == (input_file is not None):
        raise InvalidParameterError(
            "Give either inline 'values' (with optional 'dates') or 'input_file'",
            details={
                "option": "input_file" if input_file is not None else "values",
                "reason": "one_of",
                "groups": [["values", "dates"], ["input_file", "value_column"]],
            },
        )
    if input_file is not None:
        return _series_from_table(
            read_table(input_file), value_column, date_column, require_dates
        )
    for option, given in (("value_column", value_column), ("date_column", date_column)):
        if given is not None:
            raise InvalidParameterError(
                f"Option {option!r} applies to 'input_file', not to inline values",
                details={"option": option, "reason": "conflict"},
            )
    if values is None:
        raise InvalidParameterError(
            "Inline 'dates' need inline 'values'",
            details={"option": "values", "reason": "required"},
        )
    numbers_array = _inline_numbers(values)
    if len(numbers_array) == 0:
        raise InvalidParameterError(
            "Option 'values': must not be an empty list",
            details={"option": "values", "reason": "empty"},
        )
    date_array: NDArray[np.datetime64] | None = None
    if dates is not None:
        source = _Source(option="dates")
        cells = dates.tolist() if isinstance(dates, np.ndarray) else list(dates)
        date_array = _to_dates(cells, source, None)
        if len(date_array) != len(numbers_array):
            source.fail(
                f"{len(date_array)} dates for {len(numbers_array)} values",
                reason="length_mismatch",
                dates=len(date_array),
                values=len(numbers_array),
            )
        _check_increasing(date_array, source)
    elif require_dates:
        raise InvalidParameterError(
            "Option 'dates' is required: this command needs dates",
            details={"option": "dates", "reason": "required"},
        )
    return Series(values=numbers_array, dates=date_array, source="inline")


# --- hydrograph -----------------------------------------------------------------------

TIME_COLUMN = "time_min"
"""Default time column of a hydrograph file."""
DISCHARGE_COLUMN = "discharge_m3s"
"""Default discharge column of a hydrograph file."""


def _hydrograph_from_table(
    table: Table, time_column: str | None, value_column: str | None
) -> Hydrograph:
    times_name = table.resolve_column(time_column or TIME_COLUMN, option="time_column")
    values_name = table.resolve_column(
        value_column or DISCHARGE_COLUMN, option="value_column"
    )
    times = table.numbers(times_name, option="time_column")
    values = table.numbers(values_name, option="value_column")
    problem = check_table(times, values)
    if problem is not None:
        details = dict(problem.details)
        if "index" in details:
            details["row"] = details.pop("index") + 1
        _Source(path=table.source).fail(
            problem.message,
            reason=problem.reason,
            column=times_name if problem.option == "times_min" else values_name,
            **details,
        )
    return Hydrograph(times, values)


def load_hydrograph(
    *,
    times_min: ArrayLike | None = None,
    discharge_m3s: ArrayLike | None = None,
    input_file: str | os.PathLike[str] | None = None,
    time_column: str | None = None,
    value_column: str | None = None,
) -> Hydrograph:
    """Load a discharge hydrograph from inline lists or from a file.

    Exactly one source is used: the inline lists ``times_min`` and ``discharge_m3s``,
    or ``input_file`` with the optional names of its two columns. The table must obey
    the rules of :func:`hydrolog.routing.hydrograph.check_table` (ADR-0008): at least
    two ordinates, a strictly increasing regular time step, finite values, discharges
    not negative; there is no resampling and no repair.

    Parameters
    ----------
    times_min : sequence of float, optional
        Inline times of the ordinates [min].
    discharge_m3s : sequence of float, optional
        Inline discharges [m3/s], one per time.
    input_file : str or os.PathLike, optional
        CSV or JSON file (see :func:`read_table`); the file that a ``route`` command
        writes with ``output`` is one.
    time_column : str, optional
        Column of the times [min]; default ``time_min``.
    value_column : str, optional
        Column of the discharges [m3/s]; default ``discharge_m3s``.

    Returns
    -------
    Hydrograph
        The validated table.

    Raises
    ------
    InvalidParameterError
        If the source is ambiguous or missing, one inline list lacks the other, a
        column option is given with inline lists, or the inline table breaks a rule
        (``details.option`` ``times_min`` or ``discharge_m3s``, ``details.reason`` as
        in :func:`~hydrolog.routing.hydrograph.check_table`).
    NotFoundError
        If ``input_file`` does not exist.
    InputDataError
        If the file is malformed, lacks a column, has a bad number, or its table
        breaks a rule (``details.reason`` as above, ``details.column`` and the
        1-based data ``details.row``).
    """
    inline = times_min is not None or discharge_m3s is not None
    if inline == (input_file is not None):
        raise InvalidParameterError(
            "Give either the inline lists 'times_min' and 'discharge_m3s' or "
            "'input_file'",
            details={
                "option": "input_file" if input_file is not None else "times_min",
                "reason": "one_of",
                "groups": [["times_min", "discharge_m3s"], ["input_file"]],
            },
        )
    if input_file is not None:
        return _hydrograph_from_table(read_table(input_file), time_column, value_column)
    for column_option, column in (
        ("time_column", time_column),
        ("value_column", value_column),
    ):
        if column is not None:
            raise InvalidParameterError(
                f"Option {column_option!r} applies to 'input_file', not to inline "
                "values",
                details={"option": column_option, "reason": "conflict"},
            )
    if times_min is None or discharge_m3s is None:
        absent, other = (
            ("times_min", "discharge_m3s")
            if times_min is None
            else ("discharge_m3s", "times_min")
        )
        raise InvalidParameterError(
            f"Option {absent!r} is required: give it together with {other!r}",
            details={"option": absent, "reason": "required"},
        )
    return Hydrograph(times_min, discharge_m3s)


# --- watershed ------------------------------------------------------------------------


def _base_type(hint: object) -> object:
    args = [arg for arg in get_args(hint) if arg is not type(None)]
    return args[0] if len(args) == 1 else hint


@functools.cache
def _watershed_fields() -> tuple[tuple[str, ...], frozenset[str], frozenset[str]]:
    """Return required field names (declaration order), numeric fields, text fields."""
    hints = get_type_hints(WatershedParameters)
    required = tuple(
        item.name
        for item in fields(WatershedParameters)
        if item.default is MISSING and item.default_factory is MISSING
    )
    kinds = {name: _base_type(hint) for name, hint in hints.items()}
    numeric = frozenset(name for name, kind in kinds.items() if kind in (int, float))
    text = frozenset(name for name, kind in kinds.items() if kind is str)
    return required, numeric, text


def _watershed_from_mapping(
    document: Mapping[str, Any], source: _Source
) -> WatershedParameters:
    required, numeric, text = _watershed_fields()
    missing = [name for name in required if document.get(name) is None]
    if missing:
        source.fail(
            f"missing required watershed parameters: {', '.join(missing)}",
            reason="missing_field",
            hint=f"Required: {', '.join(required)}.",
            missing=missing,
        )
    for name in numeric:
        value = document.get(name)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, numbers.Real)
            or not math.isfinite(value)
        ):
            source.fail(
                f"{name} must be a finite number, got {_shown(value)!r}",
                reason="type",
                field=name,
                value=_shown(value),
            )
    for name in text:
        value = document.get(name)
        if value is not None and not isinstance(value, str):
            source.fail(
                f"{name} must be a string, got {_shown(value)!r}",
                reason="type",
                field=name,
                value=_shown(value),
            )
    try:
        return WatershedParameters.from_dict(dict(document))
    except InvalidParameterError as exc:
        source.fail(str(exc), reason="invalid_value")
    except (TypeError, ValueError) as exc:
        source.fail(f"invalid watershed parameters: {exc}", reason="invalid_value")


def load_watershed(
    *,
    watershed: Mapping[str, Any] | None = None,
    watershed_file: str | os.PathLike[str] | None = None,
) -> WatershedParameters:
    """Load watershed parameters from an inline object or from a JSON file.

    Parameters
    ----------
    watershed : Mapping, optional
        Inline object with the keys of
        :class:`~hydrolog.morphometry.WatershedParameters`.
    watershed_file : str or os.PathLike, optional
        JSON file holding such an object (the ``WatershedParameters.to_json()``
        format).

    Returns
    -------
    WatershedParameters
        Validated parameters. Unknown keys are ignored.

    Raises
    ------
    InvalidParameterError
        If both or neither source is given, or the inline object is invalid
        (``details.option`` is ``"watershed"``).
    NotFoundError
        If the file does not exist.
    InputDataError
        If the file is not a JSON object or holds missing or invalid parameters.
    """
    if (watershed is None) == (watershed_file is None):
        raise InvalidParameterError(
            "Give exactly one of 'watershed' or 'watershed_file'",
            details={
                "option": (
                    "watershed_file" if watershed_file is not None else "watershed"
                ),
                "reason": "one_of",
                "groups": [["watershed"], ["watershed_file"]],
            },
        )
    document: Any
    if watershed_file is not None:
        path = _file_path(watershed_file, "watershed_file")
        document = _parse_json(path, _read_text(path))
        source = _Source(path=path)
    else:
        document = watershed
        source = _Source(option="watershed")
    if not isinstance(document, Mapping):
        source.fail("expected a JSON object with watershed parameters", reason="shape")
    return _watershed_from_mapping(document, source)


# --- stations -------------------------------------------------------------------------


def _cell_number(
    record: Mapping[str, Any], field_name: str, row: int, source: _Source
) -> float:
    """Parse the number of a record field (``NaN`` when empty or absent)."""
    value = record.get(field_name)
    try:
        return _to_float(value)
    except ValueError:
        source.fail(
            f"row {row}: {field_name} is not a number: {_shown(value)!r}",
            reason="bad_number",
            row=row,
            field=field_name,
            value=_shown(value),
        )


def _required_number(
    record: Mapping[str, Any], field_name: str, row: int, source: _Source
) -> float:
    number = _cell_number(record, field_name, row, source)
    if math.isnan(number):
        source.fail(
            f"row {row}: {field_name} is missing",
            reason="missing_field",
            row=row,
            missing=[field_name],
        )
    return number


def _station_from_record(record: object, row: int, source: _Source) -> Station:
    if not isinstance(record, Mapping):
        source.fail(f"row {row}: expected an object", reason="shape", row=row)
    name = record.get("name", record.get("station_id"))
    if name is None or not str(name).strip():
        source.fail(
            f"row {row}: the station name ('name') is missing",
            reason="missing_field",
            row=row,
            missing=["name"],
        )
    x = _required_number(record, "x", row, source)
    y = _required_number(record, "y", row, source)
    precipitation_mm = _required_number(record, "precipitation_mm", row, source)
    elevation_m = _cell_number(record, "elevation_m", row, source)
    return Station(
        station_id=str(name).strip(),
        x=x,
        y=y,
        precipitation_mm=precipitation_mm,
        elevation_m=None if math.isnan(elevation_m) else elevation_m,
    )


def load_stations(
    *,
    stations: Sequence[Mapping[str, Any]] | None = None,
    stations_file: str | os.PathLike[str] | None = None,
) -> list[Station]:
    """Load precipitation stations from inline records or from a file.

    Records have ``name`` (``station_id`` is accepted as an alias), ``x``, ``y``,
    ``precipitation_mm`` and optionally ``elevation_m``.

    Parameters
    ----------
    stations : sequence of Mapping, optional
        Inline records.
    stations_file : str or os.PathLike, optional
        CSV (header ``name,x,y,precipitation_mm[,elevation_m]``) or JSON list of
        records.

    Returns
    -------
    list of Station
        Stations in the order of the records.

    Raises
    ------
    InvalidParameterError
        If both or neither source is given, or an inline record is invalid
        (``details.option`` is ``"stations"``).
    NotFoundError
        If the file does not exist.
    InputDataError
        If the file is malformed, lacks a required column, has a bad or missing value
        in a row, or names a station twice.
    """
    if (stations is None) == (stations_file is None):
        raise InvalidParameterError(
            "Give exactly one of 'stations' or 'stations_file'",
            details={
                "option": "stations_file" if stations_file is not None else "stations",
                "reason": "one_of",
                "groups": [["stations"], ["stations_file"]],
            },
        )
    records: Sequence[object]
    if stations_file is not None:
        table = read_table(stations_file)
        source = _Source(path=table.source)
        absent = [
            name for name in ("x", "y", "precipitation_mm") if name not in table.columns
        ]
        if not ({"name", "station_id"} & set(table.columns)):
            absent.insert(0, "name")
        if absent:
            source.fail(
                f"missing columns: {', '.join(absent)}",
                reason="missing_column",
                hint="Required columns: name, x, y, precipitation_mm "
                f"(optional: elevation_m). Found: {_listed(table.columns)}.",
                missing=absent,
                available=list(table.columns),
            )
        records = table.records()
    else:
        source = _Source(option="stations")
        if isinstance(stations, str) or not isinstance(stations, Sequence):
            source.fail("expected a list of station objects", reason="type")
        records = stations
    if not records:
        source.fail("no stations given", reason="empty")
    result = [
        _station_from_record(record, row, source)
        for row, record in enumerate(records, start=1)
    ]
    seen: dict[str, int] = {}
    for row, station in enumerate(result, start=1):
        if station.station_id in seen:
            source.fail(
                f"row {row}: station {station.station_id!r} already appears in row "
                f"{seen[station.station_id]}",
                reason="duplicate_station",
                row=row,
                value=station.station_id,
            )
        seen[station.station_id] = row
    return result
