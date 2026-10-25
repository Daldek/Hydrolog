"""The parameters of a calculation, described the same way for every element (ADR-0012).

A reach, a rainfall source, a runoff model and a node of a network each have a
``describe()`` that returns a list of :class:`Parameter`: the name, the value that the
calculation used, its unit and where it came from. A network result carries that list
for every node, next to the peak, the time to peak and the volume, so that a schematic
of the network can show the values of the calculation without knowing the models.

The source says how the value came to be:

``"given"``
    the caller set it (an argument of a constructor, a field of a document);
``"default"``
    nobody set it and the library default was used (``ia_coefficient`` 0.2, the
    initial outflow of a reach that is the first inflow ordinate);
``"computed"``
    the calculation derived it (the time of concentration of a watershed, the number
    of sub-reaches of a Muskingum reach, the celerity of a section).

The unit follows from the name, as everywhere in Hydrolog (``tc_min`` is in minutes,
``area_km2`` in km2, ``slope_m_per_m`` in m/m); a quantity without a unit suffix
(``x``, ``cn``, ``subreaches``) has none.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal

from hydrolog._serialization import JsonResultMixin

__all__ = ["Parameter", "ParameterSource", "ParameterValue", "parameter", "unit_of"]

ParameterSource = Literal["given", "computed", "default"]
ParameterValue = float | int | str | bool

_SUFFIXES: Final[tuple[tuple[str, str], ...]] = (
    ("_m_per_m", "m/m"),
    ("_m_per_s", "m/s"),
    ("_m3s", "m3/s"),
    ("_km2", "km2"),
    ("_m3", "m3"),
    ("_mm", "mm"),
    ("_km", "km"),
    ("_min", "min"),
    ("_pct", "%"),
    ("_m", "m"),
)
"""Ends of a name that give its unit, the longest first."""


def unit_of(name: str) -> str | None:
    """Return the unit that the name of a quantity gives.

    Parameters
    ----------
    name : str
        The name, with the unit as its last part (``tc_min``, ``storage_m3``).

    Returns
    -------
    str or None
        The unit (``"min"``, ``"m3"``, ``"m3/s"``, ``"m/m"``...), or ``None`` for a name
        that has none (``x``, ``cn``, ``subreaches``).

    Examples
    --------
    >>> unit_of("reference_discharge_m3s"), unit_of("x")
    ('m3/s', None)
    """
    for suffix, unit in _SUFFIXES:
        if name.endswith(suffix):
            return unit
    return None


@dataclass(frozen=True)
class Parameter(JsonResultMixin):
    """One value that a calculation used.

    Attributes
    ----------
    name : str
        The name of the quantity, as the option or the document field is called when
        there is one (``lag_min``, ``cn``, ``tc_min``).
    value : float or int or str or bool
        The value that the calculation used.
    unit : str or None
        Its unit (``"min"``, ``"km2"``...); ``None`` when it has none.
    source : {"given", "computed", "default"}
        Where the value came from: set by the caller, derived by the calculation, or
        the library default.
    """

    name: str
    value: ParameterValue
    unit: str | None
    source: ParameterSource


def parameter(
    name: str,
    value: object,
    source: ParameterSource,
    units: Mapping[str, str | None] | None = None,
) -> Parameter:
    """Make a :class:`Parameter` whose unit follows from its name.

    Parameters
    ----------
    name : str
        The name of the quantity.
    value : object
        The value: a number, a string or a boolean (a NumPy scalar is converted).
    source : {"given", "computed", "default"}
        Where the value came from.
    units : mapping, optional
        Units that replace the one the name gives (``None`` for no unit), for a name
        whose ending only looks like a unit: the ``subreaches_min`` of a Muskingum
        reach is a number of sub-reaches.

    Returns
    -------
    Parameter
        The parameter.

    Raises
    ------
    TypeError
        If the value is not a number, a string or a boolean.
    """
    item = getattr(value, "item", None)
    plain = item() if callable(item) and not isinstance(value, str) else value
    if not isinstance(plain, bool | int | float | str):
        raise TypeError(f"The value of {name!r} is not a number or a string: {value!r}")
    unit = units[name] if units is not None and name in units else unit_of(name)
    return Parameter(name, plain, unit, source)
