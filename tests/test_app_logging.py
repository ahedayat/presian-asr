"""Tests for application logging."""

import logging
from pathlib import Path

from persian_asr_app.app_logging import LOGGER_NAME, get_logger, setup_logging


def test_setup_logging_writes_to_file(tmp_path: Path) -> None:
    root_logger = logging.getLogger(LOGGER_NAME)
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    logger = setup_logging(log_dir=tmp_path)

    logger.info("model load started")
    logger.info("transcription finished for /tmp/sample.wav")

    log_file = tmp_path / "persian_asr.log"
    assert log_file.is_file()
    content = log_file.read_text(encoding="utf-8")
    assert "model load started" in content
    assert "transcription finished" in content


def test_get_logger_uses_app_namespace() -> None:
    logger = get_logger("test")
    assert logger.name == f"{LOGGER_NAME}.test"
