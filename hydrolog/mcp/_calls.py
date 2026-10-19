"""Calls of the MCP tools (spec section 7.2).

A call runs the catalog command through :func:`hydrolog.catalog.run_command` -- the
only validator and the only place of the path policy -- in a worker thread, so a
long computation does not stop the other requests of the connection. The path policy
gets the directories of the server; an empty list refuses every path option
(``forbidden``), while commands without files work.

Answers
-------
* Success: ``structuredContent`` is the ``hydrolog-result/1`` envelope and the only
  text content is the same document as compact JSON (clients that ignore structured
  content still get it).
* Failure: ``isError`` with the ``hydrolog-error/1`` document, in the same two forms.
  A :class:`~hydrolog.exceptions.HydrologError` keeps its code; an ``OSError`` is an
  ``io_error``; any other exception is an ``internal_error`` (its traceback goes to
  the log of the server, i.e. to stderr, never to the client).

A request cancelled by the client waits for its worker thread: a command that writes a
file is never cut off halfway, and its answer is dropped.
"""

from __future__ import annotations

import functools
import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any

import anyio.to_thread
import mcp.types as types

from hydrolog.catalog import run_command
from hydrolog.catalog.spec import Lang
from hydrolog.exceptions import error_document
from hydrolog.mcp._tools import LANG_OPTION, CatalogTool

__all__ = ["call_tool", "execute"]

_LOG = logging.getLogger(__name__)


def _json(document: Mapping[str, Any]) -> str:
    """Compact JSON of a document (UTF-8 text, no ``NaN``)."""
    return json.dumps(
        document, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def _answer(
    document: Mapping[str, Any], *, is_error: bool = False
) -> types.CallToolResult:
    return types.CallToolResult(
        content=[types.TextContent(text=_json(document))],
        structured_content=dict(document),
        is_error=is_error,
    )


def execute(
    tool: CatalogTool,
    arguments: Mapping[str, Any],
    *,
    allowed_dirs: Sequence[str],
    lang: Lang,
) -> types.CallToolResult:
    """Run the command of a tool and describe the outcome as a tool result.

    Parameters
    ----------
    tool : CatalogTool
        The called tool.
    arguments : Mapping[str, Any]
        Arguments of the call: the options of the command. A missing ``lang`` option
        is the server ``lang``.
    allowed_dirs : sequence of str
        Directories every path option must lie in; empty refuses every path.
    lang : {"pl", "en"}
        Language of the server (title of an error document).

    Returns
    -------
    mcp.types.CallToolResult
        The envelope on success, the error document with ``isError`` otherwise;
        raises no ``Exception``.
    """
    options = dict(arguments)
    if tool.lang_option and options.get(LANG_OPTION) is None:
        options[LANG_OPTION] = lang
    try:
        outcome = run_command(tool.command, options, allowed_dirs=allowed_dirs)
        return _answer(outcome.to_dict())
    except Exception as exc:
        document = error_document(exc, tool.command.name, lang)
        if document["code"] == "internal_error":
            _LOG.error(
                "MCP tool %s failed with an internal error",
                tool.definition.name,
                exc_info=exc,
            )
        return _answer(document, is_error=True)


async def call_tool(
    tool: CatalogTool,
    arguments: Mapping[str, Any],
    *,
    allowed_dirs: Sequence[str],
    lang: Lang,
) -> types.CallToolResult:
    """Run :func:`execute` in a worker thread (parameters and result as there)."""
    return await anyio.to_thread.run_sync(
        functools.partial(
            execute, tool, arguments, allowed_dirs=allowed_dirs, lang=lang
        )
    )
