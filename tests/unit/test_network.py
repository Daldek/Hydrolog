"""Unit tests for hydrolog.network module."""

import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.network import (
    OrderingMethod,
    StreamNetwork,
    StreamSegment,
    bifurcation_ratio,
    drainage_density,
    stream_frequency,
)


class TestStreamSegment:
    """Tests for StreamSegment dataclass."""

    def test_create_headwater(self):
        """Test creating a headwater segment."""
        seg = StreamSegment(segment_id=1, upstream_ids=[], length_km=1.5)
        assert seg.segment_id == 1
        assert seg.upstream_ids == []
        assert seg.length_km == 1.5
        assert seg.order == 0  # Not classified yet

    def test_create_junction(self):
        """Test creating a junction segment."""
        seg = StreamSegment(segment_id=3, upstream_ids=[1, 2], length_km=2.0)
        assert seg.upstream_ids == [1, 2]


class TestStreamNetwork:
    """Tests for StreamNetwork class."""

    @pytest.fixture
    def simple_network(self):
        """Create a simple Y-shaped network."""
        # Two headwaters joining into one stream
        segments = [
            StreamSegment(1, [], length_km=1.0),  # Headwater 1
            StreamSegment(2, [], length_km=0.8),  # Headwater 2
            StreamSegment(3, [1, 2], length_km=2.0),  # Junction
        ]
        return StreamNetwork(segments, area_km2=10.0)

    @pytest.fixture
    def complex_network(self):
        """Create a more complex network for testing."""
        #     1   2   3   4  (order 1 headwaters)
        #      \ /     \ /
        #       5       6    (order 2)
        #        \     /
        #          7        (order 2 or 3 depending on method)
        segments = [
            StreamSegment(1, [], length_km=0.5),
            StreamSegment(2, [], length_km=0.6),
            StreamSegment(3, [], length_km=0.4),
            StreamSegment(4, [], length_km=0.7),
            StreamSegment(5, [1, 2], length_km=1.2),
            StreamSegment(6, [3, 4], length_km=1.0),
            StreamSegment(7, [5, 6], length_km=2.5),
        ]
        return StreamNetwork(segments, area_km2=25.0)

    def test_init_empty_segments(self):
        """Test that empty segments list raises error."""
        with pytest.raises(InvalidParameterError, match="cannot be empty"):
            StreamNetwork([])

    def test_init_negative_area(self):
        """Test that negative area raises error."""
        segments = [StreamSegment(1, [], length_km=1.0)]
        with pytest.raises(InvalidParameterError, match="must be positive"):
            StreamNetwork(segments, area_km2=-10.0)

    def test_n_segments(self, simple_network):
        """Test segment count."""
        assert simple_network.n_segments == 3

    def test_strahler_simple(self, simple_network):
        """Test Strahler ordering on simple network."""
        simple_network.classify(OrderingMethod.STRAHLER)

        assert simple_network.segments[1].order == 1
        assert simple_network.segments[2].order == 1
        assert simple_network.segments[3].order == 2  # Two order-1 streams join

    def test_strahler_complex(self, complex_network):
        """Test Strahler ordering on complex network."""
        complex_network.classify(OrderingMethod.STRAHLER)

        # Headwaters
        for i in [1, 2, 3, 4]:
            assert complex_network.segments[i].order == 1

        # First junctions
        assert complex_network.segments[5].order == 2
        assert complex_network.segments[6].order == 2

        # Final junction (two order-2 join)
        assert complex_network.segments[7].order == 3

    def test_shreve_simple(self, simple_network):
        """Test Shreve ordering on simple network."""
        simple_network.classify(OrderingMethod.SHREVE)

        assert simple_network.segments[1].order == 1
        assert simple_network.segments[2].order == 1
        assert simple_network.segments[3].order == 2  # 1 + 1 = 2

    def test_shreve_complex(self, complex_network):
        """Test Shreve ordering on complex network."""
        complex_network.classify(OrderingMethod.SHREVE)

        # Headwaters
        for i in [1, 2, 3, 4]:
            assert complex_network.segments[i].order == 1

        # First junctions
        assert complex_network.segments[5].order == 2  # 1 + 1
        assert complex_network.segments[6].order == 2  # 1 + 1

        # Final junction
        assert complex_network.segments[7].order == 4  # 2 + 2

    def test_statistics_not_classified(self, simple_network):
        """Test that get_statistics raises error if not classified."""
        with pytest.raises(InvalidParameterError, match="must be classified"):
            simple_network.get_statistics()

    def test_statistics_simple(self, simple_network):
        """Test network statistics on simple network."""
        simple_network.classify(OrderingMethod.STRAHLER)
        stats = simple_network.get_statistics()

        assert stats.max_order == 2
        assert stats.segment_counts[1] == 2
        assert stats.segment_counts[2] == 1
        assert stats.total_lengths_km[1] == pytest.approx(1.8)  # 1.0 + 0.8
        assert stats.total_lengths_km[2] == pytest.approx(2.0)
        assert stats.total_stream_length_km == pytest.approx(3.8)
        assert stats.drainage_density == pytest.approx(0.38)  # 3.8 / 10.0

    def test_statistics_bifurcation_ratio(self, complex_network):
        """Test bifurcation ratio calculation."""
        complex_network.classify(OrderingMethod.STRAHLER)
        stats = complex_network.get_statistics()

        # Rb_1 = N_1 / N_2 = 4 / 2 = 2.0
        assert stats.bifurcation_ratios[1] == pytest.approx(2.0)
        # Rb_2 = N_2 / N_3 = 2 / 1 = 2.0
        assert stats.bifurcation_ratios[2] == pytest.approx(2.0)


class TestStrahlerDifferentOrders:
    """Test Strahler ordering with different order combinations."""

    def test_different_orders_higher_continues(self):
        """When different orders join, higher order continues."""
        segments = [
            StreamSegment(1, [], length_km=1.0),  # Order 1
            StreamSegment(2, [], length_km=1.0),  # Order 1
            StreamSegment(3, [1, 2], length_km=1.0),  # Order 2
            StreamSegment(4, [], length_km=1.0),  # Order 1
            StreamSegment(5, [3, 4], length_km=1.0),  # Order 2 (2 and 1 join)
        ]
        network = StreamNetwork(segments)
        network.classify(OrderingMethod.STRAHLER)

        assert network.segments[5].order == 2  # Higher order continues


class TestBifurcationRatio:
    """Tests for bifurcation_ratio function."""

    def test_normal_calculation(self):
        """Test normal bifurcation ratio calculation."""
        rb = bifurcation_ratio(n_lower=8, n_higher=2)
        assert rb == pytest.approx(4.0)

    def test_typical_range(self):
        """Test bifurcation ratio in typical range."""
        rb = bifurcation_ratio(n_lower=15, n_higher=4)
        assert rb == pytest.approx(3.75)

    def test_zero_higher(self):
        """Test that zero higher order raises error."""
        with pytest.raises(InvalidParameterError, match="cannot be zero"):
            bifurcation_ratio(n_lower=5, n_higher=0)

    def test_negative_counts(self):
        """Test that negative counts raise error."""
        with pytest.raises(InvalidParameterError, match="non-negative"):
            bifurcation_ratio(n_lower=-1, n_higher=2)


class TestDrainageDensity:
    """Tests for drainage_density function."""

    def test_normal_calculation(self):
        """Test normal drainage density calculation."""
        dd = drainage_density(total_length_km=45.0, area_km2=25.0)
        assert dd == pytest.approx(1.8)

    def test_low_density(self):
        """Test low drainage density."""
        dd = drainage_density(total_length_km=10.0, area_km2=50.0)
        assert dd == pytest.approx(0.2)
        assert dd < 1  # Low density

    def test_high_density(self):
        """Test high drainage density."""
        dd = drainage_density(total_length_km=150.0, area_km2=30.0)
        assert dd == pytest.approx(5.0)
        assert dd > 3  # High density

    def test_zero_length(self):
        """Test that zero length raises error."""
        with pytest.raises(InvalidParameterError, match="must be positive"):
            drainage_density(total_length_km=0, area_km2=10.0)

    def test_zero_area(self):
        """Test that zero area raises error."""
        with pytest.raises(InvalidParameterError, match="must be positive"):
            drainage_density(total_length_km=10.0, area_km2=0)


class TestStreamFrequency:
    """Tests for stream_frequency function."""

    def test_normal_calculation(self):
        """Test normal stream frequency calculation."""
        fs = stream_frequency(n_streams=25, area_km2=10.0)
        assert fs == pytest.approx(2.5)

    def test_zero_streams(self):
        """Test with zero streams."""
        fs = stream_frequency(n_streams=0, area_km2=10.0)
        assert fs == pytest.approx(0.0)

    def test_negative_streams(self):
        """Test that negative stream count raises error."""
        with pytest.raises(InvalidParameterError, match="non-negative"):
            stream_frequency(n_streams=-5, area_km2=10.0)

    def test_zero_area(self):
        """Test that zero area raises error."""
        with pytest.raises(InvalidParameterError, match="must be positive"):
            stream_frequency(n_streams=10, area_km2=0)


def _network(spec):
    """Network of ``(segment_id, upstream_ids)`` pairs, each 1 km long."""
    return StreamNetwork(
        [StreamSegment(seg_id, list(up), length_km=1.0) for seg_id, up in spec]
    )


class TestClassifyInvalidGraph:
    """``classify`` rejects networks that have no order.

    A cycle fed by a headwater or an unknown upstream id next to a headwater made
    it loop forever; without any headwater it silently left every order at 0.
    """

    @pytest.mark.parametrize("method", list(OrderingMethod))
    def test_a_cycle_fed_by_a_headwater_is_rejected(self, method):
        network = _network([(1, []), (2, [1, 3]), (3, [2])])
        with pytest.raises(InvalidParameterError) as caught:
            network.classify(method)
        assert caught.value.code == "validation_error"
        assert caught.value.details == {"reason": "cycle", "segments": [2, 3]}
        assert "2 -> 3 -> 2" in str(caught.value)
        assert isinstance(caught.value, ValueError)

    def test_a_cycle_without_a_headwater_is_rejected(self):
        network = _network([(1, [2]), (2, [1])])
        with pytest.raises(InvalidParameterError) as caught:
            network.classify()
        assert caught.value.details == {"reason": "cycle", "segments": [1, 2]}

    def test_a_segment_upstream_of_itself_is_rejected(self):
        network = _network([(1, []), (2, [1, 2])])
        with pytest.raises(InvalidParameterError, match="Segment 2 lists itself"):
            network.classify()

    def test_the_cycle_is_listed_in_flow_order_without_its_downstream_segments(self):
        """5 -> 3 -> 4 -> 5 flows in a circle; 6 only drains it, 1 feeds it."""
        network = _network([(1, []), (5, [4, 1]), (4, [3]), (3, [5]), (6, [3])])
        with pytest.raises(InvalidParameterError) as caught:
            network.classify()
        assert caught.value.details["segments"] == [3, 4, 5]
        assert "3 -> 4 -> 5 -> 3" in str(caught.value)

    @pytest.mark.parametrize(
        "spec",
        [
            [(1, []), (2, [1, 9])],  # next to a headwater: used to loop
            [(1, [9])],  # no headwater: used to leave every order at 0
        ],
    )
    def test_an_unknown_upstream_id_is_rejected(self, spec):
        network = _network(spec)
        with pytest.raises(InvalidParameterError) as caught:
            network.classify()
        assert caught.value.details == {
            "reason": "unknown_upstream",
            "segment_id": spec[-1][0],
            "upstream_id": 9,
            "n_unknown": 1,
        }
        assert f"Segment {spec[-1][0]} lists upstream segment 9" in str(caught.value)
        assert caught.value.hint

    def test_all_unknown_ids_are_counted_and_the_first_is_named(self):
        network = _network([(1, [7, 8]), (2, [9])])
        with pytest.raises(InvalidParameterError) as caught:
            network.classify()
        assert caught.value.details["upstream_id"] == 7
        assert caught.value.details["n_unknown"] == 3

    def test_a_rejected_network_stays_unclassified(self):
        network = _network([(1, []), (2, [1, 3]), (3, [2])])
        with pytest.raises(InvalidParameterError):
            network.classify()
        assert [seg.order for seg in network.segments.values()] == [0, 0, 0]
        with pytest.raises(InvalidParameterError, match="must be classified"):
            network.get_statistics()

    @pytest.mark.parametrize("method", list(OrderingMethod))
    def test_the_order_does_not_depend_on_the_listing_order(self, method):
        """Downstream segments listed before the ones that feed them."""
        spec = [
            (7, [5, 6]),
            (6, [3, 4]),
            (5, [1, 2]),
            (4, []),
            (3, []),
            (2, []),
            (1, []),
        ]
        network = _network(spec)
        network.classify(method)
        expected = {
            OrderingMethod.STRAHLER: {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3},
            OrderingMethod.SHREVE: {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 4},
        }[method]
        assert {
            seg_id: seg.order for seg_id, seg in network.segments.items()
        } == expected


def _links(spec, length_km=1.0):
    """Network of ``(segment_id, upstream_ids)`` links, each ``length_km`` long."""
    return StreamNetwork(
        [StreamSegment(seg_id, list(up), length_km=length_km) for seg_id, up in spec]
    )


# Strahler (1957), Fig. 2 "Method of designating stream orders (Strahler, 1954a,
# p. 344)", p. 914: a fourth-order basin; its table prints 25, 6, 2 and 1 streams of
# orders 1 to 4. The links below transcribe the figure, one per stretch between
# junctions: sources 1-25; order-2 links 101-116; order-3 links 201-207; outlet 301.
STRAHLER_1957_FIG_2 = [
    *[(source, []) for source in range(1, 26)],
    # western order-2 stream: sources 1 + 2, then tributaries 3, 4, 5, 6 join it
    (101, [1, 2]),
    (102, [101, 3]),
    (103, [102, 4]),
    (104, [103, 5]),
    (105, [104, 6]),
    (106, [7, 8]),  # order 2 from sources 7 + 8
    (107, [9, 10]),  # order 2 from sources 9 + 10
    (108, [14, 15]),  # southern order-2 stream from sources 14 + 15 ...
    (109, [108, 16]),  # ... joined by source 16
    # western order-3 stream: 105 + 106, then 107, sources 11, 12, 13 and 109 join it
    (201, [105, 106]),
    (202, [201, 107]),
    (203, [202, 11]),
    (204, [203, 12]),
    (205, [204, 13]),
    (206, [205, 109]),
    # eastern order-2 stream: sources 17 + 18, then tributaries 19 to 23 join it
    (110, [17, 18]),
    (111, [110, 19]),
    (112, [111, 20]),
    (113, [112, 21]),
    (114, [113, 22]),
    (115, [114, 23]),
    (116, [24, 25]),  # order 2 from sources 24 + 25
    (207, [115, 116]),  # eastern order-3 stream
    (301, [206, 207]),  # the fourth-order trunk to the mouth
]


class TestStreamStatistics:
    """The statistics count streams, not the segments (links) that carry them.

    A stream of order u runs from where the order u begins to its junction with a
    stream of equal or higher order (Strahler 1957, Trans. AGU 38(6): 913-920,
    p. 914; Baścik 2006, eqs. 1.2.18-1.2.22): a lower-order tributary does not split
    it. Horton's ratios Rb = N_u / N_(u+1) and Rl = mean L_(u+1) / mean L_u use these
    streams. Each expected value is a published count or a hand count of the network
    written here.
    """

    def test_a_lower_order_tributary_does_not_split_a_stream(self):
        """1 + 2 (1 km each) -> 3 (2 km); 3 + 4 (1 km, order 1) -> 5 (2 km).

        Links 3 and 5 are one order-2 stream of 4 km: N = {1: 3, 2: 1}, Rb = 3 / 1,
        mean L = {1: 3 / 3, 2: 4 / 1}, Rl = 4 / 1 (links: N_2 = 2, Rb 1.5, Rl 2.0).
        """
        network = StreamNetwork(
            [
                StreamSegment(1, [], length_km=1.0),
                StreamSegment(2, [], length_km=1.0),
                StreamSegment(3, [1, 2], length_km=2.0),
                StreamSegment(4, [], length_km=1.0),
                StreamSegment(5, [3, 4], length_km=2.0),
            ],
            area_km2=5.0,
        )
        network.classify(OrderingMethod.STRAHLER)
        stats = network.get_statistics()

        assert stats.segment_counts == {1: 3, 2: 1}
        assert stats.total_lengths_km == {1: pytest.approx(3.0), 2: pytest.approx(4.0)}
        assert stats.mean_lengths_km == {1: pytest.approx(1.0), 2: pytest.approx(4.0)}
        assert stats.bifurcation_ratios == {1: pytest.approx(3.0)}
        assert stats.length_ratios == {1: pytest.approx(4.0)}
        assert stats.drainage_density == pytest.approx(7.0 / 5.0)
        assert network.n_streams == 4

    def test_the_shipped_fixture_network(self):
        """The fixture ``tests/fixtures/network_segments.csv``, 9 links.

        1, 2 -> 3; 4, 5 -> 6; 3, 6 -> 7; 7, 8 -> 9. Link 9 continues the order-3
        stream of 7 (tributary 8 is of order 1), so N = {1: 5, 2: 2, 3: 1}; lengths
        1.2 + 0.8 + 1.0 + 0.9 + 0.7 = 4.6, 1.5 + 1.4 = 2.9 and 2.2 + 3.0 = 5.2 km;
        with A = 12 km2, Fs = 8 / 12.
        """
        network = StreamNetwork(
            [
                StreamSegment(1, [], length_km=1.2),
                StreamSegment(2, [], length_km=0.8),
                StreamSegment(3, [1, 2], length_km=1.5),
                StreamSegment(4, [], length_km=1.0),
                StreamSegment(5, [], length_km=0.9),
                StreamSegment(6, [4, 5], length_km=1.4),
                StreamSegment(7, [3, 6], length_km=2.2),
                StreamSegment(8, [], length_km=0.7),
                StreamSegment(9, [7, 8], length_km=3.0),
            ],
            area_km2=12.0,
        )
        network.classify(OrderingMethod.STRAHLER)
        stats = network.get_statistics()

        assert stats.max_order == 3
        assert stats.segment_counts == {1: 5, 2: 2, 3: 1}
        assert stats.mean_lengths_km == {
            1: pytest.approx(0.92),
            2: pytest.approx(1.45),
            3: pytest.approx(5.2),
        }
        assert stats.bifurcation_ratios == {
            1: pytest.approx(2.5),
            2: pytest.approx(2.0),
        }
        assert stats.length_ratios == {
            1: pytest.approx(1.45 / 0.92),
            2: pytest.approx(5.2 / 1.45),
        }
        assert stats.total_stream_length_km == pytest.approx(12.7)
        assert network.n_streams == 8
        assert stream_frequency(network.n_streams, 12.0) == pytest.approx(8 / 12)

    def test_strahler_1957_figure_2_has_the_published_stream_numbers(self):
        """25, 6, 2 and 1 streams of orders 1 to 4 (49 links: 25, 16, 7 and 1)."""
        network = _links(STRAHLER_1957_FIG_2)
        network.classify(OrderingMethod.STRAHLER)
        stats = network.get_statistics()

        assert stats.max_order == 4
        assert stats.segment_counts == {1: 25, 2: 6, 3: 2, 4: 1}
        assert stats.bifurcation_ratios == {
            1: pytest.approx(25 / 6),
            2: pytest.approx(6 / 2),
            3: pytest.approx(2 / 1),
        }
        # 1 km links: the total length of an order is its number of links
        assert stats.total_lengths_km == {1: 25.0, 2: 16.0, 3: 7.0, 4: 1.0}
        assert stats.mean_lengths_km == {
            1: pytest.approx(1.0),
            2: pytest.approx(16 / 6),
            3: pytest.approx(7 / 2),
            4: pytest.approx(1.0),
        }
        assert network.n_streams == 34

    def test_the_listing_order_of_the_links_changes_nothing(self):
        forward = _links(STRAHLER_1957_FIG_2)
        backward = _links(STRAHLER_1957_FIG_2[::-1])
        forward.classify(OrderingMethod.STRAHLER)
        backward.classify(OrderingMethod.STRAHLER)
        assert forward.get_statistics() == backward.get_statistics()

    def test_a_pass_through_segment_continues_its_stream(self):
        """1 + 2 -> 3 -> 4 (4 has one upstream segment): 3 and 4 are one stream."""
        for method in OrderingMethod:
            network = _links([(1, []), (2, []), (3, [1, 2]), (4, [3])])
            network.classify(method)
            stats = network.get_statistics()
            assert stats.segment_counts == {1: 2, 2: 1}, method
            assert stats.mean_lengths_km == {1: 1.0, 2: 2.0}, method

    def test_shreve_links_join_only_pass_through_segments(self):
        """Shreve (1966) magnitudes stay; a link runs between confluences.

        Side-tributary network with a pass-through split of the outlet link (5 -> 6):
        magnitudes 1, 1, 2, 1, 3, 3; links of magnitude 1: 1, 2, 4; 2: 3; 3: 5 + 6.
        """
        network = _links(
            [(1, []), (2, []), (3, [1, 2]), (4, []), (5, [3, 4]), (6, [5])]
        )
        network.classify(OrderingMethod.SHREVE)
        stats = network.get_statistics()

        assert {seg_id: seg.order for seg_id, seg in network.segments.items()} == {
            1: 1,
            2: 1,
            3: 2,
            4: 1,
            5: 3,
            6: 3,
        }
        assert stats.max_order == 3
        assert stats.segment_counts == {1: 3, 2: 1, 3: 1}
        assert stats.mean_lengths_km == {1: 1.0, 2: 1.0, 3: 2.0}
        assert stats.total_stream_length_km == pytest.approx(6.0)

    @pytest.mark.parametrize(
        "spec", [STRAHLER_1957_FIG_2, [(1, []), (2, []), (3, [1, 2])]]
    )
    def test_shreve_magnitudes_have_no_horton_ratios(self, spec):
        """Horton's laws are defined on Strahler orders, not on Shreve magnitudes."""
        network = _links(spec)
        network.classify(OrderingMethod.SHREVE)
        stats = network.get_statistics()
        assert stats.bifurcation_ratios == {}
        assert stats.length_ratios == {}

    def test_the_number_of_streams_is_strahler_s_for_either_classification(self):
        """Fs counts Strahler streams; a Shreve run leaves its magnitudes in place."""
        network = _links(STRAHLER_1957_FIG_2)
        network.classify(OrderingMethod.SHREVE)
        assert network.n_streams == 25 + 6 + 2 + 1
        assert network.segments[301].order == 25
        assert network.get_statistics().max_order == 25

    def test_the_number_of_streams_needs_a_network_with_an_order(self):
        with pytest.raises(InvalidParameterError) as caught:
            _ = _links([(1, []), (2, [1, 3]), (3, [2])]).n_streams
        assert caught.value.details["reason"] == "cycle"
