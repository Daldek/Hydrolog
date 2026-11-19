"""The Muskingum scheme through equal sub-reaches against its spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/muskingum-cases.json`` (CMP-6.1); the
limits hold the exact rational recurrence and the moments of the impulse response
(CMP-6.2). The generic strategies draw ``K``, ``X``, ``N`` and the step apart, so most
of their points lie outside the window of non-negative weights, which the spec refuses:
the hand-written strategy :func:`grids` draws points inside it, for the properties.
"""

from pathlib import Path

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import given
from hypothesis.extra.numpy import arrays

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
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
from hydrolog.routing import Hydrograph, MuskingumReach
from hydrolog.routing.formulas.muskingum import MUSKINGUM, muskingum_route

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "muskingum-cases.json"
ROUTE = as_standard(muskingum_route)


@pytest.mark.parametrize("case", range_cases(MUSKINGUM) + type_cases(MUSKINGUM))
def test_ranges_and_types(case: Case):
    run_case(MUSKINGUM, ROUTE, case, ERRORS)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in load_cases(CASES, "muskingum")]
)
def test_reference_cases(case: ReferenceCase):
    assert_case(MUSKINGUM, ROUTE, case, ERRORS)


def test_limits_and_oracles():
    assert_limits(MUSKINGUM, ROUTE, ERRORS)


@given(inputs=strategies(MUSKINGUM))
def test_properties(inputs):
    assert_property_contract(MUSKINGUM, ROUTE, inputs, ERRORS)
    assert_properties(MUSKINGUM, ROUTE, inputs, ERRORS)


@st.composite
def grids(draw) -> dict[str, object]:
    """Points inside the window: N, X and dt / (K / N) between 2X and 2(1 - X)."""
    count = draw(st.integers(min_value=2, max_value=60))
    flows = st.floats(min_value=0.0, max_value=1000.0)
    weight = draw(st.floats(min_value=0.0, max_value=0.5))
    ratio = draw(st.floats(min_value=max(2.0 * weight, 0.01), max_value=2 - 2 * weight))
    step = draw(st.floats(min_value=1.0, max_value=720.0))
    subreaches = draw(st.integers(min_value=1, max_value=10))
    return {
        "inflow_m3s": draw(arrays(np.float64, count, elements=flows)),
        "timestep_min": step,
        "k_min": subreaches * step / ratio,
        "x": weight,
        "subreaches": subreaches,
        "initial_outflow_m3s": draw(flows),
    }


@given(inputs=grids())
def test_properties_inside_the_window(inputs):
    assert_property_contract(MUSKINGUM, ROUTE, inputs, ERRORS)
    assert_properties(MUSKINGUM, ROUTE, inputs, ERRORS)


def test_a_border_of_the_window_rounds_to_zero_weights():
    """Trap stability_bound: K = 3 x 0.1 rounds up, so K / N with N = 3 is a unit in
    the last place above dt = 0.1 and 2 (K/N) X lies above dt on the lower border:
    the weight of I[t], -6.9e-17 as computed, is set to zero, so the outflow is the
    lag of one step per sub-reach and never below zero."""
    inflow = [0.0, 5.0, 20.0, 1.0e3, 7.0, 0.0]

    run = muskingum_route(inflow, 0.1, 3 * 0.1, 0.5, 3, 0.0)

    assert run.c_current == 0.0
    assert min(run.c_previous, run.c_outflow) >= 0.0
    assert run.outflow_m3s.min() >= 0.0
    assert_within(
        run.outflow_m3s,
        [0.0, 0.0, 0.0, 0.0, 5.0, 20.0],
        rel=1e-15,
        abs=1e-12,
        reason="three sub-reaches of a lag of one step each: c_previous is 1 and "
        "c_outflow 0 to a unit in the last place",
    )


def test_a_step_outside_the_window_is_refused():
    """Trap stability_bound: dt above 2K(1 - X)/N is a failed precondition."""
    with pytest.raises(InvalidParameterError) as caught:
        muskingum_route([1.0, 2.0, 3.0], 61.0, 60.0, 0.5, 1, 1.0)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "nonnegative_weights"


def test_a_long_steady_inflow_stays_steady():
    """Trap many_small_terms: 200,000 ordinates of a steady inflow stay steady."""
    inflow = np.full(200_000, 0.001)

    run = muskingum_route(inflow, 5.0, 60.0, 0.2, 12, 0.001)

    assert_within(
        run.outflow_m3s,
        inflow,
        rel=1e-14,
        reason="the weights sum to 1 to rounding and c_outflow < 1 damps the error of "
        "each step: it cannot grow along the series",
    )


def test_the_formula_records_its_version():
    with recording() as used:
        muskingum_route([0.0, 1.0, 0.0], 10.0, 20.0, 0.2, 2, 0.0)

    assert used == {"muskingum": MUSKINGUM.formula_version}


def test_the_reach_routes_through_the_formula():
    inflow = Hydrograph.from_step([100.0, 300.0, 680.0, 500.0], 720.0)

    with recording() as used:
        result = MuskingumReach(k_min=1200.0, x=0.25, subreaches=1).route(
            inflow, extend_min=0.0
        )
    run = muskingum_route(inflow.discharge_m3s, 720.0, 1200.0, 0.25, 1, 100.0)

    assert used == {"muskingum": MUSKINGUM.formula_version}
    assert result.outflow.discharge_m3s.tolist() == run.outflow_m3s.tolist()
    assert result.storage_end_m3 == run.storage_end_m3
