#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from opendhfs.recovery.recoverer import RecoveryError, recover_targets


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenDHFS evidence-guided payload recovery"
    )

    parser.add_argument(
        "case",
        type=Path,
        help="OpenDHFS case directory containing scan.sqlite and recovery_plan.sqlite",
    )

    parser.add_argument(
        "image",
        type=Path,
        help="source forensic image or authorized binary source",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace existing recovery outputs",
    )

    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()

    try:
        summary = recover_targets(
            args.case,
            args.image,
            overwrite=args.overwrite,
        )
    except RecoveryError as exc:
        print(
            f"OpenDHFS recovery error: {exc}",
            file=sys.stderr,
        )
        return 2

    print("OpenDHFS Recovery Complete")
    print("=" * 48)
    print(f"Targets:                  {summary['target_count']:,}")
    print(f"Recovered payload:        {summary['recovered_payload']:,}")
    print(f"No video payload:         {summary['no_video_payload']:,}")
    print(f"Failures:                 {summary['failed']:,}")
    print(f"Payload bytes:            {summary['payload_bytes']:,}")
    print()
    print("Source access:             Read-only")
    print("Decoder validation:        NO")
    print("Recovery assertion:        NO")
    print("Camera/channel assertion:  NO")
    print()
    print("Recovery database:")
    print(summary["recovery_database"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())