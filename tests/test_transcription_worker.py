"""Tests for the background transcription worker."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import QCoreApplication

from persian_asr_app.workers.transcription_worker import TranscriptionWorker


@pytest.fixture(scope="session")
def qcoreapp() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    return app


def test_worker_emits_finished_on_success(qcoreapp: QCoreApplication) -> None:
    engine = MagicMock()
    engine.transcribe.return_value = {
        "text": "سلام",
        "audio_path": "/tmp/sample.wav",
        "model_id": "test-model",
    }

    worker = TranscriptionWorker("/tmp/sample.wav", engine=engine)
    finished_results: list[dict] = []
    worker.finished.connect(finished_results.append)

    worker.run()

    engine.transcribe.assert_called_once_with("/tmp/sample.wav")
    assert finished_results == [
        {
            "text": "سلام",
            "audio_path": "/tmp/sample.wav",
            "model_id": "test-model",
        }
    ]


def test_worker_emits_failed_on_error(qcoreapp: QCoreApplication) -> None:
    engine = MagicMock()
    engine.transcribe.side_effect = RuntimeError("transcription failed")

    worker = TranscriptionWorker("/tmp/sample.wav", engine=engine)
    failed_messages: list[str] = []
    worker.failed.connect(failed_messages.append)

    worker.run()

    assert failed_messages == ["transcription failed"]


def test_worker_emits_started_and_progress(qcoreapp: QCoreApplication) -> None:
    engine = MagicMock()
    engine.transcribe.return_value = {"text": "ok", "audio_path": "/tmp/a.wav", "model_id": "m"}

    worker = TranscriptionWorker("/tmp/a.wav", engine=engine)
    started_events: list[bool] = []
    progress_messages: list[str] = []

    worker.started.connect(lambda: started_events.append(True))
    worker.progress.connect(progress_messages.append)
    worker.run()

    assert started_events == [True]
    assert progress_messages == [
        "در حال آماده‌سازی مدل...",
        "در حال تبدیل گفتار به متن...",
    ]
