"""Tests for the background model-load worker."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import QCoreApplication

from persian_asr_app.workers.model_load_worker import ModelLoadWorker


@pytest.fixture(scope="session")
def qcoreapp() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    return app


def test_model_load_worker_emits_finished_on_success(qcoreapp: QCoreApplication) -> None:
    engine = MagicMock()
    engine.load_model.return_value = None

    worker = ModelLoadWorker(engine)
    finished_events: list[bool] = []
    worker.finished.connect(lambda: finished_events.append(True))

    worker.run()

    engine.load_model.assert_called_once()
    assert finished_events == [True]


def test_model_load_worker_emits_failed_on_error(qcoreapp: QCoreApplication) -> None:
    engine = MagicMock()
    engine.load_model.side_effect = RuntimeError("load failed")

    worker = ModelLoadWorker(engine)
    failed_messages: list[str] = []
    worker.failed.connect(failed_messages.append)

    worker.run()

    assert failed_messages == ["load failed"]


def test_model_load_worker_emits_started_and_progress(qcoreapp: QCoreApplication) -> None:
    engine = MagicMock()

    worker = ModelLoadWorker(engine)
    started_events: list[bool] = []
    progress_messages: list[str] = []

    worker.started.connect(lambda: started_events.append(True))
    worker.progress.connect(progress_messages.append)
    worker.run()

    assert started_events == [True]
    assert progress_messages == ["در حال بارگذاری مدل..."]
