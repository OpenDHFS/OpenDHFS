from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from .constants import DHAV_MAGIC, HEADER_SIZE
from .parser import DHAVParseError, parse_record
from .validator import validation_score

SCHEMA = """
CREATE TABLE IF NOT EXISTS dhav_records (
    absolute_offset INTEGER PRIMARY KEY,
    frame_type INTEGER NOT NULL,
    frame_type_name TEXT NOT NULL,
    raw_field_05 INTEGER NOT NULL,
    raw_field_06 INTEGER NOT NULL,
    raw_field_07 INTEGER NOT NULL,
    frame_number INTEGER NOT NULL,
    declared_size INTEGER NOT NULL,
    packed_datetime TEXT,
    packed_datetime_valid INTEGER NOT NULL,
    payload_offset INTEGER NOT NULL,
    payload_size INTEGER NOT NULL,
    footer_valid INTEGER NOT NULL,
    annexb_found INTEGER NOT NULL,
    codec_guess TEXT NOT NULL,
    confidence_score INTEGER NOT NULL,
    confidence_grade TEXT NOT NULL,
    header_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scan_blocks (
    block_start INTEGER PRIMARY KEY,
    block_end_exclusive INTEGER NOT NULL,
    dhav_candidates INTEGER NOT NULL,
    parsed_records INTEGER NOT NULL,
    elapsed_seconds REAL NOT NULL,
    completed_utc TEXT NOT NULL
);
"""

class ResumeError(RuntimeError):
    pass

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def source_fingerprint(path: Path, sample_size: int = 1024 * 1024) -> str:
    """Stable lightweight identity: size + first/middle/last samples."""
    size = path.stat().st_size
    h = hashlib.sha256()
    h.update(size.to_bytes(8, "little"))
    with path.open("rb") as fh:
        positions = sorted(set((0, max(0, size // 2 - sample_size // 2), max(0, size - sample_size))))
        for pos in positions:
            fh.seek(pos)
            h.update(pos.to_bytes(8, "little"))
            h.update(fh.read(min(sample_size, max(0, size - pos))))
    return h.hexdigest()

def _metadata(conn: sqlite3.Connection) -> dict:
    return {k: json.loads(v) for k, v in conn.execute("SELECT key,value FROM metadata")}

def _write_metadata(conn: sqlite3.Connection, values: dict) -> None:
    for k, v in values.items():
        conn.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES(?,?)",
                     (k, json.dumps(v, ensure_ascii=False)))
def iter_dhav_offsets(
    path: Path,
    chunk_size: int = 64 * 1024 * 1024,
):
    """
    Yield absolute offsets of DHAV signatures in physical order.

    The overlap preserves signatures crossing chunk boundaries while the
    absolute-offset guard prevents duplicate emission.
    """
    path = Path(path)
    overlap = len(DHAV_MAGIC) - 1
    previous_offset = -1

    with path.open("rb") as handle:
        absolute_base = 0
        tail = b""

        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break

            data = tail + chunk
            data_base = absolute_base - len(tail)

            position = 0
            while True:
                found = data.find(DHAV_MAGIC, position)
                if found < 0:
                    break

                absolute_offset = data_base + found

                if absolute_offset > previous_offset:
                    yield absolute_offset
                    previous_offset = absolute_offset

                position = found + 1

            tail = data[-overlap:] if overlap else b""
            absolute_base += len(chunk)


def _find_magic_offsets(
    data: bytes,
    data_base: int,
    block_start: int,
    block_end: int,
) -> list[int]:
    """Only assign a candidate to the block in which its first byte starts."""

    out = []
    pos = 0
    while True:
        found = data.find(DHAV_MAGIC, pos)
        if found < 0:
            break
        absolute = data_base + found
        if block_start <= absolute < block_end:
            out.append(absolute)
        pos = found + 1
    return out

def _read_candidate_window(fh, image_size: int, offset: int,
                           max_declared_size: int, probe: int) -> bytes:
    fh.seek(offset)
    header = fh.read(HEADER_SIZE)
    if len(header) < HEADER_SIZE:
        return header
    declared = int.from_bytes(header[12:16], "little")
    if declared < HEADER_SIZE or declared > max_declared_size:
        return header
    requested = min(image_size - offset, max(declared + 8, HEADER_SIZE + probe))
    fh.seek(offset)
    return fh.read(requested)

def _insert_record(conn: sqlite3.Connection, r, score: int, grade: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO dhav_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            r.offset, r.frame_type, r.frame_type_name,
            r.raw_field_05, r.raw_field_06, r.raw_field_07,
            r.frame_number, r.declared_size,
            r.packed_datetime.isoformat(sep=" ") if r.packed_datetime else None,
            int(r.packed_datetime_valid), r.payload_offset, r.payload_size,
            int(r.footer.valid), int(r.nal.annexb_found), r.nal.codec,
            score, grade, r.header_sha256,
        ),
    )

def scan_image(image: Path, output_dir: Path, *, chunk_size: int = 64 * 1024 * 1024,
               max_declared_size: int = 10 * 1024 * 1024,
               payload_probe_bytes: int = 4096, resume: bool = False,
               stop_after_blocks: int | None = None) -> dict:
    image = image.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    image_size = image.stat().st_size
    fingerprint = source_fingerprint(image)
    db_path = output_dir / "scan.sqlite"

    if resume and not db_path.exists():
        raise ResumeError("--resume requested but scan.sqlite does not exist")
    if not resume and db_path.exists():
        raise ResumeError("scan.sqlite already exists; use --resume or a new output directory")

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    identity = {
        "image_size": image_size,
        "source_fingerprint": fingerprint,
        "chunk_size": chunk_size,
        "max_declared_size": max_declared_size,
        "payload_probe_bytes": payload_probe_bytes,
    }

    if resume:
        old = _metadata(conn)
        for key, value in identity.items():
            if old.get(key) != value:
                conn.close()
                raise ResumeError(f"resume identity mismatch for {key}")
    else:
        _write_metadata(conn, {
            **identity,
            "image_path": str(image),
            "source_access": "READ_ONLY",
            "camera_channel_assertion": False,
            "started_utc": utc_now(),
        })
        conn.commit()

    completed = {row[0] for row in conn.execute("SELECT block_start FROM scan_blocks")}
    blocks_completed_this_run = 0
    overlap = len(DHAV_MAGIC) - 1

    try:
        with image.open("rb") as fh:
            for block_start in range(0, image_size, chunk_size):
                if block_start in completed:
                    continue

                block_end = min(image_size, block_start + chunk_size)
                read_start = max(0, block_start - overlap)
                read_end = min(image_size, block_end + overlap)
                fh.seek(read_start)
                data = fh.read(read_end - read_start)

                t0 = time.monotonic()
                offsets = _find_magic_offsets(data, read_start, block_start, block_end)
                parsed = 0

                conn.execute("BEGIN")
                try:
                    for offset in offsets:
                        blob = _read_candidate_window(
                            fh, image_size, offset, max_declared_size, payload_probe_bytes
                        )
                        try:
                            r = parse_record(
                                blob, offset=offset, source_size=image_size,
                                max_declared_size=max_declared_size,
                                payload_probe_bytes=payload_probe_bytes,
                            )
                        except DHAVParseError:
                            continue
                        score, grade = validation_score(r)
                        _insert_record(conn, r, score, grade)
                        parsed += 1

                    conn.execute(
                        """INSERT INTO scan_blocks
                           (block_start,block_end_exclusive,dhav_candidates,parsed_records,
                            elapsed_seconds,completed_utc)
                           VALUES(?,?,?,?,?,?)""",
                        (block_start, block_end, len(offsets), parsed,
                         time.monotonic() - t0, utc_now()),
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

                blocks_completed_this_run += 1
                if stop_after_blocks is not None and blocks_completed_this_run >= stop_after_blocks:
                    raise InterruptedError("simulated interruption after completed block")
    finally:
        conn.close()

    conn = sqlite3.connect(db_path)
    candidates, parsed = conn.execute(
        "SELECT COALESCE(SUM(dhav_candidates),0), COALESCE(SUM(parsed_records),0) FROM scan_blocks"
    ).fetchone()
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for grade, count in conn.execute(
        "SELECT confidence_grade, COUNT(*) FROM dhav_records GROUP BY confidence_grade"
    ):
        grade_counts[grade] = count
    blocks = conn.execute("SELECT COUNT(*) FROM scan_blocks").fetchone()[0]
    conn.close()

    total_blocks = (image_size + chunk_size - 1) // chunk_size if image_size else 0
    summary = {
        "image": str(image),
        "image_size": image_size,
        "source_fingerprint": fingerprint,
        "dhav_candidates": candidates,
        "parsed_records": parsed,
        "grade_counts": grade_counts,
        "blocks_completed": blocks,
        "blocks_total": total_blocks,
        "complete": blocks == total_blocks,
        "database": str(db_path),
        "source_access": "READ_ONLY",
        "camera_channel_assertion": False,
    }
    (output_dir / "scan_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary
