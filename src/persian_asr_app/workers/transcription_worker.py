"""Background worker for running transcription off the UI thread."""

from PyQt6.QtCore import QObject, pyqtSignal

from persian_asr_app.core.asr_engine import ASREngine


class TranscriptionWorker(QObject):
    """Runs transcription in a background thread and emits results via signals."""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, engine: ASREngine, audio_path: str) -> None:
        super().__init__()
        self.engine = engine
        self.audio_path = audio_path

    def run(self) -> None:
        """Transcribe audio and emit the result or an error."""
        try:
            result = self.engine.transcribe(self.audio_path)
            self.finished.emit(result["text"])
        except Exception as exc:  # noqa: BLE001 — surface any failure to the UI
            self.error.emit(str(exc))
