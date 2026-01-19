"""Shared styles, colors, and labels for Hydrolog visualizations.

This module provides consistent styling across all visualization functions,
including color palettes, Polish labels, and matplotlib/seaborn configuration.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

try:
    import seaborn as sns

    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


# =============================================================================
# Color Palettes
# =============================================================================

COLORS = {
    # Precipitation
    "precipitation": "#1f77b4",  # blue
    "effective_precip": "#2ca02c",  # green
    "cumulative": "#ff7f0e",  # orange
    "infiltration": "#8c564b",  # brown
    # Discharge
    "discharge": "#d62728",  # red
    "baseflow": "#9467bd",  # purple
    # Unit Hydrograph models
    "scs": "#1f77b4",  # blue
    "nash": "#ff7f0e",  # orange
    "clark": "#2ca02c",  # green
    "snyder": "#d62728",  # red
    # Morphometry
    "hypsometric": "#17becf",  # cyan
    "elevation": "#bcbd22",  # olive
    # Network
    "stream": "#1f77b4",  # blue
    "watershed": "#7f7f7f",  # gray
}

# Color palette for multiple series
PALETTE = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


# =============================================================================
# Polish Labels (default)
# =============================================================================

LABELS_PL = {
    # Time
    "time_min": "Czas [min]",
    "time_h": "Czas [h]",
    # Precipitation
    "precipitation": "Opad [mm]",
    "precipitation_total": "Opad całkowity P [mm]",
    "precipitation_effective": "Opad efektywny Pe [mm]",
    "intensity": "Natężenie [mm/h]",
    "intensity_mm": "Natężenie [mm/krok]",
    "cumulative": "Suma kumulatywna [mm]",
    # Discharge
    "discharge": "Przepływ [m³/s]",
    "discharge_unit": "Przepływ [m³/s/mm]",
    "peak_discharge": "Przepływ szczytowy Qmax",
    "volume": "Objętość [m³]",
    # Morphometry
    "elevation": "Wysokość [m n.p.m.]",
    "relative_area": "Względna powierzchnia a/A [-]",
    "relative_height": "Względna wysokość h/H [-]",
    "hypsometric_integral": "Całka hipsograficzna HI",
    # Network
    "stream_order": "Rząd cieku",
    "segment_count": "Liczba segmentów",
    "stream_length": "Długość [km]",
    "bifurcation_ratio": "Współczynnik bifurkacji Rb",
    # Water balance
    "retention": "Retencja maksymalna S [mm]",
    "initial_abstraction": "Abstrakcja początkowa Ia [mm]",
    "runoff_coefficient": "Współczynnik odpływu C [-]",
}


# =============================================================================
# Style Configuration
# =============================================================================


def setup_hydrolog_style() -> None:
    """
    Set up global matplotlib/seaborn style for Hydrolog plots.

    This function configures:
    - Seaborn whitegrid theme (if available)
    - Figure size and DPI
    - Font sizes
    - Grid appearance
    - Line widths

    Call this at the start of your script for consistent styling.

    Examples
    --------
    >>> from hydrolog.visualization import setup_hydrolog_style
    >>> setup_hydrolog_style()
    """
    if HAS_SEABORN:
        sns.set_theme(style="whitegrid", palette="colorblind")

    plt.rcParams.update(
        {
            # Figure
            "figure.figsize": (10, 6),
            "figure.dpi": 100,
            "figure.facecolor": "white",
            # Font
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            # Grid
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "-",
            # Lines
            "lines.linewidth": 1.5,
            "lines.markersize": 6,
            # Axes
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def get_label(key: str) -> str:
    """
    Get Polish label for a given key.

    Parameters
    ----------
    key : str
        Label key (e.g., 'time_min', 'discharge').

    Returns
    -------
    str
        Polish label text.

    Examples
    --------
    >>> get_label('discharge')
    'Przepływ [m³/s]'
    """
    return LABELS_PL.get(key, key)


def get_color(key: str) -> str:
    """
    Get color for a given element type.

    Parameters
    ----------
    key : str
        Color key (e.g., 'precipitation', 'discharge', 'nash').

    Returns
    -------
    str
        Hex color code.

    Examples
    --------
    >>> get_color('precipitation')
    '#1f77b4'
    """
    return COLORS.get(key, "#333333")


# =============================================================================
# Axis Formatting
# =============================================================================


def format_time_axis(
    ax: plt.Axes,
    unit: str = "min",
    max_time: Optional[float] = None,
) -> None:
    """
    Format time axis with appropriate label and ticks.

    Parameters
    ----------
    ax : plt.Axes
        Matplotlib axes to format.
    unit : str, optional
        Time unit ('min' or 'h'), by default 'min'.
    max_time : float, optional
        Maximum time value for tick spacing.
    """
    label_key = f"time_{unit}"
    ax.set_xlabel(get_label(label_key))

    if max_time is not None:
        # Set reasonable tick spacing
        if unit == "min":
            if max_time <= 60:
                ax.xaxis.set_major_locator(plt.MultipleLocator(10))
            elif max_time <= 180:
                ax.xaxis.set_major_locator(plt.MultipleLocator(30))
            elif max_time <= 360:
                ax.xaxis.set_major_locator(plt.MultipleLocator(60))
            else:
                ax.xaxis.set_major_locator(plt.MultipleLocator(120))
        elif unit == "h":
            if max_time <= 6:
                ax.xaxis.set_major_locator(plt.MultipleLocator(1))
            elif max_time <= 24:
                ax.xaxis.set_major_locator(plt.MultipleLocator(3))
            else:
                ax.xaxis.set_major_locator(plt.MultipleLocator(6))


def add_peak_annotation(
    ax: plt.Axes,
    x: float,
    y: float,
    label: str = "Qmax",
    offset: tuple = (10, 10),
) -> None:
    """
    Add annotation for peak value on plot.

    Parameters
    ----------
    ax : plt.Axes
        Matplotlib axes.
    x : float
        X coordinate of peak.
    y : float
        Y coordinate of peak.
    label : str, optional
        Label text, by default 'Qmax'.
    offset : tuple, optional
        Text offset in points, by default (10, 10).
    """
    ax.annotate(
        f"{label} = {y:.2f}",
        xy=(x, y),
        xytext=offset,
        textcoords="offset points",
        fontsize=10,
        ha="left",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2"),
    )


def add_watermark(
    fig: plt.Figure,
    text: str = "Hydrolog",
    alpha: float = 0.1,
) -> None:
    """
    Add watermark text to figure.

    Parameters
    ----------
    fig : plt.Figure
        Matplotlib figure.
    text : str, optional
        Watermark text, by default 'Hydrolog'.
    alpha : float, optional
        Text transparency, by default 0.1.
    """
    fig.text(
        0.5,
        0.5,
        text,
        fontsize=60,
        color="gray",
        alpha=alpha,
        ha="center",
        va="center",
        rotation=30,
        transform=fig.transFigure,
        zorder=0,
    )


# =============================================================================
# Legend Helpers
# =============================================================================


def create_stats_text(
    stats: dict,
    title: Optional[str] = None,
) -> str:
    """
    Create formatted text for statistics display.

    Parameters
    ----------
    stats : dict
        Dictionary of statistic names and values.
    title : str, optional
        Title for the stats box.

    Returns
    -------
    str
        Formatted multi-line text.

    Examples
    --------
    >>> stats = {'Qmax': 12.5, 'tp': 90, 'V': 45000}
    >>> print(create_stats_text(stats))
    Qmax = 12.50
    tp = 90
    V = 45000
    """
    lines = []
    if title:
        lines.append(title)
        lines.append("-" * len(title))

    for key, value in stats.items():
        if isinstance(value, float):
            if abs(value) >= 1000:
                lines.append(f"{key} = {value:,.0f}")
            elif abs(value) >= 1:
                lines.append(f"{key} = {value:.2f}")
            else:
                lines.append(f"{key} = {value:.4f}")
        else:
            lines.append(f"{key} = {value}")

    return "\n".join(lines)


def add_stats_box(
    ax: plt.Axes,
    stats: dict,
    loc: str = "upper right",
    title: Optional[str] = None,
) -> None:
    """
    Add statistics text box to axes.

    Parameters
    ----------
    ax : plt.Axes
        Matplotlib axes.
    stats : dict
        Dictionary of statistics.
    loc : str, optional
        Location ('upper right', 'upper left', etc.), by default 'upper right'.
    title : str, optional
        Title for the stats box.
    """
    text = create_stats_text(stats, title)

    # Convert location string to coordinates
    loc_map = {
        "upper right": (0.98, 0.98, "right", "top"),
        "upper left": (0.02, 0.98, "left", "top"),
        "lower right": (0.98, 0.02, "right", "bottom"),
        "lower left": (0.02, 0.02, "left", "bottom"),
    }

    x, y, ha, va = loc_map.get(loc, (0.98, 0.98, "right", "top"))

    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment=va,
        horizontalalignment=ha,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
        family="monospace",
    )
