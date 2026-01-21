"""Report generation module for Hydrolog.

This module provides comprehensive hydrological calculation reports
in Markdown format with LaTeX formulas, tables, and Polish text.

Example
-------
>>> from hydrolog.reports import HydrologyReportGenerator
>>> from hydrolog.runoff import HydrographGenerator
>>> from hydrolog.precipitation import BetaHietogram
>>>
>>> # Generate hydrograph
>>> hietogram = BetaHietogram(alpha=2, beta=5)
>>> precip = hietogram.generate(total_mm=50, duration_min=120, timestep_min=10)
>>> generator = HydrographGenerator(area_km2=45, cn=72, tc_min=90)
>>> result = generator.generate(precip)
>>>
>>> # Generate report
>>> report = HydrologyReportGenerator()
>>> report.generate(
...     result=result,
...     hietogram=precip,
...     watershed_name="Zlewnia Testowa",
...     output_path="raport.md"
... )
"""

from hydrolog.reports.generator import HydrologyReportGenerator, ReportConfig
from hydrolog.reports.formatters import FormulaRenderer, TableGenerator

__all__ = [
    "HydrologyReportGenerator",
    "ReportConfig",
    "FormulaRenderer",
    "TableGenerator",
]
