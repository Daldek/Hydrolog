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
``outside_typical_range``, whose ``method`` is the name of the spec: for an input
outside its applicability range ``parameter`` is the input; for a violated
applicability constraint it is the quantity the constraint bounds, which the formula
module declares beside its spec with :func:`constraint_range` (the number of
``gaugings`` of a rating curve), with the constraint's name, text and source. The
code is renamed together with its consumers, in one release (plan of the computation
standard, step 5). A formula with the status ``unreferenced`` gives on every result
the notice ``unreferenced_formula`` (CMP-5.1) at level ``info``,
:class:`~hydrolog._warnings.UnreferencedFormula`. :func:`checked_outputs` runs
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
import warnings
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final, cast

from hydrolog._formula_versions import record
from hydrolog._warnings import UnreferencedFormula, warn_outside_typical_range
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
    "ConstraintRange",
    "checked_inputs",
    "checked_outputs",
    "constraint_range",
    "constraint_ranges",
    "specs",
    "tier_b",
]

FORMULA_MODULES: Final[tuple[str, ...]] = (
    "hydrolog.runoff.scs_cn",
    "hydrolog.runoff.cn_lookup",
    "hydrolog.time.concentration",
    "hydrolog.morphometry.profile",
    "hydrolog.runoff.nash_iuh",
    "hydrolog.statistics.stationarity",
    "hydrolog.statistics.homogeneity",
    "hydrolog.statistics.duration",
    "hydrolog.statistics.events",
    "hydrolog.statistics.volumes",
    "hydrolog.statistics.baseflow",
    "hydrolog.statistics.regime",
    "hydrolog.statistics.seasonality",
    "hydrolog.statistics.harmonics",
    "hydrolog.statistics.characteristic",
    "hydrolog.statistics._hydrological_year",
    "hydrolog.hydrometrics.rating_curve",
)
"""The modules whose ``SPECS`` (and ``TIER_B``) declare Hydrolog's formulas, in the
order of ``docs/FORMULAS.md``."""

DELEGATED: Final[tuple[Delegated, ...]] = (
    Delegated(
        name="nash_shape_root",
        library="scipy.optimize.brentq",
        versions="scipy>=1.10 (1.18.1 locked)",
        smoke_case="the root N of f(N) = (N-1)^N e^-(N-1) / Gamma(N) = f(2.55) on "
        "[1.1, 20] with xtol 1e-6 is 2.55 within 1e-6 (spec lutz)",
        test="tests/unit/test_formulas_lutz.py::"
        "test_the_delegated_root_finder_finds_a_known_root",
    ),
    Delegated(
        name="lyne_hollick_recursion",
        library="scipy.signal.lfilter",
        versions="scipy>=1.10 (1.18.1 locked)",
        smoke_case="lfilter([(1 + a) / 2], [1, -a], diff(Q), zi=[a Q_1]) gives the "
        "quickflow q_t = a q_(t-1) + (1 + a)/2 (Q_t - Q_(t-1)) from q_1 = Q_1 of the "
        "first pass of Ladson et al. (2013), Table 4 (Bass River, a = 0.98): 155.46 "
        "after 96 and 158 (spec lyne_hollick)",
        test="tests/unit/test_formulas_baseflow.py::"
        "test_the_delegated_recursion_is_the_first_pass_of_table_4",
    ),
    Delegated(
        name="student_t_quantile",
        library="scipy.stats.t.isf",
        versions="scipy>=1.10 (1.18.1 locked)",
        smoke_case="the upper quantile of the tail 0.025 with one degree of freedom "
        "is tan(0.475 pi) = 12.7062047361747 within 1e-13 relative (spec "
        "mean_interval_half_width)",
        test="tests/unit/test_formulas_characteristic.py::"
        "test_the_delegated_t_quantile_is_a_known_one",
    ),
    Delegated(
        name="mann_whitney_u",
        library="scipy.stats.mannwhitneyu (two-sided, method auto: exact for parts of "
        "at most 8 values without ties, else normal with the corrections for ties "
        "and continuity)",
        versions="scipy>=1.10 (1.18.1 locked)",
        smoke_case="Helsel et al. (2020), Example 5.1: U of the first part 76.5, p = "
        "0.04911 (R's wilcox.test W = 76.5, p = 0.0491099747); the frozen oracle "
        "tests/oracles/trend_regime holds R's U and p of three pairs of samples "
        "(stats homogeneity)",
        test="tests/unit/test_formulas_trend.py::"
        "test_the_delegated_mann_whitney_is_helsels_and_rs",
    ),
    Delegated(
        name="ks_two_sample",
        library="scipy.stats.ks_2samp (two-sided, method auto: exact for a continuous "
        "distribution)",
        versions="scipy>=1.10 (1.18.1 locked)",
        smoke_case="three values all below four others: D = 1, p = 2 / C(7, 3) = "
        "0.0571429; seeded samples without ties against the exact count of spec "
        "ks_exact (stats homogeneity without ties)",
        test="tests/unit/test_formulas_trend.py::"
        "test_the_delegated_ks_2samp_is_exact_without_ties",
    ),
    Delegated(
        name="rating_curve_least_squares",
        library="scipy.optimize.curve_fit (bounds: least_squares, trust region "
        "reflective)",
        versions="scipy>=1.10 (1.18.1 locked)",
        smoke_case="eight noise-free pairs of Q = 0.012 (H - 32)^1.62 at H = 40 to "
        "270 cm give back a = 0.012, b = 1.62 and H0 = 32 cm within 1e-6 relative "
        "(spec rating_curve_fit)",
        test="tests/unit/test_formulas_hydrometrics.py::"
        "test_the_delegated_least_squares_recover_a_noise_free_curve",
    ),
    Delegated(
        name="harmonic_least_squares",
        library="numpy.linalg.lstsq (LAPACK gelsd)",
        versions="numpy>=1.24 (2.5.4 locked)",
        smoke_case="the least squares of an exact signal of two harmonics over five "
        "hydrological years recover its mean 10 and amplitudes 5 and 2 within 1e-8 "
        "(spec harmonic_fit)",
        test="tests/unit/test_formulas_regime.py::"
        "test_the_delegated_least_squares_recover_an_exact_signal",
    ),
)
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


@dataclass(frozen=True, kw_only=True)
class ConstraintRange:
    """The range an applicability constraint of a formula puts on a quantity.

    A violated applicability constraint (CMP-3.3) is issued as the notice
    ``outside_typical_range`` of that quantity, as an input outside its range is.

    Attributes
    ----------
    formula, constraint : str
        The spec's name and the name of its applicability constraint.
    parameter : str
        The quantity the constraint bounds, as the notice names it (``gaugings``).
    value : callable
        Its value from the checked inputs.
    minimum, maximum : float or None
        Its range, bounds included; ``None`` for an end without a bound.
    """

    formula: str
    constraint: str
    parameter: str
    value: Callable[[Values], float]
    minimum: float | None = None
    maximum: float | None = None


_CONSTRAINT_RANGES: dict[tuple[str, str], ConstraintRange] = {}


def constraint_range(
    spec: FormulaSpec,
    constraint: str,
    *,
    parameter: str,
    value: Callable[[Values], float],
    minimum: float | None = None,
    maximum: float | None = None,
) -> ConstraintRange:
    """Declare the range an applicability constraint of a spec puts on a quantity.

    A formula module declares it beside the spec, once; :func:`checked_inputs` names
    the quantity, its value and its range in the notice of the violated constraint.

    Parameters
    ----------
    spec : FormulaSpec
        The formula's spec.
    constraint : str
        The name of its applicability constraint.
    parameter : str
        The quantity the constraint bounds.
    value : callable
        Its value from the checked inputs.
    minimum, maximum : float or None, optional
        Its range, bounds included; at least one is given.

    Returns
    -------
    ConstraintRange
        The declaration, registered for :func:`checked_inputs`.

    Raises
    ------
    ValueError
        If the spec has no applicability constraint of that name, no bound is given,
        or the range was declared before.
    """
    found = [c for c in spec.constraints if c.name == constraint]
    if not found or found[0].cls != "applicability":
        raise ValueError(f"{spec.name} has no applicability constraint {constraint!r}")
    if minimum is None and maximum is None:
        raise ValueError(f"{spec.name}.{constraint}: give minimum, maximum or both")
    key = (spec.name, constraint)
    if key in _CONSTRAINT_RANGES:
        raise ValueError(f"{spec.name}.{constraint}: its range is declared already")
    declared = ConstraintRange(
        formula=spec.name,
        constraint=constraint,
        parameter=parameter,
        value=value,
        minimum=minimum,
        maximum=maximum,
    )
    _CONSTRAINT_RANGES[key] = declared
    return declared


def constraint_ranges() -> Mapping[tuple[str, str], ConstraintRange]:
    """Return the declared ranges of applicability constraints by (spec, constraint).

    Returns
    -------
    Mapping
        Read-only view of the declarations of the imported formula modules.
    """
    return dict(_CONSTRAINT_RANGES)


def _bound(bounds: Mapping[str, object], end: str) -> float | None:
    """Return an inclusive end of a range's details; ``None`` where it has none."""
    number = bounds.get(end)
    if number is None:
        return None
    if not bounds.get(f"{end}_inclusive"):
        raise TypeError(f"the {end} end {number} of an applicability range is open")
    return cast("float", number)


def _issue(spec: FormulaSpec, notice: Notice, values: Values) -> None:
    """Warn of a notice of ``validate`` as the library warns, for the formula's caller.

    Raises
    ------
    TypeError
        For a notice the library has no warning for: an applicability range with an
        open finite end, or a violated applicability constraint whose range is not
        declared (:func:`constraint_range`).
    """
    details = notice.details
    if notice.code == "unreferenced_formula":
        warnings.warn(
            UnreferencedFormula(
                formula=spec.name,
                title=spec.title,
                formula_version=spec.formula_version,
            ),
            stacklevel=4,
        )
        return
    variable = details.get("variable")
    if notice.code == "outside_applicability" and isinstance(variable, str):
        bounds = details.get("range")
        if not isinstance(bounds, Mapping):
            raise TypeError(f"{spec.name}: {variable} has no applicability range")
        warn_outside_typical_range(
            spec.name,
            variable,
            cast("float", details["value"]),
            _bound(bounds, "low"),
            _bound(bounds, "high"),
            stacklevel=4,
        )
        return
    constraint = details.get("constraint")
    declared = (
        _CONSTRAINT_RANGES.get((spec.name, constraint))
        if notice.code == "outside_applicability" and isinstance(constraint, str)
        else None
    )
    if declared is None:
        raise TypeError(f"{spec.name}: no warning of the library for {details}")
    warn_outside_typical_range(
        spec.name,
        declared.parameter,
        declared.value(values),
        declared.minimum,
        declared.maximum,
        constraint=declared.constraint,
        condition=cast("str", details["text"]),
        source=cast("str", details["source"]),
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
        For each input outside its applicability range and each violated
        applicability constraint, in the order of the spec (``method`` the spec's
        name, ``parameter`` the input or the quantity the constraint bounds).
    UnreferencedFormula
        On every result of a formula with the status ``unreferenced`` (CMP-5.1).
    """
    values, notices = validate(spec, inputs, errors=ERRORS)
    for notice in notices:
        _issue(spec, notice, values)
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
