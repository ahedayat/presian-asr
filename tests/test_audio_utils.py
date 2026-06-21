"""Tests for audio utility functions."""

from pathlib import Path

import numpy as np
import pytest

from persian_asr_app.core.audio_utils import SAMPLE_RATE, ensure_mono, validate_audio_path


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


def test_validate_audio_path_accepts_supported_extension(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"RIFF")
    resolved = validate_audio_path(str(audio_file))
    assert resolved == audio_file.resolve()
