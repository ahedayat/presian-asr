"""Tests for audio utility functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from persian_asr_app.core.audio_utils import (
    SAMPLE_RATE,
    build_ffmpeg_convert_command,
    convert_to_temp_wav_16k_mono,
    ensure_mono,
    estimate_audio_duration,
    format_duration,
    is_audio_longer_than_threshold,
    validate_audio_path,
)


def test_sample_rate_is_whisper_default() -> None:
    assert SAMPLE_RATE == 16000


def test_ensure_mono_from_stereo() -> None:
    # Shape (channels, samples): two channels, two time steps.
    stereo = np.array([[1.0, 0.0], [0.5, 0.5]], dtype=np.float32)
    mono = ensure_mono(stereo)
    assert mono.ndim == 1
    assert mono.shape[0] == 2
    np.testing.assert_allclose(mono, [0.75, 0.25])


def test_ensure_mono_preserves_1d_array() -> None:
    mono_input = np.array([0.1, 0.2, 0.3], dtype=np.float64)
    result = ensure_mono(mono_input)
    assert result.dtype == np.float32
    np.testing.assert_allclose(result, mono_input, rtol=1e-6)


def test_validate_audio_path_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.wav"
    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        validate_audio_path(str(missing))


def test_validate_audio_path_unsupported_extension(tmp_path: Path) -> None:
    unsupported = tmp_path / "sample.txt"
    unsupported.write_text("not audio")
    with pytest.raises(ValueError, match="Unsupported audio format '.txt'"):
        validate_audio_path(str(unsupported))


@pytest.mark.parametrize("extension", [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"])
def test_validate_audio_path_accepts_supported_extensions(
    tmp_path: Path,
    extension: str,
) -> None:
    audio_file = tmp_path / f"sample{extension}"
    audio_file.write_bytes(b"fake-audio")
    resolved = validate_audio_path(str(audio_file))
    assert resolved == audio_file.resolve()


def test_format_duration_short() -> None:
    assert format_duration(65) == "1:05"
    assert format_duration(0) == "0:00"


def test_format_duration_with_hours() -> None:
    assert format_duration(3661) == "1:01:01"


def test_is_audio_longer_than_threshold() -> None:
    assert is_audio_longer_than_threshold(31 * 60, 30) is True
    assert is_audio_longer_than_threshold(30 * 60, 30) is False


def test_build_ffmpeg_convert_command() -> None:
    input_path = Path("/tmp/input.mp3")
    output_path = Path("/tmp/output.wav")
    command = build_ffmpeg_convert_command(input_path, output_path)

    assert command == [
        "ffmpeg",
        "-nostdin",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]


@patch("persian_asr_app.core.audio_utils.subprocess.run")
@patch("persian_asr_app.core.audio_utils.shutil.which", return_value="ffmpeg")
def test_convert_to_temp_wav_16k_mono_runs_ffmpeg(
    mock_which: MagicMock,
    mock_run: MagicMock,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.mp3"
    audio_file.write_bytes(b"ID3")

    def _write_output(*args, **kwargs):
        output_path = Path(args[0][-1])
        output_path.write_bytes(b"RIFF")
        return MagicMock(returncode=0)

    mock_run.side_effect = _write_output

    temp_path = convert_to_temp_wav_16k_mono(str(audio_file))

    assert temp_path.suffix == ".wav"
    assert temp_path.is_file()
    called_command = mock_run.call_args.args[0]
    assert called_command[0] == "ffmpeg"
    assert "-ac" in called_command
    assert "1" in called_command
    assert "-ar" in called_command
    assert "16000" in called_command

    temp_path.unlink(missing_ok=True)


@patch("persian_asr_app.core.audio_utils.shutil.which", return_value=None)
def test_convert_to_temp_wav_16k_mono_requires_ffmpeg(
    mock_which: MagicMock,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"RIFF")

    with pytest.raises(RuntimeError, match="ffmpeg not found"):
        convert_to_temp_wav_16k_mono(str(audio_file))


@patch("persian_asr_app.core.audio_utils._estimate_duration_librosa", return_value=42.5)
@patch("persian_asr_app.core.audio_utils._estimate_duration_ffprobe", return_value=None)
def test_estimate_audio_duration_falls_back_to_librosa(
    mock_ffprobe: MagicMock,
    mock_librosa: MagicMock,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"RIFF")

    duration = estimate_audio_duration(str(audio_file))

    assert duration == 42.5
    mock_ffprobe.assert_called_once()
    mock_librosa.assert_called_once()


@patch("persian_asr_app.core.audio_utils._estimate_duration_ffprobe", return_value=12.3)
def test_estimate_audio_duration_prefers_ffprobe(
    mock_ffprobe: MagicMock,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"RIFF")

    duration = estimate_audio_duration(str(audio_file))

    assert duration == 12.3
    mock_ffprobe.assert_called_once()
