#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from opendhfs.reporting.reporter import ReportingError, build_report


def main() -> int:
    p = argparse.ArgumentParser(
        description="OpenDHFS forensic recovery report generator"
    )
    p.add_argument("case", type=Path)
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()

    try:
        result = build_report(args.case, overwrite=args.overwrite)
    except ReportingError as exc:
        print(f"OpenDHFS reporting error: {exc}", file=sys.stderr)
        return 2

    print("OpenDHFS Report Complete")
    print("=" * 48)
    print(f"Validated video targets:  {result['validated_video_targets']:,}")
    print("Evidence upgrade:          No")
    print("Camera/channel assertion:  No")
    print()
    print("JSON report:")
    print(result["report_json"])
    print()
    print("Markdown report:")
    print(result["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
