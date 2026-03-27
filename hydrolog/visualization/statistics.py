"""Statistics and hydrometrics visualization functions.

This module provides plotting functions for statistical analysis results,
including flood frequency curves, low-flow sequences, rating curves,
and water level frequency distributions.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from hydrolog.statistics.high_flows import FrequencyAnalysisResult
from hydrolog.statistics.low_flows import LowFlowFrequencyResult, LowFlowAnalysisResult
from hydrolog.statistics.characteristic import DailyStatistics, MonthlyStatistics
from hydrolog.statistics._types import EmpiricalFrequency
from hydrolog.statistics._hydrological_year import hydrological_year
from hydrolog.hydrometrics.rating_curve import (
    RatingCurve,
    RatingCurveResult,
    FrequencyDistributionResult,
    WaterLevelZones,
)

from hydrolog.visualization.styles import PALETTE, get_color, add_stats_box

# Polish month names
_MONTH_NAMES = [
    "Sty",
    "Lut",
    "Mar",
    "Kwi",
    "Maj",
    "Cze",
    "Lip",
    "Sie",
    "Wrz",
    "Paź",
    "Lis",
    "Gru",
]

# Distribution display names
_DIST_NAMES = {
    "gev": "GEV",
    "log_normal": "Log-Normalny",
    "pearson3": "Pearson III",
    "weibull": "Weibull",
    "fisher_tippett": "Fisher-Tippett",
}


def plot_frequency_curve(
    result: FrequencyAnalysisResult,
    empirical: Optional[EmpiricalFrequency] = None,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """Plot exceedance probability (flood frequency) curve.

    Displays the theoretical fitted distribution curve on a logarithmic
    probability axis, with optional empirical plotting positions as scatter.

    Parameters
    ----------
    result : FrequencyAnalysisResult
        Fitted frequency analysis result.
    empirical : EmpiricalFrequency, optional
        Empirical plotting positions to overlay as scatter points.
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (10, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
    >>> from hydrolog.visualization.statistics import plot_frequency_curve
    >>> ffa = FloodFrequencyAnalysis(annual_maxima)
    >>> result = ffa.fit_gev()
    >>> fig = plot_frequency_curve(result)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    # Convert exceedance probabilities to percent
    exc_pct = result.exceedance_probabilities * 100.0
    quantiles = result.quantiles

    dist_label = _DIST_NAMES.get(result.distribution_name, result.distribution_name)
    color = get_color("discharge")

    ax.plot(
        exc_pct,
        quantiles,
        color=color,
        linewidth=2,
        label=f"Rozkład {dist_label}",
    )

    if empirical is not None:
        ax.scatter(
            empirical.exceedance_prob * 100.0,
            empirical.values_sorted,
            color=color,
            edgecolors="white",
            s=50,
            zorder=5,
            label="Dane empiryczne",
        )

    ax.set_xscale("log")
    ax.set_xlabel("Prawdopodobieństwo przewyższenia p [%]")
    ax.set_ylabel("Przepływ Q [m³/s]")

    if title is None:
        title = f"Krzywa prawdopodobieństwa — rozkład {dist_label}"
    ax.set_title(title)

    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    # Stats box
    stats = {
        "Rozkład": dist_label,
        "AIC": f"{result.aic:.1f}",
        "KS p": f"{result.ks_p_value:.3f}",
    }
    add_stats_box(ax, stats, loc="upper left")

    fig.tight_layout()
    return fig


def plot_frequency_comparison(
    results: dict[str, FrequencyAnalysisResult],
    empirical: Optional[EmpiricalFrequency] = None,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """Plot multiple frequency distribution curves for comparison.

    Parameters
    ----------
    results : dict[str, FrequencyAnalysisResult]
        Dictionary mapping distribution names to fitted results.
    empirical : EmpiricalFrequency, optional
        Empirical plotting positions to overlay as scatter points.
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (10, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
    >>> from hydrolog.visualization.statistics import plot_frequency_comparison
    >>> ffa = FloodFrequencyAnalysis(annual_maxima)
    >>> results = ffa.fit_all()
    >>> fig = plot_frequency_comparison(results)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    for i, (name, result) in enumerate(results.items()):
        color = PALETTE[i % len(PALETTE)]
        dist_label = _DIST_NAMES.get(name, name)
        exc_pct = result.exceedance_probabilities * 100.0
        ax.plot(
            exc_pct,
            result.quantiles,
            color=color,
            linewidth=2,
            label=f"{dist_label} (AIC={result.aic:.0f})",
        )

    if empirical is not None:
        ax.scatter(
            empirical.exceedance_prob * 100.0,
            empirical.values_sorted,
            color="black",
            edgecolors="white",
            s=50,
            zorder=5,
            label="Dane empiryczne",
        )

    ax.set_xscale("log")
    ax.set_xlabel("Prawdopodobieństwo przewyższenia p [%]")
    ax.set_ylabel("Przepływ Q [m³/s]")

    if title is None:
        title = "Porównanie rozkładów — analiza częstości"
    ax.set_title(title)

    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_non_exceedance_curve(
    result: LowFlowFrequencyResult,
    empirical: Optional[EmpiricalFrequency] = None,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """Plot non-exceedance probability curve for low flows.

    Parameters
    ----------
    result : LowFlowFrequencyResult
        Fitted low-flow frequency analysis result.
    empirical : EmpiricalFrequency, optional
        Empirical plotting positions to overlay as scatter points.
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (10, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.statistics.low_flows import LowFlowAnalysis
    >>> from hydrolog.visualization.statistics import plot_non_exceedance_curve
    >>> lfa = LowFlowAnalysis(daily_flows, dates)
    >>> result = lfa.fit_fisher_tippett()
    >>> fig = plot_non_exceedance_curve(result)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    # Non-exceedance probabilities as percent
    non_exc_pct = result.non_exceedance_probabilities * 100.0
    dist_label = _DIST_NAMES.get(result.distribution_name, result.distribution_name)
    color = PALETTE[4]  # purple

    ax.plot(
        non_exc_pct,
        result.quantiles,
        color=color,
        linewidth=2,
        label=f"Rozkład {dist_label}",
    )

    if empirical is not None:
        # For low flows, non-exceedance = 1 - exceedance
        non_exc_emp_pct = (1.0 - empirical.exceedance_prob) * 100.0
        ax.scatter(
            non_exc_emp_pct,
            empirical.values_sorted,
            color=color,
            edgecolors="white",
            s=50,
            zorder=5,
            label="Dane empiryczne",
        )

    ax.set_xscale("log")
    ax.set_xlabel("Prawdopodobieństwo nieosiągnięcia p [%]")
    ax.set_ylabel("Przepływ Q [m³/s]")

    if title is None:
        title = f"Krzywa niskich przepływów — rozkład {dist_label}"
    ax.set_title(title)

    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    stats = {
        "Rozkład": dist_label,
        "KS p": f"{result.ks_p_value:.3f}",
    }
    add_stats_box(ax, stats, loc="lower right")

    fig.tight_layout()
    return fig


def plot_daily_characteristics(
    daily_stats: DailyStatistics,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (12, 6),
) -> plt.Figure:
    """Plot daily characteristic values over the hydrological year.

    Shows four lines: maximum, mean, median, and minimum flows for each
    hydrological day of year.

    Parameters
    ----------
    daily_stats : DailyStatistics
        Per-day statistics computed from multi-year data.
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (12, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.statistics.characteristic import calculate_daily_statistics
    >>> from hydrolog.visualization.statistics import plot_daily_characteristics
    >>> stats = calculate_daily_statistics(daily_values, dates)
    >>> fig = plot_daily_characteristics(stats)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    days = daily_stats.day_of_year

    ax.plot(
        days,
        daily_stats.max_values,
        color=PALETTE[3],
        linewidth=1.5,
        label="Maksimum",
        alpha=0.85,
    )
    ax.plot(
        days, daily_stats.mean_values, color=PALETTE[0], linewidth=2, label="Średnia"
    )
    ax.plot(
        days,
        daily_stats.median_values,
        color=PALETTE[2],
        linewidth=1.5,
        linestyle="--",
        label="Mediana",
    )
    ax.plot(
        days,
        daily_stats.min_values,
        color=PALETTE[1],
        linewidth=1.5,
        label="Minimum",
        alpha=0.85,
    )

    ax.fill_between(
        days,
        daily_stats.min_values,
        daily_stats.max_values,
        alpha=0.1,
        color=PALETTE[0],
    )

    ax.set_xlabel("Dzień roku hydrologicznego")
    ax.set_ylabel("Przepływ Q [m³/s]")

    if title is None:
        title = "Charakterystyki dobowe w roku hydrologicznym"
    ax.set_title(title)

    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1, int(days[-1]))

    fig.tight_layout()
    return fig


def plot_monthly_statistics(
    monthly_stats: MonthlyStatistics,
    show_ci: bool = True,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """Plot monthly mean statistics as a bar chart.

    Parameters
    ----------
    monthly_stats : MonthlyStatistics
        Monthly statistics with confidence intervals.
    show_ci : bool, optional
        Show confidence interval error bars, by default True.
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (10, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.statistics.characteristic import calculate_monthly_statistics
    >>> from hydrolog.visualization.statistics import plot_monthly_statistics
    >>> stats = calculate_monthly_statistics(daily_values, dates)
    >>> fig = plot_monthly_statistics(stats)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    x = np.arange(12)
    means = monthly_stats.mean_values
    color = get_color("discharge")

    if show_ci:
        lower_err = means - monthly_stats.ci_lower
        upper_err = monthly_stats.ci_upper - means
        yerr = np.array([lower_err, upper_err])
        ax.bar(
            x,
            means,
            color=color,
            alpha=0.75,
            yerr=yerr,
            capsize=4,
            error_kw={"elinewidth": 1.5, "ecolor": "gray"},
        )
    else:
        ax.bar(x, means, color=color, alpha=0.75)

    ax.set_xticks(x)
    ax.set_xticklabels(_MONTH_NAMES)
    ax.set_xlabel("Miesiąc")
    ax.set_ylabel("Przepływ Q [m³/s]")

    if title is None:
        ci_pct = int(monthly_stats.confidence_level * 100)
        ci_note = f" (CI {ci_pct}%)" if show_ci else ""
        title = f"Statystyki miesięczne{ci_note}"
    ax.set_title(title)

    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    return fig


def plot_annual_hydrographs(
    daily_flows: NDArray[np.float64],
    dates: NDArray,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (12, 6),
) -> plt.Figure:
    """Plot overlaid hydrographs for each hydrological year.

    Each hydrological year is drawn as a separate line, aligned to
    hydrological day of year (day 1 = Nov 1).

    Parameters
    ----------
    daily_flows : NDArray[np.float64]
        Daily streamflow values.
    dates : NDArray
        Corresponding dates (dtype datetime64[D]).
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (12, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.visualization.statistics import plot_annual_hydrographs
    >>> fig = plot_annual_hydrographs(daily_flows, dates)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    daily_flows = np.asarray(daily_flows, dtype=np.float64)
    dates = np.asarray(dates)

    from hydrolog.statistics._hydrological_year import (
        hydrological_year,
        hydrological_day_of_year,
    )

    hydro_years = hydrological_year(dates)
    hydro_days = hydrological_day_of_year(dates)
    unique_years = np.unique(hydro_years)

    for i, yr in enumerate(unique_years):
        mask = hydro_years == yr
        year_days = hydro_days[mask]
        year_flows = daily_flows[mask]
        sort_idx = np.argsort(year_days)
        color = PALETTE[i % len(PALETTE)]
        ax.plot(
            year_days[sort_idx],
            year_flows[sort_idx],
            color=color,
            linewidth=1.2,
            alpha=0.7,
            label=str(yr),
        )

    ax.set_xlabel("Dzień roku hydrologicznego")
    ax.set_ylabel("Przepływ Q [m³/s]")

    if title is None:
        title = "Hydrogramy roczne"
    ax.set_title(title)

    ax.legend(
        loc="upper right",
        framealpha=0.9,
        fontsize=9,
        ncol=max(1, len(unique_years) // 8),
    )
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_flow_histogram(
    values: NDArray[np.float64],
    bins: int = 20,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """Plot histogram of flow values.

    Parameters
    ----------
    values : NDArray[np.float64]
        Flow values to plot.
    bins : int, optional
        Number of histogram bins, by default 20.
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (10, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.visualization.statistics import plot_flow_histogram
    >>> fig = plot_flow_histogram(daily_flows, bins=25)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    values = np.asarray(values, dtype=np.float64)
    color = get_color("discharge")

    ax.hist(values, bins=bins, color=color, edgecolor="white", linewidth=0.5, alpha=0.8)

    mean_val = float(np.mean(values))
    median_val = float(np.median(values))

    ax.axvline(
        mean_val,
        color="black",
        linestyle="--",
        linewidth=1.8,
        label=f"Średnia = {mean_val:.2f} m³/s",
    )
    ax.axvline(
        median_val,
        color=PALETTE[1],
        linestyle="-.",
        linewidth=1.8,
        label=f"Mediana = {median_val:.2f} m³/s",
    )

    ax.set_xlabel("Przepływ Q [m³/s]")
    ax.set_ylabel("Liczba obserwacji")

    if title is None:
        title = f"Histogram przepływów (n = {len(values):,})"
    ax.set_title(title)

    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    stats = {
        "Min": f"{np.min(values):.2f}",
        "Max": f"{np.max(values):.2f}",
        "Śr": f"{mean_val:.2f}",
        "Std": f"{np.std(values, ddof=1):.2f}",
    }
    add_stats_box(ax, stats, loc="upper left")

    fig.tight_layout()
    return fig


def plot_low_flow_sequences(
    daily_flows: NDArray[np.float64],
    result: LowFlowAnalysisResult,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (12, 5),
) -> plt.Figure:
    """Plot daily hydrograph with shaded drought (low-flow) periods.

    Parameters
    ----------
    daily_flows : NDArray[np.float64]
        Daily streamflow values.
    result : LowFlowAnalysisResult
        Detected low-flow sequences from threshold method.
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (12, 5).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.statistics.low_flows import LowFlowAnalysis
    >>> from hydrolog.visualization.statistics import plot_low_flow_sequences
    >>> lfa = LowFlowAnalysis(daily_flows, dates)
    >>> low_result = lfa.detect_sequences(threshold=Q70, min_duration_days=5)
    >>> fig = plot_low_flow_sequences(daily_flows, low_result)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    daily_flows = np.asarray(daily_flows, dtype=np.float64)
    days = np.arange(len(daily_flows))

    color = get_color("discharge")
    ax.plot(days, daily_flows, color=color, linewidth=1.2, label="Q dobowe")

    # Threshold line
    ax.axhline(
        result.threshold,
        color="orange",
        linestyle="--",
        linewidth=1.5,
        label=f"Próg Q = {result.threshold:.2f} m³/s",
    )

    # Shade each drought sequence
    labeled = False
    for seq in result.sequences:
        label = "Epizod niskiego przepływu" if not labeled else None
        ax.axvspan(seq.start_index, seq.end_index, alpha=0.25, color="red", label=label)
        labeled = True

    ax.set_xlabel("Czas [dni]")
    ax.set_ylabel("Przepływ Q [m³/s]")

    if title is None:
        title = (
            f"Epizody niskich przepływów — "
            f"{result.n_events} zdarzeń, próg = {result.threshold:.2f} m³/s"
        )
    ax.set_title(title)

    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, len(daily_flows) - 1)

    if result.n_events > 0:
        stats = {
            "Zdarzenia": str(result.n_events),
            "Maks. czas": f"{result.max_duration_days} dni",
            "Def. łączny": f"{result.total_deficit:.1f}",
        }
        add_stats_box(ax, stats, loc="upper left")

    fig.tight_layout()
    return fig


def plot_rating_curve(
    rating: RatingCurve,
    result: RatingCurveResult,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (8, 6),
) -> plt.Figure:
    """Plot rating curve scatter and fitted power-law curve.

    Parameters
    ----------
    rating : RatingCurve
        RatingCurve object holding the original data.
    result : RatingCurveResult
        Fitted rating curve parameters and statistics.
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (8, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.hydrometrics.rating_curve import RatingCurve
    >>> from hydrolog.visualization.statistics import plot_rating_curve
    >>> rc = RatingCurve(water_levels, discharges)
    >>> result = rc.fit(h0_initial=50.0)
    >>> fig = plot_rating_curve(rc, result)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    h_obs = rating._h
    q_obs = rating._q

    color = get_color("discharge")

    # Scatter: observed (H, Q) pairs
    ax.scatter(
        h_obs,
        q_obs,
        color=color,
        edgecolors="white",
        s=60,
        zorder=5,
        label="Pomiary (H, Q)",
    )

    # Fitted curve over the range of observed H
    h_min = float(np.min(h_obs))
    h_max = float(np.max(h_obs))
    h_line = np.linspace(h_min, h_max, 200)
    q_line = rating.predict(h_line)

    ax.plot(
        h_line,
        q_line,
        color="black",
        linewidth=2,
        zorder=4,
        label=f"Q = {result.a:.4f}·(H − {result.h0:.1f})^{result.b:.3f}",
    )

    ax.set_xlabel("Stan wody H [cm]")
    ax.set_ylabel("Przepływ Q [m³/s]")

    if title is None:
        title = f"Krzywa natężenia przepływu (R² = {result.r_squared:.4f})"
    ax.set_title(title)

    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    stats = {
        "a": f"{result.a:.4f}",
        "b": f"{result.b:.3f}",
        "H₀": f"{result.h0:.1f}",
        "R²": f"{result.r_squared:.4f}",
        "n": str(result.n_points),
    }
    add_stats_box(ax, stats, loc="lower right")

    fig.tight_layout()
    return fig


def plot_water_level_frequency(
    freq: FrequencyDistributionResult,
    zones: Optional[WaterLevelZones] = None,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """Plot water level frequency/duration curve with optional zone bands.

    Displays the duration (exceedance) curve as a bar chart of frequency
    per bin, with the cumulative duration curve overlaid. Optional Rybczyński
    zone bands (NTW/STW/WTW) are drawn as colored background regions.

    Parameters
    ----------
    freq : FrequencyDistributionResult
        Water level frequency distribution result.
    zones : WaterLevelZones, optional
        Rybczyński zone boundaries for NTW/STW/WTW shading.
    title : str, optional
        Plot title. Auto-generated if None.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (10, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency
    >>> from hydrolog.visualization.statistics import plot_water_level_frequency
    >>> wlf = WaterLevelFrequency(water_levels, bin_width=10.0)
    >>> freq = wlf.frequency_distribution()
    >>> zones = wlf.rybczynski_zones()
    >>> fig = plot_water_level_frequency(freq, zones=zones)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        assert fig is not None

    centers = freq.bin_centers
    bin_width = float(centers[1] - centers[0]) if len(centers) > 1 else 1.0

    # Optional zone bands drawn first (behind bars)
    if zones is not None:
        ax.axvspan(
            zones.ntw_range[0],
            zones.ntw_range[1],
            alpha=0.12,
            color="blue",
            label="NTW",
        )
        ax.axvspan(
            zones.stw_range[0],
            zones.stw_range[1],
            alpha=0.12,
            color="green",
            label="STW",
        )
        ax.axvspan(
            zones.wtw_range[0], zones.wtw_range[1], alpha=0.12, color="red", label="WTW"
        )

    # Bar chart of frequency [%]
    ax.bar(
        centers,
        freq.frequency_pct,
        width=bin_width * 0.9,
        color=PALETTE[0],
        alpha=0.75,
        label="Częstość [%]",
    )

    # Duration (exceedance) curve on twin y-axis
    ax2 = ax.twinx()
    ax2.plot(
        centers,
        freq.duration_pct,
        color=PALETTE[3],
        linewidth=2,
        label="Czas trwania [%]",
    )
    ax2.set_ylabel("Czas trwania [%]")
    ax2.set_ylim(0, 105)

    ax.set_xlabel("Stan wody H [cm]")
    ax.set_ylabel("Częstość [%]")

    if title is None:
        title = "Rozkład stanów wody — częstość i czas trwania"
    ax.set_title(title)

    # Combined legend from both axes
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right", framealpha=0.9)

    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig
