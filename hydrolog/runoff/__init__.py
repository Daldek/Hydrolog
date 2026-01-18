"""Runoff generation module using SCS-CN method."""

from hydrolog.runoff.convolution import HydrographResult, convolve_discrete
from hydrolog.runoff.generator import HydrographGenerator, HydrographGeneratorResult
from hydrolog.runoff.nash_iuh import IUHResult, NashIUH, NashUHResult
from hydrolog.runoff.scs_cn import AMC, SCSCN, EffectivePrecipitationResult
from hydrolog.runoff.unit_hydrograph import SCSUnitHydrograph, UnitHydrographResult

__all__ = [
    # Main generator
    "HydrographGenerator",
    "HydrographGeneratorResult",
    # SCS-CN
    "SCSCN",
    "AMC",
    "EffectivePrecipitationResult",
    # Unit hydrograph (SCS)
    "SCSUnitHydrograph",
    "UnitHydrographResult",
    # Instantaneous Unit Hydrograph (Nash)
    "NashIUH",
    "IUHResult",
    "NashUHResult",
    # Convolution
    "convolve_discrete",
    "HydrographResult",
]
