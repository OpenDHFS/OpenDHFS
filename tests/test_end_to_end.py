from __future__ import annotations

import sqlite3
import struct
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def packed_datetime(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
) -> int:
    return (
        ((year - 2000) & 0x3F) << 26
        | (month & 0x0F) << 22
        | (day & 0x1F) << 17
        | (hour & 0x1F) << 12
        | (minute & 0x3F) << 6
        | (second & 0x3F)
    )


def make_dhav_record(
    frame_number: int,
    second: int,
) -> bytes:
    payload = (
        b"\x00\x00\x00\x01"
        b"\x26\x01"              # plausible H.265 IDR NAL
        + bytes([frame_number & 0xFF]) * 64
    )

    declared_size = 24 + len(payload) + 8

    header = bytearray(24)
    header[0:4] = b"DHAV"
    header[4] = 0xFD
    header[5] = 0
    header[6] = 17               # deliberately opaque raw channel value
    header[7] = 4

    struct.pack_into("<I", header, 8, frame_number)
    struct.pack_into("<I", header, 12, declared_size)

    dt = packed_datetime(
        2026,
        6,
        30,
        3,
        42,
        second,
    )
    struct.pack_into("<I", header, 16, dt)

    struct.pack_into("<H", header, 20, frame_number & 0xFFFF)

    header[22] = 0
    header[23] = 0

    footer = b"dhav" + struct.pack("<I", declared_size)

    return bytes(header) + payload + footer


def test_scan_to_analyze_end_to_end(tmp_path: Path):
    image = tmp_path / "synthetic.bin"
    case = tmp_path / "case"

    blob = (
        b"\xAA" * 30
        + make_dhav_record(100, 10)
        + b"\xBB" * 19
        + make_dhav_record(101, 11)
        + b"\xCC" * 31
        + make_dhav_record(102, 12)
    )

    image.write_bytes(blob)

    scan_cmd = [
        sys.executable,
        str(ROOT / "opendhfs_scan.py"),
        str(image),
        "--output",
        str(case),
        "--chunk-size",
        "64",
    ]

    scan_result = subprocess.run(
        scan_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert scan_result.returncode == 0, (
        scan_result.stdout + "\n" + scan_result.stderr
    )

    scan_db = case / "scan.sqlite"
    assert scan_db.exists()

    conn = sqlite3.connect(scan_db)
    scan_count = conn.execute(
        "SELECT COUNT(*) FROM dhav_records"
    ).fetchone()[0]
    conn.close()

    assert scan_count == 3

    analyze_cmd = [
        sys.executable,
        str(ROOT / "opendhfs_analyze.py"),
        str(case),
        "--temporal-gap",
        "2",
        "--physical-gap",
        "64",
    ]

    analyze_result = subprocess.run(
        analyze_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert analyze_result.returncode == 0, (
        analyze_result.stdout + "\n" + analyze_result.stderr
    )

    analysis_db = case / "analysis.sqlite"
    summary = case / "analysis_summary.json"

    assert analysis_db.exists()
    assert summary.exists()

    conn = sqlite3.connect(analysis_db)

    analyzed = conn.execute(
        "SELECT COUNT(*) FROM record_analysis"
    ).fetchone()[0]

    temporal_islands = conn.execute(
        "SELECT COUNT(*) FROM temporal_islands"
    ).fetchone()[0]

    physical_sets = conn.execute(
        "SELECT COUNT(*) FROM physical_sets"
    ).fetchone()[0]

    strong = conn.execute(
        """
        SELECT COUNT(*)
        FROM record_analysis
        WHERE anchor_class = 'STRONG'
        """
    ).fetchone()[0]

    residual = conn.execute(
        """
        SELECT COUNT(*)
        FROM record_analysis
        WHERE residual_candidate = 1
        """
    ).fetchone()[0]

    conn.close()

    assert analyzed == 3
    assert temporal_islands == 1
    assert physical_sets == 1
    assert strong == 3
    assert residual == 0

    plan_cmd = [
        sys.executable,
        str(ROOT / "opendhfs_plan.py"),
        str(case),
    ]

    plan_result = subprocess.run(
        plan_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert plan_result.returncode == 0, (
        plan_result.stdout + "\n" + plan_result.stderr
    )

    plan_db = case / "recovery_plan.sqlite"
    plan_json = case / "recovery_plan.json"

    assert plan_db.exists()
    assert plan_json.exists()

    conn = sqlite3.connect(plan_db)

    targets = conn.execute(
        """
        SELECT
            tier,
            strategy,
            start_offset,
            end_offset_exclusive,
            record_count
        FROM recovery_targets
        ORDER BY priority
        """
    ).fetchall()

    conn.close()

    assert targets == [
        (
            "TIER_A_ANCHORED",
            "PHYSICAL_CONTINUITY",
            30,
            len(blob),
            3,
        )
    ]

    recover_cmd = [
        sys.executable,
        str(ROOT / "opendhfs_recover.py"),
        str(case),
        str(image),
    ]

    recover_result = subprocess.run(
        recover_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert recover_result.returncode == 0, (
        recover_result.stdout
        + "\n"
        + recover_result.stderr
    )

    recovery_db = case / "recovery.sqlite"
    recovery_summary = case / "recovery_summary.json"

    assert recovery_db.exists()
    assert recovery_summary.exists()

    candidate = (
        case
        / "recovery"
        / "TGT-000001"
        / "candidate.h265"
    )

    assert candidate.exists()

    recovered = candidate.read_bytes()

    assert recovered.startswith(
        b"\x00\x00\x00\x01"
    )

    assert recovered.count(
        b"\x00\x00\x00\x01"
    ) == 3

    conn = sqlite3.connect(recovery_db)

    result = conn.execute("""
        SELECT
            status,
            payload_records,
            codec,
            source_modified
        FROM recovery_results
        WHERE target_id = 'TGT-000001'
    """).fetchone()

    conn.close()

    assert result == (
        "RECOVERED_PAYLOAD",
        3,
        "H265",
        0,
    )