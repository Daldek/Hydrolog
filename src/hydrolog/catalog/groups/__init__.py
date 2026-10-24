"""Registry of the command groups of the catalog.

A *group* is a module of this package that exports ``COMMANDS``, a tuple of
:class:`~hydrolog.catalog.spec.Command` whose names share the first word (the group:
``tc kirpich`` and ``tc nrcs`` belong to ``tc``). The modules named in
:data:`GROUP_MODULES` make up the catalog; their order is the order of groups in
``hydrolog --help``, in the agent guide and in
:func:`~hydrolog.catalog.data_commands` (commands inside a group are sorted by name).
Modules are imported when the catalog is first read.

To add a group: create ``src/hydrolog/catalog/groups/<module>.py`` with ``COMMANDS`` and
append ``"<module>"`` to :data:`GROUP_MODULES` (design order: ``tc``, ``cn``, ``scs``,
``precip``, ``uh``, ``hydrograph``, ``route``, ``morphometry``, ``network``,
``stats``, ``hydrometrics``, ``soil``, ``report``, ``config``, then ``meta`` -- the
group ``commands`` -- last).
"""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from types import ModuleType

from hydrolog.catalog.spec import Command

GROUP_MODULES: tuple[str, ...] = (
    "tc",
    "cn",
    "scs",
    "precip",
    "uh",
    "hydrograph",
    "route",
    "morphometry",
    "network",
    "stats",
    "hydrometrics",
    "soil",
    "report",
    "config",
    "meta",
)
"""Names of the group modules of this package, in presentation order."""


def collect_commands(
    modules: Sequence[str | ModuleType] | None = None,
) -> tuple[Command, ...]:
    """Collect and check the commands of the group modules.

    Parameters
    ----------
    modules : sequence of str or module, optional
        Group modules, each exporting ``COMMANDS``: names of modules of this package
        (``"meta"``) or module objects. Defaults to :data:`GROUP_MODULES`.

    Returns
    -------
    tuple of Command
        Commands ordered by group (the order of ``modules``), then by name.

    Raises
    ------
    ValueError
        If a module does not export a non-empty tuple of commands, holds commands of
        more than one group, shares its group with another module, or two commands
        have the same name or ``operation_id``.
    ModuleNotFoundError
        If a named module does not exist.
    """
    chosen: Sequence[str | ModuleType] = GROUP_MODULES if modules is None else modules
    collected: list[Command] = []
    groups: dict[str, str] = {}
    names: set[str] = set()
    operation_ids: set[str] = set()
    for entry in chosen:
        module = (
            importlib.import_module(f"{__name__}.{entry}")
            if isinstance(entry, str)
            else entry
        )
        label = module.__name__
        commands = getattr(module, "COMMANDS", None)
        if (
            not isinstance(commands, tuple)
            or not commands
            or not all(isinstance(command, Command) for command in commands)
        ):
            raise ValueError(f"{label}: COMMANDS must be a non-empty tuple of Command")
        module_groups = {command.group for command in commands}
        if len(module_groups) != 1:
            raise ValueError(
                f"{label}: commands of several groups: {sorted(module_groups)}"
            )
        group = next(iter(module_groups))
        if group in groups:
            raise ValueError(
                f"{label}: group {group!r} is already defined by {groups[group]}"
            )
        groups[group] = label
        for command in sorted(commands, key=lambda item: item.name):
            if command.name in names or command.operation_id in operation_ids:
                raise ValueError(f"{label}: duplicate command {command.name!r}")
            names.add(command.name)
            operation_ids.add(command.operation_id)
            collected.append(command)
    return tuple(collected)
