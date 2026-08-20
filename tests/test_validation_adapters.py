from pathlib import Path
from unittest.mock import patch

from opendhfs.validation.ffmpeg_adapter import (
    _extract_frame_count,
    decode_candidate,
    resolve_ffmpeg,
)

from opendhfs.validation.ffprobe_adapter import (
    probe_candidate,
    resolve_ffprobe,
)


def test_resolve_ffmpeg_missing():
    with patch(
        "shutil.which",
        return_value=None,
    ):
        assert resolve_ffmpeg() is None


def test_resolve_ffprobe_missing():
    with patch(
        "shutil.which",
        return_value=None,
    ):
        assert resolve_ffprobe() is None


def test_ffprobe_unavailable(
    tmp_path: Path,
):
    candidate = (
        tmp_path
        / "candidate.h265"
    )

    candidate.write_bytes(
        b"test"
    )

    with patch(
        "shutil.which",
        return_value=None,
    ):
        result = probe_candidate(
            candidate
        )

    assert result.tool_available is False
    assert result.bitstream_recognized is False
    assert result.codec_name is None


def test_ffmpeg_unavailable(
    tmp_path: Path,
):
    candidate = (
        tmp_path
        / "candidate.h265"
    )

    candidate.write_bytes(
        b"test"
    )

    with patch(
        "shutil.which",
        return_value=None,
    ):
        result = decode_candidate(
            candidate
        )

    assert result.tool_available is False
    assert result.decoder_opened is False
    assert result.frames_decoded == 0


def test_extract_frame_count():
    stderr = """
    frame=    1 fps=0.0
    frame=   17 fps=0.0
    frame=  123 fps=0.0
    """

    assert (
        _extract_frame_count(
            stderr
        )
        == 123
    )


def test_ffprobe_success(
    tmp_path: Path,
):
    candidate = (
        tmp_path
        / "candidate.h265"
    )

    candidate.write_bytes(
        b"test"
    )

    fake = type(
        "Completed",
        (),
        {
            "returncode": 0,
            "stdout": (
                '{"streams": ['
                '{"codec_name": "hevc", '
                '"width": 2560, '
                '"height": 1440}'
                "]}"
            ),
            "stderr": "",
        },
    )()

    with patch(
        "opendhfs.validation.ffprobe_adapter.resolve_ffprobe",
        return_value=Path(
            "/fake/ffprobe"
        ),
    ):
        with patch(
            "subprocess.run",
            return_value=fake,
        ):
            result = probe_candidate(
                candidate
            )

    assert result.tool_available is True
    assert result.bitstream_recognized is True
    assert result.codec_name == "hevc"
    assert result.width == 2560
    assert result.height == 1440


def test_ffmpeg_success(
    tmp_path: Path,
):
    candidate = (
        tmp_path
        / "candidate.h265"
    )

    candidate.write_bytes(
        b"test"
    )

    fake = type(
        "Completed",
        (),
        {
            "returncode": 0,
            "stdout": "",
            "stderr": (
                "Stream #0:0: Video: hevc\n"
                "frame=   42 fps=0.0\n"
            ),
        },
    )()

    with patch(
        "opendhfs.validation.ffmpeg_adapter.resolve_ffmpeg",
        return_value=Path(
            "/fake/ffmpeg"
        ),
    ):
        with patch(
            "subprocess.run",
            return_value=fake,
        ):
            result = decode_candidate(
                candidate
            )

    assert result.tool_available is True
    assert result.decoder_opened is True
    assert result.frames_decoded == 42
    assert result.exit_code == 0