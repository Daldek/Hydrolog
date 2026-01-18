"""Stream ordering methods for river network classification.

This module provides methods for classifying river networks using
various stream ordering systems (Strahler, Shreve).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


class OrderingMethod(Enum):
    """Stream ordering method enumeration."""

    STRAHLER = "strahler"
    SHREVE = "shreve"


@dataclass
class StreamSegment:
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
class NetworkStatistics:
    """
    Statistics of a classified river network.

    Attributes
    ----------
    max_order : int
        Maximum stream order in the network.
    segment_counts : dict[int, int]
        Number of segments for each order.
    total_lengths_km : dict[int, float]
        Total length of segments for each order [km].
    mean_lengths_km : dict[int, float]
        Mean length of segments for each order [km].
    bifurcation_ratios : dict[int, float]
        Bifurcation ratio between consecutive orders.
    length_ratios : dict[int, float]
        Length ratio between consecutive orders.
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
    drainage_density: Optional[float] = None


class StreamNetwork:
    """
    River network classification and analysis.

    This class provides methods for stream ordering using Strahler
    and Shreve methods, and calculates network statistics including
    bifurcation ratios and drainage density.

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
    Strahler ordering:
    - Order 1: Headwater streams (no tributaries)
    - When two streams of order n join: order n+1
    - When streams of different orders join: higher order continues

    Shreve ordering:
    - Order 1: Headwater streams
    - Orders are additive at confluences
    """

    def __init__(
        self,
        segments: list[StreamSegment],
        area_km2: Optional[float] = None,
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
            raise InvalidParameterError(
                f"area_km2 must be positive, got {area_km2}"
            )

        self.segments = {seg.segment_id: seg for seg in segments}
        self.area_km2 = area_km2
        self._classified = False
        self._method: Optional[OrderingMethod] = None

    @property
    def n_segments(self) -> int:
        """Number of segments in the network."""
        return len(self.segments)

    def _find_headwaters(self) -> list[int]:
        """Find headwater segments (no upstream tributaries)."""
        return [
            seg_id
            for seg_id, seg in self.segments.items()
            if not seg.upstream_ids
        ]

    def _get_downstream_segments(self, segment_id: int) -> list[int]:
        """Find segments that have this segment as upstream."""
        downstream = []
        for seg_id, seg in self.segments.items():
            if segment_id in seg.upstream_ids:
                downstream.append(seg_id)
        return downstream

    def classify(self, method: OrderingMethod = OrderingMethod.STRAHLER) -> None:
        """
        Classify stream network using specified ordering method.

        Parameters
        ----------
        method : OrderingMethod
            Ordering method (STRAHLER or SHREVE).
        """
        self._method = method

        # Reset all orders
        for seg in self.segments.values():
            seg.order = 0

        # Find headwaters and assign order 1
        headwaters = self._find_headwaters()
        for seg_id in headwaters:
            self.segments[seg_id].order = 1

        # Process network from headwaters downstream
        processed = set(headwaters)
        to_process = set()

        # Find initial downstream segments
        for seg_id in headwaters:
            to_process.update(self._get_downstream_segments(seg_id))

        while to_process:
            next_round = set()

            for seg_id in to_process:
                seg = self.segments[seg_id]

                # Check if all upstream segments are processed
                upstream_orders = []
                all_processed = True
                for up_id in seg.upstream_ids:
                    if up_id not in processed:
                        all_processed = False
                        break
                    upstream_orders.append(self.segments[up_id].order)

                if not all_processed:
                    next_round.add(seg_id)
                    continue

                # Calculate order based on method
                if method == OrderingMethod.STRAHLER:
                    seg.order = self._strahler_order(upstream_orders)
                else:  # SHREVE
                    seg.order = self._shreve_order(upstream_orders)

                processed.add(seg_id)

                # Add downstream segments
                next_round.update(self._get_downstream_segments(seg_id))

            # Remove already processed
            to_process = next_round - processed

        self._classified = True

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

        # Group segments by order
        orders: dict[int, list[StreamSegment]] = {}
        for seg in self.segments.values():
            if seg.order not in orders:
                orders[seg.order] = []
            orders[seg.order].append(seg)

        max_order = max(orders.keys())

        # Calculate counts and lengths
        segment_counts: dict[int, int] = {}
        total_lengths: dict[int, float] = {}
        mean_lengths: dict[int, float] = {}

        for order, segs in orders.items():
            segment_counts[order] = len(segs)
            total_lengths[order] = sum(s.length_km for s in segs)
            mean_lengths[order] = total_lengths[order] / len(segs) if segs else 0.0

        # Calculate bifurcation ratios (Rb = N_i / N_{i+1})
        bifurcation_ratios: dict[int, float] = {}
        for order in range(1, max_order):
            if order + 1 in segment_counts and segment_counts[order + 1] > 0:
                bifurcation_ratios[order] = (
                    segment_counts[order] / segment_counts[order + 1]
                )

        # Calculate length ratios (Rl = L_{i+1} / L_i)
        length_ratios: dict[int, float] = {}
        for order in range(1, max_order):
            if mean_lengths[order] > 0 and order + 1 in mean_lengths:
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

    def get_segments_by_order(self, order: int) -> list[StreamSegment]:
        """
        Get all segments of a specific order.

        Parameters
        ----------
        order : int
            Stream order to filter by.

        Returns
        -------
        list[StreamSegment]
            Segments with the specified order.
        """
        return [seg for seg in self.segments.values() if seg.order == order]


def bifurcation_ratio(n_lower: int, n_higher: int) -> float:
    """
    Calculate bifurcation ratio between two stream orders.

    The bifurcation ratio (Rb) is defined as the ratio of the number
    of streams of a given order to the number of streams of the next
    higher order.

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
    Typical values:
    - Rb = 3-5 for natural streams
    - Rb < 3 suggests structural control
    - Rb > 5 suggests elongated basin

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

    Stream frequency (Fs) is the number of stream segments
    per unit area.

    Parameters
    ----------
    n_streams : int
        Total number of stream segments.
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
