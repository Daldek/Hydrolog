"""Low-flow frequency analysis and drought sequence detection.

Implements Fisher-Tippett (Gumbel minimum) distribution fitting to annual
minimum series, empirical plotting positions for low-flow frequency, and
vectorised detection of drought sequences based on threshold exceedance.

References
----------
WMO No. 1029 (2009): Manual on Low-flow Estimation and Prediction.
Tallaksen & van Lanen (Eds., 2004): Hydrological Drought — Processes and
    Estimation Methods for Streamflow and Groundwater. Elsevier.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray
from scipy.stats import genextreme, kstest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._hydrological_year import hydrological_year
from hydrolog.statistics._types import EmpiricalFrequency, compute_plotting_positions

_DEFAULT_RETURN_PERIODS = np.array(
    [2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0]
)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class LowFlowFrequencyResult:
    """Result of fitting Fisher-Tippett distribution to annual minima.

    Attributes
    ----------
    distribution_name : str
        Always ``"fisher_tippett"``.
    parameters : dict[str, float]
        Fitted distribution parameters: ``shape``, ``loc``, ``scale``.
    return_periods : NDArray[np.float64]
        Return periods *T* (years) — in low-flow context these are
        *non-exceedance* return periods (drought recurrence intervals).
    quantiles : NDArray[np.float64]
        Quantile estimates (minimum flow level) for each return period.
    non_exceedance_probabilities : NDArray[np.float64]
        Non-exceedance probability 1/*T* for each return period.
    ks_statistic : float
        Kolmogorov-Smirnov test statistic.
    ks_p_value : float
        Kolmogorov-Smirnov *p*-value.
    ks_valid : bool
        Always ``False`` — parameters estimated from the same data.
    """

    distribution_name: str
    parameters: dict[str, float]
    return_periods: NDArray[np.float64]
    quantiles: NDArray[np.float64]
    non_exceedance_probabilities: NDArray[np.float64]
    ks_statistic: float
    ks_p_value: float
    ks_valid: bool


@dataclass
class LowFlowSequence:
    """A single drought (low-flow) sequence.

    Attributes
    ----------
    start_index : int
        Index in the original daily flow array where the sequence begins.
    end_index : int
        Index in the original daily flow array where the sequence ends
        (inclusive).
    duration_days : int
        Total length of the sequence in days.
    min_flow : float
        Minimum flow observed during the sequence.
    mean_flow : float
        Mean flow observed during the sequence.
    deficit_volume : float
        Cumulative deficit: ``sum(threshold - Q[i])`` for all days where
        ``Q[i] < threshold`` within the sequence window.
    """

    start_index: int
    end_index: int
    duration_days: int
    min_flow: float
    mean_flow: float
    deficit_volume: float


@dataclass
class LowFlowAnalysisResult:
    """Summary of drought sequence detection.

    Attributes
    ----------
    threshold : float
        Threshold flow value used for event identification.
    sequences : list[LowFlowSequence]
        Detected drought sequences.
    total_deficit : float
        Sum of deficit volumes across all sequences.
    max_duration_days : int
        Duration of the longest individual sequence.
    n_events : int
        Total number of identified drought events.
    """

    threshold: float
    sequences: list[LowFlowSequence] = field(default_factory=list)
    total_deficit: float = 0.0
    max_duration_days: int = 0
    n_events: int = 0


# ---------------------------------------------------------------------------
# Main analysis class
# ---------------------------------------------------------------------------


class LowFlowAnalysis:
    """Low-flow frequency and drought sequence analysis.

    Parameters
    ----------
    daily_flows : NDArray[np.float64]
        Daily streamflow values (m³/s or any consistent unit).
    dates : NDArray[np.datetime64]
        Corresponding dates (dtype ``datetime64[D]``).
    return_periods : NDArray[np.float64] or None, optional
        Return periods for quantile estimation.  Defaults to
        ``[2, 5, 10, 20, 50, 100, 500, 1000]``.

    Raises
    ------
    InvalidParameterError
        If *daily_flows* is empty or lengths of *daily_flows* and *dates*
        do not match.

    Examples
    --------
    >>> import numpy as np
    >>> from hydrolog.statistics.low_flows import LowFlowAnalysis
    >>> rng = np.random.default_rng(0)
    >>> dates = np.arange(
    ...     np.datetime64("2010-11-01"),
    ...     np.datetime64("2020-10-31"),
    ...     dtype="datetime64[D]",
    ... )
    >>> flows = rng.uniform(1, 100, size=len(dates))
    >>> lfa = LowFlowAnalysis(flows, dates)  # doctest: +SKIP
    """

    def __init__(
        self,
        daily_flows: NDArray[np.float64],
        dates: NDArray,
        return_periods: NDArray[np.float64] | None = None,
    ) -> None:
        daily_flows = np.asarray(daily_flows, dtype=np.float64)
        dates = np.asarray(dates)

        if len(daily_flows) == 0 or len(dates) == 0:
            raise InvalidParameterError(
                "daily_flows and dates must not be empty."
            )
        if len(daily_flows) != len(dates):
            raise InvalidParameterError(
                f"daily_flows (length {len(daily_flows)}) and dates "
                f"(length {len(dates)}) must have the same length."
            )

        self._flows = daily_flows
        self._dates = dates
        self._return_periods = (
            np.asarray(return_periods, dtype=np.float64)
            if return_periods is not None
            else _DEFAULT_RETURN_PERIODS.copy()
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def annual_minima(self) -> NDArray[np.float64]:
        """Extract annual minimum flows (one per hydrological year).

        Uses the Polish hydrological year (Nov 1 – Oct 31).

        Returns
        -------
        NDArray[np.float64]
            Array of annual minima, one value per year present in the
            data, sorted by hydrological year.

        Warns
        -----
        UserWarning
            If fewer than 10 years are available.
        """
        hydro_years = hydrological_year(self._dates)
        unique_years = np.unique(hydro_years)

        if len(unique_years) < 10:
            warnings.warn(
                f"Only {len(unique_years)} year(s) of data available; "
                "low-flow frequency estimates may be unreliable.",
                UserWarning,
                stacklevel=2,
            )

        minima = np.array(
            [self._flows[hydro_years == yr].min() for yr in unique_years],
            dtype=np.float64,
        )
        return minima

    def fit_fisher_tippett(self) -> LowFlowFrequencyResult:
        """Fit Fisher-Tippett (Gumbel minimum / GEV) distribution to annual minima.

        For low-flow analysis the distribution is fitted to annual minima and
        quantiles are computed directly from non-exceedance probabilities
        ``p = 1/T``, giving the flow level expected to be equalled or
        *not exceeded* once in *T* years.

        Returns
        -------
        LowFlowFrequencyResult
            Fitted result with quantile estimates.

        Notes
        -----
        SciPy's ``genextreme`` parameterises GEV with ``c = -ξ``.  For the
        Gumbel minimum (Fisher-Tippett Type I minimum), ``c ≈ 0``.  The
        fitted shape parameter is retained in the result.
        """
        minima = self.annual_minima()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            c, loc, scale = genextreme.fit(minima)

        params: dict[str, float] = {
            "shape": float(c),
            "loc": float(loc),
            "scale": float(scale),
        }

        # Non-exceedance probability p = 1/T  (low flows: interested in
        # values *not exceeded* with probability p).
        p = 1.0 / self._return_periods
        quantiles = genextreme.ppf(p, c, loc=loc, scale=scale)

        # K-S test (informational; invalid when parameters estimated from data)
        cdf_func = lambda x: genextreme.cdf(x, c, loc=loc, scale=scale)  # noqa: E731
        ks_stat, ks_pval = kstest(minima, cdf_func)

        return LowFlowFrequencyResult(
            distribution_name="fisher_tippett",
            parameters=params,
            return_periods=self._return_periods.copy(),
            quantiles=np.asarray(quantiles, dtype=np.float64),
            non_exceedance_probabilities=p,
            ks_statistic=float(ks_stat),
            ks_p_value=float(ks_pval),
            ks_valid=False,
        )

    def empirical_frequency(
        self, method: str = "weibull"
    ) -> EmpiricalFrequency:
        """Compute empirical plotting positions for annual minima.

        Parameters
        ----------
        method : str, optional
            Plotting position method, by default ``"weibull"``.
            Options: ``"weibull"``, ``"hazen"``, ``"cunnane"``.

        Returns
        -------
        EmpiricalFrequency
            Annual minima sorted in descending order with exceedance
            probabilities and return periods.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            minima = self.annual_minima()

        return compute_plotting_positions(minima, method=method)

    def detect_sequences(
        self,
        threshold: float,
        min_duration_days: int = 5,
        max_gap_days: int = 4,
    ) -> LowFlowAnalysisResult:
        """Detect drought (low-flow) sequences using threshold level method.

        A drought event is defined as a continuous period where streamflow
        falls below *threshold*.  Short gaps between two sub-threshold runs
        are bridged if the gap length is strictly less than *max_gap_days*
        (i.e. gap < max_gap_days).  After merging, only sequences whose
        total duration meets or exceeds *min_duration_days* are retained.

        Parameters
        ----------
        threshold : float
            Flow threshold (same unit as *daily_flows*).
        min_duration_days : int, optional
            Minimum event duration to report, by default 5 days.
        max_gap_days : int, optional
            Maximum gap length (exclusive) that triggers merging of two
            adjacent events, by default 4 days.

        Returns
        -------
        LowFlowAnalysisResult
            Detected sequences with summary statistics.

        Notes
        -----
        Deficit volume is computed as::

            deficit = Σ max(threshold − Q[i], 0)  for i in sequence window

        This includes gap days (which contribute zero deficit if Q > threshold)
        when two runs are merged.
        """
        below: NDArray[np.bool_] = self._flows < threshold

        # ------------------------------------------------------------------
        # 1.  Find all contiguous runs of True (below-threshold days)
        #     using np.diff to locate transition points.
        # ------------------------------------------------------------------
        # Pad with False so that runs touching the boundaries are detected.
        padded = np.concatenate(([False], below, [False]))
        diff = np.diff(padded.astype(np.int8))

        # Indices where a run starts (0→1) and ends (1→0) in the *original*
        # (unpadded) array.
        starts: NDArray[np.intp] = np.where(diff == 1)[0]   # already offset-corrected
        ends: NDArray[np.intp] = np.where(diff == -1)[0] - 1  # inclusive end

        if len(starts) == 0:
            return LowFlowAnalysisResult(threshold=threshold)

        # ------------------------------------------------------------------
        # 2.  Merge runs separated by a gap < max_gap_days.
        # ------------------------------------------------------------------
        merged_starts: list[int] = [int(starts[0])]
        merged_ends: list[int] = [int(ends[0])]

        for i in range(1, len(starts)):
            gap = int(starts[i]) - int(merged_ends[-1]) - 1  # number of gap days
            if gap < max_gap_days:
                # Extend the current merged event to cover this run
                merged_ends[-1] = int(ends[i])
            else:
                merged_starts.append(int(starts[i]))
                merged_ends.append(int(ends[i]))

        # ------------------------------------------------------------------
        # 3.  Build LowFlowSequence objects; filter by min_duration_days.
        # ------------------------------------------------------------------
        sequences: list[LowFlowSequence] = []

        for s, e in zip(merged_starts, merged_ends):
            duration = e - s + 1
            if duration < min_duration_days:
                continue

            segment = self._flows[s : e + 1]
            deficit = float(np.sum(np.maximum(threshold - segment, 0.0)))

            sequences.append(
                LowFlowSequence(
                    start_index=s,
                    end_index=e,
                    duration_days=duration,
                    min_flow=float(segment.min()),
                    mean_flow=float(segment.mean()),
                    deficit_volume=deficit,
                )
            )

        total_deficit = sum(seq.deficit_volume for seq in sequences)
        max_duration = max((seq.duration_days for seq in sequences), default=0)

        return LowFlowAnalysisResult(
            threshold=threshold,
            sequences=sequences,
            total_deficit=total_deficit,
            max_duration_days=max_duration,
            n_events=len(sequences),
        )
