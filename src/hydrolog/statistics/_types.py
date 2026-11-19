"""Shared dataclasses of the statistics module and the empirical plotting positions.

The plotting positions of a sample are formulas declared by their specs (Nogat's
computation standard, ADR-0050): the exceedance probabilities and return periods of
annual maxima ranked from the largest (:data:`PLOTTING_POSITIONS`,
:func:`compute_plotting_positions`) and the non-exceedance probabilities and return
periods of annual minima ranked from the smallest (:data:`NON_EXCEEDANCE_POSITIONS`,
:func:`compute_non_exceedance_positions`), by the formula of Weibull, Hazen or
Cunnane. ``docs/FORMULAS.md`` shows their equations, constants, ranges and sources.

Examples
--------
>>> from hydrolog.statistics._types import (
...     compute_non_exceedance_positions,
...     compute_plotting_positions,
... )
>>> maxima = compute_plotting_positions([10.0, 40.0, 20.0, 30.0])
>>> maxima.values_sorted.tolist(), maxima.exceedance_prob.tolist()
([40.0, 30.0, 20.0, 10.0], [0.2, 0.4, 0.6, 0.8])
>>> maxima.return_periods.tolist()
[5.0, 2.5, 1.6666666666666667, 1.25]
>>> minima = compute_non_exceedance_positions([10.0, 40.0, 20.0, 30.0], "hazen")
>>> minima.values_ascending.tolist(), minima.non_exceedance_probabilities.tolist()
([10.0, 20.0, 30.0, 40.0], [0.125, 0.375, 0.625, 0.875])
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.nogat_formulas import (
    Constant,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    Symmetry,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics.frequency import (
    _ANY_VALUE,
    _KZGW,
    _KZGW_URL,
    _MAXIMA,
    _MINIMA,
    _UNIT,
    _WMO_168,
    _WMO_168_URL,
    _WMO_1029,
    _WMO_1029_URL,
)

__all__ = [
    "NON_EXCEEDANCE_POSITIONS",
    "PLOTTING_POSITIONS",
    "SPECS",
    "EmpiricalFrequency",
    "LowFlowEmpiricalFrequency",
    "compute_non_exceedance_positions",
    "compute_plotting_positions",
]


@dataclass
class EmpiricalFrequency(JsonResultMixin):
    """Empirical frequency (plotting positions).

    For high flows: the values are sorted in descending order and the positions
    are *exceedance* probabilities (the largest value has the smallest one). For
    low flows use :class:`LowFlowEmpiricalFrequency`, whose positions are
    non-exceedance probabilities.

    Parameters
    ----------
    values_sorted : NDArray[np.float64]
        Values sorted in descending order.
    exceedance_prob : NDArray[np.float64]
        Exceedance probability for each value.
    return_periods : NDArray[np.float64]
        Return period T = 1/P for each value.
    """

    values_sorted: NDArray[np.float64]
    exceedance_prob: NDArray[np.float64]
    return_periods: NDArray[np.float64]


@dataclass
class LowFlowEmpiricalFrequency(JsonResultMixin):
    """Empirical non-exceedance frequency of low flows (plotting positions).

    The counterpart of :class:`EmpiricalFrequency` for a sample of minima. In a
    low-flow analysis the return period *T* belongs to the *non-exceedance*
    probability ``F = 1 / T`` (the flow is equalled or undercut once in *T*
    years; WMO No. 1029, 2009; Tallaksen and van Lanen, 2004), the convention of
    the fitted distribution (:class:`~hydrolog.statistics.LowFlowFrequencyResult`).
    So the values are sorted ascending and the smallest value, the deepest low
    flow, has the smallest probability and the longest return period.

    Parameters
    ----------
    values_ascending : NDArray[np.float64]
        Values sorted in ascending order (the smallest first).
    non_exceedance_probabilities : NDArray[np.float64]
        Non-exceedance probability *F* of each value: the share of years whose
        minimum is equal to or lower than the value. For the Weibull plotting
        position ``F = m / (n + 1)`` with rank ``m = 1`` for the smallest value.
    return_periods : NDArray[np.float64]
        Return period ``T = 1 / F`` [years] of each value, in the same sense as
        ``LowFlowFrequencyResult.return_periods``.
    """

    values_ascending: NDArray[np.float64]
    non_exceedance_probabilities: NDArray[np.float64]
    return_periods: NDArray[np.float64]


# --- the plotting positions ---------------------------------------------------------

_A: Final = {"weibull": Fraction(0), "hazen": Fraction(1, 2), "cunnane": Fraction(2, 5)}
"""The constant a of each plotting position formula (i - a) / (n + 1 - 2a)."""

_WMO_168_POSITIONS: Final = Source(
    citation=_WMO_168,
    locator="sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith "
    "largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula "
    "(i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n",
    url=_WMO_168_URL,
)
_WMO_1029_POSITIONS: Final = Source(
    citation=_WMO_1029,
    locator="sect. 7.3, eq. 7.3, p. 59: P_i = (i - a) / (n + 1 - 2a), the "
    "non-exceedance probability of the ith smallest of n events; p. 60: the Weibull "
    "formula is a = 0; sect. 7.8, step I, p. 65: the AM(7) values ranked ascending, "
    "the smallest rank 1, and the Weibull formula",
    url=_WMO_1029_URL,
)
_KZGW_POSITIONS: Final = Source(
    citation=_KZGW,
    locator="eq. 3.7, p. 29: p_i = i / (N + 1) 100 %, the empirical exceedance "
    "probability of the ith largest annual maximum; example 3.4, table 3.13, pp. "
    "54-55",
    url=_KZGW_URL,
)
_PLOTTING_CONSTANTS: Final = tuple(
    Constant(
        name=f"a_{method}", value=a, unit="-", symbol="a", source=_WMO_168_POSITIONS
    )
    for method, a in _A.items()
)

_METHOD: Final = Variable(
    name="method",
    symbol="a",
    unit="-",
    kind="choice",
    description="The plotting position formula: Weibull's, Hazen's or Cunnane's.",
    choices=tuple(_A),
)
_PROBABILITIES: Final = Range(
    low=0.0, high=1.0, low_inclusive=False, high_inclusive=False
)
_PERIODS: Final = Range(low=1.0, low_inclusive=False)
_EXACT_POSITIONS: Final = Tolerance(
    abs=0.0,
    reason="sorting, negating and doubling a sample are exact, and the positions "
    "depend on its size only",
)
_RATIONAL_SIZES: Final = (1, 2, 3, 4, 5, 10, 25, 30, 34, 1000, 10_000)
"""Sample sizes of the exact oracle: the examples' 25, 30 and 34 years among them."""


def _probabilities(spec: FormulaSpec, n: int, method: str) -> NDArray[np.float64]:
    """Return the positions (i - a) / (n + 1 - 2a) of the ranks i = 1 ... n."""
    a = spec.constant(f"a_{method}")
    ranks = np.arange(1, n + 1, dtype=np.float64)
    positions: NDArray[np.float64] = (ranks - a) / (n + 1 - 2.0 * a)
    return positions


def _rational_positions(probabilities: str) -> Callable[[Callable[..., Values]], None]:
    """Return the check of the positions against their exact rationals (fractions)."""

    def check(run: Callable[..., Values]) -> None:
        for n in _RATIONAL_SIZES:
            for method, a in _A.items():
                exact = [(i - a) / (n + 1 - 2 * a) for i in range(1, n + 1)]
                out = run(values=np.arange(n, dtype=np.float64), method=method)
                assert_within(
                    out.array(probabilities),
                    [float(p) for p in exact],
                    rel=4.5e-16,
                    reason="the exact rationals (i - a) / (n + 1 - 2a); the code "
                    "rounds i - a, n + 1 - 2a and their quotient, with a of 2/5 "
                    "stored within half an ulp",
                )
                assert_within(
                    out.array("return_periods"),
                    [float(1 / p) for p in exact],
                    rel=6.7e-16,
                    reason="the exact rationals (n + 1 - 2a) / (i - a); the code "
                    "takes one over the rounded position, one rounding more",
                )

    return check


def _positions_spec(
    *,
    name: str,
    title: str,
    function: str,
    ranked: str,
    values: Variable,
    outputs: tuple[Output, Output, Output],
    sources: tuple[Source, ...],
    conventions: tuple[str, ...],
    reference_case: str,
) -> FormulaSpec:
    """Return the spec of plotting positions of the sample ranked as ``ranked`` says."""
    ordered, probabilities, _ = (output.name for output in outputs)
    return FormulaSpec(
        name=name,
        title=title,
        function=function,
        family="statistic",
        equation=(
            f"p_i = (i - a) / (n + 1 - 2a) and T_i = 1 / p_i of the value of rank i = "
            f"1 ... n, {ranked}; a = 0 (Weibull, i / (n + 1)), 1/2 (Hazen, (i - 1/2) "
            "/ n) or 2/5 (Cunnane, (i - 2/5) / (n + 1/5))"
        ),
        latex=r"p_i = \frac{i - a}{n + 1 - 2a},\qquad T_i = \frac{1}{p_i}",
        variables=(values, _METHOD),
        outputs=outputs,
        sources=sources,
        constants=_PLOTTING_CONSTANTS,
        properties=Properties(
            units="homogeneous",
            monotonic={"values": 1},
            scalings=(
                Scaling(
                    name="unit_of_the_sample",
                    inputs={"values": 1.0},
                    outputs={ordered: 1.0},
                    tolerance=_EXACT_POSITIONS,
                ),
            ),
            symmetries=(
                Symmetry(
                    name="order",
                    text="the sample in the reverse order has the same positions",
                    inputs=lambda x: {**x, "values": x.array("values")[::-1]},
                    outputs=dict,
                    tolerance=_EXACT_POSITIONS,
                ),
                Symmetry(
                    name="mirror",
                    text="the negated sample has the negated values in the reverse "
                    "order and the same positions",
                    inputs=lambda x: {**x, "values": -x.array("values")},
                    outputs=lambda out: {**out, ordered: -out.array(ordered)[::-1]},
                    tolerance=_EXACT_POSITIONS,
                ),
            ),
            limits=(
                Limit(
                    name="exact_rational",
                    text="the positions and return periods of the definition in "
                    "exact rational arithmetic, for samples of 1 to 10,000 values",
                    check=_rational_positions(probabilities),
                ),
            ),
        ),
        validation="none: an estimate of the probability of each value of the "
        "ranked sample",
        formula_version=1,
        status="referenced",
        conventions=(
            *conventions,
            "the general form (i - a) / (n + 1 - 2a) of WMO-No. 1029 eq. 7.3 with "
            "the a of WMO-No. 168 sect. 5.6.1; no Gringorten formula",
            "tied values keep consecutive ranks, each with its own position, as KZGW "
            "2017 table 3.13 ranks its two values of 10.3 and of 7.88 m3/s",
            "the sample in any unit: the positions depend on the ranks only",
        ),
        traps={
            "singular_at_bound": "limit exact_rational: the return period one over "
            "the smallest position, about 1 / n, of up to 10,000 values; the "
            "positions never reach 0 or 1",
            "gap_propagation": "type case values-nan_element: a gap is refused",
        },
        reference_cases=(reference_case,),
        oracles=(
            Oracle(
                kind="exact",
                description="the positions and return periods in exact rational "
                "arithmetic (fractions)",
                test="tests/unit/test_formulas_flood_frequency.py (limit "
                "exact_rational)",
            ),
            Oracle(
                kind="established",
                description="scipy.stats.mstats.plotting_positions with alpha = beta "
                "= a",
                test="tests/unit/test_formulas_flood_frequency.py "
                "(test_the_plotting_positions_are_scipys)",
                conventions=(
                    "scipy gives (i - alpha) / (n + 1 - alpha - beta) of the ith "
                    "smallest value, in the order of the sample",
                    "the exceedance position of the ith largest value is the "
                    "position of the ith smallest of the negated sample",
                ),
            ),
        ),
    )


_CASES: Final = "tests/fixtures/formulas/flood-frequency-cases.json"

PLOTTING_POSITIONS: Final = _positions_spec(
    name="plotting_positions",
    title="Plotting positions of annual maxima: exceedance probabilities and return "
    "periods",
    function="hydrolog.statistics._types.compute_plotting_positions",
    ranked="ranked from the largest (rank 1)",
    values=Variable(
        name="values",
        symbol="x_{(i)}",
        unit=_UNIT,
        kind="real_array",
        description="The sample, annual maxima of a discharge or a stage.",
        physical=_ANY_VALUE,
        applicability="unstated",
        typical=_MAXIMA,
    ),
    outputs=(
        Output(
            name="values_sorted",
            unit=_UNIT,
            kind="real_array",
            symbol="x_{(i)}",
            description="The values in descending order.",
            physical=Range(),
        ),
        Output(
            name="exceedance_prob",
            unit="-",
            kind="real_array",
            symbol="p_i",
            description="The exceedance probability of each value.",
            physical=_PROBABILITIES,
        ),
        Output(
            name="return_periods",
            unit="years",
            kind="real_array",
            symbol="T_i",
            description="The return period of each value, exceeded once in T years.",
            physical=_PERIODS,
        ),
    ),
    sources=(_WMO_168_POSITIONS, _KZGW_POSITIONS, _WMO_1029_POSITIONS),
    conventions=(
        "the exceedance probability of the ith largest value, rank 1 the largest "
        "(WMO-No. 168 sect. 5.6.1; KZGW 2017 eq. 3.7, Polish p_i = i / (N + 1)); the "
        "return period T = 1 / p, as of the quantiles of the maxima",
    ),
    reference_case=_CASES,
)

NON_EXCEEDANCE_POSITIONS: Final = _positions_spec(
    name="non_exceedance_positions",
    title="Plotting positions of annual minima: non-exceedance probabilities and "
    "return periods",
    function="hydrolog.statistics._types.compute_non_exceedance_positions",
    ranked="ranked from the smallest (rank 1)",
    values=Variable(
        name="values",
        symbol="x_{(i)}",
        unit=_UNIT,
        kind="real_array",
        description="The sample, annual minima of a discharge or a stage.",
        physical=_ANY_VALUE,
        applicability="unstated",
        typical=_MINIMA,
    ),
    outputs=(
        Output(
            name="values_ascending",
            unit=_UNIT,
            kind="real_array",
            symbol="x_{(i)}",
            description="The values in ascending order.",
            physical=Range(),
        ),
        Output(
            name="non_exceedance_probabilities",
            unit="-",
            kind="real_array",
            symbol="F_i",
            description="The non-exceedance probability of each value.",
            physical=_PROBABILITIES,
        ),
        Output(
            name="return_periods",
            unit="years",
            kind="real_array",
            symbol="T_i",
            description="The return period of each value, undercut once in T years.",
            physical=_PERIODS,
        ),
    ),
    sources=(_WMO_1029_POSITIONS, _WMO_168_POSITIONS),
    conventions=(
        "the non-exceedance probability of the ith smallest value, rank 1 the "
        "smallest (WMO-No. 1029 eq. 7.3 and sect. 7.8, step I); the return period T = "
        "1 / F of a low flow undercut once in T years (WMO-No. 1029 eq. 7.14), as of "
        "the quantiles of fisher_tippett_minima",
    ),
    reference_case=_CASES,
)

SPECS: Final = (PLOTTING_POSITIONS, NON_EXCEEDANCE_POSITIONS)


def compute_plotting_positions(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
    method: str = "weibull",
) -> EmpiricalFrequency:
    """Return the exceedance plotting positions of a sample, spec plotting_positions.

    Parameters
    ----------
    values : array_like of float
        The sample, annual maxima: the largest gets the smallest probability.
    method : {"weibull", "hazen", "cunnane"}, optional
        The plotting position formula, by default ``"weibull"``.

    Returns
    -------
    EmpiricalFrequency
        The values in descending order with their exceedance probabilities and
        return periods.

    Raises
    ------
    InvalidParameterError
        If the inputs are refused by the spec: an empty sample, a value that is not
        finite or an unknown ``method``.
    """
    x = checked_inputs(PLOTTING_POSITIONS, values=values, method=method)
    descending = np.sort(x.array("values"))[::-1]
    exceedance = _probabilities(PLOTTING_POSITIONS, descending.size, x.choice("method"))
    out = checked_outputs(
        PLOTTING_POSITIONS,
        {
            "values_sorted": descending,
            "exceedance_prob": exceedance,
            "return_periods": 1.0 / exceedance,
        },
    )
    return EmpiricalFrequency(
        values_sorted=out.array("values_sorted"),
        exceedance_prob=out.array("exceedance_prob"),
        return_periods=out.array("return_periods"),
    )


def compute_non_exceedance_positions(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
    method: str = "weibull",
) -> LowFlowEmpiricalFrequency:
    """Return the non-exceedance positions of minima, spec non_exceedance_positions.

    The mirror image of :func:`compute_plotting_positions`: the smallest value, the
    deepest low flow, gets the smallest probability and the longest return period.

    Parameters
    ----------
    values : array_like of float
        The sample, annual minima.
    method : {"weibull", "hazen", "cunnane"}, optional
        The plotting position formula, by default ``"weibull"``.

    Returns
    -------
    LowFlowEmpiricalFrequency
        The values in ascending order with their non-exceedance probabilities and
        return periods.

    Raises
    ------
    InvalidParameterError
        If the inputs are refused by the spec: an empty sample, a value that is not
        finite or an unknown ``method``.
    """
    x = checked_inputs(NON_EXCEEDANCE_POSITIONS, values=values, method=method)
    ascending = np.sort(x.array("values"))
    non_exceedance = _probabilities(
        NON_EXCEEDANCE_POSITIONS, ascending.size, x.choice("method")
    )
    out = checked_outputs(
        NON_EXCEEDANCE_POSITIONS,
        {
            "values_ascending": ascending,
            "non_exceedance_probabilities": non_exceedance,
            "return_periods": 1.0 / non_exceedance,
        },
    )
    return LowFlowEmpiricalFrequency(
        values_ascending=out.array("values_ascending"),
        non_exceedance_probabilities=out.array("non_exceedance_probabilities"),
        return_periods=out.array("return_periods"),
    )
