from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Iterator

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
"""

def iter_dhav_offsets(path: Path, chunk_size: int = 64 * 1024 * 1024) -> Iterator[int]:
    overlap = len(DHAV_MAGIC) - 1
    file_size = path.stat().st_size
    with path.open("rb") as fh:
        base = 0
        tail = b""
        last_yielded = None
        while base < file_size:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            data = tail + chunk
            data_base = base - len(tail)
            pos = 0
            while True:
                found = data.find(DHAV_MAGIC, pos)
                if found < 0:
                    break
                absolute = data_base + found
                if absolute >= 0 and absolute != last_yielded:
                    yield absolute
                    last_yielded = absolute
                pos = found + 1
            tail = data[-overlap:] if len(data) >= overlap else data
            base += len(chunk)

def _read_candidate_window(fh, image_size: int, offset: int, max_declared_size: int, probe: int) -> bytes:
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

def scan_image(image: Path, output_dir: Path, *, chunk_size: int = 64 * 1024 * 1024,
               max_declared_size: int = 10 * 1024 * 1024, payload_probe_bytes: int = 4096) -> dict:
    image = image.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    image_size = image.stat().st_size

    db_path = output_dir / "scan.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    for k, v in {
        "image_path": str(image),
        "image_size": image_size,
        "source_access": "READ_ONLY",
        "camera_channel_assertion": False,
    }.items():
        conn.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES(?,?)", (k, json.dumps(v)))

    candidates = parsed = 0
    grades = {"A": 0, "B": 0, "C": 0, "D": 0}

    with image.open("rb") as fh:
        for offset in iter_dhav_offsets(image, chunk_size):
            candidates += 1
            blob = _read_candidate_window(fh, image_size, offset, max_declared_size, payload_probe_bytes)
            try:
                r = parse_record(blob, offset=offset, source_size=image_size,
                                 max_declared_size=max_declared_size,
                                 payload_probe_bytes=payload_probe_bytes)
            except DHAVParseError:
                continue
            score, grade = validation_score(r)
            grades[grade] += 1
            parsed += 1
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

    conn.commit()
    conn.close()

    summary = {
        "image": str(image),
        "image_size": image_size,
        "dhav_candidates": candidates,
        "parsed_records": parsed,
        "grade_counts": grades,
        "database": str(db_path),
        "source_access": "READ_ONLY",
        "camera_channel_assertion": False,
    }
    (output_dir / "scan_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary
