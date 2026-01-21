"""Stream network visualization functions.

This module provides functions for visualizing stream network statistics
and ordering results.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from hydrolog.network.stream_order import NetworkStatistics

from hydrolog.visualization.styles import (
    get_color,
    get_label,
    PALETTE,
)


def plot_stream_order_stats(
    stats: NetworkStatistics,
    title: Optional[str] = None,
    figsize: tuple = (14, 5),
) -> plt.Figure:
    """
    Plot comprehensive stream network statistics.

    Creates a three-panel figure showing:
    1. Number of segments by stream order
    2. Mean length by stream order
    3. Bifurcation and length ratios

    Parameters
    ----------
    stats : NetworkStatistics
        Network statistics from StreamNetwork.get_statistics().
    title : str, optional
        Overall figure title.
    figsize : tuple, optional
        Figure size, by default (14, 5).

    Returns
    -------
    plt.Figure
        Matplotlib figure with three subplots.

    Examples
    --------
    >>> from hydrolog.network import StreamNetwork
    >>> from hydrolog.visualization import plot_stream_order_stats
    >>>
    >>> network = StreamNetwork(segments, area_km2=100)
    >>> network.classify()
    >>> stats = network.get_statistics()
    >>> fig = plot_stream_order_stats(stats)
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)

    orders = sorted(stats.segment_counts.keys())
    x = np.arange(len(orders))

    # Panel 1: Segment counts
    ax1 = axes[0]
    counts = [stats.segment_counts[o] for o in orders]
    bars1 = ax1.bar(x, counts, color=get_color("stream"), edgecolor="white", alpha=0.8)

    ax1.set_xlabel(get_label("stream_order"))
    ax1.set_ylabel(get_label("segment_count"))
    ax1.set_title("Liczba segmentów")
    ax1.set_xticks(x)
    ax1.set_xticklabels(orders)

    # Add count labels on bars
    for bar, count in zip(bars1, counts):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            str(count),
            ha="center",
            va="bottom",
            fontsize=10,
        )

    # Panel 2: Mean lengths
    ax2 = axes[1]
    lengths = [stats.mean_lengths_km.get(o, 0) for o in orders]
    bars2 = ax2.bar(x, lengths, color=PALETTE[1], edgecolor="white", alpha=0.8)

    ax2.set_xlabel(get_label("stream_order"))
    ax2.set_ylabel(get_label("stream_length"))
    ax2.set_title("Średnia długość segmentu")
    ax2.set_xticks(x)
    ax2.set_xticklabels(orders)

    # Add length labels on bars
    for bar, length in zip(bars2, lengths):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{length:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    # Panel 3: Ratios
    ax3 = axes[2]

    # Bifurcation ratios
    if stats.bifurcation_ratios:
        rb_orders = sorted(stats.bifurcation_ratios.keys())
        rb_values = [stats.bifurcation_ratios[o] for o in rb_orders]
        rb_x = np.arange(len(rb_orders))

        ax3.plot(
            rb_x,
            rb_values,
            "o-",
            color=PALETTE[2],
            linewidth=2,
            markersize=8,
            label=f"Rb (śr. = {np.mean(rb_values):.2f})",
        )
        ax3.set_xticks(rb_x)
        ax3.set_xticklabels([f"{o}/{o+1}" for o in rb_orders])

    # Length ratios
    if stats.length_ratios:
        rl_orders = sorted(stats.length_ratios.keys())
        rl_values = [stats.length_ratios[o] for o in rl_orders]
        rl_x = np.arange(len(rl_orders))

        ax3.plot(
            rl_x,
            rl_values,
            "s--",
            color=PALETTE[3],
            linewidth=2,
            markersize=8,
            label=f"Rl (śr. = {np.mean(rl_values):.2f})",
        )

    ax3.set_xlabel("Stosunek rzędów")
    ax3.set_ylabel("Wartość współczynnika")
    ax3.set_title("Współczynniki Rb i Rl")
    ax3.legend(loc="upper right")
    ax3.grid(True, alpha=0.3)

    # Overall title
    if title is None:
        title = f"Statystyki sieci rzecznej (rząd max. = {stats.max_order})"
    fig.suptitle(title, fontsize=13, fontweight="bold", y=1.02)

    fig.tight_layout()
    return fig


def plot_bifurcation_ratios(
    stats: NetworkStatistics,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (8, 6),
) -> plt.Figure:
    """
    Plot bifurcation ratios by stream order.

    Parameters
    ----------
    stats : NetworkStatistics
        Network statistics.
    title : str, optional
        Plot title.
    ax : plt.Axes, optional
        Existing axes.
    figsize : tuple, optional
        Figure size, by default (8, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    if not stats.bifurcation_ratios:
        ax.text(
            0.5,
            0.5,
            "Brak danych o współczynnikach bifurkacji",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        return fig

    orders = sorted(stats.bifurcation_ratios.keys())
    values = [stats.bifurcation_ratios[o] for o in orders]
    x = np.arange(len(orders))

    # Bar plot
    bars = ax.bar(x, values, color=PALETTE[2], edgecolor="white", alpha=0.8)

    # Mean line
    mean_rb = np.mean(values)
    ax.axhline(mean_rb, color="red", linestyle="--", linewidth=2, label=f"Średnia Rb = {mean_rb:.2f}")

    # Reference range (typical: 3-5)
    ax.axhspan(3, 5, alpha=0.1, color="green", label="Zakres typowy (3-5)")

    # Labels
    ax.set_xlabel("Stosunek rzędów")
    ax.set_ylabel(get_label("bifurcation_ratio"))
    ax.set_xticks(x)
    ax.set_xticklabels([f"{o}/{o+1}" for o in orders])

    if title is None:
        title = "Współczynniki bifurkacji Rb"
    ax.set_title(title, fontsize=12)

    ax.legend(loc="upper right", framealpha=0.9)
    ax.set_ylim(0, max(values) * 1.3)

    # Add value labels
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    fig.tight_layout()
    return fig
