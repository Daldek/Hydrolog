# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project documentation:
  - `CLAUDE.md` - instructions for AI developer
  - `README.md` - project description
  - `docs/SCOPE.md` - project scope
  - `docs/PRD.md` - product requirements
  - `docs/DEVELOPMENT_STANDARDS.md` - coding standards
  - `docs/IMPLEMENTATION_PROMPT.md` - implementation guide
  - `docs/PROGRESS.md` - progress tracker
  - `docs/CHANGELOG.md` - this file

### Planned for v0.1.0
- `hydrolog.time` module - concentration time calculations
- `hydrolog.precipitation` module - hietogram generation
- `hydrolog.runoff` module - SCS-CN method, unit hydrograph

---

## [0.1.0] - TBD

### Added
- `hydrolog.time.ConcentrationTime` - Kirpich and SCS Lag methods
- `hydrolog.precipitation.BetaHietogram` - Beta distribution hietogram
- `hydrolog.precipitation.BlockHietogram` - Constant intensity hietogram
- `hydrolog.runoff.calculate_effective_precipitation` - SCS-CN effective precipitation
- `hydrolog.runoff.SCSUnitHydrograph` - SCS dimensionless unit hydrograph
- `hydrolog.runoff.HydrographGenerator` - Full hydrograph generation
- Unit tests with >80% coverage
- NumPy style docstrings (English)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | TBD | Hydrogram SCS-CN |
| 0.2.0 | TBD | Morphometric parameters |
| 0.3.0 | TBD | Interpolation + river network |
| 1.0.0 | TBD | Stable API + CLI |
