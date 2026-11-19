"""The spells against their spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5); the limits hold
the oracle that counts the spells day by day (CMP-6.2). The function is given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

import numpy as np
import pytest
from hypothesis import given

from hydrolog._formulas import ERRORS
from hydrolog.catalog import run_command
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    assert_limits,
    assert_properties,
    assert_property_contract,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.statistics import precipitation_spells
from hydrolog.statistics.meteo_spells import SPELL_LENGTHS, spell_lengths

from ._formula_checks import as_standard
from ._warszawa import DATES, P

pytestmark = pytest.mark.formula

FAMILY: tuple[tuple[FormulaSpec, object], ...] = ((SPELL_LENGTHS, spell_lengths),)


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=lambda x: str(x))
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


@given(inputs=strategies(SPELL_LENGTHS))
def test_spell_lengths_properties(inputs):
    function = as_standard(spell_lengths)
    assert_property_contract(SPELL_LENGTHS, function, inputs, ERRORS)
    assert_properties(SPELL_LENGTHS, function, inputs, ERRORS)


def test_a_negative_precipitation_is_refused():
    """CMP-3.1: [0, -2, 0, 5] mm gave a dry spell of three days, -2 mm a dry day."""
    days = np.arange(np.datetime64("2001-01-01"), np.datetime64("2001-01-05"))

    with pytest.raises(InvalidParameterError) as caught:
        precipitation_spells([0.0, -2.0, 0.0, 5.0], days)

    assert caught.value.details["reason"] == "outside_physical_range"
    assert caught.value.details["option"] == "precipitation_mm"
    assert caught.value.details["index"] == [1]


def test_a_negative_accumulated_total_is_refused_too():
    """An accumulated total is a missing day of the spells, yet no negative value."""
    days = np.arange(np.datetime64("2001-01-01"), np.datetime64("2001-01-05"))

    with pytest.raises(InvalidParameterError) as caught:
        precipitation_spells(
            [0.0, np.nan, -2.0, 5.0], days, accumulated=[False, False, True, False]
        )

    assert caught.value.details["reason"] == "outside_physical_range"


def test_the_spells_of_warszawa_hold_its_dry_days():
    """Every dry day of 1991-2020 lies in one spell, listed whole by its year."""
    found = precipitation_spells(P, DATES)

    assert sum(spell.duration_days for spell in found.spells) == int(
        np.count_nonzero(P < 1.0)
    )
    assert found.max_duration_days == int(spell_lengths(P, 1.0, "dry").max())


def test_the_series_records_the_version_of_its_formula():
    envelope = run_command(
        "meteo spells",
        {
            "dates": [str(day) for day in DATES[:366]],
            "precipitation_mm": P[:366].tolist(),
        },
    ).to_dict()

    assert envelope["formula_versions"] == {
        "spell_lengths": SPELL_LENGTHS.formula_version
    }
