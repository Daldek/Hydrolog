"""The unit hydrographs against their specs (Nogat CMP §6): generated and published.

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/unit-hydrographs-cases.json`` (CMP-6.1);
the limits hold the exact and independent oracles (CMP-6.2). Table 16-1 of NEH 630
chapter 16 is the data file ``src/hydrolog/_data/tables/neh630_duh.csv``, accepted
against its two transcriptions in ``tests/oracles`` (CMP-2.5). The functions are given
to the assertions through :func:`as_standard` (ADR-0050, point 3).
"""

import csv
import math
import warnings
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given
from scipy.stats import gamma

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog._warnings import UhSubsteps
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
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.runoff import SCSUnitHydrograph, SnyderUH
from hydrolog.runoff.convolution import CONVOLUTION, convolve_discrete
from hydrolog.runoff.snyder_uh import (
    SNYDER,
    SNYDER_SHAPE,
    snyder_parameters,
    snyder_shape,
)
from hydrolog.runoff.unit_hydrograph import (
    SCS,
    SCS_DIMENSIONLESS_UH,
    scs_unit_hydrograph,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

ROOT = Path(__file__).parents[2]
CASES = ROOT / "tests" / "fixtures" / "formulas" / "unit-hydrographs-cases.json"
ORACLES = ROOT / "tests" / "oracles"
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (SCS, scs_unit_hydrograph),
    (SNYDER, snyder_parameters),
    (SNYDER_SHAPE, snyder_shape),
    (CONVOLUTION, convolve_discrete),
)


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


@given(inputs=strategies(SCS))
def test_scs_properties(inputs):
    assert_property_contract(SCS, as_standard(scs_unit_hydrograph), inputs, ERRORS)
    assert_properties(SCS, as_standard(scs_unit_hydrograph), inputs, ERRORS)


@given(inputs=strategies(CONVOLUTION))
def test_convolution_properties(inputs):
    function = as_standard(convolve_discrete)
    assert_property_contract(CONVOLUTION, function, inputs, ERRORS)
    assert_properties(CONVOLUTION, function, inputs, ERRORS)


@given(inputs=strategies(SNYDER))
def test_snyder_properties(inputs):
    function = as_standard(snyder_parameters)
    assert_property_contract(SNYDER, function, inputs, ERRORS)
    assert_properties(SNYDER, function, inputs, ERRORS)


@given(inputs=strategies(SNYDER_SHAPE))
def test_snyder_shape_properties(inputs):
    function = as_standard(snyder_shape)
    assert_property_contract(SNYDER_SHAPE, function, inputs, ERRORS)
    assert_properties(SNYDER_SHAPE, function, inputs, ERRORS)


# --- table 16-1 of NEH 630 chapter 16 (CMP-2.5) ---------------------------------------


def _rows(path: Path) -> list[tuple[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [(row["t_over_tp"], row["q_over_qp"]) for row in csv.DictReader(handle)]


DUH = _rows(ROOT / "src" / "hydrolog" / "_data" / "tables" / "neh630_duh.csv")


def test_the_scs_table_is_the_text_layer_of_neh_630():
    assert _rows(ORACLES / "neh630_duh_text_layer.csv") == DUH


def test_the_scs_table_typed_for_0_8_1_agrees_with_it():
    assert _rows(ORACLES / "neh630_duh_hydrolog_0_8_1.csv") == DUH


def test_the_scs_table_read_is_the_data_file():
    assert SCS_DIMENSIONLESS_UH.tolist() == [[float(t), float(q)] for t, q in DUH]
    assert not SCS_DIMENSIONLESS_UH.flags.writeable


# --- the traps of the spec scs (CMP-6.6) ----------------------------------------------


def _volume_mm(result, area_km2: float) -> float:
    return float(
        np.sum(result.ordinates_m3s) * result.timestep_min * 60.0 / (area_km2 * 1000.0)
    )


def test_scs_steps_at_and_beyond_the_neh_bound():
    """Trap stability_bound: D = 0.25 Tp is sampled as it is, a longer D on sub-steps.

    tc 70 min and a step of 12 min give 0.25 (6 + 42) = 12 min, the bound itself:
    the ordinates are the table at the step times. tc 69.9 min gives 0.25 Tp =
    11.985 min, so the step is divided in two; the hydrograph keeps its 1 mm, and tp
    and qp stay those of D = 12 min (E5b-07).
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error", UhSubsteps)
        on = scs_unit_hydrograph(45.3, 70.0, 12.0)
    sampled = np.interp(
        on.times_min / on.time_to_peak_min,
        SCS_DIMENSIONLESS_UH[:, 0],
        SCS_DIMENSIONLESS_UH[:, 1],
        left=0.0,
        right=0.0,
    )
    assert np.array_equal(on.ordinates_m3s, sampled * on.peak_discharge_m3s)

    with pytest.warns(UhSubsteps) as caught:
        beyond = scs_unit_hydrograph(45.3, 69.9, 12.0)
    details = caught[0].message.details
    assert (details["substeps"], details["substep_min"]) == (2, 6.0)
    assert_within(
        details["maximum_min"],
        11.985,
        rel=1e-14,
        reason="0.25 (6 + 0.6 x 69.9) min in float64",
    )
    assert_within(
        _volume_mm(beyond, 45.3),
        1.0,
        abs=0.003,
        reason="the conservation unit_volume of the spec scs",
    )
    assert beyond.ordinates_m3s[0] == beyond.ordinates_m3s[-1] == 0.0
    assert_within(
        beyond.time_to_peak_min,
        6.0 + 0.6 * 69.9,
        rel=1e-15,
        reason="Tp of D = 12 min, not of the sub-step",
    )


def test_scs_a_day_step_keeps_its_volume():
    """Trap many_small_terms, E5b-07: tc 90.7 min at a step of a day, 93 sub-steps.

    Sampled at the step alone, the hydrograph held 0.52 mm; summed over the 93
    sub-steps by cumulative sums it holds the 1 mm of the conservation law.
    """
    with pytest.warns(UhSubsteps) as caught:
        result = scs_unit_hydrograph(10.0, 90.7, 1440.0)

    assert caught[0].message.details["substeps"] == 93
    assert_within(
        _volume_mm(result, 10.0),
        1.0,
        abs=0.003,
        reason="the conservation unit_volume of the spec scs (0.9984 mm here)",
    )


def test_the_scs_wrapper_computes_through_the_spec():
    unit = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
    result = unit.generate(10.0)

    assert result.peak_discharge_m3s == unit.peak_discharge(10.0)
    assert result.time_to_peak_min == unit.time_to_peak(10.0)
    assert result.time_base_min == unit.time_base(10.0)
    assert result.lag_time_min == unit.lag_time_min
    with recording() as used:
        unit.generate(10.0)
    assert used == {"scs": SCS.formula_version}


# --- the traps of the spec snyder_shape (CMP-6.6) -------------------------------------


@pytest.mark.parametrize("peak", [1.0e-12, 1.0e6])
def test_snyder_shape_refuses_an_exponent_outside_its_bracket(peak):
    """Trap unbounded_iteration: no K of 1e-12 to 1e12 makes a curve of 1 mm.

    qpR tpR / (A x 1 mm) is 5.6e-16 for the low peak and 5.6e5 for the high one, the
    bracket of the root holds 1e-12 to about 4e5: the precondition refuses both before
    Brent's method runs.
    """
    with pytest.raises(InvalidParameterError) as caught:
        snyder_shape(45.3, 426.0, peak, 60.0, 2640.0)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "root_bracketed"
    assert caught.value.details["option"] == "peak_discharge_m3s"


def test_snyder_shape_a_million_ordinates_hold_their_volume():
    """Trap many_small_terms: a million ordinates at a step of 2^-10 min.

    999,999 steps of 2^-10 min end the grid at the million ordinates the precondition
    grid_representable allows, one more step is refused.
    """
    step = 2.0**-10
    result = snyder_shape(45.3, 426.0, 1.0664561043776108, step, 999_999 * step)

    assert result.ordinates_m3s.size == 1_000_000
    depth_mm = math.fsum(result.ordinates_m3s.tolist()) * step * 60.0 / (45.3 * 1000.0)
    assert_within(
        depth_mm,
        1.0,
        abs=1e-12,
        reason="the conservation unit_volume of the spec snyder_shape",
    )
    with pytest.raises(InvalidParameterError) as caught:
        snyder_shape(45.3, 426.0, 1.0664561043776108, step, 1_000_000 * step)
    assert caught.value.details["constraint"] == "grid_representable"


def test_the_snyder_wrapper_computes_through_the_specs():
    """SnyderUH fills the standard duration and the end at 99.99 % of the volume."""
    unit = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
    with recording() as used:
        result = unit.generate(timestep_min=30.0)
    found = snyder_parameters(100.0, 15.0, 8.0, 1.5, 0.6, unit.standard_duration_min)
    shape = snyder_shape(
        100.0, found.time_to_peak_min, found.peak_discharge_m3s, 30.0, 1.0
    )
    end = gamma(
        a=shape.shape_exponent + 1.0,
        scale=found.time_to_peak_min / shape.shape_exponent,
    ).ppf(0.9999)

    assert used == {
        "snyder": SNYDER.formula_version,
        "snyder_shape": SNYDER_SHAPE.formula_version,
    }
    assert result.duration_min == found.standard_duration_min
    assert result.time_to_peak_min == found.time_to_peak_min
    assert result.time_base_min == found.time_base_min
    assert end <= result.times_min[-1] < end + 30.0
