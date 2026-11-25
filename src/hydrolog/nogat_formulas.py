"""Formulas of a project that computes: specs, checks, units and generated tests.

Nogat's reference implementation of CMP-8.1. Every project that computes copies
this file byte for byte into its package, keeping its name ``nogat_formulas.py``,
and never edits it (DEV-15.6): a change is made in Nogat ``standards/reference/``
and copied again, and ``uv run scripts/ecosystem.py drift`` in Nogat reports each
copy. Cards follow Nogat ``schemas/formula/card-1.schema.json``, which projects
copy into ``schemas/nogat/``. The module needs NumPy only; its test helpers import
pytest and Hypothesis when they are called, so a package imports it without them.

A formula is declared once by its spec, next to its function (CMP-2.1), and leaves
every check to the module (CMP-3.5); its docstring names the spec and holds no
digit (CMP-2.7)::

    TC = FormulaSpec(name="kirpich", function="hydrolog.tc.kirpich", ...)

    def kirpich(length_km: float, slope_m_per_m: float) -> TcResult:
        inputs = {"length_km": length_km, "slope_m_per_m": slope_m_per_m}
        x, notices = validate(TC, inputs, errors=ERRORS)
        tc = TC.constant("c") * convert(x.real("length_km"), "km", "m") ** ...
        out = check_outputs(TC, {"tc_min": tc}, errors=ERRORS)
        return TcResult(out.real("tc_min"), notices, TC.formula_version)

``ERRORS`` is the project's :class:`Errors`: it turns a refusal into the project's
own exception with its registry code and ``details.reason`` (ERR-1); a project
converts each :class:`Notice` into its own and keeps its code and details. The
project's tests generate the cases of CMP-6.5 from the spec::

    register_profiles()  # in tests/conftest.py (CMP-6.9)

    @pytest.mark.formula
    @pytest.mark.parametrize("case", range_cases(TC) + type_cases(TC))
    def test_kirpich_limits(case: Case) -> None:
        run_case(TC, kirpich, case, ERRORS)

    @pytest.mark.formula
    @given(inputs=strategies(TC))
    def test_kirpich_properties(inputs: dict[str, object]) -> None:
        assert_property_contract(TC, kirpich, inputs, ERRORS)
        assert_properties(TC, kirpich, inputs, ERRORS)

    @pytest.mark.formula
    @pytest.mark.parametrize("case", load_cases(CASES, "kirpich"))
    def test_kirpich_reference_cases(case: ReferenceCase) -> None:
        assert_case(TC, kirpich, case, ERRORS)

    def test_kirpich_keeps_the_standard() -> None:
        assert_limits(TC, kirpich, ERRORS)
        assert spec_problems(TC, kirpich, root=ROOT) == []

``to_toml(card(TC))`` is ``formulas/kirpich.toml`` and ``formulas_markdown`` gives
``docs/FORMULAS.md`` (CMP-2.6); a check compares them with the committed files.

A function under test returns its outputs as a mapping, as attributes named like
the spec's outputs, as a tuple in their order, or as the value of a single output;
its notices are the ``notices`` of the result (key or attribute) and the warnings
it emits that carry ``code`` and ``details``.
"""

from __future__ import annotations

import ast
import copy
import csv
import hashlib
import inspect
import io
import itertools
import json
import math
import os
import re
import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal, NoReturn, Protocol, cast, overload
from typing import get_args as _choices_of

import numpy as np
from numpy.typing import ArrayLike, NDArray

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet
    from hypothesis.strategies import SearchStrategy

__all__ = [
    "CARD_FORMAT",
    "DEFAULT_ERRORS",
    "TRAPS",
    "UNITS",
    "Bounds",
    "Case",
    "Conservation",
    "Constant",
    "Constraint",
    "Coverage",
    "Delegated",
    "Errors",
    "FormulaCalculationError",
    "FormulaError",
    "FormulaErrors",
    "FormulaSpec",
    "FormulaValidationError",
    "IntervalFunction",
    "FrozenOracle",
    "Limit",
    "Notice",
    "Oracle",
    "Output",
    "Properties",
    "Range",
    "ReferenceCase",
    "Rounding",
    "Scaling",
    "Source",
    "SpecError",
    "Symmetry",
    "Table",
    "TierBSpec",
    "Tolerance",
    "Trap",
    "Unit",
    "Values",
    "Variable",
    "assert_case",
    "assert_coverage",
    "assert_interval_properties",
    "assert_limits",
    "assert_monotonic",
    "assert_properties",
    "assert_property_contract",
    "assert_within",
    "card",
    "case_tolerance",
    "check_outputs",
    "convert",
    "docstring_problems",
    "formulas_markdown",
    "load_cases",
    "range_cases",
    "read_frozen_oracle",
    "register_profiles",
    "rounding_tolerance",
    "run_case",
    "spec_problems",
    "strategies",
    "to_toml",
    "tolerance_problems",
    "type_cases",
    "validate",
]

CARD_FORMAT: Final = "nogat-formula-card/1"
"""The format of a card, the title of Nogat ``schemas/formula/card-1.schema.json``."""

Access = Literal["open", "author-provided"]
Kind = Literal["real", "real_array", "integer", "choice"]
ConstraintClass = Literal["physical", "precondition", "applicability"]
Status = Literal["referenced", "oracle only", "unreferenced"]
Level = Literal["info", "warning"]
Expect = Literal["ok", "ok+notice", "validation_error"]
OracleKind = Literal["exact", "algorithm", "established", "frozen"]
CaseStatus = Literal["single_source", "second_source", "discrepancy"]
UnitsProperty = Literal["homogeneous", "unit_specific"]
type Value = float | int | str | NDArray[np.float64]

_NAME = re.compile(r"[a-z][a-z0-9_]*")
_FUNCTION = re.compile(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)+", re.ASCII)
_TOML_BARE = re.compile(r"[A-Za-z0-9_-]+")
_DIGIT = re.compile(r"\d+")
_ORACLE_KEYS = ("tool", "packages", "platform", "date", "script")
_MAX_CORNERS = 16
_NUDGE = 2.0**-10
_SCALE = 2.0
_HUGE = 2**53


# --- errors and notices -------------------------------------------------------


class SpecError(ValueError):
    """A declaration that breaks a rule of the standard, raised where it is made."""


class FormulaError(Exception):
    """An error of a formula with a registry ``code``, a ``message`` and ``details``.

    Parameters
    ----------
    message : str
        English message naming the variable, its value and its range, or the cause.
    details : Mapping[str, object]
        JSON-compatible details with ``reason`` (ERR-1) and ``formula``.
    """

    code: str = "internal_error"

    def __init__(self, message: str, details: Mapping[str, object]) -> None:
        super().__init__(message)
        self.message = message
        self.details = dict(details)


class FormulaValidationError(FormulaError, ValueError):
    """Refused input, code ``validation_error`` (CMP-3.1, CMP-3.2, CMP-4.2)."""

    code = "validation_error"


class FormulaCalculationError(FormulaError, ArithmeticError):
    """A result a formula must not return, code ``calculation_error`` (CMP-3.4)."""

    code = "calculation_error"


class Errors(Protocol):
    """How a project turns a refusal or a failed result into its own exception.

    Each method returns, not raises, an exception that carries the registry code
    its name says and the ``details`` it receives, which hold ``reason`` (ERR-1).
    """

    def validation(self, message: str, details: dict[str, object]) -> Exception:
        """Return the project's exception with code ``validation_error``."""
        ...

    def calculation(self, message: str, details: dict[str, object]) -> Exception:
        """Return the project's exception with code ``calculation_error``."""
        ...


class FormulaErrors:
    """The module's own :class:`Errors`, for code that has no exceptions of its own."""

    def validation(self, message: str, details: dict[str, object]) -> Exception:
        """Return a :class:`FormulaValidationError`."""
        return FormulaValidationError(message, details)

    def calculation(self, message: str, details: dict[str, object]) -> Exception:
        """Return a :class:`FormulaCalculationError`."""
        return FormulaCalculationError(message, details)


DEFAULT_ERRORS: Final[Errors] = FormulaErrors()
"""The default of every ``errors`` argument: the module's own exceptions."""


@dataclass(frozen=True)
class Notice:
    """A notice on a result (CMP-3.3, CMP-5.1); the project converts it into its own.

    Attributes
    ----------
    level : {"info", "warning"}
        Level of the AGI notice.
    code : str
        ``outside_applicability`` or ``unreferenced_formula``.
    message : str
        English message naming the variable or constraint, the value, the range
        and the range's source.
    details : Mapping[str, object]
        JSON-compatible: ``formula`` and ``variable`` or ``constraint`` with the
        value, range and source.
    """

    level: Level
    code: str
    message: str
    details: Mapping[str, object]

    def as_dict(self) -> dict[str, object]:
        """Return the notice as a JSON-compatible dict: an AGI notice with details."""
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "details": dict(self.details),
        }


# --- declarations ---------------------------------------------------------------


def _check_name(name: object, where: str) -> None:
    if not isinstance(name, str) or not _NAME.fullmatch(name):
        raise SpecError(f"{where}: {name!r} is not a snake_case ASCII name")


def _check_texts(where: str, **texts: object) -> None:
    """Raise SpecError for a text a card needs that is not a non-blank string."""
    for name, text in texts.items():
        if not isinstance(text, str) or not text.strip():
            raise SpecError(f"{where}: {name} needs a non-blank text")


def _num(value: float) -> str:
    """Return a number as messages and intervals show it, exactly."""
    if isinstance(value, int):
        return str(value)
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return repr(float(value))


def _json_number(value: float) -> float | str:
    """Return a number for JSON details: a non-finite one becomes its text."""
    if isinstance(value, float) and not math.isfinite(value):
        return _num(value)
    return value


@dataclass(frozen=True, kw_only=True)
class Source:
    """A source of a formula, constant, range or case (CMP-2.4).

    Attributes
    ----------
    citation : str
        Authors, year, title, edition.
    locator : str
        Equation, table or page.
    url : str
        Where an auditor opens it, empty when there is none.
    access : {"open", "author-provided"}
        ``author-provided`` is a source the auditor cannot open.
    """

    citation: str
    locator: str = ""
    url: str = ""
    access: Access = "open"

    def __post_init__(self) -> None:
        """Check the declaration."""
        if not self.citation.strip():
            raise SpecError("a source needs its citation (CMP-2.4)")
        if self.access not in _choices_of(Access):
            raise SpecError(f"source access {self.access!r} is not open or provided")

    def text(self) -> str:
        """Return the citation with its locator, as notices and documents name it."""
        return f"{self.citation}, {self.locator}" if self.locator else self.citation


@dataclass(frozen=True, kw_only=True)
class Range:
    """An interval of values with its source (CMP-1.3 to CMP-1.5).

    Attributes
    ----------
    low, high : float
        Ends; ``-inf`` and ``inf`` are unbounded.
    low_inclusive, high_inclusive : bool
        Whether a finite end belongs to the range.
    source : Source or None
        Where the range comes from; required for applicability and typical ranges.
    test_low, test_high : float or None
        The finite end a test uses for an unbounded one (CMP-1.3).
    test_reason : str
        Why the test bounds are what they are.
    """

    low: float = -math.inf
    high: float = math.inf
    low_inclusive: bool = True
    high_inclusive: bool = True
    source: Source | None = None
    test_low: float | None = None
    test_high: float | None = None
    test_reason: str = ""

    def __post_init__(self) -> None:
        """Check the declaration."""
        for name in ("low", "high", "test_low", "test_high"):
            value = getattr(self, name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise SpecError(f"range {name} {value!r} is not a number")
            object.__setattr__(self, name, float(value))
        low, high = self.low, self.high
        if math.isnan(low) or math.isnan(high) or low == math.inf or high == -math.inf:
            raise SpecError(f"range ends {low!r} and {high!r} make no interval")
        inclusive = self.low_inclusive and self.high_inclusive
        if low > high or (low == high and not inclusive):
            raise SpecError(f"range {self.interval()} is empty")
        for side, end, other, test in (
            ("low", low, high, self.test_low),
            ("high", high, low, self.test_high),
        ):
            if test is None:
                continue
            if math.isfinite(end):
                raise SpecError(
                    f"test_{side} given for the finite end {end!r} (CMP-1.3)"
                )
            if not math.isfinite(test) or not self.contains(test) or test == other:
                raise SpecError(
                    f"test_{side} {test!r} is not a finite inner value of "
                    f"{self.interval()} (CMP-1.3)"
                )
        if (
            self.test_low is not None
            and self.test_high is not None
            and self.test_low >= self.test_high
        ):
            raise SpecError("test_low must lie below test_high (CMP-1.3)")
        tested = self.test_low is not None or self.test_high is not None
        if tested and not self.test_reason.strip():
            raise SpecError("a test bound needs its reason (CMP-1.3)")

    def contains(self, value: float) -> bool:
        """Return whether a value lies in the range; NaN never does."""
        if not self.low <= value <= self.high:
            return False
        if value == self.low and not self.low_inclusive:
            return False
        return not (value == self.high and not self.high_inclusive)

    def mask(self, values: NDArray[np.float64]) -> NDArray[np.bool_]:
        """Return, element by element, whether values lie in the range."""
        low = values >= self.low if self.low_inclusive else values > self.low
        high = values <= self.high if self.high_inclusive else values < self.high
        return low & high

    @property
    def lower(self) -> float:
        """The finite low end a test uses: ``low``, or ``test_low`` if unbounded."""
        if math.isfinite(self.low):
            return self.low
        if self.test_low is None:
            raise SpecError(f"range {self.interval()} has no test bound below")
        return self.test_low

    @property
    def upper(self) -> float:
        """The finite high end a test uses: ``high``, or ``test_high`` if unbounded."""
        if math.isfinite(self.high):
            return self.high
        if self.test_high is None:
            raise SpecError(f"range {self.interval()} has no test bound above")
        return self.test_high

    def interval(self) -> str:
        """Return the range in interval notation, ``(0.0, inf)``."""
        left = "[" if self.low_inclusive and math.isfinite(self.low) else "("
        right = "]" if self.high_inclusive and math.isfinite(self.high) else ")"
        return f"{left}{_num(self.low)}, {_num(self.high)}{right}"

    def details(self) -> dict[str, object]:
        """Return the range as JSON-compatible details; ``None`` is unbounded."""
        low, high = math.isfinite(self.low), math.isfinite(self.high)
        return {
            "low": self.low if low else None,
            "high": self.high if high else None,
            "low_inclusive": self.low_inclusive and low,
            "high_inclusive": self.high_inclusive and high,
        }


@dataclass(frozen=True, kw_only=True)
class Variable:
    """An input of a formula (CMP-2.1): its unit, type and three ranges.

    Attributes
    ----------
    name : str
        Public name with its unit (``area_km2``, CMP-4.3); the function's argument.
    symbol : str
        LaTeX symbol of the equation.
    unit : str
        Unit as documents show it (``km2``, ``m/m``, ``-``).
    kind : {"real", "real_array", "integer", "choice"}
        Type of the value (CMP-4.2).
    description : str
        One line on what it is.
    physical : Range or None
        Values that can exist, with test bounds for unbounded ends (CMP-1.3).
    applicability : Range or "unstated"
        Values the formula was derived for, with source (CMP-1.4).
    typical : Range or None
        Values met in the ecosystem's use, closed, with source (CMP-1.5).
    gaps_allowed : bool
        An array may hold NaN as a gap.
    dims : int
        Number of dimensions of an array.
    min_length, max_length : int, int or None
        Bounds of an array's first dimension; a minimum sample size of a method
        is a precondition instead (CMP-1.6).
    choices : tuple of str
        The values of a ``choice``.
    """

    name: str
    symbol: str
    unit: str
    kind: Kind = "real"
    description: str = ""
    physical: Range | None = None
    applicability: Range | Literal["unstated"] | None = None
    typical: Range | None = None
    gaps_allowed: bool = False
    dims: int = 1
    min_length: int = 1
    max_length: int | None = None
    choices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Check the declaration."""
        where = f"variable {self.name!r}"
        _check_name(self.name, where)
        _check_texts(where, unit=self.unit)
        if self.kind not in _choices_of(Kind):
            raise SpecError(f"{where}: kind {self.kind!r} is unknown")
        if self.kind == "choice":
            names = self.choices
            if not names or len(set(names)) != len(names):
                raise SpecError(f"{where}: a choice needs distinct choices")
            if not all(isinstance(c, str) and c.strip() for c in names):
                raise SpecError(f"{where}: choices are non-blank strings")
            if self.physical or self.applicability or self.typical:
                raise SpecError(f"{where}: a choice has no ranges")
            return
        if self.choices:
            raise SpecError(f"{where}: only a choice has choices")
        physical = self.physical
        if physical is None:
            raise SpecError(f"{where}: no physical range (CMP-1.3)")
        for side, end, test in (
            ("low", physical.low, physical.test_low),
            ("high", physical.high, physical.test_high),
        ):
            if not math.isfinite(end) and test is None:
                raise SpecError(
                    f"{where}: the unbounded {side} end of the physical range needs a "
                    "test bound with its reason (CMP-1.3)"
                )
        applicability = self.applicability
        if isinstance(applicability, Range):
            if applicability.source is None:
                raise SpecError(f"{where}: an applicability range needs its source")
        elif applicability != "unstated":
            raise SpecError(
                f"{where}: give an applicability range with its source or "
                "'unstated' (CMP-1.4)"
            )
        typical = self.typical
        if typical is None or typical.source is None:
            raise SpecError(f"{where}: a typical range with its source (CMP-1.5)")
        if not (typical.low_inclusive and typical.high_inclusive) or not (
            math.isfinite(typical.low) and math.isfinite(typical.high)
        ):
            raise SpecError(f"{where}: a typical range is closed and finite")
        if not (physical.contains(typical.low) and physical.contains(typical.high)):
            raise SpecError(
                f"{where}: typical range {typical.interval()} is not within the "
                f"physical range {physical.interval()} (CMP-1.5)"
            )
        if self.kind == "integer":
            for rng in (physical, applicability, typical):
                if not isinstance(rng, Range):
                    continue
                ends: tuple[float | None, ...] = (
                    rng.low,
                    rng.high,
                    rng.test_low,
                    rng.test_high,
                )
                for bound in ends:
                    if (
                        bound is not None
                        and math.isfinite(bound)
                        and bound != int(bound)
                    ):
                        raise SpecError(f"{where}: an integer's range ends are whole")
        if self.kind == "real_array":
            if self.dims < 1 or self.min_length < 0:
                raise SpecError(f"{where}: an array has dims >= 1 and min_length >= 0")
            if self.max_length is not None and self.max_length < max(
                self.min_length, 1
            ):
                raise SpecError(f"{where}: max_length below min_length")
        elif self.gaps_allowed:
            raise SpecError(f"{where}: only an array has gaps (CMP-3.4)")


@dataclass(frozen=True, kw_only=True)
class Constraint:
    """A relation between inputs (CMP-1.6), checked by ``validate``.

    Attributes
    ----------
    name : str
        Snake_case name, distinct from the variables'; notices and errors name it.
    cls : {"physical", "precondition", "applicability"}
        Outcome when it fails: ``outside_physical_range``, ``precondition_failed``
        or the notice ``outside_applicability`` (CMP §3).
    check : callable
        Predicate over the checked inputs, true when the constraint holds.
    text : str
        The condition as a reader writes it, ``2 K X <= dt``.
    source : Source
        Where the condition comes from.
    satisfied, violated : Mapping[str, object]
        Inputs, over the spec's typical point, where it holds and where it fails
        just beyond its bound; the generated tests use them (CMP-6.5).
    boundary : Mapping[str, object] or None
        Inputs exactly at its bound, where it holds when ``boundary_holds``.
    """

    name: str
    cls: ConstraintClass
    check: Callable[[Values], object]
    text: str
    source: Source
    satisfied: Mapping[str, object]
    violated: Mapping[str, object]
    boundary: Mapping[str, object] | None = None
    boundary_holds: bool = True

    def __post_init__(self) -> None:
        """Check the declaration."""
        where = f"constraint {self.name!r}"
        _check_name(self.name, where)
        if self.cls not in _choices_of(ConstraintClass):
            raise SpecError(f"{where}: class {self.cls!r} is unknown")
        if not self.text.strip():
            raise SpecError(f"{where}: needs its text")
        if not self.satisfied or not self.violated:
            raise SpecError(
                f"{where}: needs a satisfied and a violated point (CMP-6.5)"
            )


@dataclass(frozen=True, kw_only=True)
class Constant:
    """A named constant of a formula with its value and source (CMP-2.1, CMP-2.2).

    A rational constant is a :class:`fractions.Fraction`, kept exact.
    """

    name: str
    value: float | Fraction
    unit: str
    source: Source
    symbol: str = ""

    def __post_init__(self) -> None:
        """Check the declaration."""
        _check_name(self.name, "constant")
        _check_texts(f"constant {self.name!r}", unit=self.unit)
        if isinstance(self.value, bool) or not isinstance(self.value, float | Fraction):
            raise SpecError(f"constant {self.name!r}: a float or a Fraction")
        if not math.isfinite(self.value):
            raise SpecError(f"constant {self.name!r} is not finite")


@dataclass(frozen=True, kw_only=True)
class Output:
    """An output of a formula with its physical range (CMP-2.1, CMP-3.4).

    Attributes
    ----------
    name : str
        Name with its unit, like an input's.
    unit : str
        Unit as documents show it.
    physical : Range or None
        Values the output can take; required but for a choice.
    kind : {"real", "real_array", "integer", "choice"}
        Type of the value.
    boundary_tolerance : float or None
        Absolute distance beyond a bound set to the bound (CMP-3.4); ``None`` is
        four units in the last place of the bound.
    gaps_allowed : bool
        An array may hold NaN.
    gaps_from : str or None
        The array input whose gaps it may copy, element by element.
    choices : tuple of str
        The values of a ``choice``.
    """

    name: str
    unit: str
    physical: Range | None = None
    kind: Kind = "real"
    description: str = ""
    symbol: str = ""
    boundary_tolerance: float | None = None
    gaps_allowed: bool = False
    gaps_from: str | None = None
    choices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Check the declaration."""
        where = f"output {self.name!r}"
        _check_name(self.name, where)
        _check_texts(
            where, unit=self.unit, **{f"choice {c!r}": c for c in self.choices}
        )
        if self.kind not in _choices_of(Kind):
            raise SpecError(f"{where}: kind {self.kind!r} is unknown")
        if (self.kind == "choice") != bool(self.choices):
            raise SpecError(f"{where}: a choice and only a choice has choices")
        if (self.kind == "choice") == (self.physical is not None):
            raise SpecError(f"{where}: every output but a choice has a physical range")
        tolerance = self.boundary_tolerance
        if tolerance is not None and not (math.isfinite(tolerance) and tolerance >= 0):
            raise SpecError(f"{where}: boundary_tolerance is finite and >= 0")
        if self.kind != "real_array" and (self.gaps_allowed or self.gaps_from):
            raise SpecError(f"{where}: only an array has gaps (CMP-3.4)")
        if self.gaps_from is not None and not self.gaps_allowed:
            raise SpecError(f"{where}: gaps_from needs gaps_allowed")


def _tolerance_problem(abs_: float | None, rel: float | None, reason: str) -> str:
    if abs_ is None and rel is None:
        return "a tolerance needs abs or rel"
    for name, value in (("abs", abs_), ("rel", rel)):
        if value is not None and not (math.isfinite(value) and value >= 0):
            return f"tolerance {name} {value!r} is not finite and >= 0"
    if not isinstance(reason, str) or not reason.strip():
        return "a tolerance needs its reason (CMP-6.8)"
    return ""


@dataclass(frozen=True, kw_only=True)
class Tolerance:
    """An absolute and/or relative tolerance with its reason (CMP-6.8)."""

    abs: float | None = None
    rel: float | None = None
    reason: str

    def __post_init__(self) -> None:
        """Check the declaration."""
        problem = _tolerance_problem(self.abs, self.rel, self.reason)
        if problem:
            raise SpecError(problem)


@dataclass(frozen=True, kw_only=True)
class Scaling:
    """A scaling the output follows when inputs change units (CMP-6.5, homogeneous).

    Multiplying each input by ``2 ** inputs[name]`` multiplies each output by
    ``2 ** outputs[name]``; an absent name has exponent 0.
    """

    name: str
    inputs: Mapping[str, float]
    outputs: Mapping[str, float]
    tolerance: Tolerance

    def __post_init__(self) -> None:
        """Check the declaration."""
        _check_texts("scaling", name=self.name)


@dataclass(frozen=True, kw_only=True)
class Limit:
    """A limit case of the formula (CMP-6.5).

    Either ``expected`` outputs at ``inputs`` (over the typical point) within
    ``tolerance``, or ``check``, called with ``evaluate(**inputs)`` that returns the
    checked outputs, which asserts what it needs.
    """

    name: str
    text: str
    inputs: Mapping[str, object] = field(default_factory=dict)
    expected: Mapping[str, object] = field(default_factory=dict)
    tolerance: Tolerance | None = None
    check: Callable[[Callable[..., Values]], None] | None = None
    source: Source | None = None

    def __post_init__(self) -> None:
        """Check the declaration."""
        _check_texts("limit", name=self.name, text=self.text)
        if (self.check is not None) == bool(self.expected):
            raise SpecError(f"limit {self.name!r}: expected outputs or a check, one")
        if self.expected and self.tolerance is None:
            raise SpecError(f"limit {self.name!r}: expected outputs need a tolerance")


@dataclass(frozen=True, kw_only=True)
class Conservation:
    """A conservation law: ``residual(inputs, outputs)`` is zero within tolerance."""

    name: str
    text: str
    residual: Callable[[Values, Values], float]
    tolerance: Tolerance

    def __post_init__(self) -> None:
        """Check the declaration."""
        _check_texts("conservation law", name=self.name, text=self.text)


@dataclass(frozen=True, kw_only=True)
class Symmetry:
    """A symmetry: the formula at ``inputs(x)`` gives ``outputs(f(x))``."""

    name: str
    text: str
    inputs: Callable[[Values], Mapping[str, object]]
    outputs: Callable[[Values], Mapping[str, object]]
    tolerance: Tolerance

    def __post_init__(self) -> None:
        """Check the declaration."""
        _check_texts("symmetry", name=self.name, text=self.text)


@dataclass(frozen=True, kw_only=True)
class Properties:
    """Properties that hold for a formula, tested by the module (CMP-6.5).

    Attributes
    ----------
    units : {"homogeneous", "unit_specific"}
        A homogeneous formula declares its scalings; a unit-specific one has a
        reference case in each unit system its sources publish.
    monotonic : Mapping[str, int]
        Sign, ``1`` or ``-1``, of the change of the first output with each input
        the source states.
    scalings, limits, conservation, symmetries : tuple
        The other properties of CMP-6.5.
    """

    units: UnitsProperty
    monotonic: Mapping[str, Literal[1, -1]] = field(default_factory=dict)
    scalings: tuple[Scaling, ...] = ()
    limits: tuple[Limit, ...] = ()
    conservation: tuple[Conservation, ...] = ()
    symmetries: tuple[Symmetry, ...] = ()

    def __post_init__(self) -> None:
        """Check the declaration."""
        if self.units not in _choices_of(UnitsProperty):
            raise SpecError(f"properties: units {self.units!r} is unknown")
        if (self.units == "homogeneous") != bool(self.scalings):
            raise SpecError(
                "properties: a homogeneous formula and only it has scalings"
            )
        for name, sign in self.monotonic.items():
            if sign not in (1, -1):
                raise SpecError(f"properties: monotonic {name!r} is 1 or -1")

    @property
    def declared(self) -> bool:
        """Whether any property beyond the contract of CMP-3.4 is declared."""
        return bool(
            self.monotonic
            or self.scalings
            or self.limits
            or self.conservation
            or self.symmetries
        )


@dataclass(frozen=True, kw_only=True)
class Trap:
    """A numerical trap of a family of formulas (CMP-6.6)."""

    name: str
    description: str
    test: str


_TRAP = {
    trap.name: trap
    for trap in (
        Trap(
            name="difference_denominator",
            description="A denominator that is a difference of inputs.",
            test="A case where the difference vanishes: the error of CMP §3 or a "
            "finite value within tolerance.",
        ),
        Trap(
            name="singular_at_bound",
            description="log, sqrt or a negative or fractional power of an input at a "
            "bound of its range.",
            test="Cases at the bound and just beyond it.",
        ),
        Trap(
            name="exp_overflow",
            description="exp of a scaled input at its test bound.",
            test="A case at the test bound: a finite value or the error of a "
            "precondition.",
        ),
        Trap(
            name="unbounded_iteration",
            description="An iteration without a bounded count (root finding, fit).",
            test="A case that does not converge: calculation_error after the "
            "bounded count, named by a precondition where one can foresee it.",
        ),
        Trap(
            name="stability_bound",
            description="The stability bound of a numerical scheme (a Courant "
            "number, Muskingum's 2KX <= dt <= 2K(1-X)).",
            test="Cases at the bound and just beyond it, expecting the outcome of "
            "its constraint's class.",
        ),
        Trap(
            name="gap_propagation",
            description="A gap (NaN) that propagates through a sum, a convolution "
            "or a moving window.",
            test="A series with a gap: non-finite values only where the spec allows "
            "them.",
        ),
        Trap(
            name="many_small_terms",
            description="A sum of many small terms that loses precision.",
            test="A long series against math.fsum or an exact Fraction sum.",
        ),
        Trap(
            name="moment_cancellation",
            description="Cancellation in moments computed as E[x^2] - E[x]^2.",
            test="A series with a large mean and a small variance against an exact "
            "or two-pass oracle.",
        ),
        Trap(
            name="class_limit",
            description="A value exactly at a limit of a published class or table.",
            test="Cases at each limit and just beyond it, against the source's "
            "inclusive or exclusive limit.",
        ),
    )
}

TRAPS: Final[Mapping[str, tuple[Trap, ...]]] = MappingProxyType(
    {
        family: tuple(_TRAP[name] for name in names)
        for family, names in {
            "empirical": (
                "difference_denominator",
                "singular_at_bound",
                "exp_overflow",
            ),
            "scheme": (
                "difference_denominator",
                "stability_bound",
                "unbounded_iteration",
                "gap_propagation",
                "many_small_terms",
            ),
            "statistic": (
                "singular_at_bound",
                "exp_overflow",
                "unbounded_iteration",
                "gap_propagation",
                "many_small_terms",
                "moment_cancellation",
            ),
            "index": (
                "difference_denominator",
                "singular_at_bound",
                "gap_propagation",
                "many_small_terms",
            ),
            "classification": ("class_limit", "gap_propagation"),
        }.items()
    }
)
"""The checklist of traps per family of Tier A formulas (CMP-6.6): empirical
equations, numerical schemes and models, statistical procedures, indices and
classifications by published thresholds or tables (CMP-1.1)."""


@dataclass(frozen=True, kw_only=True)
class Oracle:
    """An independent way to the output (CMP-1.7) and where its test is.

    Attributes
    ----------
    kind : {"exact", "algorithm", "established", "frozen"}
        Exact solution or different algorithm (CMP-6.2), established implementation
        (CMP-6.3), frozen oracle (CMP-6.4).
    description : str
        What it is, with its version for an implementation.
    test : str
        The test, script or CSV file.
    conventions : tuple of str
        The conventions of both sides of the comparison (CMP-6.3).
    """

    kind: OracleKind
    description: str
    test: str
    conventions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Check the declaration."""
        if self.kind not in _choices_of(OracleKind):
            raise SpecError(f"oracle kind {self.kind!r} is unknown")
        _check_texts("oracle", description=self.description, test=self.test)
        _check_texts("oracle", **{f"convention {c!r}": c for c in self.conventions})


@dataclass(frozen=True, kw_only=True)
class Table:
    """A published table kept as a data file (CMP-2.5).

    ``comparison`` is the record of the two independent transcriptions, kept in
    ``tests/oracles/``.
    """

    path: str
    sha256: str
    source: Source
    comparison: str

    def __post_init__(self) -> None:
        """Check the declaration."""
        _check_texts("table", path=self.path, comparison=self.comparison)
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise SpecError(f"table {self.path}: sha256 is 64 lower-case hex digits")


@dataclass(frozen=True, kw_only=True)
class Delegated:
    """A computation delegated to a third-party library (CMP-1.2)."""

    name: str
    library: str
    versions: str
    smoke_case: str
    test: str

    def __post_init__(self) -> None:
        """Check the declaration."""
        _check_texts(
            "delegated computation",
            name=self.name,
            library=self.library,
            versions=self.versions,
            smoke_case=self.smoke_case,
            test=self.test,
        )


@dataclass(frozen=True, kw_only=True)
class TierBSpec:
    """A Tier B formula: one row of a module's table (CMP-2.2).

    Attributes
    ----------
    name : str
        Snake_case name.
    function : str
        Import path of the function.
    definition : str
        What it computes.
    convention : str
        The convention it implements (CMP-2.3).
    source : Source
        The definition's source.
    constants : tuple of Constant
        Exact or rational constants it uses.
    """

    name: str
    function: str
    definition: str
    convention: str
    source: Source
    constants: tuple[Constant, ...] = ()

    def __post_init__(self) -> None:
        """Check the declaration."""
        _check_name(self.name, "Tier B formula")
        _check_texts(
            f"Tier B formula {self.name!r}",
            function=self.function,
            definition=self.definition,
            convention=self.convention,
        )


@dataclass(frozen=True, kw_only=True)
class FormulaSpec:
    """The one declaration of a Tier A formula (CMP-2.1).

    Attributes
    ----------
    name : str
        Snake_case id: ``formulas/<name>.toml``, the docstring names it (CMP-2.7).
    title : str
        One line.
    function : str
        Import path of the function.
    family : str
        A key of :data:`TRAPS`.
    equation, latex : str
        The equation in plain text and in LaTeX.
    variables, outputs : tuple
        Inputs in the order of the function's arguments, and outputs.
    sources : tuple of Source
        Sources of the formula.
    properties : Properties
        Properties that hold (CMP-6.5).
    validation : str
        What the source reports of the formula's agreement with observations, or
        ``none``.
    formula_version : int
        Incremented with every change of results (CMP-2.8).
    status : {"referenced", "oracle only", "unreferenced"}
        Evidence of CMP-2.6; ``unreferenced`` adds a notice to every result.
    constraints, constants : tuple
        Constraints and preconditions (CMP-1.6), named constants.
    conventions, assumptions : tuple of str
        Conventions of CMP-2.3 and the formula's assumptions.
    notices : tuple of str
        Codes of notices the function emits besides those of ``validate``.
    traps : Mapping[str, str]
        The traps of its family that apply, each with its test (CMP-6.6).
    no_traps_reason : str
        Why none applies, when ``traps`` is empty.
    reference_cases : tuple of str
        Reference-case files, relative to the project's root (CMP-6.1).
    oracles, tables : tuple
        Oracles (CMP-6.2 to CMP-6.4) and published tables (CMP-2.5).
    base : Mapping[str, object]
        Inputs of the typical point the generated tests start from, where the
        middle of each typical range is not one (constraints between inputs).
    """

    name: str
    title: str
    function: str
    family: str
    equation: str
    latex: str
    variables: tuple[Variable, ...]
    outputs: tuple[Output, ...]
    sources: tuple[Source, ...]
    properties: Properties
    validation: str
    formula_version: int
    status: Status
    constraints: tuple[Constraint, ...] = ()
    constants: tuple[Constant, ...] = ()
    conventions: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    notices: tuple[str, ...] = ()
    traps: Mapping[str, str] = field(default_factory=dict)
    no_traps_reason: str = ""
    reference_cases: tuple[str, ...] = ()
    oracles: tuple[Oracle, ...] = ()
    tables: tuple[Table, ...] = ()
    base: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Check the declaration against CMP-2.1 and CMP-6.6."""
        where = f"spec {self.name!r}"
        _check_name(self.name, where)
        for text, what in (
            (self.title, "title"),
            (self.function, "function"),
            (self.equation, "equation"),
            (self.latex, "latex"),
            (self.validation, "validation (or 'none')"),
        ):
            if not text.strip():
                raise SpecError(f"{where}: needs its {what} (CMP-2.1)")
        if "\n" in self.title:
            raise SpecError(f"{where}: the title is one line")
        if not _FUNCTION.fullmatch(self.function):
            raise SpecError(f"{where}: function {self.function!r} is no dotted path")
        for what, texts in (
            ("convention", self.conventions),
            ("assumption", self.assumptions),
            ("reference case", self.reference_cases),
        ):
            _check_texts(where, **{f"{what} {i}": t for i, t in enumerate(texts)})
        if self.family not in TRAPS:
            raise SpecError(
                f"{where}: family {self.family!r} is not one of {list(TRAPS)}"
            )
        if not self.variables or not self.outputs or not self.sources:
            raise SpecError(f"{where}: needs variables, outputs and sources")
        inputs = [v.name for v in self.variables]
        names = (
            inputs + [o.name for o in self.outputs] + [c.name for c in self.constraints]
        )
        if len(set(names)) != len(names):
            raise SpecError(f"{where}: variable, output and constraint names repeat")
        constants = [c.name for c in self.constants]
        if len(set(constants)) != len(constants):
            raise SpecError(f"{where}: constant names repeat")
        if isinstance(self.formula_version, bool) or not (
            isinstance(self.formula_version, int) and self.formula_version >= 1
        ):
            raise SpecError(f"{where}: formula_version is an integer >= 1 (CMP-2.8)")
        if self.status not in _choices_of(Status):
            raise SpecError(f"{where}: status {self.status!r} is unknown (CMP-2.6)")
        family = {trap.name for trap in TRAPS[self.family]}
        for trap, test in self.traps.items():
            if trap not in family:
                raise SpecError(
                    f"{where}: trap {trap!r} is not of family {self.family}"
                )
            if not test.strip():
                raise SpecError(f"{where}: trap {trap!r} needs its test (CMP-6.6)")
        if not self.traps and not self.no_traps_reason.strip():
            raise SpecError(f"{where}: name the traps that apply or why none does")
        arrays = {v.name for v in self.variables if v.kind == "real_array"}
        for output in self.outputs:
            if output.gaps_from is not None and output.gaps_from not in arrays:
                raise SpecError(f"{where}: gaps_from {output.gaps_from!r} is no array")
        numbers = {v.name for v in self.variables if v.kind != "choice"}
        properties = self.properties
        if not set(properties.monotonic) <= numbers:
            raise SpecError(f"{where}: monotonic names a variable it does not have")
        for scaling in properties.scalings:
            if not set(scaling.inputs) <= numbers or not set(scaling.outputs) <= {
                o.name for o in self.outputs
            }:
                raise SpecError(f"{where}: scaling {scaling.name!r} names unknowns")
        points = [self.base, *(limit.inputs for limit in properties.limits)]
        for constraint in self.constraints:
            points += [constraint.satisfied, constraint.violated]
            if constraint.boundary is not None:
                points.append(constraint.boundary)
        for point in points:
            if not set(point) <= set(inputs):
                raise SpecError(
                    f"{where}: a point names unknown inputs {sorted(point)}"
                )
        for code in self.notices:
            _check_name(code, f"{where} notice")

    def variable(self, name: str) -> Variable:
        """Return the input of that name."""
        for variable in self.variables:
            if variable.name == name:
                return variable
        raise KeyError(f"{self.name} has no input {name!r}")

    def output(self, name: str) -> Output:
        """Return the output of that name."""
        for output in self.outputs:
            if output.name == name:
                return output
        raise KeyError(f"{self.name} has no output {name!r}")

    def constant(self, name: str) -> float:
        """Return the value of a named constant as a float."""
        for constant in self.constants:
            if constant.name == name:
                return float(constant.value)
        raise KeyError(f"{self.name} has no constant {name!r}")

    def notice_codes(self) -> tuple[str, ...]:
        """Return the codes of every notice its results can carry."""
        codes: list[str] = []
        applicable = any(isinstance(v.applicability, Range) for v in self.variables)
        if applicable or any(c.cls == "applicability" for c in self.constraints):
            codes.append("outside_applicability")
        if self.status == "unreferenced":
            codes.append("unreferenced_formula")
        return tuple(codes) + tuple(c for c in self.notices if c not in codes)

    def base_point(self) -> dict[str, object]:
        """Return the typical point: ``base`` over the middle of each typical range."""
        point: dict[str, object] = {}
        for variable in self.variables:
            if variable.name in self.base:
                point[variable.name] = copy.deepcopy(self.base[variable.name])
            else:
                point[variable.name] = _typical_value(variable)
        return point


class Values(dict[str, Value]):
    """Checked inputs or outputs by name, with typed accessors."""

    def real(self, name: str) -> float:
        """Return a real scalar."""
        value = self[name]
        if isinstance(value, float):
            return value
        raise TypeError(f"{name} is a {type(value).__name__}, not a real scalar")

    def integer(self, name: str) -> int:
        """Return an integer."""
        value = self[name]
        if isinstance(value, int):
            return value
        raise TypeError(f"{name} is a {type(value).__name__}, not an integer")

    def choice(self, name: str) -> str:
        """Return a choice."""
        value = self[name]
        if isinstance(value, str):
            return value
        raise TypeError(f"{name} is a {type(value).__name__}, not a choice")

    def array(self, name: str) -> NDArray[np.float64]:
        """Return a float64 array."""
        value = self[name]
        if isinstance(value, np.ndarray):
            return value
        raise TypeError(f"{name} is a {type(value).__name__}, not an array")


# --- run-time checks (CMP §3, CMP §4) --------------------------------------------


def _type_name(value: object) -> str:
    kind = type(value)
    if kind.__module__ in ("builtins", "numpy"):
        return kind.__qualname__
    return f"{kind.__module__}.{kind.__qualname__}"


def _is_integer(value: object) -> bool:
    """Return whether a value is a CMP-4.2 integer: no bool and no timedelta64."""
    return isinstance(value, int | np.integer) and not isinstance(
        value, bool | np.bool_ | np.timedelta64
    )


def _as_real(value: object) -> float | None:
    """Return a CMP-4.2 real scalar as a float, ``None`` for anything else."""
    if _is_integer(value):
        try:
            return float(cast("int", value))
        except OverflowError:
            return math.inf if cast("int", value) > 0 else -math.inf
    if isinstance(value, float | np.floating):
        return float(value)
    return None


def _physical(holder: Variable | Output) -> Range:
    if holder.physical is None:  # a choice; validated specs never get here
        raise SpecError(f"{holder.name} has no physical range")
    return holder.physical


def _refusal(
    spec: FormulaSpec, errors: Errors, reason: str, message: str, **details: object
) -> Exception:
    return errors.validation(
        f"{spec.name}: {message}", {"reason": reason, "formula": spec.name, **details}
    )


def _same_names(
    spec: FormulaSpec, what: str, names: Sequence[str], given: Mapping[str, object]
) -> None:
    missing = [n for n in names if n not in given]
    unknown = sorted(set(given) - set(names))
    if missing or unknown:
        raise TypeError(
            f"{spec.name}: {what} missing {missing}, unknown {unknown}; the spec "
            f"declares {list(names)}"
        )


def _check_scalar(
    spec: FormulaSpec, var: Variable, number: float, errors: Errors, given: object
) -> None:
    physical = _physical(var)
    shown = given if isinstance(given, int) else number
    if isinstance(number, float) and not math.isfinite(number):
        raise _refusal(
            spec,
            errors,
            "outside_physical_range",
            f"{var.name} = {_num(shown)} is not a finite float64 number (CMP-3.1)",
            variable=var.name,
            value=_json_number(shown),
            unit=var.unit,
            range=physical.details(),
        )
    if not physical.contains(number):
        raise _refusal(
            spec,
            errors,
            "outside_physical_range",
            f"{var.name} = {_num(shown)} {var.unit} is outside its physical range "
            f"{physical.interval()}",
            variable=var.name,
            value=shown,
            unit=var.unit,
            range=physical.details(),
        )


def _bad_element(items: Sequence[object]) -> tuple[object] | None:
    """Return the first element of nested lists that is no real scalar, boxed."""
    for item in items:
        if isinstance(item, list | tuple):
            found = _bad_element(item)
            if found is not None:
                return found
        elif _as_real(item) is None:
            return (item,)
    return None


def _index(flat: int, shape: tuple[int, ...]) -> list[int]:
    return [int(i) for i in np.unravel_index(flat, shape)]


def _lengths(var: Variable) -> str:
    if var.max_length is None:
        return f"at least {var.min_length}"
    return f"{var.min_length} to {var.max_length}"


def _clean_array(
    spec: FormulaSpec, var: Variable, value: object, errors: Errors
) -> NDArray[np.float64]:
    def refuse(reason: str, message: str, **details: object) -> Exception:
        return _refusal(
            spec, errors, reason, f"{var.name} {message}", variable=var.name, **details
        )

    if isinstance(value, np.ma.MaskedArray):
        raise refuse(
            "invalid_type", "is a masked array; a gap is NaN", type="MaskedArray"
        )
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in "fiu":
            raise refuse(
                "invalid_type", f"has dtype {value.dtype}", type=str(value.dtype)
            )
        array = value.astype(np.float64)
    elif isinstance(value, list | tuple):
        bad = _bad_element(value)
        if bad is not None:
            raise refuse(
                "invalid_type",
                f"holds {_type_name(bad[0])} {bad[0]!r}, not a real number",
                type=_type_name(bad[0]),
            )
        try:
            array = np.array(value, dtype=np.float64)
        except OverflowError:
            raise refuse(
                "outside_physical_range", "holds a number beyond float64"
            ) from None
        except ValueError:
            raise refuse("invalid_shape", "is a ragged nested list") from None
    else:
        raise refuse(
            "invalid_type",
            f"must be an array of real numbers, not {_type_name(value)}",
            type=_type_name(value),
        )
    shape = tuple(int(n) for n in array.shape)
    length = shape[0] if shape else 0
    too_long = var.max_length is not None and length > var.max_length
    if array.ndim != var.dims or length < var.min_length or too_long:
        raise refuse(
            "invalid_shape",
            f"has shape {shape}; the spec needs {var.dims} dimension(s) and "
            f"{_lengths(var)} values along the first",
            shape=list(shape),
            dims=var.dims,
            min_length=var.min_length,
            max_length=var.max_length,
        )
    physical = _physical(var)
    gaps = np.isnan(array)
    bad_values = np.isinf(array) if var.gaps_allowed else ~np.isfinite(array)
    if bad_values.any():
        flat = int(np.argmax(bad_values))
        number = float(array.flat[flat])
        raise refuse(
            "outside_physical_range",
            f"{_index(flat, shape)} = {_num(number)} is not a finite number"
            + ("" if var.gaps_allowed else " and the spec allows no gaps")
            + " (CMP-3.1)",
            value=_num(number),
            index=_index(flat, shape),
            unit=var.unit,
            range=physical.details(),
        )
    outside = ~(physical.mask(array) | gaps)
    if outside.any():
        flat = int(np.argmax(outside))
        number = float(array.flat[flat])
        raise refuse(
            "outside_physical_range",
            f"{_index(flat, shape)} = {_num(number)} {var.unit} is outside its "
            f"physical range {physical.interval()}",
            value=number,
            index=_index(flat, shape),
            unit=var.unit,
            range=physical.details(),
        )
    return array


def _clean(spec: FormulaSpec, var: Variable, value: object, errors: Errors) -> Value:
    if var.kind == "real":
        number = _as_real(value)
        if number is None:
            raise _refusal(
                spec,
                errors,
                "invalid_type",
                f"{var.name} must be a real number (int or float), not "
                f"{_type_name(value)}",
                variable=var.name,
                type=_type_name(value),
            )
        _check_scalar(spec, var, number, errors, value)
        return number
    if var.kind == "integer":
        if not _is_integer(value):
            raise _refusal(
                spec,
                errors,
                "invalid_type",
                f"{var.name} must be an integer, not {_type_name(value)}",
                variable=var.name,
                type=_type_name(value),
            )
        whole = int(cast("int", value))
        _check_scalar(spec, var, whole, errors, whole)
        return whole
    if var.kind == "choice":
        if not isinstance(value, str):
            raise _refusal(
                spec,
                errors,
                "invalid_type",
                f"{var.name} must be a string, not {_type_name(value)}",
                variable=var.name,
                type=_type_name(value),
            )
        text = str(value)
        if text not in var.choices:
            raise _refusal(
                spec,
                errors,
                "invalid_choice",
                f"{var.name} = {text!r} is not one of {list(var.choices)}",
                variable=var.name,
                value=text,
                choices=list(var.choices),
            )
        return text
    return _clean_array(spec, var, value, errors)


def _clean_all(
    spec: FormulaSpec, inputs: Mapping[str, object], errors: Errors
) -> Values:
    _same_names(spec, "inputs", [v.name for v in spec.variables], inputs)
    values = Values()
    for variable in spec.variables:
        values[variable.name] = _clean(spec, variable, inputs[variable.name], errors)
    return values


def _holds(constraint: Constraint, values: Values) -> bool:
    return bool(constraint.check(values))


def _constraint_details(spec: FormulaSpec, constraint: Constraint) -> dict[str, object]:
    return {
        "formula": spec.name,
        "constraint": constraint.name,
        "class": constraint.cls,
        "text": constraint.text,
        "source": constraint.source.text(),
    }


def _variable_notice(spec: FormulaSpec, var: Variable, value: Value) -> Notice | None:
    rng = var.applicability
    if not isinstance(rng, Range) or isinstance(value, str):
        return None
    source = rng.source.text() if rng.source is not None else ""
    details: dict[str, object] = {
        "formula": spec.name,
        "variable": var.name,
        "unit": var.unit,
        "range": rng.details(),
        "source": source,
    }
    if isinstance(value, np.ndarray):
        outside = ~(rng.mask(value) | np.isnan(value))
        count = int(outside.sum())
        if count == 0:
            return None
        flat = int(np.argmax(outside))
        number = float(value.flat[flat])
        where = _index(flat, value.shape)
        message = (
            f"{spec.name}: {count} of {value.size} values of {var.name} lie outside "
            f"its applicability range {rng.interval()} {var.unit} ({source}), the "
            f"first {_num(number)} at {where}"
        )
        details |= {"value": number, "count": count, "index": where}
        return Notice("warning", "outside_applicability", message, details)
    if rng.contains(value):
        return None
    message = (
        f"{spec.name}: {var.name} = {_num(value)} {var.unit} is outside its "
        f"applicability range {rng.interval()} ({source})"
    )
    return Notice(
        "warning", "outside_applicability", message, details | {"value": value}
    )


def validate(
    spec: FormulaSpec, inputs: Mapping[str, object], *, errors: Errors = DEFAULT_ERRORS
) -> tuple[Values, list[Notice]]:
    """Check the inputs of a formula before it computes (CMP-3.1 to CMP-3.3, CMP-4.2).

    Real scalars become ``float``, integers ``int`` and arrays new ``float64``
    arrays. Refused, in this order: a wrong type, shape or length
    (``invalid_type``, ``invalid_shape``) or choice (``invalid_choice``); a value
    that is not finite or lies outside its physical range, element by element,
    NaN allowed where the spec allows gaps (``outside_physical_range``); a
    violated physical constraint (``outside_physical_range``); a failed
    precondition (``precondition_failed``). The first problem in the spec's order
    is raised.

    Parameters
    ----------
    spec : FormulaSpec
        The formula's spec.
    inputs : Mapping[str, object]
        Every input of the spec by name, as the function received it.
    errors : Errors
        Turns a refusal into the project's exception.

    Returns
    -------
    tuple of Values and list of Notice
        The checked inputs; the notices ``outside_applicability``, one per
        variable outside its applicability range and per violated applicability
        constraint in the spec's order, then ``unreferenced_formula`` (CMP-5.1).

    Raises
    ------
    Exception
        ``errors.validation(...)`` with ``details.reason``.
    TypeError
        If the inputs' names are not the spec's: a defect of the formula module.
    """
    values = _clean_all(spec, inputs, errors)
    for cls, reason in (
        ("physical", "outside_physical_range"),
        ("precondition", "precondition_failed"),
    ):
        for constraint in spec.constraints:
            if constraint.cls == cls and not _holds(constraint, values):
                kind = (
                    "precondition" if cls == "precondition" else "physical constraint"
                )
                raise errors.validation(
                    f"{spec.name}: {kind} {constraint.name} failed: {constraint.text}",
                    {"reason": reason, **_constraint_details(spec, constraint)},
                )
    notices = [
        notice
        for variable in spec.variables
        if (notice := _variable_notice(spec, variable, values[variable.name]))
    ]
    for constraint in spec.constraints:
        if constraint.cls == "applicability" and not _holds(constraint, values):
            notices.append(
                Notice(
                    "warning",
                    "outside_applicability",
                    f"{spec.name}: {constraint.text} does not hold, outside the "
                    f"applicability of the formula ({constraint.source.text()})",
                    _constraint_details(spec, constraint),
                )
            )
    if spec.status == "unreferenced":
        notices.append(
            Notice(
                "info",
                "unreferenced_formula",
                f"{spec.name}: {spec.title} has no reference case and no oracle "
                "(CMP-5.1)",
                {"formula": spec.name, "formula_version": spec.formula_version},
            )
        )
    return values, notices


def _calc_error(
    spec: FormulaSpec, errors: Errors, reason: str, message: str, **details: object
) -> Exception:
    return errors.calculation(
        f"{spec.name}: {message}", {"reason": reason, "formula": spec.name, **details}
    )


def _bound_tolerance(output: Output, bound: float) -> float:
    if output.boundary_tolerance is not None:
        return output.boundary_tolerance
    return 4 * math.ulp(bound)


def _snap_ends(output: Output) -> tuple[float, float]:
    rng = _physical(output)
    low = rng.low if rng.low_inclusive else math.nextafter(rng.low, math.inf)
    high = rng.high if rng.high_inclusive else math.nextafter(rng.high, -math.inf)
    return low, high


def _check_real_output(
    spec: FormulaSpec, output: Output, value: object, errors: Errors
) -> float:
    number = _as_real(value)
    if number is None:
        raise TypeError(f"{spec.name}: output {output.name} is a {_type_name(value)}")
    if not math.isfinite(number):
        raise _calc_error(
            spec,
            errors,
            "non_finite_output",
            f"{output.name} = {_num(number)} is not finite (CMP-3.4)",
            output=output.name,
            value=_num(number),
        )
    rng = _physical(output)
    if rng.contains(number):
        return number
    snap_low, snap_high = _snap_ends(output)
    if number <= rng.low and rng.low - number <= _bound_tolerance(output, rng.low):
        return snap_low
    if number >= rng.high and number - rng.high <= _bound_tolerance(output, rng.high):
        return snap_high
    raise _calc_error(
        spec,
        errors,
        "output_outside_physical_range",
        f"{output.name} = {_num(number)} {output.unit} is outside its physical range "
        f"{rng.interval()} beyond its boundary tolerance (CMP-3.4)",
        output=output.name,
        value=number,
        range=rng.details(),
    )


def _check_array_output(
    spec: FormulaSpec,
    output: Output,
    value: object,
    inputs: Mapping[str, object] | None,
    errors: Errors,
) -> NDArray[np.float64]:
    if not isinstance(value, np.ndarray | list | tuple):
        raise TypeError(f"{spec.name}: output {output.name} is a {_type_name(value)}")
    array = np.array(value, dtype=np.float64)
    shape = tuple(int(n) for n in array.shape)
    gaps = np.isnan(array)
    wrong = np.isinf(array) if output.gaps_allowed else ~np.isfinite(array)
    if output.gaps_from is not None:
        if inputs is None:
            raise TypeError(f"{spec.name}: check_outputs needs the inputs for gaps")
        source = np.asarray(inputs[output.gaps_from], dtype=np.float64)
        if source.shape != array.shape:
            raise TypeError(
                f"{spec.name}: output {output.name} has shape {shape}, its gaps' "
                f"input {output.gaps_from} {source.shape}"
            )
        wrong = wrong | (gaps & ~np.isnan(source))
    if wrong.any():
        flat = int(np.argmax(wrong))
        number = float(array.flat[flat])
        raise _calc_error(
            spec,
            errors,
            "non_finite_output",
            f"{output.name}{_index(flat, shape)} = {_num(number)} is not finite where "
            "the spec allows no gap (CMP-3.4)",
            output=output.name,
            value=_num(number),
            index=_index(flat, shape),
        )
    rng = _physical(output)
    outside = ~(rng.mask(array) | gaps)
    if not outside.any():
        return array
    snap_low, snap_high = _snap_ends(output)
    low_tol = _bound_tolerance(output, rng.low) if math.isfinite(rng.low) else 0.0
    high_tol = _bound_tolerance(output, rng.high) if math.isfinite(rng.high) else 0.0
    near_low = outside & (array <= rng.low) & (rng.low - array <= low_tol)
    near_high = outside & (array >= rng.high) & (array - rng.high <= high_tol)
    far = outside & ~near_low & ~near_high
    if far.any():
        flat = int(np.argmax(far))
        number = float(array.flat[flat])
        raise _calc_error(
            spec,
            errors,
            "output_outside_physical_range",
            f"{output.name}{_index(flat, shape)} = {_num(number)} {output.unit} is "
            f"outside its physical range {rng.interval()} beyond its boundary "
            "tolerance (CMP-3.4)",
            output=output.name,
            value=number,
            index=_index(flat, shape),
            range=rng.details(),
        )
    array = np.where(near_low, snap_low, array)
    return cast("NDArray[np.float64]", np.where(near_high, snap_high, array))


def check_outputs(
    spec: FormulaSpec,
    outputs: Mapping[str, object],
    *,
    inputs: Mapping[str, object] | None = None,
    errors: Errors = DEFAULT_ERRORS,
) -> Values:
    """Check the outputs of a formula before it returns them (CMP-3.4).

    A non-finite scalar, a non-finite element where the output allows no gap or
    its ``gaps_from`` input was finite, and a value beyond its physical range by
    more than its boundary tolerance raise ``calculation_error``; a value within
    the tolerance is set to the bound (to the nearest inner value of an excluded
    one).

    Parameters
    ----------
    spec : FormulaSpec
        The formula's spec.
    outputs : Mapping[str, object]
        Every output of the spec by name.
    inputs : Mapping[str, object] or None
        The checked inputs; needed for an output with ``gaps_from``.
    errors : Errors
        Turns a failed result into the project's exception.

    Returns
    -------
    Values
        The outputs as ``float``, ``int``, ``str`` or new ``float64`` arrays.

    Raises
    ------
    Exception
        ``errors.calculation(...)`` with ``details.reason``
        ``non_finite_output`` or ``output_outside_physical_range``.
    TypeError
        If an output has a wrong name or type: a defect of the formula module.
    """
    _same_names(spec, "outputs", [o.name for o in spec.outputs], outputs)
    checked = Values()
    for output in spec.outputs:
        value = outputs[output.name]
        if output.kind == "real":
            checked[output.name] = _check_real_output(spec, output, value, errors)
        elif output.kind == "real_array":
            checked[output.name] = _check_array_output(
                spec, output, value, inputs, errors
            )
        elif output.kind == "integer":
            if not _is_integer(value):
                raise TypeError(f"{spec.name}: output {output.name} is no integer")
            whole = int(cast("int", value))
            if not _physical(output).contains(whole):
                raise _calc_error(
                    spec,
                    errors,
                    "output_outside_physical_range",
                    f"{output.name} = {whole} is outside its physical range "
                    f"{_physical(output).interval()} (CMP-3.4)",
                    output=output.name,
                    value=whole,
                    range=_physical(output).details(),
                )
            checked[output.name] = whole
        else:
            if not isinstance(value, str):
                raise TypeError(f"{spec.name}: output {output.name} is no string")
            if value not in output.choices:
                raise _calc_error(
                    spec,
                    errors,
                    "output_outside_physical_range",
                    f"{output.name} = {value!r} is not one of {list(output.choices)}",
                    output=output.name,
                    value=str(value),
                )
            checked[output.name] = str(value)
    return checked


# --- generated tests (CMP-6.5) ---------------------------------------------------


@dataclass(frozen=True)
class Case:
    """A generated test case: inputs and the outcome CMP §3 expects for them.

    Attributes
    ----------
    id : str
        ``<variable or constraint>-<point>``, the pytest id.
    inputs : Mapping[str, object]
        Every input of the spec.
    expect : {"ok", "ok+notice", "validation_error"}
        The expected outcome.
    reason : str or None
        ``details.reason`` of an expected ``validation_error``.
    notices : tuple of str
        Variables and constraints whose ``outside_applicability`` notice the
        result carries, in this order.
    """

    id: str
    inputs: Mapping[str, object]
    expect: Expect
    reason: str | None = None
    notices: tuple[str, ...] = ()


def _typical_value(var: Variable) -> object:
    if var.kind == "choice":
        return var.choices[0]
    typical = cast("Range", var.typical)
    if var.kind == "integer":
        return (math.ceil(typical.low) + math.floor(typical.high)) // 2
    middle = (typical.low + typical.high) / 2
    if var.kind == "real":
        return middle
    length = max(var.min_length, min(10, var.max_length or 10))
    column = np.linspace(typical.low, typical.high, length)
    shape = (length, *(2,) * (var.dims - 1))
    return np.broadcast_to(
        column.reshape((length,) + (1,) * (var.dims - 1)), shape
    ).copy()


def _subject(details: Mapping[str, object]) -> str:
    return str(details.get("variable") or details.get("constraint") or "")


def _expected(
    spec: FormulaSpec, inputs: Mapping[str, object]
) -> tuple[Expect, str | None, tuple[str, ...]]:
    """Return the outcome ``validate`` gives the inputs, as a case expects it."""
    try:
        _, notices = validate(spec, inputs)
    except FormulaValidationError as exc:
        return "validation_error", str(exc.details.get("reason")), ()
    names = tuple(
        _subject(n.details) for n in notices if n.code == "outside_applicability"
    )
    return ("ok+notice" if names else "ok"), None, names


def _case(spec: FormulaSpec, case_id: str, inputs: dict[str, object]) -> Case:
    expect, reason, notices = _expected(spec, inputs)
    return Case(case_id, inputs, expect, reason, notices)


def _bound_points(
    prefix: str, rng: Range, integer: bool, scale: float
) -> list[tuple[str, float]]:
    """Return the points at and beyond each end of a range (CMP-6.5)."""
    points: list[tuple[str, float]] = []
    for side, end, inclusive, outward, test in (
        ("low", rng.low, rng.low_inclusive, -1.0, rng.test_low),
        ("high", rng.high, rng.high_inclusive, 1.0, rng.test_high),
    ):
        if not math.isfinite(end):
            if test is not None:
                points.append((f"{prefix}_{side}_test_bound", test))
            continue
        delta = 0.01 * abs(end) if end != 0 else 0.01 * scale
        points.append((f"{prefix}_{side}", end))
        if integer:
            if not inclusive:
                points.append((f"{prefix}_{side}_inside", end - outward))
            points.append((f"{prefix}_{side}_beyond", end + outward))
            points.append(
                (
                    f"{prefix}_{side}_beyond_1pct",
                    end + outward * max(1, math.ceil(delta)),
                )
            )
            continue
        if not inclusive:
            points.append(
                (f"{prefix}_{side}_inside", math.nextafter(end, -outward * math.inf))
            )
        points.append(
            (f"{prefix}_{side}_beyond", math.nextafter(end, outward * math.inf))
        )
        points.append((f"{prefix}_{side}_beyond_1pct", end + outward * delta))
    return points


def _variable_points(var: Variable) -> list[tuple[str, float]]:
    typical = cast("Range", var.typical)
    integer = var.kind == "integer"
    if integer:
        whole_low, whole_high = math.ceil(typical.low), math.floor(typical.high)
        low, high = float(whole_low), float(whole_high)
        middle = float((whole_low + whole_high) // 2)
    else:
        low, high = typical.low, typical.high
        middle = (low + high) / 2
    points: list[tuple[str, float]] = [
        ("typical_low", low),
        ("typical_middle", middle),
        ("typical_high", high),
    ]
    scale = typical.high - typical.low or 1.0
    if isinstance(var.applicability, Range):
        points += _bound_points("applicability", var.applicability, integer, scale)
    points += _bound_points("physical", _physical(var), integer, scale)
    return points


def _placed(var: Variable, base: object, number: float) -> object:
    """Return the value of a range case: the number, or the base array holding it."""
    if var.kind == "integer":
        return int(number)
    if var.kind == "real":
        return float(number)
    array = np.array(base, dtype=np.float64)
    array.flat[0] = number
    return array


def _check_points(
    spec: FormulaSpec, constraint: Constraint, base: dict[str, object]
) -> None:
    """Raise SpecError if the predicate disagrees with the constraint's points."""
    for label, point, wanted in (
        ("satisfied", constraint.satisfied, True),
        ("violated", constraint.violated, False),
        ("boundary", constraint.boundary, constraint.boundary_holds),
    ):
        if point is None:
            continue
        try:
            values = _clean_all(
                spec, {**base, **copy.deepcopy(dict(point))}, DEFAULT_ERRORS
            )
        except FormulaValidationError as exc:
            raise SpecError(
                f"{spec.name}: the {label} point of {constraint.name} is refused: {exc}"
            ) from exc
        if _holds(constraint, values) != wanted:
            raise SpecError(
                f"{spec.name}: {constraint.name} ({constraint.text}) gives "
                f"{not wanted} at its {label} point {dict(point)}; the spec says "
                f"{wanted} (CMP-6.5)"
            )


def _range_cases(spec: FormulaSpec) -> list[Case]:
    base = spec.base_point()
    cases: list[Case] = []
    for var in spec.variables:
        seen: set[str] = set()
        if var.kind == "choice":
            other = "unknown"
            while other in var.choices:
                other += "_"
            for choice in (*var.choices, other):
                label = "choice_unknown" if choice == other else f"choice_{choice}"
                inputs = {**copy.deepcopy(base), var.name: choice}
                cases.append(_case(spec, f"{var.name}-{label}", inputs))
            continue
        for label, number in _variable_points(var):
            if repr(number) in seen:
                continue
            seen.add(repr(number))
            value = _placed(var, base[var.name], number)
            inputs = {**copy.deepcopy(base), var.name: value}
            cases.append(_case(spec, f"{var.name}-{label}", inputs))
    for constraint in spec.constraints:
        _check_points(spec, constraint, base)
        for label, point in (
            ("satisfied", constraint.satisfied),
            ("boundary", constraint.boundary),
            ("violated", constraint.violated),
        ):
            if point is not None:
                inputs = {**copy.deepcopy(base), **copy.deepcopy(dict(point))}
                cases.append(_case(spec, f"{constraint.name}-{label}", inputs))
    return cases


def _integer_in(var: Variable) -> int | None:
    """Return a whole number within the typical or else the physical range."""
    for rng in (var.typical, var.physical):
        if rng is None:
            continue
        low, high = math.ceil(rng.lower), math.floor(rng.upper)
        for candidate in (round((rng.lower + rng.upper) / 2), low, high):
            if low <= candidate <= high and rng.contains(candidate):
                return int(candidate)
    return None


Kinds = list[tuple[str, object, str | None]]


def _real_kinds(var: Variable, base: object) -> Kinds:
    number = float(cast("float", base))
    kinds: Kinds = [
        ("float", number, None),
        ("numpy_float64", np.float64(number), None),
    ]
    if abs(number) <= float(np.finfo(np.float32).max):
        kinds.append(("numpy_float32", np.float32(number), None))
    whole = _integer_in(var)
    if whole is not None:
        kinds.append(("int", whole, None))
        if abs(whole) < 2**63:
            kinds.append(("numpy_int64", np.int64(whole), None))
        if abs(whole) < 2**31:
            kinds.append(("numpy_int32", np.int32(whole), None))
    refused = "invalid_type"
    return kinds + [
        ("bool_true", True, refused),
        ("bool_false", False, refused),
        ("numpy_bool", np.bool_(True), refused),
        ("none", None, refused),
        ("str", repr(number), refused),
        ("decimal", Decimal(repr(number)), refused),
        ("complex", complex(number, 0.0), refused),
        ("numpy_complex", np.complex128(number), refused),
        ("numpy_timedelta", np.timedelta64(1, "s"), refused),
        ("nan", math.nan, "outside_physical_range"),
        ("inf", math.inf, "outside_physical_range"),
        ("minus_inf", -math.inf, "outside_physical_range"),
    ]


def _integer_kinds(base: object) -> Kinds:
    whole = int(cast("int", base))
    refused = "invalid_type"
    kinds: Kinds = [("int", whole, None)]
    if abs(whole) < 2**63:
        kinds.append(("numpy_int64", np.int64(whole), None))
    if abs(whole) < 2**31:
        kinds.append(("numpy_int32", np.int32(whole), None))
    return kinds + [
        ("float", float(whole), refused),
        ("bool_true", True, refused),
        ("numpy_bool", np.bool_(True), refused),
        ("none", None, refused),
        ("str", str(whole), refused),
        ("decimal", Decimal(whole), refused),
        ("complex", complex(whole, 0), refused),
        ("numpy_timedelta", np.timedelta64(1, "s"), refused),
        ("nan", math.nan, refused),
    ]


def _choice_kinds(base: object) -> Kinds:
    text = str(base)
    refused = "invalid_type"
    return [
        ("str", text, None),
        ("numpy_str", np.str_(text), None),
        ("bytes", text.encode(), refused),
        ("none", None, refused),
        ("int", 1, refused),
        ("bool_true", True, refused),
    ]


def _array_kinds(var: Variable, base: object) -> Kinds:
    array = np.array(base, dtype=np.float64)
    refused = "invalid_type"
    kinds: Kinds = [
        ("ndarray_float64", array.copy(), None),
        ("ndarray_float32", array.astype(np.float32), None),
        ("ndarray_int64", np.round(array).astype(np.int64), None),
        ("list", array.tolist(), None),
        ("tuple", tuple(array.tolist()), None),
        ("ndarray_bool", array > array.mean(), refused),
        ("ndarray_complex", array.astype(np.complex128), refused),
        ("ndarray_object", array.astype(object), refused),
        ("ndarray_str", array.astype(str), refused),
        ("masked_array", np.ma.masked_array(array.copy()), refused),
        ("scalar", float(array.flat[0]), refused),
        ("none", None, refused),
        ("wrong_ndim", array[np.newaxis, ...].copy(), "invalid_shape"),
    ]
    if var.dims == 1:
        rest = array.tolist()[1:]
        kinds += [
            ("list_with_bool", [True, *rest], refused),
            ("list_with_none", [None, *rest], refused),
        ]
    shape = array.shape[1:]
    if var.min_length > 0:
        kinds.append(("empty", np.empty((0, *shape)), "invalid_shape"))
    if var.min_length > 1:
        kinds.append(("too_short", array[: var.min_length - 1].copy(), "invalid_shape"))
    if var.max_length is not None:
        longer = np.resize(array, (var.max_length + 1, *shape))
        kinds.append(("too_long", longer, "invalid_shape"))
    gap = array.copy()
    gap.flat[0] = math.nan
    kinds.append(
        ("nan_element", gap, None if var.gaps_allowed else "outside_physical_range")
    )
    infinite = array.copy()
    infinite.flat[0] = math.inf
    return [*kinds, ("inf_element", infinite, "outside_physical_range")]


def _type_cases(spec: FormulaSpec) -> list[Case]:
    base = spec.base_point()
    cases: list[Case] = []
    for var in spec.variables:
        if var.kind == "real":
            kinds = _real_kinds(var, base[var.name])
        elif var.kind == "integer":
            kinds = _integer_kinds(base[var.name])
        elif var.kind == "choice":
            kinds = _choice_kinds(base[var.name])
        else:
            kinds = _array_kinds(var, base[var.name])
        for label, value, refusal in kinds:
            inputs = {**copy.deepcopy(base), var.name: value}
            case_id = f"{var.name}-{label}"
            if refusal is None:
                cases.append(_case(spec, case_id, inputs))
            else:
                cases.append(Case(case_id, inputs, "validation_error", refusal))
    return cases


def range_cases(spec: FormulaSpec) -> list[ParameterSet]:
    """Return the range and constraint cases of CMP-6.5 as pytest params.

    Per input in the spec's order: three points of its typical range, then each
    finite end of its applicability and physical ranges exactly, just inside an
    excluded end, just beyond (``math.nextafter``, or 1 for an integer) and 1 % of
    the end's magnitude beyond (of the typical range's width for an end at 0), or
    the test bound of an unbounded end; an array holds the point in its first
    element, a choice is tried with every value and an unknown one. Per
    constraint: its satisfied, boundary and violated points. Other inputs keep
    their typical value. Each case expects what ``validate`` gives its inputs.

    Raises
    ------
    SpecError
        If a constraint's predicate disagrees with its declared points.
    """
    import pytest

    return [pytest.param(case, id=case.id) for case in _range_cases(spec)]


def type_cases(spec: FormulaSpec) -> list[ParameterSet]:
    """Return the cases of every kind of value of CMP-4.2 as pytest params.

    Accepted kinds (``int``, ``float``, NumPy integers and floats, lists and real
    arrays) expect what ``validate`` gives them; refused ones expect
    ``validation_error`` with ``invalid_type``, ``invalid_shape`` or, for a
    non-finite value, ``outside_physical_range``.
    """
    import pytest

    return [pytest.param(case, id=case.id) for case in _type_cases(spec)]


def _fail(message: str) -> NoReturn:
    raise AssertionError(message)


def _outputs_of(spec: FormulaSpec, result: object) -> dict[str, object]:
    """Return a function's outputs by name from its result."""
    names = [o.name for o in spec.outputs]
    if isinstance(result, Mapping):
        missing = [n for n in names if n not in result]
        if missing:
            _fail(f"{spec.name}: the result has no output {missing}")
        return {n: result[n] for n in names}
    if all(hasattr(result, n) for n in names):
        return {n: getattr(result, n) for n in names}
    if len(names) == 1:
        return {names[0]: result}
    if isinstance(result, tuple) and len(result) == len(names):
        return dict(zip(names, result, strict=True))
    _fail(f"{spec.name}: no outputs {names} in a {_type_name(result)}")


def _notice_entry(item: object) -> tuple[str, Mapping[str, object]] | None:
    """Return (code, details) of a notice-like object: a mapping, attributes or both."""
    if isinstance(item, Mapping):
        code, details = item.get("code"), item.get("details", {})
    else:
        code, details = getattr(item, "code", None), getattr(item, "details", {})
    if callable(code):
        code = code()
    if not isinstance(code, str) or not isinstance(details, Mapping):
        return None
    return code, details


def _notices_in(
    result: object, caught: Sequence[warnings.WarningMessage]
) -> list[tuple[str, Mapping[str, object]]]:
    if isinstance(result, Mapping):
        listed = result.get("notices", ())
    else:
        listed = getattr(result, "notices", ())
    found = [_notice_entry(n) for n in (listed or ())]
    found += [_notice_entry(w.message) for w in caught]
    return [entry for entry in found if entry is not None]


def _assert_outputs(
    spec: FormulaSpec, raw: Mapping[str, object], inputs: Values, label: str
) -> Values:
    """Assert the contract of CMP-3.4 on returned outputs, without tolerance."""
    checked = Values()
    for output in spec.outputs:
        value = raw[output.name]
        where = f"{label}: output {output.name}"
        if output.kind == "choice":
            if not isinstance(value, str) or value not in output.choices:
                _fail(f"{where} = {value!r} is not one of {list(output.choices)}")
            checked[output.name] = str(value)
            continue
        rng = _physical(output)
        if output.kind == "real":
            number = _as_real(value)
            if number is None:
                _fail(f"{where} is a {_type_name(value)}, not a real number")
            if not math.isfinite(number) or not rng.contains(number):
                _fail(
                    f"{where} = {_num(number)} is not finite or outside its physical "
                    f"range {rng.interval()} (CMP-3.4)"
                )
            checked[output.name] = number
            continue
        if output.kind == "integer":
            if not _is_integer(value):
                _fail(f"{where} is a {_type_name(value)}, not an integer")
            whole = int(cast("int", value))
            if not rng.contains(whole):
                _fail(f"{where} = {whole} is outside its physical range (CMP-3.4)")
            checked[output.name] = whole
            continue
        if not isinstance(value, np.ndarray | list | tuple):
            _fail(f"{where} is a {_type_name(value)}, not an array")
        try:
            array = np.array(value, dtype=np.float64)
        except (TypeError, ValueError):
            _fail(f"{where} is not an array of numbers")
        gaps = np.isnan(array)
        allowed = gaps if output.gaps_allowed else np.zeros_like(gaps)
        if output.gaps_from is not None:
            source = inputs.array(output.gaps_from)
            if source.shape != array.shape:
                _fail(f"{where} has shape {array.shape}, its input {source.shape}")
            allowed = allowed & np.isnan(source)
        bad = (~np.isfinite(array) & ~allowed) | (~rng.mask(array) & ~gaps)
        if bad.any():
            flat = int(np.argmax(bad))
            _fail(
                f"{where}{_index(flat, array.shape)} = {_num(float(array.flat[flat]))} "
                f"is a non-finite value the spec does not allow or lies outside "
                f"{rng.interval()} (CMP-3.4)"
            )
        checked[output.name] = array
    return checked


def _judge_raised(
    spec: FormulaSpec, case: Case, name: str, exc: Exception, errors: Errors
) -> None:
    validation_type = type(errors.validation("probe", {"reason": "probe"}))
    calculation_type = type(errors.calculation("probe", {"reason": "probe"}))
    code = getattr(exc, "code", None)
    details = getattr(exc, "details", None)
    reason = details.get("reason") if isinstance(details, Mapping) else None
    label = f"{spec.name} [{case.id}]: {name}"
    distinct = validation_type is not calculation_type
    if code == "calculation_error" or (distinct and isinstance(exc, calculation_type)):
        raise AssertionError(
            f"{label} raised calculation_error for accepted inputs ({exc}): a defect "
            "of the spec until a precondition or constraint prevents it (CMP-3.4)"
        ) from exc
    if case.expect != "validation_error":
        raise AssertionError(
            f"{label} raised {_type_name(exc)}: {exc}; expected a result"
        ) from exc
    if code != "validation_error" or not isinstance(exc, validation_type):
        raise AssertionError(
            f"{label} raised {_type_name(exc)} with code {code!r}; expected the "
            f"project's {validation_type.__name__} with code validation_error"
        ) from exc
    if reason != case.reason:
        raise AssertionError(
            f"{label} refused with reason {reason!r}; expected {case.reason!r}"
        ) from exc


def _check_call(
    spec: FormulaSpec, function: Callable[..., object], case: Case, errors: Errors
) -> Values | None:
    """Call the function on a case and assert its outcome; return its outputs."""
    name = getattr(function, "__qualname__", repr(function))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            result = function(**copy.deepcopy(dict(case.inputs)))
        except Exception as exc:
            _judge_raised(spec, case, name, exc, errors)
            return None
    label = f"{spec.name} [{case.id}]"
    if case.expect == "validation_error":
        _fail(
            f"{label}: {name} returned a result; expected validation_error with "
            f"reason {case.reason} (CMP §3, CMP-4.2)"
        )
    inputs = _clean_all(spec, case.inputs, DEFAULT_ERRORS)
    outputs = _assert_outputs(spec, _outputs_of(spec, result), inputs, label)
    found = _notices_in(result, caught)
    observed = tuple(
        _subject(details) for code, details in found if code == "outside_applicability"
    )
    if observed != case.notices:
        _fail(
            f"{label}: notices outside_applicability for {list(observed)}; expected "
            f"{list(case.notices)}, one per variable or constraint in the spec's "
            "order (CMP-3.3)"
        )
    unreferenced = any(code == "unreferenced_formula" for code, _ in found)
    if (spec.status == "unreferenced") != unreferenced:
        _fail(f"{label}: notice unreferenced_formula present: {unreferenced} (CMP-5.1)")
    return outputs


def run_case(
    spec: FormulaSpec,
    function: Callable[..., object],
    case: Case,
    errors: Errors = DEFAULT_ERRORS,
) -> None:
    """Call the function on a generated case and assert the expected outcome.

    The function must raise the project's exception (the class ``errors``
    returns) with the expected reason, or return outputs that are finite and
    inside their physical ranges (CMP-3.4) with the expected notices (CMP-3.3,
    CMP-5.1).

    Raises
    ------
    AssertionError
        Naming the case and what differs.
    """
    _check_call(spec, function, case, errors)


def _evaluate(
    spec: FormulaSpec,
    function: Callable[..., object],
    inputs: Mapping[str, object],
    errors: Errors,
    label: str = "property",
) -> Values | None:
    """Assert the contract at the inputs; return the outputs, None when refused."""
    expect, reason, notices = _expected(spec, inputs)
    return _check_call(
        spec, function, Case(label, inputs, expect, reason, notices), errors
    )


def assert_property_contract(
    spec: FormulaSpec,
    function: Callable[..., object],
    inputs: Mapping[str, object],
    errors: Errors = DEFAULT_ERRORS,
) -> None:
    """Assert, for drawn inputs, a finite result in range or the declared error.

    The property of CMP-6.5: the function raises the ``validation_error`` that
    the spec gives these inputs, with its reason, or returns outputs finite and
    inside their physical ranges with the notices the spec gives them; it never
    raises ``calculation_error`` (CMP-3.4).
    """
    _evaluate(spec, function, inputs, errors)


def _nudged(var: Variable, value: object) -> tuple[object, int] | None:
    """Return the input moved up a little (or down at the top), and the direction."""
    physical = _physical(var)
    if var.kind == "integer":
        whole = int(cast("int", value))
        for stepped, direction in ((whole + 1, 1), (whole - 1, -1)):
            if physical.contains(stepped):
                return stepped, direction
        return None
    width = cast("Range", var.typical).high - cast("Range", var.typical).low
    array = np.array(value, dtype=np.float64)
    step = np.maximum(np.abs(array), width) * _NUDGE
    for direction in (1, -1):
        moved = array + direction * step
        finite = moved[~np.isnan(moved)]
        if (
            physical.mask(finite).all()
            and (finite <= physical.upper).all()
            and (finite >= physical.lower).all()
        ):
            return (float(moved) if var.kind == "real" else moved), direction
    return None


def assert_monotonic(
    spec: FormulaSpec,
    function: Callable[..., object],
    inputs: Mapping[str, object],
    errors: Errors = DEFAULT_ERRORS,
) -> None:
    """Assert the declared monotonicity of the first output at drawn inputs.

    Each input of ``properties.monotonic`` is moved by 2**-10 of its magnitude
    (or of its typical range's width), up or, at the top, down; the first output
    must move in the declared direction, element by element, or stay within four
    units in the last place (CMP-6.5). A refused point is skipped.
    """
    if not spec.properties.monotonic:
        return
    first = spec.outputs[0].name
    here = _evaluate(spec, function, inputs, errors)
    if here is None:
        return
    for name, sign in spec.properties.monotonic.items():
        moved = _nudged(spec.variable(name), inputs[name])
        if moved is None:
            continue
        value, direction = moved
        there = _evaluate(spec, function, {**inputs, name: value}, errors, "monotonic")
        if there is None:
            continue
        before = np.asarray(here[first], dtype=np.float64)
        after = np.asarray(there[first], dtype=np.float64)
        change = (after - before) * (direction * sign)
        slack = 4 * np.spacing(np.maximum(np.abs(before), np.abs(after)))
        if (change < -slack).any():
            _fail(
                f"{spec.name}: {first} goes from {before} to {after} when {name} "
                f"moves from {inputs[name]} to {value}; the spec declares it "
                f"{'increasing' if sign > 0 else 'decreasing'} in {name} (CMP-6.5)"
            )


def assert_properties(
    spec: FormulaSpec,
    function: Callable[..., object],
    inputs: Mapping[str, object],
    errors: Errors = DEFAULT_ERRORS,
) -> None:
    """Assert every declared property at drawn inputs (CMP-6.5).

    Monotonicity, each scaling (inputs scaled by powers of 2, exact in binary),
    each conservation law and each symmetry, within their tolerances; a refused
    point, or a refused scaled or transformed one, is skipped.
    """
    assert_monotonic(spec, function, inputs, errors)
    here = _evaluate(spec, function, inputs, errors)
    if here is None:
        return
    cleaned = _clean_all(spec, inputs, DEFAULT_ERRORS)
    properties = spec.properties
    for scaling in properties.scalings:
        scaled: dict[str, object] = dict(inputs)
        for name, exponent in scaling.inputs.items():
            factor = _SCALE**exponent
            value = cleaned[name]
            scaled[name] = value * factor if not isinstance(value, str) else value
        there = _evaluate(spec, function, scaled, errors, f"scaling {scaling.name}")
        if there is None:
            continue
        for output in spec.outputs:
            if output.kind not in ("real", "real_array"):
                continue
            exponent = scaling.outputs.get(output.name, 0.0)
            expected = (
                np.asarray(here[output.name], dtype=np.float64) * _SCALE**exponent
            )
            _within(
                there[output.name],
                expected,
                scaling.tolerance,
                f"scaling {scaling.name}",
            )
    for law in properties.conservation:
        residual = law.residual(cleaned, here)
        _within(residual, 0.0, law.tolerance, f"conservation {law.name}")
    for symmetry in properties.symmetries:
        moved = dict(symmetry.inputs(cleaned))
        there = _evaluate(spec, function, moved, errors, f"symmetry {symmetry.name}")
        if there is None:
            continue
        for name, expected in symmetry.outputs(here).items():
            _within(
                there[name], expected, symmetry.tolerance, f"symmetry {symmetry.name}"
            )


def assert_limits(
    spec: FormulaSpec,
    function: Callable[..., object],
    errors: Errors = DEFAULT_ERRORS,
) -> None:
    """Assert every declared limit case (CMP-6.5), each over the typical point."""
    base = spec.base_point()

    def evaluate(limit: Limit) -> Callable[..., Values]:
        def run(**overrides: object) -> Values:
            outputs = _evaluate(
                spec, function, {**base, **overrides}, errors, f"limit {limit.name}"
            )
            if outputs is None:
                _fail(f"{spec.name}: the point of limit {limit.name} is refused")
            return outputs

        return run

    for limit in spec.properties.limits:
        run = evaluate(limit)
        if limit.check is not None:
            limit.check(run)
            continue
        outputs = run(**copy.deepcopy(dict(limit.inputs)))
        tolerance = cast("Tolerance", limit.tolerance)
        for name, expected in limit.expected.items():
            _within(outputs[name], expected, tolerance, f"limit {limit.name}")


def strategies(spec: FormulaSpec) -> SearchStrategy[dict[str, object]]:
    """Return a Hypothesis strategy of the spec's inputs (CMP-6.5).

    Each real input, and each element of an array, is drawn from ``one_of`` its
    typical, applicability (clipped to the physical range; left out where
    unstated) and physical ranges, test bounds for unbounded ends, and the ends of
    these ranges themselves, float64, without NaN or infinity; an integer
    likewise; a choice from its values. An array's length runs from its minimum
    to its maximum, at most 50 above the minimum.
    """
    import hypothesis.strategies as st

    drawn = {var.name: _variable_strategy(var) for var in spec.variables}
    return cast("SearchStrategy[dict[str, object]]", st.fixed_dictionaries(drawn))


def _strategy_ranges(var: Variable) -> list[tuple[float, float, bool, bool]]:
    """Return (low, high, exclude low, exclude high) of each range drawn from."""
    physical = _physical(var)
    typical = cast("Range", var.typical)
    phys = (
        physical.lower,
        physical.upper,
        math.isfinite(physical.low) and not physical.low_inclusive,
        math.isfinite(physical.high) and not physical.high_inclusive,
    )
    ranges = [(typical.low, typical.high, False, False)]
    rng = var.applicability
    if isinstance(rng, Range):
        if rng.low > phys[0] or (rng.low == phys[0] and not rng.low_inclusive):
            low = (rng.low, not rng.low_inclusive)
        else:
            low = (phys[0], phys[2])
        if rng.high < phys[1] or (rng.high == phys[1] and not rng.high_inclusive):
            high = (rng.high, not rng.high_inclusive)
        else:
            high = (phys[1], phys[3])
        if low[0] < high[0] or (low[0] == high[0] and not (low[1] or high[1])):
            ranges.append((low[0], high[0], low[1], high[1]))
    ranges.append(phys)
    return ranges


def _variable_strategy(var: Variable) -> SearchStrategy[object]:
    import hypothesis.strategies as st

    if var.kind == "choice":
        return st.sampled_from(var.choices)
    branches: list[SearchStrategy[object]] = []
    ends: set[float] = set()
    for low, high, exclude_low, exclude_high in _strategy_ranges(var):
        if var.kind == "integer":
            smallest = math.ceil(low) + (
                1 if exclude_low and low == math.ceil(low) else 0
            )
            largest = math.floor(high) - (
                1 if exclude_high and high == math.floor(high) else 0
            )
            if smallest <= largest:
                branches.append(st.integers(smallest, largest))
                ends |= {smallest, largest}
            continue
        branches.append(
            st.floats(
                min_value=low,
                max_value=high,
                exclude_min=exclude_low,
                exclude_max=exclude_high,
                allow_nan=False,
                allow_infinity=False,
                width=64,
            )
        )
        ends.add(math.nextafter(low, math.inf) if exclude_low else low)
        ends.add(math.nextafter(high, -math.inf) if exclude_high else high)
    element = st.one_of(*branches, st.sampled_from(sorted(ends)))
    if var.kind != "real_array":
        return element
    from hypothesis.extra.numpy import arrays

    longest = var.min_length + 50
    if var.max_length is not None:
        longest = min(longest, var.max_length)
    lengths = st.integers(var.min_length, longest)
    if var.dims == 1:
        shapes = lengths.map(lambda n: (n,))
    else:
        shapes = st.tuples(lengths, *(st.integers(1, 5) for _ in range(var.dims - 1)))
    return cast("SearchStrategy[object]", arrays(np.float64, shapes, elements=element))


def register_profiles(default: str = "gate") -> str:
    """Register the Hypothesis profiles of CMP-6.9 and load one.

    ``gate``: 50 examples, derandomized, no database, no deadline; ``ci``: 1,000
    examples with the database in ``.hypothesis/examples`` (cached between runs);
    ``nightly``: 20,000 examples with the same database. Call it once from
    ``tests/conftest.py``.

    Parameters
    ----------
    default : str
        Profile loaded when the environment variable ``HYPOTHESIS_PROFILE`` is
        not set.

    Returns
    -------
    str
        Name of the loaded profile.
    """
    from hypothesis import HealthCheck, settings
    from hypothesis.database import DirectoryBasedExampleDatabase

    settings.register_profile(
        "gate",
        max_examples=50,
        derandomize=True,
        database=None,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    database = DirectoryBasedExampleDatabase(".hypothesis/examples")
    for name, examples in (("ci", 1_000), ("nightly", 20_000)):
        settings.register_profile(
            name,
            max_examples=examples,
            database=database,
            deadline=None,
            print_blob=True,
        )
    name = os.environ.get("HYPOTHESIS_PROFILE", default)
    settings.load_profile(name)
    return name


# --- assertions with reasons (CMP-6.8) and reference cases (CMP-6.1) -------------


def assert_within(
    actual: ArrayLike,
    expected: ArrayLike,
    *,
    abs: float | None = None,
    rel: float | None = None,
    reason: str,
) -> None:
    """Assert ``|actual - expected| <= abs + rel * |expected|``, element by element.

    NaN matches NaN and an infinity the same infinity; shapes must agree.

    Parameters
    ----------
    actual, expected : array_like
        Values compared.
    abs, rel : float or None
        Tolerances; at least one is given.
    reason : str
        Why the tolerance is what it is (CMP-6.8); never empty.

    Raises
    ------
    ValueError
        If no tolerance or no reason is given.
    AssertionError
        Naming the worst element, the tolerance and the reason.
    """
    problem = _tolerance_problem(abs, rel, reason)
    if problem:
        raise ValueError(problem)
    got = np.asarray(actual, dtype=np.float64)
    want = np.asarray(expected, dtype=np.float64)
    if got.shape != want.shape:
        _fail(f"shape {got.shape} differs from the expected {want.shape} ({reason})")
    with np.errstate(invalid="ignore"):
        finite = np.isfinite(want)
        allowed = (abs or 0.0) + (rel or 0.0) * np.where(finite, np.abs(want), 0.0)
        difference = np.abs(got - want)
        good = (
            (np.isnan(got) & np.isnan(want))
            | (np.isinf(want) & (got == want))
            | (finite & (difference <= allowed))
        )
    if good.all():
        return
    bad = np.where(good, -np.inf, np.nan_to_num(difference, nan=np.inf))
    flat = int(np.argmax(bad))
    where = f" at {_index(flat, got.shape)}" if got.ndim else ""
    limit = float(np.broadcast_to(allowed, got.shape).flat[flat])
    _fail(
        f"{float(got.flat[flat])!r} differs from {float(want.flat[flat])!r}{where} by "
        f"{float(difference.flat[flat])!r}, more than {limit!r} (abs {abs}, rel "
        f"{rel}; {int((~good).sum())} of {good.size} beyond): {reason}"
    )


def _within(actual: object, expected: object, tolerance: Tolerance, what: str) -> None:
    assert_within(
        cast("ArrayLike", actual),
        cast("ArrayLike", expected),
        abs=tolerance.abs,
        rel=tolerance.rel,
        reason=f"{what}: {tolerance.reason}",
    )


@dataclass(frozen=True, kw_only=True)
class Rounding:
    """An intermediate rounding of a source: its step and effect per output."""

    step: str
    effect: Mapping[str, float]


@dataclass(frozen=True, kw_only=True)
class ReferenceCase:
    """A reference case of a source (CMP-1.7, CMP-6.1), from :func:`load_cases`.

    Attributes
    ----------
    formula, case_id : str
        Spec name and the case's id.
    source, second_source : Source, Source or None
        The source and the second source it was checked against (CMP-5.2).
    inputs, expected : Mapping
        Inputs and the published outputs.
    printed_precision : Mapping[str, float]
        Unit of the last printed digit of each printed input and output.
    intermediate_rounding : tuple of Rounding
        Each rounding of the source, step by step.
    tolerance : Tolerance or None
        Any further tolerance, with its reason.
    conventions : tuple of str
        The source's conventions (CMP-2.3).
    status : {"single_source", "second_source", "discrepancy"}
        ``discrepancy`` is a difference two sources share, with its suspected
        cause in ``discrepancy`` (CMP-5.2).
    """

    formula: str
    case_id: str
    source: Source
    inputs: Mapping[str, object]
    expected: Mapping[str, object]
    printed_precision: Mapping[str, float] = field(default_factory=dict)
    intermediate_rounding: tuple[Rounding, ...] = ()
    tolerance: Tolerance | None = None
    conventions: tuple[str, ...] = ()
    second_source: Source | None = None
    status: CaseStatus = "single_source"
    discrepancy: str = ""


_CASE_KEYS = {
    "formula",
    "case_id",
    "source",
    "inputs",
    "expected",
    "printed_precision",
    "intermediate_rounding",
    "tolerance",
    "conventions",
    "second_source",
    "status",
    "discrepancy",
}


def _source_of(data: object, where: str) -> Source:
    if not isinstance(data, dict) or not set(data) <= {
        "citation",
        "locator",
        "url",
        "access",
    }:
        raise ValueError(
            f"{where}: a source is an object of citation, locator, url, access"
        )
    access = str(data.get("access", "open"))
    if access not in _choices_of(Access):
        raise ValueError(f"{where}: access {access!r} is not open or author-provided")
    try:
        return Source(
            citation=str(data.get("citation", "")),
            locator=str(data.get("locator", "")),
            url=str(data.get("url", "")),
            access=cast("Access", access),
        )
    except SpecError as exc:
        raise ValueError(f"{where}: {exc}") from exc


def _positive_numbers(data: object, where: str) -> dict[str, float]:
    if not isinstance(data, dict):
        raise ValueError(f"{where}: an object of numbers")
    numbers: dict[str, float] = {}
    for key, value in data.items():
        if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
            raise ValueError(f"{where}.{key}: a number >= 0")
        numbers[key] = float(value)
    return numbers


def _reference_case(item: object, where: str) -> ReferenceCase:
    if not isinstance(item, dict):
        raise ValueError(f"{where}: a case is an object")
    unknown = set(item) - _CASE_KEYS
    missing = {"formula", "case_id", "source", "inputs", "expected", "status"} - set(
        item
    )
    if unknown or missing:
        raise ValueError(
            f"{where}: unknown keys {sorted(unknown)}, missing {sorted(missing)}"
        )
    if not isinstance(item["inputs"], dict) or not isinstance(item["expected"], dict):
        raise ValueError(f"{where}: inputs and expected are objects")
    status = item["status"]
    if status not in _choices_of(CaseStatus):
        raise ValueError(f"{where}: status {status!r} is unknown")
    second = item.get("second_source")
    second_source = (
        None if second is None else _source_of(second, f"{where}.second_source")
    )
    discrepancy = str(item.get("discrepancy", ""))
    if status == "second_source" and second_source is None:
        raise ValueError(f"{where}: status second_source names its second source")
    if status == "discrepancy" and (second_source is None or not discrepancy.strip()):
        raise ValueError(
            f"{where}: a discrepancy names the second source and its suspected cause "
            "(CMP-5.2)"
        )
    steps = item.get("intermediate_rounding", [])
    if not isinstance(steps, list):
        raise ValueError(f"{where}: intermediate_rounding is a list")
    rounding = []
    for number, step in enumerate(steps):
        if not isinstance(step, dict) or set(step) != {"step", "effect"}:
            raise ValueError(
                f"{where}.intermediate_rounding[{number}]: step and effect"
            )
        effect = _positive_numbers(step["effect"], f"{where}.intermediate_rounding")
        rounding.append(Rounding(step=str(step["step"]), effect=effect))
    tolerance = None
    if "tolerance" in item:
        data = item["tolerance"]
        if not isinstance(data, dict) or not set(data) <= {"abs", "rel", "reason"}:
            raise ValueError(f"{where}: tolerance holds abs, rel and reason")
        try:
            tolerance = Tolerance(**data)
        except (SpecError, TypeError) as exc:
            raise ValueError(f"{where}: {exc}") from exc
    conventions = item.get("conventions", [])
    if not isinstance(conventions, list) or not all(
        isinstance(c, str) for c in conventions
    ):
        raise ValueError(f"{where}: conventions is a list of strings")
    return ReferenceCase(
        formula=str(item["formula"]),
        case_id=str(item["case_id"]),
        source=_source_of(item["source"], f"{where}.source"),
        inputs=item["inputs"],
        expected=item["expected"],
        printed_precision=_positive_numbers(
            item.get("printed_precision", {}), f"{where}.printed_precision"
        ),
        intermediate_rounding=tuple(rounding),
        tolerance=tolerance,
        conventions=tuple(conventions),
        second_source=second_source,
        status=status,
        discrepancy=discrepancy,
    )


def load_cases(path: str | Path, formula: str) -> list[ReferenceCase]:
    """Return the reference cases of a formula from a JSON file (CMP-6.1).

    The file is an array of cases ``{"formula", "case_id", "source": {"citation",
    "locator", "url", "access"}, "inputs", "expected", "printed_precision",
    "intermediate_rounding": [{"step", "effect": {output: abs}}], "tolerance":
    {"abs" and/or "rel", "reason"}, "conventions", "second_source", "status",
    "discrepancy"}``; cases of other formulas are skipped.

    Raises
    ------
    ValueError
        If the file or a case is malformed, or a case id repeats.
    """
    where = str(path)
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{where}: not JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{where}: a JSON array of cases")
    cases = [_reference_case(item, f"{where}[{i}]") for i, item in enumerate(data)]
    mine = [case for case in cases if case.formula == formula]
    ids = [case.case_id for case in mine]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{where}: case ids of {formula} repeat")
    return mine


def _numbers_of(spec: FormulaSpec, result: object) -> dict[str, NDArray[np.float64]]:
    return {
        name: np.asarray(value, dtype=np.float64)
        for name, value in _outputs_of(spec, result).items()
        if spec.output(name).kind in ("real", "real_array")
    }


def rounding_tolerance(
    spec: FormulaSpec,
    function: Callable[..., object],
    inputs: Mapping[str, object],
    printed_precision: Mapping[str, float],
) -> dict[str, float]:
    """Return the effect on each output of half a unit of each printed input.

    The function is evaluated at every corner of the box of the printed inputs'
    rounding intervals (CMP-6.1); an array input moves all its elements together.
    A corner the function refuses with ``validation_error`` is not a possible
    true input and is skipped.

    Returns
    -------
    dict of str to float
        Per real output, the largest absolute difference from its value at the
        printed inputs.

    Raises
    ------
    ValueError
        If more than 16 inputs are printed.
    """
    center = _numbers_of(spec, function(**copy.deepcopy(dict(inputs))))
    printed = [
        (var.name, printed_precision[var.name] / 2)
        for var in spec.variables
        if var.name in printed_precision and var.kind in ("real", "real_array")
    ]
    if len(printed) > _MAX_CORNERS:
        raise ValueError(
            f"{len(printed)} printed inputs: at most {_MAX_CORNERS} corners"
        )
    effect = dict.fromkeys(center, 0.0)
    for signs in itertools.product((-1.0, 1.0), repeat=len(printed)):
        moved = copy.deepcopy(dict(inputs))
        for (name, half), sign in zip(printed, signs, strict=True):
            value = np.asarray(moved[name], dtype=np.float64) + sign * half
            moved[name] = float(value) if value.ndim == 0 else value
        try:
            corner = _numbers_of(spec, function(**moved))
        except Exception as exc:
            if getattr(exc, "code", None) == "validation_error":
                continue
            raise
        for name, values in corner.items():
            with np.errstate(invalid="ignore"):
                difference = np.abs(values - center[name])
            if difference.size and not np.isnan(difference).all():
                effect[name] = max(effect[name], float(np.nanmax(difference)))
    return effect


def case_tolerance(
    spec: FormulaSpec, function: Callable[..., object], case: ReferenceCase
) -> dict[str, float]:
    """Return the tolerance of each expected output of a reference case (CMP-6.1).

    Half a unit of the output's last printed digit, plus the effect of the printed
    inputs' rounding (:func:`rounding_tolerance`), plus each intermediate rounding
    the case lists, plus its further tolerance.
    """
    effects = rounding_tolerance(spec, function, case.inputs, case.printed_precision)
    tolerances: dict[str, float] = {}
    for name, expected in case.expected.items():
        total = case.printed_precision.get(name, 0.0) / 2 + effects.get(name, 0.0)
        total += sum(step.effect.get(name, 0.0) for step in case.intermediate_rounding)
        if case.tolerance is not None:
            largest = float(np.max(np.abs(np.asarray(expected, dtype=np.float64))))
            total += (case.tolerance.abs or 0.0) + (case.tolerance.rel or 0.0) * largest
        tolerances[name] = total
    return tolerances


def assert_case(
    spec: FormulaSpec,
    function: Callable[..., object],
    case: ReferenceCase,
    errors: Errors = DEFAULT_ERRORS,
) -> None:
    """Assert a reference case within its tolerance of CMP-6.1.

    The function must accept the inputs and keep the contract of CMP-3.4; a case
    with status ``discrepancy`` is skipped with its cause (CMP-5.2).
    """
    if case.status == "discrepancy":
        import pytest

        pytest.skip(f"{case.case_id}: discrepancy, {case.discrepancy} (CMP-5.2)")
    outputs = _evaluate(spec, function, case.inputs, errors, case.case_id)
    if outputs is None:
        _fail(f"{spec.name} [{case.case_id}]: the formula refuses a reference case")
    tolerances = case_tolerance(spec, function, case)
    extra = f"; {case.tolerance.reason}" if case.tolerance is not None else ""
    for name, expected in case.expected.items():
        if spec.output(name).kind in ("choice", "integer"):
            if outputs[name] != expected:
                _fail(f"{case.case_id}: {name} = {outputs[name]!r}, not {expected!r}")
            continue
        assert_within(
            cast("ArrayLike", outputs[name]),
            cast("ArrayLike", expected),
            abs=tolerances[name],
            reason=f"{case.case_id} of {case.source.text()}: half a unit of the "
            f"printed {name}, the printed inputs' rounding at the corners and the "
            f"source's intermediate roundings (CMP-6.1){extra}",
        )


# --- coverage of interval estimators (CMP-6.11) ----------------------------------

type Bounds = tuple[ArrayLike, ArrayLike]
type IntervalFunction = Callable[
    [NDArray[np.float64], tuple[float, ...]], Sequence[Bounds]
]
CoverageCheck = Literal["exact", "expected", "bound"]
_COVERAGE_SAMPLES: Final = 1000
_COVERAGE_ERRORS: Final = 3.0


@dataclass(frozen=True, kw_only=True)
class Coverage:
    """The simulated coverage of an interval at one setting and level (CMP-6.11).

    ``coverage`` and ``undefined`` hold one entry per element of the true value
    in C order (one for a scalar): the share of the ``samples`` intervals that
    hold it and how many of them had a bound not computed. ``check`` names what
    the coverage was asserted against, per element in ``target``: ``exact`` the
    level itself, ``expected`` the coverage the method is known or reported to
    have, ``bound`` a lower bound. :func:`assert_coverage` returns the records; a
    project keeps those of its last run (``dataclasses.asdict`` and
    ``Coverage(**record)`` round-trip through JSON) and passes them to
    :func:`formulas_markdown`.
    """

    formula: str
    setting: str
    size: int
    samples: int
    seed: int
    confidence_level: float
    check: CoverageCheck
    target: tuple[float, ...]
    coverage: tuple[float, ...]
    undefined: tuple[int, ...]
    reason: str

    def __post_init__(self) -> None:
        """Hold the per-element values as tuples, so a JSON record rebuilds one."""
        object.__setattr__(self, "target", tuple(map(float, self.target)))
        object.__setattr__(self, "coverage", tuple(map(float, self.coverage)))
        object.__setattr__(self, "undefined", tuple(map(int, self.undefined)))
        if self.check not in _choices_of(CoverageCheck):
            raise SpecError(f"coverage check {self.check!r} is not a check")
        if not len(self.target) == len(self.coverage) == len(self.undefined) > 0:
            raise SpecError("coverage, target and undefined need one entry per element")

    def text(self) -> str:
        """Return the record as ``docs/FORMULAS.md`` lists it."""

        def shares(values: tuple[float, ...]) -> str:
            low, high = min(values), max(values)
            return f"{low:.3f}" if low == high else f"{low:.3f} to {high:.3f}"

        against = {"exact": "the level", "expected": "expected", "bound": "at least"}
        over = f" over {len(self.coverage)} values" if len(self.coverage) > 1 else ""
        return (
            f"{self.setting}, n = {self.size}, c = {_num(self.confidence_level)}: "
            f"coverage {shares(self.coverage)}{over}, asserted against "
            f"{against[self.check]} {shares(self.target)} within the Monte Carlo "
            f"error; {self.samples} samples, seed {self.seed}, "
            f"{sum(self.undefined)} bounds not computed: {self.reason}"
        )


def _levels(confidence_level: float | Sequence[float]) -> tuple[float, ...]:
    """Return the levels asked as a tuple, refusing what is no set of levels."""
    asked = (
        (confidence_level,)
        if isinstance(confidence_level, (int, float))
        else tuple(confidence_level)
    )
    for c in asked:
        if isinstance(c, bool) or not isinstance(c, (int, float)) or not 0 < c < 1:
            raise ValueError(f"a confidence level is a number in (0, 1), not {c!r}")
    if not asked or len(set(asked)) != len(asked):
        raise ValueError(f"confidence levels {asked!r} are not distinct levels")
    return tuple(float(c) for c in asked)


def _where(flat: int, shape: tuple[int, ...]) -> str:
    return f" at {_index(flat, shape)}" if shape else ""


def assert_interval_properties(
    interval: IntervalFunction,
    sample: ArrayLike,
    confidence_level: float | Sequence[float],
) -> list[tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Assert the generated properties of an interval on one sample (CMP-6.11).

    Every interval has its lower bound at most its upper bound, and the interval
    of a smaller level lies inside that of a larger one, element by element where
    both bounds are computed; a bound not computed is NaN.

    Parameters
    ----------
    interval : callable
        ``interval(sample, levels)`` gives one ``(lower, upper)`` per level, in
        the order of ``levels``, each a scalar or an array of one shape.
    sample : array_like
        The values the interval is computed from.
    confidence_level : float or sequence of float
        The level or the distinct levels asked, each in (0, 1).

    Returns
    -------
    list of (ndarray, ndarray)
        The bounds per level, as float64 arrays.

    Raises
    ------
    ValueError
        If a level is not in (0, 1) or the levels are not distinct.
    AssertionError
        Naming the level, the element and the bounds that break a property.
    """
    levels = _levels(confidence_level)
    given = interval(np.asarray(sample, dtype=np.float64), levels)
    if len(given) != len(levels):
        _fail(f"{len(given)} pairs of bounds for the {len(levels)} levels {levels}")
    bounds: list[tuple[NDArray[np.float64], NDArray[np.float64]]] = []
    for c, (low, high) in zip(levels, given, strict=True):
        lower = np.asarray(low, dtype=np.float64)
        upper = np.asarray(high, dtype=np.float64)
        shape = bounds[0][0].shape if bounds else lower.shape
        if lower.shape != shape or upper.shape != shape:
            _fail(f"bounds of shapes {lower.shape} and {upper.shape} at c = {c}")
        crossed = lower > upper
        if crossed.any():
            flat = int(np.argmax(crossed))
            _fail(
                f"at c = {_num(c)} the lower bound {float(lower.flat[flat])!r} exceeds "
                f"the upper {float(upper.flat[flat])!r}{_where(flat, shape)} (CMP-6.11)"
            )
        bounds.append((lower, upper))
    order = sorted(range(len(levels)), key=lambda k: levels[k])
    for inner, outer in itertools.combinations(order, 2):
        (low_in, high_in), (low_out, high_out) = bounds[inner], bounds[outer]
        outside = (low_out > low_in) | (high_in > high_out)
        if outside.any():
            flat = int(np.argmax(outside))
            _fail(
                f"the interval at c = {_num(levels[inner])}, "
                f"[{float(low_in.flat[flat])!r}, {float(high_in.flat[flat])!r}], is "
                f"not inside that at c = {_num(levels[outer])}, "
                f"[{float(low_out.flat[flat])!r}, {float(high_out.flat[flat])!r}]"
                f"{_where(flat, low_in.shape)} (CMP-6.11)"
            )
    return bounds


def _targets(
    given: Mapping[float, ArrayLike] | None,
    levels: tuple[float, ...],
    shape: tuple[int, ...],
    what: str,
) -> dict[float, NDArray[np.float64]]:
    """Return the coverages asserted per level, broadcast to the true value."""
    targets: dict[float, NDArray[np.float64]] = {}
    for c, value in (given or {}).items():
        if c not in levels:
            raise ValueError(f"{what} for c = {c!r}, not a level asked {levels}")
        target = np.asarray(value, dtype=np.float64)
        if not np.all((target >= 0) & (target <= 1)):
            raise ValueError(f"{what} at c = {c!r} is not a share in [0, 1]")
        try:
            targets[float(c)] = np.broadcast_to(target, shape)
        except ValueError:
            raise ValueError(
                f"{what} at c = {c!r} has the shape {target.shape}, not {shape}"
            ) from None
    return targets


def assert_coverage(
    spec: FormulaSpec,
    interval: IntervalFunction,
    draw: Callable[[np.random.Generator, int], ArrayLike],
    true_value: ArrayLike,
    *,
    setting: str,
    size: int,
    confidence_level: float | Sequence[float],
    seed: int,
    reason: str,
    samples: int = _COVERAGE_SAMPLES,
    expected: Mapping[float, ArrayLike] | None = None,
    at_least: Mapping[float, ArrayLike] | None = None,
) -> list[Coverage]:
    """Assert an interval's coverage, simulated, seeded, at one setting (CMP-6.11).

    ``samples`` samples of ``size`` values are drawn in turn from one generator
    seeded with ``seed``; on each, :func:`assert_interval_properties` holds and
    every interval asked either holds the true value, bounds included, or not.
    A bound not computed (NaN) holds nothing. The share that holds, per level
    and element, is asserted within the Monte Carlo error ``3 sqrt(p (1 - p) /
    m)`` of ``m`` samples around ``p``, three standard errors, so a right method
    fails one assertion in about 370: the level itself for an exact method; the
    coverage in ``expected`` (an exact method's known coverage, an approximate
    one's as its source reports it for the setting); or, for a level in
    ``at_least``, at least that bound less the error. The test fixes ``seed``
    once and records it; a seed is never chosen to pass.

    Parameters
    ----------
    spec : FormulaSpec
        The interval's formula.
    interval : callable
        ``interval(sample, levels)`` as in :func:`assert_interval_properties`,
        each bound of the true value's shape.
    draw : callable
        ``draw(generator, size)`` gives one sample, ``size`` values along its
        first axis, from the distribution of the setting.
    true_value : array_like
        The value the intervals estimate, finite.
    setting : str
        The distribution and its parameters, as the report names them.
    size : int
        Values per sample: 30 and 60 for annual series.
    confidence_level : float or sequence of float
        The levels asked, each in (0, 1), distinct.
    seed : int
        The generator's seed, at least 0.
    reason : str
        Why the coverage asserted is the method's (CMP-6.8); never empty.
    samples : int
        Samples drawn, at least 1,000.
    expected, at_least : Mapping[float, array_like] or None
        Per level, the coverage asserted or its lower bound, a share or one per
        element; a level in neither is asserted at itself.

    Returns
    -------
    list of Coverage
        One record per level, in the order asked, for the report.

    Raises
    ------
    ValueError
        If an argument breaks what is above.
    AssertionError
        Naming the sample, level and element whose property or coverage fails,
        the coverage, its target and the reason.
    """
    levels = _levels(confidence_level)
    for name, text in (("setting", setting), ("reason", reason)):
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"a coverage needs its {name} (CMP-6.8)")
    for name, number, least in (
        ("size", size, 1),
        ("samples", samples, _COVERAGE_SAMPLES),
        ("seed", seed, 0),
    ):
        if isinstance(number, bool) or not isinstance(number, int) or number < least:
            raise ValueError(f"{name} is an integer of at least {least}: {number!r}")
    truth = np.asarray(true_value, dtype=np.float64)
    if not np.isfinite(truth).all():
        raise ValueError("the true value is not finite")
    known = _targets(expected, levels, truth.shape, "an expected coverage")
    bound = _targets(at_least, levels, truth.shape, "a bound of the coverage")
    if both := known.keys() & bound.keys():
        raise ValueError(f"levels {sorted(both)} have both a coverage and a bound")
    held = np.zeros((len(levels), *truth.shape), dtype=np.int64)
    undefined = np.zeros_like(held)
    generator = np.random.default_rng(seed)
    where = f"{spec.name}, {setting}, n = {size}"
    for number in range(samples):
        sample = np.asarray(draw(generator, size), dtype=np.float64)
        if sample.ndim == 0 or sample.shape[0] != size:
            _fail(f"{where}: a sample of shape {sample.shape}, not {size} values")
        try:
            bounds = assert_interval_properties(interval, sample, levels)
        except AssertionError as failure:
            _fail(f"{where}, sample {number} of seed {seed}: {failure}")
        for k, (lower, upper) in enumerate(bounds):
            if lower.shape != truth.shape:
                _fail(f"{where}: bounds of shape {lower.shape}, not {truth.shape}")
            held[k] += (lower <= truth) & (truth <= upper)
            undefined[k] += np.isnan(lower) | np.isnan(upper)
    records: list[Coverage] = []
    for k, c in enumerate(levels):
        check: CoverageCheck = "exact"
        target = np.broadcast_to(np.float64(c), truth.shape)
        if c in known:
            check = "expected"
            target = known[c]
        elif c in bound:
            check = "bound"
            target = bound[c]
        share = held[k] / samples
        error = _COVERAGE_ERRORS * np.sqrt(target * (1.0 - target) / samples)
        bad = (
            share < target - error if check == "bound" else abs(share - target) > error
        )
        if bad.any():
            flat = int(np.argmax(bad))
            p, e = float(target.flat[flat]), float(error.flat[flat])
            allowed = f"{p!r} ± {e:.4f}"
            if check == "bound":
                allowed = f"at least {p!r} - {e:.4f}"
            _fail(
                f"{where}, c = {_num(c)}: coverage {float(share.flat[flat])!r}"
                f"{_where(flat, truth.shape)}, not {allowed} ({check}; the Monte "
                f"Carlo error 3 sqrt(p (1 - p) / m) of {samples} samples of seed "
                f"{seed}; {int(undefined[k].flat[flat])} bounds not computed): "
                f"{reason}"
            )
        records.append(
            Coverage(
                formula=spec.name,
                setting=setting,
                size=size,
                samples=samples,
                seed=seed,
                confidence_level=c,
                check=check,
                target=tuple(target.ravel().tolist()),
                coverage=tuple(share.ravel().tolist()),
                undefined=tuple(undefined[k].ravel().tolist()),
                reason=reason,
            )
        )
    return records


# --- frozen oracles (CMP-6.4) ----------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class FrozenOracle:
    """The output of an oracle run once, stored as CSV (CMP-6.4).

    Attributes
    ----------
    path : str
        The file.
    metadata : Mapping[str, str]
        ``tool``, ``packages``, ``platform``, ``date``, ``script`` and any other
        ``# key: value`` lines of the header.
    columns : tuple of str
        Column names.
    rows : tuple of Mapping[str, str]
        The rows as text.
    """

    path: str
    metadata: Mapping[str, str]
    columns: tuple[str, ...]
    rows: tuple[Mapping[str, str], ...]

    def floats(self, column: str) -> NDArray[np.float64]:
        """Return a column as float64; an empty cell or ``NA`` is NaN."""
        if column not in self.columns:
            raise KeyError(f"{self.path} has no column {column!r}")
        texts = [row[column].strip() for row in self.rows]
        return np.array(
            [math.nan if t in ("", "NA", "NaN", "nan") else float(t) for t in texts],
            dtype=np.float64,
        )


def read_frozen_oracle(path: str | Path) -> FrozenOracle:
    """Read a frozen oracle: CSV after a commented metadata header (CMP-6.4).

    The header is ``# key: value`` lines with at least ``tool``, ``packages``
    (with versions), ``platform``, ``date`` (ISO 8601) and ``script`` (the script
    in ``tests/oracles/`` that produced it).

    Raises
    ------
    ValueError
        If the header lacks a key, the date is not ISO, or the table is empty or
        ragged.
    """
    where = str(path)
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    data = (i for i, line in enumerate(lines) if not line.startswith("#"))
    start = next(data, len(lines))
    metadata: dict[str, str] = {}
    for line in lines[:start]:
        key, colon, value = line[1:].partition(":")
        if colon and key.strip():
            metadata[key.strip().lower()] = value.strip()
    missing = [key for key in _ORACLE_KEYS if not metadata.get(key)]
    if missing:
        raise ValueError(
            f"{where}: a frozen oracle names {list(_ORACLE_KEYS)} in its header; "
            f"missing {missing} (CMP-6.4)"
        )
    try:
        date.fromisoformat(metadata["date"])
    except ValueError as exc:
        raise ValueError(f"{where}: date {metadata['date']!r} is not ISO 8601") from exc
    reader = csv.reader(io.StringIO("\n".join(lines[start:])))
    table = [row for row in reader if row]
    if len(table) < 2:
        raise ValueError(f"{where}: no rows under the header (CMP-6.4)")
    columns = tuple(name.strip() for name in table[0])
    if any(len(row) != len(columns) for row in table[1:]):
        raise ValueError(f"{where}: a row has not {len(columns)} cells")
    rows = tuple(dict(zip(columns, row, strict=True)) for row in table[1:])
    return FrozenOracle(path=where, metadata=metadata, columns=columns, rows=rows)


# --- generated documents (CMP-2.6, CMP-2.7) and contract checks ------------------


def _source_card(source: Source) -> dict[str, object]:
    data: dict[str, object] = {"citation": source.citation, "access": source.access}
    if source.locator:
        data["locator"] = source.locator
    if source.url:
        data["url"] = source.url
    return data


def _range_card(rng: Range) -> dict[str, object]:
    data: dict[str, object] = {}
    if math.isfinite(rng.low):
        data["low"] = rng.low
        data["low_inclusive"] = rng.low_inclusive
    if math.isfinite(rng.high):
        data["high"] = rng.high
        data["high_inclusive"] = rng.high_inclusive
    if rng.test_low is not None:
        data["test_low"] = rng.test_low
    if rng.test_high is not None:
        data["test_high"] = rng.test_high
    if rng.test_reason:
        data["test_reason"] = rng.test_reason
    if rng.source is not None:
        data["source"] = _source_card(rng.source)
    return data


def _tolerance_card(tolerance: Tolerance) -> dict[str, object]:
    data: dict[str, object] = {"reason": tolerance.reason}
    if tolerance.abs is not None:
        data["abs"] = float(tolerance.abs)
    if tolerance.rel is not None:
        data["rel"] = float(tolerance.rel)
    return data


def _variable_card(var: Variable) -> dict[str, object]:
    data: dict[str, object] = {
        "name": var.name,
        "symbol": var.symbol,
        "unit": var.unit,
        "kind": var.kind,
    }
    if var.description:
        data["description"] = var.description
    if var.kind == "choice":
        data["choices"] = list(var.choices)
        return data
    data["physical"] = _range_card(_physical(var))
    applicability = var.applicability
    data["applicability"] = (
        _range_card(applicability) if isinstance(applicability, Range) else "unstated"
    )
    data["typical"] = _range_card(cast("Range", var.typical))
    if var.kind == "real_array":
        data["gaps_allowed"] = var.gaps_allowed
        data["dims"] = var.dims
        data["min_length"] = var.min_length
        if var.max_length is not None:
            data["max_length"] = var.max_length
    return data


def _output_card(output: Output) -> dict[str, object]:
    data: dict[str, object] = {
        "name": output.name,
        "unit": output.unit,
        "kind": output.kind,
    }
    if output.symbol:
        data["symbol"] = output.symbol
    if output.description:
        data["description"] = output.description
    if output.physical is not None:
        data["physical"] = _range_card(output.physical)
    if output.boundary_tolerance is not None:
        data["boundary_tolerance"] = float(output.boundary_tolerance)
    if output.kind == "real_array":
        data["gaps_allowed"] = output.gaps_allowed
        if output.gaps_from is not None:
            data["gaps_from"] = output.gaps_from
    if output.choices:
        data["choices"] = list(output.choices)
    return data


def _constant_card(constant: Constant) -> dict[str, object]:
    data: dict[str, object] = {
        "name": constant.name,
        "value": float(constant.value),
        "unit": constant.unit,
        "source": _source_card(constant.source),
    }
    if constant.symbol:
        data["symbol"] = constant.symbol
    if isinstance(constant.value, Fraction):
        data["exact"] = str(constant.value)
    return data


def card(spec: FormulaSpec) -> dict[str, object]:
    """Return the card of a Tier A formula, ``formulas/<name>.toml`` (CMP-2.6).

    The dict holds only strings, booleans, integers, finite floats, lists and
    dicts, and follows ``schemas/formula/card-1.schema.json``; :func:`to_toml`
    writes it.
    """
    properties = spec.properties
    data: dict[str, object] = {
        "schema": CARD_FORMAT,
        "name": spec.name,
        "title": spec.title,
        "function": spec.function,
        "family": spec.family,
        "formula_version": spec.formula_version,
        "status": spec.status,
        "equation": spec.equation,
        "latex": spec.latex,
        "validation": spec.validation,
        "conventions": list(spec.conventions),
        "assumptions": list(spec.assumptions),
        "notices": list(spec.notice_codes()),
        "reference_cases": list(spec.reference_cases),
    }
    if spec.no_traps_reason:
        data["no_traps_reason"] = spec.no_traps_reason
    data["properties"] = {
        "units": properties.units,
        "monotonic": dict(properties.monotonic),
        "scalings": [
            {
                "name": s.name,
                "inputs": {k: float(v) for k, v in s.inputs.items()},
                "outputs": {k: float(v) for k, v in s.outputs.items()},
                "tolerance": _tolerance_card(s.tolerance),
            }
            for s in properties.scalings
        ],
        "limits": [
            {"name": limit.name, "text": limit.text}
            | ({"source": _source_card(limit.source)} if limit.source else {})
            for limit in properties.limits
        ],
        "conservation": [
            {"name": c.name, "text": c.text, "tolerance": _tolerance_card(c.tolerance)}
            for c in properties.conservation
        ],
        "symmetries": [
            {"name": s.name, "text": s.text, "tolerance": _tolerance_card(s.tolerance)}
            for s in properties.symmetries
        ],
    }
    data["sources"] = [_source_card(s) for s in spec.sources]
    data["variables"] = [_variable_card(v) for v in spec.variables]
    data["constraints"] = [
        {
            "name": c.name,
            "class": c.cls,
            "text": c.text,
            "source": _source_card(c.source),
        }
        for c in spec.constraints
    ]
    data["constants"] = [_constant_card(c) for c in spec.constants]
    data["outputs"] = [_output_card(o) for o in spec.outputs]
    traps = {trap.name: trap for trap in TRAPS[spec.family]}
    data["traps"] = [
        {"name": name, "description": traps[name].description, "test": test}
        for name, test in spec.traps.items()
    ]
    data["oracles"] = [
        {
            "kind": o.kind,
            "description": o.description,
            "test": o.test,
            "conventions": list(o.conventions),
        }
        for o in spec.oracles
    ]
    data["tables"] = [
        {
            "path": t.path,
            "sha256": t.sha256,
            "comparison": t.comparison,
            "source": _source_card(t.source),
        }
        for t in spec.tables
    ]
    return data


_TOML_ESCAPES = {"\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r"}


def _toml_string(text: str) -> str:
    parts = ['"']
    for char in text:
        if char in ('"', "\\"):
            parts.append("\\" + char)
        elif char in _TOML_ESCAPES:
            parts.append(_TOML_ESCAPES[char])
        elif ord(char) < 0x20 or ord(char) == 0x7F:
            parts.append(f"\\u{ord(char):04X}")
        else:
            parts.append(char)
    parts.append('"')
    return "".join(parts)


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"a card holds finite numbers, not {value!r}")
        return repr(value)
    if isinstance(value, str):
        return _toml_string(value)
    if isinstance(value, list | tuple):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    raise TypeError(f"no TOML value for a {_type_name(value)}")


def _toml_key(key: str) -> str:
    return key if _TOML_BARE.fullmatch(key) else _toml_string(key)


def _is_tables(value: object) -> bool:
    return (
        isinstance(value, list | tuple)
        and bool(value)
        and all(isinstance(item, Mapping) for item in value)
    )


def _toml_table(
    table: Mapping[str, object], path: tuple[str, ...], lines: list[str]
) -> None:
    for key, value in table.items():
        if not isinstance(value, Mapping) and not _is_tables(value):
            lines.append(f"{_toml_key(key)} = {_toml_value(value)}")
    for key, value in table.items():
        if isinstance(value, Mapping):
            inner = (*path, key)
            lines += ["", f"[{'.'.join(_toml_key(k) for k in inner)}]"]
            _toml_table(value, inner, lines)
    for key, value in table.items():
        if _is_tables(value):
            inner = (*path, key)
            for item in cast("Sequence[Mapping[str, object]]", value):
                lines += ["", f"[[{'.'.join(_toml_key(k) for k in inner)}]]"]
                _toml_table(item, inner, lines)


def to_toml(data: Mapping[str, object]) -> str:
    """Return a mapping as TOML 1.0: strings, booleans, numbers, lists and tables.

    Plain keys of a table come before its tables and arrays of tables, so
    ``tomllib.loads(to_toml(data)) == data``.

    Raises
    ------
    ValueError
        If a float is not finite.
    TypeError
        If a value has no TOML form (``None`` among them).
    """
    lines: list[str] = []
    _toml_table(data, (), lines)
    return "\n".join(lines).lstrip("\n") + "\n"


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _range_text(rng: Range | str | None) -> str:
    if not isinstance(rng, Range):
        return "unstated" if rng == "unstated" else "–"
    text = rng.interval()
    tests = [
        f"{side} {_num(value)}"
        for side, value in (("low", rng.test_low), ("high", rng.test_high))
        if value is not None
    ]
    if tests:
        text += f", test bound {' and '.join(tests)} ({rng.test_reason})"
    if rng.source is not None:
        text += f": {rng.source.text()}"
    return _cell(text)


def _score(scores: Mapping[str, float], function: str) -> str:
    parts = function.split(".")
    for end in range(len(parts) - 1, 0, -1):
        module = ".".join(parts[:end])
        if module in scores:
            return f"{scores[module]:.0%}"
    return "not measured"


def _test_classes(spec: FormulaSpec) -> list[str]:
    kinds = {oracle.kind for oracle in spec.oracles}
    classes = []
    if spec.reference_cases:
        classes.append("reference cases (CMP-6.1)")
    if kinds & {"exact", "algorithm"}:
        classes.append("oracles (CMP-6.2)")
    if "established" in kinds:
        classes.append("established implementations (CMP-6.3)")
    if "frozen" in kinds:
        classes.append("frozen oracles (CMP-6.4)")
    classes.append("generated ranges and types (CMP-6.5)")
    if spec.properties.declared:
        classes.append("properties (CMP-6.5)")
    if spec.traps:
        classes.append("numerical traps (CMP-6.6)")
    if spec.family == "statistic":
        classes.append("statistical procedures (CMP-6.7)")
    return classes


def _bullets(items: Sequence[str], empty: str) -> list[str]:
    return [f"- {item}" for item in items] if items else [empty]


def _exponents(exponents: Mapping[str, float]) -> str:
    shown = (f"`{name}` e = {_num(float(e))}" for name, e in exponents.items())
    return ", ".join(shown) or "none"


def _spec_markdown(
    spec: FormulaSpec, scores: Mapping[str, float], coverage: Sequence[Coverage]
) -> list[str]:
    properties = spec.properties
    lines = [
        f'<a id="{spec.name}"></a>',
        f"### {spec.title}",
        "",
        f"`{spec.function}` · family `{spec.family}` · formula_version "
        f"{spec.formula_version} · status **{spec.status}** · mutation score "
        f"{_score(scores, spec.function)}",
        "",
        "$$",
        spec.latex,
        "$$",
        "",
        f"Plain text: `{spec.equation}`",
        "",
        "**Sources**",
        "",
        *[
            f"- {s.text()} ({s.access})" + (f" <{s.url}>" if s.url else "")
            for s in spec.sources
        ],
        "",
        "**Variables**",
        "",
        "| Variable | Symbol | Unit | Kind | Physical range | Applicability | "
        "Typical range |",
        "|---|---|---|---|---|---|---|",
    ]
    for var in spec.variables:
        kind = (
            var.kind if var.kind != "choice" else f"choice of {', '.join(var.choices)}"
        )
        lines.append(
            f"| `{var.name}` | ${var.symbol}$ | {_cell(var.unit)} | {_cell(kind)} | "
            f"{_range_text(var.physical)} | {_range_text(var.applicability)} | "
            f"{_range_text(var.typical)} |"
        )
    if spec.constraints:
        lines += [
            "",
            "**Constraints**",
            "",
            "| Constraint | Class | Condition | Source |",
        ]
        lines.append("|---|---|---|---|")
        lines += [
            f"| `{c.name}` | {c.cls} | {_cell(c.text)} | {_cell(c.source.text())} |"
            for c in spec.constraints
        ]
    if spec.constants:
        lines += [
            "",
            "**Constants**",
            "",
            "| Constant | Symbol | Value | Unit | Source |",
        ]
        lines.append("|---|---|---|---|---|")
        lines += [
            f"| `{c.name}` | {f'${c.symbol}$' if c.symbol else ''} | "
            f"{_cell(c.value if isinstance(c.value, Fraction) else _num(c.value))} | "
            f"{_cell(c.unit)} | {_cell(c.source.text())} |"
            for c in spec.constants
        ]
    lines += [
        "",
        "**Outputs**",
        "",
        "| Output | Unit | Kind | Physical range | Boundary tolerance |",
        "|---|---|---|---|---|",
    ]
    for output in spec.outputs:
        tolerance = output.boundary_tolerance
        lines.append(
            f"| `{output.name}` | {_cell(output.unit)} | {output.kind} | "
            f"{_range_text(output.physical)} | "
            f"{'4 ulp of the bound' if tolerance is None else _num(tolerance)} |"
        )
    traps = [f"`{name}`: {test}" for name, test in spec.traps.items()]
    properties_text = [f"units: {properties.units}"]
    if properties.monotonic:
        signs = ", ".join(
            f"`{name}` {'increasing' if sign > 0 else 'decreasing'}"
            for name, sign in properties.monotonic.items()
        )
        properties_text.append(f"monotonic: {signs}")
    properties_text += [
        f"scaling `{s.name}`: inputs times 2^e ({_exponents(s.inputs)}) give "
        f"outputs times 2^e ({_exponents(s.outputs)})"
        for s in properties.scalings
    ]
    properties_text += [f"limit `{x.name}`: {x.text}" for x in properties.limits]
    properties_text += [
        f"conservation `{x.name}`: {x.text}" for x in properties.conservation
    ]
    properties_text += [f"symmetry `{x.name}`: {x.text}" for x in properties.symmetries]
    lines += [
        "",
        "**Conventions (CMP-2.3)**",
        "",
        *_bullets(spec.conventions, "None stated."),
        "",
        "**Assumptions**",
        "",
        *_bullets(spec.assumptions, "None stated."),
        "",
        f"**Validation:** {spec.validation}",
        "",
        f"**Notices:** {', '.join(f'`{c}`' for c in spec.notice_codes()) or 'none'}",
        "",
        "**Numerical traps (CMP-6.6)**",
        "",
        *_bullets(traps, f"None applies: {spec.no_traps_reason}"),
        "",
        "**Properties (CMP-6.5)**",
        "",
        *_bullets(properties_text, ""),
        "",
        "**Reference cases (CMP-6.1)**",
        "",
        *_bullets([f"`{p}`" for p in spec.reference_cases], "None."),
        "",
        "**Oracles (CMP-6.2 to CMP-6.4)**",
        "",
        *_bullets(
            [f"{o.kind}: {o.description} (`{o.test}`)" for o in spec.oracles], "None."
        ),
    ]
    if spec.tables:
        lines += ["", "**Tables (CMP-2.5)**", ""]
        lines += [
            f"- `{t.path}` sha256 `{t.sha256}`: {t.source.text()}; transcriptions "
            f"compared in `{t.comparison}`"
            for t in spec.tables
        ]
    classes = _test_classes(spec)
    if coverage:
        lines += ["", "**Coverage of its intervals (CMP-6.11)**", ""]
        lines += [f"- {_cell(record.text())}" for record in coverage]
        classes.append("coverage (CMP-6.11)")
    lines += ["", f"**Tests by class (CMP §6):** {'; '.join(classes)}."]
    return lines


def formulas_markdown(
    specs: Sequence[FormulaSpec],
    tier_b: Sequence[TierBSpec] = (),
    mutation_scores: Mapping[str, float] | None = None,
    *,
    delegated: Sequence[Delegated] = (),
    coverage: Sequence[Coverage] = (),
    title: str = "Formulas",
) -> str:
    """Return ``docs/FORMULAS.md`` generated from the specs (CMP-2.6).

    Parameters
    ----------
    specs : sequence of FormulaSpec
        The Tier A formulas, in the order shown.
    tier_b : sequence of TierBSpec
        The Tier B formulas (CMP-2.2).
    mutation_scores : Mapping[str, float] or None
        Killed share of mutants per module, 0 to 1, from the last mutation run
        (CMP-7.1); a formula shows the score of its module.
    delegated : sequence of Delegated
        Computations delegated to libraries (CMP-1.2).
    coverage : sequence of Coverage
        The coverage of the intervals from the last simulation (CMP-6.11), shown
        under their formulas in the order given.
    title : str
        The document's heading.

    Returns
    -------
    str
        The document; the same specs give the same text, so a check compares it
        with the committed file (DEV-10.4).

    Raises
    ------
    ValueError
        If a coverage record names no formula of ``specs``.
    """
    scores = dict(mutation_scores or {})
    names = {spec.name for spec in specs}
    if unknown := sorted({r.formula for r in coverage} - names):
        raise ValueError(f"coverage of {unknown}, not formulas of the specs")
    lines = [
        f"# {title}",
        "",
        "<!-- Generated from the formula specs by nogat_formulas (CMP-2.6); "
        "do not edit. -->",
        "",
        "## Tier A",
        "",
        "| Formula | Function | Status | Version | Mutation score |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| [{_cell(s.title)}](#{s.name}) | `{s.function}` | {s.status} | "
        f"{s.formula_version} | {_score(scores, s.function)} |"
        for s in specs
    ]
    for spec in specs:
        own = [record for record in coverage if record.formula == spec.name]
        lines += ["", *_spec_markdown(spec, scores, own)]
    if tier_b:
        lines += [
            "",
            "## Tier B",
            "",
            "| Formula | Function | Definition | Constants | Convention | Source |",
            "|---|---|---|---|---|---|",
        ]
        for spec_b in tier_b:
            constants = "; ".join(
                f"{c.name} = {c.value} {c.unit} ({c.source.text()})"
                for c in spec_b.constants
            )
            lines.append(
                f"| `{spec_b.name}` | `{spec_b.function}` | "
                f"{_cell(spec_b.definition)} | {_cell(constants or '–')} | "
                f"{_cell(spec_b.convention)} | {_cell(spec_b.source.text())} |"
            )
    if delegated:
        lines += [
            "",
            "## Delegated computations (CMP-1.2)",
            "",
            "| Computation | Library | Versions | Smoke case | Test |",
            "|---|---|---|---|---|",
        ]
        lines += [
            f"| {_cell(d.name)} | {_cell(d.library)} | {_cell(d.versions)} | "
            f"{_cell(d.smoke_case)} | `{d.test}` |"
            for d in delegated
        ]
    if scores:
        lines += [
            "",
            "## Mutation scores (CMP-7.1)",
            "",
            "| Module | Score |",
            "|---|---|",
        ]
        lines += [f"| `{module}` | {scores[module]:.0%} |" for module in sorted(scores)]
    return "\n".join(lines) + "\n"


def docstring_problems(spec: FormulaSpec, function: Callable[..., object]) -> list[str]:
    """Return what breaks CMP-2.7 in a Tier A function's docstring.

    The docstring gives the formula's purpose and the spec's name, and no digit
    outside that name: constants, units, ranges and equations are the spec's.
    """
    name = getattr(function, "__qualname__", repr(function))
    doc = inspect.getdoc(function)
    if not doc:
        return [f"{name}: no docstring (CMP-2.7)"]
    problems = []
    if spec.name not in doc:
        problems.append(f"{name}: the docstring does not name its spec {spec.name!r}")
    for number, line in enumerate(doc.replace(spec.name, "").splitlines(), 1):
        digits = _DIGIT.findall(line)
        if digits:
            problems.append(
                f"{name}: docstring line {number} holds {digits}: {line.strip()!r} "
                "(CMP-2.7)"
            )
    return problems


def _call_name(node: ast.expr) -> tuple[str, str]:
    """Return (base, name) of a called expression, ``("np", "isclose")``."""
    if isinstance(node, ast.Attribute):
        base = node.value
        if isinstance(base, ast.Attribute):
            return base.attr, node.attr
        return (base.id if isinstance(base, ast.Name) else ""), node.attr
    if isinstance(node, ast.Name):
        return "", node.id
    return "", ""


def tolerance_problems(source: str, filename: str = "<test>") -> list[str]:
    """Return calls of a test file that compare numbers without a tolerance.

    CMP-6.8: ``approx`` without ``rel``/``abs``; ``assert_allclose``,
    ``numpy.isclose`` and ``numpy.allclose`` without ``rtol``/``atol``;
    ``math.isclose`` without ``rel_tol``/``abs_tol``.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source, filename)):
        if not isinstance(node, ast.Call):
            continue
        base, name = _call_name(node.func)
        given = {k.arg for k in node.keywords}
        if name == "approx":
            explicit = bool(given & {"rel", "abs"}) or len(node.args) >= 2
        elif name in ("assert_allclose", "allclose") or (
            name == "isclose" and base in ("np", "numpy")
        ):
            explicit = bool(given & {"rtol", "atol"}) or len(node.args) >= 3
        elif name == "isclose":
            explicit = bool(given & {"rel_tol", "abs_tol", "rtol", "atol"})
        else:
            continue
        if not explicit:
            found.append((node.lineno, name))
    return [
        f"{filename}:{line}: {name}() without an explicit tolerance (CMP-6.8)"
        for line, name in sorted(found)
    ]


def spec_problems(
    spec: FormulaSpec,
    function: Callable[..., object] | None = None,
    *,
    root: str | Path | None = None,
) -> list[str]:
    """Return what breaks the standard in a spec and its function: a contract test.

    Checks the docstring (CMP-2.7), that the function is the spec's and takes its
    inputs, two kinds of evidence unless the status is ``unreferenced`` (CMP-5.1,
    CMP-9.3), the status against its evidence (CMP-2.6, CMP-5.2), a reference
    case for a unit-specific formula (CMP-6.5), the constraints' points
    (CMP-6.5) and, under ``root``, the reference-case files and the tables'
    SHA-256 (CMP-2.5).
    """
    problems: list[str] = []
    if function is not None:
        problems += docstring_problems(spec, function)
        path = f"{function.__module__}.{function.__qualname__}"
        if path != spec.function:
            problems.append(
                f"{spec.name}: the function is {path}, the spec {spec.function}"
            )
        parameters = list(inspect.signature(function).parameters)
        inputs = [v.name for v in spec.variables]
        if parameters != inputs:
            problems.append(
                f"{spec.name}: the function takes {parameters}, the spec {inputs}"
            )
    evidence = [
        bool(spec.reference_cases),
        bool(spec.oracles),
        spec.properties.declared,
    ]
    if spec.status != "unreferenced" and sum(evidence) < 2:
        problems.append(
            f"{spec.name}: {sum(evidence)} of reference cases, oracles and properties; "
            "CMP-5.1 needs two"
        )
    if spec.properties.units == "unit_specific" and not spec.reference_cases:
        problems.append(f"{spec.name}: a unit-specific formula needs reference cases")
    base = spec.base_point()
    for constraint in spec.constraints:
        try:
            _check_points(spec, constraint, base)
        except SpecError as exc:
            problems.append(str(exc))
    referenced = bool(spec.reference_cases)
    if root is not None:
        usable = 0
        for relative in spec.reference_cases:
            path_of = Path(root) / relative
            try:
                cases = load_cases(path_of, spec.name)
            except (OSError, ValueError) as exc:
                problems.append(f"{spec.name}: {relative}: {exc}")
                continue
            if not cases:
                problems.append(f"{spec.name}: {relative} has no case of the formula")
            usable += sum(case.status != "discrepancy" for case in cases)
        referenced = usable > 0
        for table in spec.tables:
            try:
                digest = hashlib.sha256(
                    (Path(root) / table.path).read_bytes()
                ).hexdigest()
            except OSError as exc:
                problems.append(f"{spec.name}: table {table.path}: {exc}")
                continue
            if digest != table.sha256:
                problems.append(f"{spec.name}: table {table.path} has SHA-256 {digest}")
    expected: Status = (
        "referenced"
        if referenced
        else "oracle only"
        if spec.oracles
        else "unreferenced"
    )
    if spec.status != expected:
        problems.append(
            f"{spec.name}: status {spec.status!r}, its evidence gives {expected!r} "
            "(CMP-2.6)"
        )
    return problems


# --- units (CMP-4.3) ---------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class Unit:
    """A unit of the units table (CMP-4.3).

    A value ``v`` in this unit is ``factor * v + offset`` in the reference unit of
    its quantity: square metre, metre, cubic metre per second, second or kelvin.
    Factors and offsets are exact.
    """

    name: str
    quantity: str
    factor: Fraction
    source: Source
    offset: Fraction = Fraction(0)


_SI = "BIPM (2019), The International System of Units (SI), 9th edition, version 4.01"
_SI_URL = "https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf"
_SP811 = (
    "Thompson, A. and Taylor, B. N. (2008), Guide for the Use of the International "
    "System of Units (SI), NIST Special Publication 811"
)
_SP811_URL = "https://www.nist.gov/pml/special-publication-811"
_PREFIX = Source(citation=_SI, locator="Table 7, SI prefixes", url=_SI_URL)
_ACCEPTED = Source(
    citation=_SI,
    locator="Table 8, non-SI units accepted for use with the SI",
    url=_SI_URL,
)
_FACTORS = Source(
    citation=_SP811,
    locator="Appendix B.8, factors in bold are exact (international foot, inch, mile)",
    url=_SP811_URL,
)
_FOOT = Fraction(3048, 10_000)

UNITS: Final[Mapping[str, Unit]] = MappingProxyType(
    {
        unit.name: unit
        for unit in (
            Unit(name="m2", quantity="area", factor=Fraction(1), source=_PREFIX),
            Unit(name="km2", quantity="area", factor=Fraction(10**6), source=_PREFIX),
            Unit(name="ha", quantity="area", factor=Fraction(10**4), source=_ACCEPTED),
            Unit(
                name="acre",
                quantity="area",
                factor=43_560 * _FOOT**2,
                source=Source(
                    citation="NIST Handbook 44 (2024), Appendix C, General Tables of "
                    "Units of Measurement",
                    locator="acre = 43 560 square feet of the international foot, "
                    "the U.S. survey foot deprecated from 2023-01-01",
                    url="https://www.nist.gov/document/"
                    "nist-hb-44-2024-appendix-c-general-tables-units-measurement",
                ),
            ),
            Unit(name="m", quantity="length", factor=Fraction(1), source=_PREFIX),
            Unit(
                name="mm", quantity="length", factor=Fraction(1, 1000), source=_PREFIX
            ),
            Unit(name="cm", quantity="length", factor=Fraction(1, 100), source=_PREFIX),
            Unit(name="km", quantity="length", factor=Fraction(1000), source=_PREFIX),
            Unit(
                name="in",
                quantity="length",
                factor=Fraction(254, 10_000),
                source=_FACTORS,
            ),
            Unit(name="ft", quantity="length", factor=_FOOT, source=_FACTORS),
            Unit(name="mi", quantity="length", factor=5280 * _FOOT, source=_FACTORS),
            Unit(
                name="m3_per_s",
                quantity="discharge",
                factor=Fraction(1),
                source=_PREFIX,
            ),
            Unit(
                name="l_per_s",
                quantity="discharge",
                factor=Fraction(1, 1000),
                source=_ACCEPTED,
            ),
            Unit(
                name="ft3_per_s",
                quantity="discharge",
                factor=_FOOT**3,
                source=_FACTORS,
            ),
            Unit(name="s", quantity="time", factor=Fraction(1), source=_PREFIX),
            Unit(name="min", quantity="time", factor=Fraction(60), source=_ACCEPTED),
            Unit(name="h", quantity="time", factor=Fraction(3600), source=_ACCEPTED),
            Unit(name="d", quantity="time", factor=Fraction(86_400), source=_ACCEPTED),
            Unit(name="K", quantity="temperature", factor=Fraction(1), source=_PREFIX),
            Unit(
                name="degC",
                quantity="temperature",
                factor=Fraction(1),
                offset=Fraction(27_315, 100),
                source=Source(
                    citation=_SI,
                    locator="section 2.3.1, t/°C = T/K - 273.15",
                    url=_SI_URL,
                ),
            ),
            Unit(
                name="degF",
                quantity="temperature",
                factor=Fraction(5, 9),
                offset=Fraction(45_967, 180),
                source=Source(
                    citation=_SP811,
                    locator="Appendix B.8, t/°C = (t/°F - 32)/1.8, with section 2.3.1 "
                    "of the SI Brochure",
                    url=_SP811_URL,
                ),
            ),
        )
    }
)
"""The units table: every conversion a formula makes (CMP-4.3), exact."""


def _convert_number(number: float, factor: Fraction, offset: Fraction) -> float:
    """Return ``number * factor + offset`` correctly rounded."""
    if not math.isfinite(number):
        return number * float(factor) + float(offset)
    if offset == 0 and factor.numerator == 1 and factor.denominator <= _HUGE:
        return number / float(factor.denominator)
    if offset == 0 and factor.denominator == 1 and factor.numerator <= _HUGE:
        return number * float(factor.numerator)
    exact = Fraction(number) * factor + offset
    try:
        return float(exact)
    except OverflowError:
        return math.inf if exact > 0 else -math.inf


@overload
def convert(value: float, from_unit: str, to_unit: str) -> float: ...
@overload
def convert(
    value: NDArray[np.float64], from_unit: str, to_unit: str
) -> NDArray[np.float64]: ...
def convert(
    value: float | NDArray[np.float64], from_unit: str, to_unit: str
) -> float | NDArray[np.float64]:
    """Convert a value between units of the units table (CMP-4.3).

    The result is the exact conversion correctly rounded to float64, so a round
    trip returns the value within one unit in the last place; an affine one
    (temperature) within one unit in the last place of the value plus one of the
    converted value.

    Raises
    ------
    KeyError
        If a unit is not in :data:`UNITS`.
    ValueError
        If the units measure different quantities.
    """
    source, target = UNITS[from_unit], UNITS[to_unit]
    if source.quantity != target.quantity:
        raise ValueError(
            f"{from_unit} measures {source.quantity}, {to_unit} {target.quantity}"
        )
    factor = source.factor / target.factor
    offset = (source.offset - target.offset) / target.factor
    if not isinstance(value, np.ndarray):
        return _convert_number(float(value), factor, offset)
    array = np.asarray(value, dtype=np.float64)
    with np.errstate(over="ignore", under="ignore"):
        if offset == 0 and factor.numerator == 1 and factor.denominator <= _HUGE:
            return array / float(factor.denominator)
        if offset == 0 and factor.denominator == 1 and factor.numerator <= _HUGE:
            return array * float(factor.numerator)
    flat = (_convert_number(float(x), factor, offset) for x in array.ravel())
    return np.fromiter(flat, dtype=np.float64, count=array.size).reshape(array.shape)
