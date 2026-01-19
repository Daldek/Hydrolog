"""Runoff generation module using SCS-CN method."""

from hydrolog.runoff.clark_iuh import ClarkIUH, ClarkIUHResult, ClarkUHResult
from hydrolog.runoff.cn_lookup import (
    CNLookupResult,
    HydrologicCondition,
    LandCover,
    calculate_weighted_cn,
    get_cn,
    get_cn_range,
    list_land_covers,
    lookup_cn,
)
from hydrolog.runoff.convolution import HydrographResult, convolve_discrete
from hydrolog.runoff.generator import HydrographGenerator, HydrographGeneratorResult
from hydrolog.runoff.nash_iuh import IUHResult, NashIUH, NashUHResult
from hydrolog.runoff.scs_cn import AMC, SCSCN, EffectivePrecipitationResult
from hydrolog.runoff.snyder_uh import SnyderUH, SnyderUHResult
from hydrolog.runoff.unit_hydrograph import SCSUnitHydrograph, UnitHydrographResult

__all__ = [
    # Main generator
    "HydrographGenerator",
    "HydrographGeneratorResult",
    # SCS-CN
    "SCSCN",
    "AMC",
    "EffectivePrecipitationResult",
    # CN Lookup (TR-55 tables)
    "get_cn",
    "lookup_cn",
    "get_cn_range",
    "list_land_covers",
    "calculate_weighted_cn",
    "LandCover",
    "HydrologicCondition",
    "CNLookupResult",
    # Unit hydrograph (SCS)
    "SCSUnitHydrograph",
    "UnitHydrographResult",
    # Instantaneous Unit Hydrograph (Nash)
    "NashIUH",
    "IUHResult",
    "NashUHResult",
    # Instantaneous Unit Hydrograph (Clark)
    "ClarkIUH",
    "ClarkIUHResult",
    "ClarkUHResult",
    # Synthetic Unit Hydrograph (Snyder)
    "SnyderUH",
    "SnyderUHResult",
    # Convolution
    "convolve_discrete",
    "HydrographResult",
]
