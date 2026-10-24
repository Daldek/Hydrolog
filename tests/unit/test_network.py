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

    def test_get_segments_by_order(self, complex_network):
        """Test filtering segments by order."""
        complex_network.classify(OrderingMethod.STRAHLER)

        order1 = complex_network.get_segments_by_order(1)
        assert len(order1) == 4

        order2 = complex_network.get_segments_by_order(2)
        assert len(order2) == 2

        order3 = complex_network.get_segments_by_order(3)
        assert len(order3) == 1


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
