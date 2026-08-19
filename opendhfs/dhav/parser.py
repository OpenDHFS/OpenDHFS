import hashlib, struct
from datetime import datetime
from typing import Optional
from .constants import DHAV_MAGIC,HEADER_SIZE,FRAME_TYPE_NAMES,MIN_DECLARED_SIZE_DEFAULT,MAX_DECLARED_SIZE_DEFAULT
from .record import DHAVRecord
from .validator import classify_nal, locate_footer_in_bytes

class DHAVParseError(ValueError): pass

def decode_packed_datetime(value:int)->tuple[Optional[datetime],bool]:
    second=value&0x3F; minute=(value>>6)&0x3F; hour=(value>>12)&0x1F
    day=(value>>17)&0x1F; month=(value>>22)&0x0F; year=((value>>26)&0x3F)+2000
    try: return datetime(year,month,day,hour,minute,second),True
    except ValueError: return None,False

def parse_record(data:bytes, *, offset:int=0, source_size:Optional[int]=None,
                 min_declared_size:int=MIN_DECLARED_SIZE_DEFAULT,
                 max_declared_size:int=MAX_DECLARED_SIZE_DEFAULT,
                 payload_probe_bytes:int=4096)->DHAVRecord:
    if len(data)<HEADER_SIZE: raise DHAVParseError("candidate shorter than DHAV header")
    header=data[:HEADER_SIZE]
    if header[:4]!=DHAV_MAGIC: raise DHAVParseError("DHAV magic not found")
    ft=header[4]; frame=struct.unpack_from("<I",header,8)[0]; declared=struct.unpack_from("<I",header,12)[0]
    dt_raw=struct.unpack_from("<I",header,16)[0]; dt,dt_ok=decode_packed_datetime(dt_raw)
    raw=bytes(header[20:24]); u16=struct.unpack_from("<H",header,20)[0]; u32=struct.unpack_from("<I",header,20)[0]
    ext=header[22]; h23=header[23]
    size_ok=min_declared_size<=declared<=max_declared_size
    effective=source_size if source_size is not None else len(data)
    within=size_ok and offset+declared<=effective
    footer=locate_footer_in_bytes(data,record_start=0,declared_size=declared)
    plocal=HEADER_SIZE+ext
    pend=footer.offset if footer.offset is not None else (max(plocal,min(len(data),declared-8)) if size_ok else plocal)
    psz=max(0,pend-plocal)
    probe=data[plocal:min(len(data),plocal+min(psz,payload_probe_bytes))] if plocal<len(data) else b""
    nal=classify_nal(probe)
    return DHAVRecord(
        offset,ft,FRAME_TYPE_NAMES.get(ft,"UNKNOWN"),header[5],header[6],header[7],
        frame,declared,dt_raw,dt,dt_ok,raw,u16,u32,ext,h23,offset+plocal,psz,within,size_ok,
        footer,nal,hashlib.sha256(header).hexdigest()
    )
