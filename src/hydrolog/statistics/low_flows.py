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

import math
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Final, NamedTuple

import numpy as np
from numpy.typing import NDArray
from scipy.stats import genextreme, kstest

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog._warnings import IncompleteYears, NegativeQuantiles, SmallSample
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.nogat_formulas import (
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._hydrological_year import (
    AnnualExtremes,
    annual_extremes,
    incomplete_years_details,
    on_daily_calendar,
)
from hydrolog.statistics._types import (
    EmpiricalFrequency,
    LowFlowEmpiricalFrequency,
    compute_non_exceedance_positions,
    compute_plotting_positions,
)
from hydrolog.statistics.events import threshold_runs
from hydrolog.statistics.frequency import (
    _ANY_VALUE,
    _MINIMA,
    _SMITH_1985,
    _WMO_1029,
    _WMO_1029_URL,
    _count,
    _maximum_likelihood,
    _not_constant,
    fit_maximum_likelihood,
    gev_quantiles,
)

_DEFAULT_RETURN_PERIODS = np.array([2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0])
_MIN_RELIABLE_YEARS = 10  # below it the estimates may be unreliable


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
        Quantile estimates (minimum flow level) for each return period; NaN (null in
        JSON) where the fitted distribution would give a negative discharge.
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
        Total length of the sequence in days (calendar days, bridged gaps
        included).
    min_flow : float
        Minimum flow observed during the sequence.
    mean_flow : float
        Mean flow of the days of the sequence that have a value.
    deficit_volume : float
        Cumulative deficit: ``sum(threshold - Q[i])`` for all days where
        ``Q[i] < threshold`` within the sequence window.
    missing_days : int
        Days of the sequence without a value (a ``NaN`` or an absent date).
    open_start, open_end : bool
        The day before the first (after the last) has no value: the sequence may
        have begun earlier (lasted longer).
    """

    start_index: int
    end_index: int
    duration_days: int
    min_flow: float
    mean_flow: float
    deficit_volume: float
    missing_days: int = 0
    open_start: bool = False
    open_end: bool = False


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
        Versions before 0.8.0 took the minimum of every hydrological year that
        appears in the dates, including the stub years at both ends of a
        calendar-year series (for a 1991-2020 series: 31 "years", the last holding
        only November and December 2020, with a minimum above the true annual one).
        """
        extremes = self._annual_extremes()
        if extremes.incomplete:
            warnings.warn(
                IncompleteYears(**incomplete_years_details(extremes)), stacklevel=2
            )
        years = len(extremes.years)
        if years < _MIN_RELIABLE_YEARS:
            warnings.warn(
                SmallSample(years=years, minimum=_MIN_RELIABLE_YEARS), stacklevel=2
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
        (Fisher & Tippett 1928; Gumbel 1958; Coles 2001, ch. 3), by the search of
        maximum likelihood of :class:`~hydrolog.statistics.FloodFrequencyAnalysis`
        (the standardised sample, the L-moments' start, run again until it gains
        nothing). The quantile of the minima with non-exceedance probability
        ``p = 1/T`` is ``Q_T = -genextreme.isf(p, c, loc=-loc, scale=scale)``, the
        flow that is equalled or *not exceeded* once in *T* years on average.

        Returns
        -------
        LowFlowFrequencyResult
            Fitted result with quantile estimates.

        Raises
        ------
        CalculationError
            If the series has no complete hydrological year, or maximum likelihood
            gives no parameters: fewer than 4 annual minima (``too_few_values``),
            all equal (``constant_values``), a likelihood without a maximum
            (``unbounded_likelihood``: a shape of 1 or more puts the lower bound at
            the smallest minimum) or a search that does not settle
            (``not_converged``).

        Warns
        -----
        UserWarning
            If incomplete years were skipped or fewer than 10 complete years are
            available (see :meth:`annual_minima`), or quantiles are left out as
            negative discharges (``negative_quantiles``).

        Notes
        -----
        Versions before 0.8.0 fitted the distribution of *maxima* directly to the
        minima and read its quantiles at ``p``. That is the mirror-image
        distribution family: it can approximate the bulk of the minima, but its
        left tail is not that of the smallest-value distribution, so the
        quantiles of rare droughts were biased, increasingly with ``T``, and could
        even be negative. The fit to the negated minima is consistent: for a
        sample from a minimum-type distribution its quantiles converge to the
        true ones.

        The fitted distribution is not constrained to positive flows: with
        ``shape <= 0`` the minima have no lower bound, and with ``shape > 0`` the
        bound ``loc - scale / shape`` may lie below 0 (WMO No. 1029, 2009, sec. 7.5,
        wants it at 0 or above). A quantile below 0 would be a negative discharge,
        which cannot occur: it is NaN, and the warning ``negative_quantiles`` names
        its return periods and the return period at which the fitted distribution
        reaches 0. Versions up to 0.8.1 returned such quantiles, and also those of
        scipy's ``fit`` stopped far from the maximum of the likelihood (the 10-year
        low flow -0.047 m³/s instead of 0.017 for 20 minima of a small stream). For
        short records (a few tens of years) the shape, and with it the quantiles of
        rare droughts, is very uncertain.
        """
        return _fisher_tippett(
            self.annual_minima(), self._return_periods, discharge=True
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

        The flows are laid on the calendar of their dates: a day whose date is
        absent or whose flow is ``NaN`` has no value, is never below the threshold
        and counts as a gap day (:func:`hydrolog.statistics.threshold_runs`), so a
        series with gaps in the record has its sequences across them.

        Parameters
        ----------
        threshold : float
            Flow threshold (same unit as *daily_flows*), any finite number: a stage
            may lie at or below the gauge zero, and no flow is below a threshold of 0.
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
        when two runs are merged; days without a value contribute nothing. The
        minimum and the mean are those of the days with a value.

        Versions before 0.8.1 refused a threshold at or below 0, so the low-stage
        periods of a gauge whose mean annual minimum stage (SNW) lies below its zero
        could not be found.

        Raises
        ------
        InvalidParameterError
            If threshold is not finite, min_duration_days < 1 or the dates do not
            increase strictly.
        """
        if not math.isfinite(threshold):
            raise InvalidParameterError(f"threshold must be finite, got {threshold}")
        if min_duration_days < 1:
            raise InvalidParameterError(
                f"min_duration_days must be >= 1, got {min_duration_days}"
            )
        dates = np.asarray(self._dates).astype("datetime64[D]")
        if np.any(dates[1:] <= dates[:-1]):
            raise InvalidParameterError("the dates must increase strictly")

        _, flows = on_daily_calendar(self._flows, dates)
        present = ~np.isnan(flows)
        with np.errstate(invalid="ignore"):
            below = present & (flows < threshold)
        starts, ends = threshold_runs(
            below, min_duration_days=min_duration_days, max_gap_days=max_gap_days
        )
        # The calendar day of each flow, to give the positions in the given arrays.
        offsets = (dates - dates[0]).astype(np.int64)
        last = flows.size - 1
        sequences: list[LowFlowSequence] = []
        for start, end in zip(starts.tolist(), ends.tolist(), strict=True):
            window = flows[start : end + 1]
            known = window[~np.isnan(window)]
            sequences.append(
                LowFlowSequence(
                    start_index=int(np.searchsorted(offsets, start)),
                    end_index=int(np.searchsorted(offsets, end)),
                    duration_days=end - start + 1,
                    min_flow=float(known.min()),
                    mean_flow=float(known.mean()),
                    deficit_volume=float(np.sum(np.maximum(threshold - known, 0.0))),
                    missing_days=int(window.size - known.size),
                    open_start=start == 0 or not bool(present[start - 1]),
                    open_end=end == last or not bool(present[end + 1]),
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


def fit_fisher_tippett_minima(
    minima: NDArray[np.float64],
    return_periods: NDArray[np.float64] | None = None,
    *,
    discharge: bool = True,
) -> LowFlowFrequencyResult:
    """Fit the Fisher-Tippett distribution of smallest values to annual minima.

    The fit of :meth:`LowFlowAnalysis.fit_fisher_tippett` for minima that are
    already known, such as the smaller of IMGW-PIB's half-year minima: maximum
    likelihood of :data:`scipy.stats.genextreme` on the negated minima, the quantile
    of return period ``T`` at the non-exceedance probability ``1 / T``.

    Parameters
    ----------
    minima : NDArray[np.float64]
        Annual minima in the unit of the series.
    return_periods : NDArray[np.float64] or None, optional
        Return periods [years]; by default 2, 5, 10, 20, 50, 100, 500 and 1000.
    discharge : bool, optional
        Whether the minima are discharges, which cannot be negative (the default): a
        quantile below 0 is then NaN with the warning ``negative_quantiles``. False
        for a variable without that limit, such as a stage, whose zero is the
        gauge's.

    Returns
    -------
    LowFlowFrequencyResult
        The fitted parameters, the low-flow quantiles and the K-S statistics.

    Raises
    ------
    InvalidParameterError
        If a minimum is not a finite number.
    CalculationError
        If maximum likelihood gives no parameters (see
        :meth:`LowFlowAnalysis.fit_fisher_tippett`).

    Warns
    -----
    UserWarning
        If fewer than 10 minima are given (``small_sample``), or quantiles are left
        out as negative discharges (``negative_quantiles``).
    """
    sample = np.asarray(minima, dtype=np.float64)
    if not np.all(np.isfinite(sample)):
        raise InvalidParameterError(
            "minima must hold finite numbers only (no NaN or infinity).",
            details={"option": "minima", "reason": "not_finite"},
        )
    if sample.size < _MIN_RELIABLE_YEARS:
        warnings.warn(
            SmallSample(years=int(sample.size), minimum=_MIN_RELIABLE_YEARS),
            stacklevel=2,
        )
    periods = (
        np.asarray(return_periods, dtype=np.float64)
        if return_periods is not None
        else _DEFAULT_RETURN_PERIODS.copy()
    )
    return _fisher_tippett(sample, periods, discharge=discharge)


def _fisher_tippett(
    minima: NDArray[np.float64], periods: NDArray[np.float64], *, discharge: bool
) -> LowFlowFrequencyResult:
    """Return the fit of :func:`fit_fisher_tippett_minima`, with its K-S statistic."""
    fit = fisher_tippett_minima(minima, periods, "discharge" if discharge else "stage")
    fitted = genextreme(fit.shape, loc=0.0 - fit.loc, scale=fit.scale)
    # K-S test (informational; invalid when parameters estimated from data).
    # The statistic is the same for a sample and its mirror image.
    ks_stat, ks_pval = kstest(-np.asarray(minima, dtype=np.float64), fitted.cdf)
    return LowFlowFrequencyResult(
        distribution_name="fisher_tippett",
        parameters={"shape": fit.shape, "loc": fit.loc, "scale": fit.scale},
        return_periods=np.asarray(periods, dtype=np.float64).copy(),
        quantiles=fit.quantiles,
        non_exceedance_probabilities=1.0 / np.asarray(periods, dtype=np.float64),
        ks_statistic=float(ks_stat),
        ks_p_value=float(ks_pval),
        ks_valid=False,
    )


# --- the spec of the Fisher-Tippett distribution of minima ---------------------


class FisherTippettMinima(NamedTuple):
    """Fisher-Tippett distribution of minima, quantiles (spec fisher_tippett_minima)."""

    shape: float
    loc: float
    scale: float
    quantiles: NDArray[np.float64]


_STATION_223207: Final = (
    27.3, 38.0, 72.9, 53.6, 45.7, 37.0, 21.7, 36.6, 43.1, 12.6, 20.7, 66.7, 76.6,
    53.1, 15.7, 66.6, 78.0, 53.1, 62.6, 40.7, 51.6, 23.1, 23.4, 23.0, 6.0,
)  # fmt: skip
"""The AM(7) annual minima of station 223207 (WMO-No. 1029, table 7.1): the typical
sample of the generated tests."""
_UNBOUNDED_MINIMA: Final = (19.0, *[10.0] * 8, 9.5)
"""Minima whose negated sample has a GEV likelihood without a maximum (its upper
bound runs to the largest value, Smith 1985)."""
_NEGATED: Final = (
    "min(x) = -max(-x): the Fisher-Tippett distribution of the minima is the GEV of "
    "the negated minima, F(x) = 1 - exp{-[1 + c (x - loc) / scale]^(1/c)} with "
    "scipy's genextreme shape c and the location -loc of the negated sample"
)


def _gev_of_the_negated(run: Callable[..., Values]) -> None:
    """Assert that the fit is the mirrored maximum-likelihood GEV of the negated."""
    periods = [1.5, 2.0, 10.0, 100.0, 1000.0]
    out = run(minima=list(_STATION_223207), return_periods_years=periods)
    gev = fit_maximum_likelihood([-value for value in _STATION_223207], "gev")
    assert_within(
        [out.real("shape"), out.real("loc"), out.real("scale")],
        [gev.shape, -gev.loc, gev.scale],
        rel=4.5e-16,
        abs=1e-300,
        reason="the same search on the same negated sample",
    )
    assert_within(
        out.array("quantiles"),
        -gev_quantiles(gev.shape, gev.loc, gev.scale, periods),
        rel=4.5e-16,
        abs=1e-300,
        reason="the non-exceedance 1/T of the minima is the exceedance 1/T of the "
        "negated minima, the same inverse survival function",
    )


FISHER_TIPPETT: Final = FormulaSpec(
    name="fisher_tippett_minima",
    title="Fisher-Tippett distribution of annual minima by maximum likelihood and its "
    "quantiles",
    function="hydrolog.statistics.low_flows.fisher_tippett_minima",
    family="statistic",
    equation=(
        "F(x) = 1 - exp{-[1 + c (x - loc) / scale]^(1/c)}, the GEV of -x (scipy's "
        "genextreme with shape c and location -loc) fitted to the negated minima by "
        "maximum likelihood (fit_maximum_likelihood); Q_T = loc + scale ((-ln(1 - "
        "1/T))**c - 1) / c at the non-exceedance 1/T, loc + scale ln(-ln(1 - 1/T)) "
        "for c = 0; a quantile of a discharge below 0 is a gap"
    ),
    latex=(
        r"F(x) = 1 - \exp\left\{-\left[1 + c\,\frac{x - \xi}{\alpha}\right]^{1/c}"
        r"\right\},\quad Q_T = \xi + \frac{\alpha}{c}\left[\left(-\ln\left(1 - "
        r"\frac{1}{T}\right)\right)^{c} - 1\right]"
    ),
    variables=(
        Variable(
            name="minima",
            symbol="x_i",
            unit="m3/s",
            kind="real_array",
            description="Annual minima of a discharge or a stage.",
            physical=_ANY_VALUE,
            applicability="unstated",
            typical=_MINIMA,
        ),
        Variable(
            name="return_periods_years",
            symbol="T",
            unit="years",
            kind="real_array",
            description="Return periods: the quantile of T years is undercut with the "
            "probability 1/T in a year.",
            physical=Range(
                low=1.0,
                low_inclusive=False,
                test_high=1.0e6,
                test_reason="a million years tests the far lower tail; droughts are "
                "estimated for at most a thousand years",
            ),
            applicability="unstated",
            typical=Range(
                low=2.0,
                high=1000.0,
                source=Source(
                    citation="Hydrolog (2026). stats low-flow and Obserwator's "
                    "low_flow.Q",
                    locator="the default return periods, 2 to 1000 years",
                    url="https://github.com/Daldek/Hydrolog",
                ),
            ),
        ),
        Variable(
            name="variable",
            symbol="v",
            unit="-",
            kind="choice",
            description="What the minima are: a discharge, never below 0, or a stage, "
            "whose 0 is the gauge's.",
            choices=("discharge", "stage"),
        ),
    ),
    outputs=(
        Output(
            name="shape",
            unit="-",
            symbol="c",
            description="Shape c of scipy's genextreme of the negated minima: a lower "
            "bound loc - scale / c of the minima for c > 0.",
            physical=Range(),
        ),
        Output(name="loc", unit="m3/s", symbol=r"\xi", physical=Range()),
        Output(
            name="scale",
            unit="m3/s",
            symbol=r"\alpha",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="quantiles",
            unit="m3/s",
            kind="real_array",
            symbol="Q_T",
            description="The minima of the return periods; a gap where a discharge "
            "would be negative.",
            physical=Range(),
            gaps_allowed=True,
        ),
    ),
    sources=(
        Source(
            citation=_WMO_1029,
            locator="sect. 7.5, p. 62: if X is EV III distributed, -X is Weibull "
            "distributed; eq. 7.14, p. 64: T of the event X <= x_p",
            url=_WMO_1029_URL,
        ),
        Source(
            citation="Coles, S. (2001). An Introduction to Statistical Modeling of "
            "Extreme Values. Springer",
            locator="sect. 3.1.4: min(X) = -max(-X), the GEV of minima",
            access="author-provided",
        ),
    ),
    constraints=(
        _count(
            4,
            Source(
                citation=_SMITH_1985,
                locator="n values fit n parameters exactly, where the likelihood "
                "has no maximum: one value more than the three parameters",
                access="author-provided",
            ),
            "minima",
        ),
        _not_constant(
            Source(
                citation=_WMO_1029,
                locator="sect. 7.5: a distribution of the minima needs their spread",
                url=_WMO_1029_URL,
            ),
            "minima",
            satisfied=(5.0, 6.0, 6.0, 7.0),
        ),
        Constraint(
            name="discharges_not_negative",
            cls="physical",
            check=lambda x: (
                x.choice("variable") != "discharge"
                or bool(np.min(x.array("minima")) >= 0.0)
            ),
            text="min(x) >= 0 for a discharge",
            source=Source(
                citation=_WMO_1029,
                locator="sect. 7.5, p. 62: the lower bound of the minima of a flow "
                "is 0 or above",
                url=_WMO_1029_URL,
            ),
            satisfied={"variable": "discharge"},
            violated={"variable": "discharge", "minima": [-0.01, 2.0, 4.0, 8.0]},
            boundary={"variable": "discharge", "minima": [0.0, 2.0, 4.0, 8.0, 16.0]},
        ),
        Constraint(
            name="likelihood_has_a_maximum",
            cls="precondition",
            check=lambda x: (
                _maximum_likelihood("gev", -x.array("minima")).parameters is not None
            ),
            text="the GEV likelihood of the negated minima has a maximum the search "
            "settles on (precondition likelihood_has_a_maximum of "
            "fit_maximum_likelihood)",
            source=Source(
                citation=_SMITH_1985,
                locator="the bound placed at the closest value makes the likelihood "
                "grow without limit",
                access="author-provided",
            ),
            satisfied={"variable": "stage"},
            violated={"minima": list(_UNBOUNDED_MINIMA)},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_minima",
                inputs={"minima": 1.0},
                outputs={"loc": 1.0, "scale": 1.0, "quantiles": 1.0},
                tolerance=Tolerance(
                    abs=1e-300,
                    rel=4.5e-16,
                    reason="the search runs on the sample divided by a power of two "
                    "and the quantile is loc + scale times the standard one, so "
                    "doubling the minima rounds alike",
                ),
            ),
        ),
        limits=(
            Limit(
                name="gev_of_the_negated",
                text="the parameters and quantiles are those of the maximum-likelihood "
                "GEV of the negated minima, mirrored",
                check=_gev_of_the_negated,
            ),
        ),
    ),
    validation="none: the maximum-likelihood fit of the distribution of minima",
    formula_version=1,
    status="oracle only",
    conventions=(
        _NEGATED,
        "the quantile of T years at the non-exceedance probability 1/T (WMO-No. 1029 "
        "eq. 7.14), from the inverse survival function of the negated sample",
        "a discharge quantile below 0 is a gap (NaN, null in JSON) with the notice "
        "negative_quantiles; a stage keeps it",
        "the search of fit_maximum_likelihood: the GEVs with a mean, -1 < c < 1",
    ),
    assumptions=("the annual minima are independent and identically distributed",),
    notices=("negative_quantiles",),
    traps={
        "singular_at_bound": "constraint case likelihood_has_a_maximum-violated: the "
        "density infinite at a bound placed on a value",
        "unbounded_iteration": "the search of fit_maximum_likelihood "
        "(tests/unit/test_formulas_flood_frequency.py, "
        "test_a_search_that_does_not_settle_is_refused)",
        "gap_propagation": "type case minima-nan_element: a gap is refused; the gaps "
        "of the quantiles are the negative discharges",
    },
    oracles=(
        Oracle(
            kind="algorithm",
            description="the maximum-likelihood GEV of the negated minima and its "
            "quantiles, mirrored",
            test="tests/unit/test_formulas_low_flows.py (limit gev_of_the_negated)",
        ),
        Oracle(
            kind="frozen",
            description="evd 2.3.7.1 fgev and extRemes 2.2.1 fevd on the negated "
            "minima of a small stream (the research of 2026-11-18): log-likelihood "
            "54.537, Q10 0.017422 m3/s",
            test="tests/unit/test_maximum_likelihood.py "
            "(test_small_stream_low_flows_are_the_maximum_and_never_negative)",
            conventions=("evd's xi of the negated sample is -c",),
        ),
    ),
    base={
        "minima": list(_STATION_223207),
        "return_periods_years": [2.0, 10.0, 100.0],
        "variable": "discharge",
    },
)


def fisher_tippett_minima(
    minima: NDArray[np.float64] | list[float] | tuple[float, ...],
    return_periods_years: NDArray[np.float64] | list[float] | tuple[float, ...],
    variable: str,
) -> FisherTippettMinima:
    """Return the Fisher-Tippett distribution of minima, spec fisher_tippett_minima.

    Parameters
    ----------
    minima : array_like of float
        Annual minima.
    return_periods_years : array_like of float
        Return periods [years].
    variable : str
        ``"discharge"`` or ``"stage"``.

    Returns
    -------
    FisherTippettMinima
        The parameters and the quantile of each return period.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.

    Warns
    -----
    NegativeQuantiles
        If quantiles of a discharge are left out as negative.
    """
    x = checked_inputs(
        FISHER_TIPPETT,
        minima=minima,
        return_periods_years=return_periods_years,
        variable=variable,
    )
    search = _maximum_likelihood("gev", -x.array("minima")).parameters
    if search is None:  # the precondition likelihood_has_a_maximum holds
        raise CalculationError("fisher_tippett_minima: the search ended without a fit")
    c, loc_negated, scale = search
    fitted = genextreme(c, loc=loc_negated, scale=scale)
    periods = x.array("return_periods_years")
    # the non-exceedance 1/T of the minima is the exceedance 1/T of the negated
    quantiles = np.asarray(0.0 - fitted.isf(1.0 / periods), dtype=np.float64)
    negative = quantiles < 0.0
    if x.choice("variable") == "discharge" and negative.any():
        # the distribution reaches below zero flow: F(0) = P(-x >= 0) > 1 / T
        warnings.warn(
            NegativeQuantiles(
                return_periods=[float(period) for period in periods[negative]],
                zero_return_period=float(1.0 / fitted.sf(0.0)),
            ),
            stacklevel=2,
        )
        quantiles = np.where(negative, np.nan, quantiles)
    # ``0.0 - x`` instead of ``-x``: a location of 0 must give 0.0, not -0.0.
    out = checked_outputs(
        FISHER_TIPPETT,
        {"shape": c, "loc": 0.0 - loc_negated, "scale": scale, "quantiles": quantiles},
    )
    return FisherTippettMinima(
        out.real("shape"), out.real("loc"), out.real("scale"), out.array("quantiles")
    )


SPECS: Final = (FISHER_TIPPETT,)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""
