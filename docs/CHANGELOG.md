# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- `plot_hietogram()` - Y-axis now always in mm/h (intensity), new `distribution` parameter for subtitle
- `plot_hietogram_comparison()` - Y-axis in mm/h, removed duplicate stats box
- `plot_hydrograph()` - Removed text annotation at peak (only marker remains)
- `plot_cn_curve()` - Removed CN values from AMC legend (same CN, different AMC conditions)

### Removed
- `SnyderUH.from_lag_time()` - Estimated L and Lc from lag time (impractical, these parameters should be measured from maps/GIS)
- `SnyderUH.from_tc()` - Delegated to `from_lag_time()`, same issue
- `NashIUH.from_moments()` - Required variance and lag time from observed hydrograph (not practical for ungauged catchments)
- `ClarkIUH.from_recession()` - Required recession constant from observed hydrograph

---

## [0.5.0] - 2026-01-19

### Added

#### `hydrolog.visualization` - Visualization Module
New module for graphical presentation of hydrological results.
Requires optional dependencies: `pip install hydrolog[visualization]`

**Hietogram plots (`hietogram.py`):**
- `plot_hietogram()` - precipitation hyetograph with intensity bars and optional cumulative line
- `plot_hietogram_comparison()` - comparison of total vs effective precipitation

**Hydrograph plots (`hydrograph.py`):**
- `plot_hydrograph()` - runoff hydrograph Q(t) with peak annotation and volume
- `plot_unit_hydrograph()` - unit hydrograph for any model (SCS, Nash, Clark, Snyder)

**Combined plots (`combined.py`):**
- `plot_rainfall_runoff()` - classic rainfall-runoff plot with inverted hietogram on top
- `plot_generator_result()` - full dashboard with water balance table

**Unit hydrograph comparison (`unit_hydrograph.py`):**
- `plot_uh_comparison()` - multiple UH models on one plot with comparison table

**Water balance (`water_balance.py`):**
- `plot_water_balance()` - SCS-CN water balance visualization (bars or pie)
- `plot_cn_curve()` - P → Pe relationship with AMC variants

**Morphometry (`morphometry.py`):**
- `plot_hypsometric_curve()` - hypsometric curve h/H vs a/A with HI integral
- `plot_elevation_histogram()` - elevation distribution histogram

**Network (`network.py`):**
- `plot_stream_order_stats()` - three-panel stream network statistics
- `plot_bifurcation_ratios()` - bifurcation ratios by stream order

**Interpolation (`interpolation.py`):**
- `plot_stations_map()` - precipitation station map with weights

**Styles (`styles.py`):**
- `setup_hydrolog_style()` - configure matplotlib/seaborn for consistent styling
- `COLORS`, `LABELS_PL`, `PALETTE` - color scheme and Polish labels
- `get_color()`, `get_label()` - helper functions
- `format_time_axis()`, `add_peak_annotation()`, `add_stats_box()`, `add_watermark()`

#### `hydrolog.runoff.nash_iuh` - Lutz Method
- `NashIUH.from_lutz()` - parameter estimation from catchment characteristics
  - Estimates Nash model parameters (n, K) from physiographic data
  - Input parameters: L, Lc, slope, Manning's n, urban%, forest%
  - Numerical solution of f(N) equation using Brent's method
  - Verified against KZGW (2017) Table C.2 (accuracy < 0.001)
  - Reference: Lutz W. (1984), Universität Karlsruhe

### Changed
- Enhanced README.md documentation:
  - Nash model theory (reservoir cascade, IUH formula, properties)
  - All parameter estimation methods (from_tc, from_moments, from_lutz)
  - Lutz method algorithm with full equations
  - Influence of physiographic parameters on runoff
  - New visualization module section with examples

### Dependencies
- Added optional `visualization` dependency group: matplotlib>=3.7, seaborn>=0.12

### Testing
- 53 new tests for visualization module
- 17 new tests for Lutz method
- Total: 538 unit tests (all passing)

---

## [0.4.0] - 2026-01-19

### Added

#### `hydrolog.cli` - Command-Line Interface
- `hydrolog tc` - concentration time calculation
  - `kirpich` - Kirpich formula
  - `scs-lag` - SCS Lag equation
  - `giandotti` - Giandotti formula
- `hydrolog cn` - Curve Number lookup (TR-55)
  - `lookup` - look up CN for HSG and land cover
  - `list` - list available land cover types
  - `range` - show CN range for a land cover
- `hydrolog scs` - SCS-CN runoff calculation
  - AMC conditions support (I, II, III)
  - Custom initial abstraction coefficient
- `hydrolog uh` - unit hydrograph generation
  - `scs` - SCS dimensionless unit hydrograph
  - `nash` - Nash cascade IUH
  - `clark` - Clark IUH
  - `snyder` - Snyder synthetic UH
  - Output formats: table, CSV, JSON

#### `hydrolog.runoff.clark_iuh` - Clark IUH
- `ClarkIUH` - Clark Instantaneous Unit Hydrograph
  - Translation via time-area histogram
  - Linear reservoir routing
  - Simplified elliptical time-area curve
- `ClarkIUHResult` and `ClarkUHResult` dataclasses
- `from_recession()` - parameter estimation from recession analysis
- `from_tc_r_ratio()` - estimation from Tc and R/Tc ratio

#### `hydrolog.runoff.snyder_uh` - Snyder UH
- `SnyderUH` - Snyder Synthetic Unit Hydrograph
  - Empirical relationships (Snyder, 1938)
  - Parameters: L, Lc, Ct, Cp
  - Width calculations at 50% and 75% of peak
- `SnyderUHResult` dataclass
- `from_lag_time()` - parameter estimation from lag time
- `from_tc()` - estimation from concentration time

#### `hydrolog.runoff.cn_lookup` - CN Lookup Tables
- `get_cn()` - look up CN for HSG and land cover
- `lookup_cn()` - detailed lookup with result object
- `get_cn_range()` - CN range for land cover type
- `list_land_covers()` - list available land covers
- `calculate_weighted_cn()` - area-weighted CN calculation
- `LandCover` - 20 land cover types (TR-55)
- `HydrologicCondition` - poor, fair, good conditions

#### `hydrolog.runoff.nash_iuh` - Nash IUH
- `NashIUH` - Nash Instantaneous Unit Hydrograph
  - Nash cascade model with n reservoirs and K storage constant
  - `generate()` - IUH generation at specified timestep
  - `to_unit_hydrograph()` - S-curve conversion to D-minute UH
  - `from_tc()` - parameter estimation from concentration time
  - `from_moments()` - parameter estimation from lag time and variance
- `IUHResult` and `NashUHResult` dataclasses

### Changed
- **BREAKING:** `ConcentrationTime.scs_lag()` signature changed:
  - `length_m` → `length_km` (meters to kilometers)
  - `slope_percent` → `slope_m_per_m` (percent to dimensionless)
- Added parameter range warnings to all concentration time methods

### Fixed
- Corrected SCS Lag constant: `7182` → `7069` (proper metric conversion)
- Fixed docstring examples in `scs_cn.py` (Pe = 7.09 mm, not 12.89 mm)

### Dependencies
- Added `scipy` as dependency (for gamma functions in Nash IUH)
- Added optional `kartograf` dependency for spatial/soil data

### Testing
- 412 unit tests (all passing)
- 27 new CLI tests
- 41 Clark IUH tests
- 43 Snyder UH tests
- 38 CN lookup tests

---

## [0.3.0] - 2026-01-18

### Added

#### `hydrolog.network` - River Network Classification

**Stream ordering (stream_order.py):**
- `StreamSegment` - dataclass for network segments
- `StreamNetwork` - main class for network analysis
- `OrderingMethod` - enum (STRAHLER, SHREVE)
- `NetworkStatistics` - complete network statistics
- Strahler stream ordering method
- Shreve stream ordering method
- Bifurcation ratio calculation
- Length ratio calculation

**Utility functions:**
- `bifurcation_ratio()` - calculate Rb between orders
- `drainage_density()` - streams length / watershed area
- `stream_frequency()` - streams count / watershed area

#### `hydrolog.precipitation.interpolation` - Spatial Interpolation

**Interpolation methods:**
- `Station` - dataclass for measurement stations
- `thiessen_polygons()` - Thiessen/Voronoi polygon method
- `inverse_distance_weighting()` - IDW interpolation
- `areal_precipitation_idw()` - grid-based IDW averaging
- `isohyet_method()` - isohyet contour method
- `arithmetic_mean()` - simple station average

**Result dataclasses:**
- `ThiessenResult` - weights and contributions
- `IDWResult` - interpolated values with weights
- `IsohyetResult` - zone-based precipitation

#### Testing & Quality
- 60 new tests for network and interpolation (210 total)
- 95% code coverage

---

## [0.2.0] - 2026-01-18

### Added

#### `hydrolog.morphometry` - Morphometric Parameters

**Geometric parameters (geometric.py):**
- `WatershedGeometry` - main class for geometric analysis
- `GeometricParameters` - dataclass with area, perimeter, length, width
- `ShapeIndicators` - dataclass with shape coefficients:
  - Form factor (Horton)
  - Compactness coefficient (Gravelius)
  - Circularity ratio (Miller)
  - Elongation ratio (Schumm)
  - Lemniscate ratio (Chorley)

**Terrain analysis (terrain.py):**
- `TerrainAnalysis` - elevation and slope analysis
- `ElevationParameters` - min, max, mean elevation, relief
- `SlopeParameters` - watershed and channel slopes
- `mean_elevation_from_dem()` - DEM-based calculation

**Hypsometric curve (hypsometry.py):**
- `HypsometricCurve` - hypsometric analysis from DEM
- `HypsometricResult` - curve data and statistics
- Hypsometric integral calculation
- Elevation percentiles

#### Testing & Quality
- 47 new tests for morphometry (150 total)
- 95% code coverage

---

## [0.1.0] - 2026-01-18

### Added

#### `hydrolog.time` - Concentration Time
- `ConcentrationTime.kirpich()` - Kirpich formula (L in km, S in m/m)
- `ConcentrationTime.scs_lag()` - SCS Lag equation (metric units)
- `ConcentrationTime.giandotti()` - Giandotti formula

#### `hydrolog.precipitation` - Hyetographs
- `HietogramResult` - dataclass with time series results
- `BlockHietogram` - uniform intensity distribution
- `TriangularHietogram` - triangular distribution with configurable peak
- `BetaHietogram` - Beta distribution for realistic storm patterns

#### `hydrolog.runoff` - Rainfall-Runoff
- `SCSCN` - SCS Curve Number calculations
  - Maximum retention S calculation
  - Initial abstraction Ia calculation
  - Effective precipitation Pe calculation
  - AMC conditions (I, II, III) support
- `SCSUnitHydrograph` - SCS dimensionless unit hydrograph
  - Standard NRCS tabulated ratios
  - Lag time and time to peak calculations
- `convolve_discrete()` - discrete convolution function
- `HydrographGenerator` - complete rainfall-runoff transformation
  - Integration with hyetograph module
  - Water balance tracking
  - Runoff coefficient calculation

#### Testing & Quality
- 103 unit tests
- 94% code coverage
- Full type hints (mypy)
- Black formatting

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| **0.1.0** | 2026-01-18 | SCS-CN hydrograph, hyetographs, concentration time |
| **0.2.0** | 2026-01-18 | Morphometric parameters |
| **0.3.0** | 2026-01-18 | Interpolation + river network |
| **0.4.0** | 2026-01-19 | CLI + Clark IUH + Snyder UH + CN lookup |
| **0.5.0** | 2026-01-19 | Visualization module (matplotlib/seaborn) |
| 0.6.0 | TBD | Report generation with calculations |
| 1.0.0 | TBD | Stable API |
