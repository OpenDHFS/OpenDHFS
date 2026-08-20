def classify_validation(
    *,
    candidate_exists: bool,
    bitstream_recognized: bool,
    decoder_opened: bool,
    frames_decoded: int,
    decoder_exit_code: int | None,
    width: int | None,
    height: int | None,
) -> str:
    """
    Classify a recovered media candidate conservatively.

    Classification order is deliberate. OpenDHFS does not treat file
    existence, codec recognition, decoder opening, or a successful process
    exit as equivalent to validated video.
    """

    if not candidate_exists:
        return "EMPTY_OR_MISSING"

    if not bitstream_recognized:
        return "BITSTREAM_UNRECOGNIZED"

    if not decoder_opened:
        return "DECODER_REJECTED"

    if (
        frames_decoded <= 0
        and decoder_exit_code not in (0, None)
        ):
        return "DECODER_REJECTED"

    if frames_decoded <= 0:
        return "NO_DECODED_FRAMES"

    if decoder_exit_code not in (0, None):
        return "PARTIAL_DECODE"

    if (
        width is None
        or height is None
        or width <= 0
        or height <= 0
    ):
        return "PARTIAL_DECODE"

    return "VIDEO_VALIDATED"