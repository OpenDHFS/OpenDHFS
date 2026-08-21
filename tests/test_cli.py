from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "opendhfs.cli",
            *args,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_cli_version():
    result = run_cli("--version")

    assert result.returncode == 0
    assert "OpenDHFS 0.1.0" in result.stdout


def test_cli_help_lists_pipeline():
    result = run_cli("--help")

    assert result.returncode == 0

    for command in (
        "scan",
        "analyze",
        "plan",
        "recover",
        "validate",
        "report",
    ):
        assert command in result.stdout


def test_cli_unknown_command_is_rejected():
    result = run_cli("compile-in-hebrew")

    assert result.returncode == 2
    assert "unknown command" in result.stderr


def test_cli_dispatches_scan_help():
    result = run_cli("scan", "--help")

    assert result.returncode == 0
    assert "DHAV physical scanner" in result.stdout


def test_cli_dispatches_report_help():
    result = run_cli("report", "--help")

    assert result.returncode == 0
    assert "forensic recovery report generator" in result.stdout