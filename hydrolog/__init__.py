"""
Hydrolog - Python library for hydrological calculations.

A modular library providing tools for:
- Runoff generation using SCS-CN method
- Hyetograph generation (temporal precipitation distribution)
- Time of concentration calculations
- Morphometric parameters
- River network classification
"""

__version__ = "0.6.0"
__author__ = "Daldek"

from hydrolog.exceptions import HydrologError, InvalidParameterError, CalculationError

__all__ = [
    "__version__",
    "HydrologError",
    "InvalidParameterError",
    "CalculationError",
]
