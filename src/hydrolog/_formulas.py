"""Hydrolog's side of Nogat's computation standard: errors, notices and versions.

Every Tier A formula of Hydrolog is declared once, by a ``FormulaSpec`` of the copied
reference module :mod:`hydrolog.nogat_formulas` next to its function (Nogat CMP-2.1),
and leaves its checks to that module (CMP-3.5) through the two calls of this one::

    x = checked_inputs(KIRPICH, length_km=length_km, slope_m_per_m=slope_m_per_m)
    tc = ...  # the equation, with the constants of the spec
    return checked_outputs(KIRPICH, {"tc_min": tc}).real("tc_min")

:func:`checked_inputs` runs ``validate`` with :data:`ERRORS`, which turns a refusal
into :class:`~hydrolog.exceptions.InvalidParameterError` (code ``validation_error``,
``details.reason`` of the standard: ``outside_physical_range``,
``precondition_failed``, ``invalid_type``, ``invalid_shape`` or ``invalid_choice``,
``details.option`` the input it names), and issues each notice as a warning of the
library. The standard's notice ``outside_applicability`` (CMP-3.3) is issued as
Hydrolog's :class:`~hydrolog._warnings.OutsideTypicalRange`, code
``outside_typical_range``, whose ``method`` is the name of the spec and whose
``parameter`` is the input: the code is renamed together with its consumers, in one
release (plan of the computation standard, step 5). :func:`checked_outputs` runs
``check_outputs`` (:class:`~hydrolog.exceptions.CalculationError`, code
``calculation_error``, for a result a formula must not return, CMP-3.4) and records
the spec's ``formula_version`` (:mod:`hydrolog._formula_versions`, CMP-2.8).

:func:`specs` gathers the specs of the modules of :data:`FORMULA_MODULES` (each
lists them in ``SPECS``, and its Tier B formulas in ``TIER_B``), from which
``scripts/generate_formulas.py`` writes ``docs/FORMULAS.md``, the cards
``formulas/<name>.toml`` and :mod:`hydrolog._applicability` (CMP-2.6).
"""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Final, cast

from hydrolog._formula_versions import record
from hydrolog._warnings import warn_outside_typical_range
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.nogat_formulas import (
    Delegated,
    FormulaSpec,
    Notice,
    TierBSpec,
    Values,
    check_outputs,
    validate,
)

__all__ = [
    "DELEGATED",
    "ERRORS",
    "FORMULA_MODULES",
    "checked_inputs",
    "checked_outputs",
    "specs",
    "tier_b",
]

FORMULA_MODULES: Final[tuple[str, ...]] = ("hydrolog.runoff.scs_cn",)
"""The modules whose ``SPECS`` (and ``TIER_B``) declare Hydrolog's formulas, in the
order of ``docs/FORMULAS.md``."""

DELEGATED: Final[tuple[Delegated, ...]] = ()
"""Computations delegated to third-party libraries (CMP-1.2)."""


class _HydrologErrors:
    """Hydrolog's exceptions for the refusals and failed results of the standard."""

    def validation(self, message: str, details: dict[str, object]) -> Exception:
        """Return an ``InvalidParameterError`` whose ``option`` is the input."""
        variable = details.get("variable")
        named = {"option": variable} if isinstance(variable, str) else {}
        return InvalidParameterError(message, details={**details, **named})

    def calculation(self, message: str, details: dict[str, object]) -> Exception:
        """Return a ``CalculationError``."""
        return CalculationError(message, details=details)


ERRORS: Final = _HydrologErrors()
"""The project's :class:`~hydrolog.nogat_formulas.Errors` (ERR-1)."""


def _issue(spec: FormulaSpec, notice: Notice) -> None:
    """Warn of a notice of ``validate`` as the library warns, for the formula's caller.

    Raises
    ------
    TypeError
        For a notice the library has no warning for: one of an applicability
        constraint or of an unreferenced formula, or a range that is not closed.
    """
    details = notice.details
    variable = details.get("variable")
    bounds = details.get("range")
    if notice.code != "outside_applicability" or not isinstance(variable, str):
        raise TypeError(f"{spec.name}: no warning of the library for {notice.code}")
    if not isinstance(bounds, Mapping) or not (
        bounds.get("low_inclusive") and bounds.get("high_inclusive")
    ):
        raise TypeError(f"{spec.name}: {variable} needs a closed applicability range")
    warn_outside_typical_range(
        spec.name,
        variable,
        cast("float", details["value"]),
        cast("float", bounds["low"]),
        cast("float", bounds["high"]),
        stacklevel=4,
    )


def checked_inputs(spec: FormulaSpec, /, **inputs: object) -> Values:
    """Check the inputs of a formula and warn of each notice (CMP-3.1 to CMP-3.3).

    Parameters
    ----------
    spec : FormulaSpec
        The formula's spec.
    **inputs : object
        Every input of the spec, as the function received it.

    Returns
    -------
    Values
        The checked inputs: ``float``, ``int``, ``str`` or new ``float64`` arrays.

    Raises
    ------
    InvalidParameterError
        If an input is refused (``details.reason`` of the standard).

    Warns
    -----
    OutsideTypicalRange
        For each input outside its applicability range, in the order of the spec
        (``method`` the spec's name, ``parameter`` the input).
    """
    values, notices = validate(spec, inputs, errors=ERRORS)
    for notice in notices:
        _issue(spec, notice)
    return values


def checked_outputs(
    spec: FormulaSpec,
    outputs: Mapping[str, object],
    inputs: Mapping[str, object] | None = None,
) -> Values:
    """Check the outputs of a formula and record its version (CMP-3.4, CMP-2.8).

    Parameters
    ----------
    spec : FormulaSpec
        The formula's spec.
    outputs : Mapping
        Every output of the spec by name.
    inputs : Mapping, optional
        The checked inputs, needed for an output that copies the gaps of an input.

    Returns
    -------
    Values
        The checked outputs; a value within its boundary tolerance of a bound is
        set to the bound.

    Raises
    ------
    CalculationError
        If an output is not finite or lies beyond its physical range.
    """
    checked = check_outputs(spec, outputs, inputs=inputs, errors=ERRORS)
    record(spec.name, spec.formula_version)
    return checked


def specs() -> tuple[FormulaSpec, ...]:
    """Return the spec of every Tier A formula, module by module.

    Returns
    -------
    tuple of FormulaSpec
        In the order of :data:`FORMULA_MODULES` and of each module's ``SPECS``.
    """
    found: list[FormulaSpec] = []
    for name in FORMULA_MODULES:
        found += cast("tuple[FormulaSpec, ...]", importlib.import_module(name).SPECS)
    return tuple(found)


def tier_b() -> tuple[TierBSpec, ...]:
    """Return the Tier B formulas of the modules, module by module (CMP-2.2).

    Returns
    -------
    tuple of TierBSpec
        In the order of :data:`FORMULA_MODULES`.
    """
    found: list[TierBSpec] = []
    for name in FORMULA_MODULES:
        module = importlib.import_module(name)
        found += cast("tuple[TierBSpec, ...]", getattr(module, "TIER_B", ()))
    return tuple(found)
