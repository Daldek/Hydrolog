"""CLI command for concentration time calculation."""

import argparse

from hydrolog.time import ConcentrationTime


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'tc' command parser."""
    parser = subparsers.add_parser(
        "tc",
        help="Calculate time of concentration",
        description="Calculate watershed time of concentration using various methods.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Methods:
  kirpich   Kirpich formula (small agricultural watersheds)
  nrcs      NRCS equation (uses Curve Number)
  giandotti Giandotti formula (larger watersheds)

Examples:
  hydrolog tc kirpich --length 2.5 --slope 0.02
  hydrolog tc nrcs --length 5.0 --slope 0.01 --cn 72
  hydrolog tc giandotti --area 100 --length 15 --elevation 500
""",
    )

    # Create subparsers for methods
    method_parsers = parser.add_subparsers(
        title="methods",
        dest="method",
        description="Available calculation methods",
        metavar="<method>",
    )

    # Kirpich method
    kirpich = method_parsers.add_parser(
        "kirpich",
        help="Kirpich formula",
        description="Calculate Tc using Kirpich formula for small agricultural watersheds.",
    )
    kirpich.add_argument(
        "-L",
        "--length",
        type=float,
        required=True,
        metavar="KM",
        help="Channel length [km]",
    )
    kirpich.add_argument(
        "-S",
        "--slope",
        type=float,
        required=True,
        metavar="M/M",
        help="Average channel slope [m/m]",
    )
    kirpich.set_defaults(func=_run_kirpich)

    # NRCS method
    nrcs = method_parsers.add_parser(
        "nrcs",
        help="NRCS equation",
        description="Calculate Tc using NRCS equation (requires Curve Number).",
    )
    nrcs.add_argument(
        "-L",
        "--length",
        type=float,
        required=True,
        metavar="KM",
        help="Flow path length [km]",
    )
    nrcs.add_argument(
        "-S",
        "--slope",
        type=float,
        required=True,
        metavar="M/M",
        help="Average watershed slope [m/m]",
    )
    nrcs.add_argument(
        "-CN",
        "--cn",
        type=int,
        required=True,
        metavar="CN",
        help="Curve Number (1-100)",
    )
    nrcs.set_defaults(func=_run_nrcs)

    # Giandotti method
    giandotti = method_parsers.add_parser(
        "giandotti",
        help="Giandotti formula",
        description="Calculate Tc using Giandotti formula for larger watersheds.",
    )
    giandotti.add_argument(
        "-A",
        "--area",
        type=float,
        required=True,
        metavar="KM2",
        help="Watershed area [km²]",
    )
    giandotti.add_argument(
        "-L",
        "--length",
        type=float,
        required=True,
        metavar="KM",
        help="Main channel length [km]",
    )
    giandotti.add_argument(
        "-H",
        "--elevation",
        type=float,
        required=True,
        metavar="M",
        help="Mean elevation above outlet [m]",
    )
    giandotti.set_defaults(func=_run_giandotti)

    parser.set_defaults(func=_show_help, parser=parser)


def _show_help(args: argparse.Namespace) -> int:
    """Show help when no method is specified."""
    args.parser.print_help()
    return 0


def _run_kirpich(args: argparse.Namespace) -> int:
    """Execute Kirpich calculation."""
    tc = ConcentrationTime.kirpich(
        length_km=args.length,
        slope_m_per_m=args.slope,
    )

    print(f"Kirpich Time of Concentration")
    print(f"{'─' * 35}")
    print(f"  Channel length:  {args.length:.2f} km")
    print(f"  Channel slope:   {args.slope:.4f} m/m")
    print(f"{'─' * 35}")
    print(f"  Tc = {tc:.1f} min ({tc/60:.2f} h)")

    return 0


def _run_nrcs(args: argparse.Namespace) -> int:
    """Execute NRCS calculation."""
    tc = ConcentrationTime.nrcs(
        length_km=args.length,
        slope_m_per_m=args.slope,
        cn=args.cn,
    )

    print(f"NRCS Time of Concentration")
    print(f"{'─' * 35}")
    print(f"  Flow path length: {args.length:.2f} km")
    print(f"  Watershed slope:  {args.slope:.4f} m/m")
    print(f"  Curve Number:     {args.cn}")
    print(f"{'─' * 35}")
    print(f"  Tc = {tc:.1f} min ({tc/60:.2f} h)")

    return 0


def _run_giandotti(args: argparse.Namespace) -> int:
    """Execute Giandotti calculation."""
    tc = ConcentrationTime.giandotti(
        area_km2=args.area,
        length_km=args.length,
        elevation_diff_m=args.elevation,
    )

    print(f"Giandotti Time of Concentration")
    print(f"{'─' * 35}")
    print(f"  Watershed area:      {args.area:.2f} km²")
    print(f"  Main channel length: {args.length:.2f} km")
    print(f"  Mean elevation:      {args.elevation:.1f} m")
    print(f"{'─' * 35}")
    print(f"  Tc = {tc:.1f} min ({tc/60:.2f} h)")

    return 0
