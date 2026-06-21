"""Background worker for running transcription off the UI thread."""

from __future__ import annotations

import time
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from persian_asr_app.core.asr_engine import ASREngine


class TranscriptionWorker(QObject):
    """Runs transcription in a background thread and emits results via signals."""

    started = pyqtSignal()
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(
        self,
        audio_path: str,
        engine: ASREngine | None = None,
        return_timestamps: bool = False,
    ) -> None:
        super().__init__()
        self.audio_path = audio_path
        self.engine = engine or ASREngine()
        self.return_timestamps = return_timestamps

    def run(self) -> None:
        """Transcribe audio and emit progress, result, or failure."""
        self.started.emit()
        try:
            self.progress.emit("در حال آماده‌سازی مدل...")
            self.engine.return_timestamps = self.return_timestamps
            self.progress.emit("در حال تبدیل گفتار به متن...")
            start = time.perf_counter()
            result: dict[str, Any] = self.engine.transcribe(self.audio_path)
            result["processing_time"] = time.perf_counter() - start
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 — surface any failure to the UI
            self.failed.emit(str(exc))
