"""The equal-area slope of a longitudinal profile against its spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5); the limits hold
the exact rational oracle and the sources' construction by bisection (CMP-6.2). No
source publishes a profile with its equal-area slope, so the formula is ``oracle
only``. The generic strategies draw each distance apart, so they almost never draw a
profile whose distances do not step back, which the spec refuses: the hand-written
strategy :func:`profiles` draws profiles that the formula computes, for the
properties.
"""

import json
from fractions import Fraction
from pathlib import Path

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import given

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import WatershedParameters, equal_area_slope
from hydrolog.morphometry.profile import EQUAL_AREA_SLOPE, _equal_areas_slope
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

FIXTURES = Path(__file__).parents[1] / "fixtures"
PROFILE = json.loads(
    (FIXTURES / "kamiennik_flow_path_profile.json").read_text(encoding="utf-8")
)
KAMIENNIK = json.loads((FIXTURES / "kamiennik.json").read_text(encoding="utf-8"))


def _exact(distance: list[float], elevation: list[float]) -> Fraction:
    """2A/L^2 of the float inputs in exact rational arithmetic."""
    x = [Fraction(value) for value in distance]
    z = [Fraction(value) for value in elevation]
    twice_area = sum(
        (x[i + 1] - x[i]) * (z[i] + z[i + 1] - 2 * z[0]) for i in range(len(x) - 1)
    )
    return twice_area / (x[-1] - x[0]) ** 2


@pytest.mark.parametrize(
    "case", range_cases(EQUAL_AREA_SLOPE) + type_cases(EQUAL_AREA_SLOPE)
)
def test_ranges_and_types(case: Case):
    run_case(EQUAL_AREA_SLOPE, equal_area_slope, case, ERRORS)


def test_limits_and_oracles():
    assert_limits(EQUAL_AREA_SLOPE, equal_area_slope, ERRORS)


@given(inputs=strategies(EQUAL_AREA_SLOPE))
def test_properties(inputs):
    assert_property_contract(EQUAL_AREA_SLOPE, equal_area_slope, inputs, ERRORS)
    assert_properties(EQUAL_AREA_SLOPE, equal_area_slope, inputs, ERRORS)


@st.composite
def profiles(draw) -> dict[str, np.ndarray]:
    """A profile from an outlet upstream: steps of 0.5 m to 2 km or a vertical step,
    rises of -5 to 50 m, so most lie above their outlet and some do not."""
    count = draw(st.integers(min_value=2, max_value=60))
    step = st.one_of(st.just(0.0), st.floats(min_value=0.5, max_value=2000.0))
    rise = st.floats(min_value=-5.0, max_value=50.0)
    steps = draw(st.lists(step, min_size=count - 1, max_size=count - 1))
    rises = draw(st.lists(rise, min_size=count - 1, max_size=count - 1))
    start = draw(st.floats(min_value=0.0, max_value=30000.0))
    outlet = draw(st.floats(min_value=-431.0, max_value=8000.0))
    return {
        "distance_m": start + np.concatenate([[0.0], np.cumsum(steps)]),
        "elevation_m": outlet + np.concatenate([[0.0], np.cumsum(rises)]),
    }


@given(inputs=profiles())
def test_properties_of_profiles(inputs):
    assert_property_contract(EQUAL_AREA_SLOPE, equal_area_slope, inputs, ERRORS)
    assert_properties(EQUAL_AREA_SLOPE, equal_area_slope, inputs, ERRORS)


class TestKamiennik:
    """Hydrograf's longest flow path of Kamiennik to Świerzawa (the guide's example)."""

    def test_its_slope_is_the_exact_one_and_leaves_equal_areas(self):
        slope = equal_area_slope(PROFILE["distance_m"], PROFILE["elevation_m"])

        assert_within(
            slope,
            float(_exact(PROFILE["distance_m"], PROFILE["elevation_m"])),
            rel=4e-15,
            reason="1,592 trapezoids summed by math.fsum: a few roundings per term, "
            "every term positive",
        )
        assert_within(
            slope,
            _equal_areas_slope(PROFILE["distance_m"], PROFILE["elevation_m"]),
            rel=1e-12,
            reason="the bisection of the sources' construction, its areas above and "
            "below summed apart over 1,592 segments",
        )

    def test_the_guides_watershed_carries_the_slope_of_this_profile(self):
        # the profile is concave: its equal-area slope (0.0084766) is 0.742 of the
        # slope between its ends (0.0114), which Lutz took until ADR-0053
        slope = equal_area_slope(PROFILE["distance_m"], PROFILE["elevation_m"])
        watershed = WatershedParameters.from_dict(KAMIENNIK)
        length_m = PROFILE["distance_m"][-1] - PROFILE["distance_m"][0]
        drop_m = PROFILE["elevation_m"][-1] - PROFILE["elevation_m"][0]

        assert round(slope, 5) == watershed.flow_path_equal_area_slope_m_per_m
        assert round(drop_m / length_m, 4) == watershed.flow_path_slope_m_per_m
        assert round(length_m / 1000.0, 2) == watershed.flow_path_length_km


def test_a_profile_without_length_is_refused():
    """Trap difference_denominator: L = 0 is refused, not divided by."""
    with pytest.raises(InvalidParameterError) as caught:
        equal_area_slope([500.0, 500.0, 500.0], [200.0, 210.0, 220.0])

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "positive_area"


@pytest.mark.parametrize(
    ("distance", "elevation", "expected"),
    [
        ([0.0, 0.0005, 0.001], [100.0, 100.000004, 100.00001], 0.009),
        ([0.0, 1e-170], [100.0, 100.0 + 1e-172], None),
    ],
)
def test_a_tiny_profile_is_finite_or_refused(distance, elevation, expected):
    """Trap singular_at_bound: S grows as 1/L^2; an underflowing L^2 is refused."""
    if expected is None:
        with pytest.raises(InvalidParameterError) as caught:
            equal_area_slope(distance, elevation)
        assert caught.value.details["reason"] == "precondition_failed"
        return
    assert_within(
        equal_area_slope(distance, elevation),
        float(_exact(distance, elevation)),
        rel=1e-13,
        reason="the rises of a few micrometres differ from 100 m by the roundings of "
        "100 m, 1.4e-14 m: below 1e-13 of the area",
    )


def test_a_profile_of_many_points_matches_its_exact_sum():
    """Trap many_small_terms: 100,001 points of 1 cm against the exact rational sum."""
    distance = np.arange(100_001) / 100.0
    elevation = 250.0 + 0.003 * distance + 0.4 * np.sin(distance / 37.0) ** 2

    assert_within(
        equal_area_slope(distance, elevation),
        float(_exact(distance.tolist(), elevation.tolist())),
        rel=4e-15,
        reason="math.fsum rounds the sum of 100,000 positive terms once; each term "
        "carries a few roundings of its own",
    )


def test_the_formula_records_its_version():
    with recording() as used:
        equal_area_slope([0.0, 1000.0], [200.0, 210.0])

    assert used == {"equal_area_slope": EQUAL_AREA_SLOPE.formula_version}
