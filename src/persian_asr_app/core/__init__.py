"""Core ASR and audio processing modules."""

from persian_asr_app.core.audio_utils import (
    ALLOWED_AUDIO_EXTENSIONS,
    SAMPLE_RATE,
    build_ffmpeg_convert_command,
    convert_to_temp_wav_16k_mono,
    ensure_mono,
    estimate_audio_duration,
    format_duration,
    is_audio_longer_than_threshold,
    load_audio,
    validate_audio_path,
)
from persian_asr_app.core.transcription_format import (
    format_display_text,
    format_export_text,
    format_processing_time,
    format_timestamp,
)

__all__ = [
    "ALLOWED_AUDIO_EXTENSIONS",
    "ASREngine",
    "SAMPLE_RATE",
    "build_ffmpeg_convert_command",
    "convert_to_temp_wav_16k_mono",
    "ensure_mono",
    "estimate_audio_duration",
    "format_display_text",
    "format_duration",
    "format_export_text",
    "format_processing_time",
    "format_timestamp",
    "is_audio_longer_than_threshold",
    "load_audio",
    "validate_audio_path",
]


def __getattr__(name: str):
    if name == "ASREngine":
        from persian_asr_app.core.asr_engine import ASREngine

        return ASREngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
