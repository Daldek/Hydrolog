"""The indices of a river network against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); Strahler's
rule has the reference cases of ``morphometry-cases.json`` (CMP-6.1) and the
quotients their exact rational oracles (CMP-6.2). A network is no input the generator
can express, so the counts of streams that feed the indices are tested here by hand:
against hand counts of two networks (the research's cases ``network-*``) and against
another algorithm, the connected runs of links of one order, on random networks.
"""

from fractions import Fraction
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.network import OrderingMethod, StreamNetwork, StreamSegment
from hydrolog.network.stream_order import (
    SPECS,
    STRAHLER_ORDER,
    bifurcation_ratio,
    drainage_density,
    length_ratio,
    strahler_order,
    stream_frequency,
)
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    ReferenceCase,
    assert_case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    assert_within,
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "morphometry-cases.json"
FUNCTIONS = {
    "strahler_order": strahler_order,
    "bifurcation_ratio": bifurcation_ratio,
    "length_ratio": length_ratio,
    "drainage_density": drainage_density,
    "stream_frequency": stream_frequency,
}
FAMILY = tuple((spec, FUNCTIONS[spec.name]) for spec in SPECS)
EXACT = "the hand count's exact rational value, which float64 rounds once or twice"


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, function, case, ERRORS)


@pytest.mark.parametrize(
    "case", load_cases(CASES, "strahler_order"), ids=lambda case: case.case_id
)
def test_reference_cases(case: ReferenceCase):
    assert_case(STRAHLER_ORDER, strahler_order, case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=[s.name for s in SPECS])
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, function, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=[s.name for s in SPECS])
@given(data=st.data())
def test_properties(spec: FormulaSpec, function, data):
    inputs = data.draw(strategies(spec))
    assert_property_contract(spec, function, inputs, ERRORS)
    assert_properties(spec, function, inputs, ERRORS)


def _network(links: dict[int, tuple[list[int], float]]) -> StreamNetwork:
    return StreamNetwork(
        [
            StreamSegment(key, ups, length_km=length)
            for key, (ups, length) in links.items()
        ]
    )


FIXTURE = {
    1: ([], 1.2),
    2: ([], 0.8),
    3: ([1, 2], 1.5),
    4: ([], 1.0),
    5: ([], 0.9),
    6: ([4, 5], 1.4),
    7: ([3, 6], 2.2),
    8: ([], 0.7),
    9: ([7, 8], 3.0),
}
"""``tests/fixtures/network_segments.csv``: links 7 and 9 are one stream of order 3,
as tributary 8 is of order 1 (research case network-fixture-strahler-streams)."""


def test_the_example_network_counts_strahler_streams():
    network = StreamNetwork(
        [
            StreamSegment(k, ups, length_km=length)
            for k, (ups, length) in FIXTURE.items()
        ],
        area_km2=12.0,
    )
    network.classify(OrderingMethod.STRAHLER)

    stats = network.get_statistics()

    assert stats.segment_counts == {1: 5, 2: 2, 3: 1}
    assert network.n_streams == 8
    expected = {
        "mean_1": Fraction("4.6") / 5,
        "mean_2": Fraction("2.9") / 2,
        "mean_3": Fraction("5.2"),
    }
    assert stats.bifurcation_ratios == {1: 2.5, 2: 2.0}
    for order, key in ((1, "mean_1"), (2, "mean_2"), (3, "mean_3")):
        assert_within(
            stats.mean_lengths_km[order], float(expected[key]), rel=4e-16, reason=EXACT
        )
    assert_within(
        stats.length_ratios[1],
        float(expected["mean_2"] / expected["mean_1"]),
        rel=8e-16,
        reason=EXACT,
    )
    assert_within(
        stats.length_ratios[2],
        float(expected["mean_3"] / expected["mean_2"]),
        rel=8e-16,
        reason=EXACT,
    )
    assert_within(
        stats.drainage_density,
        float(Fraction("12.7") / 12),
        rel=8e-16,
        reason=EXACT,
    )
    assert_within(
        stream_frequency(network.n_streams, 12.0), 8 / 12, abs=0.0, reason=EXACT
    )


def test_a_side_tributary_does_not_split_its_stream():
    """Research case network-side-tributary: 1, 2 -> 3; 3 + 4 -> 5."""
    network = _network(
        {1: ([], 1.0), 2: ([], 1.0), 3: ([1, 2], 2.0), 4: ([], 1.0), 5: ([3, 4], 2.0)}
    )
    network.classify(OrderingMethod.STRAHLER)

    stats = network.get_statistics()

    assert stats.segment_counts == {1: 3, 2: 1}
    assert stats.bifurcation_ratios == {1: 3.0}
    assert stats.mean_lengths_km == {1: 1.0, 2: 4.0}
    assert stats.length_ratios == {1: 4.0}


def _streams(links: dict[int, list[int]], orders: dict[int, int]) -> dict[int, int]:
    """Count the streams of each order as connected runs of links of one order.

    Union-find over the links: a link joins each upstream link of its own order, so
    a stream is a set of links; its order is theirs (another algorithm than the
    code's rule of where a stream begins).
    """
    parent = {key: key for key in links}

    def root(key: int) -> int:
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    for key, ups in links.items():
        for up in ups:
            if orders[up] == orders[key]:
                parent[root(up)] = root(key)
    counts: dict[int, int] = {}
    for key in {root(key) for key in links}:
        counts[orders[key]] = counts.get(orders[key], 0) + 1
    return dict(sorted(counts.items()))


@st.composite
def networks(draw) -> dict[int, list[int]]:
    """A random tree of links from an outlet upstream, junctions of up to 3 links."""
    links: dict[int, list[int]] = {0: []}
    for key in range(1, draw(st.integers(min_value=1, max_value=60))):
        open_links = [k for k, ups in links.items() if len(ups) < 3]
        below = draw(st.sampled_from(open_links))
        links[below].append(key)
        links[key] = []
    return links


@given(links=networks())
def test_streams_are_the_runs_of_links_of_one_order(links):
    network = _network({key: (ups, 1.0) for key, ups in links.items()})
    network.classify(OrderingMethod.STRAHLER)
    orders = {key: seg.order for key, seg in network.segments.items()}

    stats = network.get_statistics()

    assert stats.segment_counts == _streams(links, orders)
    assert network.n_streams == sum(stats.segment_counts.values())


def test_a_bifurcation_ratio_below_two_is_refused():
    """Fewer than two streams per stream of the next order: links counted as
    streams, the defect of Hydrolog up to 0.8.1 (TRIAGE T16)."""
    with pytest.raises(InvalidParameterError) as refused:
        bifurcation_ratio(2, 2)

    assert refused.value.details["constraint"] == "two_streams_per_junction"


def test_the_statistics_record_the_formulas_they_use():
    network = StreamNetwork(
        [
            StreamSegment(k, ups, length_km=length)
            for k, (ups, length) in FIXTURE.items()
        ],
        area_km2=12.0,
    )
    with recording() as used:
        network.classify(OrderingMethod.STRAHLER)
        network.get_statistics()

    assert used == {
        name: spec.formula_version
        for spec in SPECS
        if (name := spec.name) != "stream_frequency"
    }
