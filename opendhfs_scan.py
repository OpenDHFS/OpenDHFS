#!/usr/bin/env python3
import argparse
from pathlib import Path
from opendhfs.dhav.scanner import scan_image

def main() -> int:
    p = argparse.ArgumentParser(description="OpenDHFS DHAV physical scanner")
    p.add_argument("image", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--chunk-size", type=int, default=64 * 1024 * 1024)
    args = p.parse_args()

    s = scan_image(args.image, args.output, chunk_size=args.chunk_size)
    print("OpenDHFS Scan Complete")
    print("=" * 72)
    print(f"Image:                    {s['image']}")
    print(f"Image size:               {s['image_size']:,} bytes")
    print(f"DHAV candidates:          {s['dhav_candidates']:,}")
    print(f"Parsed records:           {s['parsed_records']:,}")
    print(f"Grades:                   {s['grade_counts']}")
    print(f"Database:                 {s['database']}")
    print("Forensic image access:    Read-only")
    print("Camera/channel assertion: No")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
