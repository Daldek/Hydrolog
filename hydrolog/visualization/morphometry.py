"""Morphometry visualization functions.

This module provides functions for visualizing hypsometric curves
and elevation distributions.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from hydrolog.morphometry.hypsometry import HypsometricResult

from hydrolog.visualization.styles import (
    get_color,
    get_label,
    add_stats_box,
)


def plot_hypsometric_curve(
    result: HypsometricResult,
    show_integral: bool = True,
    show_reference: bool = True,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (8, 8),
) -> plt.Figure:
    """
    Plot hypsometric curve (h/H vs a/A).

    The hypsometric curve shows the distribution of elevation within
    a watershed. The hypsometric integral (HI) indicates the erosional
    stage of the landscape.

    Parameters
    ----------
    result : HypsometricResult
        Result from HypsometricCurve.analyze().
    show_integral : bool, optional
        Show hypsometric integral as filled area, by default True.
    show_reference : bool, optional
        Show reference curves for young/mature/old stages, by default True.
    title : str, optional
        Plot title.
    ax : plt.Axes, optional
        Existing axes.
    figsize : tuple, optional
        Figure size, by default (8, 8).

    Returns
    -------
    plt.Figure
        Matplotlib figure.

    Examples
    --------
    >>> from hydrolog.morphometry import HypsometricCurve
    >>> from hydrolog.visualization import plot_hypsometric_curve
    >>>
    >>> hypso = HypsometricCurve(elevations)
    >>> result = hypso.analyze()
    >>> fig = plot_hypsometric_curve(result)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    # Extract data
    rel_area = result.relative_areas
    rel_height = result.relative_heights
    HI = result.hypsometric_integral

    # Plot hypsometric curve
    color = get_color("hypsometric")
    ax.plot(rel_area, rel_height, color=color, linewidth=2.5, label="Krzywa hipsograficzna")

    # Fill area under curve (hypsometric integral)
    if show_integral:
        ax.fill_between(rel_area, rel_height, alpha=0.3, color=color)

        # Add HI annotation
        ax.annotate(
            f"HI = {HI:.3f}",
            xy=(0.5, 0.5),
            fontsize=14,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

    # Reference curves for interpretation
    if show_reference:
        x = np.linspace(0, 1, 100)

        # Young/convex (HI > 0.6) - example: y = (1-x)^0.3
        y_young = (1 - x) ** 0.3
        ax.plot(x, y_young, "--", color="green", alpha=0.5, linewidth=1, label="Młoda (HI > 0.6)")

        # Old/concave (HI < 0.4) - example: y = (1-x)^3
        y_old = (1 - x) ** 3
        ax.plot(x, y_old, "--", color="red", alpha=0.5, linewidth=1, label="Stara (HI < 0.4)")

    # Diagonal reference line
    ax.plot([0, 1], [1, 0], ":", color="gray", linewidth=1, alpha=0.5)

    # Labels
    ax.set_xlabel(get_label("relative_area"))
    ax.set_ylabel(get_label("relative_height"))

    if title is None:
        # Interpret stage
        if HI > 0.6:
            stage = "młoda (wypukła)"
        elif HI < 0.4:
            stage = "stara (wklęsła)"
        else:
            stage = "dojrzała"
        title = f"Krzywa hipsograficzna (HI = {HI:.3f}, faza: {stage})"

    ax.set_title(title, fontsize=12)

    # Format
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    # Stats box
    stats = {
        "HI": f"{HI:.3f}",
        "H_śr": f"{result.elevation_mean_m:.1f} m",
        "H_med": f"{result.elevation_median_m:.1f} m",
    }
    add_stats_box(ax, stats, loc="lower left")

    fig.tight_layout()
    return fig


def plot_elevation_histogram(
    elevations: NDArray[np.float64],
    bins: int = 20,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """
    Plot histogram of elevation distribution.

    Parameters
    ----------
    elevations : NDArray
        Array of elevation values [m a.s.l.].
    bins : int, optional
        Number of histogram bins, by default 20.
    title : str, optional
        Plot title.
    ax : plt.Axes, optional
        Existing axes.
    figsize : tuple, optional
        Figure size, by default (10, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure.

    Examples
    --------
    >>> from hydrolog.visualization import plot_elevation_histogram
    >>> fig = plot_elevation_histogram(dem_elevations, bins=25)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    elevations = np.asarray(elevations)

    # Plot histogram
    color = get_color("elevation")
    n, bins_edges, patches = ax.hist(
        elevations,
        bins=bins,
        color=color,
        edgecolor="white",
        linewidth=0.5,
        alpha=0.8,
    )

    # Add statistics lines
    mean_elev = np.mean(elevations)
    median_elev = np.median(elevations)

    ax.axvline(mean_elev, color="red", linestyle="--", linewidth=2, label=f"Średnia = {mean_elev:.1f} m")
    ax.axvline(
        median_elev, color="orange", linestyle="-.", linewidth=2, label=f"Mediana = {median_elev:.1f} m"
    )

    # Labels
    ax.set_xlabel(get_label("elevation"))
    ax.set_ylabel("Częstość")

    if title is None:
        title = f"Rozkład wysokości (n = {len(elevations):,})"
    ax.set_title(title, fontsize=12)

    ax.legend(loc="upper right", framealpha=0.9)

    # Stats box
    stats = {
        "Min": f"{np.min(elevations):.1f} m",
        "Max": f"{np.max(elevations):.1f} m",
        "Średnia": f"{mean_elev:.1f} m",
        "Std": f"{np.std(elevations):.1f} m",
    }
    add_stats_box(ax, stats, loc="upper left")

    fig.tight_layout()
    return fig
