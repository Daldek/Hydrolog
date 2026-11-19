"""The Fisher-Tippett distribution of annual minima against its spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5); the limit holds
the maximum-likelihood GEV of the negated minima; R's evd and extRemes are compared in
``test_maximum_likelihood.py``. The function is given to the assertions through
:func:`as_standard` (ADR-0050, point 3).
"""

import numpy as np
import pytest
from hypothesis import given

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog._warnings import NegativeQuantiles
from hydrolog.nogat_formulas import (
    Case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.statistics.low_flows import FISHER_TIPPETT, fisher_tippett_minima

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(case.values[0], id=case.id)
        for case in range_cases(FISHER_TIPPETT) + type_cases(FISHER_TIPPETT)
    ],
)
def test_ranges_and_types(case: Case):
    run_case(FISHER_TIPPETT, as_standard(fisher_tippett_minima), case, ERRORS)


def test_limits_and_oracles():
    assert_limits(FISHER_TIPPETT, as_standard(fisher_tippett_minima), ERRORS)


@given(inputs=strategies(FISHER_TIPPETT))
def test_fisher_tippett_properties(inputs):
    function = as_standard(fisher_tippett_minima)
    assert_property_contract(FISHER_TIPPETT, function, inputs, ERRORS)
    assert_properties(FISHER_TIPPETT, function, inputs, ERRORS)


def test_negative_discharges_are_gaps_and_negative_stages_are_kept():
    """A gap where a discharge would be below 0, with the notice; a stage keeps it."""
    minima = [0.0562, 0.0261, 0.0226, 0.0567, 0.0203, 0.0386, 0.0455, 0.0176, 0.06]
    minima += [0.0429, 0.049, 0.03, 0.0334, 0.0388, 0.0369, 0.0541, 0.0452, 0.0331]
    minima += [0.0007, 0.0678]
    periods = [10.0, 100.0]

    with pytest.warns(NegativeQuantiles):
        discharge = fisher_tippett_minima(minima, periods, "discharge")
    stage = fisher_tippett_minima(minima, periods, "stage")

    assert np.isnan(discharge.quantiles[1])
    assert stage.quantiles[1] < 0.0
    assert discharge.quantiles[0] == stage.quantiles[0] > 0.0


def test_the_formula_records_its_version():
    with recording() as used:
        fisher_tippett_minima([27.3, 38.0, 72.9, 53.6, 45.7, 6.0], [10.0], "stage")

    assert used["fisher_tippett_minima"] == FISHER_TIPPETT.formula_version
