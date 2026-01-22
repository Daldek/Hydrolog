"""Hydrograph visualization functions.

This module provides functions for plotting discharge hydrographs
and unit hydrographs.
"""

from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np

from hydrolog.runoff.convolution import HydrographResult
from hydrolog.runoff.unit_hydrograph import UnitHydrographResult
from hydrolog.runoff.nash_iuh import NashUHResult, IUHResult
from hydrolog.runoff.clark_iuh import ClarkUHResult, ClarkIUHResult
from hydrolog.runoff.snyder_uh import SnyderUHResult

from hydrolog.visualization.styles import (
    get_color,
    get_label,
    format_time_axis,
    add_peak_annotation,
    add_stats_box,
)


# Type alias for all UH result types
UHResultType = Union[
    UnitHydrographResult,
    NashUHResult,
    ClarkUHResult,
    SnyderUHResult,
    IUHResult,
    ClarkIUHResult,
]


def plot_hydrograph(
    result: HydrographResult,
    show_peak: bool = True,
    show_volume: bool = True,
    fill: bool = True,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """
    Plot discharge hydrograph Q(t).

    Parameters
    ----------
    result : HydrographResult
        Hydrograph result from convolution or generator.
    show_peak : bool, optional
        Annotate peak discharge, by default True.
    show_volume : bool, optional
        Show total volume in stats box, by default True.
    fill : bool, optional
        Fill area under curve, by default True.
    title : str, optional
        Plot title. If None, auto-generated.
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
    >>> from hydrolog.visualization import plot_hydrograph
    >>> fig = plot_hydrograph(result.hydrograph, title="Hydrogram odpływu")
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    times = result.times_min
    discharge = result.discharge_m3s

    # Plot line
    line_color = get_color("discharge")
    ax.plot(
        times,
        discharge,
        color=line_color,
        linewidth=2,
        label="Przepływ Q(t)",
    )

    # Fill under curve
    if fill:
        ax.fill_between(times, discharge, alpha=0.3, color=line_color)

    # Peak marker (no annotation text)
    if show_peak:
        peak_idx = np.argmax(discharge)
        peak_time = times[peak_idx]
        peak_q = discharge[peak_idx]
        ax.plot(peak_time, peak_q, "o", color=line_color, markersize=8)

    # Stats box
    if show_volume:
        stats = {
            "Qmax": f"{result.peak_discharge_m3s:.2f} m³/s",
            "tp": f"{result.time_to_peak_min:.0f} min",
            "V": f"{result.total_volume_m3:,.0f} m³",
        }
        add_stats_box(ax, stats, loc="upper right")

    # Labels
    ax.set_xlabel(get_label("time_min"))
    ax.set_ylabel(get_label("discharge"))

    if title is None:
        title = "Hydrogram odpływu"
    ax.set_title(title)

    # Format
    ax.set_xlim(0, result.duration_min)
    ax.set_ylim(0, result.peak_discharge_m3s * 1.2)
    format_time_axis(ax, "min", result.duration_min)

    fig.tight_layout()
    return fig


def plot_unit_hydrograph(
    result: UHResultType,
    show_params: bool = True,
    fill: bool = True,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
    color: Optional[str] = None,
    label: Optional[str] = None,
) -> plt.Figure:
    """
    Plot unit hydrograph [m³/s/mm] or IUH [1/min].

    Parameters
    ----------
    result : UHResultType
        Unit hydrograph result (SCS, Nash, Clark, or Snyder).
    show_params : bool, optional
        Show parameters in stats box, by default True.
    fill : bool, optional
        Fill area under curve, by default True.
    title : str, optional
        Plot title.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (10, 6).
    color : str, optional
        Line color. If None, uses default.
    label : str, optional
        Legend label.

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.runoff import NashIUH
    >>> from hydrolog.visualization import plot_unit_hydrograph
    >>>
    >>> nash = NashIUH(n=3, k_min=30, area_km2=45)
    >>> result = nash.generate(timestep_min=5)
    >>> fig = plot_unit_hydrograph(result, title="Nash UH")
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    # Extract data based on result type
    times = result.times_min

    # Determine if this is IUH (dimensionless) or UH (dimensional)
    is_iuh = isinstance(result, (IUHResult, ClarkIUHResult))

    if is_iuh:
        ordinates = result.ordinates_per_min
        ylabel = "Rzędne IUH [1/min]"
        peak_value = result.peak_ordinate_per_min
    else:
        ordinates = result.ordinates_m3s
        ylabel = get_label("discharge_unit")
        peak_value = result.peak_discharge_m3s

    # Determine color
    if color is None:
        if isinstance(result, (NashUHResult, IUHResult)):
            color = get_color("nash")
        elif isinstance(result, (ClarkUHResult, ClarkIUHResult)):
            color = get_color("clark")
        elif isinstance(result, SnyderUHResult):
            color = get_color("snyder")
        else:
            color = get_color("scs")

    # Plot
    if label is None:
        label = "Hydrogram jednostkowy"

    ax.plot(times, ordinates, color=color, linewidth=2, label=label)

    if fill:
        ax.fill_between(times, ordinates, alpha=0.3, color=color)

    # Mark peak
    peak_idx = np.argmax(ordinates)
    ax.plot(times[peak_idx], ordinates[peak_idx], "o", color=color, markersize=8)

    # Stats box
    if show_params:
        stats = _get_uh_stats(result, is_iuh)
        add_stats_box(ax, stats, loc="upper right")

    # Labels
    ax.set_xlabel(get_label("time_min"))
    ax.set_ylabel(ylabel)

    if title is None:
        title = _get_uh_title(result)
    ax.set_title(title)

    # Format
    max_time = times[-1]
    ax.set_xlim(0, max_time)
    ax.set_ylim(0, peak_value * 1.2)
    format_time_axis(ax, "min", max_time)

    fig.tight_layout()
    return fig


def _get_uh_stats(result: UHResultType, is_iuh: bool) -> dict:
    """Extract statistics from UH result for display."""
    stats = {}

    if is_iuh:
        stats["up"] = f"{result.peak_ordinate_per_min:.4f} 1/min"
    else:
        stats["Qp"] = f"{result.peak_discharge_m3s:.3f} m³/s/mm"

    stats["tp"] = f"{result.time_to_peak_min:.1f} min"

    # Model-specific parameters
    if isinstance(result, (NashUHResult, IUHResult)):
        stats["n"] = f"{result.n:.2f}"
        stats["K"] = f"{result.k_min:.1f} min"
    elif isinstance(result, (ClarkUHResult, ClarkIUHResult)):
        stats["Tc"] = f"{result.tc_min:.1f} min"
        stats["R"] = f"{result.r_min:.1f} min"
    elif isinstance(result, SnyderUHResult):
        stats["tL"] = f"{result.lag_time_min:.1f} min"
        stats["tb"] = f"{result.time_base_min:.0f} min"

    return stats


def _get_uh_title(result: UHResultType) -> str:
    """Generate title based on UH type."""
    if isinstance(result, (NashUHResult, IUHResult)):
        return f"Hydrogram jednostkowy Nash (n={result.n:.2f}, K={result.k_min:.1f} min)"
    elif isinstance(result, (ClarkUHResult, ClarkIUHResult)):
        return f"Hydrogram jednostkowy Clark (Tc={result.tc_min:.1f}, R={result.r_min:.1f} min)"
    elif isinstance(result, SnyderUHResult):
        return f"Hydrogram jednostkowy Snyder (tL={result.lag_time_min:.0f} min)"
    elif isinstance(result, UnitHydrographResult):
        return f"Hydrogram jednostkowy SCS (tp={result.time_to_peak_min:.0f} min)"
    else:
        return "Hydrogram jednostkowy"
