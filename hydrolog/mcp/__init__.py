"""MCP server of Hydrolog: the command catalog for AI agents (extra ``hydrolog[mcp]``).

The third adapter of the catalog, next to the Python API and the CLI: every catalog
command is one MCP tool named by its ``operation_id``, with the command's JSON Schema
as input schema. A call answers with the ``hydrolog-result/1`` envelope
(``structuredContent`` plus the same JSON as text) or, with ``isError``, with the
``hydrolog-error/1`` document. Without ``allowed_dirs`` the commands that take files
are refused (``forbidden``); commands that take only values work.

* :func:`create_server` -- the SDK ``Server`` (for tests and other transports);
* :func:`run_stdio` -- serve it over stdio (``hydrolog mcp [--allow-dir DIR]...
  [--lang pl|en]``).

Importing this package does not import the SDK; both functions raise
:class:`~hydrolog.exceptions.MissingDependencyError` (``pip install hydrolog[mcp]``)
when it is missing.

Examples
--------
Claude Code::

    claude mcp add hydrolog -- hydrolog mcp --allow-dir ~/hydrolog-data

Other clients (``mcpServers``)::

    {"command": "hydrolog", "args": ["mcp", "--allow-dir", "/home/ola/hydrolog-data"]}
"""

from hydrolog.mcp.server import create_server, run_stdio

__all__ = ["create_server", "run_stdio"]
