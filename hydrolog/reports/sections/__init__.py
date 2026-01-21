"""Report section generators.

Each module provides a function to generate a specific section
of the hydrological report in Markdown format.
"""

from hydrolog.reports.sections.watershed import generate_watershed_section
from hydrolog.reports.sections.concentration import generate_tc_section
from hydrolog.reports.sections.hietogram import generate_hietogram_section
from hydrolog.reports.sections.scs_cn import generate_scs_cn_section
from hydrolog.reports.sections.unit_hydrograph import generate_uh_section
from hydrolog.reports.sections.convolution import generate_convolution_section
from hydrolog.reports.sections.water_balance import generate_water_balance_section

__all__ = [
    "generate_watershed_section",
    "generate_tc_section",
    "generate_hietogram_section",
    "generate_scs_cn_section",
    "generate_uh_section",
    "generate_convolution_section",
    "generate_water_balance_section",
]
