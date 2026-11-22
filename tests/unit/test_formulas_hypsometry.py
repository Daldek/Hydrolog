"""The hypsometric integral against its spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5); the limits hold
the exact rational trapezoid and the exact integral (mean - min) / (max - min) with
the trapezoid's error bound (CMP-6.2). No source publishes a surface with its
integral, so the formula is ``oracle only``.
"""

import math

import numpy as np
import pytest
from hypothesis import given

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import HypsometricCurve
from hydrolog.morphometry.hypsometry import HYPSOMETRIC_INTEGRAL, hypsometric_integral
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

pytestmark = pytest.mark.formula

SPEC = HYPSOMETRIC_INTEGRAL


@pytest.mark.parametrize(
    "case", [p.values[0] for p in range_cases(SPEC) + type_cases(SPEC)]
)
def test_ranges_and_types(case: Case):
    run_case(SPEC, hypsometric_integral, case, ERRORS)


def test_limits_and_oracles():
    assert_limits(SPEC, hypsometric_integral, ERRORS)


@given(inputs=strategies(SPEC))
def test_properties(inputs):
    assert_property_contract(SPEC, hypsometric_integral, inputs, ERRORS)
    assert_properties(SPEC, hypsometric_integral, inputs, ERRORS)


def test_a_flat_surface_is_refused():
    """Trap difference_denominator: the relief divides the relative heights."""
    with pytest.raises(InvalidParameterError) as refused:
        HypsometricCurve(np.array([250.0, 250.0, 250.0])).hypsometric_integral()

    assert refused.value.details["reason"] == "precondition_failed"
    assert refused.value.details["constraint"] == "positive_relief"


def test_many_cells_match_their_exact_sums():
    """Trap many_small_terms: the shares of 200,001 cells against math.fsum."""
    rng = np.random.default_rng(20261119)
    elevations = rng.uniform(100.0, 750.0, 200_001)
    areas = rng.uniform(0.5, 1.5, 200_001) * 1e-6
    n_points = 101

    thresholds = np.linspace(elevations.min(), elevations.max(), n_points)
    total = math.fsum(areas.tolist())
    shares = [math.fsum(areas[elevations >= t].tolist()) / total for t in thresholds]
    exact = math.fsum(
        (shares[i] + shares[i + 1]) / 2.0 / (n_points - 1) for i in range(n_points - 1)
    )

    assert_within(
        hypsometric_integral(elevations, areas, n_points),
        exact,
        abs=1e-13,
        reason="NumPy's pairwise sums of 200,001 areas against correctly rounded ones: "
        "a few units of 2^-53 times log2 of the count, relative",
    )


def test_the_curve_class_gives_the_formula():
    elevations = np.array([258.72, 260.1, 261.0, 263.4, 270.0, 440.16])
    areas = np.array([4.0, 3.5, 3.0, 2.0, 1.0, 0.25])
    curve = HypsometricCurve(elevations, areas)

    assert curve.hypsometric_integral(51) == hypsometric_integral(elevations, areas, 51)
    assert curve.analyze().hypsometric_integral == hypsometric_integral(
        elevations, areas, 101
    )


def test_the_formula_records_its_version():
    with recording() as used:
        HypsometricCurve(np.array([100.0, 200.0, 400.0])).hypsometric_integral()

    assert used == {"hypsometric_integral": SPEC.formula_version}
