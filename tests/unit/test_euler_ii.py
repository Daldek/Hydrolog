"""The Euler type II design storm of ATV-DVWK-A 118 (``EulerIIHietogram``).

Each reference case is a published storm or an oracle of the Nogat audit of
2026-11-18 (research ``hyetographs.md`` section 2.3, cases ``euler2-...``). The
numbers are copied as their sources print them, and each tolerance follows from that
printing (CMP-6.1): half a unit of the last printed digit of the compared value plus
the rounding of the printed inputs it is built from.
"""

import json
import math
from pathlib import Path

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.precipitation import EulerIIHietogram

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

# DWD, Malitz G. (2009) Stark- und Extremniederschlag im Kurzzeitbereich, slides of the
# 2. Trierer Workshop: Folie 18 and 19, the 5-min depths [mm] of 60-min Euler type II
# storms, printed to 0.1 mm. Folie 17: "Die Summe der drei größten Werte ist die
# Starkniederschlagshöhe für D = 15 min": the depth of m*5 min is the sum of the m
# largest values, which gives the curve the storm was built from.
MALITZ_FOLIE_18_MM = [1.8, 2.2, 3.1, 10.4, 1.6, 1.3, 1.2, 1.2, 1.0, 1.0, 0.9, 0.9]
MALITZ_FOLIE_19_MM = [1.2, 1.8, 2.9, 5.6, 0.9, 0.7, 0.5, 0.4, 0.4, 0.3, 0.2, 0.2]
MALITZ_TOLERANCE_MM = 0.05  # half of the printed 0.1 mm

# itwh KOSTRA-DWD 2010R 3.2.3 printouts of Göllheim (Rasterfeld Spalte 18, Zeile 73,
# T = 5 a), "Anhang III" of a planning procedure of Rhineland-Palatinate, pp. 2-6: the
# KOSTRA depths [mm] (input, p. 6, to 0.1 mm) and the Euler type II storms of 30, 60
# and 90 min (pp. 2-5, to 0.01 mm). A block is the difference of two depths printed to
# 0.1 mm (each within 0.05 mm of itwh's own), so it is right within 0.1 mm plus the
# 0.005 mm of its own printing.
GOELLHEIM_KOSTRA_MM = {
    5: 9.5,
    10: 13.9,
    15: 16.9,
    20: 19.2,
    30: 22.4,
    45: 25.6,
    60: 27.9,
    90: 30.0,
}
GOELLHEIM_STORMS_MM = {
    30: [4.44, 9.51, 3.00, 2.23, 1.76, 1.44],
    60: [2.23, 3.00, 4.44, 9.51, 1.76, 1.44, 1.23, 1.06, 0.93, 0.84, 0.76, 0.70],
    90: [1.44, 1.76, 2.23, 3.00, 4.44, 9.51, 1.23, 1.06, 0.93, 0.84, 0.76, 0.70]
    + [0.40, 0.38, 0.35, 0.34, 0.32, 0.30],
}
GOELLHEIM_TOLERANCE_MM = 0.005 + 2 * 0.05

# itwh KOSTRA-DWD 2020 4.2.1 "Modellregen", Aurich (Zeile 84, Spalte 110), Euler Typ 2,
# 9 h, 5 min, "Zuschlag Toleranzwert UC" (city of Aurich, B-Plan 393, Anhang 1.2): the
# peak is interval 33 (160-165 min), 11,00 mm (T = 3 a) and 14,99 mm (T = 10 a), printed
# to 0.01 mm; the totals 40,8 and 55,6 mm to 0.1 mm. Its other blocks carry itwh's
# surcharge (negative depths before the KOSTRA steps 90, 180, 240 and 360 min) and are
# not compared; that they stand where their durations put them is why the increments
# are not sorted.
AURICH = {"T3": (11.00, 40.8), "T10": (14.99, 55.6)}

# Kaźmierczak B., Kotowski A. (2012) Weryfikacja przepustowości kanalizacji deszczowej
# w modelowaniu hydrodynamicznym, PWr: formula (2.6) p. 19, Wrocław-Strachowice
# 1960-2009, with p = 1/3 (C = 3 years); Tab. 4.6 (PDF pp. 65-66) prints the depths to
# 0.01 mm (the formula reproduces them) and the peak intensity, 101,71 mm/h, to 0.01
# mm/h, in the interval that ends at 20 min for 60 min.
WROCLAW_PEAK_MM_PER_H = 101.71
WROCLAW_TOLERANCE_MM_PER_H = 0.005


def wroclaw_depth_mm(duration_min: float, probability: float = 1 / 3) -> float:
    """Formula (2.6) of Kaźmierczak & Kotowski (2012), t [min], p [-]."""
    shape = (-math.log(probability)) ** 0.809
    return (
        -4.583
        + 7.412 * duration_min**0.242
        + (97.105 * duration_min**0.0222 - 98.675) * shape
    )


# Wdowikowski M., Kaźmierczak B., Wartalska K. et al. (2025) Atmosphere 16(3): 347,
# Tab. 2: PMAXTP depths [mm] of Wrocław, C = 5 years, to 0.1 mm; its Euler type II storm
# of 60 min peaks between the 15th and the 20th minute at 146,18 mm/h. The paper took
# its 5-min values from a curve fitted through the PMAXTP points (12,18 mm against its
# own h(5) = 12,3 mm; method not stated): 0.2 mm covers that gap.
ATMOSPHERE_PMAXTP_MM = {5: 12.3, 10: 15.0, 15: 16.6, 30: 20.1, 45: 22.5, 60: 24.2}
ATMOSPHERE_PEAK_MM = 146.18 / 12
ATMOSPHERE_TOLERANCE_MM = 0.2


def pmaxtp_curve(site: str, probability: str, longest_min: float) -> dict[float, float]:
    """The POT depths [mm] of a recorded PMAXTP table up to ``longest_min``."""
    table = json.loads((FIXTURES / f"pmaxtp_{site}_pot.json").read_text("utf-8"))
    return {
        float(duration): depths[probability]
        for duration, depths in table["data"]["ks"].items()
        if float(duration) <= longest_min
    }


PMAXTP_TOLERANCE_MM = 0.005  # half of the 0.01 mm of the PMAXTP tables


def window_mm(blocks: np.ndarray, peak: int, size: int) -> float:
    """The depth of the ``size`` blocks around the peak block ``peak``.

    The blocks ``peak-size+1 .. peak`` while they fit before the peak, else the first
    ``size`` blocks: they hold the ``size`` first increments of the curve.
    """
    start = peak - size + 1 if size <= peak + 1 else 0
    return float(blocks[start : start + size].sum())


def largest_window_mm(blocks: np.ndarray, size: int) -> float:
    """The largest depth of ``size`` consecutive blocks."""
    return max(float(blocks[i : i + size].sum()) for i in range(len(blocks) - size + 1))


def details(caught: pytest.ExceptionInfo[InvalidParameterError]) -> dict[str, object]:
    """Return the ``details`` of the error."""
    return dict(caught.value.details)


# --- reference cases ------------------------------------------------------------------


@pytest.mark.parametrize("printed", [MALITZ_FOLIE_18_MM, MALITZ_FOLIE_19_MM])
def test_dwd_storms_of_malitz_2009(printed: list[float]) -> None:
    """DWD's 60-min storms: the peak at position 4, the next three before it."""
    depths = np.cumsum(sorted(printed, reverse=True))
    curve = {5.0 * (index + 1): float(depth) for index, depth in enumerate(depths)}

    storm = EulerIIHietogram(curve).generate(curve[60.0], 60.0, 5.0)

    np.testing.assert_allclose(storm.intensities_mm, printed, atol=MALITZ_TOLERANCE_MM)
    assert int(np.argmax(storm.intensities_mm)) == 3


@pytest.mark.parametrize("duration_min", [30, 60, 90])
def test_itwh_storms_of_goellheim(duration_min: int) -> None:
    """itwh's printouts from KOSTRA depths interpolated linearly in ln D."""
    printed = GOELLHEIM_STORMS_MM[duration_min]
    hietogram = EulerIIHietogram(GOELLHEIM_KOSTRA_MM)

    storm = hietogram.generate(
        GOELLHEIM_KOSTRA_MM[duration_min], float(duration_min), 5.0
    )

    np.testing.assert_allclose(
        storm.intensities_mm, printed, atol=GOELLHEIM_TOLERANCE_MM
    )
    assert int(np.argmax(storm.intensities_mm)) == int(np.argmax(printed))


@pytest.mark.parametrize("period", ["T3", "T10"])
def test_itwh_storm_of_aurich_peaks_in_interval_33(period: str) -> None:
    """9 h: the peak interval starts at 0.3 * 540 = 162 min rounded down, 160 min."""
    peak_mm, total_mm = AURICH[period]
    hietogram = EulerIIHietogram({5: peak_mm, 540: total_mm})

    storm = hietogram.generate(total_mm, 540.0, 5.0)

    peak = int(np.argmax(storm.intensities_mm))
    assert (storm.times_min[peak] - 5.0, storm.times_min[peak]) == (160.0, 165.0)
    assert storm.intensities_mm[peak] == pytest.approx(peak_mm, abs=0.005)
    assert storm.intensities_mm.sum() == pytest.approx(total_mm, abs=0.05)


@pytest.mark.parametrize(
    "duration_min, peak_interval_min",
    [
        (60, (15.0, 20.0)),
        # The monograph's Tab. 4.6 ends the peak at D/3 (55-60 min) although its p. 31
        # gives the rule of A 118, 0.3 * 180 = 54 min rounded down to 50 min.
        (180, (50.0, 55.0)),
    ],
)
def test_wroclaw_storms_of_kazmierczak_and_kotowski_2012(
    duration_min: int, peak_interval_min: tuple[float, float]
) -> None:
    """The peak intensity of the Wrocław formula, C = 3 years."""
    curve = {float(t): wroclaw_depth_mm(t) for t in range(5, duration_min + 1, 5)}
    hietogram = EulerIIHietogram(curve)

    storm = hietogram.generate(curve[float(duration_min)], float(duration_min), 5.0)

    peak = int(np.argmax(storm.intensities_mm))
    assert storm.intensity_mm_per_h[peak] == pytest.approx(
        WROCLAW_PEAK_MM_PER_H, abs=WROCLAW_TOLERANCE_MM_PER_H
    )
    assert (storm.times_min[peak] - 5.0, storm.times_min[peak]) == peak_interval_min


def test_pmaxtp_storm_of_wroclaw_in_atmosphere_2025() -> None:
    """60 min, C = 5 years: the peak between the 15th and the 20th minute."""
    storm = EulerIIHietogram(ATMOSPHERE_PMAXTP_MM).generate(24.2, 60.0, 5.0)

    peak = int(np.argmax(storm.intensities_mm))
    assert (storm.times_min[peak] - 5.0, storm.times_min[peak]) == (15.0, 20.0)
    assert storm.intensities_mm[peak] == pytest.approx(
        ATMOSPHERE_PEAK_MM, abs=ATMOSPHERE_TOLERANCE_MM
    )


@pytest.mark.parametrize("site", ["warszawa", "kamiennik"])
@pytest.mark.parametrize("probability", ["1", "10", "50"])
def test_pmaxtp_storms_hold_the_depths_of_the_atlas(
    site: str, probability: str
) -> None:
    """The 5, 15 and 30 min around the peak hold PMAXTP's h(5), h(15), h(30)."""
    curve = pmaxtp_curve(site, probability, 60.0)

    storm = EulerIIHietogram(curve).generate(curve[60.0], 60.0, 5.0)

    blocks = storm.intensities_mm
    assert int(np.argmax(blocks)) == 3
    for size, duration in ((1, 5.0), (3, 15.0), (6, 30.0)):
        assert largest_window_mm(blocks, size) == pytest.approx(
            curve[duration], abs=PMAXTP_TOLERANCE_MM
        )


@pytest.mark.parametrize(
    "duration_min, share", [(30.0, 0.5842), (60.0, 0.4745), (120.0, 0.3854)]
)
def test_peak_share_of_a_power_law_curve(duration_min: float, share: float) -> None:
    """h = D^0.3 (an IDF i ~ D^-0.7): the peak holds h(5) / h(D), 4 decimals."""
    curve = {float(t): t**0.3 for t in range(5, int(duration_min) + 1, 5)}

    storm = EulerIIHietogram(curve).generate(curve[duration_min], duration_min, 5.0)

    assert storm.intensities_mm.max() / storm.total_mm == pytest.approx(
        share, abs=0.00005
    )


# --- properties -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "site, probability", [("kamiennik", "50"), ("warszawa", "1"), ("kamiennik", "2")]
)
@pytest.mark.parametrize(
    "duration_min, timestep_min",
    [(15.0, 5.0), (60.0, 5.0), (180.0, 15.0), (720.0, 5.0)],
)
def test_every_window_around_the_peak_holds_the_depth_of_its_duration(
    site: str, probability: str, duration_min: float, timestep_min: float
) -> None:
    """The Euler property, also where ln D interpolation makes increments grow.

    Kamiennik's p = 50 % grows from 30 to 35 min (its PMAXTP depths are convex in ln D
    there): sorted increments would put 15.14 mm into the 30 min around the peak, not
    h(30) = 15.01 mm.
    """
    hietogram = EulerIIHietogram(pmaxtp_curve(site, probability, 4320.0))

    storm = hietogram.generate(
        hietogram.depth_mm(duration_min), duration_min, timestep_min
    )

    peak = EulerIIHietogram.peak_block(storm.n_steps)
    for size in range(1, storm.n_steps + 1):
        assert window_mm(storm.intensities_mm, peak, size) == pytest.approx(
            hietogram.depth_mm(size * timestep_min), rel=1e-12
        )


def test_the_storm_holds_the_depth_of_its_duration() -> None:
    """The total is h(D) of the curve, interpolated or not."""
    hietogram = EulerIIHietogram(GOELLHEIM_KOSTRA_MM)

    for duration in (5.0, 25.0, 50.0, 75.0, 90.0):
        total = hietogram.depth_mm(duration)
        storm = hietogram.generate(total, duration, 5.0)

        assert storm.total_mm == total
        assert storm.intensities_mm.sum() == pytest.approx(total, rel=1e-12)


@pytest.mark.parametrize("n_steps", range(1, 121))
def test_the_peak_interval_starts_at_three_tenths_of_the_duration(n_steps: int) -> None:
    """The peak block starts at 0.3 * D rounded down to a multiple of the step."""
    curve = {5.0 * j: (5.0 * j) ** 0.3 for j in range(1, n_steps + 1)}
    duration = 5.0 * n_steps

    storm = EulerIIHietogram(curve).generate(curve[duration], duration, 5.0)

    start = storm.times_min[int(np.argmax(storm.intensities_mm))] - 5.0
    assert start == 5.0 * math.floor(round(0.3 * duration / 5.0, 9))


def test_the_peak_rule_rounds_down_to_the_step_not_to_five_minutes() -> None:
    """Steps of 10 min: 0.3 * 60 = 18 min rounds down to 10 min, the second block."""
    curve = {10.0 * j: (10.0 * j) ** 0.3 for j in range(1, 7)}

    storm = EulerIIHietogram(curve).generate(curve[60.0], 60.0, 10.0)

    assert int(np.argmax(storm.intensities_mm)) == 1


def test_increments_keep_the_order_of_their_durations() -> None:
    """Increments that grow are not sorted: each stands where its duration puts it.

    Δh = 10, 2, 4, 1 mm: Δh_1 in the peak block 2, Δh_2 before it, Δh_3 and Δh_4 after
    it, as the itwh printout of Aurich places its increments (see ``AURICH``).
    """
    hietogram = EulerIIHietogram({5: 10.0, 10: 12.0, 15: 16.0, 20: 17.0})

    storm = hietogram.generate(17.0, 20.0, 5.0)

    np.testing.assert_allclose(storm.intensities_mm, [2.0, 10.0, 4.0, 1.0])


def test_keys_of_a_json_object_are_durations() -> None:
    """``{"5": ...}`` is the curve ``{5: ...}`` (a network document holds it so)."""
    from_text = EulerIIHietogram({str(k): v for k, v in GOELLHEIM_KOSTRA_MM.items()})
    from_numbers = EulerIIHietogram(GOELLHEIM_KOSTRA_MM)

    np.testing.assert_array_equal(
        from_text.generate(27.9, 60.0).intensities_mm,
        from_numbers.generate(27.9, 60.0).intensities_mm,
    )
    assert from_text.depth_duration_mm == from_numbers.depth_duration_mm


def test_whole_steps_are_counted_without_the_float_trap() -> None:
    """0.3 / 0.1 is 2.9999999999999996: the storm still has three blocks."""
    storm = EulerIIHietogram({0.1: 1.0, 0.3: 2.0}).generate(2.0, 0.3, 0.1)

    assert storm.n_steps == 3


# --- validation -----------------------------------------------------------------------


def test_a_decreasing_curve_is_refused_naming_its_durations() -> None:
    """A depth-duration curve never decreases."""
    with pytest.raises(InvalidParameterError) as caught:
        EulerIIHietogram({5: 10.0, 10: 14.0, 15: 13.5, 30: 18.0})

    assert details(caught) == {
        "option": "depth_duration_mm",
        "reason": "decreasing",
        "durations_min": [10.0, 15.0],
        "depths_mm": [14.0, 13.5],
    }


@pytest.mark.parametrize(
    "duration_min, timestep_min, uncovered", [(90.0, 5.0, 90.0), (60.0, 2.5, 2.5)]
)
def test_a_curve_must_reach_from_the_step_to_the_duration(
    duration_min: float, timestep_min: float, uncovered: float
) -> None:
    """Nothing is extrapolated: the curve of 5 to 60 min serves neither 90 nor 2.5."""
    hietogram = EulerIIHietogram(pmaxtp_curve("warszawa", "1", 60.0))

    with pytest.raises(InvalidParameterError) as caught:
        hietogram.generate(39.16, duration_min, timestep_min)

    assert details(caught)["reason"] == "not_covered"
    assert details(caught)["option"] == "depth_duration_mm"
    assert details(caught)["duration_min"] == uncovered


def test_the_depth_outside_the_curve_is_refused() -> None:
    """``depth_mm`` does not extrapolate either."""
    with pytest.raises(InvalidParameterError) as caught:
        EulerIIHietogram({5: 9.5, 60: 27.9}).depth_mm(90.0)

    assert details(caught)["reason"] == "not_covered"


def test_a_duration_that_is_not_a_whole_number_of_steps_is_refused() -> None:
    """50 min in steps of 15 min would leave 5 min of the storm out."""
    with pytest.raises(InvalidParameterError) as caught:
        EulerIIHietogram(GOELLHEIM_KOSTRA_MM).generate(26.4, 50.0, 15.0)

    assert details(caught) == {
        "option": "duration_min",
        "reason": "not_multiple",
        "timestep_min": 15.0,
    }


def test_the_step_may_not_exceed_the_duration() -> None:
    """A step longer than the storm is refused with the bound."""
    with pytest.raises(InvalidParameterError) as caught:
        EulerIIHietogram(GOELLHEIM_KOSTRA_MM).generate(9.5, 5.0, 10.0)

    assert details(caught) == {
        "option": "timestep_min",
        "reason": "maximum",
        "maximum": 5.0,
        "value": 10.0,
    }


@pytest.mark.parametrize(
    "depth, reason",
    [(math.nan, "not_finite"), (math.inf, "not_finite"), (-1.0, "minimum")],
)
def test_depths_must_be_finite_and_not_negative(depth: float, reason: str) -> None:
    """NaN, infinity and a negative depth are not a curve."""
    with pytest.raises(InvalidParameterError) as caught:
        EulerIIHietogram({5: depth, 10: 14.0})

    assert details(caught)["reason"] == reason
    assert details(caught)["duration_min"] == 5.0


@pytest.mark.parametrize("key", ["abc", "nan", 0, -5.0, math.inf, True])
def test_durations_must_be_numbers_of_minutes_above_zero(key: object) -> None:
    """A key that is not a duration is refused."""
    with pytest.raises(InvalidParameterError) as caught:
        EulerIIHietogram({key: 1.0, 10: 14.0})  # type: ignore[arg-type]

    assert details(caught)["reason"] == "invalid_duration"


def test_a_duration_given_twice_is_refused() -> None:
    """``5`` and ``"5"`` are one duration."""
    with pytest.raises(InvalidParameterError) as caught:
        EulerIIHietogram({5: 9.5, "5": 9.5})  # type: ignore[arg-type]

    assert details(caught)["reason"] == "duplicate_duration"


@pytest.mark.parametrize("curve, reason", [({}, "empty"), ([(5, 9.5)], "type")])
def test_a_curve_is_a_mapping_with_points(curve: object, reason: str) -> None:
    """An empty mapping or a list of pairs is not a curve."""
    with pytest.raises(InvalidParameterError) as caught:
        EulerIIHietogram(curve)  # type: ignore[arg-type]

    assert details(caught)["reason"] == reason


def test_a_total_other_than_the_depth_of_the_duration_is_refused() -> None:
    """The total of the storm is h(D): 0.006 mm off is another storm."""
    hietogram = EulerIIHietogram(GOELLHEIM_KOSTRA_MM)

    with pytest.raises(InvalidParameterError) as caught:
        hietogram.generate(27.906, 60.0, 5.0)

    assert details(caught) == {
        "option": "total_mm",
        "reason": "total_mismatch",
        "depth_mm": 27.9,
        "duration_min": 60.0,
    }


def test_a_total_within_the_rounding_gives_the_depth_of_the_curve() -> None:
    """A total rounded to 0.01 mm is accepted; the storm holds h(D) itself."""
    hietogram = EulerIIHietogram(GOELLHEIM_KOSTRA_MM)
    depth = hietogram.depth_mm(50.0)

    storm = hietogram.generate(round(depth, 2), 50.0, 5.0)

    assert storm.total_mm == depth


@pytest.mark.parametrize("total", [math.nan, math.inf, 0.0])
def test_the_total_must_be_a_finite_number_above_zero(total: float) -> None:
    """A NaN total does not slip through the comparison with h(D)."""
    with pytest.raises(InvalidParameterError) as caught:
        EulerIIHietogram(GOELLHEIM_KOSTRA_MM).generate(total, 60.0, 5.0)

    assert details(caught)["option"] == "total_mm"
