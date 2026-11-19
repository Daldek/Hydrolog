"""The rating curve, its fit and plausibility and Rybczyński's zones (Nogat CMP §6).

Range, type and property tests are generated from the specs of
``hydrolog.hydrometrics.rating_curve`` (CMP-6.5); the limits hold the exact oracles
(CMP-6.2); the fit is compared with R's ``nls`` through the frozen oracle
``tests/oracles/rating_curve/nls_port.csv`` (CMP-6.4) and with the cases of
``tests/fixtures/formulas/hydrometrics-cases.json``, which are oracles (R and an exact
power law), not published cases, so the file is not a reference-case file of the spec
and the fit is ``oracle only``. The generic strategies draw each element of an array
apart, so they seldom draw pairs of one length, rising levels or a histogram: the
hand-written strategies :func:`rating_pairs` and :func:`histograms` draw inputs the
formulas compute, for the properties. The functions are given to the assertions
through :func:`as_standard` (ADR-0050, point 3).
"""

import math
import warnings
from fractions import Fraction
from pathlib import Path

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import given

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog._warnings import OutsideTypicalRange, UnreferencedFormula
from hydrolog.exceptions import InvalidParameterError
from hydrolog.hydrometrics import rating_curve
from hydrolog.hydrometrics.rating_curve import (
    RATING_CURVE,
    RATING_CURVE_FIT,
    RATING_CURVE_PLAUSIBILITY,
    RYBCZYNSKI_ZONES,
    RatingCurve,
    WaterLevelFrequency,
    fit_rating_curve,
    rating_curve_plausibility,
    rating_discharge,
    rybczynski_zones,
)
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

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

TESTS = Path(__file__).parents[1]
CASES = TESTS / "fixtures" / "formulas" / "hydrometrics-cases.json"
NLS = read_frozen_oracle(TESTS / "oracles" / "rating_curve" / "nls_port.csv")
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (RATING_CURVE, rating_discharge),
    (RATING_CURVE_FIT, fit_rating_curve),
    (RATING_CURVE_PLAUSIBILITY, rating_curve_plausibility),
    (RYBCZYNSKI_ZONES, rybczynski_zones),
)
PAIRS_H = list(rating_curve._PAIRS_H)
PAIRS_Q = list(rating_curve._PAIRS_Q)
NLS_SETS = {
    "doc_negative_stages": (
        [-10.0, 5.0, 20.0, 40.0, 80.0, 120.0],
        [0.5, 1.2, 2.5, 4.8, 10.1, 17.3],
        -23.0,
    ),
    "fixture_pairs": (PAIRS_H, PAIRS_Q, 41.2),
    "wmo1044_table_II_1_1": (
        [2.682, 2.786, 2.002, 1.981, 2.374, 1.557, 1.490, 1.509, 1.838, 1.780,
         1.710, 1.573, 1.570, 1.414, 1.396, 2.432],
        [99.12, 11.02, 33.13, 30.02, 67.40, 7.080, 4.928, 5.296, 20.99, 17.13,
         13.54, 7.703, 7.590, 3.483, 3.313, 69.95],
        1.396 - 0.139,
    ),
}  # fmt: skip
"""The pairs and R's start of the datasets of the frozen oracle (r_rating_oracle.R)."""


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


def _squares(levels, discharges, a, b, h0) -> float:
    """The sum of squared residuals of a curve, by math.fsum."""
    head = np.maximum(np.asarray(levels) - h0, 0.0)
    return math.fsum(((np.asarray(discharges) - a * head**b) ** 2).tolist())


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=lambda x: str(x))
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


@pytest.mark.parametrize(
    "case", load_cases(CASES, RATING_CURVE_FIT.name), ids=lambda case: case.case_id
)
def test_the_oracle_cases_of_the_fit(case: ReferenceCase):
    assert_case(RATING_CURVE_FIT, as_standard(fit_rating_curve), case, ERRORS)


# --- properties ------------------------------------------------------------------


@given(inputs=strategies(RATING_CURVE))
def test_rating_curve_properties(inputs):
    assert_property_contract(
        RATING_CURVE, as_standard(rating_discharge), inputs, ERRORS
    )
    assert_properties(RATING_CURVE, as_standard(rating_discharge), inputs, ERRORS)


@given(inputs=strategies(RATING_CURVE_FIT))
def test_fit_properties(inputs):
    fit = as_standard(fit_rating_curve)
    assert_property_contract(RATING_CURVE_FIT, fit, inputs, ERRORS)
    assert_properties(RATING_CURVE_FIT, fit, inputs, ERRORS)


@st.composite
def rating_pairs(draw) -> dict[str, object]:
    """Gaugings of a power law with noise: 3 to 40 rising levels of -50 to 600 cm."""
    count = draw(st.integers(min_value=3, max_value=40))
    lowest = draw(st.floats(min_value=-50.0, max_value=400.0))
    steps = draw(st.lists(st.floats(0.5, 40.0), min_size=count - 1, max_size=count - 1))
    levels = lowest + np.concatenate([[0.0], np.cumsum(steps)])
    depth = draw(st.floats(min_value=1.0, max_value=200.0))
    a = draw(st.floats(min_value=0.001, max_value=0.05))
    b = draw(st.floats(min_value=1.0, max_value=3.0))
    noise = draw(st.lists(st.floats(-0.1, 0.1), min_size=count, max_size=count))
    discharges = a * (levels - lowest + depth) ** b * np.exp(noise)
    start = float(lowest - max(1.0, 0.1 * float(levels[-1] - lowest)))
    return {"water_levels": levels, "discharges_m3s": discharges, "h0_initial": start}


@given(inputs=rating_pairs())
def test_fit_properties_of_gaugings(inputs):
    fit = as_standard(fit_rating_curve)
    assert_property_contract(RATING_CURVE_FIT, fit, inputs, ERRORS)
    assert_properties(RATING_CURVE_FIT, fit, inputs, ERRORS)


@given(inputs=strategies(RATING_CURVE_PLAUSIBILITY))
def test_plausibility_properties(inputs):
    check = as_standard(rating_curve_plausibility)
    assert_property_contract(RATING_CURVE_PLAUSIBILITY, check, inputs, ERRORS)
    assert_properties(RATING_CURVE_PLAUSIBILITY, check, inputs, ERRORS)


@given(inputs=strategies(RYBCZYNSKI_ZONES))
def test_zones_properties(inputs):
    zones = as_standard(rybczynski_zones)
    assert_property_contract(RYBCZYNSKI_ZONES, zones, inputs, ERRORS)
    assert_properties(RYBCZYNSKI_ZONES, zones, inputs, ERRORS)


@st.composite
def histograms(draw) -> dict[str, object]:
    """Classes of 0.5 to 50 units from -100 to 500 with counts of 0 to 500, some."""
    count = draw(st.integers(min_value=1, max_value=40))
    width = draw(st.floats(min_value=0.5, max_value=50.0))
    start = draw(st.floats(min_value=-100.0, max_value=500.0))
    counts = draw(st.lists(st.integers(0, 500), min_size=count, max_size=count))
    return {
        "bin_edges": start + width * np.arange(count + 1, dtype=np.float64),
        "counts": np.array(counts, dtype=np.float64),
    }


@given(inputs=histograms())
def test_zones_properties_of_histograms(inputs):
    zones = as_standard(rybczynski_zones)
    assert_property_contract(RYBCZYNSKI_ZONES, zones, inputs, ERRORS)
    assert_properties(RYBCZYNSKI_ZONES, zones, inputs, ERRORS)
    if inputs["counts"].sum() > 0:
        found = rybczynski_zones(inputs["bin_edges"], inputs["counts"])
        assert found.ntw_upper < found.stw_upper


def test_the_plausibility_does_not_depend_on_the_unit_of_the_levels():
    """The generic scaling compares no choice (CMP-6.5 allows a hand-written test)."""
    for b, h0 in ((1.62, 32.0), (0.85, 1.39), (6.5, -88.0), (2.0, -300.0)):
        in_cm = rating_curve_plausibility(PAIRS_H, b, h0)
        in_m = rating_curve_plausibility([h / 100.0 for h in PAIRS_H], b, h0 / 100.0)
        assert in_cm == in_m


# --- the frozen oracle of R --------------------------------------------------------


def _nls(dataset: str) -> dict[str, float]:
    return {
        row["statistic"]: float(row["value"])
        for row in NLS.rows
        if row["dataset"] == dataset and row["method"] == "nls_port_arith"
    }


@pytest.mark.parametrize("dataset", sorted(NLS_SETS))
def test_the_fit_equals_r_nls_port(dataset):
    """Both minimise the same squares: Hydrolog's sum is R's or smaller, the curves
    agree within the flatness of the optimum."""
    levels, discharges, start = NLS_SETS[dataset]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OutsideTypicalRange)
        fit = fit_rating_curve(levels, discharges, start)
    r = _nls(dataset)
    ours = _squares(levels, discharges, fit.a, fit.b, fit.h0)
    theirs = _squares(levels, discharges, r["a"], r["b"], r["h0"])
    assert_within(
        theirs,
        r["sse"],
        rel=1e-12,
        reason="R's printed parameters give back its printed sum of squares",
    )
    assert_within(
        min(r["sse"] - ours, 0.0),
        0.0,
        abs=1e-10 * r["sse"],
        reason="the least squares of Hydrolog's search are R's or smaller, beyond the "
        "sums' rounding and R's convergence of 1e-10 relative",
    )
    flat = 2e-4 if dataset.startswith("wmo") else 1e-5
    assert_within(
        [fit.a, fit.b, fit.h0],
        [r["a"], r["b"], r["h0"]],
        rel=flat,
        reason="two optimisers on a flat optimum agree in the parameters to 1e-5 "
        "(WMO's 16 gaugings of several ratings, R^2 0.58: 2e-4, where R stops 5e-8 "
        "above Hydrolog's sum of squares)",
    )


def test_the_log_space_fit_of_wmo_is_another_curve():
    """WMO-No. 1044 sect. 1.12.2 fits log Q on log(H - H0): R's curve differs from
    the fit on Q, which the spec states as its convention."""
    levels, discharges, start = NLS_SETS["doc_negative_stages"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OutsideTypicalRange)
        fit = fit_rating_curve(levels, discharges, start)
    logarithmic = {
        row["statistic"]: float(row["value"])
        for row in NLS.rows
        if row["dataset"] == "doc_negative_stages"
        and row["method"] == "ols_log_profile_h0"
    }
    assert abs(fit.b - logarithmic["b"]) > 0.1


# --- the delegated search (CMP-1.2) and the statistical cases (CMP-6.7) ---------------


def test_the_delegated_least_squares_recover_a_noise_free_curve():
    levels = np.array([40.0, 55.0, 70.0, 90.0, 120.0, 160.0, 210.0, 270.0])
    fit = fit_rating_curve(levels, 0.012 * (levels - 32.0) ** 1.62, 17.0)

    assert_within(
        [fit.a, fit.b, fit.h0],
        [0.012, 1.62, 32.0],
        rel=1e-6,
        reason="the smoke case of the delegated computation: noise-free pairs",
    )


def test_three_pairs_are_the_smallest_sample():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OutsideTypicalRange)
        fit = fit_rating_curve([60.0, 120.0, 200.0], [1.0, 8.0, 25.0], 40.0)
        with pytest.raises(InvalidParameterError) as caught:
            fit_rating_curve([60.0, 120.0], [1.0, 8.0], 40.0)
    assert_within(
        _squares([60.0, 120.0, 200.0], [1.0, 8.0, 25.0], fit.a, fit.b, fit.h0),
        0.0,
        abs=1e-18,
        reason="three parameters through three pairs: the curve meets them",
    )
    assert caught.value.details["constraint"] == "enough_pairs"


def test_ties_and_a_zero_discharge_are_fitted():
    """Two gaugings at one level and a dry one: a curve through the rest."""
    levels = [*PAIRS_H, 155.0, 62.0]
    discharges = [*PAIRS_Q, 12.9, 0.0]
    fit = fit_rating_curve(levels, discharges, 41.2)

    assert fit.n_points == 17
    assert fit.h0 < 62.0
    assert 0.98 < fit.r_squared <= 1.0


@pytest.mark.parametrize(
    ("levels", "discharges", "constraint"),
    [
        ([100.0] * 15, PAIRS_Q, "levels_not_all_equal"),
        (PAIRS_H, [5.0] * 15, "discharges_not_all_equal"),
    ],
)
def test_constant_series_are_refused(levels, discharges, constraint):
    with pytest.raises(InvalidParameterError) as caught:
        fit_rating_curve(levels, discharges, 41.2)
    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == constraint


# --- the traps of the families (CMP-6.6) ---------------------------------------------


def test_the_power_at_the_stage_of_zero_flow_is_finite():
    """Trap singular_at_bound of the curve: a fractional power of a head of 0."""
    levels = [32.0, math.nextafter(32.0, 33.0), 32.0 + 1e-300]
    for b in (0.0, 0.5, 1.62):
        found = rating_discharge(levels, 0.012, b, 32.0)
        assert found[0] == 0.0
        assert np.all(np.isfinite(found))
    assert_within(
        rating_discharge([32.0 + 2.0**-20], 0.012, 1.62, 32.0),
        [rating_curve._exact_discharge(32.0 + 2.0**-20, 0.012, 1.62, 32.0)],
        rel=4e-15,
        reason="a head of 2^-20 to the power 1.62 against 50 decimal digits: the "
        "power and the product round a few times",
    )


def test_a_power_that_overflows_is_refused():
    """Trap exp_overflow of the curve: a finite discharge at the test bounds, a
    refusal beyond them."""
    found = rating_discharge([1.0e4], 1.0e6, 20.0, -1.0e4)
    assert np.all(np.isfinite(found))
    with pytest.raises(InvalidParameterError) as caught:
        rating_discharge([270.0], 0.012, 200.0, 32.0)
    assert caught.value.details["constraint"] == "finite_discharge"


def test_a_curve_at_its_bound_is_finite():
    """Trap singular_at_bound of the fit: the least squares at H0's bound below the
    lowest level, whose pair has no flow."""
    levels = np.array([60.0, 70.0, 85.0, 100.0, 120.0, 150.0, 190.0, 240.0])
    discharges = 0.05 * (levels - 60.0) ** 1.5
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OutsideTypicalRange)
        fit = fit_rating_curve(levels, discharges, 50.0)

    assert all(math.isfinite(v) for v in (fit.a, fit.b, fit.h0, fit.r_squared))
    assert fit.h0 < 60.0
    assert_within(
        [fit.h0, fit.b],
        [60.0, 1.5],
        abs=1e-3,
        reason="the bound lies 2^-30 of 256 cm below the lowest level; there the sum "
        "of squares changes by less than the search's tolerance over 1e-4 cm, where "
        "it stops",
    )


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_levels_at_their_test_bounds_fit_or_are_refused():
    """Trap exp_overflow of the fit: the search runs on normalised levels, so levels at
    their test bounds fit; where the curve overflows the precondition refuses it."""
    levels = np.array([-1.0e4, -5.0e3, 0.0, 5.0e3, 1.0e4])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OutsideTypicalRange)
        fit = fit_rating_curve(levels, 1.0e-3 * (levels + 1.2e4) ** 1.5, -1.1e4)
        assert_within(fit.b, 1.5, rel=1e-6, reason="noise-free pairs over 20,000 cm")
        with pytest.raises(InvalidParameterError) as caught:
            fit_rating_curve([1.0e4, 9.99e3, 9.98e3], [1.0e6, 0.0, 1.0], -1.0e4)
    assert caught.value.details["reason"] == "precondition_failed"


def test_a_search_that_does_not_settle_is_refused(monkeypatch):
    """Trap unbounded_iteration: the bounded count of the search ends in the refusal
    of the precondition least_squares_minimum, not in a calculation error."""
    with pytest.raises(InvalidParameterError) as caught:
        fit_rating_curve(
            list(rating_curve._UNSETTLED_H), list(rating_curve._UNSETTLED_Q), 9.0
        )
    assert caught.value.code == "validation_error"
    assert caught.value.details["constraint"] == "least_squares_minimum"

    def no_convergence(*args, **kwargs):
        raise RuntimeError("Optimal parameters not found: maxfev exceeded")

    rating_curve._normalised_search.cache_clear()
    monkeypatch.setattr(rating_curve, "curve_fit", no_convergence)
    with pytest.raises(InvalidParameterError) as caught:
        fit_rating_curve(PAIRS_H, PAIRS_Q, 41.2)
    rating_curve._normalised_search.cache_clear()
    assert caught.value.details["constraint"] == "least_squares_minimum"


def test_many_pairs_keep_their_sums():
    """Trap many_small_terms: 20,000 pairs, R^2 and s against math.fsum."""
    rng = np.random.default_rng(20261119)
    levels = np.sort(rng.uniform(40.0, 330.0, 20_000))
    discharges = 0.012 * (levels - 30.0) ** 1.62 * rng.lognormal(0.0, 0.05, 20_000)
    fit = fit_rating_curve(levels, discharges, 10.0)
    residuals = discharges - fit.a * (levels - fit.h0) ** fit.b
    centre = math.fsum(residuals.tolist()) / residuals.size
    spread = math.sqrt(
        math.fsum(((residuals - centre) ** 2).tolist()) / (residuals.size - 1)
    )
    mean = math.fsum(discharges.tolist()) / discharges.size
    total = math.fsum(((discharges - mean) ** 2).tolist())

    assert_within(
        [fit.r_squared, fit.std_residuals],
        [1.0 - math.fsum((residuals**2).tolist()) / total, spread],
        rel=1e-12,
        reason="pairwise sums of 20,000 terms against math.fsum: a few units of "
        "2^-53 times log2 of the count",
    )


def test_a_large_mean_discharge_keeps_r_squared():
    """Trap moment_cancellation: SS_tot of discharges near 1e6 with a spread of a few
    m3/s, against exact fractions."""
    levels = [300.0, 310.0, 320.0, 330.0, 340.0, 350.0, 360.0, 370.0]
    discharges = [1.0e6 + 0.5 * (h - 290.0) ** 1.2 for h in levels]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OutsideTypicalRange)
        fit = fit_rating_curve(levels, discharges, 280.0)
    exact = [Fraction(q) for q in discharges]
    mean = sum(exact, Fraction(0)) / len(exact)
    total = sum(((q - mean) ** 2 for q in exact), Fraction(0))
    fitted = [
        Fraction(q) - Fraction(fit.a * (h - fit.h0) ** fit.b)
        for h, q in zip(levels, discharges, strict=True)
    ]
    squares = sum((r * r for r in fitted), Fraction(0))

    assert_within(
        fit.r_squared,
        float(1 - squares / total),
        abs=1e-6,
        reason="deviations from the mean, not E[Q^2] - E[Q]^2: SS_tot of a spread of "
        "a few m3/s under a mean of 1e6 keeps nine digits, the residuals' own rounding "
        "at 1e6 is 1e-10 m3/s",
    )


# --- the library's classes, notices and versions -------------------------------------


def test_a_fit_of_few_gaugings_says_so():
    """WMO-No. 1044's 12 to 15 gaugings: the notice of the applicability constraint."""
    with pytest.warns(OutsideTypicalRange) as caught:
        fit_rating_curve(*NLS_SETS["doc_negative_stages"])
    notices = [w.message for w in caught if isinstance(w.message, OutsideTypicalRange)]
    assert [n.details for n in notices] == [
        {
            "method": "rating_curve_fit",
            "parameter": "gaugings",
            "field": "gaugings",
            "value": 6,
            "minimum": 12,
            "maximum": None,
            "constraint": "enough_gaugings",
            "condition": (
                "n >= 12: at least 12 to 15 gaugings of the period of analysis"
            ),
            "source": rating_curve._GAUGINGS.text(),
        }
    ]
    assert "gaugings=6 is below its typical minimum 12" in str(notices[0])


def test_twelve_gaugings_give_no_notice():
    with warnings.catch_warnings():
        warnings.simplefilter("error", OutsideTypicalRange)
        fit_rating_curve(PAIRS_H[:12], PAIRS_Q[:12], 41.2)


@pytest.mark.parametrize(
    "call",
    [
        lambda: rating_curve_plausibility(PAIRS_H, 1.62, 32.0),
        lambda: rybczynski_zones([0.0, 10.0, 20.0], [3.0, 1.0]),
    ],
    ids=["plausibility", "zones"],
)
def test_an_unreferenced_formula_says_so_on_every_result(call):
    with pytest.warns(UnreferencedFormula) as caught:
        call()
    assert [w.message.level for w in caught] == ["info"]


def test_the_class_refuses_a_start_above_the_levels_on_its_option():
    with pytest.raises(InvalidParameterError) as caught:
        RatingCurve(PAIRS_H, PAIRS_Q).fit(h0_initial=62.0)
    assert caught.value.details["option"] == "h0_initial"
    assert caught.value.details["constraint"] == "start_below_levels"


def test_the_zones_of_the_class_are_those_of_its_histogram():
    levels = np.linspace(100.0, 300.0, 400) ** 1.01
    analysis = WaterLevelFrequency(levels, bin_width=20.0)
    histogram = analysis.frequency_distribution()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UnreferencedFormula)
        assert analysis.rybczynski_zones() == rybczynski_zones(
            histogram.bin_edges, histogram.counts
        )


def test_the_formulas_record_their_versions():
    with recording() as used, warnings.catch_warnings():
        warnings.simplefilter("ignore")
        RatingCurve(PAIRS_H, PAIRS_Q).fit(h0_initial=41.2, remove_outliers=True)
        rating_curve_plausibility(PAIRS_H, 1.62, 32.0)
        WaterLevelFrequency(PAIRS_H, 20.0).rybczynski_zones()

    assert used == {spec.name: spec.formula_version for spec, _ in FAMILY}
