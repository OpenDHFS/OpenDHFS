from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class NalObservation:
    codec: str
    nal_type: Optional[int]
    nal_name: str
    annexb_found: bool
    start_code_offset: Optional[int] = None

@dataclass(frozen=True)
class FooterObservation:
    valid: bool
    mode: str
    offset: Optional[int]
    size_field: Optional[int]
    size_matches: bool

@dataclass(frozen=True)
class DHAVRecord:
    offset: int
    frame_type: int
    frame_type_name: str
    raw_field_05: int
    raw_field_06: int
    raw_field_07: int
    frame_number: int
    declared_size: int
    packed_datetime_raw: int
    packed_datetime: Optional[datetime]
    packed_datetime_valid: bool
    raw_20_23: bytes
    raw_u16_20: int
    raw_u32_20: int
    extension_length_candidate: int
    header_byte_23: int
    payload_offset: int
    payload_size: int
    within_source: bool
    size_plausible: bool
    footer: FooterObservation
    nal: NalObservation
    header_sha256: str
