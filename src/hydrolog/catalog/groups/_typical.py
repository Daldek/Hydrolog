"""The typical ranges of the commands, from :data:`hydrolog._ranges.TYPICAL_RANGES`.

The commands of a formula check the ranges of its arguments, named like their
options; a command that takes a watershed checks the ranges of every time of
concentration method on the fields :data:`hydrolog._ranges.TC_INPUTS` names. The
option descriptions quote the ranges with :func:`typically`, so no number is written
twice.
"""

from __future__ import annotations

from collections.abc import Iterable

from hydrolog._ranges import TC_INPUTS, typical_range, typical_ranges
from hydrolog.catalog.spec import Lang, RangeCheck

TC_METHODS = ("kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich")
"""The methods of ``tc watershed`` and of ``tc_method`` of ``hydrograph generate``."""


def _number(value: float, lang: Lang) -> str:
    """Write a bound as a person reads it: ``70,000`` (en) or ``70 000`` (pl)."""
    text = f"{value:,g}"
    return text.replace(",", " ").replace(".", ",") if lang == "pl" else text


def typically(method: str, parameter: str, lang: Lang = "en") -> str:
    """Return the words of a typical range for an option description.

    Parameters
    ----------
    method, parameter : str
        The range (:func:`hydrolog._ranges.typical_range`).
    lang : {"en", "pl"}, optional
        Language of the words.

    Returns
    -------
    str
        ``"typically 0.03-0.1"`` or ``"typowo 0,03–0,1"``; ``"typically <= 0.366"``
        for a range from 0; a range to be verified (``verified`` false) adds
        ``", to be verified"`` or ``", do weryfikacji"``.
    """
    found = typical_range(method, parameter)
    word = "typowo" if lang == "pl" else "typically"
    if found.maximum is None:
        at_least = "≥" if lang == "pl" else ">="
        text = f"{word} {at_least} {_number(found.minimum or 0.0, lang)}"
    elif not found.minimum:
        text = f"{word} {'≤' if lang == 'pl' else '<='} {_number(found.maximum, lang)}"
    else:
        dash = "–" if lang == "pl" else "-"
        bounds = f"{_number(found.minimum, lang)}{dash}{_number(found.maximum, lang)}"
        text = f"{word} {bounds}"
    if found.verified:
        return text
    return f"{text}, {'do weryfikacji' if lang == 'pl' else 'to be verified'}"


def formula_ranges(method: str, options: Iterable[str]) -> tuple[RangeCheck, ...]:
    """Return the ranges of ``method`` a command of its formula checks on its options.

    Parameters
    ----------
    method : str
        The method.
    options : iterable of str
        The option names of the command, the arguments of the formula.

    Returns
    -------
    tuple of RangeCheck
        One per range whose parameter is an option, taken from that option.
    """
    names = set(options)
    return tuple(
        RangeCheck(found.method, found.parameter, (found.parameter,))
        for found in typical_ranges(method)
        if found.parameter in names
    )


WATERSHED_TC_RANGES: tuple[RangeCheck, ...] = tuple(
    RangeCheck(
        found.method, found.parameter, TC_INPUTS[method].get(found.parameter, ())
    )
    for method in TC_METHODS
    for found in typical_ranges(method)
)
"""The ranges of the six time of concentration methods, checked on a watershed."""
