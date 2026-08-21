from __future__ import annotations

import sys
from collections.abc import Callable

from opendhfs import __version__

import opendhfs_analyze
import opendhfs_plan
import opendhfs_recover
import opendhfs_report
import opendhfs_scan
import opendhfs_validate


COMMANDS: dict[str, tuple[str, Callable[[], int]]] = {
    "scan": (
        "scan a forensic image for DHAV records",
        opendhfs_scan.main,
    ),
    "analyze": (
        "analyze structural and temporal DHAV evidence",
        opendhfs_analyze.main,
    ),
    "plan": (
        "build an evidence-guided recovery plan",
        opendhfs_plan.main,
    ),
    "recover": (
        "recover payloads from planned targets",
        opendhfs_recover.main,
    ),
    "validate": (
        "validate recovered candidates with decoders",
        opendhfs_validate.main,
    ),
    "report": (
        "generate a faithful forensic recovery report",
        opendhfs_report.main,
    ),
}


def _print_help() -> None:
    print(
        f"""OpenDHFS {__version__}

Forensic recovery toolkit for DHFS/DHAV evidence.

Usage:
  opendhfs <command> [options]
  opendhfs --version
  opendhfs --help

Commands:
  scan       Scan a forensic image for DHAV records
  analyze    Analyze structural and temporal DHAV evidence
  plan       Build an evidence-guided recovery plan
  recover    Recover payloads from planned targets
  validate   Validate recovered candidates with decoders
  report     Generate a faithful forensic recovery report

Run:
  opendhfs <command> --help

for command-specific options.
"""
    )


def main() -> int:
    args = sys.argv[1:]

    if not args or args[0] in {"-h", "--help"}:
        _print_help()
        return 0

    if args[0] in {"-V", "--version"}:
        print(f"OpenDHFS {__version__}")
        return 0

    command = args[0]

    if command not in COMMANDS:
        print(
            f"opendhfs: unknown command: {command}",
            file=sys.stderr,
        )
        print(
            "Run 'opendhfs --help' for available commands.",
            file=sys.stderr,
        )
        return 2

    _, command_main = COMMANDS[command]

    # Existing command main() functions parse sys.argv directly.
    # Remove the unified command name before dispatching.
    sys.argv = [
        f"opendhfs {command}",
        *args[1:],
    ]

    return command_main()


if __name__ == "__main__":
    raise SystemExit(main())