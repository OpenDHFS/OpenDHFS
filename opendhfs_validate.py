#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from opendhfs.validation.runner import ValidationError, validate_recovery


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenDHFS decoder-based recovery validator"
    )
    parser.add_argument(
        "case",
        type=Path,
        help="OpenDHFS case directory containing recovery.sqlite",
    )
    parser.add_argument("--ffmpeg", type=Path, default=None)
    parser.add_argument("--ffprobe", type=Path, default=None)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing validation.sqlite",
    )
    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()

    try:
        summary = validate_recovery(
            args.case,
            ffmpeg_path=args.ffmpeg,
            ffprobe_path=args.ffprobe,
            overwrite=args.overwrite,
        )
    except ValidationError as exc:
        print(f"OpenDHFS validation error: {exc}", file=sys.stderr)
        return 2

    print("OpenDHFS Validation Complete")
    print("=" * 48)
    print(f"Targets:                  {summary['target_count']:,}")
    print(f"Video validated:          {summary['video_validated']:,}")
    print(f"Partial decode:           {summary['partial_decode']:,}")
    print(f"No decoded frames:        {summary['no_decoded_frames']:,}")
    print(f"Decoder rejected:         {summary['decoder_rejected']:,}")
    print(f"Bitstream unrecognized:   {summary['bitstream_unrecognized']:,}")
    print(f"Missing candidates:       {summary['candidate_missing']:,}")
    print(f"Tools unavailable:        {summary['tools_unavailable']:,}")
    print("Camera/channel assertion: No")
    print()
    print("Validation database:")
    print(summary["validation_database"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
