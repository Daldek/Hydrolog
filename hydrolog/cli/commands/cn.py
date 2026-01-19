"""CLI command for Curve Number lookup."""

import argparse

from hydrolog.runoff import (
    HydrologicCondition,
    LandCover,
    get_cn,
    get_cn_range,
    list_land_covers,
)


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'cn' command parser."""
    parser = subparsers.add_parser(
        "cn",
        help="Curve Number lookup (TR-55)",
        description="Look up Curve Number values from USDA TR-55 tables.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  lookup  Look up CN for specific HSG and land cover
  list    List available land cover types
  range   Show CN range for a land cover type

Examples:
  hydrolog cn lookup --hsg B --cover forest --condition good
  hydrolog cn lookup --hsg C --cover paved
  hydrolog cn list
  hydrolog cn range --cover forest
""",
    )

    # Create subparsers for subcommands
    cn_parsers = parser.add_subparsers(
        title="subcommands",
        dest="subcommand",
        description="Available subcommands",
        metavar="<subcommand>",
    )

    # Lookup subcommand
    lookup = cn_parsers.add_parser(
        "lookup",
        help="Look up CN value",
        description="Look up CN for a specific HSG and land cover combination.",
    )
    lookup.add_argument(
        "--hsg",
        type=str,
        required=True,
        choices=["A", "B", "C", "D", "a", "b", "c", "d"],
        metavar="HSG",
        help="Hydrologic Soil Group (A, B, C, or D)",
    )
    lookup.add_argument(
        "--cover",
        type=str,
        required=True,
        metavar="TYPE",
        help="Land cover type (use 'hydrolog cn list' to see options)",
    )
    lookup.add_argument(
        "--condition",
        type=str,
        choices=["poor", "fair", "good"],
        default=None,
        metavar="COND",
        help="Hydrologic condition (poor, fair, good) - required for some covers",
    )
    lookup.set_defaults(func=_run_lookup)

    # List subcommand
    list_cmd = cn_parsers.add_parser(
        "list",
        help="List land cover types",
        description="List all available land cover types for CN lookup.",
    )
    list_cmd.set_defaults(func=_run_list)

    # Range subcommand
    range_cmd = cn_parsers.add_parser(
        "range",
        help="Show CN range",
        description="Show the range of CN values for a land cover type across all HSGs.",
    )
    range_cmd.add_argument(
        "--cover",
        type=str,
        required=True,
        metavar="TYPE",
        help="Land cover type",
    )
    range_cmd.set_defaults(func=_run_range)

    parser.set_defaults(func=_show_help, parser=parser)


def _show_help(args: argparse.Namespace) -> int:
    """Show help when no subcommand is specified."""
    args.parser.print_help()
    return 0


def _run_lookup(args: argparse.Namespace) -> int:
    """Execute CN lookup."""
    hsg = args.hsg.upper()
    cover = args.cover.lower()
    condition = args.condition

    # Parse condition
    cond_enum = None
    if condition:
        cond_enum = HydrologicCondition(condition.lower())

    cn = get_cn(hsg, cover, cond_enum)

    print(f"Curve Number Lookup (TR-55)")
    print(f"{'─' * 35}")
    print(f"  HSG:        {hsg}")
    print(f"  Land cover: {cover}")
    if condition:
        print(f"  Condition:  {condition}")
    print(f"{'─' * 35}")
    print(f"  CN = {cn}")

    return 0


def _run_list(args: argparse.Namespace) -> int:
    """List available land cover types."""
    covers = list_land_covers()

    print("Available Land Cover Types (TR-55)")
    print(f"{'─' * 50}")

    # Group by category
    agricultural = ["FALLOW", "ROW_CROPS", "SMALL_GRAIN", "PASTURE", "MEADOW"]
    natural = ["BRUSH", "FOREST", "HERBACEOUS"]
    developed = [
        "FARMSTEAD",
        "RESIDENTIAL_LOW",
        "RESIDENTIAL_MEDIUM",
        "RESIDENTIAL_HIGH",
        "COMMERCIAL",
        "INDUSTRIAL",
        "OPEN_SPACE",
    ]
    impervious = ["PAVED", "GRAVEL", "DIRT"]
    water = ["WATER"]

    def print_category(name: str, items: list) -> None:
        print(f"\n{name}:")
        for item in items:
            if item in covers:
                print(f"  {covers[item]:20} ({item})")

    print_category("Agricultural", agricultural)
    print_category("Natural", natural)
    print_category("Developed", developed)
    print_category("Impervious", impervious)
    print_category("Water", water)

    print(f"\n{'─' * 50}")
    print("Note: Some covers require --condition (poor/fair/good)")

    return 0


def _run_range(args: argparse.Namespace) -> int:
    """Show CN range for a land cover type."""
    cover = args.cover.lower()
    ranges = get_cn_range(cover)

    print(f"CN Range for '{cover}'")
    print(f"{'─' * 35}")
    print(f"  {'HSG':<5} {'Min':<6} {'Max':<6}")
    print(f"  {'─' * 20}")

    for hsg in ["A", "B", "C", "D"]:
        if hsg in ranges:
            min_cn, max_cn = ranges[hsg]
            if min_cn == max_cn:
                print(f"  {hsg:<5} {min_cn:<6}")
            else:
                print(f"  {hsg:<5} {min_cn:<6} {max_cn:<6}")

    return 0
