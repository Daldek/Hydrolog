"""Hietogram (precipitation) visualization functions.

This module provides functions for plotting precipitation data,
including intensity bars and cumulative curves.
"""

from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from hydrolog.precipitation.hietogram import HietogramResult
from hydrolog.visualization.styles import (
    get_color,
    get_label,
    format_time_axis,
    add_stats_box,
)


def plot_hietogram(
    result: HietogramResult,
    show_cumulative: bool = True,
    distribution: Optional[str] = None,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """
    Plot hietogram with precipitation intensity and optional cumulative curve.

    Parameters
    ----------
    result : HietogramResult
        Hietogram result from any hietogram generator.
    show_cumulative : bool, optional
        Show cumulative precipitation line, by default True.
    distribution : str, optional
        Distribution name and parameters to display in subtitle
        (e.g., "Beta (α=2, β=5)").
    title : str, optional
        Plot title. If None, uses "Hietogram opadu".
    ax : plt.Axes, optional
        Existing axes to plot on. If None, creates new figure.
    figsize : tuple, optional
        Figure size if creating new figure, by default (10, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure object.

    Examples
    --------
    >>> from hydrolog.precipitation import BetaHietogram
    >>> from hydrolog.visualization import plot_hietogram
    >>>
    >>> hietogram = BetaHietogram(alpha=2, beta=5)
    >>> result = hietogram.generate(total_mm=50, duration_min=120, timestep_min=10)
    >>> fig = plot_hietogram(result, distribution="Beta (α=2, β=5)")
    >>> fig.savefig("hietogram.png")
    """
    # Create figure if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    # Prepare data
    times = result.times_min
    timestep = result.timestep_min

    # Always use intensity in mm/h
    values = result.intensity_mm_per_h
    ylabel = get_label("intensity")

    # Calculate bar positions (center of each interval)
    bar_positions = times - timestep / 2

    # Plot bars
    bars = ax.bar(
        bar_positions,
        values,
        width=timestep * 0.9,
        color=get_color("precipitation"),
        edgecolor="white",
        linewidth=0.5,
        alpha=0.8,
        label=f"Opad (P = {result.total_mm:.1f} mm)",
    )

    # Plot cumulative line on secondary axis
    if show_cumulative:
        ax2 = ax.twinx()
        cumulative = np.cumsum(result.intensities_mm)
        # Prepend 0 to start cumulative curve at (0,0)
        cum_times = np.concatenate([[0], times])
        cum_values = np.concatenate([[0], cumulative])
        ax2.plot(
            cum_times,
            cum_values,
            color=get_color("cumulative"),
            linewidth=2,
            # marker="o",
            markersize=4,
            label="Suma kumulatywna",
        )
        ax2.set_ylabel(get_label("cumulative"), color=get_color("cumulative"))
        ax2.tick_params(axis="y", labelcolor=get_color("cumulative"))
        ax2.set_ylim(0, result.total_mm * 1.1)

        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    else:
        ax.legend(loc="upper right")

    # Labels and title
    ax.set_xlabel(get_label("time_min"))
    ax.set_ylabel(ylabel)

    if title is None:
        title = "Hietogram opadu"
        if distribution:
            title += f"\nRozkład {distribution}"
    ax.set_title(title)

    # Format axes
    ax.set_xlim(0, result.duration_min)
    ax.set_ylim(0, max(values) * 1.2)
    format_time_axis(ax, "min", result.duration_min)

    fig.tight_layout()
    return fig


def plot_hietogram_comparison(
    precip: HietogramResult,
    effective: Union[NDArray[np.float64], list],
    cn: Optional[int] = None,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """
    Plot comparison of total precipitation and effective precipitation.

    Parameters
    ----------
    precip : HietogramResult
        Total precipitation hietogram.
    effective : NDArray or list
        Effective precipitation values [mm] for each timestep.
    cn : int, optional
        Curve Number value to display in legend.
    title : str, optional
        Plot title. If None, uses "Hietogram opadu".
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
    >>> from hydrolog.runoff import HydrographGenerator
    >>> from hydrolog.visualization import plot_hietogram_comparison
    >>>
    >>> result = generator.generate(precip)
    >>> fig = plot_hietogram_comparison(
    ...     precip, result.effective_precip_mm, cn=72,
    ...     title="Hietogram opadu"
    ... )
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    # Ensure effective is numpy array
    effective = np.asarray(effective)

    # Prepare data
    times = precip.times_min
    timestep = precip.timestep_min
    bar_positions = times - timestep / 2
    bar_width = timestep * 0.4

    # Convert to intensity mm/h
    conversion = 60.0 / timestep
    precip_intensity = precip.intensities_mm * conversion
    effective_intensity = effective * conversion

    # Total precipitation
    total_sum = precip.total_mm
    ax.bar(
        bar_positions - bar_width / 2,
        precip_intensity,
        width=bar_width,
        color=get_color("precipitation"),
        edgecolor="white",
        linewidth=0.5,
        alpha=0.6,
        label=f"Opad całkowity P = {total_sum:.1f} mm",
    )

    # Effective precipitation
    effective_sum = float(np.sum(effective))
    cn_label = f" (CN={cn})" if cn is not None else ""
    ax.bar(
        bar_positions + bar_width / 2,
        effective_intensity,
        width=bar_width,
        color=get_color("effective_precip"),
        edgecolor="white",
        linewidth=0.5,
        alpha=0.8,
        label=f"Opad efektywny Pe = {effective_sum:.1f} mm{cn_label}",
    )

    # Labels and title
    ax.set_xlabel(get_label("time_min"))
    ax.set_ylabel(get_label("intensity"))

    if title is None:
        title = "Hietogram opadu"
    ax.set_title(title)

    # Format
    ax.set_xlim(0, precip.duration_min)
    ax.set_ylim(0, max(precip_intensity) * 1.2)
    ax.legend(loc="upper right")
    format_time_axis(ax, "min", precip.duration_min)

    fig.tight_layout()
    return fig
