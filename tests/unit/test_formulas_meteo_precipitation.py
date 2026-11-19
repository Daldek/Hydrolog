"""The precipitation indices and the seasonality index against their specs (CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/meteo-indices-cases.json`` (CMP-6.1); the
limits hold the oracles in exact fractions (CMP-6.2). The functions are given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

from pathlib import Path

import numpy as np
import pytest
from hypothesis import example, given

from hydrolog._formulas import ERRORS
from hydrolog.catalog import run_command
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    ReferenceCase,
    assert_case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.statistics.meteo_precipitation import (
    HEAVY_SHARE,
    PCI,
    PCI_CLASS,
    SDII,
    SI_CLASS,
    WET_DAY_PERCENTILE,
    heavy_precipitation_share,
    pci_class,
    precipitation_concentration_index,
    si_class,
    wet_day_intensity,
    wet_day_percentile,
)
from hydrolog.statistics.regime import SEASONALITY_INDEX, seasonality_index

from ._formula_checks import as_standard
from ._warszawa import DATES, P

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "meteo-indices-cases.json"
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (SDII, wet_day_intensity),
    (WET_DAY_PERCENTILE, wet_day_percentile),
    (HEAVY_SHARE, heavy_precipitation_share),
    (PCI, precipitation_concentration_index),
    (PCI_CLASS, pci_class),
    (SEASONALITY_INDEX, seasonality_index),
    (SI_CLASS, si_class),
)
DECADE = {
    "dates": [str(day) for day in DATES[:3653]],
    "precipitation_mm": P[:3653].tolist(),
}


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


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=lambda x: str(x))
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


def _properties(spec: FormulaSpec, function, inputs) -> None:
    assert_property_contract(spec, as_standard(function), inputs, ERRORS)
    assert_properties(spec, as_standard(function), inputs, ERRORS)


@given(inputs=strategies(SDII))
@example(  # SDII in the subnormal range: 2 fl(t / W) and fl(2 t / W) differ by 5e-324
    inputs={
        "precipitation_mm": np.full(46, 2.225073858507203e-309),
        "wet_day_mm": 5e-324,
    }
)
def test_sdii_properties(inputs):
    _properties(SDII, wet_day_intensity, inputs)


@given(inputs=strategies(WET_DAY_PERCENTILE))
def test_wet_day_percentile_properties(inputs):
    _properties(WET_DAY_PERCENTILE, wet_day_percentile, inputs)


@given(inputs=strategies(HEAVY_SHARE))
def test_heavy_precipitation_share_properties(inputs):
    _properties(HEAVY_SHARE, heavy_precipitation_share, inputs)


@given(inputs=strategies(PCI))
def test_pci_properties(inputs):
    _properties(PCI, precipitation_concentration_index, inputs)


@given(inputs=strategies(PCI_CLASS))
def test_pci_class_properties(inputs):
    _properties(PCI_CLASS, pci_class, inputs)


@given(inputs=strategies(SEASONALITY_INDEX))
def test_seasonality_index_properties(inputs):
    _properties(SEASONALITY_INDEX, seasonality_index, inputs)


@given(inputs=strategies(SI_CLASS))
def test_si_class_properties(inputs):
    _properties(SI_CLASS, si_class, inputs)


@pytest.mark.parametrize(
    ("index", "specs"),
    [
        ("intensity", (SDII,)),
        ("heavy", (HEAVY_SHARE, WET_DAY_PERCENTILE)),
        ("seasonality", (PCI_CLASS, PCI, SEASONALITY_INDEX, SI_CLASS)),
    ],
)
def test_the_series_record_the_versions_of_their_formulas(index, specs):
    envelope = run_command("meteo precipitation", {**DECADE, "index": index}).to_dict()

    assert envelope["formula_versions"] == {
        spec.name: spec.formula_version
        for spec in sorted(specs, key=lambda spec: spec.name)
    }
