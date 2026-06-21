"""Audio loading and preprocessing utilities."""

import numpy as np

SAMPLE_RATE = 16000


def load_audio(path: str, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Load an audio file and return a mono float32 waveform at the target sample rate."""
    import librosa

    waveform, _ = librosa.load(path, sr=sample_rate, mono=True)
    return waveform.astype(np.float32)


def ensure_mono(waveform: np.ndarray) -> np.ndarray:
    """Convert a waveform to mono 1-D float32."""
    if waveform.ndim > 1:
        waveform = np.mean(waveform, axis=0)
    return waveform.astype(np.float32)
