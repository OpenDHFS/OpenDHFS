from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DecodeResult:
    tool_available: bool
    decoder_opened: bool
    frames_decoded: int
    exit_code: int | None
    stderr: str


def resolve_ffmpeg(
    explicit_path: Path | None = None,
) -> Path | None:
    if explicit_path is not None:
        path = Path(explicit_path)

        if path.exists():
            return path

        return None

    found = shutil.which("ffmpeg")

    return Path(found) if found else None


def _extract_frame_count(
    stderr: str,
) -> int:
    matches = re.findall(
        r"frame=\s*(\d+)",
        stderr,
    )

    if not matches:
        return 0

    return int(
        matches[-1]
    )


def decode_candidate(
    candidate: Path,
    *,
    ffmpeg_path: Path | None = None,
    timeout_seconds: int = 60,
) -> DecodeResult:
    candidate = Path(candidate)

    tool = resolve_ffmpeg(
        ffmpeg_path
    )

    if tool is None:
        return DecodeResult(
            tool_available=False,
            decoder_opened=False,
            frames_decoded=0,
            exit_code=None,
            stderr="ffmpeg unavailable",
        )

    if not candidate.exists():
        return DecodeResult(
            tool_available=True,
            decoder_opened=False,
            frames_decoded=0,
            exit_code=None,
            stderr="candidate missing",
        )

    command = [
        str(tool),
        "-v",
        "info",
        "-i",
        str(candidate),
        "-map",
        "0:v:0",
        "-f",
        "null",
        "-",
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return DecodeResult(
            tool_available=True,
            decoder_opened=False,
            frames_decoded=0,
            exit_code=None,
            stderr="ffmpeg timeout",
        )

    stderr = completed.stderr or ""

    frames = _extract_frame_count(
        stderr
    )

    decoder_opened = (
        "Video:" in stderr
        or frames > 0
    )

    return DecodeResult(
        tool_available=True,
        decoder_opened=decoder_opened,
        frames_decoded=frames,
        exit_code=completed.returncode,
        stderr=stderr,
    )