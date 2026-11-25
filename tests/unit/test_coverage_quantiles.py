"""The simulated coverage of the intervals of the quantiles (Nogat CMP-6.11, nightly).

Per distribution the spec fits, at 30 and 60 values and the levels 0.95 and 0.68,
1,000 samples are drawn from a distribution of typical Polish annual maxima (or
minima) with one generator of the fixed seed :data:`SEED`; each is fitted as Hydrolog
fits it (L-moments for the bootstrap, maximum likelihood for the delta method) and
its interval at every return period of ``stats flood-frequency`` holds the true
quantile or not. Both methods are approximate, so the coverage is the method's, not
forced to c (CMP-6.11): a test asserts it per element above the floor of
:data:`FLOORS` with its reason, and every record goes to
``tests/fixtures/formulas/interval-coverage.json`` and ``docs/FORMULAS.md``. A sample
the method cannot fit, or whose interval is refused (too few refits, a GEV whose
likelihood is not regular), gives bounds not computed, which hold nothing and are
counted. The bounds are those of variable ``stage``: the method itself, without the
sign rule of a discharge, which leaves out bounds below 0.

Run with ``uv run pytest -m nightly tests/unit/test_coverage_quantiles.py``; settings
run in parallel with ``-k``.
"""

import warnings
from collections.abc import Callable

import numpy as np
import pytest

from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.nogat_formulas import Bounds, FormulaSpec, assert_coverage
from hydrolog.statistics.frequency import (
    _DISTRIBUTIONS,
    fit_l_moments,
    fit_maximum_likelihood,
)
from hydrolog.statistics.intervals import (
    QUANTILE_INTERVAL_BOOTSTRAP,
    QUANTILE_INTERVAL_DELTA,
    quantile_interval_bootstrap,
    quantile_interval_delta,
)
from hydrolog.statistics.low_flows import fisher_tippett_minima

from . import _coverage

pytestmark = [pytest.mark.nightly, pytest.mark.formula]

SEED = 20261125
"""The generator's seed, fixed once on the day the test was written; never chosen."""
LEVELS = (0.95, 0.68)
PERIODS = np.array([2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0])
"""The default return periods of ``stats flood-frequency`` and ``stats low-flow``."""
SETTINGS: dict[str, tuple[float, float, float]] = {
    "log_normal": (0.6, 0.0, 50.0),
    "gev": (-0.1, 50.0, 20.0),
    "pearson3": (1.0, 60.0, 25.0),
    "weibull": (1.5, 10.0, 50.0),
}
"""Typical Polish annual maxima per distribution, scipy's (shape, loc, scale) in m3/s:
shapes inside the typical ranges of the fits (KZGW 2017, ex. 3.2 to 3.4) away from
the ends where maximum likelihood has no maximum."""
MINIMA: tuple[float, float, float] = (0.3, 40.0, 12.0)
"""The Fisher-Tippett distribution of annual minima (fisher_tippett_minima's c, loc,
scale), its lower bound loc - scale / c at a discharge of 0."""
FLOORS: dict[tuple[str, str, int], dict[float, float]] = {
    ("bootstrap", "gev", 30): {0.95: 0.82, 0.68: 0.57},
    ("bootstrap", "gev", 60): {0.95: 0.83, 0.68: 0.61},
    ("bootstrap", "log_normal", 30): {0.95: 0.87, 0.68: 0.6},
    ("bootstrap", "log_normal", 60): {0.95: 0.88, 0.68: 0.58},
    ("bootstrap", "pearson3", 30): {0.95: 0.84, 0.68: 0.6},
    ("bootstrap", "pearson3", 60): {0.95: 0.86, 0.68: 0.61},
    ("bootstrap", "weibull", 30): {0.95: 0.85, 0.68: 0.59},
    ("bootstrap", "weibull", 60): {0.95: 0.86, 0.68: 0.61},
    ("delta", "gev", 30): {0.95: 0.77, 0.68: 0.58},
    ("delta", "gev", 60): {0.95: 0.81, 0.68: 0.6},
    ("delta", "log_normal", 30): {0.95: 0.87, 0.68: 0.61},
    ("delta", "log_normal", 60): {0.95: 0.88, 0.68: 0.58},
    ("delta", "minima", 30): {0.95: 0.7, 0.68: 0.51},
    ("delta", "minima", 60): {0.95: 0.77, 0.68: 0.58},
    ("delta", "pearson3", 30): {0.95: 0.7, 0.68: 0.43},
    ("delta", "pearson3", 60): {0.95: 0.8, 0.68: 0.47},
    ("delta", "weibull", 30): {0.95: 0.68, 0.68: 0.47},
    ("delta", "weibull", 60): {0.95: 0.86, 0.68: 0.56},
}
"""The floor of the coverage asserted per spec, distribution and size, by level."""
FLOOR_REASON = (
    "an approximate interval: its coverage at 30 and 60 values is the method's and "
    "is reported (CMP-6.11); the floor stands for no source, it is the lowest "
    "coverage over the return periods of this setting first simulated, 2026-11-25, "
    "less 0.05 and rounded down, so that a fall below it is a change of the code; "
    "samples maximum likelihood cannot fit, or whose interval is refused, hold nothing"
)


def _setting(name: str, parameters: tuple[float, float, float]) -> str:
    shape, loc, scale = parameters
    return f"{name} (shape {shape}, loc {loc}, scale {scale} m3/s)"


def _not_computed(levels: tuple[float, ...]) -> list[Bounds]:
    gap = np.full(PERIODS.size, np.nan)
    return [(gap, gap) for _ in levels]


def _bootstrap(name: str) -> Callable[[np.ndarray, tuple[float, ...]], list[Bounds]]:
    def interval(sample: np.ndarray, levels: tuple[float, ...]) -> list[Bounds]:
        try:
            fitted = fit_l_moments(sample, name)
            found = quantile_interval_bootstrap(
                name, *fitted, sample.size, PERIODS, list(levels), "stage"
            )
        except InvalidParameterError:
            return _not_computed(levels)
        return list(zip(found.lower, found.upper, strict=True))

    return interval


def _delta(name: str) -> Callable[[np.ndarray, tuple[float, ...]], list[Bounds]]:
    def interval(sample: np.ndarray, levels: tuple[float, ...]) -> list[Bounds]:
        try:
            fitted = fit_maximum_likelihood(sample, name)
            found = quantile_interval_delta(
                sample, name, *fitted, PERIODS, list(levels), "stage", "maxima"
            )
        except (InvalidParameterError, CalculationError):
            return _not_computed(levels)
        return list(zip(found.lower, found.upper, strict=True))

    return interval


def _minima(sample: np.ndarray, levels: tuple[float, ...]) -> list[Bounds]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fitted = fisher_tippett_minima(sample, PERIODS, "stage")
        found = quantile_interval_delta(
            sample,
            "gev",
            fitted.shape,
            fitted.loc,
            fitted.scale,
            PERIODS,
            list(levels),
            "stage",
            "minima",
        )
    except (InvalidParameterError, CalculationError):
        return _not_computed(levels)
    return list(zip(found.lower, found.upper, strict=True))


def _run(
    spec: FormulaSpec,
    interval: Callable[[np.ndarray, tuple[float, ...]], list[Bounds]],
    draw: Callable[[np.random.Generator, int], np.ndarray],
    truth: np.ndarray,
    setting: str,
    key: tuple[str, str, int],
) -> None:
    floors = FLOORS.get(key, dict.fromkeys(LEVELS, 0.0))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        records = assert_coverage(
            spec,
            interval,
            draw,
            truth,
            setting=setting,
            size=key[2],
            confidence_level=LEVELS,
            seed=SEED,
            reason=FLOOR_REASON,
            at_least=floors,
        )
    _coverage.keep(records)


@pytest.mark.parametrize("size", [30, 60])
@pytest.mark.parametrize("name", list(SETTINGS))
def test_the_bootstrap_interval_covers(name: str, size: int) -> None:
    parameters = SETTINGS[name]
    distribution = _DISTRIBUTIONS[name](*parameters)

    def draw(generator: np.random.Generator, n: int) -> np.ndarray:
        return np.asarray(distribution.rvs(size=n, random_state=generator))

    _run(
        QUANTILE_INTERVAL_BOOTSTRAP,
        _bootstrap(name),
        draw,
        np.asarray(distribution.isf(1.0 / PERIODS)),
        _setting(name, parameters),
        ("bootstrap", name, size),
    )


@pytest.mark.parametrize("size", [30, 60])
@pytest.mark.parametrize("name", list(SETTINGS))
def test_the_delta_interval_covers(name: str, size: int) -> None:
    parameters = SETTINGS[name]
    distribution = _DISTRIBUTIONS[name](*parameters)

    def draw(generator: np.random.Generator, n: int) -> np.ndarray:
        return np.asarray(distribution.rvs(size=n, random_state=generator))

    _run(
        QUANTILE_INTERVAL_DELTA,
        _delta(name),
        draw,
        np.asarray(distribution.isf(1.0 / PERIODS)),
        _setting(name, parameters),
        ("delta", name, size),
    )


@pytest.mark.parametrize("size", [30, 60])
def test_the_delta_interval_of_minima_covers(size: int) -> None:
    shape, loc, scale = MINIMA
    negated = _DISTRIBUTIONS["gev"](shape, loc=-loc, scale=scale)

    def draw(generator: np.random.Generator, n: int) -> np.ndarray:
        return -np.asarray(negated.rvs(size=n, random_state=generator))

    _run(
        QUANTILE_INTERVAL_DELTA,
        _minima,
        draw,
        -np.asarray(negated.isf(1.0 / PERIODS)),
        f"Fisher-Tippett of minima (c {shape}, loc {loc}, scale {scale} m3/s)",
        ("delta", "minima", size),
    )


def test_the_floors_name_settings_that_run() -> None:
    """Every floor of :data:`FLOORS` belongs to a setting a test runs."""
    runs = {
        (method, name, size)
        for method in ("bootstrap", "delta")
        for name in SETTINGS
        for size in (30, 60)
    } | {("delta", "minima", size) for size in (30, 60)}
    assert set(FLOORS) <= runs
