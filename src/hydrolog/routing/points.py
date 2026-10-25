"""Control points: a network built the way an application picks it (ADR-0012).

An application that lets its user pick points on the streams of a catchment does not
think in nodes. The user picks the outlet first, then points upstream of it. Every
point closes the area that drains to it and to no point above it, its *residual* area
(the contributing area minus the areas of the points picked upstream), and the stream
between two points is a reach that routes the water of the upper one down to the lower
one. :class:`ControlPointNetwork` is that model: the application maps its picks to it
one to one, edits it as the user does, and reads the discharge at every point.

=============  =====================================================================
object         what the application gives
=============  =====================================================================
OutletPoint    the outlet: its id and its residual area (a :class:`Subcatchment`)
ControlPoint   a point above another one: its id and its residual area
channel        a :class:`Channel`, or a :class:`Reach`, between a point and the next
confluence     where a stream is joined by another; it has no area of its own
=============  =====================================================================

**Outlet first.** The network is made of its outlet, and it is a valid network, ready to
route, from then on; each edit keeps the network valid or is refused and changes
nothing. :meth:`~ControlPointNetwork.add_point` puts a point above a point,
:meth:`~ControlPointNetwork.update_subcatchment` gives a point the area that is left to
it, :meth:`~ControlPointNetwork.add_confluence` splits a channel where another stream
joins it and :meth:`~ControlPointNetwork.remove_point` takes a point away.

**What Hydrolog does not do.** It does not know areas: the residual area of a point is
the application's to compute (a point added above another takes its area from the one
below: the application gives that one a smaller subcatchment with
:meth:`~ControlPointNetwork.update_subcatchment`), and so are the parameters of every
channel, which Hydrolog never makes up. It checks what it is given: one outlet, no
bifurcation, no cycle, a time axis that all the sources share. The rainfall belongs to
each subcatchment (ADR-0012): two points of a network can be given rain from different
sources.

**What it makes.** :meth:`~ControlPointNetwork.network` is the immutable
:class:`~hydrolog.routing.RoutingNetwork` of the points, and
:meth:`~ControlPointNetwork.route` routes it. A point and a confluence become a
:class:`Junction` that has the id of the point and adds: its own subcatchment, and the
outflow of the channel of every point that flows into it. So the hydrograph of the
result at the id of a point is the discharge at that point, and a nonlinear reach is
routed once for all the water that goes through it. The outlet is a junction named
``<id>_junction`` and an :class:`Outlet` with the id of the outlet point, whose
hydrograph is that of the junction. A bare :class:`Reach` is wrapped in a channel named
``<id>_channel`` after the point it leaves.

Examples
--------
The outlet alone, then a point above it and a second one above that:

>>> from hydrolog.routing import (
...     ControlPoint, ControlPointNetwork, Hydrograph, LagReach, OutletPoint,
...     Subcatchment,
... )
>>> def basin(node_id, peak_m3s):
...     return Subcatchment(node_id, Hydrograph.from_step([0, peak_m3s, 0, 0, 0], 10.0))
>>> points = ControlPointNetwork(OutletPoint("OUT", basin("OUT_area", 1.0)))
>>> points.route().hydrographs["OUT"].peak_discharge_m3s
1.0
>>> points.add_point(
...     ControlPoint("P1", basin("P1_area", 4.0)),
...     downstream="OUT",
...     channel=LagReach(lag_min=10.0),
... )
>>> points.add_point(
...     ControlPoint("P2", basin("P2_area", 2.0)),
...     downstream="P1",
...     channel=LagReach(lag_min=10.0),
... )
>>> points.ids
('OUT', 'P1', 'P2')
>>> result = points.route()
>>> [result.hydrographs[point].peak_discharge_m3s for point in points.ids]
[4.0, 4.0, 2.0]
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any, Final, Literal

from hydrolog.routing._checks import shown
from hydrolog.routing._reading import fail
from hydrolog.routing.network import (
    Channel,
    Junction,
    NetworkResult,
    Node,
    Outlet,
    RoutingNetwork,
    Subcatchment,
    check_unique,
)
from hydrolog.routing.rainfall import RainfallSource
from hydrolog.routing.reach import Reach

__all__ = ["ControlPoint", "ControlPointNetwork", "OutletPoint"]

Kind = Literal["outlet", "point", "confluence"]
"""What a place of the network is: the outlet, a point of the application, or a
confluence."""

_CHANNEL_SUFFIX: Final = "_channel"
_JUNCTION_SUFFIX: Final = "_junction"


@dataclass(frozen=True)
class ControlPoint:
    """A point that the application picked on a stream, and the area that it closes.

    Attributes
    ----------
    id : str
        The id of the point: a plain id (see :class:`~hydrolog.routing.Node`); the
        result has the discharge at the point as ``hydrographs[id]``.
    subcatchment : Subcatchment or None
        The residual area of the point: what drains to it and to no point above it, the
        contributing area minus the areas of the points above. Its own id names its
        hydrograph in the result. A point that has points above it may have none, and a
        point that has none above it must have one, or there is no water.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``type`` if the id is not a string or the subcatchment
        is not a :class:`~hydrolog.routing.Subcatchment`.
    """

    id: str
    subcatchment: Subcatchment | None = None

    def __post_init__(self) -> None:
        """Check the types."""
        if not isinstance(self.id, str):
            fail(
                f"The id of a point must be a string, not {type(self.id).__name__}",
                reason="type",
                field="id",
            )
        if self.subcatchment is not None and not isinstance(
            self.subcatchment, Subcatchment
        ):
            fail(
                f"Point {self.id!r}: the subcatchment must be a Subcatchment, not "
                f"{type(self.subcatchment).__name__}",
                reason="type",
                field="subcatchment",
                point_id=self.id,
            )


@dataclass(frozen=True)
class OutletPoint(ControlPoint):
    """The outlet of the network, the first point: where the whole catchment drains to.

    It has the fields of a :class:`ControlPoint`; ``subcatchment`` is the residual area
    of the outlet, which at the beginning is the whole catchment.
    """


@dataclass(frozen=True)
class _Place:
    """A point or a confluence of the network, and the stream that leaves it."""

    id: str
    kind: Kind
    subcatchment: Subcatchment | None
    downstream: str | None
    channels: tuple[Channel, ...]


def _channel(value: object, owner: str, field: str) -> Channel:
    """Return the channel of the stream that leaves ``owner``, connected to nothing.

    A :class:`Channel` (a :class:`Reservoir` is one) keeps its id and its options and
    loses its inflows: the network connects it. A :class:`Reach` is wrapped in a channel
    named after ``owner``.
    """
    if isinstance(value, Channel):
        return value.with_inflows()
    if isinstance(value, Reach):
        return Channel(f"{owner}{_CHANNEL_SUFFIX}", value)
    fail(
        f"The {field} of {owner!r} must be a Channel or a Reach, not "
        f"{type(value).__name__}",
        reason="type",
        field=field,
        point_id=owner,
        hint="A Reach is wrapped in a channel; a Channel is used as it is.",
    )


def _children(places: Mapping[str, _Place]) -> dict[str, list[str]]:
    """Return the ids of the places that flow into each place, in the order given."""
    children: dict[str, list[str]] = {place_id: [] for place_id in places}
    for place in places.values():
        if place.downstream is not None:
            children[place.downstream].append(place.id)
    return children


def _expand(
    places: Mapping[str, _Place], children: Mapping[str, list[str]], outlet_id: str
) -> Outlet:
    """Return the outlet of the nodes that the places stand for.

    Every place is a junction that adds its subcatchment and the channels of the places
    that flow into it; a channel is fed by the junction of the place that it leaves. The
    order is iterative: a place is built after every place above it.
    """
    order: list[str] = []
    pending = [outlet_id]
    while pending:
        place_id = pending.pop()
        order.append(place_id)
        pending.extend(children[place_id])
    junctions: dict[str, Junction] = {}
    for place_id in reversed(order):
        inflows: list[Node] = []
        if places[place_id].subcatchment is not None:
            inflows.append(places[place_id].subcatchment)  # type: ignore[arg-type]
        for child_id in children[place_id]:
            water: Node = junctions[child_id]
            for channel in places[child_id].channels:
                water = channel.with_inflows(water)
            inflows.append(water)
        name = place_id + _JUNCTION_SUFFIX if place_id == outlet_id else place_id
        junctions[place_id] = Junction(name, inflows=inflows)
    return Outlet(outlet_id, inflow=junctions[outlet_id])


class ControlPointNetwork:
    """A network of control points, built outlet first and edited like the user does.

    Parameters
    ----------
    outlet : OutletPoint
        The outlet: its id and its residual area. The network is valid, and routes, with
        nothing else.
    name : str, optional
        A name for the network, reported in the result.
    rainfall : RainfallSource, optional
        The rainfall of every subcatchment that makes its hydrograph and has none of its
        own (:class:`~hydrolog.routing.RoutingNetwork`). The rainfall belongs to the
        subcatchment; this is only a convenience.
    timestep_min : float, optional
        The time step of the network [min], > 0
        (:class:`~hydrolog.routing.RoutingNetwork`).

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``type`` if ``outlet`` is not an :class:`OutletPoint`;
        ``no_inflow`` if the outlet has no subcatchment; the reasons of a network
        (:class:`~hydrolog.routing.RoutingNetwork`) for a subcatchment that cannot be
        routed (``missing_field`` for a rain that is nowhere, ``invalid_id``...).

    Notes
    -----
    Every edit builds the :class:`~hydrolog.routing.RoutingNetwork` of the new state and
    keeps the state only if that works, so the network is valid after every call and a
    call that raises changes nothing. An edit raises
    :class:`~hydrolog.exceptions.InvalidParameterError` with ``details.reason``:

    ``unknown_point``
        an id that is not in the network (``point_id``, ``allowed``);
    ``duplicate_node``
        an id that another node of the network has, without regard to case: the ids of
        points, confluences, subcatchments and channels are the ids of nodes
        (``node_id``, ``other_id``);
    ``type``
        a subcatchment, a channel or a point of the wrong class (``field``);
    ``no_channel``
        a confluence on the channel of the outlet, which has none;
    ``not_upstream``
        a point of ``upstream`` that does not flow into ``downstream``;
    ``not_a_point``
        an area given to a confluence;
    ``no_inflow``
        a point or a confluence that would get no water, because it has no subcatchment
        and nothing flows into it (``point_id``);
    ``outlet_removal``
        the outlet cannot be removed;
    ``still_joins``
        a confluence that still joins two streams cannot be removed;
    ``not_applicable``
        a channel for a removal that merges none;

    and the reasons of a network: ``timestep_mismatch``, ``start_mismatch``,
    ``missing_field`` (a rain that is nowhere), ``invalid_id``...
    """

    def __init__(
        self,
        outlet: OutletPoint,
        *,
        name: str | None = None,
        rainfall: RainfallSource | None = None,
        timestep_min: float | None = None,
    ) -> None:
        """Make the network of the outlet."""
        if not isinstance(outlet, OutletPoint):
            fail(
                f"The network starts with an OutletPoint, not {type(outlet).__name__}",
                reason="type",
                field="outlet",
                hint="The outlet is the first point: OutletPoint(id, subcatchment).",
            )
        self._outlet_id = outlet.id
        self._settings: dict[str, Any] = {
            "name": name,
            "rainfall": rainfall,
            "timestep_min": timestep_min,
        }
        places = {outlet.id: _Place(outlet.id, "outlet", outlet.subcatchment, None, ())}
        self._network = self._build(places)
        self._places = places

    # --- what the network is -----------------------------------------------------

    @property
    def outlet(self) -> str:
        """Str: the id of the outlet point."""
        return self._outlet_id

    @property
    def ids(self) -> tuple[str, ...]:
        """Tuple of str: the ids of the points and confluences, the outlet first."""
        return tuple(self._places)

    def __contains__(self, point_id: object) -> bool:
        """Whether ``point_id`` is the id of a point or a confluence."""
        return point_id in self._places

    def __repr__(self) -> str:
        """Return the outlet and the number of places."""
        return (
            f"ControlPointNetwork(outlet={self._outlet_id!r}, "
            f"places={len(self._places)})"
        )

    def kind(self, point_id: str) -> Kind:
        """Return what the place is: ``"outlet"``, ``"point"`` or ``"confluence"``.

        A point whose removal left two streams meeting in it is a confluence from then
        on.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unknown_point``.
        """
        return self._place(point_id).kind

    def subcatchment(self, point_id: str) -> Subcatchment | None:
        """Return the residual area of the place, ``None`` if it has none.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unknown_point``.
        """
        return self._place(point_id).subcatchment

    def downstream(self, point_id: str) -> str | None:
        """Return the id of the place that the stream of ``point_id`` flows into.

        ``None`` for the outlet.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unknown_point``.
        """
        return self._place(point_id).downstream

    def upstream(self, point_id: str) -> tuple[str, ...]:
        """Return the ids of the places that flow into ``point_id``, in the order added.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unknown_point``.
        """
        self._place(point_id)
        return tuple(_children(self._places)[point_id])

    def channels(self, point_id: str) -> tuple[Channel, ...]:
        """Return the channels between ``point_id`` and the place below it.

        One channel, unless the removal of a point put two in series (the first one is
        next to ``point_id``); none for the outlet.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unknown_point``.
        """
        return self._place(point_id).channels

    def network(self) -> RoutingNetwork:
        """Return the network of the points as it is now.

        Returns
        -------
        RoutingNetwork
            The immutable network; a later edit does not change it.
        """
        return self._network

    def route(self) -> NetworkResult:
        """Route the network as it is now.

        Returns
        -------
        NetworkResult
            The result of :meth:`network`: ``hydrographs[id]`` is the discharge at the
            point ``id``.

        Raises
        ------
        InvalidParameterError
            From a reach (see :meth:`~hydrolog.routing.RoutingNetwork.route`).
        CalculationError
            From a reach (a flood beyond a table...).
        """
        return self._network.route()

    # --- edits -------------------------------------------------------------------

    def add_point(
        self,
        point: ControlPoint,
        *,
        downstream: str,
        channel: Channel | Reach,
        upstream: Mapping[str, Channel | Reach] | None = None,
    ) -> None:
        """Put a point above ``downstream``, and the stream between them.

        Parameters
        ----------
        point : ControlPoint
            The new point and its residual area. It must have an area, or take a point
            of ``upstream``, or it would get no water.
        downstream : str
            The id of the point or the confluence that the point flows into.
        channel : Channel or Reach
            The stream between the point and ``downstream``. A :class:`Channel` that has
            inflows is used without them.
        upstream : mapping of str to Channel or Reach, optional
            For a point picked between two others, on the stream that is already there:
            the places that now flow into ``downstream``, and that are to flow into the
            new point instead. Each is given the channel that joins it to the new point;
            the one it had is dropped.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``type``, ``unknown_point``, ``duplicate_node``,
            ``not_upstream`` (a place of ``upstream`` that does not flow into
            ``downstream``), ``no_inflow`` and the reasons of a network (see the class).
        """
        if isinstance(point, OutletPoint) or not isinstance(point, ControlPoint):
            fail(
                f"A point is a ControlPoint, not {type(point).__name__}",
                reason="type",
                field="point",
                hint="The outlet is given when the network is made.",
            )
        below = self._place(downstream, "downstream")
        self._unused(point.id)
        places = dict(self._places)
        for place_id, stream in (upstream or {}).items():
            above = self._place(place_id, "upstream")
            if above.downstream != below.id:
                fail(
                    f"Point {place_id!r} does not flow into {below.id!r}, so it cannot "
                    f"flow into the new point {point.id!r}",
                    reason="not_upstream",
                    point_id=place_id,
                    downstream=below.id,
                    hint=f"The places that flow into {below.id!r} are "
                    f"{', '.join(map(repr, self.upstream(below.id)))}.",
                )
            places[place_id] = replace(
                above,
                downstream=point.id,
                channels=(_channel(stream, place_id, "upstream"),),
            )
        places[point.id] = _Place(
            point.id,
            "point",
            point.subcatchment,
            below.id,
            (_channel(channel, point.id, "channel"),),
        )
        self._commit(places)

    def add_confluence(
        self,
        confluence_id: str,
        *,
        on_channel_of: str,
        upstream_channel: Channel | Reach,
        downstream_channel: Channel | Reach,
    ) -> None:
        """Split a stream where another one joins it: a place that has no area.

        The stream of ``on_channel_of`` (from that place to the one below it) is cut in
        two at the new confluence; a point that is added with the confluence as its
        ``downstream`` then joins the stream there, and the lower part of the stream
        carries the water of both. Both channels are given, never made up: Hydrolog does
        not know where the stream is cut.

        Parameters
        ----------
        confluence_id : str
            The id of the confluence (it names the junction that adds the streams).
        on_channel_of : str
            The id of the place whose stream is cut; not the outlet, which has none.
        upstream_channel : Channel or Reach
            The stream from ``on_channel_of`` down to the confluence.
        downstream_channel : Channel or Reach
            The stream from the confluence down to the place below ``on_channel_of``.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``type``, ``unknown_point``, ``duplicate_node``,
            ``no_channel`` (``on_channel_of`` is the outlet) and the reasons of a
            network.
        """
        above = self._place(on_channel_of, "on_channel_of")
        if above.downstream is None:
            fail(
                f"The outlet {above.id!r} has no channel to put a confluence on",
                reason="no_channel",
                point_id=above.id,
                hint="A confluence is on the stream that leaves a point.",
            )
        self._unused(confluence_id)
        places = dict(self._places)
        places[above.id] = replace(
            above,
            downstream=confluence_id,
            channels=(_channel(upstream_channel, above.id, "upstream_channel"),),
        )
        places[confluence_id] = _Place(
            confluence_id,
            "confluence",
            None,
            above.downstream,
            (_channel(downstream_channel, confluence_id, "downstream_channel"),),
        )
        self._commit(places)

    def update_subcatchment(
        self, point_id: str, subcatchment: Subcatchment | None
    ) -> None:
        """Give a point the residual area that is left to it, or none.

        What a point closes changes when a point is added or removed above it: the
        application computes the new area and gives it here.

        Parameters
        ----------
        point_id : str
            The id of the outlet or of a point.
        subcatchment : Subcatchment or None
            The new residual area; ``None`` for a point that has no area left, which
            needs a point above it.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unknown_point``, ``type``, ``not_a_point`` (a
            confluence has no area), ``no_inflow`` and the reasons of a network.
        """
        place = self._place(point_id)
        if place.kind == "confluence":
            fail(
                f"{point_id!r} is a confluence: it has no area of its own",
                reason="not_a_point",
                point_id=point_id,
                hint="Add a point above the confluence for an area that drains to it.",
            )
        if subcatchment is not None and not isinstance(subcatchment, Subcatchment):
            fail(
                f"The subcatchment of {point_id!r} must be a Subcatchment, not "
                f"{type(subcatchment).__name__}",
                reason="type",
                field="subcatchment",
                point_id=point_id,
            )
        places = dict(self._places)
        places[point_id] = replace(place, subcatchment=subcatchment)
        self._commit(places)

    def remove_point(
        self, point_id: str, *, channel: Channel | Reach | None = None
    ) -> None:
        """Take a point away; the points above it stay.

        The point loses its subcatchment (the application gives its area to the point
        below with :meth:`update_subcatchment`) and then:

        * a point that has nothing above it is removed, with its channel; if that leaves
          a confluence with one stream, the confluence is dropped as below;
        * a point or a confluence that has one stream above it is dropped: the place
          above now flows into the place below through the two channels in series, which
          is what the stream was, or through ``channel`` when the application gives the
          one that replaces both;
        * a point that has two or more streams above it stays as a confluence: they
          still meet there, and the channel below it must carry them together.

        Parameters
        ----------
        point_id : str
            The id of a point or a confluence; not the outlet.
        channel : Channel or Reach, optional
            The channel that replaces the two that are merged. Only when something is
            merged: a point or a confluence with one place above it, or the removal of
            the last-but-one stream of a confluence.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unknown_point``, ``outlet_removal``,
            ``still_joins`` (a confluence that joins two or more streams),
            ``not_applicable`` (a ``channel`` when nothing merges), ``no_inflow`` (the
            point below would get no water) and the reasons of a network.
        """
        place = self._place(point_id)
        if place.kind == "outlet":
            fail(
                f"The outlet {point_id!r} cannot be removed",
                reason="outlet_removal",
                point_id=point_id,
                hint="The network ends in the outlet; make another network instead.",
            )
        places = dict(self._places)
        above = _children(places)[point_id]
        dropped: str | None = None
        if len(above) >= 2:
            if place.kind == "confluence":
                fail(
                    f"The confluence {point_id!r} still joins {len(above)} streams",
                    reason="still_joins",
                    point_id=point_id,
                    hint="Remove the points above it, or all but one of them.",
                )
            places[point_id] = replace(place, kind="confluence", subcatchment=None)
        elif above:
            dropped = point_id
        else:
            del places[point_id]
            below = places[place.downstream or ""]
            if below.kind == "confluence" and len(_children(places)[below.id]) == 1:
                dropped = below.id
        if channel is not None and dropped is None:
            fail(
                f"Removing {point_id!r} merges no channels: there is nothing for "
                "'channel' to replace",
                reason="not_applicable",
                field="channel",
                point_id=point_id,
                hint="'channel' replaces the two channels of a point that is dropped.",
            )
        if dropped is not None:
            self._drop(places, dropped, channel)
        self._commit(places)

    # --- inside ------------------------------------------------------------------

    def _place(self, point_id: object, field: str = "point") -> _Place:
        """Return the place called ``point_id`` or refuse the unknown id."""
        place = self._places.get(point_id) if isinstance(point_id, str) else None
        if place is None:
            fail(
                f"There is no point or confluence {shown(point_id)} in the network "
                f"(argument {field!r})",
                reason="unknown_point",
                point_id=shown(point_id),
                allowed=list(self._places),
                hint=f"The ids are {', '.join(map(repr, self._places))}.",
            )
        return place

    def _unused(self, new_id: object) -> None:
        """Refuse an id that another place has, with any case."""
        if not isinstance(new_id, str):
            fail(
                f"An id must be a string, not {type(new_id).__name__}",
                reason="type",
                field="id",
            )
        check_unique([*self._places, new_id])

    @staticmethod
    def _drop(places: dict[str, _Place], dropped: str, channel: object) -> None:
        """Remove ``dropped`` and join the place above it to the place below it."""
        place = places.pop(dropped)
        (above,) = (item for item in places.values() if item.downstream == dropped)
        series = (
            (_channel(channel, above.id, "channel"),)
            if channel is not None
            else (*above.channels, *place.channels)
        )
        places[above.id] = replace(above, downstream=place.downstream, channels=series)

    def _build(self, places: Mapping[str, _Place]) -> RoutingNetwork:
        """Return the network of ``places``, or refuse them."""
        children = _children(places)
        for place in places.values():
            if place.subcatchment is None and not children[place.id]:
                fail(
                    f"Point {place.id!r} would get no water: it has no subcatchment "
                    "and no point above it",
                    reason="no_inflow",
                    point_id=place.id,
                    hint="Give it a subcatchment, or remove it.",
                )
        outlet = _expand(places, children, self._outlet_id)
        return RoutingNetwork(outlet, **self._settings)

    def _commit(self, places: dict[str, _Place]) -> None:
        """Keep ``places`` as the state if they make a valid network."""
        network = self._build(places)
        self._places = places
        self._network = network
