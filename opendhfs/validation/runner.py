from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .ffmpeg_adapter import DecodeResult, decode_candidate
from .ffprobe_adapter import ProbeResult, probe_candidate
from .validator import classify_validation


class ValidationError(RuntimeError):
    pass


VALIDATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS validation_results(
    target_id TEXT PRIMARY KEY,
    candidate_path TEXT,
    candidate_exists INTEGER NOT NULL,
    tool_status TEXT NOT NULL,
    bitstream_recognized INTEGER NOT NULL,
    codec_name TEXT,
    width INTEGER,
    height INTEGER,
    decoder_opened INTEGER NOT NULL,
    frames_decoded INTEGER NOT NULL,
    decoder_exit_code INTEGER,
    classification TEXT NOT NULL,
    candidate_sha256 TEXT,
    candidate_modified INTEGER NOT NULL,
    ffprobe_stderr TEXT NOT NULL,
    ffmpeg_stderr TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_metadata(
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _connect_ro(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise ValidationError(f"required database not found: {path}")
    return sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)


def _candidate_state(path: Path) -> tuple[int | None, int | None, str | None]:
    if not path.exists():
        return None, None, None
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, _sha256_file(path)


def validate_recovery(
    case_dir: Path,
    *,
    ffmpeg_path: Path | None = None,
    ffprobe_path: Path | None = None,
    overwrite: bool = False,
) -> dict:
    case_dir = Path(case_dir).resolve()
    recovery_db_path = case_dir / "recovery.sqlite"
    validation_db_path = case_dir / "validation.sqlite"
    summary_path = case_dir / "validation_summary.json"

    if validation_db_path.exists():
        if not overwrite:
            raise ValidationError(
                "validation.sqlite already exists; use overwrite=True"
            )
        validation_db_path.unlink()

    recovery = _connect_ro(recovery_db_path)
    validation = sqlite3.connect(validation_db_path)
    validation.executescript(VALIDATION_SCHEMA)

    rows = recovery.execute(
        """
        SELECT target_id, candidate_path
        FROM recovery_results
        ORDER BY target_id
        """
    ).fetchall()

    counts = {
        "VIDEO_VALIDATED": 0,
        "PARTIAL_DECODE": 0,
        "NO_DECODED_FRAMES": 0,
        "DECODER_REJECTED": 0,
        "BITSTREAM_UNRECOGNIZED": 0,
        "EMPTY_OR_MISSING": 0,
        "TOOLS_UNAVAILABLE": 0,
        "CANDIDATE_MISSING": 0,
    }

    manifests = []

    for target_id, candidate_path_text in rows:
        candidate = Path(candidate_path_text) if candidate_path_text else None

        if candidate is None or not candidate.exists():
            tool_status = "CANDIDATE_MISSING"
            classification = "EMPTY_OR_MISSING"
            probe = ProbeResult(
                tool_available=False,
                bitstream_recognized=False,
                codec_name=None,
                width=None,
                height=None,
                exit_code=None,
                stderr="candidate missing",
            )
            decode = DecodeResult(
                tool_available=False,
                decoder_opened=False,
                frames_decoded=0,
                exit_code=None,
                stderr="candidate missing",
            )
            candidate_sha256 = None
            candidate_modified = False
            counts["CANDIDATE_MISSING"] += 1
        else:
            before_size, before_mtime, before_sha = _candidate_state(candidate)

            probe = probe_candidate(candidate, ffprobe_path=ffprobe_path)
            decode = decode_candidate(candidate, ffmpeg_path=ffmpeg_path)

            after_size, after_mtime, after_sha = _candidate_state(candidate)

            candidate_modified = (
                before_size != after_size
                or before_mtime != after_mtime
                or before_sha != after_sha
            )

            if candidate_modified:
                recovery.close()
                validation.close()
                raise ValidationError(
                    f"candidate modified during validation: {candidate}"
                )

            candidate_sha256 = after_sha

            if not probe.tool_available or not decode.tool_available:
                tool_status = "TOOLS_UNAVAILABLE"
                classification = "BITSTREAM_UNRECOGNIZED"
                counts["TOOLS_UNAVAILABLE"] += 1
            else:
                tool_status = "TOOLS_AVAILABLE"
                classification = classify_validation(
                    candidate_exists=True,
                    bitstream_recognized=probe.bitstream_recognized,
                    decoder_opened=decode.decoder_opened,
                    frames_decoded=decode.frames_decoded,
                    decoder_exit_code=decode.exit_code,
                    width=probe.width,
                    height=probe.height,
                )

        if classification in counts:
            counts[classification] += 1

        manifest = {
            "target_id": target_id,
            "candidate_path": str(candidate) if candidate else None,
            "candidate_exists": bool(candidate and candidate.exists()),
            "tool_status": tool_status,
            "probe": asdict(probe),
            "decode": asdict(decode),
            "classification": classification,
            "candidate_sha256": candidate_sha256,
            "candidate_modified": candidate_modified,
            "camera_channel_assertion": False,
        }
        manifests.append(manifest)

        validation.execute(
            """
            INSERT INTO validation_results VALUES(
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
            """,
            (
                target_id,
                str(candidate) if candidate else None,
                int(bool(candidate and candidate.exists())),
                tool_status,
                int(probe.bitstream_recognized),
                probe.codec_name,
                probe.width,
                probe.height,
                int(decode.decoder_opened),
                decode.frames_decoded,
                decode.exit_code,
                classification,
                candidate_sha256,
                int(candidate_modified),
                probe.stderr,
                decode.stderr,
            ),
        )

    summary = {
        "target_count": len(rows),
        "video_validated": counts["VIDEO_VALIDATED"],
        "partial_decode": counts["PARTIAL_DECODE"],
        "no_decoded_frames": counts["NO_DECODED_FRAMES"],
        "decoder_rejected": counts["DECODER_REJECTED"],
        "bitstream_unrecognized": counts["BITSTREAM_UNRECOGNIZED"],
        "empty_or_missing": counts["EMPTY_OR_MISSING"],
        "tools_unavailable": counts["TOOLS_UNAVAILABLE"],
        "candidate_missing": counts["CANDIDATE_MISSING"],
        "camera_channel_assertion": False,
        "validation_database": str(validation_db_path),
    }

    for key, value in summary.items():
        validation.execute(
            "INSERT OR REPLACE INTO validation_metadata(key,value) VALUES(?,?)",
            (key, json.dumps(value, ensure_ascii=False)),
        )

    validation.commit()
    validation.close()
    recovery.close()

    summary_path.write_text(
        json.dumps(
            {
                "summary": summary,
                "targets": manifests,
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    return summary
