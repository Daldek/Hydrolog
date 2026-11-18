"""Stream ordering methods for river network classification.

This module provides methods for classifying river networks using
various stream ordering systems (Strahler, Shreve).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.network._graph import UnknownUpstream, UpstreamCycle, upstream_first


class OrderingMethod(Enum):
    """Stream ordering method enumeration."""

    STRAHLER = "strahler"
    SHREVE = "shreve"


@dataclass
class StreamSegment(JsonResultMixin):
    """
    Represents a single stream segment in a river network.

    Attributes
    ----------
    segment_id : int
        Unique identifier for the segment.
    upstream_ids : list[int]
        IDs of segments flowing into this segment.
    length_km : float
        Length of the segment [km].
    order : int
        Stream order (assigned after classification).
    """

    segment_id: int
    upstream_ids: list[int]
    length_km: float = 0.0
    order: int = 0


@dataclass
class NetworkStatistics(JsonResultMixin):
    """
    Statistics of a classified river network.

    The counts and mean lengths are those of streams, not of segments. A segment
    continues the stream of the segment upstream of it that has the same order, so a
    stream is the chain of segments from where its order begins to its junction with a
    stream of an equal or higher order (Strahler 1957): a tributary of a lower order
    does not split it. Applied to Shreve magnitudes, the same rule joins only a
    segment with one upstream segment to it, which gives Shreve's (1966) links between
    confluences.

    Attributes
    ----------
    max_order : int
        Maximum stream order in the network.
    segment_counts : dict[int, int]
        Number of streams N_u of each order u (for Shreve, the number of links of
        each magnitude). The number of segments is ``StreamNetwork.n_segments``.
    total_lengths_km : dict[int, float]
        Total length of the segments of each order [km].
    mean_lengths_km : dict[int, float]
        Mean stream length of each order: total length / number of streams [km].
    bifurcation_ratios : dict[int, float]
        Horton's bifurcation ratio Rb = N_u / N_(u+1), keyed by u; Strahler orders
        only (empty for Shreve magnitudes: Horton's laws are defined on Strahler
        orders).
    length_ratios : dict[int, float]
        Horton's length ratio Rl = mean length_(u+1) / mean length_u, keyed by u;
        Strahler orders only (empty for Shreve), none above an order whose streams
        have zero length.
    total_stream_length_km : float
        Total length of all streams [km].
    drainage_density : float
        Drainage density if area provided [km/km²].
    """

    max_order: int
    segment_counts: dict[int, int]
    total_lengths_km: dict[int, float]
    mean_lengths_km: dict[int, float]
    bifurcation_ratios: dict[int, float]
    length_ratios: dict[int, float]
    total_stream_length_km: float
    drainage_density: float | None = None


class StreamNetwork:
    """
    River network classification and analysis.

    This class provides methods for stream ordering using Strahler
    and Shreve methods, and calculates network statistics including
    stream numbers, Horton's bifurcation and length ratios and drainage density.

    Parameters
    ----------
    segments : list[StreamSegment]
        List of stream segments defining the network.
    area_km2 : float, optional
        Watershed area for drainage density calculation [km²].

    Examples
    --------
    >>> # Define a simple network
    >>> segments = [
    ...     StreamSegment(1, [], length_km=1.0),  # Headwater
    ...     StreamSegment(2, [], length_km=0.8),  # Headwater
    ...     StreamSegment(3, [1, 2], length_km=2.0),  # Junction
    ... ]
    >>> network = StreamNetwork(segments, area_km2=10.0)
    >>> network.classify(OrderingMethod.STRAHLER)
    >>> stats = network.get_statistics()
    >>> print(f"Max order: {stats.max_order}")

    Notes
    -----
    A segment is a link: the channel between two junctions, or between a source
    or a junction and the outlet; a segment may also have one upstream segment (a
    pass-through split of a link).

    Strahler ordering (Strahler 1952, 1957):
    - Order 1: Headwater streams (no tributaries)
    - When two streams of order n join: order n+1
    - When streams of different orders join: higher order continues

    Shreve ordering (Shreve 1966):
    - Order 1: Headwater streams
    - Orders are additive at confluences

    The statistics count streams: a stream of order u runs from where order u begins
    to its junction with a stream of an equal or higher order (Strahler 1957), so
    the segments below a junction with a lower-order tributary continue it.
    """

    def __init__(
        self,
        segments: list[StreamSegment],
        area_km2: float | None = None,
    ) -> None:
        """
        Initialize stream network.

        Parameters
        ----------
        segments : list[StreamSegment]
            List of stream segments.
        area_km2 : float, optional
            Watershed area [km²].

        Raises
        ------
        InvalidParameterError
            If segments list is empty or area is non-positive.
        """
        if not segments:
            raise InvalidParameterError("segments list cannot be empty")

        if area_km2 is not None and area_km2 <= 0:
            raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")

        self.segments = {seg.segment_id: seg for seg in segments}
        self.area_km2 = area_km2
        self._classified = False
        self._method: OrderingMethod | None = None

    @property
    def n_segments(self) -> int:
        """Number of segments in the network."""
        return len(self.segments)

    @property
    def n_streams(self) -> int:
        """Number of Strahler streams of all orders, whatever the classification.

        Horton's (1945) stream frequency counts them (:func:`stream_frequency`;
        Strahler 1957; Baścik 2006, eq. 1.2.22). Computed from Strahler orders of
        the segments without changing their ``order``, so it is the same after a
        Shreve classification.

        Raises
        ------
        InvalidParameterError
            If the network has no order (a cycle or an unknown upstream id), as in
            :meth:`classify`.
        """
        return sum(self._stream_counts(self._orders(OrderingMethod.STRAHLER)).values())

    def classify(self, method: OrderingMethod = OrderingMethod.STRAHLER) -> None:
        """
        Classify stream network using specified ordering method.

        Parameters
        ----------
        method : OrderingMethod
            Ordering method (STRAHLER or SHREVE).

        Raises
        ------
        InvalidParameterError
            If a segment lists an upstream id that is not in the network
            (``details``: ``reason="unknown_upstream"``, ``segment_id``,
            ``upstream_id``, ``n_unknown``) or the segments form a cycle, a
            segment being upstream of itself (``details``: ``reason="cycle"``,
            ``segments``: the segments of one cycle in flow order). Such a network
            has no order; the segments are left unchanged.
        """
        orders = self._orders(method)
        for seg_id, seg in self.segments.items():
            seg.order = orders[seg_id]
        self._method = method
        self._classified = True

    def _orders(self, method: OrderingMethod) -> dict[int, int]:
        """Order of every segment by ``method``; the segments are not changed.

        Raises the errors of :meth:`classify` for a network without an order.
        """
        try:
            order = upstream_first(
                {seg_id: seg.upstream_ids for seg_id, seg in self.segments.items()}
            )
        except UnknownUpstream as unknown:
            raise InvalidParameterError(
                f"Segment {unknown.key} lists upstream segment {unknown.upstream}, "
                "which is not in the network",
                details={
                    "reason": "unknown_upstream",
                    "segment_id": unknown.key,
                    "upstream_id": unknown.upstream,
                    "n_unknown": unknown.count,
                },
                hint="Every id in upstream_ids must be the segment_id of a segment "
                "of the network.",
            ) from unknown
        except UpstreamCycle as looped:
            cycle = looped.members
            if len(cycle) == 1:
                message = f"Segment {cycle[0]} lists itself as upstream"
            else:
                path = " -> ".join(str(seg_id) for seg_id in [*cycle, cycle[0]])
                message = f"The segments form a cycle: {path}"
            raise InvalidParameterError(
                message,
                details={"reason": "cycle", "segments": cycle},
                hint="A segment flows into each segment that lists it in upstream_ids; "
                "remove the link that closes the loop.",
            ) from looped

        # Process the network from the headwaters downstream: a segment is ready
        # when all its upstream segments have an order.
        orders: dict[int, int] = {}
        for seg_id in order:
            upstream_orders = [
                orders[up_id] for up_id in self.segments[seg_id].upstream_ids
            ]
            if method == OrderingMethod.STRAHLER:
                orders[seg_id] = self._strahler_order(upstream_orders)
            else:  # SHREVE
                orders[seg_id] = self._shreve_order(upstream_orders)
        return orders

    def _strahler_order(self, upstream_orders: list[int]) -> int:
        """Calculate Strahler order from upstream orders."""
        if not upstream_orders:
            return 1

        max_order = max(upstream_orders)
        count_max = upstream_orders.count(max_order)

        if count_max >= 2:
            return max_order + 1
        return max_order

    def _shreve_order(self, upstream_orders: list[int]) -> int:
        """Calculate Shreve order from upstream orders."""
        if not upstream_orders:
            return 1
        return sum(upstream_orders)

    def get_statistics(self) -> NetworkStatistics:
        """
        Calculate network statistics.

        Returns
        -------
        NetworkStatistics
            Complete network statistics.

        Raises
        ------
        InvalidParameterError
            If network has not been classified yet.
        """
        if not self._classified:
            raise InvalidParameterError(
                "Network must be classified first. Call classify() method."
            )

        orders = {seg_id: seg.order for seg_id, seg in self.segments.items()}
        segment_counts = self._stream_counts(orders)
        max_order = max(segment_counts)

        # Lengths: total of the segments of an order, mean over its streams
        total_lengths = dict.fromkeys(segment_counts, 0.0)
        for seg in self.segments.values():
            total_lengths[seg.order] += seg.length_km
        mean_lengths = {
            order: total_lengths[order] / count
            for order, count in segment_counts.items()
        }

        # Horton's ratios Rb = N_u / N_(u+1) and Rl = L_(u+1) / L_u: Strahler orders
        # only (contiguous from 1 to max_order, every order has a stream)
        bifurcation_ratios: dict[int, float] = {}
        length_ratios: dict[int, float] = {}
        if self._method == OrderingMethod.STRAHLER:
            for order in range(1, max_order):
                bifurcation_ratios[order] = (
                    segment_counts[order] / segment_counts[order + 1]
                )
                if mean_lengths[order] > 0:
                    length_ratios[order] = mean_lengths[order + 1] / mean_lengths[order]

        # Total stream length
        total_length = sum(total_lengths.values())

        # Drainage density
        drainage_density = None
        if self.area_km2 is not None:
            drainage_density = total_length / self.area_km2

        return NetworkStatistics(
            max_order=max_order,
            segment_counts=segment_counts,
            total_lengths_km=total_lengths,
            mean_lengths_km=mean_lengths,
            bifurcation_ratios=bifurcation_ratios,
            length_ratios=length_ratios,
            total_stream_length_km=total_length,
            drainage_density=drainage_density,
        )

    def _stream_counts(self, orders: Mapping[int, int]) -> dict[int, int]:
        """Count the streams of each order, ascending by order.

        A segment continues the stream of an upstream segment of its own order; a
        segment with none is where a stream begins. Strahler: a source, or the
        junction of two streams of the order below (a lower-order tributary keeps
        the order, so the stream goes on). Shreve: the magnitude adds up at every
        confluence, so only a segment with one upstream segment continues one.
        """
        counts: dict[int, int] = {}
        for seg_id, seg in self.segments.items():
            order = orders[seg_id]
            if all(orders[up_id] != order for up_id in seg.upstream_ids):
                counts[order] = counts.get(order, 0) + 1
        return dict(sorted(counts.items()))


def bifurcation_ratio(n_lower: int, n_higher: int) -> float:
    """
    Calculate bifurcation ratio between two stream orders.

    The bifurcation ratio (Rb) is defined as the ratio of the number
    of streams of a given order to the number of streams of the next
    higher order (Horton 1945; Strahler 1957), streams in Strahler's sense
    (:attr:`NetworkStatistics.segment_counts`), not segments between junctions.

    Parameters
    ----------
    n_lower : int
        Number of streams of lower order.
    n_higher : int
        Number of streams of higher order.

    Returns
    -------
    float
        Bifurcation ratio Rb = N_i / N_{i+1}.

    Raises
    ------
    InvalidParameterError
        If n_higher is zero or counts are negative.

    Notes
    -----
    Horton's law of stream numbers makes Rb nearly constant across orders. It is
    about 3 to 5 where geological structure does not distort the drainage pattern
    ("highly stable ... except where powerful geologic controls dominate",
    Strahler 1957, p. 914: 3.52 in his example; Coates 1956: 2.8 to 5.1); Rb above
    about 5 indicates structural control (Strahler 1964, cited by Rai et al.,
    Applied Water Science, doi:10.1007/s13201-014-0238-y).

    Examples
    --------
    >>> rb = bifurcation_ratio(n_lower=8, n_higher=2)
    >>> print(f"Rb = {rb}")
    Rb = 4.0
    """
    if n_lower < 0 or n_higher < 0:
        raise InvalidParameterError("Stream counts must be non-negative")

    if n_higher == 0:
        raise InvalidParameterError("n_higher cannot be zero")

    return n_lower / n_higher


def drainage_density(total_length_km: float, area_km2: float) -> float:
    """
    Calculate drainage density.

    Drainage density (Dd) is the total length of all streams
    divided by the watershed area.

    Parameters
    ----------
    total_length_km : float
        Total length of all streams [km].
    area_km2 : float
        Watershed area [km²].

    Returns
    -------
    float
        Drainage density [km/km²].

    Raises
    ------
    InvalidParameterError
        If values are non-positive.

    Notes
    -----
    Interpretation:
    - Dd < 1: Low drainage density (permeable soils)
    - Dd = 1-3: Moderate drainage density
    - Dd > 3: High drainage density (impermeable soils)

    Examples
    --------
    >>> dd = drainage_density(total_length_km=45.0, area_km2=25.0)
    >>> print(f"Dd = {dd} km/km²")
    Dd = 1.8 km/km²
    """
    if total_length_km <= 0:
        raise InvalidParameterError(
            f"total_length_km must be positive, got {total_length_km}"
        )

    if area_km2 <= 0:
        raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")

    return total_length_km / area_km2


def stream_frequency(n_streams: int, area_km2: float) -> float:
    """
    Calculate stream frequency.

    Stream frequency (Fs) is the number of streams per unit area (Horton 1945;
    Strahler 1957; Baścik 2006, eq. 1.2.22): streams in Strahler's sense, of all
    orders (:attr:`StreamNetwork.n_streams`), not segments between junctions.

    Parameters
    ----------
    n_streams : int
        Total number of streams.
    area_km2 : float
        Watershed area [km²].

    Returns
    -------
    float
        Stream frequency [1/km²].

    Raises
    ------
    InvalidParameterError
        If values are non-positive.

    Examples
    --------
    >>> fs = stream_frequency(n_streams=25, area_km2=10.0)
    >>> print(f"Fs = {fs} streams/km²")
    Fs = 2.5 streams/km²
    """
    if n_streams < 0:
        raise InvalidParameterError(f"n_streams must be non-negative, got {n_streams}")

    if area_km2 <= 0:
        raise InvalidParameterError(f"area_km2 must be positive, got {area_km2}")

    return n_streams / area_km2
