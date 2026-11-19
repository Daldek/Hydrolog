"""Hyetograph generation for temporal rainfall distribution.

The design storms are declared by their specs (Nogat's computation standard, ADR-0050,
ADR-0067): :data:`BLOCK` (``block_hyetograph``), :data:`TRIANGULAR`
(``triangular_hyetograph``), :data:`BETA` (``beta_hyetograph``) and :data:`EULER_II`
(``euler_ii_hyetograph``), with the interpolation of a depth-duration curve in the
Tier B table (``depth_duration_interpolation``); ``docs/FORMULAS.md`` shows their
equations, constants, ranges and sources. The generators :class:`BlockHietogram`,
:class:`TriangularHietogram`, :class:`BetaHietogram` and :class:`EulerIIHietogram`
keep the interface and the refusals of earlier versions and compute through them.

Every generator cuts the storm into ``n = D / Δt`` whole steps of the time step Δt and
puts the whole total into them, so the duration D must be a whole number of steps
(``details.reason`` ``not_multiple`` otherwise; ADR-0046): the storm then lasts D and
its mean intensity is the total over D.

Chow, Maidment and Mays (1988), Example 14.3.1 (1.07 in = 27.178 mm in 15 min, r =
0.38) in steps of 5 min, and the Euler type II storm of the PMAXTP curve of Warsaw
(POT, p = 1 %):

>>> chow = triangular_hyetograph(27.178, 15.0, 5.0, 0.38)
>>> chow.intensities_mm.round(3).tolist(), round(chow.peak_intensity_mm_per_h, 2)
([7.947, 14.361, 4.871], 217.42)
>>> warsaw = euler_ii_hyetograph(
...     [5, 10, 15, 30, 45, 60], [21.82, 25.68, 28.22, 33.23, 36.58, 39.16], 60, 5
... )
>>> warsaw.peak_start_min, warsaw.intensities_mm[:4].round(2).tolist()
(15.0, [2.08, 2.54, 3.86, 21.82])
"""

from __future__ import annotations

import itertools
import math
import numbers
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import ClassVar, Final

import numpy as np
from numpy.typing import NDArray
from scipy.special import betainc

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Conservation,
    Constant,
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    Symmetry,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
    convert,
)

_SAME_DURATION = 1e-9
"""Relative difference under which two durations are one (``5 * 12`` and ``60.0``)."""


def _finite_number(name: str, value: object) -> float:
    """Return ``value`` as a finite float, or refuse it naming ``name``."""
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise InvalidParameterError(
            f"{name} must be a number, got {value!r}",
            details={
                "option": name,
                "reason": "type",
                "expected": "number",
                "got": type(value).__name__,
            },
        )
    number = float(value)
    if not math.isfinite(number):
        raise InvalidParameterError(
            f"{name} must be a finite number, got {number}",
            details={"option": name, "reason": "not_finite", "value": str(number)},
        )
    return number


def _finite_positive(name: str, value: object) -> float:
    """Return ``value`` as a float above zero, or refuse it naming ``name``."""
    number = _finite_number(name, value)
    if number <= 0:
        raise InvalidParameterError(
            f"{name} must be positive, got {number:g}",
            details={
                "option": name,
                "reason": "exclusive_minimum",
                "exclusive_minimum": 0,
                "value": number,
            },
        )
    return number


def _storm_steps(
    duration_min: object, timestep_min: object
) -> tuple[float, float, int]:
    """Return the duration [min], the step [min] and the number of whole steps.

    Raises
    ------
    InvalidParameterError
        If a value is not a finite number above zero (``details.option`` names it),
        the step exceeds the duration (``reason`` ``maximum``) or the duration is not
        a whole number of steps (``reason`` ``not_multiple``, with ``timestep_min``).
    """
    duration = _finite_positive("duration_min", duration_min)
    step = _finite_positive("timestep_min", timestep_min)
    if step > duration * (1 + _SAME_DURATION):
        raise InvalidParameterError(
            f"timestep_min ({step:g}) cannot exceed duration_min ({duration:g})",
            details={
                "option": "timestep_min",
                "reason": "maximum",
                "maximum": duration,
                "value": step,
            },
        )
    n_steps = max(round(duration / step), 1)
    if abs(n_steps * step - duration) > _SAME_DURATION * duration:
        raise InvalidParameterError(
            f"duration_min ({duration:g}) is not a whole number of steps of "
            f"{step:g} min: a hyetograph is made of whole steps, and fewer steps "
            "would hold the whole total in a shorter storm",
            details={
                "option": "duration_min",
                "reason": "not_multiple",
                "timestep_min": step,
            },
            hint="Give a duration that is a multiple of the time step.",
        )
    return duration, step, n_steps


def _storm(
    total_mm: object, duration_min: object, timestep_min: object
) -> tuple[float, float, float, int]:
    """Return the total [mm], duration [min], step [min] and number of steps.

    Raises
    ------
    InvalidParameterError
        If the total is not a finite number above zero, or as :func:`_storm_steps`.
    """
    total = _finite_positive("total_mm", total_mm)
    duration, step, n_steps = _storm_steps(duration_min, timestep_min)
    return total, duration, step, n_steps


def _step_ends(n_steps: int, timestep_min: float) -> NDArray[np.float64]:
    """Return the ends of the steps [min]: ``Δt, 2Δt, ..., nΔt``."""
    return np.arange(1, n_steps + 1, dtype=np.float64) * timestep_min


@dataclass
class HietogramResult(JsonResultMixin):
    """
    Result of hyetograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values at the end of each interval [min].
    intensities_mm : NDArray[np.float64]
        Precipitation depths per time step [mm].

        Note: Despite the name, this field contains incremental
        precipitation depths (volume per timestep), not intensity
        rates. For intensity in [mm/h], use the ``intensity_mm_per_h``
        property.
    total_mm : float
        Total precipitation depth [mm].
    duration_min : float
        Total duration [min].
    timestep_min : float
        Time step [min].
    """

    times_min: NDArray[np.float64]
    intensities_mm: NDArray[np.float64]
    total_mm: float
    duration_min: float
    timestep_min: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)

    @property
    def intensity_mm_per_h(self) -> NDArray[np.float64]:
        """Precipitation intensity [mm/h]."""
        return self.intensities_mm * (60.0 / self.timestep_min)


class Hietogram(ABC):
    """
    Abstract base class for hyetograph generators.

    A hyetograph represents the temporal distribution of rainfall
    over the duration of a storm event.
    """

    @abstractmethod
    def generate(
        self,
        total_mm: float,
        duration_min: float,
        timestep_min: float = 5.0,
    ) -> HietogramResult:
        """
        Generate hyetograph.

        Parameters
        ----------
        total_mm : float
            Total precipitation depth [mm].
        duration_min : float
            Duration of the storm event [min].
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0; the duration must be
            a whole number of steps.

        Returns
        -------
        HietogramResult
            Generated hyetograph with times and intensities.
        """
        pass

    @staticmethod
    def _validate_params(
        total_mm: float, duration_min: float, timestep_min: float
    ) -> int:
        """
        Validate the input and return the number of steps.

        Returns
        -------
        int
            Number of time steps, ``duration_min / timestep_min``.

        Raises
        ------
        InvalidParameterError
            If a value is not a finite number above zero (``details.option`` names
            it, ``reason`` ``type``, ``not_finite`` or ``exclusive_minimum``), the
            step exceeds the duration (``reason`` ``maximum``) or the duration is
            not a whole number of steps (``reason`` ``not_multiple``).
        """
        return _storm(total_mm, duration_min, timestep_min)[3]


@dataclass
class TriangularStorm(HietogramResult):
    """A triangular hyetograph with its triangle (spec ``triangular_hyetograph``).

    Attributes
    ----------
    peak_intensity_mm_per_h : float
        Intensity at the peak of the triangle [mm/h].
    peak_time_min : float
        Time of the peak from the start of the storm [min].
    """

    peak_intensity_mm_per_h: float
    peak_time_min: float


@dataclass
class EulerIIStorm(HietogramResult):
    """An Euler type II storm with the start of its peak (spec ``euler_ii_hyetograph``).

    Attributes
    ----------
    peak_start_min : float
        Start of the interval of the peak from the start of the storm [min].
    """

    peak_start_min: float


# --- the specs (Nogat's computation standard, ADR-0050, ADR-0067) ---------------------

_STEPS_MAX: Final = 1_000_000
"""The most steps a hyetograph holds: a year in steps of half a minute."""

_PEAK_START: Final = Fraction(3, 10)
"""The share of the duration at which the peak interval of an Euler II storm starts."""

_CHOW = (
    "Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, "
    "New York"
)
_CHOW_URL = "https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf"
_KZGW = (
    "KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych "
    "o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i "
    "niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona)"
)
_KZGW_URL = (
    "https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/"
    "zal-2-do-OPZ-ujednolicony-1.pdf"
)
_STEPS_OF_CHOW = Source(
    citation=_CHOW,
    locator="sec. 14.4, p. 466: a design hyetograph gives the depth of n successive "
    "intervals of duration dt over the total duration Td = n dt",
    url=_CHOW_URL,
)
_HYDROLOG_BOUND = Source(
    citation="Hydrolog, ADR-0067: the precipitation formulas by specs",
    locator="docs/decisions/0067-the-precipitation-formulas-by-specs.md, point 3",
)
_PMAXTP = Source(
    citation="Ozga-Zieliński, B. (ed.) (2022). Modele probabilistyczne opadów "
    "maksymalnych o określonym czasie trwania i prawdopodobieństwie przewyższenia - "
    "projekt PMAXTP. IMGW-PIB, Warszawa, ISBN 978-83-64979-48-4",
    locator="p. 10: the tables give 16 durations, 5 min to 72 h",
    url="https://klimat.imgw.pl/opady-maksymalne/",
)
_PMAXTP_FIXTURES = Source(
    citation="Hydrolog's test fixtures: the PMAXTP depths of IMGW-PIB for Kamiennik "
    "(51.015 N, 15.890 E) and Warsaw (52.23 N, 21.01 E), POT, recorded in "
    "November 2026",
    locator="tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: "
    "6.96 to 341.27 mm over durations of 5 min to 72 h and probabilities of 0.01 "
    "to 99.9 %",
)
_STEPS_IN_USE = Source(
    citation="The steps of the design storms of the sources: 5 min (DWD, Malitz 2009, "
    "slide 17; the shortest duration of the PMAXTP tables) to 1 h (KZGW 2017, "
    "example 6.1, p. 92)",
    locator="Malitz 2009 slide 17; KZGW 2017 p. 92",
)
_A118 = Source(
    citation="ATV-DVWK (2001). Arbeitsblatt ATV-DVWK-A 118, Kap. 5.2.2.1, as quoted by "
    "Thewes, K. (2005). Diplomarbeit, Fachhochschule Trier",
    locator="p. 10: the interval of the highest intensity begins at 0.3 of the "
    "duration rounded down to a multiple of 5 min; the next lower intervals follow "
    "to the left back to t = 0, the others to the right",
    url="https://www.hochschule-trier.de/fileadmin/Hauptcampus/Fachbereich_BL/BI/"
    "Personen/Erzmann/Abschlussarbeiten/DA-Thewes.pdf",
)
_MALITZ = Source(
    citation="Malitz, G. (2009). Stark- und Extremniederschlag im Kurzzeitbereich. "
    "Deutscher Wetterdienst, Hydrometeorologie; slides of the 2. Trierer Workshop zur "
    "Niederschlag-Abfluss-Modellierung",
    locator="slide 17: the highest 5-min value at position 4, the three next higher "
    "to its left, the rest decreasing to its right, the sum of the three largest the "
    "depth of 15 min; slides 18 and 19: two storms of 60 min",
    url="https://www.uni-trier.de/fileadmin/fb6/prof/PHY/PDF-Dateien/AG_ModSim/"
    "N-A-Workshop_2009/Malitz.pdf",
)
_KAZMIERCZAK = Source(
    citation="Kaźmierczak, B. and Kotowski, A. (2012). Weryfikacja przepustowości "
    "kanalizacji deszczowej w modelowaniu hydrodynamicznym. Oficyna Wydawnicza "
    "Politechniki Wrocławskiej, Wrocław",
    locator="pp. 31-32 (the construction); Tab. 4.6, pp. 65-66 (eight storms of 75 to "
    "180 min)",
    url="https://www.dbc.wroc.pl/Content/19608/PDF/kazmierczak_weryfikacja.pdf",
)
_WORLD_RECORD = (
    "the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January "
    "1966 (WMO Archive of Weather and Climate Extremes)"
)
_LONGEST = "ten times the longest duration of the PMAXTP tables, 72 h"


def _step_count(duration: float, step: float) -> int:
    """Return the number of whole steps of a duration the constraints accepted."""
    return max(round(duration / step), 1)


def _steps_ratio(x: Values) -> float:
    return x.real("duration_min") / x.real("timestep_min")


def _step_within_duration(x: Values) -> bool:
    return x.real("timestep_min") <= x.real("duration_min") * (1.0 + _SAME_DURATION)


def _steps_representable(x: Values) -> bool:
    return _steps_ratio(x) <= _STEPS_MAX + 0.5


def _whole_steps(x: Values) -> bool:
    ratio = _steps_ratio(x)
    if not ratio <= _STEPS_MAX + 0.5:
        return False
    duration = x.real("duration_min")
    count = max(round(ratio), 1)
    return abs(count * x.real("timestep_min") - duration) <= _SAME_DURATION * duration


_STEP_CONSTRAINTS: Final = (
    Constraint(
        name="step_within_duration",
        cls="precondition",
        check=_step_within_duration,
        text="dt <= Td: the storm holds at least one step",
        source=_STEPS_OF_CHOW,
        satisfied={"timestep_min": 5.0},
        violated={"timestep_min": 61.0},
        boundary={"timestep_min": 60.0},
    ),
    Constraint(
        name="steps_representable",
        cls="precondition",
        check=_steps_representable,
        text="Td / dt <= 1,000,000: at most a million steps",
        source=_HYDROLOG_BOUND,
        satisfied={"timestep_min": 5.0},
        violated={"duration_min": 6.0e6},
    ),
    Constraint(
        name="whole_steps",
        cls="precondition",
        check=_whole_steps,
        text="Td = n dt for a whole n, to 1e-9 of Td: the storm is made of whole steps",
        source=_STEPS_OF_CHOW,
        satisfied={"timestep_min": 5.0},
        violated={"timestep_min": 7.0},
    ),
)
"""The steps of a storm: at least one, at most a million, and whole (ADR-0046)."""

_TOTAL: Final = Variable(
    name="total_mm",
    symbol="P",
    unit="mm",
    description="Total depth of the storm.",
    physical=Range(
        low=0.0, low_inclusive=False, test_high=1825.0, test_reason=_WORLD_RECORD
    ),
    applicability="unstated",
    typical=Range(low=6.96, high=341.27, source=_PMAXTP_FIXTURES),
)
_DURATION: Final = Variable(
    name="duration_min",
    symbol="T_d",
    unit="min",
    description="Duration of the storm, a whole number of steps.",
    physical=Range(
        low=0.0, low_inclusive=False, test_high=43200.0, test_reason=_LONGEST
    ),
    applicability="unstated",
    typical=Range(low=5.0, high=4320.0, source=_PMAXTP),
)
_TIMESTEP: Final = Variable(
    name="timestep_min",
    symbol=r"\Delta t",
    unit="min",
    description="Time step: the length of each block of the storm.",
    physical=Range(
        low=0.0, low_inclusive=False, test_high=43200.0, test_reason=_LONGEST
    ),
    applicability="unstated",
    typical=Range(low=5.0, high=60.0, source=_STEPS_IN_USE),
)
_BLOCKS: Final = Output(
    name="intensities_mm",
    unit="mm",
    kind="real_array",
    symbol="P_j",
    description="Depth of each step (the field keeps its name of earlier versions; "
    "the result's intensity_mm_per_h is the rate).",
    physical=Range(low=0.0),
    boundary_tolerance=1e-9,
)
_TIMES: Final = Output(
    name="times_min",
    unit="min",
    kind="real_array",
    symbol="t_j",
    description="End of each step from the start of the storm.",
    physical=Range(low=0.0, low_inclusive=False),
)
_STORM_BASE: Final = {"total_mm": 30.0, "duration_min": 60.0, "timestep_min": 5.0}
"""The typical point of the generated tests: a storm of a whole number of steps."""

_ADD_UP: Final = Tolerance(
    abs=1e-9,
    reason="the steps are rounded products or differences of a total below 2 m; their "
    "exact sum (fsum) differs from it by a few units in its last place per million "
    "steps",
)
_DOUBLED: Final = Tolerance(
    rel=1e-15,
    abs=1e-300,
    reason="doubling a total or a time is exact in binary; one rounding of a quotient "
    "but for subnormal values",
)


def _steps_add_up(x: Values, out: Values) -> float:
    return math.fsum(out.array("intensities_mm")) - x.real("total_mm")


def _storm_scalings(
    depth: Mapping[str, float], time: Mapping[str, float], tolerance: Tolerance
) -> tuple[Scaling, Scaling]:
    """Return the scalings of a storm: of its depths and of its times."""
    return (
        Scaling(
            name="depth",
            inputs={"total_mm": 1},
            outputs=dict(depth),
            tolerance=tolerance,
        ),
        Scaling(
            name="time",
            inputs={"duration_min": 1, "timestep_min": 1},
            outputs=dict(time),
            tolerance=tolerance,
        ),
    )


def _result(x: Values, out: Values) -> HietogramResult:
    return HietogramResult(
        times_min=out.array("times_min"),
        intensities_mm=out.array("intensities_mm"),
        total_mm=x.real("total_mm"),
        duration_min=x.real("duration_min"),
        timestep_min=x.real("timestep_min"),
    )


# --- block -------------------------------------------------------------------------


def _block(x: Values) -> dict[str, object]:
    total, step = x.real("total_mm"), x.real("timestep_min")
    count = _step_count(x.real("duration_min"), step)
    return {
        "intensities_mm": np.full(count, total / count, dtype=np.float64),
        "times_min": _step_ends(count, step),
    }


def _block_exact(run: Callable[..., Values]) -> None:
    for total, duration, step in (
        (30.0, 60.0, 10.0),
        (39.16, 60.0, 5.0),
        (7.0, 3.0, 1.0),
    ):
        out = run(total_mm=total, duration_min=duration, timestep_min=step)
        count = round(Fraction(duration) / Fraction(step))
        assert_within(
            out.array("intensities_mm"),
            [float(Fraction(total) / count)] * count,
            rel=1.2e-16,
            reason="P / n in exact rational arithmetic, rounded once to float64",
        )


BLOCK: Final = FormulaSpec(
    name="block_hyetograph",
    title="Block (uniform) design hyetograph",
    function="hydrolog.precipitation.hietogram.block_hyetograph",
    family="scheme",
    equation="P_j = P / n for j = 1..n, n = Td / dt; t_j = j dt",
    latex=r"P_j = \frac{P}{n},\quad n = \frac{T_d}{\Delta t},\quad t_j = j\,\Delta t",
    variables=(_TOTAL, _DURATION, _TIMESTEP),
    outputs=(_BLOCKS, _TIMES),
    sources=(
        Source(
            citation="Wachulec, K., Licznar, P., Zaleski, J. and Wójcik, R. (2016). "
            "Przegląd Naukowy Inżynieria i Kształtowanie Środowiska 71",
            locator="p. 74: the block rain of constant intensity, the design rain most "
            "often taken by designers of drainage systems",
        ),
        _STEPS_OF_CHOW,
    ),
    constraints=_STEP_CONSTRAINTS,
    properties=Properties(
        units="homogeneous",
        monotonic={"total_mm": 1},
        scalings=_storm_scalings({"intensities_mm": 1}, {"times_min": 1}, _DOUBLED),
        conservation=(
            Conservation(
                name="steps_add_up",
                text="the steps hold the total",
                residual=_steps_add_up,
                tolerance=_ADD_UP,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="every step holds P / n in exact rational arithmetic",
                check=_block_exact,
            ),
        ),
    ),
    validation="none: the block storm is a design convention, not a model of observed "
    "storms",
    formula_version=1,
    status="oracle only",
    conventions=(
        "depths in mm per step; t_j the end of step j, step j covers ((j - 1) dt, "
        "j dt]",
        "the storm is made of whole steps: Td = n dt (ADR-0046)",
    ),
    traps={
        "many_small_terms": "conservation steps_add_up and "
        "test_a_storm_of_a_million_steps_holds_its_total",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="P / n in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_hyetographs.py (limit exact_rational)",
        ),
    ),
    base=_STORM_BASE,
)


def block_hyetograph(
    total_mm: float, duration_min: float, timestep_min: float
) -> HietogramResult:
    """Return the block hyetograph of a storm, spec block_hyetograph.

    Parameters
    ----------
    total_mm : float
        Total depth of the storm [mm].
    duration_min : float
        Duration of the storm [min], a whole number of steps.
    timestep_min : float
        Time step [min].

    Returns
    -------
    HietogramResult
        The depth and the end of each step.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        BLOCK, total_mm=total_mm, duration_min=duration_min, timestep_min=timestep_min
    )
    return _result(x, checked_outputs(BLOCK, _block(x)))


# --- triangle ----------------------------------------------------------------------


def _triangle_shares(count: int, peak: float) -> NDArray[np.float64]:
    """Return the share of each step: differences of the triangle's cumulative share."""
    ends = np.arange(count + 1, dtype=np.float64) / count
    rising = ends <= peak
    cumulative = np.empty_like(ends)
    cumulative[rising] = ends[rising] ** 2 / peak
    cumulative[~rising] = 1.0 - (1.0 - ends[~rising]) ** 2 / (1.0 - peak)
    return np.diff(cumulative)


def _peak_intensity_finite(x: Values) -> bool:
    hours = convert(x.real("duration_min"), "min", "h")
    return hours > 0.0 and math.isfinite(2.0 * x.real("total_mm") / hours)


def _triangle(x: Values) -> dict[str, object]:
    total, duration = x.real("total_mm"), x.real("duration_min")
    step, peak = x.real("timestep_min"), x.real("peak_position")
    count = _step_count(duration, step)
    return {
        "intensities_mm": total * _triangle_shares(count, peak),
        "times_min": _step_ends(count, step),
        "peak_intensity_mm_per_h": 2.0 * total / convert(duration, "min", "h"),
        "peak_time_min": peak * duration,
    }


def _triangle_cumulative(u: Fraction, r: Fraction) -> Fraction:
    return u * u / r if u <= r else 1 - (1 - u) ** 2 / (1 - r)


def _triangle_exact(run: Callable[..., Values]) -> None:
    for total, duration, step, peak in (
        (27.178, 15.0, 5.0, 0.38),
        (30.0, 60.0, 5.0, 0.5),
        (39.16, 60.0, 10.0, 0.294),
        (12.0, 90.0, 1.0, 0.9),
    ):
        out = run(
            total_mm=total, duration_min=duration, timestep_min=step, peak_position=peak
        )
        count = round(Fraction(duration) / Fraction(step))
        r = Fraction(peak)
        shares = [
            _triangle_cumulative(Fraction(j, count), r)
            - _triangle_cumulative(Fraction(j - 1, count), r)
            for j in range(1, count + 1)
        ]
        assert_within(
            out.array("intensities_mm"),
            [float(Fraction(total) * share) for share in shares],
            rel=1e-13,
            abs=1e-14,
            reason="the block integrals of the triangle in exact rational arithmetic; "
            "float64 rounds the squares and the differences of the cumulative share",
        )


def _mirrored(x: Values) -> dict[str, object]:
    return {**x, "peak_position": 1.0 - x.real("peak_position")}


def _reversed_blocks(out: Values) -> dict[str, object]:
    return {"intensities_mm": out.array("intensities_mm")[::-1]}


_PEAK_POSITION_SOURCE: Final = Source(
    citation=_CHOW,
    locator="Table 14.3.2, p. 464: storm advancement coefficients r of 0.294 to 0.480 "
    "for cities of the USA, India and Canada; Hydrolog's default 0.5 puts the peak "
    "at the centre",
    url=_CHOW_URL,
)

TRIANGULAR: Final = FormulaSpec(
    name="triangular_hyetograph",
    title="Triangular design hyetograph of Yen and Chow: block integrals of a triangle",
    function="hydrolog.precipitation.hietogram.triangular_hyetograph",
    family="scheme",
    equation=(
        "h = 2 P / Td, ta = r Td; cumulative share F(u) = u**2 / r for u <= r, else "
        "1 - "
        "(1 - u)**2 / (1 - r), u = t / Td; P_j = P (F(j / n) - F((j - 1) / n)), n = Td "
        "/ dt"
    ),
    latex=(
        r"h = \frac{2P}{T_d},\quad t_a = r\,T_d,\quad F(u) = \begin{cases} u^2/r & u "
        r"\le r \\ 1 - (1-u)^2/(1-r) & u > r \end{cases},\quad P_j = P\left[F\left("
        r"\tfrac{j}{n}\right) - F\left(\tfrac{j-1}{n}\right)\right]"
    ),
    variables=(
        _TOTAL,
        _DURATION,
        _TIMESTEP,
        Variable(
            name="peak_position",
            symbol="r",
            unit="-",
            description="Storm advancement coefficient: the time of the peak over the "
            "duration.",
            physical=Range(
                low=0.0, low_inclusive=False, high=1.0, high_inclusive=False
            ),
            applicability="unstated",
            typical=Range(low=0.294, high=0.5, source=_PEAK_POSITION_SOURCE),
        ),
    ),
    outputs=(
        _BLOCKS,
        _TIMES,
        Output(
            name="peak_intensity_mm_per_h",
            unit="mm/h",
            symbol="h",
            description="Intensity at the peak of the triangle.",
            physical=Range(low=0.0),
        ),
        Output(
            name="peak_time_min",
            unit="min",
            symbol="t_a",
            description="Time of the peak from the start of the storm.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        Source(
            citation=_CHOW,
            locator="sec. 14.3 Triangular hyetograph method, eqs. 14.3.1 to 14.3.3, "
            "Example 14.3.1, pp. 462-465 (after Yen and Chow 1980)",
            url=_CHOW_URL,
        ),
        Source(
            citation="Yen, B.C. and Chow, V.T. (1980). Design hyetographs for small "
            "drainage structures. Journal of the Hydraulics Division, ASCE 106(HY6), "
            "1055-1076",
            access="author-provided",
        ),
    ),
    constraints=(
        *_STEP_CONSTRAINTS,
        Constraint(
            name="peak_intensity_finite",
            cls="precondition",
            check=_peak_intensity_finite,
            text="2 P / Td is a finite intensity in float64 (a storm of a fraction of "
            "a second of 1e-300 mm or more is beyond it)",
            source=_HYDROLOG_BOUND,
            satisfied={"duration_min": 60.0},
            violated={"duration_min": 1e-310, "timestep_min": 1e-310},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"total_mm": 1},
        scalings=_storm_scalings(
            {"intensities_mm": 1, "peak_intensity_mm_per_h": 1},
            {"times_min": 1, "peak_time_min": 1, "peak_intensity_mm_per_h": -1},
            _DOUBLED,
        ),
        conservation=(
            Conservation(
                name="steps_add_up",
                text="the steps hold the total",
                residual=_steps_add_up,
                tolerance=_ADD_UP,
            ),
        ),
        symmetries=(
            Symmetry(
                name="mirror",
                text="the peak at 1 - r gives the steps in reverse order",
                inputs=_mirrored,
                outputs=_reversed_blocks,
                tolerance=Tolerance(
                    abs=1e-9,
                    reason="1 - r rounds once; the shares of the mirror differ by a "
                    "few "
                    "units in the last place of the total",
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="the steps equal the block integrals of the triangle in exact "
                "rational arithmetic",
                check=_triangle_exact,
            ),
        ),
    ),
    validation=(
        "Chow et al. (1988, p. 464) tabulate r fitted to storms of cities of the USA, "
        "India and Canada; the triangle itself is a design shape and the sources give "
        "no error statistic of it"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "depths in mm per step; t_j the end of step j; h in mm/h through the units "
        "table",
        (
            "each step holds the depth the continuous triangle gives it, the "
            "difference of the cumulative share at its ends (ADR-0046); the triangle "
            "is not sampled"
        ),
        "the storm is made of whole steps: Td = n dt (ADR-0046)",
    ),
    traps={
        "difference_denominator": "range cases peak_position-physical_low_inside and "
        "physical_high_inside: r next to 0 and next to 1 divide by r and 1 - r and "
        "stay finite",
        "many_small_terms": "conservation steps_add_up and "
        "test_a_storm_of_a_million_steps_holds_its_total",
    },
    reference_cases=("tests/fixtures/formulas/hyetographs-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the block integrals of the triangle in exact rational "
            "arithmetic (fractions)",
            test="tests/unit/test_formulas_hyetographs.py (limit exact_rational)",
        ),
    ),
    base={**_STORM_BASE, "peak_position": 0.38},
)


def triangular_hyetograph(
    total_mm: float, duration_min: float, timestep_min: float, peak_position: float
) -> TriangularStorm:
    """Return the triangular hyetograph of a storm, spec triangular_hyetograph.

    Parameters
    ----------
    total_mm : float
        Total depth of the storm [mm].
    duration_min : float
        Duration of the storm [min], a whole number of steps.
    timestep_min : float
        Time step [min].
    peak_position : float
        Storm advancement coefficient: the time of the peak over the duration.

    Returns
    -------
    TriangularStorm
        The depth and the end of each step, the intensity and the time of the peak.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        TRIANGULAR,
        total_mm=total_mm,
        duration_min=duration_min,
        timestep_min=timestep_min,
        peak_position=peak_position,
    )
    out = checked_outputs(TRIANGULAR, _triangle(x))
    storm = _result(x, out)
    return TriangularStorm(
        times_min=storm.times_min,
        intensities_mm=storm.intensities_mm,
        total_mm=storm.total_mm,
        duration_min=storm.duration_min,
        timestep_min=storm.timestep_min,
        peak_intensity_mm_per_h=out.real("peak_intensity_mm_per_h"),
        peak_time_min=out.real("peak_time_min"),
    )


# --- Beta --------------------------------------------------------------------------


def _beta(x: Values) -> dict[str, object]:
    total, step = x.real("total_mm"), x.real("timestep_min")
    count = _step_count(x.real("duration_min"), step)
    ends = np.arange(count + 1, dtype=np.float64) / count
    cumulative = betainc(x.real("alpha"), x.real("beta"), ends)
    return {
        "intensities_mm": total * np.diff(cumulative),
        "times_min": _step_ends(count, step),
    }


def _beta_polynomial(u: Fraction, a: int, b: int) -> Fraction:
    """Return I_u(a, b) of whole a and b: the binomial sum of the Beta distribution."""
    n = a + b - 1
    return sum(
        (
            Fraction(math.comb(n, k)) * u**k * (1 - u) ** (n - k)
            for k in range(a, n + 1)
        ),
        Fraction(0),
    )


def _beta_half(u: Fraction, b: int) -> Decimal:
    """Return I_u(1/2, b) of a whole b at 50 digits.

    The closed form sqrt(u) sum (1/2)_k (1 - u)^k / k! over k < b.
    """
    with localcontext() as context:
        context.prec = 50
        rising, total = Fraction(1), Fraction(0)
        for k in range(b):
            total += rising / math.factorial(k) * (1 - u) ** k
            rising *= Fraction(1, 2) + k
        root = (Decimal(u.numerator) / Decimal(u.denominator)).sqrt()
        return root * Decimal(total.numerator) / Decimal(total.denominator)


def _beta_exact(run: Callable[..., Values]) -> None:
    for a, b, count in ((2, 5, 12), (2, 5, 6), (1, 10, 24), (6, 6, 12), (10, 2, 24)):
        out = run(
            total_mm=1.0,
            duration_min=float(count),
            timestep_min=1.0,
            alpha=float(a),
            beta=float(b),
        )
        ends = [_beta_polynomial(Fraction(j, count), a, b) for j in range(count + 1)]
        assert_within(
            out.array("intensities_mm"),
            [float(high - low) for low, high in itertools.pairwise(ends)],
            abs=2e-15,
            reason="the block shares of whole alpha and beta in exact rational "
            "arithmetic; SciPy's betainc is within a few units in the last place",
        )
    count = 12
    out = run(
        total_mm=1.0,
        duration_min=float(count),
        timestep_min=1.0,
        alpha=0.5,
        beta=5.0,
    )
    ends_half = [_beta_half(Fraction(j, count), 5) for j in range(count + 1)]
    assert_within(
        out.array("intensities_mm"),
        [float(high - low) for low, high in itertools.pairwise(ends_half)],
        abs=2e-15,
        reason="I_u(1/2, 5) in closed form at 50 digits (decimal): the density is "
        "infinite at u = 0 and the first step holds its exact integral",
    )


def _swapped(x: Values) -> dict[str, object]:
    return {**x, "alpha": x.real("beta"), "beta": x.real("alpha")}


_SHAPE_SOURCE: Final = Source(
    citation=_KZGW,
    locator="Fig. 2.7, p. 26: typical Beta shapes (1, 10), (2, 10), (6, 6) and "
    "(10, 2); "
    "Hydrolog's default (2, 5)",
    url=_KZGW_URL,
)
_SHAPE_TEST = "a hundred times the largest parameter of KZGW (2017) Fig. 2.7, 10"

BETA: Final = FormulaSpec(
    name="beta_hyetograph",
    title="Beta design hyetograph: block integrals of the Beta density",
    function="hydrolog.precipitation.hietogram.beta_hyetograph",
    family="scheme",
    equation=(
        "P_j = P (I_(j / n)(alpha, beta) - I_((j - 1) / n)(alpha, beta)), n = Td / "
        "dt, I "
        "the regularised incomplete Beta function: the integral of the density "
        "u**(alpha - 1) (1 - u)**(beta - 1) / B(alpha, beta) over the step, u = t / Td"
    ),
    latex=(
        r"P_j = P\left[I_{j/n}(\alpha, \beta) - I_{(j-1)/n}(\alpha, \beta)\right],"
        r"\quad I_u(\alpha, \beta) = \frac{1}{B(\alpha, \beta)}\int_0^u s^{\alpha - 1}"
        r"(1 - s)^{\beta - 1}\,ds"
    ),
    variables=(
        _TOTAL,
        _DURATION,
        _TIMESTEP,
        Variable(
            name="alpha",
            symbol=r"\alpha",
            unit="-",
            description="First shape parameter (r of KZGW): the rise of the storm.",
            physical=Range(
                low=0.0, low_inclusive=False, test_high=1000.0, test_reason=_SHAPE_TEST
            ),
            applicability="unstated",
            typical=Range(low=1.0, high=10.0, source=_SHAPE_SOURCE),
        ),
        Variable(
            name="beta",
            symbol=r"\beta",
            unit="-",
            description="Second shape parameter (s of KZGW): the fall of the storm.",
            physical=Range(
                low=0.0, low_inclusive=False, test_high=1000.0, test_reason=_SHAPE_TEST
            ),
            applicability="unstated",
            typical=Range(low=2.0, high=10.0, source=_SHAPE_SOURCE),
        ),
    ),
    outputs=(_BLOCKS, _TIMES),
    sources=(
        Source(
            citation=_KZGW,
            locator="ch. II.3, eqs. 2.20-2.22, p. 25 (after Węglarczyk 1993); "
            "Fig. 2.7, "
            "p. 26",
            url=_KZGW_URL,
        ),
        Source(
            citation="Węglarczyk, S. (1993), as cited by KZGW (2017)",
            access="author-provided",
        ),
    ),
    constraints=_STEP_CONSTRAINTS,
    properties=Properties(
        units="homogeneous",
        monotonic={"total_mm": 1},
        scalings=_storm_scalings({"intensities_mm": 1}, {"times_min": 1}, _DOUBLED),
        conservation=(
            Conservation(
                name="steps_add_up",
                text="the steps hold the total",
                residual=_steps_add_up,
                tolerance=_ADD_UP,
            ),
        ),
        symmetries=(
            Symmetry(
                name="swap",
                text="swapping alpha and beta gives the steps in reverse order",
                inputs=_swapped,
                outputs=_reversed_blocks,
                tolerance=Tolerance(
                    abs=1e-9,
                    reason="I_u(a, b) = 1 - I_(1-u)(b, a) holds to SciPy's precision "
                    "of the incomplete Beta function, a few units in the last place",
                ),
            ),
        ),
        limits=(
            Limit(
                name="uniform",
                text="alpha = beta = 1 gives the block storm",
                inputs={"alpha": 1.0, "beta": 1.0},
                expected={"intensities_mm": [2.5] * 12},
                tolerance=Tolerance(
                    abs=1e-14,
                    reason="I_u(1, 1) = u; the differences of j / n round once",
                ),
            ),
            Limit(
                name="exact_integrals",
                text="the steps equal the integrals of the density in exact "
                "arithmetic: rational for whole alpha and beta, a closed form at 50 "
                "digits for alpha = 1/2",
                check=_beta_exact,
            ),
        ),
    ),
    validation=(
        "KZGW (2017, p. 26) fits alpha and beta so that the peak of the hydrograph of "
        "the storm equals the flow of the same probability; the sources give no error "
        "statistic of the shape against observed storms"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        "depths in mm per step; t_j the end of step j",
        (
            "each step holds the integral of the density over it (ADR-0046); KZGW "
            "(2017, eq. 2.20) evaluates the density at the ends of the steps, which "
            "shifts the storm by half a step and is not followed"
        ),
        "the storm is made of whole steps: Td = n dt (ADR-0046)",
    ),
    assumptions=(
        (
            "KZGW (2017) splits a daily total into hourly steps of a hypothetical "
            "flood; Hydrolog takes any duration and step"
        ),
    ),
    traps={
        "many_small_terms": "conservation steps_add_up and "
        "test_a_storm_of_a_million_steps_holds_its_total",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="the block integrals in exact rational arithmetic for whole "
            "alpha and beta (the binomial sum of I_u) and in closed form at 50 digits "
            "(decimal) for alpha = 1/2",
            test="tests/unit/test_formulas_hyetographs.py (limit exact_integrals)",
        ),
    ),
    base={**_STORM_BASE, "alpha": 2.0, "beta": 5.0},
)


def beta_hyetograph(
    total_mm: float,
    duration_min: float,
    timestep_min: float,
    alpha: float,
    beta: float,
) -> HietogramResult:
    """Return the Beta hyetograph of a storm, spec beta_hyetograph.

    Parameters
    ----------
    total_mm : float
        Total depth of the storm [mm].
    duration_min : float
        Duration of the storm [min], a whole number of steps.
    timestep_min : float
        Time step [min].
    alpha, beta : float
        Shape parameters of the Beta density.

    Returns
    -------
    HietogramResult
        The depth and the end of each step.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        BETA,
        total_mm=total_mm,
        duration_min=duration_min,
        timestep_min=timestep_min,
        alpha=alpha,
        beta=beta,
    )
    return _result(x, checked_outputs(BETA, _beta(x)))


# --- Euler type II ---------------------------------------------------------------


def _interpolated_depths(
    durations: NDArray[np.float64],
    depths: NDArray[np.float64],
    at: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Return the depths of a curve at durations within it, linear in ln D.

    A duration within 1e-9 of a point of the curve takes that point's depth.
    """
    found = np.searchsorted(durations, at)
    upper = np.clip(found, 0, len(durations) - 1)
    lower = np.clip(found - 1, 0, len(durations) - 1)
    snapped = np.where(
        np.abs(durations[upper] - at) <= _SAME_DURATION * durations[upper],
        durations[upper],
        np.where(
            np.abs(durations[lower] - at) <= _SAME_DURATION * durations[lower],
            durations[lower],
            at,
        ),
    )
    return np.interp(np.log(snapped), np.log(durations), depths)


def euler_ii_peak_block(n_steps: int) -> int:
    """Return the block of the peak of an Euler II storm of whole steps, from zero.

    The peak interval starts at the share of the duration of spec
    euler_ii_hyetograph, rounded down to a whole step.
    """
    return (n_steps * _PEAK_START.numerator) // _PEAK_START.denominator


def _euler_ii(x: Values) -> dict[str, object]:
    step = x.real("timestep_min")
    count = _step_count(x.real("duration_min"), step)
    times = _step_ends(count, step)
    cumulative = _interpolated_depths(
        x.array("durations_min"), x.array("depths_mm"), times
    )
    increments = np.diff(cumulative, prepend=0.0)
    peak = euler_ii_peak_block(count)
    # Δh_1 at the peak, Δh_2..Δh_(k+1) back to t = 0, the rest after the peak
    blocks = np.concatenate((increments[peak::-1], increments[peak + 1 :]))
    return {
        "intensities_mm": blocks,
        "times_min": times,
        "total_mm": float(cumulative[-1]),
        "peak_start_min": peak * step,
    }


def _curve_lengths(x: Values) -> bool:
    return len(x.array("durations_min")) == len(x.array("depths_mm"))


def _durations_increasing(x: Values) -> bool:
    return bool(np.all(np.diff(x.array("durations_min")) > 0.0))


def _depths_not_decreasing(x: Values) -> bool:
    return bool(np.all(np.diff(x.array("depths_mm")) >= 0.0))


def _curve_covers(x: Values) -> bool:
    durations = x.array("durations_min")
    return bool(
        durations[0] * (1.0 - _SAME_DURATION) <= x.real("timestep_min")
        and durations[-1] * (1.0 + _SAME_DURATION) >= x.real("duration_min")
    )


def _ln_depth(durations: list[float], depths: list[float], at: Fraction) -> Decimal:
    """Return h at a duration, linear in ln D, at 40 digits (the oracle's own form)."""
    with localcontext() as context:
        context.prec = 40
        where = Decimal(at.numerator) / Decimal(at.denominator)
        for (d0, h0), (d1, h1) in itertools.pairwise(
            zip(durations, depths, strict=True)
        ):
            if Decimal(d0) <= where <= Decimal(d1):
                share = (where / Decimal(d0)).ln() / (Decimal(d1) / Decimal(d0)).ln()
                return Decimal(h0) + (Decimal(h1) - Decimal(h0)) * share
        raise AssertionError(f"{float(at)} min lies outside the curve")


_DECREASING_CURVES: Final = (
    (
        [5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 90.0],
        [9.513, 13.95, 16.947, 19.176, 22.392, 25.596, 27.9, 29.97],
        90.0,
    ),
    (
        [5.0, 10.0, 15.0, 30.0, 45.0, 60.0],
        [21.82, 25.68, 28.22, 33.23, 36.58, 39.16],
        60.0,
    ),
)
"""Curves whose increments decrease at steps of 5 min: KOSTRA-DWD of Göllheim (T = 5 a,
from its rain rates) and PMAXTP of Warsaw (POT, p = 1 %)."""


def _a118_sorted(run: Callable[..., Values]) -> None:
    for durations, depths, duration in _DECREASING_CURVES:
        out = run(
            durations_min=durations,
            depths_mm=depths,
            duration_min=duration,
            timestep_min=5.0,
        )
        count = int(duration) // 5
        cumulative = [
            _ln_depth(durations, depths, Fraction(5 * j)) for j in range(1, count + 1)
        ]
        ranked = sorted(
            (high - low for low, high in itertools.pairwise([Decimal(0), *cumulative])),
            reverse=True,
        )
        peak = math.floor(Fraction(3, 10) * count)
        storm = [*reversed(ranked[: peak + 1]), *ranked[peak + 1 :]]
        assert_within(
            out.array("intensities_mm"),
            [float(block) for block in storm],
            abs=1e-12,
            reason="the storm of A 118 as DWD describes it (the largest increment at "
            "the peak, the next larger before it ascending, the rest after it "
            "descending), its curve interpolated in ln D at 40 digits",
        )


_AURICH: Final = (
    [5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 240.0, 360.0, 540.0],
    [
        11.0,
        14.16,
        16.09,
        17.69,
        19.89,
        22.02,
        23.84,
        26.19,
        28.32,
        31.0,
        33.17,
        36.68,
        40.81,
    ],
)
"""The curve of the itwh KOSTRA-DWD 2020 printout of Aurich (T = 3 a) at the durations
of KOSTRA: the cumulative depths of its blocks in the order of their durations."""


def _peak_start(run: Callable[..., Values]) -> None:
    for duration in (5.0, 15.0, 60.0, 150.0, 165.0, 180.0, 540.0):
        out = run(
            durations_min=_AURICH[0],
            depths_mm=_AURICH[1],
            duration_min=duration,
            timestep_min=5.0,
        )
        count = int(duration) // 5
        start = 5 * math.floor(Fraction(3, 10) * count)
        assert out.real("peak_start_min") == start, (duration, out["peak_start_min"])
        blocks = out.array("intensities_mm")
        assert blocks[start // 5] == blocks.max(), duration


def _windows(x: Values, out: Values) -> float:
    """Return the largest miss of the windows around the peak from their h(m dt)."""
    durations = x.array("durations_min").tolist()
    depths = x.array("depths_mm").tolist()
    step = x.real("timestep_min")
    blocks = out.array("intensities_mm").tolist()
    peak = round(out.real("peak_start_min") / step)
    # the window of m steps: back from the peak while it fits, then from t = 0
    before = list(itertools.accumulate(reversed(blocks[: peak + 1])))
    onward = list(itertools.accumulate(blocks))
    largest, segment = 0.0, 0
    for m in range(1, len(blocks) + 1):
        held = before[m - 1] if m <= peak + 1 else onward[m - 1]
        at = min(max(m * step, durations[0]), durations[-1])
        while segment < len(durations) - 2 and at > durations[segment + 1]:
            segment += 1
        if len(durations) == 1:
            design = depths[0]
        else:
            d0, d1 = durations[segment], durations[segment + 1]
            h0, h1 = depths[segment], depths[segment + 1]
            design = h0 + (h1 - h0) * math.log(at / d0) / math.log(d1 / d0)
        largest = max(largest, abs(held - design))
    return largest


EULER_II: Final = FormulaSpec(
    name="euler_ii_hyetograph",
    title="Euler type II design storm of ATV-DVWK-A 118 from a depth-duration curve",
    function="hydrolog.precipitation.hietogram.euler_ii_hyetograph",
    family="scheme",
    equation=(
        "h(t) of the curve at t = j dt (depth_duration_interpolation); increments dh_j "
        "= h(j dt) - h((j - 1) dt), j = 1..n, n = Td / dt; peak block k = floor(0.3 n) "
        "(from 0, the interval from 0.3 Td rounded down to a step); block k holds "
        "dh_1, blocks k - 1 .. 0 hold dh_2 .. dh_(k+1), blocks k + 1 .. n - 1 hold "
        "dh_(k+2) .. "
        "dh_n; the total is h(Td)"
    ),
    latex=(
        r"\Delta h_j = h(j\,\Delta t) - h((j-1)\,\Delta t),\quad k = \lfloor 0.3\,n "
        r"\rfloor,\quad P_{k-i} = \Delta h_{i+1}\ (i = 0..k),\quad P_{i-1} = \Delta "
        r"h_i\ (i = k+2..n)"
    ),
    variables=(
        Variable(
            name="durations_min",
            symbol="D_i",
            unit="min",
            kind="real_array",
            description="Durations of the points of the depth-duration curve, "
            "increasing.",
            physical=Range(
                low=0.0, low_inclusive=False, test_high=43200.0, test_reason=_LONGEST
            ),
            applicability="unstated",
            typical=Range(low=5.0, high=4320.0, source=_PMAXTP),
        ),
        Variable(
            name="depths_mm",
            symbol="h_i",
            unit="mm",
            kind="real_array",
            description="Depths of the curve at those durations, of one probability.",
            physical=Range(low=0.0, test_high=1825.0, test_reason=_WORLD_RECORD),
            applicability="unstated",
            typical=Range(low=6.96, high=341.27, source=_PMAXTP_FIXTURES),
        ),
        _DURATION,
        _TIMESTEP,
    ),
    outputs=(
        _BLOCKS,
        _TIMES,
        Output(
            name="total_mm",
            unit="mm",
            symbol="h(T_d)",
            description="Total depth of the storm, the depth of the curve at Td.",
            physical=Range(low=0.0),
        ),
        Output(
            name="peak_start_min",
            unit="min",
            symbol=r"k\,\Delta t",
            description="Start of the interval of the peak from the start of the "
            "storm.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_A118, _MALITZ, _KAZMIERCZAK),
    constants=(
        Constant(
            name="peak_start_share",
            value=_PEAK_START,
            unit="-",
            symbol="0.3",
            source=_A118,
        ),
    ),
    constraints=(
        Constraint(
            name="depths_not_decreasing",
            cls="physical",
            check=_depths_not_decreasing,
            text="h_(i+1) >= h_i: the depth of a longer duration is never smaller",
            source=_MALITZ,
            satisfied={"depths_mm": [21.82, 25.68, 28.22, 33.23, 36.58, 39.16]},
            violated={"depths_mm": [21.82, 25.68, 28.22, 33.23, 36.58, 36.0]},
        ),
        Constraint(
            name="curve_lengths",
            cls="precondition",
            check=_curve_lengths,
            text="one depth for each duration of the curve",
            source=_A118,
            satisfied={"depths_mm": [21.82, 25.68, 28.22, 33.23, 36.58, 39.16]},
            violated={"depths_mm": [21.82, 25.68]},
        ),
        Constraint(
            name="durations_increasing",
            cls="precondition",
            check=_durations_increasing,
            text="D_(i+1) > D_i: each duration of the curve once, in order",
            source=_A118,
            satisfied={"durations_min": [5.0, 10.0, 15.0, 30.0, 45.0, 60.0]},
            violated={"durations_min": [5.0, 10.0, 10.0, 30.0, 45.0, 60.0]},
        ),
        *_STEP_CONSTRAINTS,
        Constraint(
            name="curve_covers",
            cls="precondition",
            check=_curve_covers,
            text="D_1 <= dt and D_m >= Td: the curve reaches from the step to the "
            "duration, nothing is extrapolated",
            source=_HYDROLOG_BOUND,
            satisfied={"duration_min": 60.0},
            violated={"duration_min": 90.0},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="depth",
                inputs={"depths_mm": 1},
                outputs={"intensities_mm": 1, "total_mm": 1},
                tolerance=_DOUBLED,
            ),
            Scaling(
                name="time",
                inputs={"durations_min": 1, "duration_min": 1, "timestep_min": 1},
                outputs={"times_min": 1, "peak_start_min": 1},
                tolerance=Tolerance(
                    rel=1e-9,
                    abs=1e-9,
                    reason="the logarithms of doubled durations round differently; the "
                    "interpolated depths move by a few units in the last place of a "
                    "depth over the logarithm of a ratio of durations",
                ),
            ),
        ),
        conservation=(
            Conservation(
                name="steps_add_up",
                text="the steps hold h(Td), the total",
                residual=lambda x, out: (
                    math.fsum(out.array("intensities_mm")) - out.real("total_mm")
                ),
                tolerance=_ADD_UP,
            ),
            Conservation(
                name="windows_hold_design_depths",
                text="the m steps around the peak (back to t = 0, then onward) hold "
                "h(m dt) of the curve for every m (Malitz 2009, slide 17)",
                residual=_windows,
                tolerance=Tolerance(
                    abs=1e-9,
                    reason="sums of up to a million differences of the interpolated "
                    "depths against the interpolation in another form",
                ),
            ),
        ),
        limits=(
            Limit(
                name="a118_sorted",
                text="for a curve whose increments decrease, the storm DWD describes: "
                "the largest increment at the peak, the next larger ones before it in "
                "ascending order, the rest after it in descending order",
                check=_a118_sorted,
                source=_MALITZ,
            ),
            Limit(
                name="peak_start",
                text="the peak interval starts at 0.3 Td rounded down to a step: 0, 0, "
                "15, 45, 45, 50 and 160 min for 5 to 540 min in steps of 5 min",
                check=_peak_start,
                source=_A118,
            ),
        ),
    ),
    validation=(
        "none: a design storm of drainage design (A 118); Licznar and Szeląg (2014, "
        "abstract) find its shape departs from observed storms beyond 180 min"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "depths in mm per step; t_j the end of step j",
        (
            "the increments keep the order of their durations and are not sorted, so "
            "the m steps that end with the peak hold h(m dt) also where interpolation "
            "makes an increment grow (ADR-0042, as the itwh software); for a curve "
            "whose increments decrease this is the sorted arrangement of A 118 and DWD"
        ),
        (
            "the peak starts at 0.3 Td rounded down to a whole step (A 118 as quoted: "
            "to a multiple of 5 min); the itwh software puts the peak of 15 min in "
            "the second step and Kaźmierczak and Kotowski (2012) end it at Td / 3, a "
            "step later for Td of 165 and 180 min"
        ),
        "the total is h(Td) of the curve; the curve is of one probability",
        "the storm is made of whole steps: Td = n dt (ADR-0046)",
    ),
    assumptions=(
        (
            "A 118 asks for a duration of at least twice the longest flow time; the "
            "Polish models of Wartalska and Kotowski (2020) span 30 to 180 min; the "
            "sources state no range of the formula's inputs, so none gives a notice"
        ),
    ),
    traps={
        "difference_denominator": "durations_increasing refuses equal durations, whose "
        "ln ratio is 0; a step end within 1e-9 of a point takes its depth",
        "gap_propagation": "type cases durations_min-nan_element and "
        "depths_mm-nan_element: a gap is refused",
        "many_small_terms": "conservation steps_add_up and windows_hold_design_depths",
    },
    reference_cases=("tests/fixtures/formulas/hyetographs-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="the arrangement DWD describes (sorted increments) on a curve "
            "interpolated in ln D at 40 digits (decimal), for curves whose increments "
            "decrease",
            test="tests/unit/test_formulas_hyetographs.py (limit a118_sorted)",
        ),
    ),
    base={
        "durations_min": [5.0, 10.0, 15.0, 30.0, 45.0, 60.0],
        "depths_mm": [21.82, 25.68, 28.22, 33.23, 36.58, 39.16],
        "duration_min": 60.0,
        "timestep_min": 5.0,
    },
)


def euler_ii_hyetograph(
    durations_min: NDArray[np.float64] | list[float] | tuple[float, ...],
    depths_mm: NDArray[np.float64] | list[float] | tuple[float, ...],
    duration_min: float,
    timestep_min: float,
) -> EulerIIStorm:
    """Return the Euler type II storm of a curve, spec euler_ii_hyetograph.

    Parameters
    ----------
    durations_min : array_like of float
        Durations of the points of the curve [min], increasing.
    depths_mm : array_like of float
        Depths of the curve at those durations [mm], of one probability.
    duration_min : float
        Duration of the storm [min], a whole number of steps.
    timestep_min : float
        Time step [min].

    Returns
    -------
    EulerIIStorm
        The depth and the end of each step, the total and the start of the peak.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        EULER_II,
        durations_min=durations_min,
        depths_mm=depths_mm,
        duration_min=duration_min,
        timestep_min=timestep_min,
    )
    out = checked_outputs(EULER_II, _euler_ii(x))
    return EulerIIStorm(
        times_min=out.array("times_min"),
        intensities_mm=out.array("intensities_mm"),
        total_mm=out.real("total_mm"),
        duration_min=x.real("duration_min"),
        timestep_min=x.real("timestep_min"),
        peak_start_min=out.real("peak_start_min"),
    )


SPECS: Final = (BLOCK, TRIANGULAR, BETA, EULER_II)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""

TIER_B: Final = (
    TierBSpec(
        name="depth_duration_interpolation",
        function="hydrolog.precipitation.hietogram.EulerIIHietogram.depth_mm",
        definition="the depth of a depth-duration curve at a duration between two of "
        "its points D_i <= D <= D_(i+1): h = h_i + (h_(i+1) - h_i) ln(D / D_i) / "
        "ln(D_(i+1) / D_i); a duration within 1e-9 of a point takes its depth; none "
        "outside the curve",
        convention="linear in ln D (ADR-0042): it reproduces the itwh KOSTRA-DWD 2010R "
        "printouts of Göllheim to 0.07 mm from their depths printed to 0.1 mm, where "
        "linear in D misses by 0.16 mm; the DWA MDMS tool interpolates linearly in D "
        "and HEC-HMS in log-log; nothing is extrapolated",
        source=Source(
            citation="itwh KOSTRA-DWD 2010R 3.2.3, model rains of Göllheim (T = 5 a), "
            "Anhang III of a planning procedure of Rhineland-Palatinate",
            locator="pp. 2-5 (storms of 15 to 90 min) against p. 6 (depths hN)",
            url="https://upload.open.rlp.de/dataset/2420cfcf-294f-400f-8b82-"
            "93f2537feef6/resource/f7ac269a-d9c3-40ce-b926-ee7cafa9a4ab/download/"
            "merged-anhang-iii.pdf",
        ),
    ),
    TierBSpec(
        name="pmaxtp_depth",
        function="hydrolog._pmaxtp.fetch_depth",
        definition="the depth of the PMAXTP table of IMGW-PIB for a point, a duration "
        "and a probability of exceedance of the tables, by POT or AMP, with the depths "
        "of the 16 durations at that probability: the depth-duration curve of "
        "euler_ii_hyetograph; nothing is computed or interpolated",
        convention="p is a probability of exceedance in per cent (practice reads T = "
        "100 / p years; IMGW-PIB documents no conversion of POT to annual "
        "probabilities); the depth is returned as IMGW-PIB gives it (0.01 mm); only "
        "the durations and probabilities of the tables; POT by default, which IMGW-PIB "
        "recommends for p >= 50 % and treats as equivalent to AMP below (p. 23). The "
        "row is declared here: hydrolog._pmaxtp imports no numerical library",
        source=Source(
            citation="Ozga-Zieliński, B. (ed.) (2022). Modele probabilistyczne opadów "
            "maksymalnych o określonym czasie trwania i prawdopodobieństwie "
            "przewyższenia - projekt PMAXTP. IMGW-PIB, Warszawa",
            locator="p. 10 (16 durations of 5 min to 72 h, 27 probabilities of 0.01 to "
            "99.9 %), p. 23 (POT and AMP)",
            url="https://klimat.imgw.pl/opady-maksymalne/",
        ),
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""


class BlockHietogram(Hietogram):
    """
    Block (uniform) hyetograph with constant intensity (spec ``block_hyetograph``).

    The simplest hyetograph type where precipitation is uniformly
    distributed over the storm duration.

    Examples
    --------
    >>> hietogram = BlockHietogram()
    >>> result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)
    >>> print(result.intensities_mm)
    [5. 5. 5. 5. 5. 5.]
    """

    def generate(
        self,
        total_mm: float,
        duration_min: float,
        timestep_min: float = 5.0,
    ) -> HietogramResult:
        """
        Generate block (uniform) hyetograph.

        Parameters
        ----------
        total_mm : float
            Total precipitation depth [mm].
        duration_min : float
            Duration of the storm event [min].
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.

        Returns
        -------
        HietogramResult
            Generated hyetograph with uniform intensities.

        Examples
        --------
        >>> hietogram = BlockHietogram()
        >>> result = hietogram.generate(total_mm=30.0, duration_min=60.0)
        >>> print(f"Total: {result.intensities_mm.sum():.1f} mm")
        Total: 30.0 mm
        """
        total, duration, step, _ = _storm(total_mm, duration_min, timestep_min)
        return block_hyetograph(total, duration, step)


class TriangularHietogram(Hietogram):
    """
    Triangular hyetograph of Yen and Chow (1980) (spec ``triangular_hyetograph``).

    The intensity rises linearly from zero at the start to its peak at
    ``peak_position`` of the duration (the storm advancement coefficient r) and falls
    linearly to zero at the end; each step holds the depth the continuous triangle
    gives it, so the steps hold the total whatever their number, and with r = 0.5 and
    an even number of steps the two middle steps are equal. ``docs/FORMULAS.md`` shows
    the equation, ranges and sources of the spec.

    Parameters
    ----------
    peak_position : float, optional
        The storm advancement coefficient r: the time of the peak as a fraction of the
        duration, 0 < r < 1, by default 0.5 (peak at the centre).

    References
    ----------
    .. [1] Yen B.C., Chow V.T. (1980). Design hyetographs for small drainage
           structures. J. Hydraul. Div. ASCE 106(HY6), 1055-1076.
    .. [2] Chow V.T., Maidment D.R., Mays L.W. (1988). Applied Hydrology.
           McGraw-Hill, sec. 14.3, eqs. 14.3.1-14.3.3, Example 14.3.1, pp. 462-465.

    Examples
    --------
    Chow et al. (1988), Example 14.3.1 (Urbana, 5-year, 15 min, 1.07 in = 27.178 mm,
    r = 0.38) in steps of 5 min:

    >>> hietogram = TriangularHietogram(peak_position=0.38)
    >>> result = hietogram.generate(27.178, duration_min=15.0, timestep_min=5.0)
    >>> result.intensities_mm.round(3).tolist()
    [7.947, 14.361, 4.871]
    """

    def __init__(self, peak_position: float = 0.5) -> None:
        """
        Initialize triangular hyetograph.

        Parameters
        ----------
        peak_position : float, optional
            The time of the peak as a fraction of the duration, 0 < r < 1, by
            default 0.5.

        Raises
        ------
        InvalidParameterError
            If peak_position is not a finite number in (0, 1) (``details.option``
            ``peak_position``).
        """
        position = _finite_number("peak_position", peak_position)
        if not 0 < position < 1:
            bound = "exclusive_minimum" if position <= 0 else "exclusive_maximum"
            raise InvalidParameterError(
                f"peak_position must be in range (0, 1), got {position:g}",
                details={
                    "option": "peak_position",
                    "reason": bound,
                    bound: 0 if position <= 0 else 1,
                    "value": position,
                },
            )
        self.peak_position = position

    def generate(
        self,
        total_mm: float,
        duration_min: float,
        timestep_min: float = 5.0,
    ) -> HietogramResult:
        """
        Generate triangular hyetograph.

        Parameters
        ----------
        total_mm : float
            Total precipitation depth [mm].
        duration_min : float
            Duration of the storm event [min], a whole number of steps.
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.

        Returns
        -------
        HietogramResult
            The depth of the triangle in each step.

        Raises
        ------
        InvalidParameterError
            As :meth:`Hietogram._validate_params`.
        """
        total, duration, step, _ = _storm(total_mm, duration_min, timestep_min)
        storm = triangular_hyetograph(total, duration, step, self.peak_position)
        return HietogramResult(
            times_min=storm.times_min,
            intensities_mm=storm.intensities_mm,
            total_mm=storm.total_mm,
            duration_min=storm.duration_min,
            timestep_min=storm.timestep_min,
        )


class BetaHietogram(Hietogram):
    """
    Beta distribution hyetograph (spec ``beta_hyetograph``).

    The intensity over the relative time of the storm follows the Beta density of
    ``alpha`` and ``beta`` (KZGW 2017, after Węglarczyk 1993); each step holds the
    integral of the density over it, so the steps hold the total for every α, β > 0,
    also where the density is infinite (α < 1 or β < 1). ``docs/FORMULAS.md`` shows the
    equation, ranges and sources of the spec.

    Parameters
    ----------
    alpha : float, optional
        Alpha parameter of Beta distribution, by default 2.0.
        Controls the shape of the rising limb.
    beta : float, optional
        Beta parameter of Beta distribution, by default 5.0.
        Controls the shape of the falling limb.

    Notes
    -----
    The peak of the density lies at ``(α-1)/(α+β-2)`` of the duration for α, β > 1:
    (2, 5) puts it at 0.2, (2, 2) at the centre, (5, 2) at 0.8. KZGW (2017, Fig. 2.7)
    shows (1, 10), (2, 10), (6, 6) and (10, 2) and fits α and β so that the peak flow
    equals the flow of the same probability. KZGW evaluates the density at the ends
    of the intervals; the block integrals here neither shift the storm by half a step
    nor depend on where in the step the density is read.

    References
    ----------
    .. [1] KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów
           maksymalnych ... (Banasik K., Wałęga A., Węglarczyk S., Wiezik B.), ch. II.3,
           eqs. 2.20-2.22, p. 25, after Węglarczyk S. (1993).

    Examples
    --------
    >>> hietogram = BetaHietogram(alpha=2.0, beta=5.0)
    >>> result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)
    >>> result.intensities_mm.round(3).tolist()
    [7.897, 11.568, 7.254, 2.746, 0.515, 0.02]
    """

    def __init__(self, alpha: float = 2.0, beta: float = 5.0) -> None:
        """
        Initialize Beta hyetograph.

        Parameters
        ----------
        alpha : float, optional
            Alpha parameter (>0), by default 2.0.
        beta : float, optional
            Beta parameter (>0), by default 5.0.

        Raises
        ------
        InvalidParameterError
            If alpha or beta is not a finite number above zero (``details.option``
            names it).
        """
        self.alpha = _finite_positive("alpha", alpha)
        self.beta = _finite_positive("beta", beta)

    def generate(
        self,
        total_mm: float,
        duration_min: float,
        timestep_min: float = 5.0,
    ) -> HietogramResult:
        """
        Generate Beta distribution hyetograph.

        Parameters
        ----------
        total_mm : float
            Total precipitation depth [mm].
        duration_min : float
            Duration of the storm event [min], a whole number of steps.
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.

        Returns
        -------
        HietogramResult
            The depth of the Beta storm in each step.

        Raises
        ------
        InvalidParameterError
            As :meth:`Hietogram._validate_params`.
        """
        total, duration, step, _ = _storm(total_mm, duration_min, timestep_min)
        return beta_hyetograph(total, duration, step, self.alpha, self.beta)


DepthDurationCurve = Mapping[float, float] | Mapping[int, float] | Mapping[str, float]
"""A depth-duration curve: duration [min] -> depth [mm] of one probability. A key may
also be the text of a number (``"60"``), as in a JSON object."""


def _curve_error(message: str, reason: str, **details: object) -> InvalidParameterError:
    """Build the error of a depth-duration curve that cannot be used."""
    return InvalidParameterError(
        f"depth_duration_mm: {message}",
        details={"option": "depth_duration_mm", "reason": reason, **details},
        hint=(
            "Give the depths [mm] of one probability by duration [min], not "
            "decreasing, e.g. the depth_duration_mm of `precip pmaxtp`."
        ),
    )


def _curve_duration(key: object) -> float:
    """Return the duration [min] of a key of the curve: a number or its text."""
    duration = math.nan
    if isinstance(key, numbers.Real) and not isinstance(key, bool):
        duration = float(key)
    elif isinstance(key, str):
        try:
            duration = float(key.strip())
        except ValueError:
            duration = math.nan
    if not math.isfinite(duration) or duration <= 0:
        raise _curve_error(
            f"the duration {key!r} is not a number of minutes above 0",
            "invalid_duration",
            value=key if isinstance(key, str | int | float) else str(key),
        )
    return duration


def _curve_depth(duration: float, value: object) -> float:
    """Return the depth [mm] of the curve at ``duration``: finite, not negative."""
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise _curve_error(
            f"the depth of {duration:g} min must be a number, got {value!r}",
            "type",
            duration_min=duration,
        )
    depth = float(value)
    if not math.isfinite(depth):
        raise _curve_error(
            f"the depth of {duration:g} min is not finite ({depth})",
            "not_finite",
            duration_min=duration,
            value=str(depth),
        )
    if depth < 0:
        raise _curve_error(
            f"the depth of {duration:g} min is negative ({depth:g} mm)",
            "minimum",
            duration_min=duration,
            minimum=0,
            value=depth,
        )
    return depth


def _curve_points(
    curve: object,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return the durations [min] and depths [mm] of a curve, by duration.

    Raises
    ------
    InvalidParameterError
        If the curve is not a mapping or is empty, a duration or a depth is not valid
        (not a number, not finite, not above zero, negative), a duration is given twice
        or the depth decreases with the duration (``details.reason`` ``decreasing``
        with the two ``durations_min`` and their ``depths_mm``).
    """
    if not isinstance(curve, Mapping):
        raise _curve_error(
            f"expected a mapping of duration [min] to depth [mm], got "
            f"{type(curve).__name__}",
            "type",
        )
    if not curve:
        raise _curve_error("the curve has no point", "empty")
    points: dict[float, float] = {}
    for key, value in curve.items():
        duration = _curve_duration(key)
        if duration in points:
            raise _curve_error(
                f"the duration {duration:g} min is given twice",
                "duplicate_duration",
                duration_min=duration,
            )
        points[duration] = _curve_depth(duration, value)
    durations = sorted(points)
    for shorter, longer in itertools.pairwise(durations):
        if points[longer] < points[shorter]:
            raise _curve_error(
                f"the depth decreases from {points[shorter]:g} mm at {shorter:g} min "
                f"to {points[longer]:g} mm at {longer:g} min; a depth-duration curve "
                "never decreases",
                "decreasing",
                durations_min=[shorter, longer],
                depths_mm=[points[shorter], points[longer]],
            )
    return (
        np.array(durations, dtype=np.float64),
        np.array([points[duration] for duration in durations], dtype=np.float64),
    )


class EulerIIHietogram(Hietogram):
    """
    Euler type II design storm of ATV-DVWK-A 118 from a depth-duration curve.

    The storm is built from the depth-duration curve h(D) of one probability (return
    period): PMAXTP of IMGW-PIB (``precip pmaxtp`` gives it), KOSTRA-DWD or a local
    formula, by spec ``euler_ii_hyetograph``: the increments of the curve over the
    steps, the first at the peak, which starts at 0.3·D rounded down to a step, the
    next ones back to t = 0 and the rest after the peak, in the order of their
    durations. Every ``m`` steps around the peak then hold ``h(mΔt)``, and the whole
    storm h(D). Depths between the points of the curve are interpolated linearly in
    ln D (Tier B ``depth_duration_interpolation``); the curve must reach from the time
    step to the duration: nothing is extrapolated. ``docs/FORMULAS.md`` shows the
    equation, constants, ranges and sources.

    Parameters
    ----------
    depth_duration_mm : mapping of float to float
        Depth [mm] by duration [min] of one probability, at least the durations from
        the time step to the duration of the storm; a key may be the text of a number
        (a JSON object). The depth must not decrease with the duration.

    Raises
    ------
    InvalidParameterError
        If the curve is empty, a duration is not a number above 0 or given twice, a
        depth is not finite or negative, or the depth decreases with the duration
        (``details.option`` ``depth_duration_mm``, ``details.reason`` ``decreasing``
        with the two durations).

    Notes
    -----
    The peak rule is that of ATV-DVWK-A 118, Kap. 5.2.2.1, as quoted by Thewes (2005,
    p. 10): "Beginn des Regenintervalls mit der höchsten Niederschlagsintensität beim
    0,3-fachen der Modellregendauer ... auf ein Vielfaches von 5 Minuten abgerundet";
    DWD (Malitz 2009, slide 17) puts the 60-min peak at position 4 with the three next
    highest values to its left. Others differ by a block: the itwh software puts the
    15-min peak in block 2 (this class: block 1), and the Wrocław monograph
    (Kaźmierczak & Kotowski 2012, Tab. 4.6) ends the peak at D/3, a block later than
    0.3·D for D > 150 min.

    The total of the storm is h(D). :meth:`generate` takes ``total_mm`` as every
    hyetograph does, but refuses a total that differs from h(D) by more than
    :attr:`TOTAL_TOLERANCE_MM`; :meth:`depth_mm` gives h(D). The duration must be a
    whole number of time steps.

    References
    ----------
    .. [1] ATV-DVWK (2001). Arbeitsblatt ATV-DVWK-A 118, Kap. 5.2.2.1, as quoted by
           Thewes K. (2005). Diplomarbeit, FH Trier, p. 10.
    .. [2] Malitz G. (2009). Stark- und Extremniederschlag im Kurzzeitbereich.
           Deutscher Wetterdienst, slides 17-19.
    .. [3] Kaźmierczak B., Kotowski A. (2012). Weryfikacja przepustowości kanalizacji
           deszczowej w modelowaniu hydrodynamicznym. Oficyna Wydawnicza PWr,
           pp. 31-32.

    Examples
    --------
    The KOSTRA-DWD 2010R depths of Göllheim, T = 5 a, as the itwh printout lists them
    (to 0.1 mm; from its unrounded depths itwh prints 2.23, 3.00, 4.44, 9.51, 1.76,
    1.44, 1.23, 1.06, 0.93, 0.84, 0.76, 0.70 mm):

    >>> kostra = {5: 9.5, 10: 13.9, 15: 16.9, 20: 19.2, 30: 22.4, 45: 25.6, 60: 27.9}
    >>> hietogram = EulerIIHietogram(kostra)
    >>> result = hietogram.generate(
    ...     total_mm=27.9, duration_min=60.0, timestep_min=5.0
    ... )
    >>> result.intensities_mm.round(2).tolist()
    [2.3, 3.0, 4.4, 9.5, 1.76, 1.44, 1.22, 1.05, 0.93, 0.84, 0.76, 0.7]
    >>> float(result.intensities_mm[2:4].sum())  # the 10 min around the peak: h(10)
    13.9
    """

    TOTAL_TOLERANCE_MM: ClassVar[float] = 0.005
    """Largest difference between ``total_mm`` and h(D) that :meth:`generate` takes
    [mm]: half of the 0.01 mm the PMAXTP tables print."""

    def __init__(self, depth_duration_mm: DepthDurationCurve) -> None:
        """Read the depth-duration curve (see the class docstring)."""
        self._durations, self._depths = _curve_points(depth_duration_mm)

    @property
    def depth_duration_mm(self) -> dict[float, float]:
        """Dict of float to float: the curve, depth [mm] by duration [min]."""
        return dict(zip(self._durations.tolist(), self._depths.tolist(), strict=True))

    @staticmethod
    def peak_block(n_steps: int) -> int:
        """Return the block of the peak, counted from 0: ``floor(0.3 * n_steps)``.

        The peak interval starts at 0.3·D rounded down to a multiple of the step.

        Parameters
        ----------
        n_steps : int
            Number of blocks of the storm, ``duration / timestep``, >= 1.

        Returns
        -------
        int
            The index of the peak block.

        Examples
        --------
        >>> EulerIIHietogram.peak_block(12), EulerIIHietogram.peak_block(108)
        (3, 32)
        """
        return euler_ii_peak_block(n_steps)

    def _check_covers(self, first_min: float, last_min: float) -> None:
        """Refuse durations outside the curve: nothing is extrapolated."""
        shortest, longest = float(self._durations[0]), float(self._durations[-1])
        if first_min < shortest * (1 - _SAME_DURATION):
            raise _curve_error(
                f"the curve starts at {shortest:g} min, but the first block needs the "
                f"depth of {first_min:g} min",
                "not_covered",
                duration_min=first_min,
                durations_min=[shortest, longest],
            )
        if last_min > longest * (1 + _SAME_DURATION):
            raise _curve_error(
                f"the curve ends at {longest:g} min, but the storm needs the depth of "
                f"{last_min:g} min",
                "not_covered",
                duration_min=last_min,
                durations_min=[shortest, longest],
            )

    def depth_mm(self, duration_min: float) -> float:
        """Return the depth h(D) of the curve at a duration [mm].

        A duration between two points of the curve is interpolated linearly in ln D
        (Tier B ``depth_duration_interpolation``).

        Parameters
        ----------
        duration_min : float
            The duration [min], within the curve.

        Returns
        -------
        float
            The depth [mm]: the total of the Euler II storm of that duration.

        Raises
        ------
        InvalidParameterError
            If the duration is not a finite number above 0 or lies outside the curve
            (``details.reason`` ``not_covered``).

        Examples
        --------
        >>> curve = EulerIIHietogram({30: 22.4, 45: 25.6, 60: 27.9})
        >>> round(curve.depth_mm(40.0), 2)
        24.67
        """
        duration = _finite_positive("duration_min", duration_min)
        self._check_covers(duration, duration)
        at = np.array([duration], dtype=np.float64)
        return float(_interpolated_depths(self._durations, self._depths, at)[0])

    def generate(
        self,
        total_mm: float,
        duration_min: float,
        timestep_min: float = 5.0,
    ) -> HietogramResult:
        """
        Generate the Euler type II storm of the curve.

        Parameters
        ----------
        total_mm : float
            Total precipitation depth [mm]: h(``duration_min``) of the curve, to
            :attr:`TOTAL_TOLERANCE_MM` (:meth:`depth_mm` gives it).
        duration_min : float
            Duration of the storm [min], a whole number of time steps.
        timestep_min : float, optional
            Time step [min], by default 5.0; the curve must start at it or before.

        Returns
        -------
        HietogramResult
            The blocks; its ``total_mm`` is h(``duration_min``).

        Raises
        ------
        InvalidParameterError
            If a value is not a finite number above zero (``details.option`` names
            it), the step exceeds the duration, the duration is not a whole number of
            steps (``reason`` ``not_multiple``), the curve does not reach from the
            step to the duration (``reason`` ``not_covered``) or ``total_mm`` is not
            h(D) (``reason`` ``total_mismatch``, ``details.depth_mm`` h(D)).

        Examples
        --------
        >>> pmaxtp = {5: 21.82, 10: 25.68, 15: 28.22, 30: 33.23, 45: 36.58, 60: 39.16}
        >>> storm = EulerIIHietogram(pmaxtp).generate(39.16, 60.0)
        >>> int(storm.intensities_mm.argmax()), float(storm.intensities_mm.max())
        (3, 21.82)
        """
        duration, step, _ = _storm_steps(duration_min, timestep_min)
        self._check_covers(step, duration)
        storm = euler_ii_hyetograph(self._durations, self._depths, duration, step)
        depth = storm.total_mm
        total = _finite_positive("total_mm", total_mm)
        if not abs(total - depth) <= self.TOTAL_TOLERANCE_MM:
            raise InvalidParameterError(
                f"total_mm ({total:g} mm) is not the depth of the curve at "
                f"{duration:g} min, h = {depth:.6g} mm: an Euler II storm holds h(D)",
                details={
                    "option": "total_mm",
                    "reason": "total_mismatch",
                    "depth_mm": depth,
                    "duration_min": duration,
                },
                hint=f"Give total_mm {depth:.6g}, or scale the curve.",
            )
        return HietogramResult(
            times_min=storm.times_min,
            intensities_mm=storm.intensities_mm,
            total_mm=depth,
            duration_min=storm.duration_min,
            timestep_min=storm.timestep_min,
        )
