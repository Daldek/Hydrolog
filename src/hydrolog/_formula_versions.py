"""The versions of the formulas a computation used (Nogat CMP-2.8).

Every Tier A formula with a spec records its name and ``formula_version`` when it
returns a checked result (:func:`hydrolog._formulas.checked_outputs`); a
:func:`recording` block collects what ran inside it, so a result can carry the
version of each formula it depends on: :func:`hydrolog.catalog.run_command` records
around every operation and the envelope carries the record in ``formula_versions``.

The module is a leaf without NumPy, so the catalog imports it as it imports
:mod:`hydrolog._warnings`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

__all__ = ["record", "recording"]

_RECORDS: ContextVar[tuple[dict[str, int], ...]] = ContextVar(
    "hydrolog_formula_versions", default=()
)


@contextmanager
def recording() -> Iterator[dict[str, int]]:
    """Collect the formulas that return a result inside the block.

    Blocks nest: a formula is recorded in every block around it. The record is kept
    in a context variable, so threads and tasks do not see each other's.

    Yields
    ------
    dict of str to int
        Spec name to ``formula_version``, filled while the block runs.

    Examples
    --------
    >>> with recording() as used:
    ...     record("kirpich", 1)
    >>> used
    {'kirpich': 1}
    """
    found: dict[str, int] = {}
    token = _RECORDS.set((*_RECORDS.get(), found))
    try:
        yield found
    finally:
        _RECORDS.reset(token)


def record(name: str, version: int) -> None:
    """Record that the formula ``name`` of ``version`` gave a result.

    Parameters
    ----------
    name : str
        Name of the formula's spec.
    version : int
        Its ``formula_version``.
    """
    for found in _RECORDS.get():
        found[name] = version
