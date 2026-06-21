"""Tests for the ASR engine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from persian_asr_app.core.asr_engine import ASREngine


def test_engine_not_loaded_before_transcribe() -> None:
    engine = ASREngine()
    assert engine.is_loaded is False


@patch("persian_asr_app.core.asr_engine.pipeline")
@patch("persian_asr_app.core.asr_engine.AutoModelForSpeechSeq2Seq")
@patch("persian_asr_app.core.asr_engine.AutoProcessor")
def test_load_model_caches_pipeline(
    mock_processor_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_pipeline: MagicMock,
) -> None:
    mock_pipeline.return_value = MagicMock()

    engine = ASREngine()
    engine.load_model()
    engine.load_model()

    mock_processor_cls.from_pretrained.assert_called_once()
    mock_model_cls.from_pretrained.assert_called_once()
    mock_pipeline.assert_called_once()


@patch("persian_asr_app.core.asr_engine.convert_to_temp_wav_16k_mono")
@patch("persian_asr_app.core.asr_engine.pipeline")
@patch("persian_asr_app.core.asr_engine.AutoModelForSpeechSeq2Seq")
@patch("persian_asr_app.core.asr_engine.AutoProcessor")
def test_transcribe_returns_structured_result(
    mock_processor_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_pipeline: MagicMock,
    mock_convert: MagicMock,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"RIFF")

    mock_pipe = MagicMock(return_value={"text": "  سلام  "})
    mock_pipeline.return_value = mock_pipe

    engine = ASREngine(model_id="C1Tech/whisper_small_persian", convert_to_16k_mono_wav=False)
    result = engine.transcribe(str(audio_file))

    assert result == {
        "text": "سلام",
        "audio_path": str(audio_file.resolve()),
        "model_id": "C1Tech/whisper_small_persian",
    }
    mock_pipe.assert_called_once()
    mock_convert.assert_not_called()
    call_kwargs = mock_pipe.call_args.kwargs
    assert call_kwargs["return_timestamps"] is False
    assert call_kwargs["batch_size"] == 1
    assert call_kwargs["generate_kwargs"] == {
        "language": "fa",
        "task": "transcribe",
        "condition_on_prev_tokens": False,
    }


@patch("persian_asr_app.core.asr_engine.convert_to_temp_wav_16k_mono")
@patch("persian_asr_app.core.asr_engine.pipeline")
@patch("persian_asr_app.core.asr_engine.AutoModelForSpeechSeq2Seq")
@patch("persian_asr_app.core.asr_engine.AutoProcessor")
def test_transcribe_uses_temp_wav_when_normalization_enabled(
    mock_processor_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_pipeline: MagicMock,
    mock_convert: MagicMock,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.mp3"
    audio_file.write_bytes(b"ID3")
    temp_wav = tmp_path / "temp.wav"
    temp_wav.write_bytes(b"RIFF")
    mock_convert.return_value = temp_wav

    mock_pipe = MagicMock(return_value={"text": "سلام"})
    mock_pipeline.return_value = mock_pipe

    engine = ASREngine(convert_to_16k_mono_wav=True)
    engine.transcribe(str(audio_file))

    mock_convert.assert_called_once_with(str(audio_file.resolve()))
    mock_pipe.assert_called_once_with(
        str(temp_wav),
        batch_size=1,
        return_timestamps=False,
        generate_kwargs={
            "language": "fa",
            "task": "transcribe",
            "condition_on_prev_tokens": False,
        },
    )
    assert not temp_wav.exists()


@patch("persian_asr_app.core.asr_engine.convert_to_temp_wav_16k_mono")
@patch("persian_asr_app.core.asr_engine.pipeline")
@patch("persian_asr_app.core.asr_engine.AutoModelForSpeechSeq2Seq")
@patch("persian_asr_app.core.asr_engine.AutoProcessor")
def test_transcribe_includes_chunks_when_timestamps_enabled(
    mock_processor_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_pipeline: MagicMock,
    mock_convert: MagicMock,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.mp3"
    audio_file.write_bytes(b"ID3")

    chunks = [{"text": "سلام", "timestamp": (0.0, 1.0)}]
    mock_pipe = MagicMock(return_value={"text": "سلام", "chunks": chunks})
    mock_pipeline.return_value = mock_pipe

    engine = ASREngine(return_timestamps=True, convert_to_16k_mono_wav=False)
    result = engine.transcribe(str(audio_file))

    assert result["text"] == "سلام"
    assert result["chunks"] == chunks


@patch("persian_asr_app.core.asr_engine.AutoProcessor")
def test_load_model_gated_repo_error(mock_processor_cls: MagicMock) -> None:
    from huggingface_hub.errors import GatedRepoError

    mock_processor_cls.from_pretrained.side_effect = GatedRepoError(
        "403 Client Error",
        response=MagicMock(status_code=403),
    )

    engine = ASREngine()
    with pytest.raises(RuntimeError, match="gated model"):
        engine.load_model()


@patch("persian_asr_app.core.asr_engine.pipeline")
@patch("persian_asr_app.core.asr_engine.AutoModelForSpeechSeq2Seq")
@patch("persian_asr_app.core.asr_engine.AutoProcessor")
def test_model_loaded_with_cpu_float32_settings(
    mock_processor_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_pipeline: MagicMock,
) -> None:
    import torch

    engine = ASREngine(device="cpu")
    engine.load_model()

    mock_model_cls.from_pretrained.assert_called_once_with(
        engine.model_id,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    )
    mock_pipeline.assert_called_once()
    pipeline_kwargs = mock_pipeline.call_args.kwargs
    assert pipeline_kwargs["device"] == "cpu"
    assert pipeline_kwargs["dtype"] == torch.float32
