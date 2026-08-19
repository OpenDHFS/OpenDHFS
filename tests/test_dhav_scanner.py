import json
import sqlite3
import struct
from pathlib import Path
from opendhfs.dhav.scanner import iter_dhav_offsets, scan_image

def pack_dt(y,m,d,h,mi,s):
    return ((y-2000)&0x3F)<<26 | (m&0x0F)<<22 | (d&0x1F)<<17 | (h&0x1F)<<12 | (mi&0x3F)<<6 | (s&0x3F)

def make_record(frame_number=1):
    h=bytearray(24)
    h[:4]=b"DHAV"; h[4]=0xFD; h[6]=17; h[7]=4
    struct.pack_into("<I",h,8,frame_number)
    struct.pack_into("<I",h,16,pack_dt(2026,6,30,3,42,59))
    h[20]=0x34; h[21]=0x12; h[22]=0; h[23]=0x7A
    payload=b"\x00\x00\x00\x01\x42\x01"+b"\xAA"*32
    declared=24+len(payload)+8
    struct.pack_into("<I",h,12,declared)
    return bytes(h)+payload+b"dhav"+struct.pack("<I",declared)

def test_chunk_boundary_magic_is_not_lost(tmp_path: Path):
    path=tmp_path/"image.bin"
    path.write_bytes(b"X"*62 + make_record() + b"Z"*32)
    assert list(iter_dhav_offsets(path,chunk_size=64)) == [62]

def test_scan_creates_sqlite_and_summary(tmp_path: Path):
    image=tmp_path/"image.bin"; out=tmp_path/"case"
    image.write_bytes(b"\x00"*11 + make_record(100) + b"\x99"*17 + make_record(101))
    s=scan_image(image,out,chunk_size=64)
    assert s["dhav_candidates"]==2
    assert s["parsed_records"]==2
    assert s["camera_channel_assertion"] is False
    conn=sqlite3.connect(out/"scan.sqlite")
    rows=conn.execute("SELECT raw_field_06,raw_field_07,frame_number FROM dhav_records ORDER BY absolute_offset").fetchall()
    conn.close()
    assert rows == [(17,4,100),(17,4,101)]
    loaded=json.loads((out/"scan_summary.json").read_text())
    assert loaded["source_access"]=="READ_ONLY"
