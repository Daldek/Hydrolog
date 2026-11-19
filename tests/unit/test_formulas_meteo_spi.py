"""The SPI and the classes of relative precipitation against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/meteo-indices-cases.json`` (CMP-6.1); the
limits hold the decimal oracles (CMP-6.2); the SPI of Warszawa-Okęcie is compared with
the frozen output of climate_indices 3.2.0 (CMP-6.4). The functions are given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

import math
from pathlib import Path

import numpy as np
import pytest
from hypothesis import example, given

from hydrolog._formulas import ERRORS
from hydrolog.catalog import run_command
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
    read_frozen_oracle,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.statistics import standardized_precipitation_index
from hydrolog.statistics.meteo_spi import (
    GAMMA_FIT,
    MONTH_CLASS,
    SPI,
    YEAR_CLASS,
    fit_gamma,
    month_precipitation_class,
    spi_values,
    year_precipitation_class,
)

from ._formula_checks import as_standard
from ._warszawa import DATES, P

pytestmark = pytest.mark.formula

ROOT = Path(__file__).parents[1]
CASES = ROOT / "fixtures" / "formulas" / "meteo-indices-cases.json"
ORACLE = ROOT / "oracles" / "spi_climate_indices_warszawa.csv"
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (GAMMA_FIT, fit_gamma),
    (SPI, spi_values),
    (YEAR_CLASS, year_precipitation_class),
    (MONTH_CLASS, month_precipitation_class),
)
FAMILY_SPECS = tuple(spec for spec, _ in FAMILY)


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


@given(inputs=strategies(GAMMA_FIT))
def test_gamma_fit_properties(inputs):
    assert_property_contract(GAMMA_FIT, as_standard(fit_gamma), inputs, ERRORS)
    assert_properties(GAMMA_FIT, as_standard(fit_gamma), inputs, ERRORS)


@given(inputs=strategies(SPI))
@example(  # a subnormal shape: scipy's gammainc gives 0, the SPI the upper tail
    inputs={
        "sums_mm": np.array([1.0]),
        "alpha": 5e-324,
        "beta_mm": 6.0,
        "zero_probability": 0.0,
    }
)
@example(  # a subnormal shape: scipy's gammaincc goes negative, held at 0
    inputs={
        "sums_mm": np.array([3.0]),
        "alpha": 2.2250738585e-313,
        "beta_mm": 6.0,
        "zero_probability": 0.0,
    }
)
def test_spi_properties(inputs):
    assert_property_contract(SPI, as_standard(spi_values), inputs, ERRORS)
    assert_properties(SPI, as_standard(spi_values), inputs, ERRORS)


@given(inputs=strategies(YEAR_CLASS))
def test_year_class_properties(inputs):
    function = as_standard(year_precipitation_class)
    assert_property_contract(YEAR_CLASS, function, inputs, ERRORS)
    assert_properties(YEAR_CLASS, function, inputs, ERRORS)


@given(inputs=strategies(MONTH_CLASS))
def test_month_class_properties(inputs):
    function = as_standard(month_precipitation_class)
    assert_property_contract(MONTH_CLASS, function, inputs, ERRORS)
    assert_properties(MONTH_CLASS, function, inputs, ERRORS)


def test_the_spi_of_warszawa_equals_that_of_climate_indices():
    """The frozen oracle (CMP-6.4): the same monthly sums, fits and conventions.

    A hand-written test: the generator compares one formula with its spec, not the
    pipeline of daily sums, k-month sums, fits and the SPI of a station (CMP-6.5).
    """
    frozen = read_frozen_oracle(ORACLE)
    result = standardized_precipitation_index(P, DATES, scales_months=(1, 3, 6, 12))

    months = result.months
    assert [(m.year, m.month) for m in months] == [
        (int(row["year"]), int(row["month"])) for row in frozen.rows
    ]
    for number, scale in enumerate((1, 3, 6, 12)):
        ours = [math.nan if m.spi[number] is None else m.spi[number] for m in months]
        assert_within(
            ours,
            frozen.floats(f"spi{scale}"),
            abs=1e-9,
            reason="the same estimator and conventions; Hydrolog's A is the mean of "
            "d - ln(1 + d) and its upper tail comes from Q(alpha, z): differences of "
            "1e-14 in H, at most 1e-12 of SPI",
        )


def test_a_negative_sum_is_refused():
    """A negative sum was taken as 0 by spi_values and left out by fit_gamma."""
    with pytest.raises(InvalidParameterError) as caught:
        spi_values([10.0, -0.1], 2.0, 20.0, 0.0)

    assert caught.value.details["reason"] == "outside_physical_range"
    assert caught.value.details["option"] == "sums_mm"


def test_a_calendar_month_whose_sums_the_fit_refuses_has_no_spi():
    """The precondition of spi_gamma_fit leaves the month without a fit (notice)."""
    days = np.arange(np.datetime64("2001-01-01"), np.datetime64("2004-01-01"))
    values = np.where(days.astype("datetime64[M]").astype(int) % 12 == 6, 0.0, 1.0)
    values[days == np.datetime64("2002-07-15")] = 5.0

    result = standardized_precipitation_index(values, days, scales_months=(1,))

    july = result.period.scales[0].fits[6]
    assert (july.alpha, july.beta, july.zero_probability, july.n_values) == (
        None,
        None,
        None,
        3,
    )
    assert all(m.spi[0] is None for m in result.months if m.month == 7)


def test_a_half_percent_counts_in_the_class_above():
    """Kaczorowska's classes of whole percents, a half rounded up (ADR-0059).

    Python's ``round`` (a half to even) made 74.5 % very dry and 75.5 % dry, 110.5 %
    normal and 111.5 % wet: the classes were not intervals.
    """
    classes = [year_precipitation_class(value) for value in (73.5, 74.5, 75.5)]
    upper = [year_precipitation_class(value) for value in (109.5, 110.5, 111.5)]

    assert classes == ["very_dry", "dry", "dry"]
    assert upper == ["normal", "wet", "wet"]


def test_the_formulas_record_their_versions():
    envelope = run_command(
        "meteo spi",
        {"dates": [str(day) for day in DATES], "precipitation_mm": P.tolist()},
    ).to_dict()

    assert envelope["formula_versions"] == {
        spec.name: spec.formula_version
        for spec in sorted(FAMILY_SPECS, key=lambda spec: spec.name)
    }
