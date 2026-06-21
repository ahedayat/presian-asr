"""Tests for transcription formatting helpers."""

from __future__ import annotations

from persian_asr_app.core.transcription_format import (
    format_chunk_line,
    format_display_text,
    format_export_text,
    format_processing_time,
    format_timestamp,
)


def test_format_timestamp() -> None:
    assert format_timestamp(0.0) == "00:00.00"
    assert format_timestamp(1.2) == "00:01.20"
    assert format_timestamp(61.5) == "01:01.50"


def test_format_chunk_line() -> None:
    chunk = {"text": "سلام", "timestamp": (1.2, 3.5)}
    assert format_chunk_line(chunk) == "[00:01.20 - 00:03.50] سلام"


def test_format_chunk_line_without_timestamp() -> None:
    chunk = {"text": "سلام"}
    assert format_chunk_line(chunk) == "سلام"


def test_format_display_text_plain() -> None:
    result = {"text": "سلام دنیا"}
    assert format_display_text(result) == "سلام دنیا"


def test_format_display_text_with_chunks() -> None:
    result = {
        "text": "سلام دنیا",
        "chunks": [
            {"text": "سلام", "timestamp": (0.0, 1.0)},
            {"text": "دنیا", "timestamp": (1.0, 2.5)},
        ],
    }
    assert format_display_text(result) == (
        "[00:00.00 - 00:01.00] سلام\n"
        "[00:01.00 - 00:02.50] دنیا"
    )


def test_format_display_text_falls_back_when_chunks_empty() -> None:
    result = {"text": "سلام", "chunks": []}
    assert format_display_text(result) == "سلام"


def test_format_processing_time() -> None:
    assert format_processing_time(12.34) == "12.3 ثانیه"


def test_format_export_text_includes_metadata() -> None:
    result = {
        "text": "سلام",
        "audio_path": "/tmp/sample.wav",
        "model_id": "C1Tech/whisper_small_persian",
    }
    content = format_export_text(result, processing_time=5.0)
    assert "فایل صوتی: /tmp/sample.wav" in content
    assert "مدل: C1Tech/whisper_small_persian" in content
    assert "زمان پردازش: 5.0 ثانیه" in content
    assert content.endswith("سلام")
