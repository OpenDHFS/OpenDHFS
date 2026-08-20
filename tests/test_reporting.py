import json
import sqlite3
from pathlib import Path

from opendhfs.reporting.reporter import build_report


def make_case(tmp_path: Path) -> Path:
    case = tmp_path / "case"
    case.mkdir()

    scan = sqlite3.connect(case / "scan.sqlite")
    scan.executescript("""
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE scan_blocks(block_start INTEGER PRIMARY KEY);
        CREATE TABLE dhav_records(absolute_offset INTEGER PRIMARY KEY);
    """)
    scan.executemany(
        "INSERT INTO metadata VALUES(?,?)",
        [
            ("image_path", json.dumps("/evidence/source.001")),
            ("image_size", json.dumps(100000)),
            ("source_fingerprint", json.dumps("abc123")),
            ("source_access", json.dumps("READ_ONLY")),
        ],
    )
    scan.executemany("INSERT INTO scan_blocks VALUES(?)", [(0,), (65536,)])
    scan.executemany(
        "INSERT INTO dhav_records VALUES(?)",
        [(100,), (200,), (300,), (400,)],
    )
    scan.commit()
    scan.close()

    analysis = sqlite3.connect(case / "analysis.sqlite")
    analysis.executescript("""
        CREATE TABLE temporal_islands(island_id INTEGER PRIMARY KEY);
        CREATE TABLE physical_sets(set_id INTEGER PRIMARY KEY);
        CREATE TABLE record_analysis(
            absolute_offset INTEGER PRIMARY KEY,
            anchor_class TEXT,
            residual_candidate INTEGER
        );
    """)
    analysis.executemany("INSERT INTO temporal_islands VALUES(?)", [(1,), (2,)])
    analysis.executemany(
        "INSERT INTO physical_sets VALUES(?)", [(1,), (2,), (3,)]
    )
    analysis.executemany(
        "INSERT INTO record_analysis VALUES(?,?,?)",
        [
            (100, "STRONG", 0),
            (200, "WEAK", 0),
            (300, "WEAK", 1),
            (400, "NONE", 0),
        ],
    )
    analysis.commit()
    analysis.close()

    plan = sqlite3.connect(case / "recovery_plan.sqlite")
    plan.executescript("""
        CREATE TABLE planning_metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE recovery_targets(target_id TEXT PRIMARY KEY, tier TEXT);
    """)
    plan.execute(
        "INSERT INTO planning_metadata VALUES(?,?)",
        ("unresolved_not_scheduled", json.dumps(1)),
    )
    plan.executemany(
        "INSERT INTO recovery_targets VALUES(?,?)",
        [
            ("TGT-000001", "TIER_A_ANCHORED"),
            ("TGT-000002", "TIER_C_RESIDUAL"),
        ],
    )
    plan.commit()
    plan.close()

    recovery = sqlite3.connect(case / "recovery.sqlite")
    recovery.executescript("""
        CREATE TABLE recovery_metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE recovery_results(target_id TEXT PRIMARY KEY, status TEXT);
    """)
    recovery.execute(
        "INSERT INTO recovery_metadata VALUES(?,?)",
        ("payload_bytes", json.dumps(12345)),
    )
    recovery.executemany(
        "INSERT INTO recovery_results VALUES(?,?)",
        [
            ("TGT-000001", "RECOVERED_PAYLOAD"),
            ("TGT-000002", "RECOVERED_PAYLOAD"),
        ],
    )
    recovery.commit()
    recovery.close()

    validation = sqlite3.connect(case / "validation.sqlite")
    validation.executescript("""
        CREATE TABLE validation_metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE validation_results(
            target_id TEXT PRIMARY KEY,
            candidate_path TEXT,
            codec_name TEXT,
            width INTEGER,
            height INTEGER,
            frames_decoded INTEGER,
            candidate_sha256 TEXT,
            classification TEXT
        );
    """)
    validation.executemany(
        "INSERT INTO validation_results VALUES(?,?,?,?,?,?,?,?)",
        [
            (
                "TGT-000001",
                "/case/recovery/TGT-000001/candidate.h265",
                "hevc",
                640,
                360,
                50,
                "sha-good",
                "VIDEO_VALIDATED",
            ),
            (
                "TGT-000002",
                "/case/recovery/TGT-000002/candidate.h265",
                "hevc",
                None,
                None,
                0,
                "sha-bad",
                "DECODER_REJECTED",
            ),
        ],
    )
    validation.commit()
    validation.close()

    return case


def test_report_does_not_upgrade_evidence(tmp_path: Path):
    case = make_case(tmp_path)
    result = build_report(case)

    assert result["validated_video_targets"] == 1
    assert result["evidence_upgrade"] is False
    assert result["camera_channel_assertion"] is False

    report = json.loads((case / "report.json").read_text())

    assert report["validation"]["classification_counts"] == {
        "DECODER_REJECTED": 1,
        "VIDEO_VALIDATED": 1,
    }

    text = (case / "report.md").read_text()
    assert "TGT-000001" in text
    assert "TGT-000002" in text
    assert "DECODER_REJECTED" in text
    assert text.count("Validated video targets: 1") == 1


def test_report_never_asserts_camera_identity(tmp_path: Path):
    case = make_case(tmp_path)
    build_report(case)

    report = json.loads((case / "report.json").read_text())
    assert report["report_policy"]["camera_channel_assertion"] is False
    assert report["source"]["camera_channel_assertion"] is False

    text = (case / "report.md").read_text()
    assert "Camera/channel assertion: No" in text
    assert "Camera 1" not in text
    assert "Camera 2" not in text


def test_report_outputs_are_created(tmp_path: Path):
    case = make_case(tmp_path)
    result = build_report(case)

    assert Path(result["report_json"]).exists()
    assert Path(result["report_markdown"]).exists()
