"""CLI entry point for Hydrolog.

Provides command-line interface for hydrological calculations:
- tc: Concentration time calculation
- cn: Curve Number lookup (TR-55)
- scs: SCS-CN runoff calculation
- uh: Unit hydrograph generation
"""

import argparse
import sys
from typing import Optional, Sequence

from hydrolog import __version__
from hydrolog.cli.commands import cn, scs, tc, uh


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="hydrolog",
        description="Hydrolog - Python library for hydrological calculations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hydrolog tc kirpich --length 2.5 --slope 0.02
  hydrolog cn lookup --hsg B --cover forest --condition good
  hydrolog scs --cn 72 --precipitation 50
  hydrolog uh scs --area 45 --tc 90 --timestep 5

For more information on a command, use: hydrolog <command> --help
""",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        description="Available commands",
        metavar="<command>",
    )

    # Register subcommands
    tc.register_parser(subparsers)
    cn.register_parser(subparsers)
    scs.register_parser(subparsers)
    uh.register_parser(subparsers)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Main entry point for CLI.

    Parameters
    ----------
    argv : Sequence[str], optional
        Command line arguments. If None, uses sys.argv[1:].

    Returns
    -------
    int
        Exit code (0 for success, non-zero for errors).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    # Execute the command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
