"""Unit hydrograph comparison visualization.

This module provides functions for comparing multiple unit hydrograph models.
"""

from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np

from hydrolog.runoff.unit_hydrograph import UnitHydrographResult
from hydrolog.runoff.nash_iuh import NashUHResult, IUHResult
from hydrolog.runoff.clark_iuh import ClarkUHResult, ClarkIUHResult
from hydrolog.runoff.snyder_uh import SnyderUHResult

from hydrolog.visualization.styles import (
    PALETTE,
    get_color,
    get_label,
    format_time_axis,
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


def plot_uh_comparison(
    models: dict[str, UHResultType],
    title: Optional[str] = None,
    show_table: bool = True,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (12, 7),
) -> plt.Figure:
    """
    Compare multiple unit hydrograph models on a single plot.

    Parameters
    ----------
    models : dict[str, UHResultType]
        Dictionary mapping model names to their results.
        Example: {"SCS": scs_result, "Nash (n=3)": nash_result}
    title : str, optional
        Plot title, by default "Porównanie hydrogramów jednostkowych".
    show_table : bool, optional
        Show comparison table below plot, by default True.
    ax : plt.Axes, optional
        Existing axes to plot on (only for plot, not table).
    figsize : tuple, optional
        Figure size, by default (12, 7).

    Returns
    -------
    plt.Figure
        Matplotlib figure.

    Examples
    --------
    >>> from hydrolog.runoff import SCSUnitHydrograph, NashIUH, ClarkIUH, SnyderUH
    >>> from hydrolog.visualization import plot_uh_comparison
    >>>
    >>> # Generate UH results
    >>> scs = SCSUnitHydrograph(area_km2=45, tc_min=90).generate(timestep_min=10)
    >>> nash = NashIUH(n=3, k_min=30, area_km2=45).generate(timestep_min=10)
    >>> clark = ClarkIUH(tc_min=60, r_min=30, area_km2=45).generate(timestep_min=10)
    >>> snyder = SnyderUH(area_km2=45, L_km=15, Lc_km=8).generate(timestep_min=10)
    >>>
    >>> models = {
    ...     "SCS": scs,
    ...     "Nash (n=3, K=30)": nash,
    ...     "Clark (Tc=60, R=30)": clark,
    ...     "Snyder (Ct=1.5, Cp=0.6)": snyder,
    ... }
    >>> fig = plot_uh_comparison(models)
    >>> fig.savefig("uh_comparison.png")
    """
    if not models:
        raise ValueError("models dictionary cannot be empty")

    # Determine if we need table
    if show_table:
        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.15)
        ax_plot = fig.add_subplot(gs[0])
        ax_table = fig.add_subplot(gs[1])
    else:
        if ax is None:
            fig, ax_plot = plt.subplots(figsize=figsize)
        else:
            ax_plot = ax
            fig = ax.get_figure()
        ax_table = None

    # Get colors for models
    model_colors = {}
    for i, name in enumerate(models.keys()):
        # Try to get specific color based on model type
        name_lower = name.lower()
        if "scs" in name_lower:
            model_colors[name] = get_color("scs")
        elif "nash" in name_lower:
            model_colors[name] = get_color("nash")
        elif "clark" in name_lower:
            model_colors[name] = get_color("clark")
        elif "snyder" in name_lower:
            model_colors[name] = get_color("snyder")
        else:
            model_colors[name] = PALETTE[i % len(PALETTE)]

    # Plot each model
    max_time = 0
    max_q = 0

    for name, result in models.items():
        times = result.times_min

        # Get ordinates based on result type
        is_iuh = isinstance(result, (IUHResult, ClarkIUHResult))
        if is_iuh:
            ordinates = result.ordinates_per_min
        else:
            ordinates = result.ordinates_m3s

        color = model_colors[name]
        ax_plot.plot(times, ordinates, color=color, linewidth=2, label=name)

        # Track max values
        max_time = max(max_time, times[-1])
        max_q = max(max_q, np.max(ordinates))

    # Labels
    ax_plot.set_xlabel(get_label("time_min"))

    # Check if all are IUH or UH for ylabel
    all_iuh = all(isinstance(r, (IUHResult, ClarkIUHResult)) for r in models.values())
    if all_iuh:
        ax_plot.set_ylabel("Rzędne IUH [1/min]")
    else:
        ax_plot.set_ylabel(get_label("discharge_unit"))

    if title is None:
        title = "Porównanie hydrogramów jednostkowych"
    ax_plot.set_title(title, fontsize=13, fontweight="bold")

    # Legend
    ax_plot.legend(loc="upper right", framealpha=0.9)

    # Format
    ax_plot.set_xlim(0, max_time)
    ax_plot.set_ylim(0, max_q * 1.15)
    format_time_axis(ax_plot, "min", max_time)

    # =========================================================================
    # Comparison table
    # =========================================================================
    if ax_table is not None:
        ax_table.axis("off")

        # Build table data
        headers = ["Model", "tp [min]", "Qp [m³/s/mm]", "tb [min]"]
        rows = []

        for name, result in models.items():
            is_iuh = isinstance(result, (IUHResult, ClarkIUHResult))

            tp = result.time_to_peak_min

            if is_iuh:
                qp = result.peak_ordinate_per_min
                qp_str = f"{qp:.4f} [1/min]"
            else:
                qp = result.peak_discharge_m3s
                qp_str = f"{qp:.3f}"

            # Time base - varies by model
            if hasattr(result, "time_base_min"):
                tb = result.time_base_min
                tb_str = f"{tb:.0f}"
            else:
                # Estimate as time when Q < 1% of peak
                ordinates = result.ordinates_per_min if is_iuh else result.ordinates_m3s
                peak = np.max(ordinates)
                idx = np.where(ordinates > 0.01 * peak)[0]
                if len(idx) > 0:
                    tb = result.times_min[idx[-1]]
                    tb_str = f"~{tb:.0f}"
                else:
                    tb_str = "-"

            rows.append([name, f"{tp:.1f}", qp_str, tb_str])

        # Create table
        table = ax_table.table(
            cellText=rows,
            colLabels=headers,
            loc="center",
            cellLoc="center",
            colWidths=[0.35, 0.2, 0.25, 0.2],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        # Style header
        for i in range(4):
            table[(0, i)].set_facecolor("#4472C4")
            table[(0, i)].set_text_props(color="white", fontweight="bold")

        # Color code model names
        for i, name in enumerate(models.keys()):
            cell = table[(i + 1, 0)]
            cell.set_text_props(color=model_colors[name], fontweight="bold")

    fig.tight_layout()
    return fig
