"""MCP server of Hydrolog: the catalog commands as tools (spec section 7.2).

Built on the low-level ``Server`` of the official SDK (``mcp`` 2.x, extra
``hydrolog[mcp]``): one tool per catalog command (:mod:`hydrolog.mcp._tools`), every
call runs :func:`hydrolog.catalog.run_command` (:mod:`hydrolog.mcp._calls`), the
``instructions`` of the server are short rules built from the catalog
(:mod:`hydrolog.mcp._instructions`). The tool list is fixed when the server is created.

This module does not import the SDK: ``import hydrolog.mcp`` works without the extra,
:func:`create_server` and :func:`run_stdio` report its absence with a
:class:`~hydrolog.exceptions.MissingDependencyError` (``pip install hydrolog[mcp]``).
"""

from __future__ import annotations

import contextlib
import difflib
import importlib
import os
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import hydrolog
from hydrolog.catalog import data_commands
from hydrolog.catalog.spec import LANGUAGES, Lang
from hydrolog.exceptions import InvalidParameterError, MissingDependencyError

if TYPE_CHECKING:
    from mcp.server import Server

__all__ = ["INSTALL_HINT", "SDK_REQUIREMENT", "create_server", "run_stdio"]

SERVER_NAME: Final = "hydrolog"
SERVER_TITLE: Final = "Hydrolog"
SDK_REQUIREMENT: Final = "mcp>=2.3,<3"
"""Requirement on the SDK; the ``mcp`` extra of the package says the same."""
INSTALL_HINT: Final = "pip install hydrolog[mcp]"
"""Command that installs the SDK, as shown in the ``missing_dependency`` error."""

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


def _checked_lang(lang: str) -> Lang:
    if lang not in LANGUAGES:
        raise InvalidParameterError(
            f"Unknown language {lang!r}; allowed: {', '.join(LANGUAGES)}",
            details={
                "option": "lang",
                "reason": "choice",
                "allowed": list(LANGUAGES),
                "value": str(lang),
            },
        )
    return "en" if lang == "en" else "pl"


def _resolved_dirs(
    allowed_dirs: Sequence[str | os.PathLike[str]] | str | os.PathLike[str],
) -> tuple[str, ...]:
    """Absolute, symlink-free directories (``~`` expanded, relative ones against the
    working directory of now), without duplicates; an empty text is refused because
    it would silently mean the working directory."""
    if isinstance(allowed_dirs, str | os.PathLike):
        allowed_dirs = (allowed_dirs,)
    resolved: dict[str, None] = {}
    for item in allowed_dirs:
        text = os.fspath(item)
        if not text.strip():
            raise InvalidParameterError(
                "An allowed directory must not be empty",
                details={"option": "allowed_dirs", "reason": "empty"},
            )
        try:
            resolved[str(Path(os.path.expanduser(text)).resolve())] = None
        except (OSError, RuntimeError) as exc:
            raise InvalidParameterError(
                f"Cannot resolve the allowed directory {text!r}: {exc}",
                details={
                    "option": "allowed_dirs",
                    "reason": "invalid_path",
                    "value": text,
                },
            ) from exc
    return tuple(resolved)


def _unknown_tool(name: str, names: Iterable[str]) -> str:
    close = difflib.get_close_matches(name, list(names), n=3, cutoff=0.6)
    hint = f" Did you mean: {', '.join(close)}?" if close else ""
    return f"Unknown tool {name!r}.{hint}"


def create_server(
    *,
    allowed_dirs: Sequence[str | os.PathLike[str]] = (),
    lang: Lang = "pl",
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
    lang : {"pl", "en"}, optional
        Language of the tool texts, of the instructions, of the error titles and the
        default of the ``lang`` options of the commands.

    Returns
    -------
    mcp.server.Server
        Low-level SDK server with one tool per catalog command, named by the
        ``operation_id``, in catalog order. A call answers with the
        ``hydrolog-result/1`` envelope as ``structuredContent`` and as JSON text, or
        with ``isError`` and the ``hydrolog-error/1`` document; a tool the server does
        not have is a protocol error (``INVALID_PARAMS``).

    Raises
    ------
    InvalidParameterError
        If ``lang`` is not ``"pl"`` or ``"en"`` or an allowed directory is empty or
        cannot be resolved.
    MissingDependencyError
        If the ``mcp`` package (2.x) is not installed; ``hint`` says how to install it.
    """
    checked_lang = _checked_lang(lang)
    directories = _resolved_dirs(allowed_dirs)
    _require_sdk()
    import mcp.types as types
    from mcp.server import Server, ServerRequestContext
    from mcp.shared.exceptions import MCPError

    from hydrolog.mcp._calls import call_tool
    from hydrolog.mcp._instructions import build_instructions
    from hydrolog.mcp._tools import catalog_tools

    commands = data_commands()
    tools = catalog_tools(commands, lang=checked_lang)
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
        return await call_tool(
            tool, params.arguments or {}, allowed_dirs=directories, lang=checked_lang
        )

    return Server(
        SERVER_NAME,
        version=hydrolog.__version__,
        title=SERVER_TITLE,
        instructions=build_instructions(
            commands, lang=checked_lang, allowed_dirs=directories
        ),
        on_list_tools=list_tools,
        on_call_tool=call,
    )


def run_stdio(
    *,
    allowed_dirs: Sequence[str | os.PathLike[str]] = (),
    lang: Lang = "pl",
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
        Directories for path options (``hydrolog mcp --allow-dir DIR``); see
        :func:`create_server`.
    lang : {"pl", "en"}, optional
        Language of the server (``hydrolog mcp --lang``).

    Raises
    ------
    InvalidParameterError
        If ``lang`` or an allowed directory is invalid.
    MissingDependencyError
        If the ``mcp`` package (2.x) is not installed.
    """
    server = create_server(allowed_dirs=allowed_dirs, lang=lang)
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
