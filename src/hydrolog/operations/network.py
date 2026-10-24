"""Operations of the group ``network``: classification of a river network.

Stream ordering (Strahler, Shreve) and network statistics of
:class:`~hydrolog.network.StreamNetwork` for segments given inline or in a CSV/JSON
file. The function is re-exported by :mod:`hydrolog.operations`.

Segments
--------
A segment has ``segment_id`` (integer), ``upstream_ids`` (the ids of the segments that
flow into it; empty for a headwater) and ``length_km``. In a file the columns have
these names; in CSV the ids of ``upstream_ids`` are separated by ``;``, ``|``, a
comma or a space (``"3;4"``) and an empty cell is a headwater; in JSON the cell is a
list of integers (or ``null``/``[]``).
"""

from __future__ import annotations

import math
import numbers
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, NoReturn

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.inputs import read_table
from hydrolog.exceptions import InputDataError, InvalidParameterError
from hydrolog.network import (
    NetworkStatistics,
    OrderingMethod,
    StreamNetwork,
    StreamSegment,
    stream_frequency,
)
from hydrolog.operations._analysis import check_choice

__all__ = ["NetworkAnalysis", "network_stats"]

Method = Literal["strahler", "shreve"]

_METHODS: tuple[str, ...] = ("strahler", "shreve")
_ID_SEPARATORS = re.compile(r"[;|,\s]+")
_MAX_LISTED = 10


@dataclass
class NetworkAnalysis(JsonResultMixin):
    """Stream order statistics of a river network.

    Attributes
    ----------
    method : str
        Ordering method: ``"strahler"`` or ``"shreve"``.
    n_segments : int
        Number of segments in the network.
    stream_frequency_per_km2 : float or None
        Stream frequency Fs = number of segments / area [1/km2]; ``None`` without
        ``area_km2``.
    statistics : NetworkStatistics
        Maximum order, segment counts, total and mean lengths per order,
        bifurcation and length ratios, total stream length [km] and drainage density
        [km/km2] (``None`` without ``area_km2``). Dictionaries are keyed by the order
        (a string in JSON).
    """

    method: str
    n_segments: int
    stream_frequency_per_km2: float | None
    statistics: NetworkStatistics


# --- reading segments -----------------------------------------------------------------


def _fail(
    path: Path | None, message: str, *, reason: str, **details: object
) -> NoReturn:
    """Raise the error of a bad segment: a data error for a file, else a parameter."""
    if path is not None:
        raise InputDataError(
            f"{path}: {message}",
            details={"path": str(path), "reason": reason, **details},
        )
    raise InvalidParameterError(
        f"Option 'segments': {message}",
        details={"option": "segments", "reason": reason, **details},
    )


def _integer(value: object, field: str, row: int, path: Path | None) -> int:
    """Integer of an id cell: an int, an integral float or a numeric string."""
    number: float | None = None
    if isinstance(value, bool):
        number = None
    elif isinstance(value, numbers.Real):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            number = None
    if number is None or not math.isfinite(number) or not number.is_integer():
        _fail(
            path,
            f"row {row}: {field} must be an integer, got {value!r}",
            reason="bad_number",
            row=row,
            field=field,
            value=str(value),
        )
    return int(number)


def _upstream_ids(value: object, row: int, path: Path | None) -> list[int]:
    """Ids of the upstream segments of a record (empty for a headwater)."""
    if value is None:
        return []
    if isinstance(value, str):
        tokens = [token for token in _ID_SEPARATORS.split(value.strip()) if token]
        return [_integer(token, "upstream_ids", row, path) for token in tokens]
    if isinstance(value, Sequence):
        return [_integer(item, "upstream_ids", row, path) for item in value]
    return [_integer(value, "upstream_ids", row, path)]


def _length_km(value: object, row: int, path: Path | None) -> float:
    """Length of a segment [km]: a finite number, not negative."""
    if value is None or (isinstance(value, str) and not value.strip()):
        _fail(
            path,
            f"row {row}: length_km is missing",
            reason="missing_field",
            row=row,
            missing=["length_km"],
        )
    number: float | None = None
    if isinstance(value, bool):
        number = None
    elif isinstance(value, numbers.Real):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip().replace(",", "."))
        except ValueError:
            number = None
    if number is None or not math.isfinite(number) or number < 0:
        _fail(
            path,
            f"row {row}: length_km must be a finite number >= 0, got {value!r}",
            reason="bad_number",
            row=row,
            field="length_km",
            value=str(value),
        )
    return number


def _graph_error(
    exc: InvalidParameterError, rows: Mapping[int, int], path: Path | None
) -> NoReturn:
    """Re-raise a graph error of the library (unknown upstream id, cycle) with its row.

    ``StreamNetwork.classify`` finds the problem; this adds the row of the record
    (and, for a file, turns it into an input data error).
    """
    reason = exc.details.get("reason")
    if reason == "unknown_upstream":
        segment_id = exc.details["segment_id"]
        upstream = exc.details["upstream_id"]
        row = rows[segment_id]
        _fail(
            path,
            f"row {row}: upstream segment {upstream} of segment {segment_id} is not "
            "in the network",
            reason="unknown_upstream",
            row=row,
            value=upstream,
        )
    if reason == "cycle":
        members: list[int] = exc.details["segments"]
        if len(members) == 1:
            row = rows[members[0]]
            _fail(
                path,
                f"row {row}: segment {members[0]} lists itself as upstream",
                reason="cycle",
                row=row,
                segments=members,
            )
        listed = ", ".join(str(item) for item in members[:_MAX_LISTED])
        _fail(
            path,
            f"the segments form a cycle (involving {listed}"
            f"{', ...' if len(members) > _MAX_LISTED else ''})",
            reason="cycle",
            segments=members[:_MAX_LISTED],
        )
    raise exc


def _build_segments(
    records: Sequence[object], path: Path | None
) -> tuple[list[StreamSegment], dict[int, int]]:
    """Validated segments of the records and the row of each segment id.

    Each record has ``segment_id``, ``length_km`` and (optionally) ``upstream_ids``.
    The links between the segments are checked by ``StreamNetwork.classify``.
    """
    if not records:
        _fail(path, "no segments given", reason="empty")
    segments: list[StreamSegment] = []
    rows: dict[int, int] = {}
    for row, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            _fail(path, f"row {row}: expected an object", reason="shape", row=row)
        missing = [name for name in ("segment_id", "length_km") if name not in record]
        if missing:
            _fail(
                path,
                f"row {row}: missing {', '.join(missing)}",
                reason="missing_field",
                row=row,
                missing=missing,
            )
        segment_id = _integer(record["segment_id"], "segment_id", row, path)
        if segment_id in rows:
            _fail(
                path,
                f"row {row}: segment {segment_id} already appears in row "
                f"{rows[segment_id]}",
                reason="duplicate_segment",
                row=row,
                value=segment_id,
            )
        upstream = _upstream_ids(record.get("upstream_ids"), row, path)
        if len(set(upstream)) != len(upstream):
            _fail(
                path,
                f"row {row}: upstream_ids of segment {segment_id} repeat an id",
                reason="duplicate_upstream",
                row=row,
            )
        rows[segment_id] = row
        segments.append(
            StreamSegment(
                segment_id=segment_id,
                upstream_ids=upstream,
                length_km=_length_km(record["length_km"], row, path),
            )
        )
    return segments, rows


def _file_records(path: str | os.PathLike[str]) -> tuple[Path, list[dict[str, Any]]]:
    """Records ``segment_id``/``upstream_ids``/``length_km`` of a CSV or JSON file."""
    table = read_table(path)
    names = {
        field: table.resolve_column(field, option="segments_file")
        for field in ("segment_id", "upstream_ids", "length_km")
    }
    records = [
        {field: table.data[column][row] for field, column in names.items()}
        for row in range(table.n_rows)
    ]
    return table.source, records


# --- operation ------------------------------------------------------------------------


def network_stats(
    *,
    segments: Sequence[Mapping[str, Any]] | None = None,
    segments_file: str | os.PathLike[str] | None = None,
    method: Method = "strahler",
    area_km2: float | None = None,
) -> NetworkAnalysis:
    """Stream ordering and network statistics (``network stats``).

    Orders the segments of a river network with the Strahler or Shreve method and
    summarizes the network: segments and lengths per order, bifurcation ratios
    ``Rb = N_i / N_(i+1)``, length ratios ``Rl = mean length_(i+1) / mean length_i``,
    total stream length and, with ``area_km2``, drainage density and stream frequency
    (:class:`hydrolog.network.StreamNetwork`). The ratios have their Horton meaning
    for the Strahler orders; for Shreve magnitudes they are formal ratios between
    consecutive magnitudes.

    Parameters
    ----------
    segments : sequence of Mapping, optional
        Inline segments: objects with ``segment_id``, ``upstream_ids`` (may be empty
        or omitted for a headwater) and ``length_km``.
    segments_file : str or os.PathLike, optional
        CSV or JSON file with the columns ``segment_id``, ``upstream_ids`` and
        ``length_km`` (see the module docstring for the format of ``upstream_ids``).
    method : {"strahler", "shreve"}, optional
        Ordering method, by default ``"strahler"``.
    area_km2 : float, optional
        Watershed area [km2], positive; enables drainage density and stream frequency.

    Returns
    -------
    NetworkAnalysis
        Method, number of segments, stream frequency and the network statistics.

    Raises
    ------
    InvalidParameterError
        If both or neither of ``segments`` and ``segments_file`` is given, an inline
        segment is invalid, ``method`` is not allowed or ``area_km2`` is not
        positive.
    NotFoundError
        If ``segments_file`` does not exist.
    InputDataError
        If the file cannot be read, lacks a column, or a segment is invalid: a bad
        number, a repeated segment id, an upstream id that is not in the network or
        a cycle (``details.reason``, ``details.row``).
    """
    check_choice("method", method, _METHODS)
    if (segments is None) == (segments_file is None):
        raise InvalidParameterError(
            "Give exactly one of 'segments' or 'segments_file'",
            details={
                "option": "segments_file" if segments_file is not None else "segments",
                "reason": "one_of",
                "groups": [["segments"], ["segments_file"]],
            },
        )
    path: Path | None = None
    records: Sequence[object]
    if segments_file is not None:
        path, records = _file_records(segments_file)
    else:
        if isinstance(segments, str) or not isinstance(segments, Sequence):
            _fail(None, "expected a list of segment objects", reason="type")
        records = segments
    segment_list, rows = _build_segments(records, path)
    network = StreamNetwork(segment_list, area_km2=area_km2)
    try:
        network.classify(OrderingMethod(method))
    except InvalidParameterError as exc:
        _graph_error(exc, rows, path)
    frequency = (
        None
        if area_km2 is None
        else stream_frequency(n_streams=network.n_segments, area_km2=area_km2)
    )
    return NetworkAnalysis(
        method=method,
        n_segments=network.n_segments,
        stream_frequency_per_km2=frequency,
        statistics=network.get_statistics(),
    )
