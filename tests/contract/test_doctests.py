"""The examples in the docstrings run (TRIAGE T14): a curated list of modules.

``scripts/gate.sh`` runs ``pytest tests``, which does not collect the docstrings of
``src/``; this test runs the examples of the modules listed below. A module joins
the list once its examples pass; those of the visualisation modules and of
``reports.generator`` write files and stay out. Not listed, because some of their
examples fail (2026-11-18): ``hydrometrics.rating_curve``, ``operations.config``,
``precipitation.interpolation``, ``reports`` and the ``visualization`` modules.
"""

import doctest
import importlib

import pytest

MODULES = (
    "hydrolog",
    "hydrolog._atomic",
    "hydrolog._formula_versions",
    "hydrolog._serialization",
    "hydrolog._warnings",
    "hydrolog.agent_guide",
    "hydrolog.catalog.envelope",
    "hydrolog.catalog.lines",
    "hydrolog.catalog.notices",
    "hydrolog.cli.values",
    "hydrolog.exceptions",
    "hydrolog.morphometry.geometric",
    "hydrolog.morphometry.hypsometry",
    "hydrolog.morphometry.terrain",
    "hydrolog.morphometry.watershed_params",
    "hydrolog.network.stream_order",
    "hydrolog.operations.meta",
    "hydrolog.precipitation.hietogram",
    "hydrolog.reports.formatters",
    "hydrolog.routing",
    "hydrolog.routing._layout",
    "hydrolog.routing._registry",
    "hydrolog.routing._svg",
    "hydrolog.routing.cascade",
    "hydrolog.routing.document",
    "hydrolog.routing.hydrograph",
    "hydrolog.routing.lag",
    "hydrolog.routing.level_pool",
    "hydrolog.routing.muskingum",
    "hydrolog.routing.network",
    "hydrolog.routing.parameters",
    "hydrolog.routing.points",
    "hydrolog.routing.rainfall",
    "hydrolog.routing.runoff",
    "hydrolog.routing.schematic",
    "hydrolog.routing.sections",
    "hydrolog.runoff.cn_lookup",
    "hydrolog.runoff.clark_iuh",
    "hydrolog.runoff.convolution",
    "hydrolog.runoff.generator",
    "hydrolog.runoff.nash_iuh",
    "hydrolog.runoff.scs_cn",
    "hydrolog.runoff.snyder_uh",
    "hydrolog.runoff.unit_hydrograph",
    "hydrolog.soil",
    "hydrolog.soil.hsg",
    "hydrolog.soil.texture",
    "hydrolog.statistics._types",
    "hydrolog.statistics.frequency",
    "hydrolog.statistics.high_flows",
    "hydrolog.statistics.homogeneity",
    "hydrolog.statistics.low_flows",
    "hydrolog.statistics.meteo_precipitation",
    "hydrolog.statistics.meteo_hydrothermal",
    "hydrolog.statistics.meteo_spells",
    "hydrolog.statistics.meteo_spi",
    "hydrolog.statistics.meteo_temperature",
    "hydrolog.statistics.regime",
    "hydrolog.statistics.stationarity",
    "hydrolog.testing",
    "hydrolog.time.concentration",
)


@pytest.mark.parametrize("name", MODULES)
def test_the_examples_of_the_module_run(name):
    found = doctest.testmod(
        importlib.import_module(name), optionflags=doctest.ELLIPSIS, verbose=False
    )

    assert found.attempted > 0
    assert found.failed == 0
