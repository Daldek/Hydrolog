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
  kirpich        Kirpich formula (small agricultural watersheds)
  nrcs           NRCS equation (uses Curve Number)
  giandotti      Giandotti formula (larger watersheds)
  faa            FAA method (airport/overland flow)
  kerby          Kerby formula (shallow overland flow)
  kerby-kirpich  Kerby-Kirpich composite (overland + channel)

Examples:
  hydrolog tc kirpich --length 2.5 --slope 0.02
  hydrolog tc nrcs --length 5.0 --slope 0.01 --cn 72
  hydrolog tc giandotti --area 100 --length 15 --elevation 500
  hydrolog tc faa --length 0.15 --slope 0.02 --runoff-coeff 0.6
  hydrolog tc kerby --length 0.1 --slope 0.008 --retardance 0.40
  hydrolog tc kerby-kirpich --ov-length 0.25 --ov-slope 0.008 --retardance 0.40 --ch-length 5.0 --ch-slope 0.005
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

    # FAA method
    faa = method_parsers.add_parser(
        "faa",
        help="FAA method",
        description="Calculate Tc using FAA method for overland flow.",
    )
    faa.add_argument(
        "-L",
        "--length",
        type=float,
        required=True,
        metavar="KM",
        help="Overland flow length [km]",
    )
    faa.add_argument(
        "-S",
        "--slope",
        type=float,
        required=True,
        metavar="M/M",
        help="Average overland slope [m/m]",
    )
    faa.add_argument(
        "-C",
        "--runoff-coeff",
        type=float,
        required=True,
        metavar="C",
        help="Rational method runoff coefficient (0-1)",
    )
    faa.set_defaults(func=_run_faa)

    # Kerby method
    kerby = method_parsers.add_parser(
        "kerby",
        help="Kerby formula",
        description="Calculate Tc using Kerby formula for shallow overland flow.",
    )
    kerby.add_argument(
        "-L",
        "--length",
        type=float,
        required=True,
        metavar="KM",
        help="Overland flow length [km]",
    )
    kerby.add_argument(
        "-S",
        "--slope",
        type=float,
        required=True,
        metavar="M/M",
        help="Average overland slope [m/m]",
    )
    kerby.add_argument(
        "-N",
        "--retardance",
        type=float,
        required=True,
        metavar="N",
        help="Kerby retardance roughness coefficient (0.02-0.80)",
    )
    kerby.set_defaults(func=_run_kerby)

    # Kerby-Kirpich composite method
    kerby_kirpich = method_parsers.add_parser(
        "kerby-kirpich",
        help="Kerby-Kirpich composite method",
        description=(
            "Calculate Tc using Kerby-Kirpich composite method "
            "(overland + channel flow)."
        ),
    )
    kerby_kirpich.add_argument(
        "-OL",
        "--ov-length",
        type=float,
        required=True,
        metavar="KM",
        help="Overland flow length [km]",
    )
    kerby_kirpich.add_argument(
        "-OS",
        "--ov-slope",
        type=float,
        required=True,
        metavar="M/M",
        help="Overland slope [m/m]",
    )
    kerby_kirpich.add_argument(
        "-N",
        "--retardance",
        type=float,
        required=True,
        metavar="N",
        help="Kerby retardance roughness coefficient (0.02-0.80)",
    )
    kerby_kirpich.add_argument(
        "-CL",
        "--ch-length",
        type=float,
        required=True,
        metavar="KM",
        help="Channel length [km]",
    )
    kerby_kirpich.add_argument(
        "-CS",
        "--ch-slope",
        type=float,
        required=True,
        metavar="M/M",
        help="Channel slope [m/m]",
    )
    kerby_kirpich.set_defaults(func=_run_kerby_kirpich)

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

    print("Kirpich Time of Concentration")
    print("─" * 35)
    print(f"  Channel length:  {args.length:.2f} km")
    print(f"  Channel slope:   {args.slope:.4f} m/m")
    print("─" * 35)
    print(f"  Tc = {tc:.1f} min ({tc / 60:.2f} h)")

    return 0


def _run_nrcs(args: argparse.Namespace) -> int:
    """Execute NRCS calculation."""
    tc = ConcentrationTime.nrcs(
        length_km=args.length,
        slope_m_per_m=args.slope,
        cn=args.cn,
    )

    print("NRCS Time of Concentration")
    print("─" * 35)
    print(f"  Flow path length: {args.length:.2f} km")
    print(f"  Watershed slope:  {args.slope:.4f} m/m")
    print(f"  Curve Number:     {args.cn}")
    print("─" * 35)
    print(f"  Tc = {tc:.1f} min ({tc / 60:.2f} h)")

    return 0


def _run_giandotti(args: argparse.Namespace) -> int:
    """Execute Giandotti calculation."""
    tc = ConcentrationTime.giandotti(
        area_km2=args.area,
        length_km=args.length,
        elevation_diff_m=args.elevation,
    )

    print("Giandotti Time of Concentration")
    print("─" * 35)
    print(f"  Watershed area:      {args.area:.2f} km²")
    print(f"  Main channel length: {args.length:.2f} km")
    print(f"  Mean elevation:      {args.elevation:.1f} m")
    print("─" * 35)
    print(f"  Tc = {tc:.1f} min ({tc / 60:.2f} h)")

    return 0


def _run_faa(args: argparse.Namespace) -> int:
    """Execute FAA calculation."""
    tc = ConcentrationTime.faa(
        length_km=args.length,
        slope_m_per_m=args.slope,
        runoff_coeff=args.runoff_coeff,
    )

    print("FAA Time of Concentration")
    print("─" * 35)
    print(f"  Overland flow length: {args.length:.2f} km")
    print(f"  Overland slope:       {args.slope:.4f} m/m")
    print(f"  Runoff coefficient:   {args.runoff_coeff:.2f}")
    print("─" * 35)
    print(f"  Tc = {tc:.1f} min ({tc / 60:.2f} h)")

    return 0


def _run_kerby(args: argparse.Namespace) -> int:
    """Execute Kerby calculation."""
    tc = ConcentrationTime.kerby(
        length_km=args.length,
        slope_m_per_m=args.slope,
        retardance=args.retardance,
    )

    print("Kerby Time of Concentration")
    print("─" * 35)
    print(f"  Overland flow length: {args.length:.2f} km")
    print(f"  Overland slope:       {args.slope:.4f} m/m")
    print(f"  Retardance (N):       {args.retardance:.2f}")
    print("─" * 35)
    print(f"  Tc = {tc:.1f} min ({tc / 60:.2f} h)")

    return 0


def _run_kerby_kirpich(args: argparse.Namespace) -> int:
    """Execute Kerby-Kirpich composite calculation."""
    # Compute individual components for display
    t_overland = ConcentrationTime.kerby(
        length_km=args.ov_length,
        slope_m_per_m=args.ov_slope,
        retardance=args.retardance,
    )

    tc = ConcentrationTime.kerby_kirpich(
        overland_length_km=args.ov_length,
        overland_slope_m_per_m=args.ov_slope,
        retardance=args.retardance,
        channel_length_km=args.ch_length,
        channel_slope_m_per_m=args.ch_slope,
    )

    t_channel = tc - t_overland

    print("Kerby-Kirpich Time of Concentration")
    print("─" * 35)
    print("  Overland flow:")
    print(f"    Length:      {args.ov_length:.2f} km")
    print(f"    Slope:       {args.ov_slope:.4f} m/m")
    print(f"    Retardance:  {args.retardance:.2f}")
    print(f"    t_overland = {t_overland:.1f} min")
    print("  Channel flow:")
    print(f"    Length:      {args.ch_length:.2f} km")
    print(f"    Slope:       {args.ch_slope:.4f} m/m")
    print(f"    t_channel  = {t_channel:.1f} min")
    print("─" * 35)
    print(f"  Tc = {tc:.1f} min ({tc / 60:.2f} h)")

    return 0
