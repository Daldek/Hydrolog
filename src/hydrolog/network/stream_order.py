"""Stream ordering methods for river network classification.

This module provides methods for classifying river networks using
various stream ordering systems (Strahler, Shreve).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry._sources import AREA, BASCIK, BASCIK_URL
from hydrolog.network._graph import UnknownUpstream, UpstreamCycle, upstream_first
from hydrolog.nogat_formulas import (
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)


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
    Max order: 2

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
        """Calculate Strahler order from upstream orders (:func:`strahler_order`)."""
        return strahler_order([float(order) for order in upstream_orders])

    def _shreve_order(self, upstream_orders: list[int]) -> int:
        """Calculate Shreve magnitude from upstream ones (:func:`shreve_magnitude`)."""
        return shreve_magnitude([float(order) for order in upstream_orders])

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
                bifurcation_ratios[order] = bifurcation_ratio(
                    segment_counts[order], segment_counts[order + 1]
                )
                if mean_lengths[order] > 0:
                    length_ratios[order] = length_ratio(
                        mean_lengths[order], mean_lengths[order + 1]
                    )

        # Total stream length
        total_length = sum(total_lengths.values())

        # Drainage density
        density = None
        if self.area_km2 is not None:
            density = drainage_density(total_length, self.area_km2)

        return NetworkStatistics(
            max_order=max_order,
            segment_counts=segment_counts,
            total_lengths_km=total_lengths,
            mean_lengths_km=mean_lengths,
            bifurcation_ratios=bifurcation_ratios,
            length_ratios=length_ratios,
            total_stream_length_km=total_length,
            drainage_density=density,
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


# --- the specs of the network's indices (Nogat CMP-2.1) ------------------------------

_STRAHLER_1957 = Source(
    citation="Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. "
    "Transactions, American Geophysical Union 38(6): 913-920",
    locator="stream orders, the numbers and mean lengths of the streams of each order "
    "and Horton's laws (not opened; the definitions as Baścik 2006 gives them)",
    url="https://doi.org/10.1029/TR038i006p00913",
)
_BASCIK_ORDERS = Source(
    citation=BASCIK,
    locator="p. 28: Strahler's orders: a source stream is of order 1, two streams of "
    "order u form one of order u + 1, and where streams of different orders join, the "
    "stream below keeps the higher order",
    url=BASCIK_URL,
)
_BASCIK_LAWS = Source(
    citation=BASCIK,
    locator="eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the "
    "bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio "
    "of the mean lengths of the streams of consecutive orders and the frequency of "
    "streams, the number of streams of all orders over A",
    url=BASCIK_URL,
)
_FIXTURE = (
    "Hydrolog's example network tests/fixtures/network_segments.csv, the example of "
    "network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2"
)
_COUNT_TEST = 1.0e7
_COUNT_REASON = (
    "ten million streams: a D8 network on 10^8 cells, a 10 m DEM of 10,000 km2, has "
    "fewer sources than cells"
)
_TOTAL_LENGTH_TEST = 1.0e7
_TOTAL_LENGTH_REASON = (
    "ten million km: a drainage density of 10 km/km2 over a million km2, beyond any "
    "network a DEM of Poland gives"
)
_GAPS = "type cases of every input with nan: a gap is refused"


def _fixture(what: str) -> Source:
    return Source(citation=_FIXTURE, locator=what)


def _whole(*names: str) -> Callable[[Values], bool]:
    def check(x: Values) -> bool:
        return all(float(x.real(name)).is_integer() for name in names)

    return check


def _exact_quotients(
    output: str,
    names: tuple[str, str],
    points: tuple[tuple[float, float], ...],
    reason: str,
) -> Callable[[Callable[..., Values]], None]:
    """Return a limit: the index is the exact rational quotient, rounded once."""

    def check(run: Callable[..., Values]) -> None:
        for upper, lower in points:
            exact = Fraction(upper) / Fraction(lower)
            assert_within(
                run(**{names[0]: upper, names[1]: lower}).real(output),
                float(exact),
                rel=1.2e-16,
                reason=reason,
            )

    return check


_ROUNDED_ONCE = (
    "the exact rational quotient of the float inputs, which float64 division rounds "
    "once: at most half a unit in the last place"
)

BIFURCATION_RATIO: Final = FormulaSpec(
    name="bifurcation_ratio",
    title="Horton's bifurcation ratio of the streams of two consecutive orders",
    function="hydrolog.network.stream_order.bifurcation_ratio",
    family="index",
    equation="Rb = N_u / N_(u+1)",
    latex=r"R_b = \frac{N_u}{N_{u+1}}",
    variables=(
        Variable(
            name="n_lower",
            symbol="N_u",
            unit="-",
            description="Number of Strahler streams of order u.",
            physical=Range(low=2.0, test_high=_COUNT_TEST, test_reason=_COUNT_REASON),
            applicability="unstated",
            typical=Range(
                low=2.0, high=5.0, source=_fixture("5 and 2 streams of orders 1 and 2")
            ),
        ),
        Variable(
            name="n_higher",
            symbol="N_{u+1}",
            unit="-",
            description="Number of Strahler streams of order u + 1.",
            physical=Range(low=1.0, test_high=_COUNT_TEST, test_reason=_COUNT_REASON),
            applicability="unstated",
            typical=Range(
                low=1.0, high=2.0, source=_fixture("2 and 1 streams of orders 2 and 3")
            ),
        ),
    ),
    outputs=(
        Output(
            name="bifurcation_ratio",
            unit="-",
            symbol="R_b",
            description="Bifurcation ratio of orders u and u + 1.",
            physical=Range(low=2.0),
        ),
    ),
    sources=(_BASCIK_LAWS, _STRAHLER_1957),
    constraints=(
        Constraint(
            name="whole_numbers",
            cls="physical",
            check=_whole("n_lower", "n_higher"),
            text="N_u and N_(u+1) are numbers of streams, whole numbers",
            source=_BASCIK_LAWS,
            satisfied={"n_lower": 5.0, "n_higher": 2.0},
            violated={"n_lower": 5.5, "n_higher": 2.0},
        ),
        Constraint(
            name="two_streams_per_junction",
            cls="physical",
            check=lambda x: x.real("n_lower") >= 2.0 * x.real("n_higher"),
            text="N_u >= 2 N_(u+1): every stream of order u + 1 begins where at least "
            "two streams of order u end, and a stream ends once, so Rb >= 2",
            source=_BASCIK_ORDERS,
            satisfied={"n_lower": 5.0, "n_higher": 2.0},
            boundary={"n_lower": 4.0, "n_higher": 2.0},
            violated={"n_lower": 3.0, "n_higher": 2.0},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"n_lower": 1, "n_higher": -1},
        scalings=(
            Scaling(
                name="counts",
                inputs={"n_lower": 1, "n_higher": 1},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0, reason="both counts doubled: the same quotient, exactly"
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="Rb is the exact quotient of the counts, rounded once",
                check=_exact_quotients(
                    "bifurcation_ratio",
                    ("n_lower", "n_higher"),
                    ((5.0, 2.0), (2.0, 1.0), (139.0, 46.0), (9_999_999.0, 3.0)),
                    _ROUNDED_ONCE,
                ),
            ),
        ),
    ),
    validation="none: Horton's law of stream numbers makes Rb nearly constant across "
    "orders; its sources report ranges of Rb, not its agreement with a quantity",
    formula_version=1,
    status="oracle only",
    conventions=(
        (
            "N_u counts Strahler streams, a stream of order u running from where the "
            "order begins to its junction with a stream of an equal or higher order, "
            "not the links between junctions (StreamNetwork.get_statistics)"
        ),
        (
            "Horton's ratios are defined on Strahler orders only: Shreve magnitudes "
            "get none"
        ),
    ),
    traps={
        "difference_denominator": "none of the denominator is a difference: "
        "N_(u+1) >= 1 by its physical range, so no division by zero",
        "gap_propagation": _GAPS,
    },
    oracles=(
        Oracle(
            kind="exact",
            description="N_u / N_(u+1) in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_network.py (limit exact_rational)",
        ),
        Oracle(
            kind="algorithm",
            description="the streams of a network counted as the connected runs of "
            "links of one order (union-find), another algorithm than the code's rule",
            test="tests/unit/test_formulas_network.py "
            "(test_streams_are_the_runs_of_links_of_one_order)",
        ),
    ),
    base={"n_lower": 5.0, "n_higher": 2.0},
)

LENGTH_RATIO: Final = FormulaSpec(
    name="length_ratio",
    title="Horton's length ratio of the streams of two consecutive orders",
    function="hydrolog.network.stream_order.length_ratio",
    family="index",
    equation="Rl = mean L_(u+1) / mean L_u",
    latex=r"R_l = \frac{\bar L_{u+1}}{\bar L_u}",
    variables=(
        Variable(
            name="mean_length_lower_km",
            symbol=r"\bar L_u",
            unit="km",
            description="Mean length of the Strahler streams of order u.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=_TOTAL_LENGTH_TEST,
                test_reason=_TOTAL_LENGTH_REASON,
            ),
            applicability="unstated",
            typical=Range(
                low=0.9,
                high=5.2,
                source=_fixture("mean lengths of 0.92, 1.45 and 5.2 km of orders 1-3"),
            ),
        ),
        Variable(
            name="mean_length_higher_km",
            symbol=r"\bar L_{u+1}",
            unit="km",
            description="Mean length of the Strahler streams of order u + 1.",
            physical=Range(
                low=0.0, test_high=_TOTAL_LENGTH_TEST, test_reason=_TOTAL_LENGTH_REASON
            ),
            applicability="unstated",
            typical=Range(
                low=0.9,
                high=5.2,
                source=_fixture("mean lengths of 0.92, 1.45 and 5.2 km of orders 1-3"),
            ),
        ),
    ),
    outputs=(
        Output(
            name="length_ratio",
            unit="-",
            symbol="R_l",
            description="Length ratio of orders u and u + 1.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_BASCIK_LAWS, _STRAHLER_1957),
    constraints=(
        Constraint(
            name="within_float64",
            cls="precondition",
            check=lambda x: math.isfinite(
                x.real("mean_length_higher_km") / x.real("mean_length_lower_km")
            ),
            text="mean L_(u+1) / mean L_u lies within float64",
            source=_BASCIK_LAWS,
            satisfied={"mean_length_lower_km": 1.45, "mean_length_higher_km": 5.2},
            violated={"mean_length_lower_km": 5e-324, "mean_length_higher_km": 5.2},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"mean_length_lower_km": -1, "mean_length_higher_km": 1},
        scalings=(
            Scaling(
                name="units_of_length",
                inputs={"mean_length_lower_km": 1, "mean_length_higher_km": 1},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0, reason="both lengths doubled: the same quotient, exactly"
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="Rl is the exact quotient of the mean lengths, rounded once",
                check=_exact_quotients(
                    "length_ratio",
                    ("mean_length_higher_km", "mean_length_lower_km"),
                    ((1.45, 0.92), (5.2, 1.45), (4.0, 1.0), (0.0, 2.6)),
                    _ROUNDED_ONCE,
                ),
            ),
        ),
    ),
    validation="none: Horton's law of stream lengths makes Rl nearly constant across "
    "orders; its sources report no agreement with a quantity",
    formula_version=1,
    status="oracle only",
    conventions=(
        (
            "mean lengths of Strahler streams: the total length of the segments of "
            "an order over the number of its streams (StreamNetwork.get_statistics), "
            "km"
        ),
        "Rl of the mean lengths, Horton's ratio; not the ratio of total lengths",
    ),
    traps={
        "singular_at_bound": "range cases mean_length_lower_km-physical_low_*: Rl "
        "grows as 1/mean L_u; a value beyond float64 is refused by the precondition "
        "within_float64",
        "gap_propagation": _GAPS,
    },
    oracles=(
        Oracle(
            kind="exact",
            description="mean L_(u+1) / mean L_u in exact rational arithmetic",
            test="tests/unit/test_formulas_network.py (limit exact_rational)",
        ),
    ),
    base={"mean_length_lower_km": 1.45, "mean_length_higher_km": 5.2},
)

DRAINAGE_DENSITY: Final = FormulaSpec(
    name="drainage_density",
    title="Drainage density: the length of the streams over the watershed's area",
    function="hydrolog.network.stream_order.drainage_density",
    family="index",
    equation="Dd = sum(L) / A [km/km2]",
    latex=r"D_d = \frac{\sum L}{A}",
    variables=(
        Variable(
            name="total_length_km",
            symbol=r"\sum L",
            unit="km",
            description="Total length of the streams of the watershed.",
            physical=Range(
                low=0.0, test_high=_TOTAL_LENGTH_TEST, test_reason=_TOTAL_LENGTH_REASON
            ),
            applicability="unstated",
            typical=Range(
                low=0.7,
                high=12.7,
                source=_fixture("segments of 0.7 to 3.0 km, 12.7 km in all"),
            ),
        ),
        AREA,
    ),
    outputs=(
        Output(
            name="drainage_density",
            unit="km/km2",
            symbol="D_d",
            description="Drainage density.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_BASCIK_LAWS, _STRAHLER_1957),
    constraints=(
        Constraint(
            name="within_float64",
            cls="precondition",
            check=lambda x: math.isfinite(
                x.real("total_length_km") / x.real("area_km2")
            ),
            text="sum(L) / A lies within float64",
            source=_BASCIK_LAWS,
            satisfied={"total_length_km": 12.7, "area_km2": 12.0},
            violated={"total_length_km": 12.7, "area_km2": 5e-324},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"total_length_km": 1, "area_km2": -1},
        scalings=(
            Scaling(
                name="units_of_length",
                inputs={"total_length_km": 1, "area_km2": 2},
                outputs={"drainage_density": -1},
                tolerance=Tolerance(
                    abs=5e-324,
                    reason="lengths doubled and areas quadrupled: the quotient halves "
                    "exactly, but below the smallest normal float, 2.2e-308, both "
                    "quotients round to the subnormal step of 5e-324",
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="Dd is the exact quotient of the length and the area, rounded "
                "once",
                check=_exact_quotients(
                    "drainage_density",
                    ("total_length_km", "area_km2"),
                    ((12.7, 12.0), (45.0, 25.0), (0.0, 37.22), (6.0, 5.0)),
                    _ROUNDED_ONCE,
                ),
            ),
        ),
    ),
    validation="none: a ratio of measured quantities; Baścik (2006) notes that it "
    "depends strongly on the map's scale and the threshold that defines a stream",
    formula_version=1,
    status="oracle only",
    conventions=(
        (
            "the length of every stream of the network over the area of the "
            "watershed, km/km2; a network from a DEM depends on the threshold area of "
            "a stream, one from a map on its scale, so values compare only by one "
            "method"
        ),
    ),
    traps={
        "singular_at_bound": "range cases area_km2-physical_low_*: Dd grows as 1/A; a "
        "value beyond float64 is refused by the precondition within_float64",
        "gap_propagation": _GAPS,
    },
    oracles=(
        Oracle(
            kind="exact",
            description="sum(L) / A in exact rational arithmetic",
            test="tests/unit/test_formulas_network.py (limit exact_rational)",
        ),
    ),
    base={"total_length_km": 12.7, "area_km2": 12.0},
)

STREAM_FREQUENCY: Final = FormulaSpec(
    name="stream_frequency",
    title="Stream frequency: the number of streams over the watershed's area",
    function="hydrolog.network.stream_order.stream_frequency",
    family="index",
    equation="Fs = sum(N_u) / A [1/km2]",
    latex=r"F_s = \frac{\sum_u N_u}{A}",
    variables=(
        Variable(
            name="n_streams",
            symbol=r"\sum N_u",
            unit="-",
            kind="integer",
            description="Number of Strahler streams of all orders.",
            physical=Range(low=0.0, test_high=_COUNT_TEST, test_reason=_COUNT_REASON),
            applicability="unstated",
            typical=Range(
                low=1.0, high=8.0, source=_fixture("8 streams of orders 1-3")
            ),
        ),
        AREA,
    ),
    outputs=(
        Output(
            name="stream_frequency",
            unit="1/km2",
            symbol="F_s",
            description="Stream frequency.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_BASCIK_LAWS, _STRAHLER_1957),
    constraints=(
        Constraint(
            name="within_float64",
            cls="precondition",
            check=lambda x: math.isfinite(x.integer("n_streams") / x.real("area_km2")),
            text="sum(N_u) / A lies within float64",
            source=_BASCIK_LAWS,
            satisfied={"n_streams": 8, "area_km2": 12.0},
            violated={"n_streams": 8, "area_km2": 5e-324},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"n_streams": 1, "area_km2": -1},
        scalings=(
            Scaling(
                name="area",
                inputs={"area_km2": 1},
                outputs={"stream_frequency": -1},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the area doubled: the quotient halves exactly, unless it "
                    "underflows",
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="Fs is the exact quotient of the count and the area, rounded once",
                check=_exact_quotients(
                    "stream_frequency",
                    ("n_streams", "area_km2"),
                    ((8, 12.0), (25, 10.0), (0, 37.22), (4, 5.0)),
                    _ROUNDED_ONCE,
                ),
            ),
        ),
    ),
    validation="none: a ratio of counted and measured quantities",
    formula_version=1,
    status="oracle only",
    conventions=(
        (
            "Strahler streams of all orders (StreamNetwork.n_streams), not the links "
            "between junctions; Hydrograf's stream frequency counts links of the "
            "BDOT10k network and says so"
        ),
    ),
    traps={
        "singular_at_bound": "range cases area_km2-physical_low_*: Fs grows as 1/A; a "
        "value beyond float64 is refused by the precondition within_float64",
        "gap_propagation": _GAPS,
    },
    oracles=(
        Oracle(
            kind="exact",
            description="sum(N_u) / A in exact rational arithmetic",
            test="tests/unit/test_formulas_network.py (limit exact_rational)",
        ),
    ),
    base={"n_streams": 8, "area_km2": 12.0},
)


def _strahler(orders: NDArray[np.float64]) -> int:
    """Strahler's order below a junction of streams of the given orders."""
    if orders.size == 0:
        return 1
    highest = float(np.max(orders))
    return int(highest) + 1 if int(np.sum(orders == highest)) >= 2 else int(highest)


STRAHLER_ORDER: Final = FormulaSpec(
    name="strahler_order",
    title="Strahler's order of a stream below a junction",
    function="hydrolog.network.stream_order.strahler_order",
    family="classification",
    equation=(
        "u = 1 for a source; else u = max(upstream) + 1 if two or more upstream "
        "streams have the highest order, max(upstream) otherwise"
    ),
    latex=(
        r"u = \begin{cases} 1 & \text{no upstream stream} \\ "
        r"\max u_i + 1 & \text{two or more } u_i = \max u_i \\ "
        r"\max u_i & \text{otherwise} \end{cases}"
    ),
    variables=(
        Variable(
            name="upstream_orders",
            symbol="u_i",
            unit="-",
            kind="real_array",
            description="Strahler orders of the streams that flow into the stream; "
            "empty for a source.",
            physical=Range(
                low=1.0,
                test_high=64.0,
                test_reason="an order of 64 needs 2^63 sources, more than the cells "
                "of any DEM",
            ),
            applicability="unstated",
            typical=Range(low=1.0, high=3.0, source=_fixture("orders 1 to 3")),
            min_length=0,
        ),
    ),
    outputs=(
        Output(
            name="order",
            unit="-",
            kind="integer",
            symbol="u",
            description="Strahler order of the stream below the junction.",
            physical=Range(low=1.0),
        ),
    ),
    sources=(_BASCIK_ORDERS, _STRAHLER_1957),
    constraints=(
        Constraint(
            name="whole_orders",
            cls="physical",
            check=lambda x: bool(
                np.all(np.mod(x.array("upstream_orders"), 1.0) == 0.0)
            ),
            text="orders are whole numbers",
            source=_BASCIK_ORDERS,
            satisfied={"upstream_orders": [1.0, 2.0]},
            violated={"upstream_orders": [1.5, 2.0]},
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"upstream_orders": 1},
        limits=(
            Limit(
                name="source",
                text="a stream without upstream streams is of order 1",
                inputs={"upstream_orders": []},
                expected={"order": 1},
                tolerance=Tolerance(abs=0.0, reason="an integer class"),
            ),
            Limit(
                name="pass_through",
                text="a single upstream stream keeps its order",
                inputs={"upstream_orders": [3.0]},
                expected={"order": 3},
                tolerance=Tolerance(abs=0.0, reason="an integer class"),
            ),
            Limit(
                name="three_highest",
                text="three upstream streams of the highest order raise it by one, as "
                "two do",
                inputs={"upstream_orders": [2.0, 2.0, 2.0, 1.0]},
                expected={"order": 3},
                tolerance=Tolerance(abs=0.0, reason="an integer class"),
            ),
        ),
    ),
    validation="none: a classification of the streams of a network",
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "a junction of three or more streams raises the order when at least two "
            "of them have the highest order"
        ),
        "Shreve's magnitude, the sum of the upstream magnitudes, is another ordering "
        "(spec shreve_magnitude)",
    ),
    traps={
        "class_limit": "reference cases strahler-* at the junctions of equal and "
        "unequal orders",
        "gap_propagation": "type case upstream_orders-nan_element: a gap is refused",
    },
    reference_cases=("tests/fixtures/formulas/morphometry-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="the streams of a network counted as the connected runs of "
            "links of one order (union-find)",
            test="tests/unit/test_formulas_network.py "
            "(test_streams_are_the_runs_of_links_of_one_order)",
        ),
    ),
    base={"upstream_orders": [1.0, 1.0]},
)

_SHREVE_1966 = Source(
    citation="Shreve, R.L. (1966). Statistical law of stream numbers. Journal of "
    "Geology 74(1): 17-37",
    locator="the magnitude of a link, the number of sources upstream of it: a source "
    "link is of magnitude 1 and the magnitudes add at every junction (not opened; the "
    "definition as Esri's documentation gives it)",
    url="https://doi.org/10.1086/627137",
)
_ESRI_SHREVE = Source(
    citation="Esri. How Stream Order works. ArcGIS Pro 3.8 documentation, Spatial "
    "Analyst",
    locator="'Shreve method': exterior links are of order 1 and the orders of interior "
    "links are additive, 1 and 1 give 2, 1 and 2 give 3, 2 and 3 give 5; the "
    "magnitude of a link is the number of upstream links (after Shreve 1966)",
    url="https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/"
    "how-stream-order-works.htm",
)


SHREVE_MAGNITUDE: Final = FormulaSpec(
    name="shreve_magnitude",
    title="Shreve's magnitude of a link below a junction",
    function="hydrolog.network.stream_order.shreve_magnitude",
    family="classification",
    equation="M = 1 for a source; else M = sum of the upstream magnitudes",
    latex=(
        r"M = \begin{cases} 1 & \text{no upstream link} \\ "
        r"\sum_i M_i & \text{otherwise} \end{cases}"
    ),
    variables=(
        Variable(
            name="upstream_magnitudes",
            symbol="M_i",
            unit="-",
            kind="real_array",
            description="Shreve magnitudes of the links that flow into the link; "
            "empty for a source.",
            physical=Range(low=1.0, test_high=_COUNT_TEST, test_reason=_COUNT_REASON),
            applicability="unstated",
            typical=Range(low=1.0, high=4.0, source=_fixture("magnitudes 1 to 4 meet")),
            min_length=0,
        ),
    ),
    outputs=(
        Output(
            name="magnitude",
            unit="-",
            kind="integer",
            symbol="M",
            description="Shreve magnitude of the link below the junction, the number "
            "of sources upstream of it.",
            physical=Range(low=1.0),
        ),
    ),
    sources=(_ESRI_SHREVE, _SHREVE_1966),
    constraints=(
        Constraint(
            name="whole_magnitudes",
            cls="physical",
            check=lambda x: bool(
                np.all(np.mod(x.array("upstream_magnitudes"), 1.0) == 0.0)
            ),
            text="magnitudes are whole numbers, counts of sources",
            source=_SHREVE_1966,
            satisfied={"upstream_magnitudes": [1.0, 2.0]},
            violated={"upstream_magnitudes": [1.5, 2.0]},
        ),
        Constraint(
            name="sum_exact",
            cls="precondition",
            check=lambda x: float(np.sum(x.array("upstream_magnitudes"))) < 2.0**53,
            text="the sum of the magnitudes is below 2^53, where float64 holds every "
            "whole number",
            source=Source(
                citation="IEEE 754 double precision (float64)",
                locator="53-bit significand: whole numbers exact up to 2^53",
            ),
            satisfied={"upstream_magnitudes": [1.0, 2.0]},
            violated={"upstream_magnitudes": [2.0**52, 2.0**52]},
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"upstream_magnitudes": 1},
        limits=(
            Limit(
                name="source",
                text="a link without upstream links is of magnitude 1",
                inputs={"upstream_magnitudes": []},
                expected={"magnitude": 1},
                tolerance=Tolerance(abs=0.0, reason="an integer count"),
            ),
            Limit(
                name="pass_through",
                text="a single upstream link keeps its magnitude",
                inputs={"upstream_magnitudes": [3.0]},
                expected={"magnitude": 3},
                tolerance=Tolerance(abs=0.0, reason="an integer count"),
            ),
            Limit(
                name="three_links",
                text="three links meeting add their magnitudes, as two do",
                inputs={"upstream_magnitudes": [2.0, 1.0, 4.0]},
                expected={"magnitude": 7},
                tolerance=Tolerance(abs=0.0, reason="an integer count"),
            ),
        ),
    ),
    validation="none: a classification of the links of a network",
    formula_version=1,
    status="referenced",
    conventions=(
        "magnitudes of links, the segments between junctions, as the segments of "
        "StreamNetwork are",
        "network stats --method shreve counts the links of each magnitude and gives no "
        "Horton ratios, which are defined for Strahler's orders",
    ),
    traps={
        "gap_propagation": "type case upstream_magnitudes-nan_element: a gap is "
        "refused",
    },
    reference_cases=("tests/fixtures/formulas/morphometry-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="the magnitude of every link of a random network as the number "
            "of sources reached by a search upstream of it",
            test="tests/unit/test_formulas_network.py "
            "(test_magnitudes_count_the_sources_upstream)",
        ),
    ),
    base={"upstream_magnitudes": [1.0, 1.0]},
)

SPECS: Final[tuple[FormulaSpec, ...]] = (
    STRAHLER_ORDER,
    SHREVE_MAGNITUDE,
    BIFURCATION_RATIO,
    LENGTH_RATIO,
    DRAINAGE_DENSITY,
    STREAM_FREQUENCY,
)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""

TIER_B: Final[tuple[TierBSpec, ...]] = (
    TierBSpec(
        name="streams_of_each_order",
        function="hydrolog.network.stream_order.StreamNetwork.get_statistics",
        definition="the number of Strahler streams of each order, their total and mean "
        "lengths [km] and the total length of the network [km]",
        convention="a segment continues the stream of an upstream segment of its own "
        "order and begins one otherwise; the mean length is the total length of the "
        "order's segments over the number of its streams",
        source=_BASCIK_ORDERS,
    ),
)
"""The Tier B formula of the module (CMP-2.2)."""


def strahler_order(upstream_orders: NDArray[np.float64] | Sequence[float]) -> int:
    """Return Strahler's order of a stream below a junction, spec strahler_order.

    Parameters
    ----------
    upstream_orders : array_like
        Orders of the streams flowing into it; empty for a source.

    Returns
    -------
    int
        Strahler order.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the orders (``details.reason``, ``details.option``).
    """
    x = checked_inputs(STRAHLER_ORDER, upstream_orders=upstream_orders)
    return checked_outputs(
        STRAHLER_ORDER, {"order": _strahler(x.array("upstream_orders"))}
    ).integer("order")


def shreve_magnitude(upstream_magnitudes: NDArray[np.float64] | Sequence[float]) -> int:
    """Return Shreve's magnitude of a link below a junction, spec shreve_magnitude.

    Parameters
    ----------
    upstream_magnitudes : array_like
        Magnitudes of the links flowing into it; empty for a source.

    Returns
    -------
    int
        Shreve magnitude, the number of sources upstream.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the magnitudes (``details.reason``, ``details.option``).
    """
    x = checked_inputs(SHREVE_MAGNITUDE, upstream_magnitudes=upstream_magnitudes)
    magnitudes = x.array("upstream_magnitudes")
    magnitude = int(np.sum(magnitudes)) if magnitudes.size else 1
    return checked_outputs(SHREVE_MAGNITUDE, {"magnitude": magnitude}).integer(
        "magnitude"
    )


def bifurcation_ratio(n_lower: float, n_higher: float) -> float:
    """Return Horton's bifurcation ratio, spec bifurcation_ratio.

    The numbers count streams in Strahler's sense
    (:attr:`NetworkStatistics.segment_counts`), not segments between junctions.

    Parameters
    ----------
    n_lower : float
        Number of streams of the lower order, a whole number.
    n_higher : float
        Number of streams of the next order, a whole number.

    Returns
    -------
    float
        Bifurcation ratio [-].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input, or fewer than two streams of the lower order
        end in each stream of the higher (``details.constraint``).

    Notes
    -----
    Horton's law of stream numbers makes the ratio nearly constant across orders,
    about three to five where geological structure does not distort the drainage
    pattern; a higher ratio indicates structural control (Strahler, cited by Rai
    et al. in Applied Water Science).
    """
    x = checked_inputs(BIFURCATION_RATIO, n_lower=n_lower, n_higher=n_higher)
    return checked_outputs(
        BIFURCATION_RATIO,
        {"bifurcation_ratio": x.real("n_lower") / x.real("n_higher")},
    ).real("bifurcation_ratio")


def length_ratio(mean_length_lower_km: float, mean_length_higher_km: float) -> float:
    """Return Horton's length ratio, spec length_ratio.

    Parameters
    ----------
    mean_length_lower_km : float
        Mean length of the streams of the lower order [km].
    mean_length_higher_km : float
        Mean length of the streams of the next order [km].

    Returns
    -------
    float
        Length ratio [-].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``, ``details.option``).
    """
    x = checked_inputs(
        LENGTH_RATIO,
        mean_length_lower_km=mean_length_lower_km,
        mean_length_higher_km=mean_length_higher_km,
    )
    ratio = x.real("mean_length_higher_km") / x.real("mean_length_lower_km")
    return checked_outputs(LENGTH_RATIO, {"length_ratio": ratio}).real("length_ratio")


def drainage_density(total_length_km: float, area_km2: float) -> float:
    """Return the drainage density of a watershed, spec drainage_density.

    The second input is the area of the watershed in square kilometres (its name
    carries the unit, so the standard's check of this docstring, which allows no
    digit, keeps it out of the list below).

    Parameters
    ----------
    total_length_km : float
        Total length of the streams [km].

    Returns
    -------
    float
        Drainage density [km/km²].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``, ``details.option``).
    """
    x = checked_inputs(
        DRAINAGE_DENSITY, total_length_km=total_length_km, area_km2=area_km2
    )
    density = x.real("total_length_km") / x.real("area_km2")
    return checked_outputs(DRAINAGE_DENSITY, {"drainage_density": density}).real(
        "drainage_density"
    )


def stream_frequency(n_streams: int, area_km2: float) -> float:
    """Return the stream frequency of a watershed, spec stream_frequency.

    The number counts streams in Strahler's sense, of all orders
    (:attr:`StreamNetwork.n_streams`), not segments between junctions.

    The second input is the area of the watershed in square kilometres (its name
    carries the unit, so the standard's check of this docstring, which allows no
    digit, keeps it out of the list below).

    Parameters
    ----------
    n_streams : int
        Number of streams.

    Returns
    -------
    float
        Stream frequency, streams per square kilometre.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``, ``details.option``).
    """
    x = checked_inputs(STREAM_FREQUENCY, n_streams=n_streams, area_km2=area_km2)
    frequency = x.integer("n_streams") / x.real("area_km2")
    return checked_outputs(STREAM_FREQUENCY, {"stream_frequency": frequency}).real(
        "stream_frequency"
    )
