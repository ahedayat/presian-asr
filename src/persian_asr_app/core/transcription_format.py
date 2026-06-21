"""Pure-Python helpers for formatting transcription results (no PyQt dependency)."""

from __future__ import annotations

from typing import Any


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS.ss (e.g. 61.2 -> '01:01.20')."""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"


def format_chunk_line(chunk: dict[str, Any]) -> str:
    """Format a single chunk as '[start - end] text'."""
    text = chunk.get("text", "").strip()
    timestamp = chunk.get("timestamp")
    if not timestamp or len(timestamp) != 2:
        return text
    start, end = timestamp
    return f"[{format_timestamp(start)} - {format_timestamp(end)}] {text}"


def format_display_text(result: dict[str, Any]) -> str:
    """Build user-facing text from a transcription result.

    Uses timestamped chunks when available; otherwise returns plain text.
    """
    chunks = result.get("chunks")
    if chunks:
        lines = [format_chunk_line(chunk) for chunk in chunks]
        body = "\n".join(line for line in lines if line)
        if body:
            return body
    return result.get("text", "")


def format_processing_time(seconds: float) -> str:
    """Format processing duration for display (one decimal place)."""
    return f"{seconds:.1f} ثانیه"


def format_export_text(
    result: dict[str, Any],
    processing_time: float | None = None,
) -> str:
    """Build UTF-8 export content with optional metadata header."""
    lines: list[str] = [
        "--- Persian ASR ---",
        f"فایل صوتی: {result.get('audio_path', '')}",
        f"مدل: {result.get('model_id', '')}",
    ]
    if processing_time is not None:
        lines.append(f"زمان پردازش: {format_processing_time(processing_time)}")
    lines.extend(["---", "", format_display_text(result)])
    return "\n".join(lines)
