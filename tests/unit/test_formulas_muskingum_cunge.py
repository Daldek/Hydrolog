"""Muskingum-Cunge routing and Manning's normal flow against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs ``muskingum_cunge`` and
``manning_normal_flow`` (CMP-6.5); the reference cases are those of
``tests/fixtures/formulas/muskingum-cunge-cases.json`` (CMP-6.1): NEH 630 chapter 17's
example 17-4 and the rows of its Table 17-16; the limits hold the exact rational
recurrence in Ponce's form, the moments of the diffusion wave, the closed form of a
triangle and Manning's equation at fifty digits (CMP-6.2). The generic strategies of
``muskingum_cunge`` draw the reach and the step apart, so nearly all of their points lie
outside the window of non-negative weights, which the spec refuses: the hand-written
strategy :func:`grids` draws points inside it, for the properties.
"""

import math
from pathlib import Path

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import example, given
from hypothesis.extra.numpy import arrays
from scipy.optimize import brentq

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
    convert,
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.routing import Hydrograph, MuskingumCungeReach, TrapezoidalSection
from hydrolog.routing.formulas.cunge import (
    MUSKINGUM_CUNGE,
    distance_step_window,
    muskingum_cunge_route,
)
from hydrolog.routing.formulas.manning import MANNING_NORMAL_FLOW, normal_flow

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

CASES = (
    Path(__file__).parents[1] / "fixtures" / "formulas" / "muskingum-cunge-cases.json"
)
ROUTE = as_standard(muskingum_cunge_route)
FLOW = as_standard(normal_flow)
FUNCTIONS = {MUSKINGUM_CUNGE.name: ROUTE, MANNING_NORMAL_FLOW.name: FLOW}


def _generated(spec: FormulaSpec) -> list:
    return [
        pytest.param(spec, c.values[0], id=f"{spec.name}-{c.id}")
        for c in range_cases(spec) + type_cases(spec)
    ]


def _cases(spec: FormulaSpec) -> list:
    return [pytest.param(spec, c, id=c.case_id) for c in load_cases(CASES, spec.name)]


@pytest.mark.parametrize(
    ("spec", "case"), _generated(MUSKINGUM_CUNGE) + _generated(MANNING_NORMAL_FLOW)
)
def test_ranges_and_types(spec: FormulaSpec, case: Case):
    run_case(spec, FUNCTIONS[spec.name], case, ERRORS)


@pytest.mark.parametrize(
    ("spec", "case"), _cases(MUSKINGUM_CUNGE) + _cases(MANNING_NORMAL_FLOW)
)
def test_reference_cases(spec: FormulaSpec, case: ReferenceCase):
    assert_case(spec, FUNCTIONS[spec.name], case, ERRORS)


@pytest.mark.parametrize(
    "spec", [MUSKINGUM_CUNGE, MANNING_NORMAL_FLOW], ids=lambda spec: spec.name
)
def test_limits_and_oracles(spec: FormulaSpec):
    assert_limits(spec, FUNCTIONS[spec.name], ERRORS)


@given(inputs=strategies(MUSKINGUM_CUNGE))
def test_properties_of_the_routing(inputs):
    assert_property_contract(MUSKINGUM_CUNGE, ROUTE, inputs, ERRORS)
    assert_properties(MUSKINGUM_CUNGE, ROUTE, inputs, ERRORS)


@given(inputs=strategies(MANNING_NORMAL_FLOW))
@example(  # a subnormal depth, which representable_flow refuses: no scaling then
    inputs={
        "discharge_m3s": 5e-324,
        "slope_m_per_m": 0.015625,
        "bottom_width_m": 1.0,
        "side_slope_m_per_m": 0.0,
        "manning_n": 9.409615755365123e-200,
    }
)
def test_properties_of_the_normal_flow(inputs):
    assert_property_contract(MANNING_NORMAL_FLOW, FLOW, inputs, ERRORS)
    assert_properties(MANNING_NORMAL_FLOW, FLOW, inputs, ERRORS)


@st.composite
def grids(draw) -> dict[str, object]:
    """Points inside the window: Cg and Dg with |Cg - Dg| <= 1 <= Cg + Dg."""
    count = draw(st.integers(min_value=2, max_value=60))
    flows = st.floats(min_value=0.0, max_value=1000.0)
    subreaches = draw(st.integers(min_value=1, max_value=8))
    dx = draw(st.floats(min_value=1.0, max_value=20_000.0))
    courant = draw(st.floats(min_value=1e-3, max_value=50.0))
    reynolds = draw(
        st.floats(min_value=max(abs(1.0 - courant), 1e-3), max_value=1.0 + courant)
    )
    celerity = draw(st.floats(min_value=0.05, max_value=10.0))
    slope = draw(st.floats(min_value=1e-4, max_value=0.05))
    width = draw(st.floats(min_value=1.0, max_value=1000.0))
    return {
        "inflow_m3s": draw(arrays(np.float64, count, elements=flows)),
        "timestep_min": convert(courant * dx / celerity, "s", "min"),
        "length_km": convert(dx * subreaches, "m", "km"),
        "slope_m_per_m": slope,
        "celerity_m_per_s": celerity,
        "top_width_m": width,
        "reference_discharge_m3s": reynolds * dx * width * slope * celerity,
        "subreaches": subreaches,
        "initial_outflow_m3s": draw(flows),
    }


@given(inputs=grids())
@example(  # subnormal volumes: the residual's floor of the smallest normal float
    inputs={
        "inflow_m3s": np.array([5e-324, 5e-324]),
        "timestep_min": 0.5333333333333333,
        "length_km": 0.001,
        "slope_m_per_m": 0.03125,
        "celerity_m_per_s": 0.0625,
        "top_width_m": 1.0,
        "reference_discharge_m3s": 0.001953125,
        "subreaches": 1,
        "initial_outflow_m3s": 0.0,
    }
)
def test_properties_inside_the_window(inputs):
    assert_property_contract(MUSKINGUM_CUNGE, ROUTE, inputs, ERRORS)
    assert_properties(MUSKINGUM_CUNGE, ROUTE, inputs, ERRORS)


@given(inputs=grids())
def test_every_grid_inside_the_window_is_inside_the_accuracy_limit(inputs):
    """NEH eq. 17-36 on the drawn grids: |Cg - Dg| <= 1 gives Dg <= exp(2.3 Cg), to
    the window's slack (the limit inside_the_accuracy_limit holds chosen borders)."""
    try:
        run = muskingum_cunge_route(**inputs)
    except InvalidParameterError as refused:
        assert refused.details["reason"] == "precondition_failed"
        return

    assert run.grid_reynolds_number <= run.grid_reynolds_limit + 2e-9


def test_a_border_of_the_window_rounds_to_zero_weights():
    """Trap stability_bound: dx = c dt + D puts the weight of I[t] on zero, which the
    weights of K and X compute as -2.7e-17: it is set to zero, so the outflow is the
    recurrence of the other two weights, C = c dt / dx and 1 - C, and never negative."""
    inflow = [0.0, 5.0, 20.0, 1.0e3, 7.0, 0.0]

    run = muskingum_cunge_route(inflow, 5.0, 0.3, 0.001, 0.3, 10.0, 0.63, 1, 0.0)

    assert run.c_current == 0.0
    assert run.outflow_m3s.min() >= 0.0
    expected = [0.0]
    for previous in inflow[:-1]:
        expected.append(0.3 * previous + 0.7 * expected[-1])
    assert_within(
        run.outflow_m3s,
        expected,
        rel=1e-14,
        abs=1e-12,
        reason="the kept weights, divided by their sum, are 0.3 and 0.7 to a few units "
        "in the last place, over five steps",
    )


def test_a_grid_outside_the_window_is_refused():
    """Trap stability_bound: dx above c dt + D (Cg + Dg < 1) fails the precondition."""
    with pytest.raises(InvalidParameterError) as caught:
        muskingum_cunge_route([1.0, 2.0, 3.0], 4.9, 2.6, 0.001, 1.0, 20.0, 20.0, 2, 1.0)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "nonnegative_weights"


def test_a_wave_as_long_as_its_diffusion_length_has_no_top():
    """Trap difference_denominator: c dt = D = 600 m makes |c dt - D| zero, so the
    window has no top; a thousand steps of 3 m (Cg = Dg = 200, X = -99.5) route."""
    lowest, highest = distance_step_window(10.0, 3.0, 0.001, 1.0, 20.0, 12.0)

    run = muskingum_cunge_route(
        [0.0, 10.0, 40.0, 20.0, 5.0], 10.0, 3.0, 0.001, 1.0, 20.0, 12.0, 1000, 0.0
    )

    assert highest == math.inf
    assert lowest < 3.0
    assert_within(
        run.x,
        -99.5,
        rel=1e-14,
        reason="X = (1 - D / dx) / 2 with D = 600 m and dx = 3 m, a few roundings",
    )
    assert_within(
        [run.c_current, run.c_previous, run.c_outflow],
        [399.0 / 401.0, 1.0 / 401.0, 1.0 / 401.0],
        rel=1e-12,
        reason="Ponce's weights (C + D - 1, 1 + C - D, 1 - C + D) / (1 + C + D) at C = "
        "D = 200, computed from K and X = -99.5 with a few roundings",
    )
    assert run.outflow_m3s.min() >= 0.0


def test_a_long_steady_inflow_stays_steady():
    """Trap many_small_terms: 200,000 ordinates of a steady inflow stay steady."""
    inflow = np.full(200_000, 0.001)

    run = muskingum_cunge_route(inflow, 10.0, 3.0, 0.001, 1.0, 20.0, 30.0, 3, 0.001)

    assert_within(
        run.outflow_m3s,
        inflow,
        rel=1e-14,
        reason="the weights sum to 1 to rounding and c_outflow < 1 damps the error of "
        "each step: it cannot grow along the series",
    )


def test_a_depth_beyond_a_float_is_refused():
    """Trap exp_overflow: a rectangle 1e-300 m wide carries a million m3/s only at a
    depth beyond the largest float: the precondition representable_flow refuses it."""
    with pytest.raises(InvalidParameterError) as caught:
        normal_flow(1.0e6, 0.001, 1.0e-300, 0.0, 0.035)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "representable_flow"


@pytest.mark.parametrize(
    ("narrow", "wide"),
    [
        ({"bottom_width_m": 0.0}, {"bottom_width_m": 30.0}),
        ({"bottom_width_m": 4.0}, {"bottom_width_m": 4.5}),
        ({"side_slope_m_per_m": 0.0}, {"side_slope_m_per_m": 2.0}),
        ({"side_slope_m_per_m": 1.0}, {"side_slope_m_per_m": 1.1}),
    ],
)
def test_a_wider_section_or_flatter_banks_carry_the_flow_shallower(narrow, wide):
    """Manning's conveyance grows with b and z at a given depth, so the depth falls:
    the generated nudge cannot show it where the bottom or the banks carry a share of
    the conveyance below the root finder's resolution, so the spec declares no
    monotonicity in them and the typical range is checked here."""
    base = {
        "discharge_m3s": 10.0,
        "slope_m_per_m": 0.001,
        "bottom_width_m": 4.0,
        "side_slope_m_per_m": 2.0,
        "manning_n": 0.035,
    }

    shallow = normal_flow(**{**base, **wide})
    deep = normal_flow(**{**base, **narrow})

    assert shallow.depth_m < deep.depth_m


def test_the_delegated_root_finder_finds_a_known_root():
    """DELEGATED manning_normal_depth: brentq finds ln y = 0, the depth of 1 m at which
    a rectangle 2 m wide has a given Manning conveyance, on [-1, 1]."""

    def conveyance(depth: float) -> float:
        area = 2.0 * depth
        return area * (area / (2.0 + 2.0 * depth)) ** (2.0 / 3.0)

    target = conveyance(1.0)

    root = brentq(
        lambda u: math.log(conveyance(math.exp(u)) / target), -1.0, 1.0, xtol=1e-15
    )

    assert_within(
        root,
        0.0,
        abs=1e-14,
        reason="brentq stops within xtol = 1e-15 of the root (scipy.optimize.brentq); "
        "the logarithm of the conveyance rounds at a few units of 1e-16",
    )


def test_the_formulas_record_their_versions():
    with recording() as used:
        muskingum_cunge_route([0.0, 1.0, 0.0], 6.0, 2.6, 0.001, 1.0, 20.0, 20.0, 2, 0.0)
        normal_flow(10.0, 0.001, 4.0, 2.0, 0.035)

    assert used == {
        "muskingum_cunge": MUSKINGUM_CUNGE.formula_version,
        "manning_normal_flow": MANNING_NORMAL_FLOW.formula_version,
    }


def test_a_trickle_or_a_hairline_section_gets_a_flow_or_a_refusal():
    """Regression: TrapezoidalSection.flow divided by a zero area where the depth fell
    below its root finder's absolute tolerance of 1e-14 m (ZeroDivisionError), and
    raised scipy's ValueError for a section that needed a depth beyond 2^80 m; it now
    has the formula's normal flow, or its refusal of a depth no float holds."""
    state = TrapezoidalSection(4.0, 2.0, 0.035).flow(1e-300, 0.001)

    assert state.depth_m == normal_flow(1e-300, 0.001, 4.0, 2.0, 0.035).depth_m
    assert state.depth_m > 0.0
    with pytest.raises(InvalidParameterError) as caught:
        TrapezoidalSection(1e-300, 0.0, 0.035).flow(1.0e6, 0.001)
    assert caught.value.details["constraint"] == "representable_flow"


def test_the_section_flows_through_the_formula():
    with recording() as used:
        state = TrapezoidalSection(4.0, 2.0, 0.035).flow(10.0, 0.001)
    flow = normal_flow(10.0, 0.001, 4.0, 2.0, 0.035)

    assert used == {"manning_normal_flow": MANNING_NORMAL_FLOW.formula_version}
    assert (state.depth_m, state.top_width_m, state.celerity_m_per_s) == (
        flow.depth_m,
        flow.top_width_m,
        flow.celerity_m_per_s,
    )


def test_the_reach_routes_through_the_formulas():
    inflow = Hydrograph.from_step([0.0, 4.0, 15.0, 30.0, 22.0, 12.0, 6.0, 3.0], 30.0)
    reach = MuskingumCungeReach(
        length_km=6.0,
        slope_m_per_m=0.001,
        manning_n=0.035,
        bottom_width_m=8.0,
        side_slope_m_per_m=2.0,
    )

    with recording() as used:
        result = reach.route(inflow, extend_min=0.0)
    parameters = result.parameters
    step = inflow.timestep_min / parameters["substeps"]
    run = muskingum_cunge_route(
        inflow.refined(parameters["substeps"]).discharge_m3s,
        step,
        6.0,
        0.001,
        parameters["celerity_m_per_s"],
        parameters["top_width_m"],
        parameters["reference_discharge_m3s"],
        parameters["subreaches"],
        0.0,
    )

    assert used == {
        "muskingum_cunge": MUSKINGUM_CUNGE.formula_version,
        "manning_normal_flow": MANNING_NORMAL_FLOW.formula_version,
    }
    assert (
        result.outflow.discharge_m3s.tolist()
        == run.outflow_m3s[:: parameters["substeps"]].tolist()
    )
    assert result.storage_end_m3 == run.storage_end_m3
    assert (parameters["x"], parameters["k_min"]) == (run.x, run.k_min)
