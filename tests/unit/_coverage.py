"""The records of the simulated coverage of the intervals (Nogat CMP-6.11).

A coverage test (marker ``nightly``) asserts the coverage of an interval with
``assert_coverage`` and keeps the records it returns with :func:`keep`, in the file of
the last run, :data:`RECORDS`: one record per formula, setting, sample size and level,
replaced when the same setting runs again. ``scripts/generate_formulas.py`` reads the
file and lists the records under their formulas in ``docs/FORMULAS.md``; after a
nightly run that changes them, regenerate the document and commit both. Runs of
several processes at once (``pytest -m nightly -k ...`` in parallel) merge their
records under a lock file beside the records.
"""

import contextlib
import dataclasses
import json
import os
import time
from collections.abc import Iterator, Sequence
from pathlib import Path

from hydrolog.nogat_formulas import Coverage

RECORDS = Path(__file__).resolve().parents[1] / "fixtures" / "formulas"
RECORDS = RECORDS / "interval-coverage.json"
"""The coverage of the last nightly run, a JSON array of ``Coverage`` records."""
_LOCK = RECORDS.with_suffix(".lock")


def _key(record: Coverage) -> tuple[str, str, int, float]:
    return (record.formula, record.setting, record.size, -record.confidence_level)


def load() -> list[Coverage]:
    """Return the records of the last run, in the order of the file."""
    if not RECORDS.exists():
        return []
    return [Coverage(**item) for item in json.loads(RECORDS.read_text("utf-8"))]


@contextlib.contextmanager
def _locked(wait_s: float = 600.0) -> Iterator[None]:
    """Hold the lock file while the records are merged (O_EXCL, any platform)."""
    deadline = time.monotonic() + wait_s
    while True:
        try:
            handle = os.open(_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise TimeoutError(f"{_LOCK} is held by another run") from None
            time.sleep(0.1)
    try:
        yield
    finally:
        os.close(handle)
        _LOCK.unlink()


def keep(records: Sequence[Coverage]) -> None:
    """Merge the records of a run into :data:`RECORDS`, sorted by their key.

    A record replaces the one of the same formula, setting, sample size and level.
    """
    with _locked():
        merged = {_key(record): record for record in load()}
        merged.update({_key(record): record for record in records})
        items = [dataclasses.asdict(merged[key]) for key in sorted(merged)]
        text = json.dumps(items, ensure_ascii=False, indent=1) + "\n"
        RECORDS.write_text(text, encoding="utf-8")
