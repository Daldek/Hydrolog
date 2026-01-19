"""Water balance visualization functions.

This module provides functions for visualizing SCS-CN water balance
and runoff relationships.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from hydrolog.runoff.generator import HydrographGeneratorResult
from hydrolog.runoff.scs_cn import SCSCN, AMC

from hydrolog.visualization.styles import (
    get_color,
    get_label,
)


def plot_water_balance(
    result: HydrographGeneratorResult,
    style: str = "bars",
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """
    Visualize SCS-CN water balance components.

    Parameters
    ----------
    result : HydrographGeneratorResult
        Result from HydrographGenerator.
    style : str, optional
        Visualization style: 'bars' or 'pie', by default 'bars'.
    title : str, optional
        Plot title.
    ax : plt.Axes, optional
        Existing axes to plot on.
    figsize : tuple, optional
        Figure size, by default (10, 6).

    Returns
    -------
    plt.Figure
        Matplotlib figure.

    Examples
    --------
    >>> from hydrolog.visualization import plot_water_balance
    >>> fig = plot_water_balance(result, style='bars')
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    # Extract components
    P = result.total_precip_mm
    Pe = result.total_effective_mm
    Ia = result.initial_abstraction_mm
    F = P - Pe - Ia  # Continuing abstraction (infiltration)

    if style == "bars":
        _plot_balance_bars(ax, P, Ia, F, Pe)
    elif style == "pie":
        _plot_balance_pie(ax, P, Ia, F, Pe)
    else:
        raise ValueError(f"Unknown style: {style}. Use 'bars' or 'pie'.")

    if title is None:
        title = f"Bilans wodny SCS-CN (CN = {result.cn_used})"
    ax.set_title(title, fontsize=13, fontweight="bold")

    fig.tight_layout()
    return fig


def _plot_balance_bars(ax: plt.Axes, P: float, Ia: float, F: float, Pe: float) -> None:
    """Create stacked bar chart for water balance."""
    # Single stacked bar
    components = [Ia, F, Pe]
    labels = [
        f"Abstrakcja początkowa Ia = {Ia:.1f} mm",
        f"Infiltracja F = {F:.1f} mm",
        f"Opad efektywny Pe = {Pe:.1f} mm",
    ]
    colors = ["#8c564b", "#bcbd22", get_color("effective_precip")]

    bottom = 0
    bars = []
    for value, label, color in zip(components, labels, colors):
        bar = ax.bar(
            "Bilans",
            value,
            bottom=bottom,
            color=color,
            edgecolor="white",
            linewidth=2,
            label=label,
        )
        bars.append(bar)

        # Add value label in center of bar segment
        if value > P * 0.05:  # Only if segment is large enough
            ax.text(
                0,
                bottom + value / 2,
                f"{value:.1f}",
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color="white",
            )

        bottom += value

    # Add total P line
    ax.axhline(y=P, color="black", linestyle="--", linewidth=2, label=f"Opad P = {P:.1f} mm")

    ax.set_ylabel("Wysokość warstwy [mm]")
    ax.set_ylim(0, P * 1.1)
    ax.legend(loc="upper right", framealpha=0.9)

    # Remove x-axis label
    ax.set_xticks([])


def _plot_balance_pie(ax: plt.Axes, P: float, Ia: float, F: float, Pe: float) -> None:
    """Create pie chart for water balance."""
    values = [Ia, F, Pe]
    labels = [
        f"Ia\n{Ia:.1f} mm\n({Ia/P*100:.1f}%)",
        f"F\n{F:.1f} mm\n({F/P*100:.1f}%)",
        f"Pe\n{Pe:.1f} mm\n({Pe/P*100:.1f}%)",
    ]
    colors = ["#8c564b", "#bcbd22", get_color("effective_precip")]
    explode = (0, 0, 0.05)  # Slight explosion for Pe

    ax.pie(
        values,
        labels=labels,
        colors=colors,
        explode=explode,
        autopct="",
        startangle=90,
        wedgeprops=dict(edgecolor="white", linewidth=2),
    )

    # Add center text
    ax.text(0, 0, f"P = {P:.1f} mm", ha="center", va="center", fontsize=12, fontweight="bold")


def plot_cn_curve(
    cn: int,
    p_range: tuple = (0, 150),
    amc_variants: bool = True,
    ia_coefficient: float = 0.2,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """
    Plot P → Pe relationship for given CN value.

    Shows how total precipitation is converted to effective precipitation
    using the SCS-CN method.

    Parameters
    ----------
    cn : int
        Curve Number for AMC-II conditions.
    p_range : tuple, optional
        Range of precipitation values [mm], by default (0, 150).
    amc_variants : bool, optional
        Show curves for AMC-I, II, III, by default True.
    ia_coefficient : float, optional
        Initial abstraction coefficient (Ia = λ×S), by default 0.2.
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
    >>> from hydrolog.visualization import plot_cn_curve
    >>> fig = plot_cn_curve(cn=72, amc_variants=True)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    # Generate P values
    P = np.linspace(p_range[0], p_range[1], 200)

    # Calculate Pe for different AMC conditions
    scs = SCSCN(cn=cn, ia_coefficient=ia_coefficient)

    if amc_variants:
        conditions = [
            (AMC.I, "AMC-I (suche)", "--", 0.7),
            (AMC.II, "AMC-II (normalne)", "-", 1.0),
            (AMC.III, "AMC-III (mokre)", "-.", 0.7),
        ]
    else:
        conditions = [(AMC.II, f"CN = {cn}", "-", 1.0)]

    for amc, label, linestyle, alpha in conditions:
        Pe = []
        for p in P:
            result = scs.effective_precipitation(p, amc=amc)
            Pe.append(result.effective_mm if hasattr(result, "effective_mm") else float(result))

        Pe = np.array(Pe)

        # Get adjusted CN for label
        cn_adj = scs.adjust_cn_for_amc(amc)

        ax.plot(
            P,
            Pe,
            linestyle=linestyle,
            linewidth=2,
            alpha=alpha,
            label=f"{label} (CN={cn_adj})",
            color=get_color("effective_precip") if amc == AMC.II else None,
        )

    # Add 1:1 line (P = Pe, no losses)
    ax.plot(P, P, ":", color="gray", linewidth=1, label="P = Pe (brak strat)")

    # Labels
    ax.set_xlabel(get_label("precipitation_total"))
    ax.set_ylabel(get_label("precipitation_effective"))

    if title is None:
        title = f"Krzywa SCS-CN: opad całkowity → opad efektywny (CN = {cn})"
    ax.set_title(title, fontsize=12)

    # Format
    ax.set_xlim(p_range)
    ax.set_ylim(0, p_range[1])
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    # Add Ia threshold annotation
    S = scs.retention(cn)
    Ia = ia_coefficient * S
    ax.axvline(x=Ia, color="red", linestyle=":", alpha=0.5)
    ax.annotate(
        f"Ia = {Ia:.1f} mm",
        xy=(Ia, 0),
        xytext=(Ia + 5, p_range[1] * 0.1),
        fontsize=9,
        color="red",
    )

    fig.tight_layout()
    return fig
