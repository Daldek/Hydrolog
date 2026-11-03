"""Families of tools (AGI-5.8, AGI-5.12): ``--tools`` selects commands by family.

A family is a command group (``tc``, ``stats``...) or ``core``, the main tasks of the
catalog (``Command.families``). The module does not need the MCP SDK, so the command
line can check the families before the server is built.
"""

from __future__ import annotations

from collections.abc import Sequence

from hydrolog.catalog import Command
from hydrolog.exceptions import InvalidParameterError

__all__ = ["family_names", "parse_families", "select_commands"]


def family_names(commands: Sequence[Command]) -> tuple[str, ...]:
    """Return the families of ``commands``: the groups in catalog order, then ``core``.

    Parameters
    ----------
    commands : sequence of Command
        The catalog.

    Returns
    -------
    tuple of str
        Each family name once.
    """
    names: dict[str, None] = {}
    for command in commands:
        for family in command.families:
            names[family] = None
    ordered = [name for name in names if name != "core"]
    return (*ordered, "core") if "core" in names else tuple(ordered)


def parse_families(text: str) -> tuple[str, ...]:
    """Split the comma-separated value of ``--tools`` into family names.

    Parameters
    ----------
    text : str
        E.g. ``"core"`` or ``"tc, cn"``.

    Returns
    -------
    tuple of str
        The names, stripped, in the given order.

    Raises
    ------
    InvalidParameterError
        If a name is empty (``details.reason`` ``empty``).
    """
    names = tuple(item.strip() for item in text.split(","))
    if not all(names):
        raise InvalidParameterError(
            f"The list of families {text!r} has an empty name",
            details={"option": "tools", "reason": "empty", "value": text},
            hint="Give comma-separated family names, e.g. core,stats.",
        )
    return names


def select_commands(
    commands: Sequence[Command], families: Sequence[str] | None
) -> tuple[Command, ...]:
    """Pick the commands of the given families, in catalog order.

    Parameters
    ----------
    commands : sequence of Command
        The catalog.
    families : sequence of str or None
        Family names (see :func:`family_names`); ``None`` selects every command.

    Returns
    -------
    tuple of Command
        The commands that belong to at least one of the families.

    Raises
    ------
    InvalidParameterError
        If ``families`` is empty (``details.reason`` ``empty``) or names a family that
        does not exist (``choice``); ``details.allowed`` lists the families.
    """
    if families is None:
        return tuple(commands)
    allowed = family_names(commands)
    if not families:
        raise InvalidParameterError(
            "No tool family is selected",
            details={
                "option": "tools",
                "reason": "empty",
                "value": [],
                "allowed": list(allowed),
            },
            hint=f"Use one or more of: {', '.join(allowed)}.",
        )
    unknown = [name for name in families if name not in allowed]
    if unknown:
        raise InvalidParameterError(
            f"Unknown tool family {', '.join(map(repr, unknown))}; "
            f"allowed: {', '.join(allowed)}",
            details={
                "option": "tools",
                "reason": "choice",
                "value": unknown,
                "allowed": list(allowed),
            },
            hint=f"Use one or more of: {', '.join(allowed)}.",
        )
    wanted = set(families)
    return tuple(command for command in commands if wanted & set(command.families))
