"""JSON serialization helpers shared by all Hydrolog result dataclasses.

The module provides :func:`to_jsonable`, a strict recursive converter from
Hydrolog result objects (dataclasses holding NumPy arrays, enums, nested
containers) to plain JSON-compatible Python structures, and
:class:`JsonResultMixin`, which adds ``to_dict()`` and ``to_json()`` to a
dataclass.
"""

from __future__ import annotations

import dataclasses
import json
import math
from enum import Enum
from pathlib import PurePath
from typing import Any, Optional

import numpy as np


def _key_to_str(key: Any) -> str:
    """Convert a mapping key to the string used as a JSON object key."""
    if isinstance(key, str) and not isinstance(key, Enum):
        return str(key)
    if isinstance(key, Enum):
        return _key_to_str(key.value)
    if isinstance(key, (bool, np.bool_)):
        return "true" if bool(key) else "false"
    if isinstance(key, (int, np.integer)):
        return str(int(key))
    if isinstance(key, (float, np.floating)):
        return str(float(key))
    if isinstance(key, PurePath):
        return key.as_posix()
    raise TypeError(f"Cannot use object of type {type(key).__name__} as a JSON key")


def _array_to_list(array: np.ndarray) -> Any:
    """Convert an ndarray to nested lists, mapping NaN/Inf to ``None``."""
    if array.dtype.kind in "iub":
        return array.tolist()
    if array.dtype.kind == "f" and bool(np.isfinite(array).all()):
        return array.tolist()
    return to_jsonable(array.tolist())


def to_jsonable(obj: Any) -> Any:
    """
    Recursively convert an object to JSON-compatible Python structures.

    Parameters
    ----------
    obj : Any
        Value to convert. Supported: ``None``, ``bool``, ``int``, ``float``,
        ``str``, NumPy scalars and arrays, ``Enum``, ``pathlib`` paths,
        dataclass instances, ``dict``, ``list`` and ``tuple`` (containing any
        of the above).

    Returns
    -------
    Any
        Structure built only from ``None``, ``bool``, ``int``, ``float``,
        ``str``, ``list`` and ``dict`` that ``json.dumps(allow_nan=False)``
        accepts.

    Raises
    ------
    TypeError
        If ``obj`` (or a nested value) is of an unsupported type. There is no
        silent ``str()`` fallback.

    Notes
    -----
    - Dataclasses become dicts keyed by field name, in declaration order.
    - ``numpy.ndarray`` becomes a (nested) list; NaN and +/-Inf become ``None``.
    - NumPy scalars become Python scalars; non-finite floats become ``None``.
    - ``Enum`` becomes its ``value``; tuples become lists.
    - Dict keys are converted to strings.
    - Paths become POSIX strings.

    Examples
    --------
    >>> to_jsonable({"a": (1, float("nan"))})
    {'a': [1, None]}
    """
    if obj is None:
        return None
    if isinstance(obj, Enum):
        return to_jsonable(obj.value)
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        value = float(obj)
        return value if math.isfinite(value) else None
    if isinstance(obj, str):
        return str(obj)
    if isinstance(obj, np.ndarray):
        return _array_to_list(obj)
    if isinstance(obj, PurePath):
        return obj.as_posix()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: to_jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj)
        }
    if isinstance(obj, dict):
        return {_key_to_str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class JsonResultMixin:
    """
    Mixin adding JSON export to a result dataclass.

    Inherit from it in a ``@dataclass`` class. The mixin declares no fields,
    so it does not affect the dataclass constructor or field order.
    """

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the result to a JSON-compatible dictionary.

        Returns
        -------
        dict
            Field name to value mapping (see :func:`to_jsonable`).
        """
        result = to_jsonable(self)
        assert isinstance(result, dict)
        return result

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Serialize the result to a JSON string.

        Parameters
        ----------
        indent : int, optional
            Indentation level for pretty printing.

        Returns
        -------
        str
            JSON document (UTF-8 characters are not escaped; NaN/Inf are
            emitted as ``null``).
        """
        return json.dumps(
            self.to_dict(), ensure_ascii=False, allow_nan=False, indent=indent
        )
