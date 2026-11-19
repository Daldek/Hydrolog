"""The regime, seasonality and harmonics of a station against their specs (CMP §6).

Range, type and property tests are generated from the five specs (CMP-6.5); the limits
hold their oracles: exact fractions of the Pardé means and of the spring share, the
criteria of Dynowska's types on the printed decimals, the quadrant rules of Bayliss and
Jones (1992), exact harmonic signals and the normal equations in fractions (CMP-6.2).
The reference cases (``tests/fixtures/formulas/regime-cases.json``) are IMGW-PIB's
means of Kłodzko in 2010, the mean coefficients of Wrzesiński's (2017, 2018) Tables 1
and Kłodzko's type of Perz (2019) (CMP-6.1). The generic strategies draw the arrays of
a series apart, so they rarely draw days with their months or dates with their years:
the strategies below draw series the formulas compute, for the properties. SciPy's
``circmean`` is the established oracle of the circular mean (CMP-6.3).
"""

import calendar
import csv
import gzip
import math
from datetime import date
from fractions import Fraction
from pathlib import Path

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import given
from scipy import stats as scipy_stats

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.catalog import run_command
from hydrolog.exceptions import InvalidParameterError
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
from hydrolog.statistics._hydrological_year import hydrological_day_of_year
from hydrolog.statistics.harmonics import (
    HARMONIC_FIT,
    _normal_equations,
    harmonic_fit,
)
from hydrolog.statistics.regime import (
    DYNOWSKA_REGIME_TYPE,
    HYDROLOGICAL_MONTHS,
    PARDE_COEFFICIENTS,
    SPRING_SHARE,
    _calendar_months,
    _rational_means,
    dynowska_regime_type,
    flow_regime,
    parde_coefficients,
    spring_share,
)
from hydrolog.statistics.seasonality import (
    CIRCULAR_MEAN,
    _times_of,
    circular_mean,
    circular_mean_date,
)

pytestmark = pytest.mark.formula

FIXTURES = Path(__file__).parents[1] / "fixtures"
CASES = FIXTURES / "formulas" / "regime-cases.json"
KLODZKO = FIXTURES / "imgw_klodzko"
WARSZAWA = FIXTURES / "warszawa_okecie_1991_2020.csv.gz"

FORMULAS = (
    (PARDE_COEFFICIENTS, parde_coefficients),
    (SPRING_SHARE, spring_share),
    (DYNOWSKA_REGIME_TYPE, dynowska_regime_type),
    (CIRCULAR_MEAN, circular_mean),
    (HARMONIC_FIT, harmonic_fit),
)
PERIOD = 365.25


def _generated() -> list:
    return [
        pytest.param(spec, function, param.values[0], id=f"{spec.name}:{param.id}")
        for spec, function in FORMULAS
        for param in range_cases(spec) + type_cases(spec)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec, function, case: Case):
    run_case(spec, function, case, ERRORS)


@pytest.mark.parametrize(
    ("spec", "function"), FORMULAS, ids=[spec.name for spec, _ in FORMULAS]
)
def test_limits_and_oracles(spec, function):
    assert_limits(spec, function, ERRORS)


@pytest.mark.parametrize(
    ("spec", "function", "case"),
    [
        pytest.param(spec, function, case, id=case.case_id)
        for spec, function in FORMULAS
        for case in load_cases(CASES, spec.name)
    ],
)
def test_reference_cases(spec, function, case: ReferenceCase):
    assert_case(spec, function, case, ERRORS)


@given(inputs=strategies(PARDE_COEFFICIENTS))
def test_properties_of_parde_coefficients(inputs):
    assert_property_contract(PARDE_COEFFICIENTS, parde_coefficients, inputs, ERRORS)
    assert_properties(PARDE_COEFFICIENTS, parde_coefficients, inputs, ERRORS)


@given(inputs=strategies(SPRING_SHARE))
def test_properties_of_spring_share(inputs):
    assert_property_contract(SPRING_SHARE, spring_share, inputs, ERRORS)
    assert_properties(SPRING_SHARE, spring_share, inputs, ERRORS)


@given(inputs=strategies(DYNOWSKA_REGIME_TYPE))
def test_properties_of_dynowska_regime_type(inputs):
    assert_property_contract(DYNOWSKA_REGIME_TYPE, dynowska_regime_type, inputs, ERRORS)
    assert_properties(DYNOWSKA_REGIME_TYPE, dynowska_regime_type, inputs, ERRORS)


@given(inputs=strategies(CIRCULAR_MEAN))
def test_properties_of_circular_mean(inputs):
    assert_property_contract(CIRCULAR_MEAN, circular_mean, inputs, ERRORS)
    assert_properties(CIRCULAR_MEAN, circular_mean, inputs, ERRORS)


@given(inputs=strategies(HARMONIC_FIT))
def test_properties_of_harmonic_fit(inputs):
    assert_property_contract(HARMONIC_FIT, harmonic_fit, inputs, ERRORS)
    assert_properties(HARMONIC_FIT, harmonic_fit, inputs, ERRORS)


# --- strategies of series the formulas compute -------------------------------------


@st.composite
def daily_series(draw) -> dict[str, np.ndarray]:
    """One to three years of daily discharge from a seeded gamma, some days missing."""
    rng = np.random.default_rng(draw(st.integers(0, 2**32 - 1)))
    start = draw(st.dates(min_value=date(1951, 1, 1), max_value=date(2020, 12, 31)))
    count = draw(st.integers(365, 3 * 365 + 40))
    days = np.datetime64(start) + np.arange(count)
    flows = rng.gamma(draw(st.floats(0.3, 3.0)), draw(st.floats(0.5, 80.0)), count)
    flows[rng.random(count) < draw(st.floats(0.0, 0.3))] = np.nan
    if draw(st.booleans()):
        flows[rng.integers(0, count)] = 0.0  # a dry day
    return {"values": flows, "month": _calendar_months(days)}


@st.composite
def dates_on_their_years(draw) -> dict[str, list[float]]:
    """One to eighty dates of 1900-2100 as times in their years."""
    dates = draw(
        st.lists(
            st.dates(min_value=date(1900, 1, 1), max_value=date(2100, 12, 31)),
            min_size=1,
            max_size=80,
        )
    )
    elapsed, length = _times_of([str(day) for day in dates])
    return {"elapsed_days": elapsed, "year_days": length}


@st.composite
def annual_cycles(draw) -> dict[str, object]:
    """One to three hydrological years of a noisy annual cycle with a gap of up to
    250 days, which the precondition year_covered refuses beyond P / (2 K)."""
    rng = np.random.default_rng(draw(st.integers(0, 2**32 - 1)))
    years = draw(st.integers(1, 3))
    first = draw(st.integers(1952, 2090))
    dates = np.arange(
        np.datetime64(f"{first - 1}-11-01"), np.datetime64(f"{first + years - 1}-11-01")
    )
    day = hydrological_day_of_year(dates).astype(np.float64)
    t = day - 1.0
    values = draw(st.floats(-5.0, 20.0)) + draw(st.floats(0.0, 12.0)) * np.cos(
        2.0 * np.pi * (t - draw(st.floats(0.0, 365.0))) / PERIOD
    )
    values = values + rng.normal(0.0, draw(st.floats(0.0, 3.0)), values.size)
    gap = draw(st.integers(0, 250))
    start = draw(st.integers(0, 364))
    values[((t - start) % 365.0) < gap] = np.nan
    return {
        "day_of_year": day,
        "values": values,
        "n_harmonics": draw(st.integers(1, 4)),
    }


@given(inputs=daily_series())
def test_properties_of_daily_series(inputs):
    assert_property_contract(PARDE_COEFFICIENTS, parde_coefficients, inputs, ERRORS)
    assert_properties(PARDE_COEFFICIENTS, parde_coefficients, inputs, ERRORS)


@given(inputs=dates_on_their_years())
def test_properties_of_dates(inputs):
    assert_property_contract(CIRCULAR_MEAN, circular_mean, inputs, ERRORS)
    assert_properties(CIRCULAR_MEAN, circular_mean, inputs, ERRORS)


@given(inputs=annual_cycles())
def test_properties_of_annual_cycles(inputs):
    assert_property_contract(HARMONIC_FIT, harmonic_fit, inputs, ERRORS)
    assert_properties(HARMONIC_FIT, harmonic_fit, inputs, ERRORS)


# --- Pardé's coefficients ------------------------------------------------------------


def _kłodzko_2010() -> tuple[list[float], list[float]]:
    rows = list(
        csv.reader((KLODZKO / "imgw_150160180_codz_2010.csv").open(encoding="utf-8"))
    )[1:]
    days = []
    for row in rows:
        month = int(row[9])
        year = int(row[3]) - 1 if month >= 11 else int(row[3])
        days.append((date(year, month, int(row[5])), float(row[7])))
    days.sort()
    return [flow for _, flow in days], [float(day.month) for day, _ in days]


def test_the_coefficients_do_not_sum_to_twelve():
    """The convention of the annual mean: the coefficients weighted by the days of
    their months average one (Σ n_m K_m = N), so twelve of them sum to 12 only when
    every month has as many days; a gapless year of Kłodzko sums to 12.00029."""
    values, month = _kłodzko_2010()
    out = parde_coefficients(values, month)
    monthly, annual = _rational_means(values, month)
    exact_sum = sum((mean / annual for mean in monthly), Fraction(0))

    assert exact_sum != 12
    assert_within(
        math.fsum(out.parde.tolist()),
        float(exact_sum),
        rel=2e-15,
        reason="twelve coefficients of three roundings each against their exact sum",
    )
    assert abs(float(exact_sum) - 12.0) > 1e-4


def test_the_perz_coefficients_are_those_of_the_imgw_monthly_means():
    """The inputs of Perz's case come from the monthly means in the fixture: each
    month's mean of its years over the mean of all months weighted by their days."""
    rows = list(
        csv.reader(
            (KLODZKO / "imgw_150160180_mies_1971_2015.csv").open(encoding="utf-8")
        )
    )[1:]
    means: dict[int, list[Fraction]] = {month: [] for month in HYDROLOGICAL_MONTHS}
    weighted, days = Fraction(0), 0
    for row in rows:
        if row[5].strip() != "2" or float(row[7]) >= 99999:
            continue
        year, month, flow = int(row[3]), int(row[9]), Fraction(row[7])
        means[month].append(flow)
        calendar_year = year - 1 if month >= 11 else year
        length = calendar.monthrange(calendar_year, month)[1]
        weighted += flow * length
        days += length
    annual = weighted / days
    exact = [sum(means[m], Fraction(0)) / len(means[m]) / annual for m in means]
    (case,) = [
        case
        for case in load_cases(CASES, "dynowska_regime_type")
        if case.case_id == "perz2019_nysa_klodzka_klodzko_1971_2015"
    ]

    assert {len(years) for years in means.values()} == {44}
    assert_within(
        case.inputs["parde"],
        [float(value) for value in exact],
        rel=5e-15,
        reason="the audit's sequential float sums of 44 monthly means, up to 44 "
        "roundings, against exact fractions",
    )


def test_a_tiny_or_vanishing_mean():
    """Trap singular_at_bound: Q̄ divides every coefficient."""
    month = [float(m) for m in HYDROLOGICAL_MONTHS for _ in range(2)]
    tiny = parde_coefficients([0.0] * 23 + [1e-300], month)
    with pytest.raises(InvalidParameterError) as no_flow:
        parde_coefficients([0.0] * 24, month)
    with pytest.raises(InvalidParameterError) as underflow:
        parde_coefficients([0.0] * 23 + [5e-324], month)

    assert_within(
        tiny.parde[-1],
        12.0,
        rel=4.5e-16,
        reason="October holds the whole flow of its two days: (q/2)/(q/24), two "
        "roundings",
    )
    assert np.isfinite(tiny.parde).all()
    for refused in (no_flow, underflow):
        assert refused.value.details["reason"] == "precondition_failed"
        assert refused.value.details["constraint"] == "positive_mean"


def test_gaps_are_left_out_of_both_means():
    """Trap gap_propagation: a day without a value counts in neither mean."""
    values, month = _kłodzko_2010()
    gaps = np.array(values)
    gaps[::7] = np.nan
    kept = ~np.isnan(gaps)
    with_gaps = parde_coefficients(gaps, month)
    without = parde_coefficients(gaps[kept], np.array(month)[kept])

    assert np.array_equal(with_gaps.parde, without.parde)
    assert with_gaps.annual_mean == without.annual_mean


def test_a_century_of_days_keeps_the_exact_means():
    """Trap many_small_terms: 36,525 days summed by math.fsum against fractions."""
    rng = np.random.default_rng(20261119)
    days = np.arange(np.datetime64("1920-11-01"), np.datetime64("2020-11-01"))
    values = np.round(rng.gamma(2.0, 9.0, days.size), 3)
    month = _calendar_months(days)
    out = parde_coefficients(values, month)
    monthly, annual = _rational_means(values.tolist(), month.tolist())

    assert days.size == 36525
    assert_within(
        [*out.monthly_mean.tolist(), out.annual_mean],
        [*(float(mean) for mean in monthly), float(annual)],
        rel=4.5e-16,
        reason="a correctly rounded sum and one division against exact fractions",
    )


def test_flow_regime_refuses_a_negative_or_infinite_discharge():
    """A negative discharge was averaged and an infinite one taken for a gap (0.8)."""
    dates = np.datetime64("2020-11-01") + np.arange(365)
    for wrong in (-1.0, math.inf):
        flows = np.ones(365)
        flows[40] = wrong
        with pytest.raises(InvalidParameterError) as refused:
            flow_regime(flows, dates)

        assert refused.value.details["reason"] == "outside_physical_range"


# --- Dynowska's type -----------------------------------------------------------------


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(case, id=case.case_id)
        for case in load_cases(CASES, "dynowska_regime_type")
        if case.case_id.startswith("wrzesinski")
    ],
)
def test_the_rows_of_the_tables_lie_beyond_their_rounding_from_every_limit(
    case: ReferenceCase,
):
    """The class of a printed row holds at every corner of its rounding (CMP-6.1)."""
    half = case.printed_precision["parde"] / 2
    parde = np.array(case.inputs["parde"])
    deciding = [HYDROLOGICAL_MONTHS.index(m) for m in (3, 4, 6, 7, 8)]
    for corner in range(2 ** len(deciding)):
        moved = parde.copy()
        for bit, index in enumerate(deciding):
            moved[index] += half if corner >> bit & 1 else -half
        assert dynowska_regime_type(moved).code == case.expected["code"]


# --- the circular mean ----------------------------------------------------------------


def _random_dates(seed: int, size: int) -> list[str]:
    rng = np.random.default_rng(seed)
    days = np.datetime64("1951-01-01") + rng.integers(0, 365 * 70, size)
    return [str(day) for day in days]


AUDIT_DATES = [
    "2001-03-15",
    "2002-03-20",
    "2003-04-02",
    "2004-02-28",
    "2005-03-30",
    "2006-12-30",
    "2007-01-05",
]


@pytest.mark.parametrize("seed", range(12))
def test_the_mean_direction_is_scipys(seed):
    """scipy.stats.circmean of the same angles (CMP-6.3): both take the angles of
    Bayliss and Jones's half-day offset and give the direction in [0, 2 pi)."""
    dates = AUDIT_DATES if seed == 0 else _random_dates(seed, 3 + 5 * seed)
    elapsed, length = _times_of(dates)
    angles = 2.0 * np.pi * np.array(elapsed) / np.array(length)
    out = circular_mean(elapsed, length)
    expected = scipy_stats.circmean(angles, high=2.0 * np.pi, low=0.0) / (2.0 * np.pi)
    turn = (out.mean_fraction - expected + 0.5) % 1.0 - 0.5

    assert out.concentration > 1e-3
    assert_within(
        turn,
        0.0,
        abs=1e-12,
        reason="SciPy's mean of the unit vectors against NumPy's: a few ulps of the "
        "sums, turned by that over r",
    )


def test_the_audit_sample_and_hall_and_bloschls_convention():
    """The audit's seven dates give its scipy mean day; Hall and Blöschl (2018) put a
    date at its day D, not at D - 0.5, which moves the mean by about 0.0001 day."""
    mean = circular_mean_date(AUDIT_DATES)
    days = np.asarray(AUDIT_DATES, dtype="datetime64[D]")
    years = days.astype("datetime64[Y]")
    day = (days - years.astype("datetime64[D]")).astype(np.int64) + 1
    length = np.array([366 if d.startswith("2004") else 365 for d in AUDIT_DATES])
    hall = 2.0 * np.pi * day / length
    hall_day = (
        (math.atan2(np.mean(np.sin(hall)), np.mean(np.cos(hall))) % (2.0 * math.pi))
        * PERIOD
        / (2.0 * math.pi)
    )

    assert_within(
        [mean.mean_day, mean.concentration],
        [58.65241753873519, 0.8187674334145761],
        abs=1e-9,
        reason="the audit's scipy.stats.circmean of the same angles (case "
        "circular_mean_scipy_and_hall_bloschl), a few ulps apart",
    )
    assert mean.mean_date == "02-28"
    assert_within(
        hall_day - mean.mean_day,
        1e-4,
        abs=1e-5,
        reason="the offset of half a day on years of 365 and 366 days against the "
        "mean year: 0.5 (1 - 365.25 / L) per date, the audit's 0.0001 day",
    )


def test_no_direction_gives_a_fraction_in_the_year():
    """Trap singular_at_bound: opposite dates have no direction (Hall and Blöschl);
    r is the rounding left of zero and the direction stays a fraction of the year."""
    for elapsed, length in (
        ([0.5, 183.5], [366.0, 366.0]),
        ([10.0, 192.5], [365.0] * 2),
    ):
        out = circular_mean(elapsed, length)

        assert out.concentration < 4e-16
        assert 0.0 <= out.mean_fraction <= 1.0


def test_many_dates_keep_their_sums():
    """Trap many_small_terms: 100,000 dates, NumPy's pairwise sums against fsum."""
    elapsed, length = _times_of(_random_dates(20261119, 100_000))
    angles = [2.0 * math.pi * t / n for t, n in zip(elapsed, length, strict=True)]
    x = math.fsum(math.cos(a) for a in angles) / len(angles)
    y = math.fsum(math.sin(a) for a in angles) / len(angles)
    out = circular_mean(elapsed, length)

    assert_within(
        out.concentration,
        math.hypot(x, y),
        abs=1e-15,
        reason="pairwise sums of 100,000 terms of at most one: about log2(n) ulps",
    )


def test_small_samples_ties_and_constant_dates():
    """CMP-6.7: one date, repeated dates and a constant series."""
    one = circular_mean_date(["2010-06-15"])
    tied = circular_mean_date(["2010-06-15", "2011-06-15", "2009-06-15"])
    leap = circular_mean_date(["2010-06-15", "2012-06-14"])
    pair = circular_mean_date(["2010-06-15", "2011-06-15", "2010-12-15"])

    assert (one.mean_date, tied.mean_date, leap.mean_date) == ("06-15",) * 3
    assert_within(
        [one.concentration, tied.concentration],
        [1.0, 1.0],
        abs=4.5e-16,
        reason="the vector of one angle, or of one angle thrice, has the length of "
        "its rounded sine and cosine",
    )
    assert 0.9999 < leap.concentration < 1.0  # day 166 of 365 and of 366 days
    assert 0.0 < pair.concentration < 1.0 / 3.0 + 1e-3


# --- the harmonic fit -----------------------------------------------------------------


def _year() -> tuple[np.ndarray, np.ndarray]:
    day = np.arange(1.0, 366.0)
    return day, day - 1.0


def test_the_delegated_least_squares_recover_an_exact_signal():
    """The smoke case of numpy.linalg.lstsq (CMP-1.2), on its own."""
    dates = np.arange(np.datetime64("2014-11-01"), np.datetime64("2019-11-01"))
    t = hydrological_day_of_year(dates).astype(np.float64) - 1.0
    signal = (
        10.0
        + 5.0 * np.cos(2.0 * np.pi * (t - 100.0) / PERIOD)
        + 2.0 * np.cos(4.0 * np.pi * (t - 30.0) / PERIOD)
    )
    columns = [np.ones_like(t)]
    for k in (1, 2):
        columns += [
            np.cos(2 * np.pi * k * t / PERIOD),
            np.sin(2 * np.pi * k * t / PERIOD),
        ]
    a0, a1, b1, a2, b2 = np.linalg.lstsq(np.column_stack(columns), signal, rcond=None)[
        0
    ]

    assert_within(
        [a0, math.hypot(a1, b1), math.hypot(a2, b2)],
        [10.0, 5.0, 2.0],
        abs=1e-8,
        reason="least squares of an exact signal of 1,826 days: rounding only",
    )


def test_a_constant_series_is_refused():
    """R2 and the phases of a constant series do not exist; 0.8 gave r_squared null
    and phases of the rounding noise (day 366.1 of a cycle of 7.0)."""
    day, _ = _year()
    with pytest.raises(InvalidParameterError) as refused:
        harmonic_fit(day, np.full(365, 7.0), 2)

    assert refused.value.details["reason"] == "precondition_failed"
    assert refused.value.details["constraint"] == "values_not_all_equal"


def test_a_season_of_values_is_refused():
    """Trap unbounded_iteration: 121 days of a year leave a gap of 244 days, beyond
    P / 4 for two harmonics; 0.8 fitted them with amplitudes of 1.8 and 4.6 and the
    shares -0.63 and 1.47."""
    day, t = _year()
    rng = np.random.default_rng(1)
    values = 10 + 8 * np.cos(2 * np.pi * (t - 250) / PERIOD) + rng.normal(0, 1, 365)
    values[(day < 180) | (day > 300)] = np.nan
    with pytest.raises(InvalidParameterError) as refused:
        harmonic_fit(day, values, 2)

    assert refused.value.details["constraint"] == "year_covered"


def test_the_shares_of_a_year_with_a_gap_lie_between_zero_and_one():
    """A gap of 55 days, within P / 6 for three harmonics: 0.8 cut the whole fit and
    gave the second harmonic the share -2.6e-5; the nested fits give shares in [0, 1]
    that add up to R2."""
    day, t = _year()
    rng = np.random.default_rng(27)
    values = 10 + 8 * np.cos(2 * np.pi * (t - 250) / PERIOD) + rng.normal(0, 2, 365)
    start = int(rng.integers(0, 365))  # 272: the gap of the search for a negative share
    values[((t - start) % 365) < 55] = np.nan
    fit = harmonic_fit(day, values, 3)
    shares = [harmonic.explained_variance for harmonic in fit.harmonics]

    assert all(share is not None and 0.0 <= share <= 1.0 for share in shares)
    assert_within(
        math.fsum(share for share in shares if share is not None),
        fit.r_squared,
        abs=1e-14,
        reason="the shares are differences of nested R2 that add up to the last",
    )


def test_a_missing_harmonic_has_a_finite_phase():
    """Trap singular_at_bound: a pure annual cycle has no half-year harmonic; its
    phase is noise, but finite and on the half-year."""
    day, t = _year()
    fit = harmonic_fit(day, 4.0 + 3.0 * np.cos(2 * np.pi * (t - 80) / PERIOD), 2)
    second = fit.harmonics[1]

    assert second.amplitude < 1e-13
    assert 1.0 <= second.phase_day <= 1.0 + PERIOD / 2


def test_gaps_are_left_out_of_the_fit():
    """Trap gap_propagation: a NaN day is left out, as if it were not given."""
    day, t = _year()
    values = 5.0 + 2.0 * np.sin(2 * np.pi * t / PERIOD) + 0.1 * np.cos(t)
    values[::5] = np.nan
    kept = ~np.isnan(values)
    with_gaps = harmonic_fit(day, values, 2)
    without = harmonic_fit(day[kept], values[kept], 2)

    assert with_gaps == without


def test_thirty_years_of_temperature_match_the_normal_equations():
    """Trap many_small_terms: 10,958 days of Warszawa-Okęcie, LAPACK against the normal
    equations summed by math.fsum and solved in fractions."""
    with gzip.open(WARSZAWA, "rt", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    dates = np.array([row["date"] for row in rows], dtype="datetime64[D]")
    values = np.array([float(row["Tmean [degC]"]) for row in rows])
    day = hydrological_day_of_year(dates).astype(np.float64)
    fit = harmonic_fit(day, values, 2)
    exact = _normal_equations(day - 1.0, values, 2)

    assert_within(
        [fit.mean, *fit.amplitudes],
        [
            float(exact[0]),
            math.hypot(float(exact[1]), float(exact[2])),
            math.hypot(float(exact[3]), float(exact[4])),
        ],
        abs=1e-10,
        reason="10,958 rows of a design of condition near one: LAPACK within a few "
        "hundred ulps of the exact solution",
    )


def test_a_large_offset_keeps_the_amplitudes():
    """Trap moment_cancellation: a cycle on top of 1e6 keeps its amplitudes and R2."""
    day, t = _year()
    rng = np.random.default_rng(5)
    cycle = 3.0 * np.cos(2 * np.pi * (t - 40) / PERIOD) + rng.normal(0, 0.5, 365)
    near = harmonic_fit(day, cycle, 2)
    far = harmonic_fit(day, 1.0e6 + cycle, 2)

    assert_within(
        [far.mean - 1.0e6, *far.amplitudes, far.r_squared],
        [near.mean, *near.amplitudes, near.r_squared],
        abs=1e-8,
        reason="values of 1e6 round to 1.2e-10; the deviations from the mean keep "
        "the sum of squares",
    )


def test_small_samples_and_ties():
    """CMP-6.7: the fewest values a fit takes and a day repeated over years."""
    day = np.array([1, 37, 73, 109, 145, 181, 217, 253, 289, 325], dtype=float)
    values = 10.0 + 4.0 * np.cos(2 * np.pi * (day - 1 - 120) / PERIOD)
    fewest = harmonic_fit(day, values, 2)
    tied = harmonic_fit(np.concatenate([day, day]), np.concatenate([values, values]), 2)

    assert_within(
        [fewest.mean, fewest.amplitudes[0], tied.mean, tied.amplitudes[0]],
        [10.0, 4.0, 10.0, 4.0],
        abs=1e-12,
        reason="an exact cycle on ten days, and the same days twice",
    )


def test_a_year_the_fit_refuses_is_named():
    """stats harmonics names a year with enough days but a gap the harmonics cannot
    span (notice years_without_fit), apart from a short one (short_years_left_out)."""
    days = np.datetime64("2019-11-01") + np.arange(731 + 250)
    t = np.arange(days.size) % 365
    values = 8.0 + 6.0 * np.cos(2 * np.pi * (t - 200) / PERIOD)
    kept = np.ones(days.size, dtype=bool)
    kept[366 + 30 : 366 + 30 + 62] = False  # 62 days of 2021 missing: a gap of 63
    result = run_command(
        "stats harmonics",
        {
            "values": values[kept].tolist(),
            "dates": [str(day) for day in days[kept]],
            "harmonics": 3,
        },
    ).to_dict()
    notices = {notice["code"]: notice["details"] for notice in result["notices"]}

    assert [row["year"] for row in result["result"]["years"]] == [2020]
    assert notices["years_without_fit"] == {
        "count": 1,
        "harmonics": 3,
        "max_gap_days": PERIOD / 6,
        "years": [2021],
    }
    assert notices["short_years_left_out"]["years"] == [2022]


def test_the_formulas_record_their_versions():
    month = [float(m) for m in HYDROLOGICAL_MONTHS for _ in range(2)]
    day, t = _year()
    with recording() as used:
        parde_coefficients([3.0] * 24, month)
        spring_share([10.0] * 12)
        dynowska_regime_type([1.0] * 12)
        circular_mean([100.5], [365.0])
        harmonic_fit(day, np.cos(2 * np.pi * t / PERIOD), 1)

    assert used == {spec.name: spec.formula_version for spec, _ in FORMULAS}
