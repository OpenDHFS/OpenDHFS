import sqlite3
from pathlib import Path
from unittest.mock import patch

from opendhfs.validation.ffmpeg_adapter import DecodeResult
from opendhfs.validation.ffprobe_adapter import ProbeResult
from opendhfs.validation.runner import validate_recovery


def make_case(tmp_path: Path, with_candidate: bool = True):
    case = tmp_path / "case"
    case.mkdir()

    candidate = case / "candidate.h265"
    candidate_path = None

    if with_candidate:
        candidate.write_bytes(b"\x00\x00\x00\x01\x42\x01" + b"A" * 32)
        candidate_path = str(candidate)

    db = sqlite3.connect(case / "recovery.sqlite")
    db.execute("""
        CREATE TABLE recovery_results(
            target_id TEXT PRIMARY KEY,
            status TEXT,
            tier TEXT,
            strategy TEXT,
            start_offset INTEGER,
            end_offset_exclusive INTEGER,
            planned_records INTEGER,
            records_examined INTEGER,
            payload_records INTEGER,
            payload_bytes INTEGER,
            codec TEXT,
            candidate_path TEXT,
            candidate_sha256 TEXT,
            source_modified INTEGER,
            reason TEXT
        )
    """)
    db.execute(
        "INSERT INTO recovery_results VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "TGT-000001",
            "RECOVERED_PAYLOAD" if with_candidate else "NO_VIDEO_PAYLOAD",
            "TIER_A_ANCHORED",
            "PHYSICAL_CONTINUITY",
            100,
            200,
            1,
            1,
            1 if with_candidate else 0,
            candidate.stat().st_size if with_candidate else 0,
            "H265",
            candidate_path,
            None,
            0,
            "",
        ),
    )
    db.commit()
    db.close()

    return case, candidate


def test_runner_tools_unavailable(tmp_path: Path):
    case, _ = make_case(tmp_path)

    probe = ProbeResult(False, False, None, None, None, None, "ffprobe unavailable")
    decode = DecodeResult(False, False, 0, None, "ffmpeg unavailable")

    with patch(
        "opendhfs.validation.runner.probe_candidate", return_value=probe
    ), patch(
        "opendhfs.validation.runner.decode_candidate", return_value=decode
    ):
        summary = validate_recovery(case)

    assert summary["tools_unavailable"] == 1
    assert summary["video_validated"] == 0

    conn = sqlite3.connect(case / "validation.sqlite")
    row = conn.execute(
        "SELECT tool_status,classification FROM validation_results"
    ).fetchone()
    conn.close()

    assert row == ("TOOLS_UNAVAILABLE", "BITSTREAM_UNRECOGNIZED")


def test_runner_video_validated(tmp_path: Path):
    case, candidate = make_case(tmp_path)

    probe = ProbeResult(True, True, "hevc", 2560, 1440, 0, "")
    decode = DecodeResult(True, True, 120, 0, "frame=120")

    before = candidate.read_bytes()

    with patch(
        "opendhfs.validation.runner.probe_candidate", return_value=probe
    ), patch(
        "opendhfs.validation.runner.decode_candidate", return_value=decode
    ):
        summary = validate_recovery(case)

    assert before == candidate.read_bytes()
    assert summary["video_validated"] == 1

    conn = sqlite3.connect(case / "validation.sqlite")
    row = conn.execute(
        "SELECT classification,width,height,frames_decoded,candidate_modified "
        "FROM validation_results"
    ).fetchone()
    conn.close()

    assert row == ("VIDEO_VALIDATED", 2560, 1440, 120, 0)


def test_runner_partial_decode(tmp_path: Path):
    case, _ = make_case(tmp_path)

    probe = ProbeResult(True, True, "hevc", 1920, 1080, 0, "")
    decode = DecodeResult(True, True, 17, 1, "frame=17")

    with patch(
        "opendhfs.validation.runner.probe_candidate", return_value=probe
    ), patch(
        "opendhfs.validation.runner.decode_candidate", return_value=decode
    ):
        summary = validate_recovery(case)

    assert summary["partial_decode"] == 1


def test_runner_missing_candidate(tmp_path: Path):
    case, _ = make_case(tmp_path, with_candidate=False)

    summary = validate_recovery(case)

    assert summary["candidate_missing"] == 1
    assert summary["video_validated"] == 0
