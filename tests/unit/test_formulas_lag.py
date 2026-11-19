"""The lag against its spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5). The HEC-HMS TRM
defines the lag (Lag model, eq. 1) but publishes no routed table, so the formula is
``oracle only``: its limits hold the exact shift by whole steps, the Muskingum scheme
with X = 0.5 and K = dt, and a fractional lag as the convex combination of two shifts
(CMP-6.2). The generic strategies are refused only beyond float64, so they serve the
properties without a hand-written one; the conservation law is exact once the ramp
before the first ordinate and the trapezoid's error at the kinks are counted.
"""

import math

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
from hydrolog.routing import Hydrograph, LagReach
from hydrolog.routing.formulas.lag import LAG, lag_route

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

ROUTE = as_standard(lag_route)


@pytest.mark.parametrize("case", range_cases(LAG) + type_cases(LAG))
def test_ranges_and_types(case: Case):
    run_case(LAG, ROUTE, case, ERRORS)


def test_limits_and_oracles():
    assert_limits(LAG, ROUTE, ERRORS)


@given(inputs=strategies(LAG))
@example(
    inputs={
        "inflow_m3s": np.array([150120.0, 0.0]),
        "timestep_min": 5e-324,
        "lag_min": 5e-324,
        "initial_outflow_m3s": 0.0,
    }
)
def test_properties(inputs):
    assert_property_contract(LAG, ROUTE, inputs, ERRORS)
    assert_properties(LAG, ROUTE, inputs, ERRORS)


def test_a_lag_in_steps_beyond_float64_is_refused():
    with pytest.raises(InvalidParameterError) as caught:
        lag_route([1.0, 2.0], 5e-324, 30.0, 1.0)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "representable"


def test_a_lag_a_rounding_away_from_whole_steps_is_a_whole_shift():
    """0.3 / 0.1 is 2.9999999999999996 in float64: the shift is three whole steps."""
    run = lag_route([1.0, 2.0, 4.0, 8.0, 16.0], 0.1, 0.3, 1.0)

    assert run.lag_fraction == 0.0
    assert run.outflow_m3s.tolist() == [1.0, 1.0, 1.0, 1.0, 2.0]


def test_a_long_transit_volume_sums_exactly():
    """Trap many_small_terms: the water in transit over 100,000 steps."""
    values = 1.0 + np.sin(np.arange(200_000) / 7.0) ** 2
    step, lag = 5.0, 5.0 * 100_000

    run = lag_route(values, step, lag, 1.0)

    tail = values[-100_001:]
    trapezoids = (0.5 * (tail[1:] + tail[:-1]) * step).tolist()
    assert_within(
        run.storage_end_m3,
        math.fsum(trapezoids) * 60.0,
        rel=1e-12,
        reason="NumPy's pairwise sum of 100,000 positive trapezoids errs by about "
        "1e-16 log2(1e5) relative, against the correctly rounded math.fsum",
    )


def test_the_formula_records_its_version():
    with recording() as used:
        lag_route([0.0, 1.0, 0.0], 10.0, 25.0, 0.0)

    assert used == {"lag": LAG.formula_version}


def test_the_reach_routes_through_the_formula():
    inflow = Hydrograph.from_step([0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0], 10.0)

    with recording() as used:
        result = LagReach(lag_min=25.0).route(inflow, extend_min=0.0)
    run = lag_route(inflow.discharge_m3s, 10.0, 25.0, 0.0)

    assert used == {"lag": LAG.formula_version}
    assert result.outflow.discharge_m3s.tolist() == run.outflow_m3s.tolist()
    assert result.storage_end_m3 == run.storage_end_m3
    assert "lag_interpolated" in [notice.code for notice in result.notices]
