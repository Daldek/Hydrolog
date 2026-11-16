"""The order of the nodes of a network, and what is wrong with a network that has none.

:func:`ordered` is :func:`~hydrolog.network._graph.upstream_first` with its two failures
told in the vocabulary of a routing network (``unknown_upstream``, ``cycle``). Objects
that link by reference cannot form a cycle nor name a node that is not there; a document
that links by id can, so the reader of a document uses it before it makes the nodes, and
the network uses it to order what it was given.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from hydrolog.exceptions import InvalidParameterError
from hydrolog.network._graph import UnknownUpstream, UpstreamCycle, upstream_first

__all__ = ["ordered"]


def ordered(upstream: Mapping[str, Sequence[str]]) -> list[str]:
    """Order the ids of a network, headwaters first, or say what is wrong with it.

    Parameters
    ----------
    upstream : mapping
        Each id with the ids that flow into it.

    Returns
    -------
    list of str
        Every id once; among the ids that are ready the smallest first.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``unknown_upstream`` (``node_id``, ``upstream_id``,
        ``n_unknown``) or ``cycle`` (``nodes`` in flow order).
    """
    try:
        return upstream_first(upstream)
    except UnknownUpstream as unknown:
        raise InvalidParameterError(
            f"Node {unknown.key!r} lists upstream node {unknown.upstream!r}, "
            "which is not in the network",
            details={
                "reason": "unknown_upstream",
                "node_id": unknown.key,
                "upstream_id": unknown.upstream,
                "n_unknown": unknown.count,
            },
            hint="Every id in `from` must be the id of a node of the network.",
        ) from unknown
    except UpstreamCycle as looped:
        members = [str(member) for member in looped.members]
        if len(members) == 1:
            message = f"Node {members[0]!r} lists itself as upstream"
        else:
            chain = " -> ".join(repr(member) for member in [*members, members[0]])
            message = f"The nodes form a cycle: {chain}"
        raise InvalidParameterError(
            message,
            details={"reason": "cycle", "nodes": members},
            hint="Water flows from a node into each node that lists it; remove "
            "the link that closes the loop.",
        ) from looped
