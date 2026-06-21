"""Audio loading and preprocessing utilities."""

from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000

ALLOWED_AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"})


def validate_audio_path(path: str) -> Path:
    """Validate that *path* points to a supported audio file and return its resolved path."""
    audio_path = Path(path).expanduser()

    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    extension = audio_path.suffix.lower()
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        supported = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        raise ValueError(
            f"Unsupported audio format '{extension}'. Supported formats: {supported}"
        )

    return audio_path.resolve()


def load_audio(path: str, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Load an audio file and return a mono float32 waveform at the target sample rate."""
    import librosa

    validated_path = validate_audio_path(path)
    waveform, _ = librosa.load(str(validated_path), sr=sample_rate, mono=True)
    return waveform.astype(np.float32)


def ensure_mono(waveform: np.ndarray) -> np.ndarray:
    """Convert a waveform to mono 1-D float32."""
    if waveform.ndim > 1:
        waveform = np.mean(waveform, axis=0)
    return waveform.astype(np.float32)
