"""The design hyetographs against their specs (Nogat CMP §6): generated and published.

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/hyetographs-cases.json`` (CMP-6.1); the
limits hold the exact and algorithmic oracles (CMP-6.2). The functions are given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

import itertools
import math
import operator
from fractions import Fraction
from pathlib import Path
from typing import cast

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from scipy.special import betainc

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    ReferenceCase,
    assert_case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    assert_within,
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.precipitation import (
    BetaHietogram,
    BlockHietogram,
    EulerIIHietogram,
    TriangularHietogram,
)
from hydrolog.precipitation.hietogram import (
    BETA,
    BLOCK,
    EULER_II,
    TRIANGULAR,
    beta_hyetograph,
    block_hyetograph,
    euler_ii_hyetograph,
    triangular_hyetograph,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "hyetographs-cases.json"
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (BLOCK, block_hyetograph),
    (TRIANGULAR, triangular_hyetograph),
    (BETA, beta_hyetograph),
    (EULER_II, euler_ii_hyetograph),
)
NAMES = [spec.name for spec, _ in FAMILY]
STORMS = FAMILY[:3]
"""The specs of a total, a duration and a step (and their shape)."""


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


def _published() -> list[object]:
    return [
        pytest.param(spec, function, case, id=f"{spec.name}-{case.case_id}")
        for spec, function in FAMILY
        for case in load_cases(CASES, spec.name)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function", "case"), _published())
def test_reference_cases(spec: FormulaSpec, function, case: ReferenceCase):
    assert_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=NAMES)
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


@given(inputs=strategies(BLOCK))
def test_block_properties(inputs):
    assert_property_contract(BLOCK, as_standard(block_hyetograph), inputs, ERRORS)
    assert_properties(BLOCK, as_standard(block_hyetograph), inputs, ERRORS)


@given(inputs=strategies(TRIANGULAR))
def test_triangular_properties(inputs):
    function = as_standard(triangular_hyetograph)
    assert_property_contract(TRIANGULAR, function, inputs, ERRORS)
    assert_properties(TRIANGULAR, function, inputs, ERRORS)


@given(inputs=strategies(BETA))
def test_beta_properties(inputs):
    assert_property_contract(BETA, as_standard(beta_hyetograph), inputs, ERRORS)
    assert_properties(BETA, as_standard(beta_hyetograph), inputs, ERRORS)


@given(inputs=strategies(EULER_II))
def test_euler_ii_properties(inputs):
    function = as_standard(euler_ii_hyetograph)
    assert_property_contract(EULER_II, function, inputs, ERRORS)
    assert_properties(EULER_II, function, inputs, ERRORS)


def _with_whole_steps(drawn: tuple[dict[str, object], int]) -> dict[str, object]:
    inputs, steps = drawn
    return {**inputs, "duration_min": steps * cast(float, inputs["timestep_min"])}


def _whole_steps(spec: FormulaSpec) -> st.SearchStrategy[dict[str, object]]:
    """The spec's draws with the duration a whole number of the drawn step."""
    return st.tuples(strategies(spec), st.integers(1, 400)).map(_with_whole_steps)


@pytest.mark.parametrize(("spec", "function"), STORMS, ids=NAMES[:3])
def test_storms_of_whole_steps_keep_their_properties(spec: FormulaSpec, function):
    """Hand-written: the generator draws the duration and the step apart, so nearly
    every draw fails the precondition whole_steps; here the duration is a whole
    number of the drawn step and the properties are exercised."""

    @given(inputs=_whole_steps(spec))
    def check(inputs):
        assert_property_contract(spec, as_standard(function), inputs, ERRORS)
        assert_properties(spec, as_standard(function), inputs, ERRORS)

    check()


@st.composite
def _curves(draw: st.DrawFn) -> dict[str, object]:
    """A depth-duration curve of increasing durations and depths, and a storm of whole
    steps within it."""
    count = draw(st.integers(1, 10))
    first = draw(st.floats(0.5, 60.0))
    ratios = draw(
        st.lists(st.floats(1.05, 4.0), min_size=count - 1, max_size=count - 1)
    )
    durations = list(itertools.accumulate([first, *ratios], operator.mul))
    increments = draw(st.lists(st.floats(0.0, 150.0), min_size=count, max_size=count))
    depths = list(itertools.accumulate(increments))
    divisor = draw(st.integers(1, 3))
    step = first / divisor
    steps = draw(st.integers(1, min(600, max(1, math.floor(durations[-1] / step)))))
    return {
        "durations_min": durations,
        "depths_mm": depths,
        "duration_min": steps * step,
        "timestep_min": step,
    }


@given(inputs=_curves())
def test_euler_ii_storms_of_valid_curves_keep_their_properties(inputs):
    """Hand-written: the generator draws the durations and depths element by element,
    so nearly every draw is refused as a curve; here the curve increases and covers
    the storm, and the properties (the windows around the peak among them) are
    exercised."""
    function = as_standard(euler_ii_hyetograph)
    assert_property_contract(EULER_II, function, inputs, ERRORS)
    assert_properties(EULER_II, function, inputs, ERRORS)


@pytest.mark.parametrize(
    ("spec", "function", "shape"),
    [
        (BLOCK, block_hyetograph, {}),
        (TRIANGULAR, triangular_hyetograph, {"peak_position": 0.38}),
        (BETA, beta_hyetograph, {"alpha": 2.0, "beta": 5.0}),
    ],
    ids=lambda x: getattr(x, "name", ""),
)
def test_a_storm_of_a_million_steps_holds_its_total(spec, function, shape):
    """Trap many_small_terms: the largest storm the spec takes against its total."""
    storm = function(total_mm=341.27, duration_min=1.0e6, timestep_min=1.0, **shape)

    assert storm.intensities_mm.size == 1_000_000
    assert_within(
        math.fsum(storm.intensities_mm),
        341.27,
        abs=1e-9,
        reason="a million rounded shares of 341.27 mm summed exactly: at most a few "
        "units in the last place of the total",
    )


def test_a_storm_of_more_than_a_million_steps_is_refused_before_it_is_made():
    """The number of steps had no bound: 0.3 min in steps of 1e-7 min allocated three
    million floats; the spec's precondition steps_representable refuses it."""
    with pytest.raises(InvalidParameterError) as caught:
        block_hyetograph(total_mm=10.0, duration_min=0.3, timestep_min=1e-7)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "steps_representable"


def test_the_delegated_incomplete_beta_is_the_closed_form():
    """CMP-1.2: SciPy's regularised incomplete Beta function, delegated by
    beta_hyetograph, at x = 1/4 of (2, 5): 1 - (3/4)^6 - 6 (1/4) (3/4)^5 = 1909/4096."""
    assert_within(
        float(betainc(2.0, 5.0, 0.25)),
        float(Fraction(1909, 4096)),
        rel=4e-16,
        reason="1909/4096 is exact in binary; SciPy's betainc is within an ulp",
    )


def test_the_generators_compute_through_the_specs_and_record_their_versions():
    curve = {5: 21.82, 10: 25.68, 15: 28.22, 30: 33.23, 45: 36.58, 60: 39.16}
    with recording() as used:
        BlockHietogram().generate(30.0, 60.0)
        TriangularHietogram(0.4).generate(30.0, 60.0)
        BetaHietogram(2.0, 5.0).generate(30.0, 60.0)
        EulerIIHietogram(curve).generate(39.16, 60.0)

    assert used == {
        spec.name: spec.formula_version for spec in (BLOCK, TRIANGULAR, BETA, EULER_II)
    }


def test_the_euler_ii_generator_gives_the_storm_of_the_spec():
    curve = {5: 9.513, 10: 13.95, 15: 16.947, 20: 19.176, 30: 22.392, 60: 27.9}
    storm = EulerIIHietogram(curve).generate(27.9, 60.0, 5.0)
    spec = euler_ii_hyetograph(list(curve), list(curve.values()), 60.0, 5.0)

    assert storm.intensities_mm.tolist() == spec.intensities_mm.tolist()
    assert spec.peak_start_min == 15.0
    assert np.argmax(storm.intensities_mm) == 3
