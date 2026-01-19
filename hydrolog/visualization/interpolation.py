"""Precipitation interpolation visualization functions.

This module provides functions for visualizing station locations
and interpolation weights.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from hydrolog.precipitation.interpolation import Station

from hydrolog.visualization.styles import (
    get_color,
    PALETTE,
)


def plot_stations_map(
    stations: list[Station],
    weights: Optional[dict[str, float]] = None,
    title: Optional[str] = None,
    show_values: bool = True,
    ax: Optional[plt.Axes] = None,
    figsize: tuple = (10, 8),
) -> plt.Figure:
    """
    Plot map of precipitation stations with optional weights.

    Parameters
    ----------
    stations : list[Station]
        List of Station objects with coordinates and precipitation.
    weights : dict[str, float], optional
        Dictionary of station_id -> weight (e.g., from Thiessen).
        If provided, marker sizes are scaled by weight.
    title : str, optional
        Plot title.
    show_values : bool, optional
        Show precipitation values as labels, by default True.
    ax : plt.Axes, optional
        Existing axes.
    figsize : tuple, optional
        Figure size, by default (10, 8).

    Returns
    -------
    plt.Figure
        Matplotlib figure.

    Examples
    --------
    >>> from hydrolog.precipitation import Station, thiessen_polygons
    >>> from hydrolog.visualization import plot_stations_map
    >>>
    >>> stations = [
    ...     Station("S1", x=0, y=0, precipitation_mm=25.0),
    ...     Station("S2", x=10, y=0, precipitation_mm=35.0),
    ...     Station("S3", x=5, y=8, precipitation_mm=30.0),
    ... ]
    >>> areas = {"S1": 15.0, "S2": 20.0, "S3": 10.0}
    >>> result = thiessen_polygons(stations, areas)
    >>> fig = plot_stations_map(stations, weights=result.station_weights)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    # Extract coordinates and values
    x_coords = [s.x for s in stations]
    y_coords = [s.y for s in stations]
    precip_values = [s.precipitation_mm for s in stations]
    station_ids = [s.station_id for s in stations]

    # Calculate marker sizes
    if weights is not None:
        # Scale by weights
        weight_values = [weights.get(s.station_id, 0.1) for s in stations]
        max_weight = max(weight_values) if weight_values else 1
        sizes = [300 + 500 * (w / max_weight) for w in weight_values]
    else:
        # Scale by precipitation value
        max_precip = max(precip_values) if precip_values else 1
        sizes = [100 + 300 * (p / max_precip) for p in precip_values]

    # Color by precipitation value
    scatter = ax.scatter(
        x_coords,
        y_coords,
        c=precip_values,
        s=sizes,
        cmap="Blues",
        edgecolors="black",
        linewidths=1.5,
        alpha=0.8,
        vmin=0,
    )

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, label="Opad [mm]", pad=0.02)

    # Add labels
    if show_values:
        for i, (x, y, precip, sid) in enumerate(zip(x_coords, y_coords, precip_values, station_ids)):
            # Station ID above marker
            ax.annotate(
                sid,
                xy=(x, y),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

            # Precipitation value below marker
            label_text = f"{precip:.1f} mm"
            if weights is not None:
                w = weights.get(sid, 0)
                label_text += f"\n(w={w:.2f})"

            ax.annotate(
                label_text,
                xy=(x, y),
                xytext=(0, -15),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=9,
            )

    # Labels
    ax.set_xlabel("X [jednostki]")
    ax.set_ylabel("Y [jednostki]")

    if title is None:
        mean_precip = np.mean(precip_values)
        title = f"Stacje opadowe (n = {len(stations)}, średnia = {mean_precip:.1f} mm)"
    ax.set_title(title, fontsize=12)

    # Format
    margin = 0.1 * (max(x_coords) - min(x_coords) + 1)
    ax.set_xlim(min(x_coords) - margin, max(x_coords) + margin)
    ax.set_ylim(min(y_coords) - margin, max(y_coords) + margin)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig
