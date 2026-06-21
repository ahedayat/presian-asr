"""Background worker for loading the ASR model off the UI thread."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from persian_asr_app.core.asr_engine import ASREngine


class ModelLoadWorker(QObject):
    """Loads the ASR model in a background thread and emits status via signals."""

    started = pyqtSignal()
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, engine: ASREngine) -> None:
        super().__init__()
        self.engine = engine

    def run(self) -> None:
        """Load the model and emit progress, success, or failure."""
        self.started.emit()
        try:
            self.progress.emit("در حال بارگذاری مدل...")
            self.engine.load_model()
            self.finished.emit()
        except Exception as exc:  # noqa: BLE001 — surface any failure to the UI
            self.failed.emit(str(exc))
