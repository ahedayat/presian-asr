"""Tests for the ASR engine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from persian_asr_app.core.asr_engine import ASREngine, _resolve_dtype


def test_resolve_dtype_defaults_to_float32() -> None:
    import torch

    assert _resolve_dtype("float32") == torch.float32
    assert _resolve_dtype("unknown") == torch.float32


def test_engine_not_loaded_raises() -> None:
    engine = ASREngine()
    with pytest.raises(RuntimeError, match="not loaded"):
        engine.transcribe(np.zeros(16000, dtype=np.float32))


def test_engine_is_loaded_flag() -> None:
    engine = ASREngine()
    assert engine.is_loaded is False


@patch("persian_asr_app.core.asr_engine.pipeline")
@patch("persian_asr_app.core.asr_engine.AutoModelForSpeechSeq2Seq")
@patch("persian_asr_app.core.asr_engine.AutoProcessor")
def test_transcribe_numpy_waveform(
    mock_processor_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_pipeline: MagicMock,
) -> None:
    mock_pipe = MagicMock(return_value={"text": "  سلام  "})
    mock_pipeline.return_value = mock_pipe

    engine = ASREngine()
    engine.load()

    waveform = np.zeros(16000, dtype=np.float32)
    text = engine.transcribe(waveform)

    assert text == "سلام"
    mock_pipe.assert_called_once()
    call_args = mock_pipe.call_args
    assert call_args[0][0]["sampling_rate"] == 16000
    assert call_args[1]["generate_kwargs"]["language"] == "fa"


@patch("persian_asr_app.core.asr_engine.pipeline")
@patch("persian_asr_app.core.asr_engine.AutoModelForSpeechSeq2Seq")
@patch("persian_asr_app.core.asr_engine.AutoProcessor")
@patch("persian_asr_app.core.asr_engine.load_audio")
def test_transcribe_file_path(
    mock_load_audio: MagicMock,
    mock_processor_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_pipeline: MagicMock,
) -> None:
    mock_load_audio.return_value = np.zeros(16000, dtype=np.float32)
    mock_pipe = MagicMock(return_value={"text": "test"})
    mock_pipeline.return_value = mock_pipe

    engine = ASREngine()
    engine.load()
    text = engine.transcribe(Path("/tmp/sample.wav"))

    assert text == "test"
    mock_load_audio.assert_called_once_with("/tmp/sample.wav")
