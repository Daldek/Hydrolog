"""Rating curve fitting and water level frequency analysis."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import curve_fit

from hydrolog.exceptions import InvalidParameterError

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class RatingCurveResult:
    """
    Result of rating curve fitting Q = a * (H - H0)^b.

    Attributes
    ----------
    a : float
        Scale coefficient [m³/s / m^b].
    b : float
        Power exponent [-].
    h0 : float
        Zero-flow water level (gauge zero) [cm or m, same units as input].
    r_squared : float
        Coefficient of determination R² [-].
    std_residuals : float
        Standard deviation of residuals [m³/s].
    n_points : int
        Number of data points used for final fit.
    n_outliers_removed : int
        Number of outlier observations removed before final fit.
    """

    a: float
    b: float
    h0: float
    r_squared: float
    std_residuals: float
    n_points: int
    n_outliers_removed: int


@dataclass
class WaterLevelZones:
    """
    Rybczyński water level zones.

    The hydrological year is divided into three zones based on the
    frequency distribution of water levels:

    - NTW (Niskie Tło Wodne / Low Background Water): below peak
    - STW (Średnie Tło Wodne / Medium Background Water): around peak
    - WTW (Wysokie Tło Wodne / High Background Water): above STW upper

    Attributes
    ----------
    ntw_upper : float
        Upper boundary of the NTW zone.
    stw_upper : float
        Upper boundary of the STW zone.
    ntw_range : tuple[float, float]
        (min_H, ntw_upper).
    stw_range : tuple[float, float]
        (ntw_upper, stw_upper).
    wtw_range : tuple[float, float]
        (stw_upper, max_H).
    """

    ntw_upper: float
    stw_upper: float
    ntw_range: tuple[float, float]
    stw_range: tuple[float, float]
    wtw_range: tuple[float, float]


@dataclass
class FrequencyDistributionResult:
    """
    Result of water level frequency distribution analysis.

    Attributes
    ----------
    bin_edges : NDArray[np.float64]
        Edges of histogram bins, length = n_bins + 1.
    bin_centers : NDArray[np.float64]
        Centre of each bin, length = n_bins.
    counts : NDArray[np.float64]
        Observation count per bin.
    frequency_pct : NDArray[np.float64]
        Relative frequency [%], sums to 100.
    cumulative_frequency_pct : NDArray[np.float64]
        Cumulative frequency from lowest to highest bin [%].
    duration_pct : NDArray[np.float64]
        Exceedance probability (duration curve) [%]:
        ``duration_pct[i]`` is the percentage of time H >= bin_edges[i].
    """

    bin_edges: NDArray[np.float64]
    bin_centers: NDArray[np.float64]
    counts: NDArray[np.float64]
    frequency_pct: NDArray[np.float64]
    cumulative_frequency_pct: NDArray[np.float64]
    duration_pct: NDArray[np.float64]


# ---------------------------------------------------------------------------
# Rating curve
# ---------------------------------------------------------------------------


class RatingCurve:
    """
    Fit a power-law rating curve Q = a * (H - H0)^b to paired measurements.

    Parameters
    ----------
    water_levels : NDArray[np.float64]
        Observed water levels H [cm or m].
    discharges : NDArray[np.float64]
        Corresponding discharge measurements Q [m³/s].

    Raises
    ------
    InvalidParameterError
        If arrays have mismatched lengths or fewer than 3 data points.

    Examples
    --------
    >>> import numpy as np
    >>> h = np.array([60.0, 80.0, 100.0, 130.0, 160.0])
    >>> q = np.array([25.0, 120.0, 280.0, 620.0, 1050.0])
    >>> rc = RatingCurve(h, q)
    >>> result = rc.fit(h0_initial=50.0)
    >>> result.r_squared  # doctest: +SKIP
    0.999...
    """

    def __init__(
        self,
        water_levels: NDArray[np.float64],
        discharges: NDArray[np.float64],
    ) -> None:
        water_levels = np.asarray(water_levels, dtype=np.float64)
        discharges = np.asarray(discharges, dtype=np.float64)

        if water_levels.shape != discharges.shape:
            raise InvalidParameterError(
                f"water_levels and discharges must have the same length, "
                f"got {len(water_levels)} and {len(discharges)}"
            )
        if len(water_levels) < 3:
            raise InvalidParameterError(
                f"At least 3 data points required for curve fitting, "
                f"got {len(water_levels)}"
            )

        self._h: NDArray[np.float64] = water_levels
        self._q: NDArray[np.float64] = discharges
        self._result: Optional[RatingCurveResult] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(
        self,
        h0_initial: float = 0.0,
        remove_outliers: bool = False,
        outlier_std: float = 2.0,
    ) -> RatingCurveResult:
        """
        Fit the rating curve Q = a * (H - H0)^b using non-linear least squares.

        Parameters
        ----------
        h0_initial : float, optional
            Initial guess for H0 (zero-flow level), by default 0.0.
        remove_outliers : bool, optional
            If True, remove points whose residuals exceed ``outlier_std``
            standard deviations before the final fit, by default False.
        outlier_std : float, optional
            Threshold in standard deviations for outlier removal,
            by default 2.0.

        Returns
        -------
        RatingCurveResult
            Fitted parameters and goodness-of-fit statistics.

        Raises
        ------
        InvalidParameterError
            If the curve cannot be fitted (e.g., all points are removed).
        """
        h = self._h.copy()
        q = self._q.copy()
        n_outliers_removed = 0

        # First fit (always performed)
        popt = self._fit_once(h, q, h0_initial)

        if remove_outliers:
            a, b, h0 = popt
            q_pred = _power_law(h, a, b, h0)
            residuals = q - q_pred
            std_res = np.std(residuals, ddof=1)
            mask = np.abs(residuals) <= outlier_std * std_res
            n_removed = int(np.sum(~mask))

            if n_removed > 0 and np.sum(mask) >= 3:
                h = h[mask]
                q = q[mask]
                n_outliers_removed = n_removed
                popt = self._fit_once(h, q, h0_initial)

        a_fit, b_fit, h0_fit = popt
        q_pred_final = _power_law(h, a_fit, b_fit, h0_fit)
        residuals_final = q - q_pred_final
        ss_res = float(np.sum(residuals_final**2))
        ss_tot = float(np.sum((q - np.mean(q)) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 0.0
        std_residuals = float(np.std(residuals_final, ddof=1))

        self._result = RatingCurveResult(
            a=float(a_fit),
            b=float(b_fit),
            h0=float(h0_fit),
            r_squared=float(r_squared),
            std_residuals=std_residuals,
            n_points=int(len(h)),
            n_outliers_removed=n_outliers_removed,
        )
        return self._result

    def predict(self, water_levels: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        Predict discharge for given water levels using the fitted curve.

        Parameters
        ----------
        water_levels : NDArray[np.float64]
            Water levels to predict discharge for.

        Returns
        -------
        NDArray[np.float64]
            Predicted discharge values [m³/s].

        Raises
        ------
        RuntimeError
            If ``fit()`` has not been called yet.
        """
        if self._result is None:
            raise RuntimeError("Call fit() before predict().")
        h = np.asarray(water_levels, dtype=np.float64)
        return _power_law(h, self._result.a, self._result.b, self._result.h0)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fit_once(
        h: NDArray[np.float64],
        q: NDArray[np.float64],
        h0_initial: float,
    ) -> NDArray[np.float64]:
        """Run curve_fit and return optimised parameters (a, b, h0)."""
        h_min = float(np.min(h))
        h0_upper = h_min - 1e-6  # H0 must stay below all H values

        try:
            popt, _ = curve_fit(
                _power_law,
                h,
                q,
                p0=[1.0, 1.5, h0_initial],
                bounds=(
                    [0.0, 0.0, -np.inf],
                    [np.inf, np.inf, h0_upper],
                ),
                maxfev=10_000,
            )
        except RuntimeError as exc:
            raise InvalidParameterError(
                f"Rating curve fitting did not converge: {exc}"
            ) from exc

        return popt


# ---------------------------------------------------------------------------
# Module-level helper (used inside RatingCurve._fit_once via curve_fit)
# ---------------------------------------------------------------------------


def _power_law(
    h: NDArray[np.float64],
    a: float,
    b: float,
    h0: float,
) -> NDArray[np.float64]:
    """
    Power-law rating curve Q = a * (H - H0)^b.

    Parameters
    ----------
    h : NDArray[np.float64]
        Water levels.
    a : float
        Scale coefficient.
    b : float
        Exponent.
    h0 : float
        Zero-flow level.

    Returns
    -------
    NDArray[np.float64]
        Discharge values.
    """
    diff = np.asarray(h, dtype=np.float64) - h0
    # Guard against negative bases (physically meaningless)
    diff = np.maximum(diff, 0.0)
    return a * diff**b


# ---------------------------------------------------------------------------
# Water level frequency analysis
# ---------------------------------------------------------------------------


class WaterLevelFrequency:
    """
    Frequency and duration analysis of water level time series.

    Builds a histogram of water levels and derives:
    - Relative frequency [%]
    - Cumulative frequency [%]
    - Duration (exceedance) curve [%]
    - Rybczyński water level zones (NTW / STW / WTW)

    Parameters
    ----------
    water_levels : NDArray[np.float64]
        Time series of water level observations [cm or m].
    bin_width : float, optional
        Width of histogram bins in the same units as water_levels,
        by default 10.0.

    Raises
    ------
    InvalidParameterError
        If ``water_levels`` is empty or ``bin_width`` is not positive.

    Examples
    --------
    >>> import numpy as np
    >>> rng = np.random.default_rng(0)
    >>> levels = rng.uniform(100, 300, size=500)
    >>> wlf = WaterLevelFrequency(levels, bin_width=20.0)
    >>> result = wlf.frequency_distribution()
    >>> round(result.frequency_pct.sum(), 1)
    100.0
    """

    def __init__(
        self,
        water_levels: NDArray[np.float64],
        bin_width: float = 10.0,
    ) -> None:
        water_levels = np.asarray(water_levels, dtype=np.float64)

        if water_levels.size == 0:
            raise InvalidParameterError("water_levels must not be empty.")
        if bin_width <= 0.0:
            raise InvalidParameterError(f"bin_width must be positive, got {bin_width}")

        self._h: NDArray[np.float64] = water_levels
        self._bin_width: float = float(bin_width)
        self._freq_result: Optional[FrequencyDistributionResult] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def frequency_distribution(self) -> FrequencyDistributionResult:
        """
        Compute histogram-based frequency and duration distribution.

        Returns
        -------
        FrequencyDistributionResult
            Bin edges, centres, counts, frequency [%], cumulative
            frequency [%], and duration (exceedance) curve [%].
        """
        h_min = math.floor(float(np.min(self._h)))
        h_max = math.ceil(float(np.max(self._h)))

        # Extend upper edge so the maximum value falls inside the last bin
        bin_edges = np.arange(h_min, h_max + self._bin_width, self._bin_width)
        # Ensure the last edge exceeds the maximum observation
        while bin_edges[-1] <= h_max:
            bin_edges = np.append(bin_edges, bin_edges[-1] + self._bin_width)

        counts, _ = np.histogram(self._h, bins=bin_edges)
        counts = counts.astype(np.float64)
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

        total = float(counts.sum())
        frequency_pct = counts / total * 100.0 if total > 0.0 else counts.copy()
        cumulative_frequency_pct = np.cumsum(frequency_pct)

        # Duration (exceedance): fraction of time H >= lower edge of bin i
        # = 100 - cumulative up to (but not including) bin i
        duration_pct = 100.0 - np.concatenate([[0.0], cumulative_frequency_pct[:-1]])

        result = FrequencyDistributionResult(
            bin_edges=bin_edges,
            bin_centers=bin_centers,
            counts=counts,
            frequency_pct=frequency_pct,
            cumulative_frequency_pct=cumulative_frequency_pct,
            duration_pct=duration_pct,
        )
        self._freq_result = result
        return result

    def rybczynski_zones(self) -> WaterLevelZones:
        """
        Delimit Rybczyński water level zones from frequency distribution.

        Zone definitions
        ----------------
        NTW (Niskie Tło Wodne)
            Low background water: water levels below the modal (most
            frequent) class.
        STW (Średnie Tło Wodne)
            Medium background water: water levels from modal class up to
            the level where the duration curve drops below 50 %.
        WTW (Wysokie Tło Wodne)
            High background water: remaining (high) water levels.

        Returns
        -------
        WaterLevelZones
            Boundary values and ranges for each zone.
        """
        if self._freq_result is None:
            self.frequency_distribution()

        result = self._freq_result  # type: ignore[assignment]

        h_min = float(result.bin_edges[0])
        h_max = float(result.bin_edges[-1])

        # NTW upper boundary: lower edge of the bin with maximum frequency
        peak_idx = int(np.argmax(result.frequency_pct))
        ntw_upper = float(result.bin_centers[peak_idx])

        # STW upper boundary: first bin where duration drops below 50 %
        below_50 = np.where(result.duration_pct < 50.0)[0]
        if len(below_50) > 0:
            stw_idx = int(below_50[0])
        else:
            # Fallback: use the bin after the peak
            stw_idx = min(peak_idx + 1, len(result.bin_centers) - 1)

        stw_upper = float(result.bin_centers[stw_idx])

        # Ensure strict ordering: ntw_upper < stw_upper
        if stw_upper <= ntw_upper:
            # Push stw_upper one bin beyond ntw
            fallback_idx = min(peak_idx + 1, len(result.bin_centers) - 1)
            stw_upper = float(result.bin_centers[fallback_idx])
            if stw_upper <= ntw_upper:
                stw_upper = ntw_upper + self._bin_width

        return WaterLevelZones(
            ntw_upper=ntw_upper,
            stw_upper=stw_upper,
            ntw_range=(h_min, ntw_upper),
            stw_range=(ntw_upper, stw_upper),
            wtw_range=(stw_upper, h_max),
        )
