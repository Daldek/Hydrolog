"""Command catalog: the single source of truth for every Hydrolog interface.

The catalog declares each command once (:class:`Command`, :class:`Option`); the CLI,
the MCP server and the generated agent guides are built from it, and Python callers
reach the same operations through :func:`run_command`.

Public API
----------
* :func:`data_commands` -- all commands, ordered by group, then by name;
* :func:`get_command` -- one command by name (``"tc kirpich"``) or ``operation_id``
  (``"tc_kirpich"``);
* :func:`command_schema` -- the ``hydrolog-commands/1`` JSON Schema document;
* :func:`validate_command` -- validate and normalize option values;
* :func:`run_command` -- validate, apply the path policy, run the operation, return a
  :class:`CommandResult` (``hydrolog-result/1`` envelope);
* :func:`capture_warnings` -- inside an operation, turn the library's Python warnings
  into the :class:`Notice` objects of the envelope.

Submodules: :mod:`~hydrolog.catalog.spec` (declarations),
:mod:`~hydrolog.catalog.envelope` (envelope, notices, operation return protocol),
:mod:`~hydrolog.catalog.inputs` (series, watershed, stations from inline JSON or
files), :mod:`~hydrolog.catalog.dispatch` (lookup, validation, running) and
:mod:`~hydrolog.catalog.groups` (one module per command group).

How to add a command
--------------------
1. **Operation.** Add a public, documented (NumPy docstring), fully type-hinted,
   keyword-only function to the module of its group, ``hydrolog/operations/<group>.py``
   (``operations`` is a package with one module per group; a new group gets a new
   module), and re-export it in ``hydrolog/operations/__init__.py`` (``import`` and
   ``__all__``), where ``function="hydrolog.operations:<name>"`` resolves.
   Its parameters are named exactly like the options, take JSON-friendly values
   (numbers, strings, lists, paths as ``str``) and have a Python default wherever the
   option has no ``required=True``. It composes existing classes (no new
   hydrology) and returns a ``JsonResultMixin`` result, or an
   :class:`~hydrolog.catalog.envelope.OperationOutput` when it has notices (for the
   library's ``UserWarning`` use :func:`capture_warnings`) or writes
   files (see :mod:`hydrolog.catalog.envelope`). Load series, stations and watershed
   parameters with :mod:`hydrolog.catalog.inputs`; raise the errors of
   :mod:`hydrolog.exceptions` (``InvalidParameterError``, ``InputDataError``,
   ``CalculationError``, ``OutputError``...).
2. **Declaration.** Create ``hydrolog/catalog/groups/<group>.py`` (or extend the
   module of an existing group) exporting ``COMMANDS``, a tuple of :class:`Command`::

       COMMANDS = (
           Command(
               name="tc kirpich",
               operation_id="tc_kirpich",
               summary="...",            # Polish, <= 120 characters
               summary_en="...",
               description="...",        # Polish: method, literature, limits
               description_en="...",
               function="hydrolog.operations:tc_kirpich",
               options=(
                   Option("length_km", "number", "Długość cieku [km]",
                          "Channel length [km]", required=True,
                          exclusive_minimum=0, unit="km"),
               ),
               examples=({"length_km": 8.2, "slope_m_per_m": 0.023},),
           ),
       )

   Declarations are checked when the module is imported (unique names, choices only
   for ``choice``, ``operation_id`` = snake_case of ``name``, function path
   format...).
3. **Registration.** Append the module name to ``GROUP_MODULES`` in
   ``hydrolog/catalog/groups/__init__.py`` (its position is the group order in the CLI
   help and the agent guide; the ``commands`` group stays last).
4. **Tests.** Every command needs at least one ``examples`` entry; the catalog tests
   run each example through :func:`run_command` and check that every option is a
   parameter of the operation.
"""

from hydrolog.catalog.dispatch import (
    command_schema,
    data_commands,
    get_command,
    run_command,
    validate_command,
)
from hydrolog.catalog.envelope import (
    CommandResult,
    FileRecord,
    Notice,
    OperationOutput,
    capture_warnings,
)
from hydrolog.catalog.spec import Command, Option

__all__ = [
    "Command",
    "CommandResult",
    "FileRecord",
    "Notice",
    "OperationOutput",
    "Option",
    "capture_warnings",
    "command_schema",
    "data_commands",
    "get_command",
    "run_command",
    "validate_command",
]
