import struct
from typing import Optional
from .constants import DHAV_FOOTER_MAGIC, HEADER_SIZE, H264_NAL_NAMES, H265_NAL_NAMES
from .record import FooterObservation, NalObservation

def find_annexb(data: bytes) -> Optional[tuple[int,int]]:
    c=[]
    for sig in (b"\x00\x00\x00\x01", b"\x00\x00\x01"):
        p=data.find(sig)
        if p>=0: c.append((p,len(sig)))
    return min(c) if c else None

def classify_nal(data: bytes) -> NalObservation:
    found=find_annexb(data)
    if not found:
        return NalObservation("UNKNOWN",None,"",False,None)
    p,n=found; h=p+n
    if h>=len(data):
        return NalObservation("UNRECOGNIZED_NAL_HEADER",None,"",True,p)
    b0=data[h]
    h264_ok=((b0>>7)&1)==0 and 1 <= (b0 & 0x1F) <= 12
    h264_type=b0 & 0x1F
    h265_ok=False; h265_type=-1
    if h+1 < len(data):
        b1=data[h+1]
        h265_type=(b0>>1)&0x3F
        h265_ok=((b0>>7)&1)==0 and 0 <= h265_type <= 40 and (b1 & 0x07)!=0
    s265=(1 if h265_ok else 0)+(3 if h265_ok and h265_type in H265_NAL_NAMES else 0)
    s264=(1 if h264_ok else 0)+(3 if h264_ok and h264_type in H264_NAL_NAMES else 0)
    if s265>s264:
        return NalObservation("H265",h265_type,H265_NAL_NAMES.get(h265_type,f"NAL_{h265_type}"),True,p)
    if s264>s265:
        return NalObservation("H264",h264_type,H264_NAL_NAMES.get(h264_type,f"NAL_{h264_type}"),True,p)
    if h265_ok and h264_ok:
        return NalObservation("AMBIGUOUS_H264_H265",h265_type,f"H265_{h265_type}/H264_{h264_type}",True,p)
    return NalObservation("UNRECOGNIZED_NAL_HEADER",None,"",True,p)

def locate_footer_in_bytes(data: bytes, *, record_start:int, declared_size:int)->FooterObservation:
    for mode,pos in (
        ("SIZE_INCLUDES_8_BYTE_FOOTER",record_start+declared_size-8),
        ("FOOTER_AT_START_PLUS_SIZE",record_start+declared_size),
    ):
        if pos < record_start + HEADER_SIZE or pos+4 > len(data): continue
        if data[pos:pos+4] != DHAV_FOOTER_MAGIC: continue
        size_field=None; matches=False
        if pos+8 <= len(data):
            size_field=struct.unpack_from("<I",data,pos+4)[0]
            matches=size_field in {declared_size,declared_size-8,pos-record_start,pos-record_start+8}
        return FooterObservation(True,mode,pos,size_field,matches)
    return FooterObservation(False,"NOT_FOUND_AT_DECLARED_BOUNDARY",None,None,False)

def validation_score(record)->tuple[int,str]:
    score=0
    score += 15 if record.size_plausible else 0
    score += 15 if record.packed_datetime_valid else 0
    score += 10 if record.within_source else 0
    score += 25 if record.footer.valid else 0
    score += 5 if record.footer.size_matches else 0
    score += 20 if record.nal.annexb_found else 0
    score += 10 if record.frame_type_name != "UNKNOWN" else 0
    if record.footer.valid and record.nal.annexb_found and record.packed_datetime_valid and score>=80: grade="A"
    elif record.nal.annexb_found and record.size_plausible and score>=55: grade="B"
    elif record.footer.valid or record.packed_datetime_valid: grade="C"
    else: grade="D"
    return score,grade
