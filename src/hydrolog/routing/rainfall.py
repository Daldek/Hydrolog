"""Rainfall of a subcatchment: where its water comes from (ADR-0012).

A subcatchment that makes its own runoff takes its rainfall from a *rainfall source*,
an object that gives a hyetograph at the time step of the network. The rainfall is
a property of each subcatchment, never of the network: two subcatchments of one network
can take it from different sources (a design storm over one, the record of a gauge over
another, later an areal rainfall from IMGWTools, radar or PMAXTP). A default for the
whole network is only a convenience (``RoutingNetwork(..., rainfall=...)``); nothing
assumes that it exists.

:class:`RainfallSource` is the protocol. Anything that has its methods can be given to
a :class:`~hydrolog.routing.Subcatchment`; to be named in a ``hydrolog-network/1``
document too, the class has a ``kind``, reads and writes its own fields
(:meth:`~RainfallSource.from_document`, :meth:`~RainfallSource.to_document`) and is
registered in :data:`RAINFALL_KINDS`; no list of the kinds exists anywhere else. Two
are in the package:

=============  =====================================================================
kind           the rainfall
=============  =====================================================================
``design``     :class:`DesignStorm`: a depth over a duration, in the shape of one of
               the hyetographs of :mod:`hydrolog.precipitation` (``block``,
               ``triangular``, ``beta``, ``euler_ii``, or a class that is added to
               :data:`HIETOGRAMS`)
``series``     :class:`RainfallSeries`: the depth of every time step, measured or
               made by the caller
=============  =====================================================================

A series has its own time step and is never resampled (ADR-0008): a network at another
step refuses it. A design storm can be cut at any step.

Examples
--------
>>> from hydrolog.precipitation import EulerIIHietogram
>>> from hydrolog.routing import DesignStorm
>>> storm = DesignStorm(45.0, duration_min=60.0, hietogram=EulerIIHietogram())
>>> storm.hyetograph(timestep_min=10.0).intensities_mm.round(1).tolist()
[9.0, 14.7, 6.8, 5.6, 4.8, 4.2]
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, ClassVar, Protocol, Self, runtime_checkable

import numpy as np
from numpy.typing import ArrayLike, NDArray

from hydrolog.exceptions import InvalidParameterError
from hydrolog.precipitation.hietogram import (
    BetaHietogram,
    BlockHietogram,
    EulerIIHietogram,
    Hietogram,
    HietogramResult,
    TriangularHietogram,
)
from hydrolog.routing._checks import as_array, positive
from hydrolog.routing._reading import (
    as_object,
    check_fields,
    constructor_arguments,
    constructor_defaults,
    fail,
    required,
    without_defaults,
)
from hydrolog.routing._registry import Registry
from hydrolog.routing.hydrograph import STEP_TOLERANCE
from hydrolog.routing.parameters import Parameter, ParameterSource, parameter

__all__ = [
    "HIETOGRAMS",
    "RAINFALL_KINDS",
    "DesignStorm",
    "RainfallSeries",
    "RainfallSource",
    "rainfall_from_document",
    "rainfall_to_document",
]

_DURATION_TOLERANCE = 1e-9


@runtime_checkable
class RainfallSource(Protocol):
    """What a subcatchment needs of its rainfall, and what a document needs of a kind.

    The calculation uses :attr:`timestep_min`, :meth:`hyetograph` and :meth:`describe`.
    A source that a document can name has the rest: a ``kind``, :meth:`to_document` and
    :meth:`from_document`, and is registered in :data:`RAINFALL_KINDS`.

    Attributes
    ----------
    kind : str
        The ``kind`` of the rainfall in a document.
    """

    kind: ClassVar[str]

    @property
    def timestep_min(self) -> float | None:
        """Float or None: the time step of the source [min]; ``None`` for any step."""
        ...

    def hyetograph(
        self, timestep_min: float, duration_min: float | None = None
    ) -> HietogramResult:
        """Return the rainfall of the event at a time step.

        Parameters
        ----------
        timestep_min : float
            The time step of the network [min]; a source that has a step of its own
            refuses another one (``details.reason`` ``timestep_mismatch``).
        duration_min : float, optional
            The duration that the caller wants [min]; ``None`` is the duration of the
            source. A source that has a duration of its own refuses another one
            (``details.reason`` ``duration_mismatch``); one whose depth depends on the
            duration (a depth-duration-frequency source) takes it.

        Returns
        -------
        HietogramResult
            The depth of every step of the event [mm], from time 0.
        """
        ...

    def describe(self, hyetograph: HietogramResult | None = None) -> list[Parameter]:
        """List the values that the rainfall uses.

        Parameters
        ----------
        hyetograph : HietogramResult, optional
            What :meth:`hyetograph` returned; with it the list holds the values that
            the calculation derived from the source as well.

        Returns
        -------
        list of Parameter
            Name, value, unit and source (``given``, ``computed``, ``default``).
        """
        ...

    def to_document(self) -> dict[str, Any]:
        """Return the source as the object of a document, with its ``kind``."""
        ...

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> Self:
        """Read the source from the object of a document (see :meth:`to_document`)."""
        ...


RAINFALL_KINDS: Registry[RainfallSource] = Registry(
    "kind",
    key="kind",
    reason="unknown_kind",
    needs=("from_document", "to_document"),
)
"""The rainfall sources by their ``kind``, the ``kind`` of a ``rainfall`` in a document:
a new source is a class that is registered here (``@RAINFALL_KINDS.register``)."""

HIETOGRAMS: Registry[Hietogram] = Registry(
    "hietogram type", key="hietogram_type", reason="unknown_hietogram_type"
)
"""The shapes of a design storm by name, the ``hietogram_type`` of a ``design``
rainfall. The arguments of the constructor of a class are the fields of its shape in a
document and must be kept as attributes of the same name; a new shape is a
:class:`~hydrolog.precipitation.Hietogram` that is added here
(``HIETOGRAMS.add("name", cls)``)."""

HIETOGRAMS.add("block", BlockHietogram)
HIETOGRAMS.add("triangular", TriangularHietogram)
HIETOGRAMS.add("beta", BetaHietogram)
HIETOGRAMS.add("euler_ii", EulerIIHietogram)


def _same_duration(own: float, asked: float | None, what: str) -> None:
    """Refuse a duration that the caller asks for and the source does not have."""
    if asked is None:
        return
    if not math.isclose(asked, own, rel_tol=_DURATION_TOLERANCE):
        raise InvalidParameterError(
            f"{what} lasts {own:g} min, not the {asked:g} min asked for",
            details={
                "option": "duration_min",
                "reason": "duration_mismatch",
                "expected": own,
                "value": asked,
            },
            hint="A rainfall that has a duration of its own is not stretched or cut.",
        )


def rainfall_from_document(document: object) -> RainfallSource:
    """Read a ``rainfall`` of a document: the class is found by its ``kind``.

    Parameters
    ----------
    document : mapping
        The object: ``kind`` and the fields of that kind.

    Returns
    -------
    RainfallSource
        The rainfall.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``type`` (not an object), ``missing_field`` (no
        ``kind``), ``unknown_kind`` (``value`` and ``allowed``), or the reason that
        the class gives (``unknown_field``, ``missing_field``, ``minimum``...), with
        ``details.field``.
    """
    fields = as_object(document, "The rainfall")
    kind = required(
        "The rainfall",
        fields,
        "kind",
        hint=f"The kinds are {', '.join(RAINFALL_KINDS.names)}.",
    )
    cls = RAINFALL_KINDS.resolve(kind, "The rainfall", field="kind")
    return cls.from_document(fields)


def rainfall_to_document(source: RainfallSource) -> dict[str, Any]:
    """Write a rainfall as the object of a document, if a document can name its kind.

    Parameters
    ----------
    source : RainfallSource
        The rainfall; its class must be in :data:`RAINFALL_KINDS`, or the reader would
        not find it.

    Returns
    -------
    dict
        The object, with its ``kind``: what :meth:`RainfallSource.to_document` returns.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``unregistered`` if the class is not in the registry.
    """
    RAINFALL_KINDS.name_of(source)
    return source.to_document()


@RAINFALL_KINDS.register
class DesignStorm:
    """A design storm: a depth over a duration, in the shape of a hyetograph.

    The depth is spread over the duration by the ``hietogram`` (the generators of
    :mod:`hydrolog.precipitation`), cut at the time step of the network. The duration
    is the duration of the storm, not of the network: a duration that is not a whole
    number of steps gives a storm of the whole steps that it holds.

    Parameters
    ----------
    total_mm : float
        Depth of the storm [mm], > 0.
    duration_min : float
        Duration of the storm [min], > 0.
    hietogram : Hietogram
        The shape: ``BlockHietogram()``, ``TriangularHietogram(peak_position=0.4)``,
        ``BetaHietogram(alpha=2, beta=5)``, ``EulerIIHietogram()`` or any class added to
        :data:`HIETOGRAMS`.

    Raises
    ------
    InvalidParameterError
        If ``total_mm`` or ``duration_min`` is not a finite number above zero, or
        ``hietogram`` is not a :class:`~hydrolog.precipitation.Hietogram`.

    Examples
    --------
    >>> from hydrolog.precipitation import BlockHietogram
    >>> from hydrolog.routing import DesignStorm
    >>> storm = DesignStorm(30.0, 60.0, BlockHietogram())
    >>> storm.hyetograph(20.0).intensities_mm.tolist()
    [10.0, 10.0, 10.0]
    """

    kind: ClassVar[str] = "design"

    def __init__(
        self, total_mm: float, duration_min: float, hietogram: Hietogram
    ) -> None:
        """Create the rainfall."""
        self._total_mm = positive(total_mm, "total_mm")
        self._duration_min = positive(duration_min, "duration_min")
        if not isinstance(hietogram, Hietogram):
            raise InvalidParameterError(
                "The shape of a design storm must be a Hietogram, not "
                f"{type(hietogram).__name__}",
                details={"option": "hietogram", "reason": "type"},
            )
        self._hietogram = hietogram

    @property
    def total_mm(self) -> float:
        """Float: the depth of the storm [mm]."""
        return self._total_mm

    @property
    def duration_min(self) -> float:
        """Float: the duration of the storm [min]."""
        return self._duration_min

    @property
    def hietogram(self) -> Hietogram:
        """Hietogram: the shape of the storm."""
        return self._hietogram

    @property
    def timestep_min(self) -> float | None:
        """None: a design storm is cut at any time step."""
        return None

    def hyetograph(
        self, timestep_min: float, duration_min: float | None = None
    ) -> HietogramResult:
        """Return the storm cut at ``timestep_min``.

        Parameters
        ----------
        timestep_min : float
            The time step [min], > 0 and not above the duration of the storm.
        duration_min : float, optional
            Refused unless it is the duration of the storm.

        Returns
        -------
        HietogramResult
            The depth of every step [mm].

        Raises
        ------
        InvalidParameterError
            If the step is not valid or longer than the storm, or ``duration_min`` is
            another duration (``details.reason`` ``duration_mismatch``).
        """
        step = positive(timestep_min, "timestep_min")
        _same_duration(self._duration_min, duration_min, "The design storm")
        return self._hietogram.generate(
            total_mm=self._total_mm,
            duration_min=self._duration_min,
            timestep_min=step,
        )

    def _shape(self) -> dict[str, Any]:
        """Return the arguments of the shape, by the names of its constructor."""
        names, _ = constructor_arguments(type(self._hietogram))
        return {
            name: getattr(self._hietogram, name)
            for name in names
            if hasattr(self._hietogram, name)
        }

    def _shape_name(self) -> str:
        """Return the name of the shape in :data:`HIETOGRAMS`, else its class name."""
        try:
            return HIETOGRAMS.name_of(self._hietogram)
        except InvalidParameterError:
            return type(self._hietogram).__name__

    def describe(self, hyetograph: HietogramResult | None = None) -> list[Parameter]:
        """List the depth, the duration, the shape and, with a run, the time step.

        The arguments of the shape are ``"default"`` when they are the defaults of its
        constructor; the time step of a run is ``"computed"``: the network gives it.
        """
        listed = [
            parameter("total_mm", self._total_mm, "given"),
            parameter("duration_min", self._duration_min, "given"),
            parameter("hietogram_type", self._shape_name(), "given"),
        ]
        defaults = constructor_defaults(type(self._hietogram))
        for name, value in self._shape().items():
            source: ParameterSource = (
                "default" if value == defaults.get(name) else "given"
            )
            listed.append(parameter(name, value, source))
        if hyetograph is not None:
            listed.append(
                parameter("timestep_min", hyetograph.timestep_min, "computed")
            )
        return listed

    def to_document(self) -> dict[str, Any]:
        """Return the document of the storm, with its ``kind``.

        The fields are ``hietogram_type``, ``total_mm``, ``duration_min`` and the
        arguments of the shape that are not the defaults of its class.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unregistered`` if the shape is not in
            :data:`HIETOGRAMS`: a document cannot name it.
        """
        name = HIETOGRAMS.name_of(self._hietogram)
        return {
            "kind": self.kind,
            "hietogram_type": name,
            "total_mm": self._total_mm,
            "duration_min": self._duration_min,
            **without_defaults(type(self._hietogram), self._shape()),
        }

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> Self:
        """Read the object of a document.

        The fields are ``hietogram_type``, ``total_mm``, ``duration_min`` and the
        arguments of that shape (``alpha`` and ``beta``; ``peak_position``).

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``missing_field``, ``unknown_hietogram_type``,
            ``unknown_field`` (a field that the shape does not take) or the reason of
            the value, and ``details.field``.
        """
        subject = "A design rainfall"
        type_name = required(subject, document, "hietogram_type")
        shape_cls = HIETOGRAMS.resolve(type_name, subject, field="hietogram_type")
        names, _ = constructor_arguments(shape_cls)
        check_fields(
            subject,
            document,
            ("kind", "hietogram_type", "total_mm", "duration_min", *names),
        )
        total = required(subject, document, "total_mm")
        duration = required(subject, document, "duration_min")
        shape = {
            name: document[name] for name in names if document.get(name) is not None
        }
        try:
            hietogram = shape_cls(**shape)
        except InvalidParameterError as exc:
            if exc.details:
                raise
            # the shape classes begin the message with the argument they refuse
            argument = str(exc).split(" ", 1)[0]
            fail(
                str(exc),
                reason="invalid_value",
                field=argument if argument in names else "hietogram_type",
            )
        return cls(total, duration, hietogram)

    def __eq__(self, other: object) -> bool:
        """Compare the documents of two storms."""
        return isinstance(other, DesignStorm) and (
            self.to_document() == other.to_document()
        )

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        """Return the depth, the duration and the shape."""
        return (
            f"DesignStorm(total_mm={self._total_mm:g}, "
            f"duration_min={self._duration_min:g}, hietogram={self._shape_name()!r})"
        )


@RAINFALL_KINDS.register
class RainfallSeries:
    """The depth of rain of every time step: a record, or a series that the caller made.

    The series has the time step that it was measured at. It is not resampled: a
    network at another step refuses it (``timestep_mismatch``), and so does a call of
    :meth:`hyetograph` with another step.

    Parameters
    ----------
    depths_mm : array_like
        The depth of each step [mm], finite and not negative; at least one.
    timestep_min : float
        The time step [min], > 0.

    Raises
    ------
    InvalidParameterError
        If a depth is not valid (``details.reason`` ``too_short``, ``type``,
        ``not_finite``, ``negative``, with ``details.index``) or the step is not.

    Examples
    --------
    >>> from hydrolog.routing import RainfallSeries
    >>> record = RainfallSeries([0.0, 4.0, 11.0, 6.0, 1.0], timestep_min=10.0)
    >>> record.hyetograph(10.0).total_mm
    22.0
    """

    kind: ClassVar[str] = "series"

    def __init__(self, depths_mm: ArrayLike, timestep_min: float) -> None:
        """Create the rainfall."""
        values = as_array(depths_mm, "depths_mm")
        if values.ndim != 1 or values.size == 0:
            raise InvalidParameterError(
                "depths_mm needs at least one value, in one list",
                details={"option": "depths_mm", "reason": "too_short"},
            )
        for reason, found, what in (
            ("not_finite", ~np.isfinite(values), "finite"),
            ("negative", values < 0.0, "not negative"),
        ):
            if found.any():
                index = int(np.flatnonzero(found)[0])
                raise InvalidParameterError(
                    f"depths_mm[{index}] is {float(values[index])!r}: a depth is a "
                    f"number of mm that is {what}",
                    details={
                        "option": "depths_mm",
                        "reason": reason,
                        "index": index,
                    },
                )
        values.setflags(write=False)
        self._depths_mm: NDArray[np.float64] = values
        self._timestep_min = positive(timestep_min, "timestep_min")

    @property
    def depths_mm(self) -> NDArray[np.float64]:
        """numpy.ndarray: the depth of each step [mm] (read-only)."""
        return self._depths_mm

    @property
    def timestep_min(self) -> float:
        """Float: the time step of the series [min]."""
        return self._timestep_min

    @property
    def duration_min(self) -> float:
        """Float: the duration of the series [min]."""
        return len(self._depths_mm) * self._timestep_min

    def hyetograph(
        self, timestep_min: float, duration_min: float | None = None
    ) -> HietogramResult:
        """Return the series as a hyetograph, at its own time step.

        Parameters
        ----------
        timestep_min : float
            Refused unless it is the time step of the series.
        duration_min : float, optional
            Refused unless it is the duration of the series.

        Returns
        -------
        HietogramResult
            The depth of every step [mm], the times being the ends of the steps.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``timestep_mismatch`` or ``duration_mismatch``.
        """
        step = positive(timestep_min, "timestep_min")
        if abs(step - self._timestep_min) > STEP_TOLERANCE * self._timestep_min:
            raise InvalidParameterError(
                f"The rainfall series has a time step of {self._timestep_min:g} min, "
                f"not {step:g} min",
                details={
                    "option": "timestep_min",
                    "reason": "timestep_mismatch",
                    "expected": self._timestep_min,
                    "value": step,
                },
                hint="A series is not resampled: give the network the time step of "
                "the series.",
            )
        _same_duration(self.duration_min, duration_min, "The rainfall series")
        count = len(self._depths_mm)
        return HietogramResult(
            times_min=np.arange(1, count + 1, dtype=np.float64) * self._timestep_min,
            intensities_mm=self._depths_mm.copy(),
            total_mm=float(self._depths_mm.sum()),
            duration_min=self.duration_min,
            timestep_min=self._timestep_min,
        )

    def describe(self, hyetograph: HietogramResult | None = None) -> list[Parameter]:
        """List the time step (given), the depth and the duration (computed)."""
        return [
            parameter("timestep_min", self._timestep_min, "given"),
            parameter("total_mm", float(self._depths_mm.sum()), "computed"),
            parameter("duration_min", self.duration_min, "computed"),
        ]

    def to_document(self) -> dict[str, Any]:
        """Return ``kind``, ``depths_mm`` and ``timestep_min``."""
        return {
            "kind": self.kind,
            "depths_mm": self._depths_mm.tolist(),
            "timestep_min": self._timestep_min,
        }

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> Self:
        """Read the object of a document: ``depths_mm`` and ``timestep_min``.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``missing_field``, ``unknown_field`` or the reason
            of the value, and ``details.field``.
        """
        subject = "A rainfall series"
        check_fields(subject, document, ("kind", "depths_mm", "timestep_min"))
        return cls(
            required(subject, document, "depths_mm"),
            required(subject, document, "timestep_min"),
        )

    def __eq__(self, other: object) -> bool:
        """Compare the depths and the step of two series."""
        return (
            isinstance(other, RainfallSeries)
            and self._timestep_min == other._timestep_min
            and np.array_equal(self._depths_mm, other._depths_mm)
        )

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        """Return the number of steps, the step and the depth."""
        return (
            f"RainfallSeries({len(self._depths_mm)} steps of "
            f"{self._timestep_min:g} min, total_mm={self._depths_mm.sum():g})"
        )
