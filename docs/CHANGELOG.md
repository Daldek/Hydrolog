# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for v0.3.0
- `hydrolog.network` module - river network classification
- `hydrolog.precipitation.interpolation` - spatial interpolation

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
| 0.3.0 | TBD | Interpolation + river network |
| 1.0.0 | TBD | Stable API + CLI |
