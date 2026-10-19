"""Operation layer: one public function per catalog command (spec section 6.3).

Every command of :mod:`hydrolog.catalog` calls exactly one function of this package
(``Command.function`` = ``"hydrolog.operations:<name>"``). The functions are the
Python surface for Retman handlers and for ``retman-scaffold`` (signature and
docstring parsing), so each one is

* public and documented (NumPy docstring, English),
* fully type-hinted, keyword-only, with ``Literal`` for choices,
* taking JSON-friendly inputs (numbers, strings, lists, paths as ``str``) whose names
  equal the catalog options,
* returning a :class:`~hydrolog._serialization.JsonResultMixin` result (or a small
  result dataclass defined next to it), or a
  :class:`~hydrolog.catalog.envelope.OperationOutput` when it has notices or writes
  files (return protocol: :mod:`hydrolog.catalog.envelope`).

Operations compose the existing classes and functions; they contain no new
hydrology. Series, stations and watershed parameters are loaded with
:mod:`hydrolog.catalog.inputs`.

Layout: one module per command group, named like the group module of
:mod:`hydrolog.catalog.groups` (``operations/tc.py`` implements
``catalog/groups/tc.py``). Operation functions are named ``<group>_<command>``
(``tc_kirpich``); they are re-exported here, so ``function="hydrolog.operations:<name>"``
resolves to this package, and listed in ``__all__``. A new group adds its import and
its names below, in the order of ``hydrolog.catalog.groups.GROUP_MODULES``; the
``commands`` group (``meta``) stays last.
"""

from __future__ import annotations

from hydrolog.operations.cn import (
    CnBounds,
    CnEntry,
    CnList,
    CnLookup,
    CnRange,
    CnWeighted,
    cn_list,
    cn_lookup,
    cn_range,
    cn_weighted,
)
from hydrolog.operations.hydrograph import (
    HydrographGenerateResult,
    HydrographRun,
    compute_hydrograph,
    hydrograph_generate,
)
from hydrolog.operations.hydrometrics import (
    WaterLevelAnalysis,
    hydrometrics_rating_curve,
    hydrometrics_water_level_zones,
)
from hydrolog.operations.meta import (
    CommandSummary,
    commands_guide,
    commands_schema,
    list_commands,
)
from hydrolog.operations.morphometry import WatershedMorphometry, morphometry_watershed
from hydrolog.operations.network import NetworkAnalysis, network_stats
from hydrolog.operations.precip import (
    ArealPrecipitationResult,
    PrecipHietogramResult,
    precip_areal,
    precip_hietogram,
)
from hydrolog.operations.report import ReportResult, report_generate
from hydrolog.operations.scs import ScsEffectiveResult, scs_effective
from hydrolog.operations.soil import (
    SoilTextureResult,
    soil_hsg,
    soil_hsg_stats,
    soil_texture,
)
from hydrolog.operations.stats import (
    FloodFrequencyResult,
    LowFlowEvent,
    LowFlowFrequencyAnalysis,
    LowFlowSequencesResult,
    stats_characteristic,
    stats_daily,
    stats_flood_frequency,
    stats_low_flow,
    stats_low_flow_sequences,
    stats_mann_kendall,
    stats_monthly,
)
from hydrolog.operations.tc import (
    TcResult,
    tc_faa,
    tc_giandotti,
    tc_kerby,
    tc_kerby_kirpich,
    tc_kirpich,
    tc_nrcs,
    tc_watershed,
)
from hydrolog.operations.uh import UhResult, uh_clark, uh_nash, uh_scs, uh_snyder

__all__ = [
    # tc
    "TcResult",
    "tc_faa",
    "tc_giandotti",
    "tc_kerby",
    "tc_kerby_kirpich",
    "tc_kirpich",
    "tc_nrcs",
    "tc_watershed",
    # cn
    "CnBounds",
    "CnEntry",
    "CnList",
    "CnLookup",
    "CnRange",
    "CnWeighted",
    "cn_list",
    "cn_lookup",
    "cn_range",
    "cn_weighted",
    # scs
    "ScsEffectiveResult",
    "scs_effective",
    # precip
    "ArealPrecipitationResult",
    "PrecipHietogramResult",
    "precip_areal",
    "precip_hietogram",
    # uh
    "UhResult",
    "uh_clark",
    "uh_nash",
    "uh_scs",
    "uh_snyder",
    # hydrograph
    "HydrographGenerateResult",
    "HydrographRun",
    "compute_hydrograph",
    "hydrograph_generate",
    # morphometry
    "WatershedMorphometry",
    "morphometry_watershed",
    # network
    "NetworkAnalysis",
    "network_stats",
    # stats
    "FloodFrequencyResult",
    "LowFlowEvent",
    "LowFlowFrequencyAnalysis",
    "LowFlowSequencesResult",
    "stats_characteristic",
    "stats_daily",
    "stats_flood_frequency",
    "stats_low_flow",
    "stats_low_flow_sequences",
    "stats_mann_kendall",
    "stats_monthly",
    # hydrometrics
    "WaterLevelAnalysis",
    "hydrometrics_rating_curve",
    "hydrometrics_water_level_zones",
    # soil
    "SoilTextureResult",
    "soil_hsg",
    "soil_hsg_stats",
    "soil_texture",
    # report
    "ReportResult",
    "report_generate",
    # commands
    "CommandSummary",
    "commands_guide",
    "commands_schema",
    "list_commands",
]
