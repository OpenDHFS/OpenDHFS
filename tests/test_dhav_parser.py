import struct
from datetime import datetime
import pytest
from opendhfs.dhav.parser import DHAVParseError, decode_packed_datetime, parse_record
from opendhfs.dhav.validator import validation_score

def pack_dt(y,m,d,h,mi,s):
    return ((y-2000)&0x3F)<<26 | (m&0x0F)<<22 | (d&0x1F)<<17 | (h&0x1F)<<12 | (mi&0x3F)<<6 | (s&0x3F)

def make_record(field06=0, field07=0, nal=b"\x00\x00\x00\x01\x42\x01"):
    h=bytearray(24); h[:4]=b"DHAV"; h[4]=0xFD; h[6]=field06; h[7]=field07
    struct.pack_into("<I",h,8,123); struct.pack_into("<I",h,16,pack_dt(2026,6,30,3,42,59))
    h[20]=0x34; h[21]=0x12; h[22]=0; h[23]=0x7A
    payload=nal+b"\xAA"*32; declared=24+len(payload)+8; struct.pack_into("<I",h,12,declared)
    return bytes(h)+payload+b"dhav"+struct.pack("<I",declared)

def test_datetime():
    dt,ok=decode_packed_datetime(pack_dt(2026,6,30,3,42,59))
    assert ok and dt==datetime(2026,6,30,3,42,59)

def test_valid_record():
    r=parse_record(make_record(17,4))
    assert r.raw_field_06==17 and r.raw_field_07==4
    assert not hasattr(r,"channel")
    assert r.footer.valid and r.footer.size_matches
    assert r.nal.codec=="H265" and r.nal.nal_type==33

def test_raw_20_23():
    r=parse_record(make_record())
    assert r.raw_20_23==bytes([0x34,0x12,0x00,0x7A])
    assert r.raw_u16_20==0x1234 and r.raw_u32_20==0x7A001234

def test_grade_does_not_depend_on_channel():
    r=parse_record(make_record(255,255))
    score,grade=validation_score(r)
    assert score>=80 and grade=="A"

def test_bad_magic():
    b=bytearray(make_record()); b[:4]=b"NOPE"
    with pytest.raises(DHAVParseError): parse_record(bytes(b))

def test_bad_nal_not_forced():
    r=parse_record(make_record(nal=b"\x00\x00\x00\x01\xFF\x00"))
    assert r.nal.codec=="UNRECOGNIZED_NAL_HEADER"
