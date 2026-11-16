"""MCP server of Hydrolog: the command catalog for AI agents (extra ``hydrolog[mcp]``).

The third adapter of the catalog, next to the Python API and the CLI: every catalog
command is one MCP tool named by its ``operation_id``, with the command's JSON Schema
as input schema and the ``hydrolog-result/1`` envelope as output schema. A call
answers with the envelope (``structuredContent`` plus the same JSON as text) or, with
``isError``, with the ``hydrolog-error/1`` document. Without ``allowed_dirs`` the
commands that take files are refused (``forbidden``); commands that take only values
work. Without ``allow_writes`` the commands that write files only plan (``check``).

* :func:`create_server` -- the SDK ``Server`` (for tests and other transports);
* :func:`run_stdio` -- serve it over stdio (``hydrolog mcp`` and ``hydrolog-mcp``,
  ``[--allow-dir DIR]... [--allow-writes] [--tools FAMILIES]``);
* :func:`main` -- the console script ``hydrolog-mcp``.

Importing this package does not import the SDK; the functions that serve raise
:class:`~hydrolog.exceptions.MissingDependencyError` (``pip install hydrolog[mcp]``)
when it is missing.

Examples
--------
Claude Code::

    claude mcp add hydrolog -- hydrolog-mcp --allow-dir ~/hydrolog-data

Other clients (``mcpServers``)::

    {"command": "hydrolog-mcp", "args": ["--allow-dir", "/path/to/hydrolog-data"]}
"""

from hydrolog.mcp.server import create_server, main, run_stdio

__all__ = ["create_server", "main", "run_stdio"]
