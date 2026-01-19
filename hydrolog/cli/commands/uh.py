"""CLI command for unit hydrograph generation."""

import argparse
import sys

from hydrolog.runoff import ClarkIUH, NashIUH, SCSUnitHydrograph, SnyderUH


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'uh' command parser."""
    parser = subparsers.add_parser(
        "uh",
        help="Generate unit hydrograph",
        description="Generate unit hydrograph using various methods.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Methods:
  scs     SCS dimensionless unit hydrograph
  nash    Nash cascade of linear reservoirs
  clark   Clark IUH (translation + linear reservoir)
  snyder  Snyder synthetic unit hydrograph

Examples:
  hydrolog uh scs --area 45 --tc 90 --timestep 5
  hydrolog uh nash --area 45 --n 3 --k 30 --timestep 5
  hydrolog uh clark --area 45 --tc 60 --r 30 --timestep 5
  hydrolog uh snyder --area 100 --L 15 --Lc 8 --timestep 30

Output options:
  --csv    Output as CSV (time, discharge)
  --json   Output as JSON
""",
    )

    # Create subparsers for methods
    method_parsers = parser.add_subparsers(
        title="methods",
        dest="method",
        description="Available unit hydrograph methods",
        metavar="<method>",
    )

    # Common arguments function
    def add_common_args(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "-A",
            "--area",
            type=float,
            required=True,
            metavar="KM2",
            help="Watershed area [km²]",
        )
        p.add_argument(
            "-dt",
            "--timestep",
            type=float,
            default=5.0,
            metavar="MIN",
            help="Time step [min] (default: 5)",
        )
        p.add_argument(
            "-D",
            "--duration",
            type=float,
            default=None,
            metavar="MIN",
            help="Rainfall duration [min] (default: auto)",
        )
        p.add_argument(
            "--csv",
            action="store_true",
            help="Output as CSV format",
        )
        p.add_argument(
            "--json",
            action="store_true",
            help="Output as JSON format",
        )

    # SCS method
    scs = method_parsers.add_parser(
        "scs",
        help="SCS dimensionless UH",
        description="Generate SCS (NRCS) dimensionless unit hydrograph.",
    )
    add_common_args(scs)
    scs.add_argument(
        "-Tc",
        "--tc",
        type=float,
        required=True,
        metavar="MIN",
        help="Time of concentration [min]",
    )
    scs.set_defaults(func=_run_scs)

    # Nash method
    nash = method_parsers.add_parser(
        "nash",
        help="Nash cascade IUH",
        description="Generate Nash cascade unit hydrograph.",
    )
    add_common_args(nash)
    nash.add_argument(
        "-n",
        "--n",
        type=float,
        required=True,
        metavar="N",
        help="Number of reservoirs (shape parameter)",
    )
    nash.add_argument(
        "-k",
        "--k",
        type=float,
        required=True,
        metavar="MIN",
        help="Storage constant K [min]",
    )
    nash.set_defaults(func=_run_nash)

    # Clark method
    clark = method_parsers.add_parser(
        "clark",
        help="Clark IUH",
        description="Generate Clark IUH (translation + linear reservoir).",
    )
    add_common_args(clark)
    clark.add_argument(
        "-Tc",
        "--tc",
        type=float,
        required=True,
        metavar="MIN",
        help="Time of concentration [min]",
    )
    clark.add_argument(
        "-R",
        "--r",
        type=float,
        required=True,
        metavar="MIN",
        help="Storage coefficient R [min]",
    )
    clark.set_defaults(func=_run_clark)

    # Snyder method
    snyder = method_parsers.add_parser(
        "snyder",
        help="Snyder synthetic UH",
        description="Generate Snyder synthetic unit hydrograph.",
    )
    add_common_args(snyder)
    snyder.add_argument(
        "-L",
        "--L",
        type=float,
        required=True,
        metavar="KM",
        help="Main stream length [km]",
    )
    snyder.add_argument(
        "-Lc",
        "--Lc",
        type=float,
        required=True,
        metavar="KM",
        help="Length to centroid [km]",
    )
    snyder.add_argument(
        "--ct",
        type=float,
        default=2.0,
        metavar="CT",
        help="Time coefficient Ct (default: 2.0)",
    )
    snyder.add_argument(
        "--cp",
        type=float,
        default=0.6,
        metavar="CP",
        help="Peak coefficient Cp (default: 0.6)",
    )
    snyder.set_defaults(func=_run_snyder)

    parser.set_defaults(func=_show_help, parser=parser)


def _show_help(args: argparse.Namespace) -> int:
    """Show help when no method is specified."""
    args.parser.print_help()
    return 0


def _format_output(
    times: list,
    ordinates: list,
    method: str,
    params: dict,
    csv: bool = False,
    json_out: bool = False,
) -> str:
    """Format output based on requested format."""
    import json

    if json_out:
        output = {
            "method": method,
            "parameters": params,
            "hydrograph": {
                "times_min": times,
                "ordinates_m3s_per_mm": ordinates,
            },
        }
        return json.dumps(output, indent=2)

    if csv:
        lines = ["time_min,discharge_m3s_per_mm"]
        for t, q in zip(times, ordinates):
            lines.append(f"{t:.1f},{q:.4f}")
        return "\n".join(lines)

    # Default: table format
    lines = [
        f"Unit Hydrograph ({method})",
        "─" * 40,
    ]
    for key, value in params.items():
        if isinstance(value, float):
            lines.append(f"  {key}: {value:.2f}")
        else:
            lines.append(f"  {key}: {value}")
    lines.append("─" * 40)
    lines.append(f"  {'Time [min]':<12} {'Q [m³/s/mm]':<12}")
    lines.append(f"  {'─' * 26}")

    # Show first 10, peak area, and last 5
    peak_idx = ordinates.index(max(ordinates))
    n = len(times)

    # Determine which indices to show
    show_indices = set()
    # First 5
    for i in range(min(5, n)):
        show_indices.add(i)
    # Around peak
    for i in range(max(0, peak_idx - 2), min(n, peak_idx + 3)):
        show_indices.add(i)
    # Last 3
    for i in range(max(0, n - 3), n):
        show_indices.add(i)

    show_indices = sorted(show_indices)
    prev_i = -1
    for i in show_indices:
        if prev_i >= 0 and i > prev_i + 1:
            lines.append("  ...")
        marker = " *" if i == peak_idx else ""
        lines.append(f"  {times[i]:<12.1f} {ordinates[i]:<12.4f}{marker}")
        prev_i = i

    lines.append("─" * 40)
    lines.append(f"  Peak: {max(ordinates):.4f} m³/s/mm at {times[peak_idx]:.1f} min")
    lines.append(f"  (* marks peak)")

    return "\n".join(lines)


def _run_scs(args: argparse.Namespace) -> int:
    """Execute SCS unit hydrograph generation."""
    uh = SCSUnitHydrograph(area_km2=args.area, tc_min=args.tc)
    result = uh.generate(timestep_min=args.timestep)

    params = {
        "Area [km²]": args.area,
        "Tc [min]": args.tc,
        "Timestep [min]": args.timestep,
        "Time to peak [min]": result.time_to_peak_min,
        "Peak discharge [m³/s/mm]": result.peak_discharge_m3s,
    }

    output = _format_output(
        times=result.times_min.tolist(),
        ordinates=result.ordinates_m3s.tolist(),
        method="SCS",
        params=params,
        csv=args.csv,
        json_out=args.json,
    )
    print(output)
    return 0


def _run_nash(args: argparse.Namespace) -> int:
    """Execute Nash unit hydrograph generation."""
    iuh = NashIUH(n=args.n, k_min=args.k)

    duration = args.duration if args.duration else args.timestep
    result = iuh.to_unit_hydrograph(
        area_km2=args.area,
        duration_min=duration,
        timestep_min=args.timestep,
    )

    params = {
        "Area [km²]": args.area,
        "n": args.n,
        "K [min]": args.k,
        "Duration [min]": duration,
        "Timestep [min]": args.timestep,
        "Lag time [min]": iuh.lag_time_min,
        "Time to peak [min]": result.time_to_peak_min,
        "Peak discharge [m³/s/mm]": result.peak_discharge_m3s,
    }

    output = _format_output(
        times=result.times_min.tolist(),
        ordinates=result.ordinates_m3s.tolist(),
        method="Nash",
        params=params,
        csv=args.csv,
        json_out=args.json,
    )
    print(output)
    return 0


def _run_clark(args: argparse.Namespace) -> int:
    """Execute Clark unit hydrograph generation."""
    iuh = ClarkIUH(tc_min=args.tc, r_min=args.r)

    duration = args.duration if args.duration else args.timestep
    result = iuh.to_unit_hydrograph(
        area_km2=args.area,
        duration_min=duration,
        timestep_min=args.timestep,
    )

    params = {
        "Area [km²]": args.area,
        "Tc [min]": args.tc,
        "R [min]": args.r,
        "Duration [min]": duration,
        "Timestep [min]": args.timestep,
        "Approx. lag [min]": iuh.lag_time_min,
        "Time to peak [min]": result.time_to_peak_min,
        "Peak discharge [m³/s/mm]": result.peak_discharge_m3s,
    }

    output = _format_output(
        times=result.times_min.tolist(),
        ordinates=result.ordinates_m3s.tolist(),
        method="Clark",
        params=params,
        csv=args.csv,
        json_out=args.json,
    )
    print(output)
    return 0


def _run_snyder(args: argparse.Namespace) -> int:
    """Execute Snyder unit hydrograph generation."""
    uh = SnyderUH(
        area_km2=args.area,
        L_km=args.L,
        Lc_km=args.Lc,
        ct=args.ct,
        cp=args.cp,
    )

    duration = args.duration if args.duration else uh.standard_duration_min
    result = uh.generate(
        timestep_min=args.timestep,
        duration_min=duration,
    )

    params = {
        "Area [km²]": args.area,
        "L [km]": args.L,
        "Lc [km]": args.Lc,
        "Ct": args.ct,
        "Cp": args.cp,
        "Duration [min]": duration,
        "Timestep [min]": args.timestep,
        "Lag time [min]": result.lag_time_min,
        "Time to peak [min]": result.time_to_peak_min,
        "Peak discharge [m³/s/mm]": result.peak_discharge_m3s,
    }

    output = _format_output(
        times=result.times_min.tolist(),
        ordinates=result.ordinates_m3s.tolist(),
        method="Snyder",
        params=params,
        csv=args.csv,
        json_out=args.json,
    )
    print(output)
    return 0
