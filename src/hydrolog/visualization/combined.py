"""Combined rainfall-runoff visualization functions.

This module provides the classic combined plot with hietogram on top
(bars pointing down) and hydrograph on bottom.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from numpy.typing import NDArray

from hydrolog.precipitation.hietogram import HietogramResult
from hydrolog.runoff.convolution import HydrographResult
from hydrolog.visualization.styles import (
    add_stats_box,
    format_time_axis,
    get_color,
    get_label,
)


def plot_rainfall_runoff(
    hietogram: HietogramResult,
    hydrograph: HydrographResult,
    effective_precip: NDArray[np.float64] | list[float] | None = None,
    title: str | None = None,
    figsize: tuple[float, float] = (12, 8),
    height_ratios: tuple[float, float] = (1, 2),
) -> Figure:
    """
    Create classic rainfall-runoff plot with hietogram above and hydrograph below.

    The hietogram bars point downward (inverted Y-axis) following hydrological
    convention. The hydrograph is shown below with normal orientation.

    Layout:
    ┌─────────────────────────┐
    │  Hietogram (bars ↓)     │  <- top, inverted Y-axis
    │  P [mm]                 │
    ├─────────────────────────┤
    │  Hydrograph             │  <- bottom
    │  Q [m³/s]               │
    └─────────────────────────┘

    Parameters
    ----------
    hietogram : HietogramResult
        Precipitation hietogram result.
    hydrograph : HydrographResult
        Discharge hydrograph result.
    effective_precip : NDArray or list, optional
        Effective precipitation values [mm] to overlay on hietogram.
    title : str, optional
        Overall figure title.
    figsize : tuple[float, float], optional
        Figure size (width, height), by default (12, 8).
    height_ratios : tuple[float, float], optional
        Height ratio between panels (hietogram, hydrograph), by default (1, 2).

    Returns
    -------
    plt.Figure
        Matplotlib figure with two subplots.

    Examples
    --------
    >>> from hydrolog.runoff import HydrographGenerator
    >>> from hydrolog.precipitation import BetaHietogram
    >>> from hydrolog.visualization import plot_rainfall_runoff
    >>>
    >>> hietogram = BetaHietogram(alpha=2, beta=5)
    >>> precip = hietogram.generate(total_mm=50, duration_min=120, timestep_min=10)
    >>>
    >>> generator = HydrographGenerator(area_km2=45, cn=72, tc_min=90)
    >>> result = generator.generate(precip)
    >>>
    >>> fig = plot_rainfall_runoff(
    ...     precip,
    ...     result.hydrograph,
    ...     effective_precip=result.effective_precip_mm,
    ...     title="Zlewnia Potok - epizod opadowy"
    ... )
    >>> fig.savefig("rainfall_runoff.png", dpi=150)
    """
    # Create figure with gridspec for different panel heights
    fig, (ax_precip, ax_discharge) = plt.subplots(
        2,
        1,
        figsize=figsize,
        sharex=True,
        gridspec_kw={"height_ratios": height_ratios, "hspace": 0.05},
    )

    # =========================================================================
    # Top panel: Hietogram (inverted)
    # =========================================================================
    times = hietogram.times_min
    timestep = hietogram.timestep_min
    bar_positions = times - timestep / 2
    bar_width = timestep * 0.9

    # Total precipitation bars
    ax_precip.bar(
        bar_positions,
        hietogram.intensities_mm,
        width=bar_width,
        color=get_color("precipitation"),
        edgecolor="white",
        linewidth=0.5,
        alpha=0.6,
        label=f"Opad P = {hietogram.total_mm:.1f} mm",
    )

    # Effective precipitation overlay
    if effective_precip is not None:
        effective_precip = np.asarray(effective_precip)
        effective_sum = float(np.sum(effective_precip))
        ax_precip.bar(
            bar_positions,
            effective_precip,
            width=bar_width,
            color=get_color("effective_precip"),
            edgecolor="white",
            linewidth=0.5,
            alpha=0.9,
            label=f"Opad efektywny Pe = {effective_sum:.1f} mm",
        )

    # Invert Y-axis (bars pointing down)
    ax_precip.invert_yaxis()

    # Labels for top panel
    ax_precip.set_ylabel(get_label("precipitation"))
    ax_precip.legend(loc="lower right")

    # Remove bottom spine (shared with hydrograph)
    ax_precip.spines["bottom"].set_visible(False)
    ax_precip.tick_params(axis="x", which="both", bottom=False, labelbottom=False)

    # =========================================================================
    # Bottom panel: Hydrograph
    # =========================================================================
    discharge_times = hydrograph.times_min
    discharge = hydrograph.discharge_m3s

    # Plot discharge line with fill
    line_color = get_color("discharge")
    ax_discharge.plot(
        discharge_times,
        discharge,
        color=line_color,
        linewidth=2,
        label="Przepływ Q(t)",
    )
    ax_discharge.fill_between(discharge_times, discharge, alpha=0.3, color=line_color)

    # Mark peak
    peak_idx = np.argmax(discharge)
    peak_time = discharge_times[peak_idx]
    peak_q = discharge[peak_idx]
    ax_discharge.plot(peak_time, peak_q, "o", color=line_color, markersize=8)

    # Peak annotation
    ax_discharge.annotate(
        f"Qmax = {peak_q:.2f} m³/s\nt = {peak_time:.0f} min",
        xy=(peak_time, peak_q),
        xytext=(15, 5),
        textcoords="offset points",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.9},
        arrowprops={"arrowstyle": "->", "connectionstyle": "arc3,rad=0.2"},
    )

    # Labels for bottom panel
    ax_discharge.set_xlabel(get_label("time_min"))
    ax_discharge.set_ylabel(get_label("discharge"))

    # Stats box for hydrograph
    stats = {
        "Qmax": f"{hydrograph.peak_discharge_m3s:.2f} m³/s",
        "tp": f"{hydrograph.time_to_peak_min:.0f} min",
        "V": f"{hydrograph.total_volume_m3: .0f} m³",  # change to no commas
    }
    add_stats_box(ax_discharge, stats, loc="upper right")

    # Remove top spine
    ax_discharge.spines["top"].set_visible(False)

    # Format time axis
    max_time = max(hietogram.duration_min, hydrograph.duration_min)
    ax_discharge.set_xlim(0, max_time)
    ax_discharge.set_ylim(0, peak_q * 1.2)
    format_time_axis(ax_discharge, "min", max_time)

    # Overall title
    if title:
        fig.suptitle(title, fontsize=14, fontweight="bold", y=0.98)

    fig.tight_layout()
    return fig
