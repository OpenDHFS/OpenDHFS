from pathlib import Path

from opendhfs.validation.validator import (
    classify_validation,
)


def test_video_validated():
    result = classify_validation(
        candidate_exists=True,
        bitstream_recognized=True,
        decoder_opened=True,
        frames_decoded=120,
        decoder_exit_code=0,
        width=2560,
        height=1440,
    )

    assert result == "VIDEO_VALIDATED"


def test_missing_candidate():
    result = classify_validation(
        candidate_exists=False,
        bitstream_recognized=False,
        decoder_opened=False,
        frames_decoded=0,
        decoder_exit_code=None,
        width=None,
        height=None,
    )

    assert result == "EMPTY_OR_MISSING"


def test_decoder_rejected():
    result = classify_validation(
        candidate_exists=True,
        bitstream_recognized=True,
        decoder_opened=False,
        frames_decoded=0,
        decoder_exit_code=1,
        width=None,
        height=None,
    )

    assert result == "DECODER_REJECTED"


def test_no_frames_is_not_valid_video():
    result = classify_validation(
        candidate_exists=True,
        bitstream_recognized=True,
        decoder_opened=True,
        frames_decoded=0,
        decoder_exit_code=0,
        width=2560,
        height=1440,
    )

    assert result == "NO_DECODED_FRAMES"


def test_partial_decode():
    result = classify_validation(
        candidate_exists=True,
        bitstream_recognized=True,
        decoder_opened=True,
        frames_decoded=17,
        decoder_exit_code=1,
        width=2560,
        height=1440,
    )

    assert result == "PARTIAL_DECODE"