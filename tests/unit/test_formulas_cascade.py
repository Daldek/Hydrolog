"""The cascade of linear reservoirs against its spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5). No source
publishes a routed table of the cascade (NEH 630 ch. 17, the HEC-HMS TRM and EM
1110-2-1417 have none), so the formula is ``oracle only``: its limits hold the step
response of SciPy's ``gammainc``, the matrix exponential of the chain for whole ``n``
and the moments of the impulse response (CMP-6.2, CMP-6.3). The generic strategies
are refused only beyond float64, so they serve the properties without a hand-written
one.
"""

import numpy as np
import pytest
from hypothesis import example, given

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    assert_within,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.routing import CascadeReach, Hydrograph
from hydrolog.routing.formulas.cascade import LINEAR_RESERVOIR_CASCADE, cascade_route

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

SPEC = LINEAR_RESERVOIR_CASCADE
ROUTE = as_standard(cascade_route)


@pytest.mark.parametrize("case", range_cases(SPEC) + type_cases(SPEC))
def test_ranges_and_types(case: Case):
    run_case(SPEC, ROUTE, case, ERRORS)


def test_limits_and_oracles():
    assert_limits(SPEC, ROUTE, ERRORS)


@given(inputs=strategies(SPEC))
@example(
    inputs={
        "inflow_m3s": np.zeros(4),
        "timestep_min": 6.0,
        "n": 30.0,
        "k_min": 5.0,
        "initial_outflow_m3s": 0.0,
    }
)
@example(
    inputs={
        "inflow_m3s": np.zeros(2),
        "timestep_min": 5.0,
        "n": 1.0,
        "k_min": 5.0,
        "initial_outflow_m3s": 5e-324,
    }
)
@example(
    inputs={
        "inflow_m3s": np.array([1.0, 0.0, 0.0]),
        "timestep_min": 5.0,
        "n": 1.2477902272600502e-23,
        "k_min": 13.0,
        "initial_outflow_m3s": 0.0,
    }
)
@example(
    inputs={
        "inflow_m3s": np.zeros(4),
        "timestep_min": 5.0,
        "n": 18.0,
        "k_min": 17.0,
        "initial_outflow_m3s": 0.001953125,
    }
)
@example(
    inputs={
        "inflow_m3s": np.ones(4),
        "timestep_min": 5.0,
        "n": 29.0,
        "k_min": 5.0,
        "initial_outflow_m3s": 0.0,
    }
)
@example(
    inputs={
        "inflow_m3s": np.r_[1.0, np.zeros(30)],
        "timestep_min": 5.0,
        "n": 1.0,
        "k_min": 5.0,
        "initial_outflow_m3s": 0.0,
    }
)
def test_properties(inputs):
    assert_property_contract(SPEC, ROUTE, inputs, ERRORS)
    assert_properties(SPEC, ROUTE, inputs, ERRORS)


@pytest.mark.parametrize(
    ("step", "k_min", "inflow"),
    [
        (60.0, 1.0e-320, [1.0, 2.0]),
        (1.0e-320, 1.0, [1.0e6, 0.0]),
    ],
    ids=["ratio-overflows", "inflow-over-ratio-overflows"],
)
def test_a_step_ratio_beyond_float64_is_refused(step, k_min, inflow):
    """Trap difference_denominator: the weights divide by dt / K; a ratio that
    overflows, or under which an inflow overflows, is a failed precondition."""
    with pytest.raises(InvalidParameterError) as caught:
        cascade_route(inflow, step, 2.0, k_min, 0.0)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "representable"


def test_a_subnormal_number_of_reservoirs_is_refused():
    """Trap difference_denominator: SciPy's gammainc(5e-324, 1) is 0, not 1, so the
    kernel of a subnormal n would hold the water instead of passing it at once; it is
    a failed precondition (found by the properties: a step of 1 m3/s lost half its
    volume)."""
    with pytest.raises(InvalidParameterError) as caught:
        cascade_route([1.0, 1.0], 5.0, 5e-324, 5.0, 0.0)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "representable"


def test_the_smallest_normal_number_of_reservoirs_passes_the_inflow():
    """Trap difference_denominator: n = 2.2e-308 is a delay of nothing."""
    run = cascade_route([1.0, 3.0, 2.0], 5.0, 2.2250738585072014e-308, 5.0, 0.0)

    assert_within(
        run.outflow_m3s,
        [0.0, 3.0, 2.0],
        abs=1e-13,
        reason="P(n, x) is 1 and the kernel a unit impulse to rounding; the first "
        "ordinate is the initial outflow by convention",
    )


def test_an_outflow_that_rounds_below_zero_is_zero():
    """Defect found by the properties: for a cascade far longer than the series, the
    share P(n, x) - (1 - (V(x_j) - V(x_(j-1))) / a) of the first inflow ordinate is
    about 1e-20 and rounds to -3e-17, so the outflow came out at -3.1e-18 m3/s; every
    term is a discharge times a non-negative share, so it is set to zero."""
    run = cascade_route([100.0 / 1024.0] * 4, 6.0, 30.0, 5.0, 0.0)

    assert run.outflow_m3s.min() >= 0.0
    assert_within(
        run.outflow_m3s,
        [0.0, 0.0, 0.0, 0.0],
        abs=1e-16,
        reason="P(30, 3.6) is 1e-20; the share of the first ordinate cancels to its "
        "rounding, a few 1e-16, times the inflow of 0.1 m3/s",
    )


def test_a_cascade_that_has_released_nothing_holds_all_the_water():
    """Defect found by the properties: the storage at the end summed only the three
    newest segments when no weight within the series was above zero, taking a
    kernel that had not started for one that had ended: 600 m3 instead of 900 m3
    (a balance error of a third of the inflow); the outflow was right."""
    run = cascade_route([1.0] * 4, 5.0, 29.0, 5.0, 0.0)

    assert_within(
        run.storage_end_m3,
        3 * 5.0 * 60.0,
        rel=1e-14,
        reason="P(29, 3) is 1e-21: the reservoirs hold the 900 m3 that entered "
        "but for rounding",
    )


def test_a_tiny_step_ratio_keeps_the_initial_state():
    """Trap difference_denominator: dt / K = 1e-300 is accepted and finite, and the
    water has not moved: every outflow is the initial outflow."""
    run = cascade_route([3.0, 5.0, 9.0, 2.0], 1.0e-300, 2.0, 1.0, 4.0)

    assert_within(
        run.outflow_m3s,
        [4.0] * 4,
        rel=1e-15,
        reason="after three steps of 1e-300 K the released share P(n, x) is about "
        "1e-600, nothing in float64",
    )


def test_a_long_steady_inflow_stays_steady():
    """Trap many_small_terms: 200,000 ordinates, convolved by the FFT in blocks."""
    inflow = np.full(200_000, 0.001)

    run = cascade_route(inflow, 5.0, 4.0, 15.0, 0.001)

    assert_within(
        run.outflow_m3s,
        inflow,
        rel=1e-12,
        reason="the coefficients of every ordinate add up to one; the FFT of "
        "oaconvolve rounds each output at about 1e-16 times the kernel's length",
    )


def test_the_formula_records_its_version():
    with recording() as used:
        cascade_route([0.0, 1.0, 0.0], 10.0, 2.0, 20.0, 0.0)

    assert used == {"linear_reservoir_cascade": SPEC.formula_version}


def test_the_reach_routes_through_the_formula():
    inflow = Hydrograph.from_step([5.0, 20.0, 60.0, 35.0, 12.0, 5.0], 60.0)

    with recording() as used:
        result = CascadeReach(2.5, length_km=18.0, celerity_m_per_s=1.5).route(
            inflow, extend_min=0.0
        )
    run = cascade_route(inflow.discharge_m3s, 60.0, 2.5, 80.0, 5.0)

    assert used == {"linear_reservoir_cascade": SPEC.formula_version}
    assert result.outflow.discharge_m3s.tolist() == run.outflow_m3s.tolist()
    assert result.storage_end_m3 == run.storage_end_m3
