"""MCP server of Hydrolog: the catalog commands as tools (AGI section 5).

Built on the low-level ``Server`` of the official SDK (``mcp`` 2.x, extra
``hydrolog[mcp]``): one tool per catalog command (:mod:`hydrolog.mcp._tools`), every
call runs :func:`hydrolog.catalog.run_command` (:mod:`hydrolog.mcp._calls`), the
``instructions`` of the server say how the tools fit together
(:mod:`hydrolog.mcp._instructions`). The tool list is fixed when the server is
created; the operations behind the tools are imported only when a tool is called, so
the start and ``tools/list`` import no numerical library (AGI-5.11).

MCP specification revision
--------------------------
SDK 2.3 implements the revision **2026-07-28** (``mcp.types.LATEST_PROTOCOL_VERSION``);
a client that speaks an older revision is served through the ``initialize``
handshake. The SDK is pinned as ``mcp>=2.3,<3`` (``pyproject.toml``): the server uses
the low-level ``Server`` API of SDK v2, which a major release may change.

Options
-------
``--allow-dir DIR`` (repeatable) is the only place where files may be read or written
(every path option of a call is checked); ``--allow-writes`` lets the writing tools
write, without it they only plan (``check``); ``--tools FAMILIES`` limits the tools to
the given families (the command groups and ``core``). They are shared by
``hydrolog mcp`` and the console script ``hydrolog-mcp`` (:func:`main`), and by
:func:`create_server` and :func:`run_stdio` as keyword arguments.

This module does not import the SDK: ``import hydrolog.mcp`` works without the extra,
:func:`create_server` and :func:`run_stdio` report its absence with a
:class:`~hydrolog.exceptions.MissingDependencyError` (``pip install hydrolog[mcp]``).
"""

from __future__ import annotations

import argparse
import contextlib
import difflib
import importlib
import json
import os
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, NoReturn

import hydrolog
from hydrolog.catalog import data_commands
from hydrolog.exceptions import (
    HydrologError,
    InvalidParameterError,
    MissingDependencyError,
    NotFoundError,
    error_document,
)
from hydrolog.mcp._families import select_commands

if TYPE_CHECKING:
    from mcp.server import Server

__all__ = [
    "ALLOW_DIR_HELP",
    "ALLOW_WRITES_HELP",
    "INSTALL_HINT",
    "SDK_REQUIREMENT",
    "TOOLS_HELP",
    "add_arguments",
    "create_server",
    "main",
    "run_arguments",
    "run_stdio",
]

SERVER_NAME: Final = "hydrolog"
SERVER_TITLE: Final = "Hydrolog"
SDK_REQUIREMENT: Final = "mcp>=2.3,<3"
"""Requirement on the SDK; the ``mcp`` extra of the package says the same."""
INSTALL_HINT: Final = "pip install hydrolog[mcp]"
"""Command that installs the SDK, as shown in the ``missing_dependency`` error."""
EXIT_INTERRUPTED: Final = 130
"""Exit status after Ctrl-C (128 + SIGINT)."""

ALLOW_DIR_HELP: Final = (
    "Directory in which tools may read and, with --allow-writes, write files "
    "(repeatable); without it commands with path options are refused."
)
ALLOW_WRITES_HELP: Final = (
    "Let the tools that write files write; without it they only plan (check mode)."
)
TOOLS_HELP: Final = (
    "Comma-separated tool families to expose: command groups and core "
    "(default: all tools)."
)
"""English help of the server options (``hydrolog mcp`` shows its own translations)."""

# ``mcp_types`` exists only in SDK 2.x, so an old SDK 1.x counts as missing too; it
# comes first, as the module whose absence best says "install the extra".
_SDK_MODULES: Final = (
    "mcp_types",
    "mcp.server",
    "mcp.server.stdio",
    "mcp.shared.exceptions",
    "mcp.types",
    "anyio",
)
_DEST_ALLOW_DIR: Final = "allow_dir"
_DEST_ALLOW_WRITES: Final = "allow_writes"
_DEST_TOOLS: Final = "tools"


def _require_sdk() -> None:
    """Raise :class:`MissingDependencyError` unless the SDK 2.x can be imported."""
    for module in _SDK_MODULES:
        try:
            importlib.import_module(module)
        except ImportError as exc:
            raise MissingDependencyError(
                f"The MCP server needs the 'mcp' package ({SDK_REQUIREMENT}): "
                f"cannot import {module!r} ({exc})",
                hint=INSTALL_HINT,
                details={
                    "extra": "mcp",
                    "requirement": SDK_REQUIREMENT,
                    "module": module,
                },
            ) from exc


def _resolved_dirs(
    allowed_dirs: Sequence[str | os.PathLike[str]] | str | os.PathLike[str],
) -> tuple[str, ...]:
    """Resolve directories to absolute, symlink-free paths without duplicates.

    ``~`` is expanded and relative ones are taken against the working directory of
    now. An empty text is refused because it would silently mean the working
    directory; a directory that does not exist (a typo) or is a file is refused too.
    """
    if isinstance(allowed_dirs, str | os.PathLike):
        allowed_dirs = (allowed_dirs,)
    resolved: dict[str, None] = {}
    for item in allowed_dirs:
        text = os.fspath(item)
        if not text.strip():
            raise InvalidParameterError(
                "An allowed directory must not be empty",
                details={"option": "allow_dir", "reason": "empty"},
            )
        try:
            path = Path(os.path.expanduser(text)).resolve()
        except (OSError, RuntimeError) as exc:
            raise InvalidParameterError(
                f"Cannot resolve the allowed directory {text!r}: {exc}",
                details={
                    "option": "allow_dir",
                    "reason": "invalid_path",
                    "value": text,
                },
            ) from exc
        if not path.exists():
            raise NotFoundError(
                f"The allowed directory {str(path)!r} does not exist",
                details={"option": "allow_dir", "path": str(path)},
                hint="Give an existing directory.",
            )
        if not path.is_dir():
            raise InvalidParameterError(
                f"The allowed directory {str(path)!r} is not a directory",
                details={
                    "option": "allow_dir",
                    "reason": "not_a_directory",
                    "path": str(path),
                },
                hint="Give a directory, not a file.",
            )
        resolved[str(path)] = None
    return tuple(resolved)


def _unknown_tool(name: str, names: Iterable[str]) -> str:
    close = difflib.get_close_matches(name, list(names), n=3, cutoff=0.6)
    hint = f" Did you mean: {', '.join(close)}?" if close else ""
    return f"Unknown tool {name!r}.{hint}"


def create_server(
    *,
    allowed_dirs: Sequence[str | os.PathLike[str]] = (),
    allow_writes: bool = False,
    families: Sequence[str] | None = None,
) -> Server[Any]:
    """Create the MCP server of the command catalog.

    Parameters
    ----------
    allowed_dirs : sequence of str or os.PathLike, optional
        Directories that every ``path`` option of a call must lie inside (checked
        after resolving ``~``, relative paths and symlinks). Relative entries are taken
        against the working directory at this moment. The default, an empty sequence,
        refuses every path option with the ``forbidden`` error; commands that take no
        files work.
    allow_writes : bool, optional
        Let the tools that write files write them (inside ``allowed_dirs``). By
        default they run in check mode: a call is a plan, ``force`` is ignored, and
        the tool reports ``readOnlyHint`` true.
    families : sequence of str, optional
        Families of tools to expose: the command groups (``"tc"``, ``"stats"``...) and
        ``"core"``, the main tasks. ``None`` (default) exposes every tool.

    Returns
    -------
    mcp.server.Server
        Low-level SDK server with one tool per selected catalog command, named by the
        ``operation_id``, in catalog order. A call answers with the
        ``hydrolog-result/1`` envelope as ``structuredContent`` and as JSON text, or
        with ``isError`` and the ``hydrolog-error/1`` document; a tool the server does
        not have is a protocol error (``INVALID_PARAMS``).

    Raises
    ------
    InvalidParameterError
        If an allowed directory is empty, cannot be resolved or is a file, or
        ``families`` is empty or names an unknown family (``details.allowed`` lists
        the families).
    NotFoundError
        If an allowed directory does not exist.
    MissingDependencyError
        If the ``mcp`` package (2.x) is not installed; ``hint`` says how to install it.
    """
    directories = _resolved_dirs(allowed_dirs)
    selected = select_commands(data_commands(), families)
    _require_sdk()
    import mcp.types as types
    from mcp.server import Server, ServerRequestContext
    from mcp.shared.exceptions import MCPError

    from hydrolog.mcp._calls import call_tool
    from hydrolog.mcp._instructions import build_instructions
    from hydrolog.mcp._tools import catalog_tools

    tools = catalog_tools(selected, allow_writes=allow_writes)
    definitions = [tool.definition for tool in tools.values()]

    async def list_tools(
        ctx: ServerRequestContext[Any], params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        return types.ListToolsResult(tools=definitions)  # one page, whole catalog

    async def call(
        ctx: ServerRequestContext[Any], params: types.CallToolRequestParams
    ) -> types.CallToolResult:
        tool = tools.get(params.name)
        if tool is None:
            raise MCPError(types.INVALID_PARAMS, _unknown_tool(params.name, tools))
        return await call_tool(tool, params.arguments or {}, allowed_dirs=directories)

    return Server(
        SERVER_NAME,
        version=hydrolog.__version__,
        title=SERVER_TITLE,
        instructions=build_instructions(
            data_commands(),
            allowed_dirs=directories,
            allow_writes=allow_writes,
            families=families,
        ),
        on_list_tools=list_tools,
        on_call_tool=call,
    )


def run_stdio(
    *,
    allowed_dirs: Sequence[str | os.PathLike[str]] = (),
    allow_writes: bool = False,
    families: Sequence[str] | None = None,
) -> None:
    """Serve MCP over stdin and stdout until the client closes the connection.

    stdout belongs to the protocol: while serving, the SDK points the process stdout at
    stderr, so stray output of a computation (a ``print`` in an operation) never
    reaches the client; what Python still buffers when the client leaves is flushed to
    stderr before the SDK restores stdout. The call blocks, returns ``None`` when the
    client closes stdin and lets a ``KeyboardInterrupt`` propagate.

    Parameters
    ----------
    allowed_dirs : sequence of str or os.PathLike, optional
        Directories for path options (``--allow-dir DIR``); see :func:`create_server`.
    allow_writes : bool, optional
        Let the writing tools write (``--allow-writes``).
    families : sequence of str, optional
        Families of tools to expose (``--tools``).

    Raises
    ------
    InvalidParameterError
        If an allowed directory or ``families`` is invalid.
    NotFoundError
        If an allowed directory does not exist.
    MissingDependencyError
        If the ``mcp`` package (2.x) is not installed.
    """
    server = create_server(
        allowed_dirs=allowed_dirs, allow_writes=allow_writes, families=families
    )
    import anyio
    from mcp.server.stdio import stdio_server

    async def serve() -> None:
        async with stdio_server() as (read_stream, write_stream):
            try:
                await server.run(
                    read_stream, write_stream, server.create_initialization_options()
                )
            finally:
                # Block-buffered stdout (a pipe) holds the text of a ``print`` until
                # it is flushed; flushed after the SDK restored file descriptor 1 it
                # would reach the client, flushed here it goes to stderr.
                with contextlib.suppress(OSError, ValueError):
                    sys.stdout.flush()

    anyio.run(serve)


# --- command line ---------------------------------------------------------------------


def add_arguments(
    parser: argparse.ArgumentParser | argparse._ArgumentGroup,
    helps: Mapping[str, str] | None = None,
) -> None:
    """Add the server options to a parser (``hydrolog-mcp`` and ``hydrolog mcp``).

    This is the one definition of the options of both entry points.

    Parameters
    ----------
    parser : argparse.ArgumentParser or argparse._ArgumentGroup
        Where to add ``--allow-dir``, ``--allow-writes`` and ``--tools``. An option
        that is not given is absent from the namespace (read it with
        :func:`run_arguments`).
    helps : Mapping[str, str], optional
        Help texts by ``"allow_dir"``, ``"allow_writes"`` and ``"tools"``; the English
        :data:`ALLOW_DIR_HELP`, :data:`ALLOW_WRITES_HELP` and :data:`TOOLS_HELP` by
        default.
    """
    texts = {
        _DEST_ALLOW_DIR: ALLOW_DIR_HELP,
        _DEST_ALLOW_WRITES: ALLOW_WRITES_HELP,
        _DEST_TOOLS: TOOLS_HELP,
        **(helps or {}),
    }
    parser.add_argument(
        "--allow-dir",
        dest=_DEST_ALLOW_DIR,
        action="append",
        metavar="DIR",
        default=argparse.SUPPRESS,
        help=texts[_DEST_ALLOW_DIR],
    )
    parser.add_argument(
        "--allow-writes",
        dest=_DEST_ALLOW_WRITES,
        action="store_true",
        default=argparse.SUPPRESS,
        help=texts[_DEST_ALLOW_WRITES],
    )
    parser.add_argument(
        "--tools",
        dest=_DEST_TOOLS,
        metavar="FAMILIES",
        default=argparse.SUPPRESS,
        help=texts[_DEST_TOOLS],
    )


def run_arguments(namespace: argparse.Namespace) -> None:
    """Serve MCP over stdio with the options of a parsed command line.

    Parameters
    ----------
    namespace : argparse.Namespace
        Result of a parser that got :func:`add_arguments`.

    Raises
    ------
    InvalidParameterError
        If a directory or the list of families is invalid.
    NotFoundError
        If an allowed directory does not exist.
    MissingDependencyError
        If the ``mcp`` package (2.x) is not installed.
    """
    from hydrolog.mcp._families import parse_families

    values = vars(namespace)
    tools = values.get(_DEST_TOOLS)
    run_stdio(
        allowed_dirs=values.get(_DEST_ALLOW_DIR, []),
        allow_writes=values.get(_DEST_ALLOW_WRITES, False),
        families=None if tools is None else parse_families(tools),
    )


class _ServerParser(argparse.ArgumentParser):
    """Parser of ``hydrolog-mcp`` whose usage errors are ``validation_error``."""

    def error(self, message: str) -> NoReturn:
        """Raise :class:`InvalidParameterError` instead of printing and exiting."""
        raise InvalidParameterError(
            message,
            details={"reason": "usage"},
            hint=f"Run '{self.prog} --help' to see the usage.",
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the console script ``hydrolog-mcp``: serve MCP over stdio.

    Parameters
    ----------
    argv : sequence of str, optional
        The command line without the program name; ``sys.argv[1:]`` by default.

    Returns
    -------
    int
        ``0`` when the client closed the connection, ``2`` for an invalid command line
        or option value (a ``--lang`` too: the server output is always English),
        ``3`` for a missing allowed directory, ``6`` when the ``mcp`` extra is missing
        (the ``hydrolog-error/1`` document goes to stderr), ``130`` after Ctrl-C.
    """
    parser = _ServerParser(
        prog="hydrolog-mcp",
        description="Start the Hydrolog MCP server on stdin/stdout. Needs the "
        "hydrolog[mcp] extra; only the protocol goes to stdout.",
        allow_abbrev=False,
    )
    add_arguments(parser)
    try:
        run_arguments(parser.parse_args(argv))
    except SystemExit as exc:  # argparse prints the help after --help and exits with 0
        return exc.code if isinstance(exc.code, int) else 0
    except KeyboardInterrupt:
        return EXIT_INTERRUPTED
    except HydrologError as exc:
        document = error_document(exc)
        print(json.dumps(document, ensure_ascii=False), file=sys.stderr)
        return int(document["exit_code"])
    return 0
