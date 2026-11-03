"""Low-flow frequency analysis and drought sequence detection.

Implements the Fisher-Tippett distribution of *smallest* values (the generalized
extreme value distribution for minima; Gumbel minimum and the three-parameter
Weibull distribution are its special cases) fitted to annual minimum series,
empirical plotting positions for low-flow frequency, and vectorised detection of
drought sequences based on threshold exceedance.

The annual minima are those of the *complete* Polish hydrological years (1 November
- 31 October) of the daily series; a year in which a day has no value is skipped
with a warning. The return periods of low flows are non-exceedance return periods
(a flow equalled or undercut once in *T* years): the fitted quantiles
(:class:`LowFlowFrequencyResult`) and the empirical plotting positions
(:class:`~hydrolog.statistics.LowFlowEmpiricalFrequency`) follow the same
convention.

References
----------
Fisher, R. A. & Tippett, L. H. C. (1928): Limiting forms of the frequency
    distribution of the largest or smallest member of a sample. Proc. Cambridge
    Philos. Soc. 24(2), 180-190.
Gumbel, E. J. (1958): Statistics of Extremes. Columbia University Press.
Coles, S. (2001): An Introduction to Statistical Modeling of Extreme Values.
    Springer, ch. 3 (minima are modelled as maxima of the negated series).
Stedinger, J. R., Vogel, R. M. & Foufoula-Georgiou, E. (1993): Frequency analysis
    of extreme events. In: Maidment, D. R. (Ed.), Handbook of Hydrology, ch. 18.
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

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.statistics._hydrological_year import (
    AnnualExtremes,
    annual_extremes,
    incomplete_years_message,
)
from hydrolog.statistics._types import (
    EmpiricalFrequency,
    LowFlowEmpiricalFrequency,
    compute_non_exceedance_positions,
    compute_plotting_positions,
)

_DEFAULT_RETURN_PERIODS = np.array([2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0])


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class LowFlowFrequencyResult(JsonResultMixin):
    """Result of fitting the Fisher-Tippett distribution of smallest values.

    The fitted distribution function of the annual minima *x* is::

        F(x) = 1 - exp(-(1 + shape * (x - loc) / scale) ** (1 / shape))

    where ``1 + shape * (x - loc) / scale > 0``. For ``shape -> 0`` it becomes
    the Gumbel minimum ``F(x) = 1 - exp(-exp((x - loc) / scale))``; for
    ``shape > 0`` the minima have the lower bound ``loc - scale / shape`` (the
    three-parameter Weibull distribution with shape ``1 / shape``). The
    quantile with non-exceedance probability *p* is
    ``loc + scale / shape * ((-ln(1 - p)) ** shape - 1)``.

    Attributes
    ----------
    distribution_name : str
        Always ``"fisher_tippett"``.
    parameters : dict[str, float]
        Fitted distribution parameters: ``shape`` (the ``c`` of
        :data:`scipy.stats.genextreme`, i.e. minus the shape ``xi`` of the usual
        GEV notation), ``loc`` and ``scale`` (in the unit of the flows).
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
class LowFlowSequence(JsonResultMixin):
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
class LowFlowAnalysisResult(JsonResultMixin):
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

    Notes
    -----
    The annual minima are those of the *complete* hydrological years (see
    :meth:`annual_minima`); a ``NaN`` flow and a day absent from ``dates`` are
    days without a value. The return periods of the results are non-exceedance
    return periods: a low flow of return period *T* is equalled or undercut once
    in *T* years.

    Examples
    --------
    >>> import numpy as np
    >>> from hydrolog.statistics.low_flows import LowFlowAnalysis
    >>> rng = np.random.default_rng(0)
    >>> dates = np.arange(
    ...     np.datetime64("2010-11-01"),
    ...     np.datetime64("2020-11-01"),
    ...     dtype="datetime64[D]",
    ... )
    >>> flows = rng.uniform(1, 100, size=len(dates))
    >>> lfa = LowFlowAnalysis(flows, dates)  # doctest: +SKIP
    """

    def __init__(
        self,
        daily_flows: NDArray[np.float64],
        dates: NDArray[np.datetime64],
        return_periods: NDArray[np.float64] | None = None,
    ) -> None:
        daily_flows = np.asarray(daily_flows, dtype=np.float64)
        dates = np.asarray(dates)

        if len(daily_flows) == 0 or len(dates) == 0:
            raise InvalidParameterError("daily_flows and dates must not be empty.")
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
        """Extract annual minimum flows (one per complete hydrological year).

        Uses the Polish hydrological year (Nov 1 – Oct 31). Only *complete* years
        are used: a year is complete when the series has a value for every day of
        it (365 days, or 366 when it contains 29 February; a ``NaN`` flow is a day
        without a value). The minimum of a year with missing days may be higher
        than the true one and would bias the low-flow quantiles, so such a year is
        skipped and named in a warning (WMO No. 1029, 2009, and KZGW, 2017, take
        whole years of observations for annual extremes). A calendar-year series
        (1 January - 31 December) therefore loses its first hydrological year
        (which lacks November and December) and its last one (which holds only
        those two months).

        Returns
        -------
        NDArray[np.float64]
            Array of annual minima, one value per complete hydrological year,
            sorted by hydrological year.

        Raises
        ------
        CalculationError
            If the series has no complete hydrological year.

        Warns
        -----
        UserWarning
            If incomplete years were skipped, and if fewer than 10 complete
            years are available.

        Notes
        -----
        Versions before 1.0.0 took the minimum of every hydrological year that
        appears in the dates, including the stub years at both ends of a
        calendar-year series (for a 1991-2020 series: 31 "years", the last holding
        only November and December 2020, with a minimum above the true annual one).
        """
        extremes = self._annual_extremes()
        if extremes.incomplete:
            warnings.warn(incomplete_years_message(extremes), UserWarning, stacklevel=2)
        if len(extremes.years) < 10:
            warnings.warn(
                f"Only {len(extremes.years)} year(s) of data available; "
                "low-flow frequency estimates may be unreliable.",
                UserWarning,
                stacklevel=2,
            )
        return extremes.values.copy()

    def fit_fisher_tippett(self) -> LowFlowFrequencyResult:
        """Fit the Fisher-Tippett distribution of smallest values to annual minima.

        The annual minima are modelled with the generalized extreme value (GEV)
        distribution *for minima* (Fisher-Tippett distribution of smallest
        values; see :class:`LowFlowFrequencyResult` for the distribution
        function and its special cases, Gumbel minimum and Weibull). Because the
        minimum of a sample is the negative of the maximum of the negated sample,
        ``min(x) = -max(-x)``, the parameters are estimated by maximum
        likelihood from the *negated* minima with :data:`scipy.stats.genextreme`
        (Fisher & Tippett 1928; Gumbel 1958; Coles 2001, ch. 3). The quantile of
        the minima with non-exceedance probability ``p = 1/T`` is
        ``Q_T = -genextreme.isf(p, c, loc=-loc, scale=scale)``, the flow that is
        equalled or *not exceeded* once in *T* years on average.

        Returns
        -------
        LowFlowFrequencyResult
            Fitted result with quantile estimates.

        Raises
        ------
        CalculationError
            If the series has no complete hydrological year.

        Warns
        -----
        UserWarning
            If incomplete years were skipped or fewer than 10 complete years are
            available (see :meth:`annual_minima`).

        Notes
        -----
        Versions before 1.0.0 fitted the distribution of *maxima* directly to the
        minima and read its quantiles at ``p``. That is the mirror-image
        distribution family: it can approximate the bulk of the minima, but its
        left tail is not that of the smallest-value distribution, so the
        quantiles of rare droughts were biased, increasingly with ``T``, and could
        even be negative. The fit to the negated minima is consistent: for a
        sample from a minimum-type distribution its quantiles converge to the
        true ones.

        The fitted distribution is not constrained to positive flows: with
        ``shape <= 0`` the minima have no lower bound and the quantiles of very
        long return periods can be negative. The three parameters are estimated
        by maximum likelihood; for short records (a few tens of years) the shape,
        and with it the quantiles of rare droughts, is very uncertain.
        """
        minima = self.annual_minima()
        # min(x) = -max(-x): the minima-type GEV is the maxima-type GEV of -x.
        negated = -minima

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            c, loc_negated, scale = genextreme.fit(negated)
        fitted = genextreme(c, loc=loc_negated, scale=scale)

        # ``0.0 - x`` instead of ``-x``: an all-zero record must give 0.0, not -0.0.
        params: dict[str, float] = {
            "shape": float(c),
            "loc": float(0.0 - loc_negated),
            "scale": float(scale),
        }

        # Non-exceedance probability p = 1/T of the minima = exceedance
        # probability of the negated series; isf stays accurate for tiny p.
        p = 1.0 / self._return_periods
        quantiles = 0.0 - fitted.isf(p)

        # K-S test (informational; invalid when parameters estimated from data).
        # The statistic is the same for a sample and its mirror image.
        ks_stat, ks_pval = kstest(negated, fitted.cdf)

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

    def empirical_frequency(self, method: str = "weibull") -> EmpiricalFrequency:
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

        Notes
        -----
        The probabilities and return periods of the result belong to the
        *exceedance* of the minima: the deepest low flow has the largest
        exceedance probability ``n / (n + 1)`` and the shortest return period
        ``(n + 1) / n``. They are not the return periods of low flows used by
        :meth:`fit_fisher_tippett`; to compare the sample with the fitted
        quantiles use :meth:`empirical_non_exceedance`.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            minima = self.annual_minima()

        return compute_plotting_positions(minima, method=method)

    def empirical_non_exceedance(
        self, method: str = "weibull"
    ) -> LowFlowEmpiricalFrequency:
        """Compute empirical non-exceedance plotting positions of annual minima.

        The empirical counterpart of :meth:`fit_fisher_tippett`, in the same
        convention: the annual minima are sorted ascending, the ``m``-th smallest
        gets the non-exceedance probability ``F = m / (n + 1)`` (Weibull) and the
        return period ``T = 1 / F``, the average interval in years between years
        whose minimum is equal to or lower than the value (WMO No. 1029, 2009;
        Tallaksen and van Lanen, 2004). The deepest low flow of ``n`` years has
        ``T = n + 1``; compare these ``(F, value)`` pairs with the fitted
        quantiles at ``F = 1 / T``.

        Parameters
        ----------
        method : str, optional
            Plotting position method, by default ``"weibull"``.
            Options: ``"weibull"`` (``F = m / (n + 1)``), ``"hazen"``
            (``F = (m - 0.5) / n``), ``"cunnane"`` (``F = (m - 0.4) / (n + 0.2)``).

        Returns
        -------
        LowFlowEmpiricalFrequency
            Annual minima sorted in ascending order with non-exceedance
            probabilities and return periods.

        Raises
        ------
        CalculationError
            If the series has no complete hydrological year.
        InvalidParameterError
            If ``method`` is not one of the supported options.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            minima = self.annual_minima()

        return compute_non_exceedance_positions(minima, method=method)

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

        Raises
        ------
        InvalidParameterError
            If threshold <= 0 or min_duration_days < 1.
        """
        from hydrolog.exceptions import InvalidParameterError

        if threshold <= 0:
            raise InvalidParameterError(f"threshold must be positive, got {threshold}")
        if min_duration_days < 1:
            raise InvalidParameterError(
                f"min_duration_days must be >= 1, got {min_duration_days}"
            )

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
        starts: NDArray[np.intp] = np.where(diff == 1)[0]  # already offset-corrected
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

        for s, e in zip(merged_starts, merged_ends, strict=False):
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _annual_extremes(self) -> AnnualExtremes:
        """Annual minima of the complete hydrological years of the series.

        Raises
        ------
        CalculationError
            If the series has no complete hydrological year.
        """
        extremes = annual_extremes(self._flows, self._dates, "min")
        if len(extremes.years) == 0:
            raise CalculationError(
                "The series has no complete hydrological year (1 November - "
                "31 October with a value for every day), so there are no annual "
                "minima",
                details={"incomplete_years": extremes.incomplete_years},
                hint="Provide at least one full hydrological year of daily values "
                "without gaps.",
            )
        return extremes
