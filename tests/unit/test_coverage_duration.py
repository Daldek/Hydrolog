"""The coverage of the interval of the median annual flow-duration curve (CMP-6.11).

Nightly (marker ``nightly``), never in the gate: samples of N independent years, each
a curve of three percentages whose log-normal values are correlated within the year,
are drawn from one generator seeded once, and the share of the intervals of spec
``duration_curve_annual_median_interval`` that hold the true medians is asserted per
level and percentage within three Monte Carlo errors of its exact binomial coverage,
the coverage of the pair of order statistics the spec takes at N years, computed here
in fractions. The records go to ``tests/fixtures/formulas/interval-coverage.json``
for ``docs/FORMULAS.md``.
"""

import math
from fractions import Fraction

import numpy as np
import pytest

from hydrolog.nogat_formulas import assert_coverage
from hydrolog.statistics.duration import (
    DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL,
    annual_median_interval,
)

from ._coverage import keep

pytestmark = [pytest.mark.nightly, pytest.mark.formula]

SEED = 20261125
"""Fixed once, on the day the test was written, and never changed to pass."""
SAMPLES = 10_000
LEVELS = (0.95, 0.68)
MEDIANS = np.array([40.0, 6.0, 1.5])
"""The true median annual values of the three percentages [m3/s]."""
SIGMAS = np.array([0.6, 0.4, 0.5])
CORRELATION = 0.8
SETTING = (
    "log-normal annual values of three percentages, medians 40, 6 and 1.5 m3/s, "
    "sigma of ln 0.6, 0.4 and 0.5, correlation 0.8 between the percentages of a year, "
    "the years independent"
)


def _draw(generator: np.random.Generator, size: int) -> np.ndarray:
    """The curves of ``size`` years: a deviate common to the year and one of each
    percentage, mixed to the correlation, each column standard normal before exp."""
    common = generator.standard_normal((size, 1))
    own = generator.standard_normal((size, MEDIANS.size))
    normal = CORRELATION * common + math.sqrt(1.0 - CORRELATION**2) * own
    return MEDIANS * np.exp(SIGMAS * normal)


def _interval(sample: np.ndarray, levels: tuple[float, ...]) -> list:
    found = annual_median_interval(sample, list(levels))
    return list(zip(found.lower, found.upper, strict=True))


def _binomial_coverage(years: int, level: float) -> float:
    """The coverage of the pair at ``years`` years: of each pair k, N + 1 - k the
    probability that from k to N - k of N values lie below the median, the middle
    terms of Bin(N, 1/2) as fractions, and of these the smallest at least c."""
    whole = 2**years
    held = [
        Fraction(sum(math.comb(years, j) for j in range(k, years - k + 1)), whole)
        for k in range(1, years // 2 + 1)
    ]
    return float(min(share for share in held if share >= Fraction(level)))


@pytest.mark.parametrize("size", [30, 60])
def test_the_coverage_is_the_binomial_one(size):
    records = assert_coverage(
        DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL,
        _interval,
        _draw,
        MEDIANS,
        setting=SETTING,
        size=size,
        confidence_level=LEVELS,
        seed=SEED,
        reason="order statistics: the pair Q(k), Q(N + 1 - k) holds the median of a "
        "continuous distribution with exactly the binomial probability "
        "1 - 2 F(k - 1), F of N trials with probability 1/2 (Helsel and Hirsch "
        "2002, sect. 3.3.1), above the level by the discreteness of the ranks",
        samples=SAMPLES,
        expected={level: _binomial_coverage(size, level) for level in LEVELS},
    )

    keep(records)
