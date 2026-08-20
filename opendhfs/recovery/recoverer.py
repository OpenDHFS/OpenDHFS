from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from opendhfs.dhav.parser import DHAVParseError, parse_record


class RecoveryError(RuntimeError):
    pass


RECOVERY_SCHEMA = """
CREATE TABLE IF NOT EXISTS recovery_results(
    target_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    tier TEXT NOT NULL,
    strategy TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset_exclusive INTEGER NOT NULL,
    planned_records INTEGER NOT NULL,
    records_examined INTEGER NOT NULL,
    payload_records INTEGER NOT NULL,
    payload_bytes INTEGER NOT NULL,
    codec TEXT NOT NULL,
    candidate_path TEXT,
    candidate_sha256 TEXT,
    source_modified INTEGER NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recovery_metadata(
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _connect_ro(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise RecoveryError(f"required database not found: {path}")
    return sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _read_record_blob(handle, image_size: int, absolute_offset: int, declared_size: int) -> bytes:
    requested = declared_size + 8
    if absolute_offset < 0:
        return b""
    if absolute_offset + requested > image_size:
        requested = max(0, image_size - absolute_offset)
    handle.seek(absolute_offset)
    return handle.read(requested)


def _candidate_name(codec: str) -> str:
    if codec == "H265":
        return "candidate.h265"
    if codec == "H264":
        return "candidate.h264"
    return "candidate.es"


def recover_targets(case_dir: Path, image: Path, *, overwrite: bool = False) -> dict:
    case_dir = Path(case_dir).resolve()
    image = Path(image).resolve()

    if not image.exists():
        raise RecoveryError(f"source image not found: {image}")

    scan_path = case_dir / "scan.sqlite"
    plan_path = case_dir / "recovery_plan.sqlite"
    recovery_db_path = case_dir / "recovery.sqlite"
    recovery_root = case_dir / "recovery"
    summary_path = case_dir / "recovery_summary.json"

    if recovery_db_path.exists():
        if not overwrite:
            raise RecoveryError("recovery.sqlite already exists; use overwrite=True")
        recovery_db_path.unlink()

    if recovery_root.exists():
        if not overwrite:
            raise RecoveryError("recovery output directory already exists; use overwrite=True")
        import shutil
        shutil.rmtree(recovery_root)

    recovery_root.mkdir(parents=True, exist_ok=True)

    scan = _connect_ro(scan_path)
    plan = _connect_ro(plan_path)

    recovery = sqlite3.connect(recovery_db_path)
    recovery.executescript(RECOVERY_SCHEMA)

    image_size = image.stat().st_size
    source_before_size = image_size
    source_before_mtime_ns = image.stat().st_mtime_ns

    targets = plan.execute(
        """
        SELECT target_id, priority, tier, strategy,
               start_offset, end_offset_exclusive, record_count
        FROM recovery_targets
        ORDER BY priority, target_id
        """
    ).fetchall()

    recovered_payload = 0
    no_video_payload = 0
    failed = 0
    total_payload_bytes = 0
    manifests = []

    with image.open("rb") as image_handle:
        for target_id, priority, tier, strategy, start_offset, end_offset_exclusive, planned_records in targets:
            target_dir = recovery_root / target_id
            target_dir.mkdir(parents=True, exist_ok=True)

            rows = scan.execute(
                """
                SELECT absolute_offset, frame_type, declared_size, codec_guess
                FROM dhav_records
                WHERE absolute_offset >= ? AND absolute_offset < ?
                ORDER BY absolute_offset
                """,
                (start_offset, end_offset_exclusive),
            ).fetchall()

            payloads = []
            codecs = []
            accepted_offsets = []
            rejection_reasons = []
            examined = 0
            status = "NO_VIDEO_PAYLOAD"

            try:
                for absolute_offset, frame_type, declared_size, codec_guess in rows:
                    examined += 1
                    if frame_type not in (0xFC, 0xFD):
                        continue
                    if declared_size is None:
                        rejection_reasons.append(f"{absolute_offset}:MISSING_DECLARED_SIZE")
                        continue

                    declared_size = int(declared_size)
                    blob = _read_record_blob(
                        image_handle, image_size, absolute_offset, declared_size
                    )

                    try:
                        record = parse_record(
                            blob,
                            offset=absolute_offset,
                            source_size=image_size,
                        )
                    except DHAVParseError:
                        rejection_reasons.append(f"{absolute_offset}:DHAV_REPARSE_FAILED")
                        continue

                    if not record.size_plausible:
                        rejection_reasons.append(f"{absolute_offset}:IMPLAUSIBLE_SIZE")
                        continue
                    if record.payload_size <= 0:
                        rejection_reasons.append(f"{absolute_offset}:EMPTY_PAYLOAD")
                        continue

                    local_start = record.payload_offset - absolute_offset
                    local_end = local_start + record.payload_size
                    if local_start < 0 or local_end > len(blob):
                        rejection_reasons.append(f"{absolute_offset}:PAYLOAD_OUT_OF_BOUNDS")
                        continue

                    payload = blob[local_start:local_end]
                    if not payload:
                        continue

                    payloads.append(payload)
                    accepted_offsets.append(absolute_offset)

                    if record.nal.codec in ("H264", "H265"):
                        codecs.append(record.nal.codec)
                    elif codec_guess in ("H264", "H265"):
                        codecs.append(codec_guess)

                unique_codecs = sorted(set(codecs))
                if len(unique_codecs) == 1:
                    result_codec = unique_codecs[0]
                elif len(unique_codecs) > 1:
                    result_codec = "MIXED_H264_H265"
                else:
                    result_codec = "UNKNOWN"

                payload_bytes = sum(len(p) for p in payloads)
                candidate_path = None
                candidate_sha256 = None

                if payloads:
                    candidate_path_obj = target_dir / _candidate_name(result_codec)
                    with candidate_path_obj.open("wb") as out_handle:
                        for payload in payloads:
                            out_handle.write(payload)

                    candidate_path = str(candidate_path_obj)
                    candidate_sha256 = _sha256_file(candidate_path_obj)
                    status = "RECOVERED_PAYLOAD"
                    recovered_payload += 1
                    total_payload_bytes += payload_bytes
                else:
                    no_video_payload += 1

            except Exception as exc:
                status = "READ_OR_STRUCTURE_FAILURE"
                failed += 1
                payload_bytes = 0
                result_codec = "UNKNOWN"
                candidate_path = None
                candidate_sha256 = None
                rejection_reasons.append(
                    f"TARGET_FAILURE:{type(exc).__name__}:{exc}"
                )

            manifest = {
                "target_id": target_id,
                "priority": priority,
                "tier": tier,
                "strategy": strategy,
                "status": status,
                "start_offset": start_offset,
                "end_offset_exclusive": end_offset_exclusive,
                "planned_records": planned_records,
                "records_examined": examined,
                "payload_records": len(payloads),
                "payload_bytes": payload_bytes,
                "codec": result_codec,
                "accepted_offsets": accepted_offsets,
                "candidate_path": candidate_path,
                "candidate_sha256": candidate_sha256,
                "rejection_reasons": rejection_reasons,
                "source_access": "READ_ONLY",
                "camera_channel_assertion": False,
                "decoder_validation": False,
            }

            (target_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            manifests.append(manifest)

            recovery.execute(
                """
                INSERT INTO recovery_results VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    target_id,
                    status,
                    tier,
                    strategy,
                    start_offset,
                    end_offset_exclusive,
                    planned_records,
                    examined,
                    len(payloads),
                    payload_bytes,
                    result_codec,
                    candidate_path,
                    candidate_sha256,
                    0,
                    "|".join(rejection_reasons),
                ),
            )

    source_after = image.stat()
    source_modified = (
        source_after.st_size != source_before_size
        or source_after.st_mtime_ns != source_before_mtime_ns
    )
    if source_modified:
        recovery.close()
        scan.close()
        plan.close()
        raise RecoveryError("source image metadata changed during recovery")

    summary = {
        "target_count": len(targets),
        "recovered_payload": recovered_payload,
        "no_video_payload": no_video_payload,
        "failed": failed,
        "payload_bytes": total_payload_bytes,
        "recovery_assertion": False,
        "decoder_validation": False,
        "camera_channel_assertion": False,
        "source_access": "READ_ONLY",
        "recovery_database": str(recovery_db_path),
    }

    for key, value in summary.items():
        recovery.execute(
            "INSERT OR REPLACE INTO recovery_metadata(key,value) VALUES(?,?)",
            (key, json.dumps(value, ensure_ascii=False)),
        )

    recovery.commit()
    recovery.close()
    scan.close()
    plan.close()

    summary_path.write_text(
        json.dumps({"summary": summary, "targets": manifests}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return summary
