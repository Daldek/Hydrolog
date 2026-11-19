"""Level-pool routing by storage indication against its spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5); the reference
cases are NEH 630 chapter 17's examples 17-1 and 17-2, the reservoir's three steps as
three cases with the state the source carries between them
(``tests/fixtures/formulas/level-pool-cases.json``, CMP-6.1); the limits hold the exact
rational recurrence, the linear reservoir of the spec ``muskingum`` and the bounds of a
monotone scheme (CMP-6.2), and SciPy's ODE solver the convergence (CMP-6.3). The
generic strategies draw the rows of a table apart, so almost every table they draw falls
somewhere and is refused: the hand-written strategy :func:`runs` draws valid tables, a
flood inside them and a step within their limit, for the properties.
"""

from itertools import pairwise
from pathlib import Path
from typing import Any

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import example, given
from hypothesis.extra.numpy import arrays
from scipy.integrate import solve_ivp

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
    convert,
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.routing import Hydrograph, LevelPoolReach
from hydrolog.routing.formulas.level_pool import (
    LEVEL_POOL,
    TableExit,
    level_pool_route,
    step_limit_s,
    table_exit,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "level-pool-cases.json"
ROUTE = as_standard(level_pool_route)
BASE = LEVEL_POOL.base_point()


@pytest.mark.parametrize("case", range_cases(LEVEL_POOL) + type_cases(LEVEL_POOL))
def test_ranges_and_types(case: Case):
    run_case(LEVEL_POOL, ROUTE, case, ERRORS)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in load_cases(CASES, "level_pool")]
)
def test_reference_cases(case: ReferenceCase):
    assert_case(LEVEL_POOL, ROUTE, case, ERRORS)


def test_limits_and_oracles():
    assert_limits(LEVEL_POOL, ROUTE, ERRORS)


@given(inputs=strategies(LEVEL_POOL))
def test_properties(inputs):
    assert_property_contract(LEVEL_POOL, ROUTE, inputs, ERRORS)
    assert_properties(LEVEL_POOL, ROUTE, inputs, ERRORS)


@st.composite
def runs(draw, anywhere: bool = False) -> dict[str, object]:
    """Valid runs: a table rising from an optional dead zone, a flood within its
    outflows, a step within the limit of the segments the flood reaches (of the whole
    table ``anywhere``, so that any flood within its outflows may be routed)."""
    rows = draw(st.integers(min_value=2, max_value=8))
    dead = draw(st.integers(min_value=0, max_value=rows - 2))
    lowest = draw(st.sampled_from([0.0]) | st.floats(min_value=0.0, max_value=20.0))
    rises = draw(arrays(np.float64, rows - 1 - dead, elements=st.floats(0.5, 50.0)))
    rating = lowest + np.concatenate([np.zeros(dead + 1), np.cumsum(rises)])
    volumes = draw(arrays(np.float64, rows - 1, elements=st.floats(1.0e2, 1.0e5)))
    datum = draw(st.sampled_from([0.0]) | st.floats(min_value=0.0, max_value=1.0e6))
    storage = datum + np.concatenate([[0.0], np.cumsum(volumes)])
    count = draw(st.integers(min_value=1, max_value=6))
    flows = st.floats(min_value=float(rating[0]), max_value=float(rating[-1]))
    inflow = draw(arrays(np.float64, draw(st.integers(2, 40)), elements=flows))
    initial = draw(flows)
    reached = (
        (rating[0], rating[-1])
        if anywhere
        else (
            min(float(inflow.min()), initial),
            max(float(inflow.max()), initial),
        )
    )
    limit = step_limit_s(storage, rating, count, *reached)
    longest = min(convert(limit, "s", "min"), 720.0)
    return {
        "inflow_m3s": inflow,
        "timestep_min": draw(st.floats(min_value=longest / 100.0, max_value=longest)),
        "table_storage_m3": storage,
        "table_outflow_m3s": rating,
        "subreaches": count,
        "initial_outflow_m3s": initial,
    }


def working_top(inputs: dict[str, Any]) -> float:
    """The working curve's value at the last row [m3/s], the scale of its rounding."""
    step_s = convert(float(inputs["timestep_min"]), "min", "s")
    storage = np.asarray(inputs["table_storage_m3"], dtype=np.float64)
    rating = np.asarray(inputs["table_outflow_m3s"], dtype=np.float64)
    held = float(storage[-1]) / (int(inputs["subreaches"]) * step_s)
    return held + 0.5 * float(rating[-1])


@given(inputs=runs())
@example(
    inputs={
        "inflow_m3s": np.array([2.22507386e-313, 2.22507386e-313]),
        "timestep_min": 0.011111111111111112,
        "table_storage_m3": np.array([0.0, 100.0]),
        "table_outflow_m3s": np.array([0.0, 3.0]),
        "subreaches": 1,
        "initial_outflow_m3s": 0.0,
    },
).via("discovered failure: a subnormal flood kept its balance to 1.3e-9 of itself")
def test_properties_of_valid_runs(inputs):
    assert_property_contract(LEVEL_POOL, ROUTE, inputs, ERRORS)
    assert_properties(LEVEL_POOL, ROUTE, inputs, ERRORS)


@given(inputs=runs())
def test_the_outflow_of_a_valid_run_stays_between_its_flows(inputs):
    """The monotone scheme's bound on random valid runs: the generator checks only the
    fixed points of the limit bounded_by_its_flows, not a bound at drawn inputs."""
    run = level_pool_route(**inputs)

    flows = [*np.asarray(inputs["inflow_m3s"]), inputs["initial_outflow_m3s"]]
    assert_within(
        np.clip(run.outflow_m3s, min(flows), max(flows)),
        run.outflow_m3s,
        abs=1e-13 * working_top(inputs),
        reason="a step within the limit of every segment the run reaches makes each "
        "outflow a non-decreasing function of the earlier flows; the state rounds at "
        "1e-16 of the working curve per step, damped by the weight (2K - dt)/(2K + dt)",
    )


@given(
    inputs=runs(anywhere=True),
    raised=st.sampled_from(["inflow_m3s", "initial_outflow_m3s"]),
    lift=st.floats(min_value=0.0, max_value=1.0),
)
@example(
    inputs={
        "inflow_m3s": np.full(24, 12.6875),
        "timestep_min": 0.021484375,
        "table_storage_m3": np.array([0.0, 100.0, 200.0]),
        "table_outflow_m3s": np.array([0.0, 0.5, 44.30078125]),
        "subreaches": 3,
        "initial_outflow_m3s": 0.0,
    },
    raised="initial_outflow_m3s",
    lift=0.09765625,
).via(
    "discovered failure of the generated monotonicity: the converged outflows of the "
    "two runs, 12.6875 to the rounding of a working curve of 74 m3/s, differ by five "
    "units in the last place of the outflow, where it allows four"
)
def test_the_outflow_rises_with_its_inflow_and_initial_outflow(inputs, raised, lift):
    """Monotonicity in each of the two flows at drawn valid runs: the generated test
    allows four units in the last place of the outflow, but the scheme reads the outflow
    from its working curve, whose rounding (1e-16 of its top, which a short step makes
    much larger than the outflow) passes to the outflow; the tolerance is that rounding,
    which the generator cannot express."""
    top = float(np.asarray(inputs["table_outflow_m3s"])[-1])
    value = np.minimum(np.asarray(inputs[raised], dtype=np.float64) + lift, top)
    moved = {**inputs, raised: value if value.ndim else float(value)}

    lower = level_pool_route(**inputs).outflow_m3s
    higher = level_pool_route(**moved).outflow_m3s

    assert_within(
        np.maximum(higher, lower),
        higher,
        abs=1e-13 * working_top(inputs),
        reason="a step within the limit of every segment of the table makes each "
        "outflow a non-decreasing function of the earlier flows; the state rounds at "
        "1e-16 of the working curve per step, damped by the weight (2K - dt)/(2K + dt)",
    )


def test_rows_the_working_curve_cannot_tell_apart_are_refused():
    """Trap difference_denominator: two rows 1e-30 m3 apart at the same outflow give
    the same working curve in float64, and the fraction of their segment would divide
    by zero: the precondition working_curve_rises refuses them."""
    with pytest.raises(InvalidParameterError) as caught:
        level_pool_route(
            [5.0, 6.0, 5.0], 10.0, [0.0, 1e-30, 6.0e4], [1.0, 1.0, 40.0], 1, 5.0
        )

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "working_curve_rises"


def test_a_step_that_the_rule_for_the_whole_curve_allows_is_refused():
    """Trap stability_bound: K = dS/dO is 100 s up to 20 m3/s and 5 s above, S/O at
    70 m3/s 32 s; NEH 630's rule dt <= 2 S/O at every row allows 64 s, on which a rise
    from 40 to 60 m3/s overshoots, while the steep segment allows 10 s."""
    rise = [40.0, 40.0] + [60.0] * 10

    with pytest.raises(InvalidParameterError) as caught:
        level_pool_route(rise, 1.0, [0.0, 2000.0, 2250.0], [0.0, 20.0, 70.0], 1, 40.0)

    assert caught.value.details["constraint"] == "timestep_within_limit"
    assert_within(
        step_limit_s(
            np.array([0.0, 2000.0, 2250.0]), np.array([0.0, 20.0, 70.0]), 1, 40.0, 60.0
        ),
        10.0,
        rel=1e-15,
        reason="2 (2250 - 2000) / (70 - 20) s: one division and one product",
    )
    run = level_pool_route(
        rise,
        convert(10.0, "s", "min"),
        [0.0, 2000.0, 2250.0],
        [0.0, 20.0, 70.0],
        1,
        40.0,
    )
    assert_within(
        run.outflow_m3s,
        [40.0, 40.0, 50.0] + [60.0] * 9,
        rel=1e-13,
        reason="on the step 2K of the steep segment the weight of the previous state "
        "is zero, so each outflow is the average inflow of its step; the working curve "
        "rounds at 1e-16 of its 235 m3/s",
    )


def test_a_long_steady_inflow_stays_steady():
    """Trap many_small_terms: 200,000 ordinates of a steady inflow through two pools
    stay steady: the state is a running sum of the step's inflow and outflow."""
    inflow = np.full(200_000, 25.0)

    run = level_pool_route(
        inflow, 30.0, BASE["table_storage_m3"], BASE["table_outflow_m3s"], 2, 25.0
    )

    assert_within(
        run.outflow_m3s,
        inflow,
        rel=1e-12,
        reason="the state changes by the rounding of the outflow it reads back, 1e-16 "
        "of it per step, damped by the weight (2K - dt)/(2K + dt) = 0.82 of the "
        "segment: it cannot grow along the series",
    )


def test_a_flood_beyond_the_top_of_the_table_is_refused_where_it_leaves_it():
    flood = [5.0, 60.0, 200.0, 300.0, 300.0, 300.0, 200.0, 100.0]
    inputs = {**BASE, "inflow_m3s": flood}

    with pytest.raises(InvalidParameterError) as caught:
        level_pool_route(**inputs)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "flood_below_table_top"
    leave = table_exit(**inputs)
    assert isinstance(leave, TableExit)
    assert (leave.pool, leave.above) == (1, True)
    # the flood up to the ordinate before is routed; with it, it is refused
    level_pool_route(**{**inputs, "inflow_m3s": flood[: leave.index]})
    with pytest.raises(InvalidParameterError):
        level_pool_route(**{**inputs, "inflow_m3s": flood[: leave.index + 1]})


def test_an_inflow_that_drains_the_bottom_of_the_table_is_refused():
    raised = (5.0, 10.0, 40.0, 100.0, 200.0)
    inputs = {
        **BASE,
        "inflow_m3s": [5.0, 20.0, 60.0, 90.0, 70.0, 40.0] + [0.0] * 14,
        "table_outflow_m3s": raised,
    }

    with pytest.raises(InvalidParameterError) as caught:
        level_pool_route(**inputs)

    assert caught.value.details["constraint"] == "flood_above_table_bottom"
    leave = table_exit(**inputs)
    assert leave is not None and not leave.above
    assert table_exit(**BASE) is None


def test_the_scheme_converges_to_the_integrated_equation():
    """Oracle: scipy.integrate.solve_ivp of dS/dt = I(t) - O(S) for a tank of 50,000 m2
    draining over a weir O = 20 h^1.5, the table its line in 6,001 rows; the inflow is
    linear between the ordinates on both sides."""
    area, weir = 50_000.0, 20.0
    depth = np.linspace(0.0, 3.0, 6001)
    knots, flows = [0.0, 30.0, 90.0, 180.0, 240.0], [10.0, 10.0, 70.0, 10.0, 10.0]
    start = (flows[0] / weir) ** (1.0 / 1.5)

    def rate(seconds, level):
        inflow = np.interp(convert(seconds, "s", "min"), knots, flows)
        return [(inflow - weir * max(level[0], 0.0) ** 1.5) / area]

    errors = []
    for step in (10.0, 5.0, 2.5):
        times = np.arange(0.0, 240.0 + step / 2.0, step)
        run = level_pool_route(
            np.interp(times, knots, flows),
            step,
            area * depth,
            weir * depth**1.5,
            1,
            flows[0],
        )
        solved = solve_ivp(
            rate,
            [0.0, convert(240.0, "min", "s")],
            [start],
            t_eval=[convert(t, "min", "s") for t in times],
            rtol=1e-11,
            atol=1e-13,
            max_step=30.0,
        )
        reference = weir * np.maximum(solved.y[0], 0.0) ** 1.5
        errors.append(float(np.abs(run.outflow_m3s - reference).max()))

    assert errors[-1] < 0.03
    assert_within(
        [coarse / fine for coarse, fine in pairwise(errors)],
        [4.0, 4.0],
        abs=0.5,
        reason="the trapezoid rule is of second order: halving the step divides the "
        "error by four, to the higher-order terms of a flood whose inflow bends at "
        "its knots",
    )


def test_the_formula_records_its_version():
    with recording() as used:
        level_pool_route([0.0, 1.0, 0.0], 10.0, [0.0, 3.0e4], [0.0, 10.0], 1, 0.0)

    assert used == {"level_pool": LEVEL_POOL.formula_version}


def test_the_reach_routes_through_the_formula():
    inflow = Hydrograph.from_step([5.0, 20.0, 60.0, 90.0, 70.0, 40.0, 20.0], 30.0)
    reach = LevelPoolReach(
        BASE["table_storage_m3"], BASE["table_outflow_m3s"], subreaches=2
    )

    with recording() as used:
        result = reach.route(inflow, extend_min=0.0)
    run = level_pool_route(
        inflow.discharge_m3s,
        30.0,
        BASE["table_storage_m3"],
        BASE["table_outflow_m3s"],
        2,
        5.0,
    )

    assert used == {"level_pool": LEVEL_POOL.formula_version}
    assert result.outflow.discharge_m3s.tolist() == run.outflow_m3s.tolist()
    assert result.storage_end_m3 == run.storage_m3[-1]
    assert result.parameters["storage_peak_m3"] == run.storage_peak_m3


def test_the_reach_words_rows_its_step_cannot_tell_apart_as_a_repeated_row():
    reach = LevelPoolReach([0.0, 1e-30, 6.0e4], [1.0, 1.0, 40.0])

    with pytest.raises(InvalidParameterError) as caught:
        reach.route(Hydrograph.from_step([5.0, 6.0, 5.0], 10.0))

    assert caught.value.details == {"option": "storage_m3", "reason": "repeated_row"}
