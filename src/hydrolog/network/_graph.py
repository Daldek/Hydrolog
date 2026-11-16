"""The order of the elements of a river network: every one after the ones it lists.

:class:`~hydrolog.network.StreamNetwork` (segments, integer ids) and
:class:`~hydrolog.routing.RoutingNetwork` (nodes, string ids) both describe a network
by the upstream elements that each element lists, and both need the same three
things: an unknown id is an error, a cycle is an error that names the elements of one
cycle, and the rest can be processed from the headwaters downstream. This module does
that once, for ids of one comparable type; each network turns the two exceptions into
the error of its own vocabulary (``segment_id`` or ``node_id``).
"""

from __future__ import annotations

import heapq
from collections.abc import Mapping, Sequence

__all__ = ["UnknownUpstream", "UpstreamCycle", "upstream_first"]


class UnknownUpstream(Exception):
    """An element lists an upstream id that is not in the network.

    Attributes
    ----------
    key : int or str
        The first element that lists an unknown id, in the order of the mapping.
    upstream : int or str
        The first unknown id it lists.
    count : int
        How many unknown ids the network lists in all.
    """

    def __init__(self, key: int | str, upstream: int | str, count: int) -> None:
        super().__init__(f"{key!r} lists {upstream!r}, which is not in the network")
        self.key = key
        self.upstream = upstream
        self.count = count


class UpstreamCycle(Exception):
    """The elements form a cycle: one is, through the ones it lists, its own upstream.

    Attributes
    ----------
    members : list of int or str
        The elements of one cycle in flow order, from the smallest id.
    """

    def __init__(self, members: list[int] | list[str]) -> None:
        super().__init__(f"the elements form a cycle: {members!r}")
        self.members = members


def _find_cycle[K: (int, str)](
    upstream: Mapping[K, Sequence[K]], blocked: set[K]
) -> list[K]:
    """Return one cycle in flow order from its smallest id.

    ``blocked`` are the elements that could not be ordered: every one of them has an
    upstream element that is blocked too, so walking upstream from any of them must
    run into a cycle.
    """
    walk: list[K] = []
    position: dict[K, int] = {}
    current = min(blocked)
    while current not in position:
        position[current] = len(walk)
        walk.append(current)
        current = next(up for up in upstream[current] if up in blocked)
    cycle = walk[position[current] :][::-1]  # upstream walk -> flow order
    start = cycle.index(min(cycle))
    return cycle[start:] + cycle[:start]


def upstream_first[K: (int, str)](upstream: Mapping[K, Sequence[K]]) -> list[K]:
    """Order the elements of a network so that each comes after the ones it lists.

    Parameters
    ----------
    upstream : Mapping
        The ids of the elements, each with the ids of the elements that flow into it
        (empty for a headwater). An id may be listed twice by one element.

    Returns
    -------
    list
        Every id once, headwaters first. Among the elements that are ready the
        smallest id comes first, so the order depends on the ids and the links only,
        not on the order of the mapping.

    Raises
    ------
    UnknownUpstream
        If an element lists an id that is not a key of ``upstream``.
    UpstreamCycle
        If the elements form a cycle (a self-link is a cycle of one).
    """
    unknown = [
        (key, up)
        for key, listed in upstream.items()
        for up in listed
        if up not in upstream
    ]
    if unknown:
        raise UnknownUpstream(unknown[0][0], unknown[0][1], len(unknown))
    waiting = {key: len(listed) for key, listed in upstream.items()}
    downstream: dict[K, list[K]] = {key: [] for key in upstream}
    for key, listed in upstream.items():
        for up in listed:
            downstream[up].append(key)
    ready = [key for key, count in waiting.items() if count == 0]
    heapq.heapify(ready)
    order: list[K] = []
    while ready:
        key = heapq.heappop(ready)
        order.append(key)
        for down in downstream[key]:
            waiting[down] -= 1
            if waiting[down] == 0:
                heapq.heappush(ready, down)
    if len(order) < len(upstream):
        raise UpstreamCycle(_find_cycle(upstream, set(upstream) - set(order)))
    return order
