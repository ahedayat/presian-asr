"""Tests for audio utility functions."""

import numpy as np

from persian_asr_app.core.audio_utils import SAMPLE_RATE, ensure_mono


def test_sample_rate_is_whisper_default() -> None:
    assert SAMPLE_RATE == 16000


def test_ensure_mono_from_stereo() -> None:
    stereo = np.array([[1.0, 0.0], [0.5, 0.5]], dtype=np.float32)
    mono = ensure_mono(stereo)
    assert mono.ndim == 1
    assert mono.shape[0] == 2
    np.testing.assert_allclose(mono, [0.5, 0.25])


def test_ensure_mono_preserves_1d_array() -> None:
    mono_input = np.array([0.1, 0.2, 0.3], dtype=np.float64)
    result = ensure_mono(mono_input)
    assert result.dtype == np.float32
    np.testing.assert_allclose(result, mono_input, rtol=1e-6)
