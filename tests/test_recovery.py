from __future__ import annotations

import sqlite3
import struct
from pathlib import Path

from opendhfs.recovery.recoverer import recover_targets


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


def make_record(
    frame_number: int,
    second: int,
    payload: bytes,
) -> bytes:
    header = bytearray(24)

    header[:4] = b"DHAV"
    header[4] = 0xFD
    header[5] = 0
    header[6] = 17
    header[7] = 4

    struct.pack_into(
        "<I",
        header,
        8,
        frame_number,
    )

    struct.pack_into(
        "<I",
        header,
        16,
        packed_datetime(
            2026,
            6,
            30,
            3,
            42,
            second,
        ),
    )

    header[20] = 0x34
    header[21] = 0x12
    header[22] = 0
    header[23] = 0

    declared_size = (
        24
        + len(payload)
        + 8
    )

    struct.pack_into(
        "<I",
        header,
        12,
        declared_size,
    )

    footer = (
        b"dhav"
        + struct.pack(
            "<I",
            declared_size,
        )
    )

    return (
        bytes(header)
        + payload
        + footer
    )


def make_case(
    root: Path,
) -> tuple[Path, Path]:
    case = root / "case"
    case.mkdir()

    payload_1 = (
        b"\x00\x00\x00\x01"
        b"\x42\x01"
        + b"\xAA" * 32
    )

    payload_2 = (
        b"\x00\x00\x00\x01"
        b"\x26\x01"
        + b"\xBB" * 32
    )

    record_1 = make_record(
        100,
        10,
        payload_1,
    )

    record_2 = make_record(
        101,
        11,
        payload_2,
    )

    prefix = b"X" * 30
    middle = b"Y" * 17

    offset_1 = len(prefix)

    offset_2 = (
        offset_1
        + len(record_1)
        + len(middle)
    )

    image = (
        prefix
        + record_1
        + middle
        + record_2
        + b"END"
    )

    image_path = root / "synthetic.bin"
    image_path.write_bytes(image)

    scan = sqlite3.connect(
        case / "scan.sqlite"
    )

    scan.execute("""
        CREATE TABLE dhav_records(
            absolute_offset INTEGER PRIMARY KEY,
            frame_type INTEGER,
            declared_size INTEGER,
            codec_guess TEXT
        )
    """)

    scan.executemany(
        """
        INSERT INTO dhav_records
        VALUES(?,?,?,?)
        """,
        [
            (
                offset_1,
                0xFD,
                len(record_1),
                "H265",
            ),
            (
                offset_2,
                0xFD,
                len(record_2),
                "H265",
            ),
        ],
    )

    scan.commit()
    scan.close()

    plan = sqlite3.connect(
        case / "recovery_plan.sqlite"
    )

    plan.execute("""
        CREATE TABLE recovery_targets(
            target_id TEXT PRIMARY KEY,
            priority INTEGER,
            tier TEXT,
            strategy TEXT,
            start_offset INTEGER,
            end_offset_exclusive INTEGER,
            temporal_start TEXT,
            temporal_end TEXT,
            record_count INTEGER,
            strong_anchors INTEGER,
            weak_anchors INTEGER,
            reason TEXT
        )
    """)

    plan.execute(
        """
        INSERT INTO recovery_targets
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "TGT-000001",
            1,
            "TIER_A_ANCHORED",
            "PHYSICAL_CONTINUITY",
            offset_1,
            offset_2 + len(record_2),
            "2026-06-30 03:42:10",
            "2026-06-30 03:42:11",
            2,
            2,
            0,
            "TEST",
        ),
    )

    plan.commit()
    plan.close()

    return case, image_path


def test_recovery_contract(
    tmp_path: Path,
):
    case, image = make_case(
        tmp_path
    )

    summary = recover_targets(
        case,
        image,
    )

    assert summary["target_count"] == 1
    assert summary["recovered_payload"] == 1
    assert summary["failed"] == 0

    candidate = (
        case
        / "recovery"
        / "TGT-000001"
        / "candidate.h265"
    )

    assert candidate.exists()

    data = candidate.read_bytes()

    assert data.startswith(
        b"\x00\x00\x00\x01"
    )

    assert data.count(
        b"\x00\x00\x00\x01"
    ) == 2


def test_recovery_preserves_source_order(
    tmp_path: Path,
):
    case, image = make_case(
        tmp_path
    )

    recover_targets(
        case,
        image,
    )

    candidate = (
        case
        / "recovery"
        / "TGT-000001"
        / "candidate.h265"
    ).read_bytes()

    first = candidate.find(
        b"\xAA" * 8
    )

    second = candidate.find(
        b"\xBB" * 8
    )

    assert first >= 0
    assert second > first


def test_recovery_does_not_modify_source(
    tmp_path: Path,
):
    case, image = make_case(
        tmp_path
    )

    before = image.read_bytes()

    recover_targets(
        case,
        image,
    )

    after = image.read_bytes()

    assert before == after