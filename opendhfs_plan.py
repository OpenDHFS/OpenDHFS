#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from opendhfs.planning.planner import PlanningError, build_recovery_plan


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenDHFS evidence-guided recovery planner"
    )

    parser.add_argument(
        "case",
        type=Path,
        help="OpenDHFS case directory containing scan.sqlite and analysis.sqlite",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing recovery plan",
    )

    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()

    try:
        summary = build_recovery_plan(
            args.case,
            overwrite=args.overwrite,
        )
    except PlanningError as exc:
        print(f"OpenDHFS planning error: {exc}", file=sys.stderr)
        return 2

    print("OpenDHFS Recovery Plan")
    print("=" * 48)
    print(f"Targets:                  {summary['target_count']:,}")
    print(f"Tier A — anchored:        {summary['tier_a']:,}")
    print(f"Tier B — supported:       {summary['tier_b']:,}")
    print(f"Tier C — residual:        {summary['tier_c']:,}")
    print(
        "Unresolved / unscheduled: "
        f"{summary['unresolved_not_scheduled']:,}"
    )
    print()
    print("Recovery assertion:       NO")
    print("Camera-channel assertion: NO")
    print()
    print("Plan database:")
    print(summary["plan_database"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())