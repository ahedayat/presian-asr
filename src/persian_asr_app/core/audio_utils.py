"""Audio loading and preprocessing utilities."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
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


def estimate_audio_duration(path: str) -> float | None:
    """Estimate audio duration in seconds using ffprobe, with librosa as fallback."""
    validated_path = validate_audio_path(path)
    duration = _estimate_duration_ffprobe(validated_path)
    if duration is not None:
        return duration
    return _estimate_duration_librosa(validated_path)


def _estimate_duration_ffprobe(audio_path: Path) -> float | None:
    if shutil.which("ffprobe") is None:
        return None

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        duration = float(result.stdout.strip())
        if duration >= 0:
            return duration
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return None


def _estimate_duration_librosa(audio_path: Path) -> float | None:
    try:
        import librosa
    except ImportError:
        return None

    try:
        return float(librosa.get_duration(path=str(audio_path)))
    except Exception:
        return None


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as MM:SS or H:MM:SS."""
    total_seconds = max(0, int(round(seconds)))
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def is_audio_longer_than_threshold(duration_seconds: float, threshold_minutes: float) -> bool:
    """Return True when *duration_seconds* exceeds *threshold_minutes*."""
    return duration_seconds > threshold_minutes * 60


def build_ffmpeg_convert_command(input_path: Path, output_path: Path) -> list[str]:
    """Build the ffmpeg command for converting audio to 16 kHz mono PCM WAV."""
    return [
        "ffmpeg",
        "-nostdin",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]


def convert_to_temp_wav_16k_mono(input_path: str) -> Path:
    """Convert *input_path* to a temporary 16 kHz mono WAV file and return its path."""
    validated_path = validate_audio_path(input_path)

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found. Install ffmpeg to normalize audio for transcription."
        )

    fd, temp_name = tempfile.mkstemp(suffix=".wav", prefix="persian_asr_")
    os.close(fd)
    temp_path = Path(temp_name)
    command = build_ffmpeg_convert_command(validated_path, temp_path)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=600,
        )
    except subprocess.CalledProcessError as exc:
        temp_path.unlink(missing_ok=True)
        stderr = (exc.stderr or "").strip()
        detail = stderr or str(exc)
        raise RuntimeError(f"ffmpeg conversion failed: {detail}") from exc
    except subprocess.TimeoutExpired as exc:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError("ffmpeg conversion timed out after 10 minutes.") from exc
    except OSError as exc:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg conversion failed: {exc}") from exc
    else:
        del result

    if not temp_path.is_file() or temp_path.stat().st_size == 0:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError("ffmpeg conversion produced an empty output file.")

    return temp_path


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
