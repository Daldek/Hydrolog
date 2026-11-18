"""Hyetograph generation for temporal rainfall distribution.

Every generator cuts the storm into ``n = D / Δt`` whole steps of the time step Δt and
puts the whole total into them, so the duration D must be a whole number of steps
(``details.reason`` ``not_multiple`` otherwise; ADR-0046): the storm then lasts D and
its mean intensity is the total over D.
"""

import itertools
import math
import numbers
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from numpy.typing import NDArray
from scipy.special import betainc

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError

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


class BlockHietogram(Hietogram):
    """
    Block (uniform) hyetograph with constant intensity.

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
        total, duration, step, n_steps = _storm(total_mm, duration_min, timestep_min)
        return HietogramResult(
            times_min=_step_ends(n_steps, step),
            intensities_mm=np.full(n_steps, total / n_steps, dtype=np.float64),
            total_mm=total,
            duration_min=duration,
            timestep_min=step,
        )


class TriangularHietogram(Hietogram):
    """
    Triangular hyetograph of Yen and Chow (1980): the block integrals of a triangle.

    The intensity rises linearly from zero at t = 0 to its peak ``h = 2P/D`` at
    ``t_a = r·D`` (``r`` = ``peak_position``, the storm advancement coefficient) and
    falls linearly to zero at t = D. Each step holds the depth that falls in it, the
    difference of the cumulative depth at its ends:

    ``F(t) = P t² / (D t_a)`` for ``t <= t_a``,
    ``F(t) = P [1 - (D - t)² / (D (D - t_a))]`` for ``t > t_a``,

    so the steps hold exactly P whatever their number, and with r = 0.5 and an even
    number of steps the two middle steps are equal.

    Parameters
    ----------
    peak_position : float, optional
        The storm advancement coefficient r: the time of the peak as a fraction of the
        duration, 0 < r < 1, by default 0.5 (peak at the centre). Chow et al. (1988,
        Table 14.3.2) list 0.294 to 0.480 for US, Indian and Canadian cities.

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
        total, duration, step, n_steps = _storm(total_mm, duration_min, timestep_min)
        peak = self.peak_position
        # cumulative share of the triangle at the step ends, in relative time u = t/D
        ends = np.arange(n_steps + 1, dtype=np.float64) / n_steps
        cumulative = np.where(
            ends <= peak, ends**2 / peak, 1.0 - (1.0 - ends) ** 2 / (1.0 - peak)
        )
        return HietogramResult(
            times_min=_step_ends(n_steps, step),
            intensities_mm=total * np.diff(cumulative),
            total_mm=total,
            duration_min=duration,
            timestep_min=step,
        )


class BetaHietogram(Hietogram):
    """
    Beta distribution hyetograph: the block integrals of a Beta density.

    The intensity over the relative time ``u = t/D`` follows the Beta density
    ``f(u) = u^(α-1) (1-u)^(β-1) / B(α, β)`` (KZGW 2017, eq. 2.20, after Węglarczyk
    1993). Each step holds the share of the total that the density gives it, the
    difference of the regularised incomplete Beta function ``I_u(α, β)`` (the Beta
    distribution function) at its ends:

    ``P_i = P [I_(i/n)(α, β) - I_((i-1)/n)(α, β)]``,

    so the steps hold exactly P for every α, β > 0, also where the density is
    infinite (α < 1 or β < 1).

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
        total, duration, step, n_steps = _storm(total_mm, duration_min, timestep_min)
        ends = np.arange(n_steps + 1, dtype=np.float64) / n_steps
        cumulative = betainc(self.alpha, self.beta, ends)
        return HietogramResult(
            times_min=_step_ends(n_steps, step),
            intensities_mm=total * np.diff(cumulative),
            total_mm=total,
            duration_min=duration,
            timestep_min=step,
        )


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
    formula. With ``n = D / Δt`` blocks of the time step Δt, the increments are
    ``Δh_j = h(jΔt) - h((j-1)Δt)``, ``j = 1..n`` (``h(0) = 0``). The peak interval
    starts at 0.3·D rounded down to a multiple of Δt (the block ``k = floor(0.3 n)``,
    counted from 0) and holds ``Δh_1``; ``Δh_2 .. Δh_(k+1)`` fill the time before it
    back to t = 0, ``Δh_(k+2) .. Δh_n`` follow the peak. The increments of a curve of
    intensities that fall with the duration (an IDF curve) decrease, so the largest is
    at the peak, the next larger ones before it in ascending order and the rest after
    it in descending order, as A 118 and DWD describe the storm; and every ``m``
    blocks around the peak (blocks ``k-m+1..k`` while ``m <= k+1``, else ``0..m-1``)
    hold ``h(mΔt)``, the depth of the duration ``mΔt``, whatever the curve: the whole
    storm holds h(D). Where the increments of a curve do not decrease (a coarse table
    interpolated between its points), they keep their order by duration and are not
    sorted, as the itwh software does (its KOSTRA-DWD 2020 printout of Aurich).

    Depths at durations between the points of the curve are interpolated linearly in
    ln D (this reproduces the printouts of the itwh KOSTRA-DWD 2010R software to 0.07
    mm; the DWA MDMS tool interpolates linearly in D). The curve must reach from the
    time step to the duration: nothing is extrapolated.

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
        return (3 * n_steps) // 10

    def _depths_at(self, durations_min: NDArray[np.float64]) -> NDArray[np.float64]:
        """Return h at ``durations_min``, which lie within the curve."""
        durations, depths = self._durations, self._depths
        found = np.searchsorted(durations, durations_min)
        at = np.clip(found, 0, len(durations) - 1)
        before = np.clip(found - 1, 0, len(durations) - 1)
        snapped = np.where(
            np.abs(durations[at] - durations_min) <= _SAME_DURATION * durations[at],
            durations[at],
            np.where(
                np.abs(durations[before] - durations_min)
                <= _SAME_DURATION * durations[before],
                durations[before],
                durations_min,
            ),
        )
        return np.interp(np.log(snapped), np.log(durations), depths)

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

        A duration between two points of the curve is interpolated linearly in ln D.

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
        return float(self._depths_at(np.array([duration], dtype=np.float64))[0])

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
        duration, step, n_steps = _storm_steps(duration_min, timestep_min)
        self._check_covers(step, duration)
        times = _step_ends(n_steps, step)
        cumulative = self._depths_at(times)
        depth = float(cumulative[-1])
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
        increments = np.diff(cumulative, prepend=0.0)
        peak = self.peak_block(n_steps)
        # Δh_1 at the peak, Δh_2..Δh_(k+1) back to t = 0, the rest after the peak
        blocks = np.concatenate((increments[peak::-1], increments[peak + 1 :]))
        return HietogramResult(
            times_min=times,
            intensities_mm=blocks,
            total_mm=depth,
            duration_min=duration,
            timestep_min=step,
        )
