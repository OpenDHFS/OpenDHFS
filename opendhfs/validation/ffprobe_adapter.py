from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class FFprobeUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ProbeResult:
    tool_available: bool
    bitstream_recognized: bool
    codec_name: str | None
    width: int | None
    height: int | None
    exit_code: int | None
    stderr: str


def resolve_ffprobe(
    explicit_path: Path | None = None,
) -> Path | None:
    if explicit_path is not None:
        path = Path(explicit_path)

        if path.exists():
            return path

        return None

    found = shutil.which("ffprobe")

    return Path(found) if found else None


def probe_candidate(
    candidate: Path,
    *,
    ffprobe_path: Path | None = None,
    timeout_seconds: int = 30,
) -> ProbeResult:
    candidate = Path(candidate)

    tool = resolve_ffprobe(
        ffprobe_path
    )

    if tool is None:
        return ProbeResult(
            tool_available=False,
            bitstream_recognized=False,
            codec_name=None,
            width=None,
            height=None,
            exit_code=None,
            stderr="ffprobe unavailable",
        )

    if not candidate.exists():
        return ProbeResult(
            tool_available=True,
            bitstream_recognized=False,
            codec_name=None,
            width=None,
            height=None,
            exit_code=None,
            stderr="candidate missing",
        )

    command = [
        str(tool),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height",
        "-of",
        "json",
        str(candidate),
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            tool_available=True,
            bitstream_recognized=False,
            codec_name=None,
            width=None,
            height=None,
            exit_code=None,
            stderr="ffprobe timeout",
        )

    codec_name = None
    width = None
    height = None
    recognized = False

    if completed.returncode == 0:
        try:
            payload = json.loads(
                completed.stdout or "{}"
            )
        except json.JSONDecodeError:
            payload = {}

        streams = payload.get(
            "streams",
            [],
        )

        if streams:
            stream = streams[0]

            codec_name = stream.get(
                "codec_name"
            )

            width = stream.get(
                "width"
            )

            height = stream.get(
                "height"
            )

            recognized = bool(
                codec_name
            )

    return ProbeResult(
        tool_available=True,
        bitstream_recognized=recognized,
        codec_name=codec_name,
        width=width,
        height=height,
        exit_code=completed.returncode,
        stderr=completed.stderr or "",
    )