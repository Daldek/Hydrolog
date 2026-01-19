"""CLI command for SCS-CN runoff calculation."""

import argparse

from hydrolog.runoff import AMC, SCSCN


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'scs' command parser."""
    parser = subparsers.add_parser(
        "scs",
        help="SCS-CN runoff calculation",
        description="Calculate effective precipitation using SCS Curve Number method.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
AMC (Antecedent Moisture Condition):
  I   - Dry conditions (lowest runoff potential)
  II  - Normal/average conditions (default)
  III - Wet conditions (highest runoff potential)

Examples:
  hydrolog scs --cn 72 --precipitation 50
  hydrolog scs --cn 80 --precipitation 75 --amc III
  hydrolog scs --cn 65 --precipitation 100 --ia 0.1
""",
    )

    parser.add_argument(
        "-CN",
        "--cn",
        type=int,
        required=True,
        metavar="CN",
        help="Curve Number for AMC-II (1-100)",
    )
    parser.add_argument(
        "-P",
        "--precipitation",
        type=float,
        required=True,
        metavar="MM",
        help="Total precipitation [mm]",
    )
    parser.add_argument(
        "--amc",
        type=str,
        choices=["I", "II", "III", "1", "2", "3"],
        default="II",
        metavar="AMC",
        help="Antecedent Moisture Condition (I, II, III) - default: II",
    )
    parser.add_argument(
        "--ia",
        type=float,
        default=0.2,
        metavar="COEF",
        help="Initial abstraction coefficient (default: 0.2)",
    )

    parser.set_defaults(func=_run_scs)


def _run_scs(args: argparse.Namespace) -> int:
    """Execute SCS-CN calculation."""
    # Parse AMC
    amc_map = {
        "I": AMC.I,
        "1": AMC.I,
        "II": AMC.II,
        "2": AMC.II,
        "III": AMC.III,
        "3": AMC.III,
    }
    amc = amc_map[args.amc]

    # Create calculator and compute
    scs = SCSCN(cn=args.cn, ia_coefficient=args.ia)
    result = scs.effective_precipitation(
        precipitation_mm=args.precipitation,
        amc=amc,
    )

    # Calculate runoff coefficient
    c = result.total_effective_mm / args.precipitation if args.precipitation > 0 else 0

    print(f"SCS-CN Runoff Calculation")
    print(f"{'─' * 40}")
    print(f"  Input:")
    print(f"    Precipitation (P):     {args.precipitation:.2f} mm")
    print(f"    Curve Number (CN-II):  {args.cn}")
    print(f"    AMC:                   {amc.name} ({amc.value})")
    print(f"    Ia coefficient:        {args.ia}")
    print(f"{'─' * 40}")
    print(f"  Results:")
    print(f"    Adjusted CN:           {result.cn_adjusted}")
    print(f"    Max retention (S):     {result.retention_mm:.2f} mm")
    print(f"    Initial abstraction:   {result.initial_abstraction_mm:.2f} mm")
    print(f"    Effective precip (Pe): {result.total_effective_mm:.2f} mm")
    print(f"    Runoff coefficient:    {c:.3f}")
    print(f"{'─' * 40}")

    # Summary
    if args.precipitation > result.initial_abstraction_mm:
        print(f"\n  P > Ia: Runoff occurs")
    else:
        print(f"\n  P <= Ia: No runoff (all precipitation abstracted)")

    return 0
