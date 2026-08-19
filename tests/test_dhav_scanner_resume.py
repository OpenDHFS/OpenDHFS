import sqlite3
import struct
from pathlib import Path
import pytest

from opendhfs.dhav.scanner import ResumeError, scan_image

def pack_dt(y,m,d,h,mi,s):
    return ((y-2000)&0x3F)<<26 | (m&0x0F)<<22 | (d&0x1F)<<17 | (h&0x1F)<<12 | (mi&0x3F)<<6 | (s&0x3F)

def make_record(frame_number=1, second=10):
    h=bytearray(24); h[:4]=b"DHAV"; h[4]=0xFD; h[6]=17; h[7]=4
    struct.pack_into("<I",h,8,frame_number)
    struct.pack_into("<I",h,16,pack_dt(2026,6,30,3,42,second))
    h[20]=0x34; h[21]=0x12; h[22]=0; h[23]=0x7A
    payload=b"\x00\x00\x00\x01\x42\x01"+b"\xAA"*32
    declared=24+len(payload)+8
    struct.pack_into("<I",h,12,declared)
    return bytes(h)+payload+b"dhav"+struct.pack("<I",declared)

def rows(db):
    conn=sqlite3.connect(db)
    result=conn.execute(
        "SELECT absolute_offset,frame_number,confidence_grade FROM dhav_records ORDER BY absolute_offset"
    ).fetchall()
    conn.close()
    return result

def test_resume_matches_continuous_scan(tmp_path: Path):
    image=tmp_path/"image.bin"
    image.write_bytes(
        b"X"*62 + make_record(100,10) + b"Y"*71 +
        make_record(101,11) + b"Z"*83 + make_record(102,12)
    )

    continuous=tmp_path/"continuous"
    resumed=tmp_path/"resumed"
    scan_image(image, continuous, chunk_size=64)

    with pytest.raises(InterruptedError):
        scan_image(image, resumed, chunk_size=64, stop_after_blocks=2)

    conn=sqlite3.connect(resumed/"scan.sqlite")
    completed=conn.execute("SELECT COUNT(*) FROM scan_blocks").fetchone()[0]
    conn.close()
    assert completed == 2

    result=scan_image(image, resumed, chunk_size=64, resume=True)
    assert result["complete"] is True
    assert rows(continuous/"scan.sqlite") == rows(resumed/"scan.sqlite")

def test_resume_does_not_duplicate_records(tmp_path: Path):
    image=tmp_path/"image.bin"
    image.write_bytes(b"A"*30 + make_record(1) + b"B"*150 + make_record(2))
    out=tmp_path/"case"

    with pytest.raises(InterruptedError):
        scan_image(image,out,chunk_size=64,stop_after_blocks=2)
    scan_image(image,out,chunk_size=64,resume=True)

    data=rows(out/"scan.sqlite")
    assert len(data)==2
    assert [r[1] for r in data]==[1,2]

def test_resume_rejects_different_source(tmp_path: Path):
    image=tmp_path/"image.bin"
    image.write_bytes(b"A"*30 + make_record(1) + b"B"*200)
    out=tmp_path/"case"

    with pytest.raises(InterruptedError):
        scan_image(image,out,chunk_size=64,stop_after_blocks=1)

    altered=bytearray(image.read_bytes())
    altered[len(altered)//2] ^= 0x01
    image.write_bytes(altered)

    with pytest.raises(ResumeError, match="source_fingerprint"):
        scan_image(image,out,chunk_size=64,resume=True)

def test_resume_rejects_changed_chunk_size(tmp_path: Path):
    image=tmp_path/"image.bin"
    image.write_bytes(b"A"*30 + make_record(1) + b"B"*200)
    out=tmp_path/"case"

    with pytest.raises(InterruptedError):
        scan_image(image,out,chunk_size=64,stop_after_blocks=1)

    with pytest.raises(ResumeError, match="chunk_size"):
        scan_image(image,out,chunk_size=128,resume=True)
