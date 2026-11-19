"""The relief ratio against its spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5); the reference
cases are Baścik's (2006) slopes of a river in ``morphometry-cases.json`` (CMP-6.1),
the limit the exact rational ratio (CMP-6.2).
"""

from pathlib import Path

import pytest
from hypothesis import given

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import TerrainAnalysis
from hydrolog.morphometry.terrain import RELIEF_RATIO, relief_ratio
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

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "morphometry-cases.json"


@pytest.mark.parametrize(
    "case", [p.values[0] for p in range_cases(RELIEF_RATIO) + type_cases(RELIEF_RATIO)]
)
def test_ranges_and_types(case: Case):
    run_case(RELIEF_RATIO, relief_ratio, case, ERRORS)


@pytest.mark.parametrize(
    "case", load_cases(CASES, "relief_ratio"), ids=lambda case: case.case_id
)
def test_reference_cases(case: ReferenceCase):
    assert_case(RELIEF_RATIO, relief_ratio, case, ERRORS)


def test_limits_and_oracles():
    assert_limits(RELIEF_RATIO, relief_ratio, ERRORS)


@given(inputs=strategies(RELIEF_RATIO))
def test_properties(inputs):
    assert_property_contract(RELIEF_RATIO, relief_ratio, inputs, ERRORS)
    assert_properties(RELIEF_RATIO, relief_ratio, inputs, ERRORS)


def test_the_channel_slope_of_raclawka_is_bascik_s():
    """Baścik (2006, p. 33): the Racławka, 390 to 242 m over 16.3 km, 9.1 per mille;
    TerrainAnalysis takes the watershed's relief over the channel's length."""
    terrain = TerrainAnalysis(
        elevation_min_m=242.0,
        elevation_max_m=390.0,
        length_km=16.3,
        channel_length_km=16.3,
    )

    percent, per_unit = terrain.channel_slope()

    assert per_unit == relief_ratio(242.0, 390.0, 16.3)
    assert_within(
        percent * 10.0,
        9.1,
        abs=0.05 + 0.09,
        reason="half a unit of the printed 9.1 per mille and the printed inputs' "
        "rounding (0.5 m of each elevation, 0.05 km of the length)",
    )


def test_a_channel_length_is_checked_as_a_length():
    with pytest.raises(InvalidParameterError) as refused:
        TerrainAnalysis(150.0, 520.0, 12.0, channel_length_km=0.0)

    assert refused.value.details["reason"] == "outside_physical_range"
    assert refused.value.details["option"] == "length_km"


def test_equal_elevations_are_refused():
    """Trap difference_denominator: no relief, no watershed draining to an outlet."""
    with pytest.raises(InvalidParameterError) as refused:
        relief_ratio(300.0, 300.0, 5.0)

    assert refused.value.details["constraint"] == "rises_above_outlet"


def test_the_formula_records_its_version():
    with recording() as used:
        TerrainAnalysis(150.0, 520.0, 12.0).get_slope_parameters()

    assert used == {"relief_ratio": RELIEF_RATIO.formula_version}
