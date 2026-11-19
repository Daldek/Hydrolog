"""The formulas of the frequency analyses against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/flood-frequency-cases.json`` (CMP-6.1);
the limits hold the exact rational oracles (CMP-6.2); NumPy and SciPy are compared in
the tests (CMP-6.3), R's lmom and lmomco through the frozen oracle
``tests/oracles/frequency_lmom_r.csv`` (CMP-6.4). The functions are given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

import csv
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from hypothesis import example, given
from scipy.stats import skew

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
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
from hydrolog.statistics.frequency import (
    L_MOMENTS,
    MOMENTS,
    sample_l_moments,
    sample_moments,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

TESTS = Path(__file__).parents[1]
CASES = TESTS / "fixtures" / "formulas" / "flood-frequency-cases.json"
LMOM = read_frozen_oracle(TESTS / "oracles" / "frequency_lmom_r.csv")
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (MOMENTS, sample_moments),
    (L_MOMENTS, sample_l_moments),
)


def _samples() -> dict[str, list[float]]:
    """The samples of the frozen R oracles, by dataset."""
    found: dict[str, list[float]] = {}
    path = TESTS / "oracles" / "frequency_ml_samples.csv"
    with path.open(encoding="utf-8") as stream:
        for row in csv.DictReader(line for line in stream if not line.startswith("#")):
            found.setdefault(row["dataset"], []).append(float(row["value"]))
    return found


SAMPLES = _samples()


def _lmom(dataset: str, function: str) -> dict[str, float]:
    """The outputs of an R function on a dataset in the frozen oracle."""
    return {
        row["output"]: float(row["value"])
        for row in LMOM.rows
        if row["dataset"] == dataset and row["function"] == function
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


@given(inputs=strategies(MOMENTS))
def test_moments_properties(inputs):
    assert_property_contract(MOMENTS, as_standard(sample_moments), inputs, ERRORS)
    assert_properties(MOMENTS, as_standard(sample_moments), inputs, ERRORS)


@given(inputs=strategies(L_MOMENTS))
@example(inputs={"values": np.array([0.8125, *[0.0] * 23])}).via(
    "discovered failure: t3 of values all equal but the largest rounded 5 ulp above 1"
)
@example(inputs={"values": np.array([-999600.0, 0.81, 999595.0, *[1.0] * 18])}).via(
    "discovered failure: the mean of the sorted deviations was not the negated mean of "
    "the negated sample"
)
def test_l_moments_properties(inputs):
    assert_property_contract(L_MOMENTS, as_standard(sample_l_moments), inputs, ERRORS)
    assert_properties(L_MOMENTS, as_standard(sample_l_moments), inputs, ERRORS)


@pytest.mark.parametrize("dataset", sorted(SAMPLES))
def test_the_moments_are_numpys_and_scipys(dataset):
    """CMP-6.3: NumPy's mean and std (ddof 1) and SciPy's skew (bias False, G1)."""
    values = np.array(SAMPLES[dataset])

    found = sample_moments(values)

    assert_within(
        [found.mean, found.std, found.skewness],
        [np.mean(values), np.std(values, ddof=1), skew(values, bias=False)],
        rel=1e-13,
        reason="the same two-pass moments in another order of operations",
    )


@pytest.mark.parametrize("dataset", sorted(SAMPLES))
@pytest.mark.parametrize("function", ["lmom::samlmu", "lmomco::lmoms"])
def test_the_l_moments_are_those_of_r(dataset, function):
    """CMP-6.4: Hosking's samlmu and Asquith's lmoms (frozen, R 4.5.3)."""
    oracle = _lmom(dataset, function)

    found = sample_l_moments(SAMPLES[dataset])

    assert_within(
        [found.l1, found.l2, found.t3],
        [oracle["l1"], oracle["l2"], oracle["t3"]],
        rel=1e-13,
        reason="R prints 15 significant digits; both sides sum the same unbiased "
        "probability-weighted moments",
    )


def test_long_samples_keep_their_moments():
    """Trap many_small_terms: 20,000 values against rational arithmetic."""
    rng = np.random.default_rng(20261119)
    values = 1000.0 + 100.0 * rng.standard_normal(20_000)
    exact = [Fraction(float(value)) for value in values]
    n = len(exact)
    mean = sum(exact, Fraction(0)) / n
    m2 = sum(((value - mean) ** 2 for value in exact), Fraction(0)) / n
    ascending = sorted(exact)
    b1 = sum((j * x for j, x in enumerate(ascending)), Fraction(0)) / (n * (n - 1))

    moments = sample_moments(values)
    l_moments = sample_l_moments(values)

    assert_within(
        [moments.mean, moments.std, l_moments.l1, l_moments.l2],
        [
            float(mean),
            math.sqrt(float(m2 * n / (n - 1))),
            float(mean),
            float(2 * b1 - mean),
        ],
        rel=1e-13,
        reason="NumPy's pairwise sums of 20,000 terms round within about log2(n) ulp; "
        "a naive running sum would lose about n ulp",
    )


def test_the_formulas_record_their_versions():
    with recording() as used:
        sample_moments([1.0, 2.0, 4.0])
        sample_l_moments([1.0, 2.0, 4.0])

    assert used == {spec.name: spec.formula_version for spec, _ in FAMILY}
