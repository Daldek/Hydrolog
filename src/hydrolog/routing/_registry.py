"""Registries: the name that a document gives a class, and the class (ADR-0012).

A network is extended by a new class, not by an edit of a central switch: a node type,
a routing method, a rainfall source and a runoff model are each a class that has a
name (``kind`` or ``model``) and reads and writes its own fields. The class is
registered under its name once, and the reader and the writer of
``hydrolog-network/1`` (:mod:`hydrolog.routing.document`) find it there. Nothing else
knows the list.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._checks import shown

__all__ = ["Registry"]


class Registry[T]:
    """Classes of one family by the name a document gives them.

    Parameters
    ----------
    what : str
        What the name is, for the messages (``"type"``, ``"method"``, ``"kind"``,
        ``"model"``): ``unknown type 'river'``, ``The types are ...``.
    key : str
        The class attribute that holds the name (``"kind"``, ``"model"``).
    reason : str
        ``details.reason`` of the error of a name that is not registered
        (``"unknown_type"``...).
    needs : sequence of str, optional
        Methods that a class must have to be registered, so that a class that a
        document names cannot lack the code that reads and writes it.

    Examples
    --------
    >>> from hydrolog.routing import NODE_TYPES
    >>> NODE_TYPES.names
    ('subcatchment', 'reach', 'reservoir', 'junction', 'outlet')
    >>> NODE_TYPES["junction"].__name__
    'Junction'
    """

    def __init__(
        self, what: str, *, key: str, reason: str, needs: Sequence[str] = ()
    ) -> None:
        """Create an empty registry."""
        self.what = what
        self._key = key
        self._reason = reason
        self._needs = tuple(needs)
        self._classes: dict[str, type[T]] = {}

    def register(self, cls: type[T]) -> type[T]:
        """Register ``cls`` under the name in its attribute; use it as a decorator.

        Parameters
        ----------
        cls : type
            The class; its attribute named by ``key`` is the name.

        Returns
        -------
        type
            ``cls``, so that the method can decorate the class.

        Raises
        ------
        TypeError
            If the class has no name.
        ValueError
            If the name is taken by another class.
        """
        name = getattr(cls, self._key, None)
        if not isinstance(name, str) or not name:
            raise TypeError(
                f"{cls.__name__} has no {self._key!r}: the name of its {self.what}"
            )
        return self.add(name, cls)

    def add(self, name: str, cls: type[T]) -> type[T]:
        """Register ``cls`` under ``name`` (for a class that has no name of its own).

        Parameters
        ----------
        name : str
            The name a document gives the class.
        cls : type
            The class.

        Returns
        -------
        type
            ``cls``.

        Raises
        ------
        TypeError
            If the class lacks a method that the registry needs.
        ValueError
            If the name is taken by another class.
        """
        lacking = [
            method for method in self._needs if not callable(getattr(cls, method, None))
        ]
        if lacking:
            raise TypeError(
                f"{cls.__name__} cannot be a {self.what} of a document: it has no "
                f"{', '.join(lacking)}"
            )
        taken = self._classes.get(name)
        if taken is not None and taken is not cls:
            raise ValueError(
                f"The {self.what} {name!r} is already registered to {taken.__name__}"
            )
        self._classes[name] = cls
        return cls

    @property
    def names(self) -> tuple[str, ...]:
        """Tuple of str: the registered names, in the order of registration."""
        return tuple(self._classes)

    def __contains__(self, name: object) -> bool:
        """Whether ``name`` is registered."""
        return name in self._classes

    def __getitem__(self, name: str) -> type[T]:
        """Return the class registered under ``name``; ``KeyError`` if there is none."""
        return self._classes[name]

    def __iter__(self) -> Iterator[str]:
        """Iterate over the registered names."""
        return iter(self._classes)

    def resolve(self, name: object, subject: str, **details: Any) -> type[T]:
        """Return the class of a name that a document gave, or explain what is wrong.

        Parameters
        ----------
        name : object
            The name as the document has it (any JSON value).
        subject : str
            Who has the name, for the message: ``"Node 'A'"``.
        **details
            Facts that go to ``details`` of the error (``node_id``...).

        Returns
        -------
        type
            The registered class.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` the ``reason`` of the registry, ``value`` and
            ``allowed`` (the registered names), when ``name`` is not registered.
        """
        if isinstance(name, str) and name in self._classes:
            return self._classes[name]
        allowed = ", ".join(self._classes)
        raise InvalidParameterError(
            f"{subject} has the unknown {self.what} {shown(name)}",
            details={
                "reason": self._reason,
                **details,
                "value": shown(name),
                "allowed": list(self._classes),
            },
            hint=f"The {self.what}s are {allowed}.",
        )

    def name_of(self, instance: object) -> str:
        """Return the name under which the class of ``instance`` is registered.

        A subclass that is not registered takes the name of its nearest registered
        parent.

        Parameters
        ----------
        instance : object
            An object of a registered class.

        Returns
        -------
        str
            The name.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unregistered`` when no class of the object is
            registered: a document cannot name it.
        """
        for parent in type(instance).__mro__:
            for name, cls in self._classes.items():
                if cls is parent:
                    return name
        raise InvalidParameterError(
            f"{type(instance).__name__} is not a registered {self.what} of a document",
            details={"reason": "unregistered", "value": type(instance).__name__},
            hint="Register its class, so that a document can name it.",
        )
