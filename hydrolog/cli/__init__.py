"""Command line of Hydrolog, generated from the command catalog.

``hydrolog <group> <command> --option VALUE ...`` runs one catalog command (see
:func:`hydrolog.catalog.data_commands`); ``hydrolog mcp`` starts the MCP server. The
modules are:

* :mod:`hydrolog.cli.main` -- the entry point :func:`main` (``python -m hydrolog.cli``);
* :mod:`hydrolog.cli.args` -- general flags, group and command words, language;
* :mod:`hydrolog.cli.parser` -- the argparse parsers and help generated from the
  catalog;
* :mod:`hydrolog.cli.values` -- command-line text to JSON-native option values;
* :mod:`hydrolog.cli.render` -- the text summary of a result and of an error;
* :mod:`hydrolog.cli.texts` -- the Polish and English words the CLI adds to the catalog.

Nothing here is specific to a command: a command added to the catalog is available on
the command line, with help, ``--json`` and ``--schema``, without changes to this
package.
"""

from hydrolog.cli.main import main

__all__ = ["main"]
