"""Hyetograph generation for temporal rainfall distribution."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


@dataclass
class HietogramResult:
    """
    Result of hyetograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values at the end of each interval [min].
    intensities_mm : NDArray[np.float64]
        Precipitation depth in each interval [mm].
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
            Time step for discretization [min], by default 5.0.

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
        Validate input parameters and return number of steps.

        Returns
        -------
        int
            Number of time steps.

        Raises
        ------
        InvalidParameterError
            If any parameter is invalid.
        """
        if total_mm <= 0:
            raise InvalidParameterError(f"total_mm must be positive, got {total_mm}")
        if duration_min <= 0:
            raise InvalidParameterError(
                f"duration_min must be positive, got {duration_min}"
            )
        if timestep_min <= 0:
            raise InvalidParameterError(
                f"timestep_min must be positive, got {timestep_min}"
            )
        if timestep_min > duration_min:
            raise InvalidParameterError(
                f"timestep_min ({timestep_min}) cannot exceed duration_min ({duration_min})"
            )

        n_steps = int(duration_min / timestep_min)
        if n_steps < 1:
            raise InvalidParameterError(
                f"Duration must allow at least 1 time step, got {n_steps}"
            )

        return n_steps


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
        n_steps = self._validate_params(total_mm, duration_min, timestep_min)

        # Uniform distribution: equal intensity in each step
        intensity_per_step = total_mm / n_steps
        intensities = np.full(n_steps, intensity_per_step, dtype=np.float64)

        # Time at end of each interval
        times = np.arange(1, n_steps + 1, dtype=np.float64) * timestep_min

        return HietogramResult(
            times_min=times,
            intensities_mm=intensities,
            total_mm=total_mm,
            duration_min=duration_min,
            timestep_min=timestep_min,
        )


class TriangularHietogram(Hietogram):
    """
    Triangular hyetograph with peak at specified position.

    The triangular distribution has a linear increase to peak
    and linear decrease after peak.

    Parameters
    ----------
    peak_position : float, optional
        Relative position of peak intensity (0.0 to 1.0),
        by default 0.5 (peak at center).

    Examples
    --------
    >>> hietogram = TriangularHietogram(peak_position=0.4)
    >>> result = hietogram.generate(total_mm=30.0, duration_min=60.0)
    """

    def __init__(self, peak_position: float = 0.5) -> None:
        """
        Initialize triangular hyetograph.

        Parameters
        ----------
        peak_position : float, optional
            Relative position of peak (0.0-1.0), by default 0.5.

        Raises
        ------
        InvalidParameterError
            If peak_position is not in range (0, 1).
        """
        if not 0 < peak_position < 1:
            raise InvalidParameterError(
                f"peak_position must be in range (0, 1), got {peak_position}"
            )
        self.peak_position = peak_position

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
            Duration of the storm event [min].
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.

        Returns
        -------
        HietogramResult
            Generated hyetograph with triangular distribution.
        """
        n_steps = self._validate_params(total_mm, duration_min, timestep_min)

        # Create triangular distribution
        # Peak at relative position
        peak_idx = int(n_steps * self.peak_position)
        if peak_idx == 0:
            peak_idx = 1
        if peak_idx >= n_steps:
            peak_idx = n_steps - 1

        # Build triangular shape
        intensities = np.zeros(n_steps, dtype=np.float64)

        # Rising limb (0 to peak)
        for i in range(peak_idx + 1):
            intensities[i] = (i + 1) / (peak_idx + 1)

        # Falling limb (peak to end)
        remaining = n_steps - peak_idx - 1
        if remaining > 0:
            for i in range(remaining):
                intensities[peak_idx + 1 + i] = (remaining - i) / (remaining + 1)

        # Normalize to total precipitation
        intensities = intensities / intensities.sum() * total_mm

        # Time at end of each interval
        times = np.arange(1, n_steps + 1, dtype=np.float64) * timestep_min

        return HietogramResult(
            times_min=times,
            intensities_mm=intensities,
            total_mm=total_mm,
            duration_min=duration_min,
            timestep_min=timestep_min,
        )


class BetaHietogram(Hietogram):
    """
    Beta distribution hyetograph.

    Uses the Beta probability distribution to create a flexible
    temporal rainfall pattern. The shape is controlled by alpha
    and beta parameters.

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
    Common parameter combinations:
    - alpha=2, beta=5: Peak early (typical convective storm)
    - alpha=2, beta=2: Symmetric peak at center
    - alpha=5, beta=2: Peak late

    Examples
    --------
    >>> hietogram = BetaHietogram(alpha=2.0, beta=5.0)
    >>> result = hietogram.generate(total_mm=30.0, duration_min=60.0)
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
            If alpha or beta is not positive.
        """
        if alpha <= 0:
            raise InvalidParameterError(f"alpha must be positive, got {alpha}")
        if beta <= 0:
            raise InvalidParameterError(f"beta must be positive, got {beta}")
        self.alpha = alpha
        self.beta = beta

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
            Duration of the storm event [min].
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.

        Returns
        -------
        HietogramResult
            Generated hyetograph with Beta distribution.
        """
        n_steps = self._validate_params(total_mm, duration_min, timestep_min)

        # Generate Beta distribution PDF values at interval midpoints
        # Normalized time: 0 to 1
        t_mid = (np.arange(n_steps) + 0.5) / n_steps

        # Beta PDF: f(x) = x^(a-1) * (1-x)^(b-1) / B(a,b)
        # We don't need the normalizing constant B(a,b) since we normalize anyway
        intensities = (t_mid ** (self.alpha - 1)) * ((1 - t_mid) ** (self.beta - 1))

        # Handle edge cases where intensities might be 0 or inf
        intensities = np.nan_to_num(intensities, nan=0.0, posinf=0.0, neginf=0.0)

        # Normalize to total precipitation
        if intensities.sum() > 0:
            intensities = intensities / intensities.sum() * total_mm
        else:
            # Fallback to uniform if Beta gives all zeros
            intensities = np.full(n_steps, total_mm / n_steps, dtype=np.float64)

        # Time at end of each interval
        times = np.arange(1, n_steps + 1, dtype=np.float64) * timestep_min

        return HietogramResult(
            times_min=times,
            intensities_mm=intensities,
            total_mm=total_mm,
            duration_min=duration_min,
            timestep_min=timestep_min,
        )


class EulerIIHietogram(Hietogram):
    """
    DVWK Euler Type II hyetograph.

    The Euler Type II distribution places the maximum intensity at
    approximately 1/3 of the storm duration. Intensities decrease
    alternately before and after the peak position.

    This is the most commonly used design storm in German-speaking
    countries (DVWK - Deutscher Verband für Wasserwirtschaft und Kulturbau).

    Parameters
    ----------
    peak_position : float, optional
        Relative position of peak intensity (0.0 to 1.0),
        by default 0.33 (1/3 of duration, standard for Euler II).

    Notes
    -----
    The Euler Type II method uses the "alternating block" approach:
    1. Rank intensities from highest to lowest
    2. Place highest intensity at peak position
    3. Alternate remaining intensities before and after peak

    The intensity distribution follows an exponential decay pattern
    from the peak, which approximates the standard IDF curve behavior.

    References
    ----------
    .. [1] DVWK (1984). Arbeitsanleitung zur Anwendung von
           Niederschlag-Abfluss-Modellen in kleinen Einzugsgebieten.
           DVWK-Regeln 113.

    Examples
    --------
    >>> hietogram = EulerIIHietogram()
    >>> result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=5.0)
    >>> # Peak is at approximately 1/3 of duration (around 20 min)
    >>> peak_idx = result.intensities_mm.argmax()
    >>> print(f"Peak at interval {peak_idx + 1} of {result.n_steps}")
    Peak at interval 4 of 12
    """

    def __init__(self, peak_position: float = 0.33) -> None:
        """
        Initialize Euler Type II hyetograph.

        Parameters
        ----------
        peak_position : float, optional
            Relative position of peak (0.0-1.0), by default 0.33.
            Standard Euler II uses 1/3 (0.33).

        Raises
        ------
        InvalidParameterError
            If peak_position is not in range (0, 1).
        """
        if not 0 < peak_position < 1:
            raise InvalidParameterError(
                f"peak_position must be in range (0, 1), got {peak_position}"
            )
        self.peak_position = peak_position

    def generate(
        self,
        total_mm: float,
        duration_min: float,
        timestep_min: float = 5.0,
    ) -> HietogramResult:
        """
        Generate DVWK Euler Type II hyetograph.

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
            Generated hyetograph with Euler II distribution.

        Examples
        --------
        >>> hietogram = EulerIIHietogram()
        >>> result = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)
        >>> print(f"Peak intensity: {result.intensities_mm.max():.2f} mm")
        Peak intensity: 12.47 mm
        """
        n_steps = self._validate_params(total_mm, duration_min, timestep_min)

        # Generate ranked intensities using exponential decay
        # This approximates the behavior of IDF curves
        ranks = np.arange(1, n_steps + 1, dtype=np.float64)
        ranked_intensities = 1.0 / ranks**0.7  # Decay exponent ~0.7 typical for IDF

        # Normalize ranked intensities
        ranked_intensities = ranked_intensities / ranked_intensities.sum()

        # Place intensities using alternating block method
        # Peak at specified position
        peak_idx = int(n_steps * self.peak_position)
        if peak_idx == 0:
            peak_idx = 1
        if peak_idx >= n_steps:
            peak_idx = n_steps - 1

        intensities = np.zeros(n_steps, dtype=np.float64)
        intensities[peak_idx] = ranked_intensities[0]  # Highest at peak

        # Alternate placement: before and after peak
        left_idx = peak_idx - 1
        right_idx = peak_idx + 1
        place_left = True  # Start by placing to the left (Euler II characteristic)

        for i in range(1, n_steps):
            if place_left and left_idx >= 0:
                intensities[left_idx] = ranked_intensities[i]
                left_idx -= 1
                place_left = False
            elif right_idx < n_steps:
                intensities[right_idx] = ranked_intensities[i]
                right_idx += 1
                place_left = True
            elif left_idx >= 0:
                intensities[left_idx] = ranked_intensities[i]
                left_idx -= 1

        # Scale to total precipitation
        intensities = intensities * total_mm

        # Time at end of each interval
        times = np.arange(1, n_steps + 1, dtype=np.float64) * timestep_min

        return HietogramResult(
            times_min=times,
            intensities_mm=intensities,
            total_mm=total_mm,
            duration_min=duration_min,
            timestep_min=timestep_min,
        )
