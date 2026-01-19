"""Visualization module for Hydrolog.

This module provides plotting functions for hydrological data visualization,
including hietograms, hydrographs, unit hydrographs, and combined plots.

Requirements
------------
This module requires matplotlib and seaborn (optional dependencies).
Install with: pip install hydrolog[visualization]

Examples
--------
>>> from hydrolog.visualization import plot_rainfall_runoff, setup_hydrolog_style
>>> setup_hydrolog_style()
>>> fig = plot_rainfall_runoff(hietogram, hydrograph)
>>> fig.savefig('output.png')
"""

# Check for required dependencies
try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import seaborn as sns

    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


def _check_visualization_deps() -> None:
    """Check if visualization dependencies are installed."""
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "Moduł visualization wymaga matplotlib. "
            "Zainstaluj: pip install hydrolog[visualization]"
        )


# Only import submodules if matplotlib is available
if HAS_MATPLOTLIB:
    from hydrolog.visualization.styles import (
        COLORS,
        LABELS_PL,
        PALETTE,
        add_peak_annotation,
        add_stats_box,
        add_watermark,
        format_time_axis,
        get_color,
        get_label,
        setup_hydrolog_style,
    )

    from hydrolog.visualization.hietogram import (
        plot_hietogram,
        plot_hietogram_comparison,
    )

    from hydrolog.visualization.hydrograph import (
        plot_hydrograph,
        plot_unit_hydrograph,
    )

    from hydrolog.visualization.combined import (
        plot_rainfall_runoff,
        plot_generator_result,
    )

    from hydrolog.visualization.unit_hydrograph import (
        plot_uh_comparison,
    )

    from hydrolog.visualization.water_balance import (
        plot_water_balance,
        plot_cn_curve,
    )

    from hydrolog.visualization.morphometry import (
        plot_hypsometric_curve,
        plot_elevation_histogram,
    )

    from hydrolog.visualization.network import (
        plot_stream_order_stats,
        plot_bifurcation_ratios,
    )

    from hydrolog.visualization.interpolation import (
        plot_stations_map,
    )

    __all__ = [
        # Styles
        "setup_hydrolog_style",
        "COLORS",
        "LABELS_PL",
        "PALETTE",
        "get_color",
        "get_label",
        "add_watermark",
        "add_peak_annotation",
        "add_stats_box",
        "format_time_axis",
        # Hietogram
        "plot_hietogram",
        "plot_hietogram_comparison",
        # Hydrograph
        "plot_hydrograph",
        "plot_unit_hydrograph",
        # Combined
        "plot_rainfall_runoff",
        "plot_generator_result",
        # Unit Hydrograph comparison
        "plot_uh_comparison",
        # Water balance
        "plot_water_balance",
        "plot_cn_curve",
        # Morphometry
        "plot_hypsometric_curve",
        "plot_elevation_histogram",
        # Network
        "plot_stream_order_stats",
        "plot_bifurcation_ratios",
        # Interpolation
        "plot_stations_map",
    ]
else:
    __all__ = []

    def __getattr__(name: str):
        """Raise helpful error when matplotlib is not installed."""
        _check_visualization_deps()
