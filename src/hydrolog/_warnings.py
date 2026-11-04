"""Warnings of the library with a stable code and structured details (plan D16).

The library reports a non-fatal observation (a value outside the typical range of a
formula, a short sample...) with ``warnings.warn`` of a :class:`HydrologWarning`. Each
observation has a subclass whose name is its code in CamelCase
(:class:`OutsideTypicalRange` has the code ``outside_typical_range``), and an instance
is made from its details, the values that its English message holds::

    warnings.warn(SmallSample(years=6, minimum=10), stacklevel=2)

``HydrologWarning`` is a ``UserWarning``, so warning filters and
``pytest.warns(UserWarning)`` keep working. Inside an operation
:func:`hydrolog.catalog.capture_warnings` turns a captured warning into a notice with
its code, message and details; the registry :data:`hydrolog.catalog.notices.NOTICES`
lists every code with its level, template and detail keys.

The module is a leaf: the library imports it, and it imports nothing of Hydrolog.
"""

from __future__ import annotations

import re
import warnings
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, ClassVar, Final, Literal

__all__ = [
    "LIBRARY_WARNINGS",
    "MAX_LISTED",
    "HydrologWarning",
    "IncompleteYears",
    "KsTestApproximate",
    "OutsideTypicalRange",
    "ShortRecord",
    "SmallSample",
    "UhModelMismatch",
    "UnknownHietogramType",
    "render",
    "typical_range_fields",
    "warn_outside_typical_range",
    "warning_code",
]

MAX_LISTED: Final = 10
"""Items of a list detail that a message names; the rest are counted."""

_WORD_START = re.compile(r"(?<!^)(?=[A-Z])")


def warning_code(category: type[Warning]) -> str:
    """Return the name of a warning class in snake_case.

    Parameters
    ----------
    category : type
        A warning class.

    Returns
    -------
    str
        ``"user_warning"`` for ``UserWarning``, ``"outside_typical_range"`` for
        :class:`OutsideTypicalRange`.
    """
    return _WORD_START.sub("_", category.__name__).lower()


def _shown(value: Any) -> Any:
    """Write a list or tuple as its items joined by ", " (the first ``MAX_LISTED``)."""
    if not isinstance(value, list | tuple):
        return value
    text = ", ".join(str(item) for item in value[:MAX_LISTED])
    hidden = len(value) - MAX_LISTED
    return f"{text}, and {hidden} more" if hidden > 0 else text


def render(template: str, details: Mapping[str, Any]) -> str:
    """Write a message from its template and details.

    Parameters
    ----------
    template : str
        English message with ``str.format`` fields named after the details; a field
        may have a conversion or a format spec (``{name!r}``, ``{tc_min:g}``).
    details : Mapping
        The values of the fields. A list or tuple is written as its items joined by
        ``", "``, at most :data:`MAX_LISTED` of them followed by ``", and N more"``;
        any other value is formatted as it is.

    Returns
    -------
    str
        The message.

    Raises
    ------
    KeyError
        If the template names a field that is not in ``details``.

    Examples
    --------
    >>> render("Gauges were not used: {stations}.", {"stations": ["A", "B"]})
    'Gauges were not used: A, B.'
    >>> render("tc = {tc_min:g} min", {"tc_min": 90.0})
    'tc = 90 min'
    >>> render("Years {years}", {"years": list(range(2001, 2013))})
    'Years 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, and 2 more'
    """
    return template.format(**{key: _shown(value) for key, value in details.items()})


class HydrologWarning(UserWarning):
    """A non-fatal observation of the library, with a stable code and its details.

    The base of one subclass per code. A subclass sets the class attributes
    ``template`` and ``keys`` (and ``level`` when it is not ``"warning"``); an instance
    is made from exactly the details named by ``keys``, as keyword arguments, and its
    message is the template filled with them (:func:`render`). An instance pickles
    and copies.

    Parameters
    ----------
    **details : Any
        The values of the keys of the class.

    Attributes
    ----------
    level : {"info", "warning"}
        Level of the notice that the warning becomes (class attribute).
    template : str
        English message with a field per detail (class attribute).
    keys : tuple of str
        Names of the details (class attribute).
    details : dict
        The details of this warning, in the order of ``keys``.

    Raises
    ------
    TypeError
        If the details are not exactly ``keys``, or the class is ``HydrologWarning``
        itself (it has no code).

    Examples
    --------
    >>> warning = SmallSample(years=6, minimum=10)
    >>> warning.code(), warning.details
    ('small_sample', {'years': 6, 'minimum': 10})
    >>> str(warning).split(":")[0]
    'Only 6 year(s) in the sample, fewer than 10'
    """

    level: ClassVar[Literal["info", "warning"]] = "warning"
    template: ClassVar[str] = ""
    keys: ClassVar[tuple[str, ...]] = ()

    def __init__(self, **details: Any) -> None:
        kind = type(self)
        if kind is HydrologWarning:
            raise TypeError(
                "HydrologWarning has no code: warn with one of its subclasses"
            )
        if set(details) != set(kind.keys):
            expected = ", ".join(kind.keys) or "(none)"
            raise TypeError(
                f"{kind.__name__} takes the details {expected}; "
                f"got {', '.join(details) or '(none)'}"
            )
        self.details: dict[str, Any] = {key: details[key] for key in kind.keys}
        super().__init__(render(kind.template, self.details))

    @classmethod
    def code(cls) -> str:
        """Return the notice code: the class name in snake_case (:func:`warning_code`).

        Returns
        -------
        str
            The code (``"small_sample"`` for :class:`SmallSample`).
        """
        return warning_code(cls)

    def __reduce__(self) -> tuple[Any, ...]:
        """Rebuild the warning from its class and details (pickle, copy)."""
        return (_restore, (type(self), self.details))


def _restore(kind: type[HydrologWarning], details: dict[str, Any]) -> HydrologWarning:
    """Make a warning of ``kind`` from its details (see ``__reduce__``)."""
    return kind(**details)


class OutsideTypicalRange(HydrologWarning):
    """A parameter of a formula or a model is outside its typical range.

    Details: ``method`` (the formula or the model: a time of concentration method,
    ``scs_cn_amc``, a unit hydrograph model, ``lutz``; the ranges are those of
    ``hydrolog._ranges.TYPICAL_RANGES``), ``parameter`` (its argument, the option of
    the command of the formula), ``field`` (the input the value came from: the option
    of the command that was run or the field of the watershed, see
    :func:`typical_range_fields`), ``value`` and the range ``minimum``, ``maximum``
    (in the unit of the parameter).
    """

    template = (
        "{method}: {parameter}={value} is outside typical range [{minimum}, "
        "{maximum}]. Results may be unreliable."
    )
    keys = ("method", "parameter", "field", "value", "minimum", "maximum")


_FIELDS: ContextVar[Mapping[str, str]] = ContextVar("hydrolog_typical_range_fields")


@contextmanager
def typical_range_fields(fields: Mapping[str, str]) -> Iterator[None]:
    """Name the inputs the parameters of :class:`OutsideTypicalRange` come from.

    Inside the block a warning about the parameter ``name`` has ``field``
    ``fields[name]``; outside every block, or for a parameter that no block names, it
    is the parameter itself. Blocks nest, the inner one first: the time of
    concentration of a watershed names its fields (``length_km`` is
    ``channel_length_km``) inside ``hydrograph generate``, which names its options
    (``ct`` is ``snyder_ct``). The names are kept in a context variable, so threads
    and tasks do not see each other's.

    Parameters
    ----------
    fields : Mapping of str to str
        Parameter name to input name.
    """
    token = _FIELDS.set({**_FIELDS.get({}), **fields})
    try:
        yield
    finally:
        _FIELDS.reset(token)


def warn_outside_typical_range(
    method: str,
    parameter: str,
    value: float,
    minimum: float,
    maximum: float,
    *,
    stacklevel: int = 2,
) -> None:
    """Warn (:class:`OutsideTypicalRange`) if ``value`` is outside [minimum, maximum].

    Parameters
    ----------
    method : str
        The formula or the model.
    parameter : str
        Its argument; ``field`` is the input that :func:`typical_range_fields` names
        for it, else the parameter.
    value : float
        The value.
    minimum, maximum : float
        The typical range, bounds included.
    stacklevel : int, optional
        As in ``warnings.warn``, counted from the caller of this function.
    """
    if minimum <= value <= maximum:
        return
    warnings.warn(
        OutsideTypicalRange(
            method=method,
            parameter=parameter,
            field=_FIELDS.get({}).get(parameter, parameter),
            value=value,
            minimum=minimum,
            maximum=maximum,
        ),
        stacklevel=stacklevel + 1,
    )


class SmallSample(HydrologWarning):
    """A frequency analysis sample has fewer years than its estimates need.

    Details: ``years`` in the sample and the ``minimum`` number of years.
    """

    template = (
        "Only {years} year(s) in the sample, fewer than {minimum}: the frequency "
        "estimates may be unreliable."
    )
    keys = ("years", "minimum")


class ShortRecord(HydrologWarning):
    """A flood frequency sample is shorter than KZGW (2017) requires.

    Details: ``years`` in the sample and the ``minimum`` number of years.
    """

    template = (
        "KZGW (2017) requires at least {minimum} years of data for flood frequency "
        "analysis; the sample has {years}."
    )
    keys = ("years", "minimum")


class KsTestApproximate(HydrologWarning):
    """The Kolmogorov-Smirnov test of a fitted distribution is approximate.

    The parameters are estimated from the same data, so the critical values do not
    apply. No details.
    """

    template = (
        "Kolmogorov-Smirnov test critical values are invalid when parameters are "
        "estimated from the same data. Use Anderson-Darling or AIC for model "
        "selection."
    )
    keys = ()


class IncompleteYears(HydrologWarning):
    """Hydrological years with a day without a value were skipped.

    Details: ``skipped`` and ``total`` years, the skipped ``years`` and, for each of
    them, ``days_with_data`` and ``days_in_year`` (lists in the order of ``years``).
    """

    template = (
        "Skipped {skipped} of {total} hydrological year(s) that are incomplete (a "
        "value is needed for every day of the year): {years}"
    )
    keys = ("skipped", "total", "years", "days_with_data", "days_in_year")


class UnknownHietogramType(HydrologWarning):
    """A report is configured with a hyetograph type that is not known.

    Details: ``hietogram_type`` (the configured one) and the ``allowed`` types.
    """

    template = (
        "ReportConfig.hietogram_type={hietogram_type!r} is not one of {allowed}. "
        "Report may contain incorrect distribution labels."
    )
    keys = ("hietogram_type", "allowed")


class UhModelMismatch(HydrologWarning):
    """A report is configured with another unit hydrograph model than the result's.

    Details: ``uh_model`` (the configured one) and ``result_uh_model`` (the model of
    the unit hydrograph of the result, which the report documents).
    """

    template = (
        "ReportConfig.uh_model={uh_model!r} is not the model of the unit hydrograph "
        "of the result ({result_uh_model!r}); the report documents "
        "{result_uh_model!r}."
    )
    keys = ("uh_model", "result_uh_model")


LIBRARY_WARNINGS: Final[tuple[type[HydrologWarning], ...]] = (
    OutsideTypicalRange,
    SmallSample,
    ShortRecord,
    KsTestApproximate,
    IncompleteYears,
    UnknownHietogramType,
    UhModelMismatch,
)
"""Every warning class of the library, one per code."""
