"""Tests for visualization module."""

import numpy as np
import pytest
import matplotlib

matplotlib.use("Agg")  # Non-GUI backend for testing
import matplotlib.pyplot as plt

from hydrolog.visualization import (
    # Styles
    setup_hydrolog_style,
    COLORS,
    LABELS_PL,
    PALETTE,
    get_color,
    get_label,
    add_watermark,
    add_peak_annotation,
    add_stats_box,
    format_time_axis,
    # Hietogram
    plot_hietogram,
    plot_hietogram_comparison,
    # Hydrograph
    plot_hydrograph,
    plot_unit_hydrograph,
    # Combined
    plot_rainfall_runoff,
    # Unit Hydrograph comparison
    plot_uh_comparison,
    # Water balance
    plot_cn_curve,
    # Morphometry
    plot_hypsometric_curve,
    plot_elevation_histogram,
    # Network
    plot_stream_order_stats,
    plot_bifurcation_ratios,
    # Interpolation
    plot_stations_map,
)

from hydrolog.precipitation import BetaHietogram, Station
from hydrolog.runoff import (
    HydrographGenerator,
    SCSUnitHydrograph,
    NashIUH,
    ClarkIUH,
    SnyderUH,
)
from hydrolog.morphometry import HypsometricCurve
from hydrolog.network import StreamNetwork, StreamSegment


@pytest.fixture(autouse=True)
def close_figures():
    """Close all figures after each test."""
    yield
    plt.close("all")


class TestStyles:
    """Tests for styles module."""

    def test_setup_hydrolog_style(self):
        """Test that setup_hydrolog_style doesn't raise."""
        setup_hydrolog_style()
        # Verify some rcParams were set
        assert plt.rcParams["figure.dpi"] == 100

    def test_get_color_known_key(self):
        """Test get_color with known key."""
        color = get_color("precipitation")
        assert color == "#1f77b4"

    def test_get_color_unknown_key(self):
        """Test get_color with unknown key returns default."""
        color = get_color("unknown_key")
        assert color == "#333333"

    def test_get_label_known_key(self):
        """Test get_label with known key."""
        label = get_label("discharge")
        assert label == "Przepływ [m³/s]"

    def test_get_label_unknown_key(self):
        """Test get_label with unknown key returns key."""
        label = get_label("unknown_key")
        assert label == "unknown_key"

    def test_colors_dict_not_empty(self):
        """Test COLORS dictionary is populated."""
        assert len(COLORS) > 0
        assert "precipitation" in COLORS
        assert "discharge" in COLORS

    def test_labels_dict_not_empty(self):
        """Test LABELS_PL dictionary is populated."""
        assert len(LABELS_PL) > 0
        assert "time_min" in LABELS_PL

    def test_palette_is_list(self):
        """Test PALETTE is a non-empty list."""
        assert isinstance(PALETTE, list)
        assert len(PALETTE) >= 10

    def test_format_time_axis(self):
        """Test format_time_axis function."""
        fig, ax = plt.subplots()
        format_time_axis(ax, unit="min", max_time=120)
        assert "Czas" in ax.get_xlabel()

    def test_add_peak_annotation(self):
        """Test add_peak_annotation function."""
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [0, 5, 2])
        add_peak_annotation(ax, x=1, y=5, label="Qmax")
        # Check annotation was added
        assert len(ax.texts) > 0

    def test_add_watermark(self):
        """Test add_watermark function."""
        fig, ax = plt.subplots()
        add_watermark(fig, text="Test")
        assert len(fig.texts) > 0

    def test_add_stats_box(self):
        """Test add_stats_box function."""
        fig, ax = plt.subplots()
        stats = {"Qmax": 12.5, "tp": 90}
        add_stats_box(ax, stats, loc="upper right")
        assert len(ax.texts) > 0


class TestHietogram:
    """Tests for hietogram visualization."""

    @pytest.fixture
    def hietogram_result(self):
        """Create sample hietogram result."""
        hietogram = BetaHietogram(alpha=2, beta=5)
        return hietogram.generate(total_mm=50, duration_min=120, timestep_min=10)

    def test_plot_hietogram_returns_figure(self, hietogram_result):
        """Test plot_hietogram returns a Figure."""
        fig = plot_hietogram(hietogram_result)
        assert isinstance(fig, plt.Figure)

    def test_plot_hietogram_with_cumulative(self, hietogram_result):
        """Test plot_hietogram with cumulative line."""
        fig = plot_hietogram(hietogram_result, show_cumulative=True)
        assert isinstance(fig, plt.Figure)

    def test_plot_hietogram_without_cumulative(self, hietogram_result):
        """Test plot_hietogram without cumulative line."""
        fig = plot_hietogram(hietogram_result, show_cumulative=False)
        assert isinstance(fig, plt.Figure)

    def test_plot_hietogram_custom_title(self, hietogram_result):
        """Test plot_hietogram with custom title."""
        fig = plot_hietogram(hietogram_result, title="Test Title")
        assert isinstance(fig, plt.Figure)

    def test_plot_hietogram_existing_axes(self, hietogram_result):
        """Test plot_hietogram with existing axes."""
        fig, ax = plt.subplots()
        result_fig = plot_hietogram(hietogram_result, ax=ax)
        assert result_fig is fig

    def test_plot_hietogram_comparison_returns_figure(self, hietogram_result):
        """Test plot_hietogram_comparison returns a Figure."""
        effective = hietogram_result.intensities_mm * 0.5  # Mock effective precip
        fig = plot_hietogram_comparison(hietogram_result, effective)
        assert isinstance(fig, plt.Figure)

    def test_plot_hietogram_comparison_with_list(self, hietogram_result):
        """Test plot_hietogram_comparison with list input."""
        effective = list(hietogram_result.intensities_mm * 0.5)
        fig = plot_hietogram_comparison(hietogram_result, effective)
        assert isinstance(fig, plt.Figure)


class TestHydrograph:
    """Tests for hydrograph visualization."""

    @pytest.fixture
    def hydrograph_result(self):
        """Create sample hydrograph result."""
        hietogram = BetaHietogram(alpha=2, beta=5)
        precip = hietogram.generate(total_mm=50, duration_min=120, timestep_min=10)
        generator = HydrographGenerator(area_km2=45, cn=72, tc_min=90)
        return generator.generate(precip)

    def test_plot_hydrograph_returns_figure(self, hydrograph_result):
        """Test plot_hydrograph returns a Figure."""
        fig = plot_hydrograph(hydrograph_result.hydrograph)
        assert isinstance(fig, plt.Figure)

    def test_plot_hydrograph_with_peak(self, hydrograph_result):
        """Test plot_hydrograph with peak annotation."""
        fig = plot_hydrograph(hydrograph_result.hydrograph, show_peak=True)
        assert isinstance(fig, plt.Figure)

    def test_plot_hydrograph_without_volume(self, hydrograph_result):
        """Test plot_hydrograph without volume display."""
        fig = plot_hydrograph(hydrograph_result.hydrograph, show_volume=False)
        assert isinstance(fig, plt.Figure)

    def test_plot_hydrograph_existing_axes(self, hydrograph_result):
        """Test plot_hydrograph with existing axes."""
        fig, ax = plt.subplots()
        result_fig = plot_hydrograph(hydrograph_result.hydrograph, ax=ax)
        assert result_fig is fig

    def test_plot_unit_hydrograph_scs(self):
        """Test plot_unit_hydrograph with SCS model."""
        scs = SCSUnitHydrograph(area_km2=45, tc_min=90)
        result = scs.generate(timestep_min=10)
        fig = plot_unit_hydrograph(result)
        assert isinstance(fig, plt.Figure)

    def test_plot_unit_hydrograph_nash(self):
        """Test plot_unit_hydrograph with Nash model."""
        nash = NashIUH(n=3, k_min=30, area_km2=45)
        result = nash.generate(timestep_min=10)
        fig = plot_unit_hydrograph(result)
        assert isinstance(fig, plt.Figure)

    def test_plot_unit_hydrograph_clark(self):
        """Test plot_unit_hydrograph with Clark model."""
        clark = ClarkIUH(tc_min=60, r_min=30, area_km2=45)
        result = clark.generate(timestep_min=10)
        fig = plot_unit_hydrograph(result)
        assert isinstance(fig, plt.Figure)

    def test_plot_unit_hydrograph_snyder(self):
        """Test plot_unit_hydrograph with Snyder model."""
        snyder = SnyderUH(area_km2=45, L_km=15, Lc_km=8)
        result = snyder.generate(timestep_min=10)
        fig = plot_unit_hydrograph(result)
        assert isinstance(fig, plt.Figure)


class TestCombined:
    """Tests for combined rainfall-runoff visualization."""

    @pytest.fixture
    def combined_data(self):
        """Create sample combined data."""
        hietogram = BetaHietogram(alpha=2, beta=5)
        precip = hietogram.generate(total_mm=50, duration_min=120, timestep_min=10)
        generator = HydrographGenerator(area_km2=45, cn=72, tc_min=90)
        result = generator.generate(precip)
        return precip, result

    def test_plot_rainfall_runoff_returns_figure(self, combined_data):
        """Test plot_rainfall_runoff returns a Figure."""
        precip, result = combined_data
        fig = plot_rainfall_runoff(precip, result.hydrograph)
        assert isinstance(fig, plt.Figure)

    def test_plot_rainfall_runoff_with_effective(self, combined_data):
        """Test plot_rainfall_runoff with effective precipitation."""
        precip, result = combined_data
        fig = plot_rainfall_runoff(
            precip,
            result.hydrograph,
            effective_precip=result.effective_precip_mm,
        )
        assert isinstance(fig, plt.Figure)

    def test_plot_rainfall_runoff_custom_figsize(self, combined_data):
        """Test plot_rainfall_runoff with custom figure size."""
        precip, result = combined_data
        fig = plot_rainfall_runoff(precip, result.hydrograph, figsize=(14, 10))
        assert isinstance(fig, plt.Figure)

    def test_plot_rainfall_runoff_custom_ratios(self, combined_data):
        """Test plot_rainfall_runoff with custom height ratios."""
        precip, result = combined_data
        fig = plot_rainfall_runoff(precip, result.hydrograph, height_ratios=(1, 3))
        assert isinstance(fig, plt.Figure)


class TestUHComparison:
    """Tests for unit hydrograph comparison."""

    @pytest.fixture
    def uh_models(self):
        """Create sample UH models."""
        scs = SCSUnitHydrograph(area_km2=45, tc_min=90).generate(timestep_min=10)
        nash = NashIUH(n=3, k_min=30, area_km2=45).generate(timestep_min=10)
        return {"SCS": scs, "Nash": nash}

    def test_plot_uh_comparison_returns_figure(self, uh_models):
        """Test plot_uh_comparison returns a Figure."""
        fig = plot_uh_comparison(uh_models)
        assert isinstance(fig, plt.Figure)

    def test_plot_uh_comparison_with_table(self, uh_models):
        """Test plot_uh_comparison with table."""
        fig = plot_uh_comparison(uh_models, show_table=True)
        assert isinstance(fig, plt.Figure)

    def test_plot_uh_comparison_without_table(self, uh_models):
        """Test plot_uh_comparison without table."""
        fig = plot_uh_comparison(uh_models, show_table=False)
        assert isinstance(fig, plt.Figure)

    def test_plot_uh_comparison_empty_raises(self):
        """Test plot_uh_comparison raises on empty models."""
        with pytest.raises(ValueError, match="cannot be empty"):
            plot_uh_comparison({})


class TestWaterBalance:
    """Tests for water balance visualization."""

    def test_plot_cn_curve_returns_figure(self):
        """Test plot_cn_curve returns a Figure."""
        fig = plot_cn_curve(cn=72)
        assert isinstance(fig, plt.Figure)

    def test_plot_cn_curve_with_amc_variants(self):
        """Test plot_cn_curve with AMC variants."""
        fig = plot_cn_curve(cn=72, amc_variants=True)
        assert isinstance(fig, plt.Figure)

    def test_plot_cn_curve_without_amc_variants(self):
        """Test plot_cn_curve without AMC variants."""
        fig = plot_cn_curve(cn=72, amc_variants=False)
        assert isinstance(fig, plt.Figure)

    def test_plot_cn_curve_custom_range(self):
        """Test plot_cn_curve with custom precipitation range."""
        fig = plot_cn_curve(cn=72, p_range=(0, 200))
        assert isinstance(fig, plt.Figure)

    def test_plot_cn_curve_custom_ia(self):
        """Test plot_cn_curve with custom initial abstraction coefficient."""
        fig = plot_cn_curve(cn=72, ia_coefficient=0.05)
        assert isinstance(fig, plt.Figure)


class TestMorphometry:
    """Tests for morphometry visualization."""

    @pytest.fixture
    def hypsometric_result(self):
        """Create sample hypsometric result."""
        elevations = np.linspace(100, 500, 1000)
        hypso = HypsometricCurve(elevations)
        return hypso.analyze()

    def test_plot_hypsometric_curve_returns_figure(self, hypsometric_result):
        """Test plot_hypsometric_curve returns a Figure."""
        fig = plot_hypsometric_curve(hypsometric_result)
        assert isinstance(fig, plt.Figure)

    def test_plot_hypsometric_curve_with_integral(self, hypsometric_result):
        """Test plot_hypsometric_curve with integral shading."""
        fig = plot_hypsometric_curve(hypsometric_result, show_integral=True)
        assert isinstance(fig, plt.Figure)

    def test_plot_hypsometric_curve_without_reference(self, hypsometric_result):
        """Test plot_hypsometric_curve without reference curves."""
        fig = plot_hypsometric_curve(hypsometric_result, show_reference=False)
        assert isinstance(fig, plt.Figure)

    def test_plot_elevation_histogram_returns_figure(self):
        """Test plot_elevation_histogram returns a Figure."""
        elevations = np.random.normal(300, 50, 1000)
        fig = plot_elevation_histogram(elevations)
        assert isinstance(fig, plt.Figure)

    def test_plot_elevation_histogram_custom_bins(self):
        """Test plot_elevation_histogram with custom bins."""
        elevations = np.random.normal(300, 50, 1000)
        fig = plot_elevation_histogram(elevations, bins=30)
        assert isinstance(fig, plt.Figure)


class TestNetwork:
    """Tests for network visualization."""

    @pytest.fixture
    def network_stats(self):
        """Create sample network statistics."""
        segments = [
            StreamSegment(segment_id=1, upstream_ids=[], length_km=1.0),
            StreamSegment(segment_id=2, upstream_ids=[], length_km=1.5),
            StreamSegment(segment_id=3, upstream_ids=[1, 2], length_km=0.8),
            StreamSegment(segment_id=4, upstream_ids=[3], length_km=2.0),
        ]
        network = StreamNetwork(segments, area_km2=50)
        network.classify()
        return network.get_statistics()

    def test_plot_stream_order_stats_returns_figure(self, network_stats):
        """Test plot_stream_order_stats returns a Figure."""
        fig = plot_stream_order_stats(network_stats)
        assert isinstance(fig, plt.Figure)

    def test_plot_stream_order_stats_custom_title(self, network_stats):
        """Test plot_stream_order_stats with custom title."""
        fig = plot_stream_order_stats(network_stats, title="Test Network")
        assert isinstance(fig, plt.Figure)

    def test_plot_bifurcation_ratios_returns_figure(self, network_stats):
        """Test plot_bifurcation_ratios returns a Figure."""
        fig = plot_bifurcation_ratios(network_stats)
        assert isinstance(fig, plt.Figure)


class TestInterpolation:
    """Tests for interpolation visualization."""

    @pytest.fixture
    def stations(self):
        """Create sample stations."""
        return [
            Station("S1", x=0, y=0, precipitation_mm=25.0),
            Station("S2", x=10, y=0, precipitation_mm=35.0),
            Station("S3", x=5, y=8, precipitation_mm=30.0),
        ]

    def test_plot_stations_map_returns_figure(self, stations):
        """Test plot_stations_map returns a Figure."""
        fig = plot_stations_map(stations)
        assert isinstance(fig, plt.Figure)

    def test_plot_stations_map_with_weights(self, stations):
        """Test plot_stations_map with weights."""
        weights = {"S1": 0.3, "S2": 0.4, "S3": 0.3}
        fig = plot_stations_map(stations, weights=weights)
        assert isinstance(fig, plt.Figure)

    def test_plot_stations_map_without_values(self, stations):
        """Test plot_stations_map without value labels."""
        fig = plot_stations_map(stations, show_values=False)
        assert isinstance(fig, plt.Figure)

    def test_plot_stations_map_custom_title(self, stations):
        """Test plot_stations_map with custom title."""
        fig = plot_stations_map(stations, title="Test Stations")
        assert isinstance(fig, plt.Figure)


class TestModuleImport:
    """Test module imports."""

    def test_import_all_functions(self):
        """Test that all public functions can be imported."""
        from hydrolog.visualization import (
            setup_hydrolog_style,
            plot_hietogram,
            plot_hietogram_comparison,
            plot_hydrograph,
            plot_unit_hydrograph,
            plot_rainfall_runoff,
            plot_uh_comparison,
            plot_cn_curve,
            plot_hypsometric_curve,
            plot_elevation_histogram,
            plot_stream_order_stats,
            plot_bifurcation_ratios,
            plot_stations_map,
        )

        assert setup_hydrolog_style is not None
        assert plot_hietogram is not None
        assert plot_rainfall_runoff is not None
