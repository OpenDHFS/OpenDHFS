from __future__ import annotations

import sqlite3
from pathlib import Path

from opendhfs.planning.planner import build_recovery_plan


def make_case(case: Path) -> None:
    case.mkdir()

    scan = sqlite3.connect(case / "scan.sqlite")
    scan.execute("""
        CREATE TABLE dhav_records(
            absolute_offset INTEGER PRIMARY KEY,
            frame_type INTEGER,
            declared_size INTEGER,
            packed_datetime TEXT
        )
    """)

    scan.executemany(
        "INSERT INTO dhav_records VALUES(?,?,?,?)",
        [
            (100,   0xFD, 100, "2026-06-30 03:00:00"),
            (200,   0xFC, 100, "2026-06-30 03:00:01"),
            (300,   0xFC, 100, "2026-06-30 03:00:02"),

            (10000, 0xFC, 120, "2026-06-30 03:10:00"),
            (10120, 0xFC, 120, "2026-06-30 03:10:01"),

            (50000, 0xFC, 80,  "2026-06-30 04:00:00"),

            (90000, 0xF0, 100, None),
        ],
    )
    scan.commit()
    scan.close()

    analysis = sqlite3.connect(case / "analysis.sqlite")

    analysis.executescript("""
        CREATE TABLE record_analysis(
            absolute_offset INTEGER PRIMARY KEY,
            temporal_island_id INTEGER,
            physical_set_id INTEGER,
            anchor_class TEXT,
            video_like INTEGER NOT NULL,
            residual_candidate INTEGER,
            reasons TEXT
        );

        CREATE TABLE temporal_islands(
            island_id INTEGER PRIMARY KEY,
            start_datetime TEXT,
            end_datetime TEXT,
            first_offset INTEGER,
            last_offset INTEGER,
            record_count INTEGER,
            strong_anchor_count INTEGER,
            weak_anchor_count INTEGER
        );

        CREATE TABLE physical_sets(
            set_id INTEGER PRIMARY KEY,
            first_offset INTEGER,
            last_offset INTEGER,
            record_count INTEGER,
            strong_anchor_count INTEGER,
            weak_anchor_count INTEGER
        );
    """)

    analysis.executemany(
        "INSERT INTO record_analysis VALUES(?,?,?,?,?,?,?)",
        [
            (100,   1, 1, "STRONG", 1, 0, "TEST"),
            (200,   1, 1, "STRONG", 1, 0, "TEST"),
            (300,   1, 1, "STRONG", 1, 0, "TEST"),

            (10000, 2, 2, "WEAK",   1, 0, "TEST"),
            (10120, 2, 2, "WEAK",   1, 0, "TEST"),

            (50000, 3, 3, "WEAK",   1, 1, "TEST"),

            (90000, None, 4, "NONE", 0, 0, ""),
        ],
    )

    analysis.executemany(
        "INSERT INTO temporal_islands VALUES(?,?,?,?,?,?,?,?)",
        [
            (
                1,
                "2026-06-30 03:00:00",
                "2026-06-30 03:00:02",
                100,
                300,
                3,
                3,
                0,
            ),
            (
                2,
                "2026-06-30 03:10:00",
                "2026-06-30 03:10:01",
                10000,
                10120,
                2,
                0,
                2,
            ),
            (
                3,
                "2026-06-30 04:00:00",
                "2026-06-30 04:00:00",
                50000,
                50000,
                1,
                0,
                1,
            ),
        ],
    )

    analysis.executemany(
        "INSERT INTO physical_sets VALUES(?,?,?,?,?,?)",
        [
            (1, 100,   300,   3, 3, 0),
            (2, 10000, 10120, 2, 0, 2),
            (3, 50000, 50000, 1, 0, 1),
            (4, 90000, 90000, 1, 0, 0),
        ],
    )

    analysis.commit()
    analysis.close()


def test_recovery_plan_contract(tmp_path: Path):
    case = tmp_path / "case"
    make_case(case)

    summary = build_recovery_plan(case)

    assert summary["target_count"] == 3
    assert summary["tier_a"] == 1
    assert summary["tier_b"] == 1
    assert summary["tier_c"] == 1
    assert summary["unresolved_not_scheduled"] == 1

    plan = sqlite3.connect(case / "recovery_plan.sqlite")

    targets = plan.execute("""
        SELECT
            target_id,
            tier,
            strategy,
            start_offset,
            end_offset_exclusive,
            record_count
        FROM recovery_targets
        ORDER BY priority, target_id
    """).fetchall()

    plan.close()

    assert targets == [
        (
            "TGT-000001",
            "TIER_A_ANCHORED",
            "PHYSICAL_CONTINUITY",
            100,
            400,
            3,
        ),
        (
            "TGT-000002",
            "TIER_B_SUPPORTED",
            "PHYSICAL_CONTINUITY",
            10000,
            10240,
            2,
        ),
        (
            "TGT-000003",
            "TIER_C_RESIDUAL",
            "ISOLATED_RECORD",
            50000,
            50080,
            1,
        ),
    ]


def test_plan_does_not_schedule_unresolved(tmp_path: Path):
    case = tmp_path / "case"
    make_case(case)

    build_recovery_plan(case)

    plan = sqlite3.connect(case / "recovery_plan.sqlite")

    count = plan.execute("""
        SELECT COUNT(*)
        FROM recovery_targets
        WHERE start_offset = 90000
    """).fetchone()[0]

    plan.close()

    assert count == 0