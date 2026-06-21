"""Whisper-based automatic speech recognition engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from huggingface_hub.errors import GatedRepoError, HfHubHTTPError
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from persian_asr_app.app_logging import get_logger
from persian_asr_app.config import (
    ASR_BATCH_SIZE,
    CONVERT_TO_16K_MONO_WAV,
    DEFAULT_LANGUAGE,
    DEVICE,
    MODEL_ID,
    TORCH_NUM_THREADS,
)
from persian_asr_app.core.audio_utils import convert_to_temp_wav_16k_mono, validate_audio_path

TORCH_DTYPE = torch.float32

_logger = get_logger("asr_engine")
_torch_configured = False


def _configure_torch_runtime() -> None:
    """Apply one-time CPU runtime settings."""
    global _torch_configured  # noqa: PLW0603 — module-level init guard
    if _torch_configured:
        return

    if TORCH_NUM_THREADS is not None:
        torch.set_num_threads(TORCH_NUM_THREADS)
        _logger.info("torch.set_num_threads(%s)", TORCH_NUM_THREADS)

    _torch_configured = True


def _format_model_access_error(model_id: str, error: Exception) -> RuntimeError:
    """Build a clear error message for Hugging Face model access failures."""
    message = (
        f"Failed to load model '{model_id}'. "
        "If this is a gated model, authenticate with Hugging Face first:\n"
        "  1. Accept the model terms at https://huggingface.co/{model_id}\n"
        "  2. Run: huggingface-cli login\n"
        "     or set HF_TOKEN in your environment / .env file\n"
        f"Original error: {error}"
    )
    return RuntimeError(message)


class ASREngine:
    """CPU-first Whisper ASR engine backed by Hugging Face Transformers."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        device: str = DEVICE,
        language: str = DEFAULT_LANGUAGE,
        return_timestamps: bool = False,
        convert_to_16k_mono_wav: bool = CONVERT_TO_16K_MONO_WAV,
        batch_size: int = ASR_BATCH_SIZE,
    ) -> None:
        self.model_id = model_id
        self.device = device
        self.language = language
        self.return_timestamps = return_timestamps
        self.convert_to_16k_mono_wav = convert_to_16k_mono_wav
        self.batch_size = batch_size
        self._pipe: Any | None = None

    @property
    def is_loaded(self) -> bool:
        return self._pipe is not None

    def load_model(self) -> None:
        """Load the model and processor into memory (cached after first call)."""
        if self._pipe is not None:
            return

        _configure_torch_runtime()
        _logger.info("Model load started: %s (device=%s)", self.model_id, self.device)

        try:
            processor = AutoProcessor.from_pretrained(self.model_id)
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_id,
                torch_dtype=TORCH_DTYPE,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            model.to(self.device)

            self._pipe = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                dtype=TORCH_DTYPE,
                device=self.device,
            )
        except GatedRepoError as exc:
            _logger.exception("Model load failed (gated repo): %s", self.model_id)
            raise _format_model_access_error(self.model_id, exc) from exc
        except HfHubHTTPError as exc:
            _logger.exception("Model load failed (hub HTTP): %s", self.model_id)
            if exc.response is not None and exc.response.status_code in {401, 403}:
                raise _format_model_access_error(self.model_id, exc) from exc
            raise RuntimeError(
                f"Failed to download model '{self.model_id}': {exc}"
            ) from exc
        except OSError as exc:
            _logger.exception("Model load failed (OS error): %s", self.model_id)
            error_text = str(exc).lower()
            if "gated" in error_text or "401" in error_text or "403" in error_text:
                raise _format_model_access_error(self.model_id, exc) from exc
            raise RuntimeError(
                f"Failed to load model '{self.model_id}': {exc}"
            ) from exc
        except Exception:
            _logger.exception("Model load failed: %s", self.model_id)
            raise
        else:
            _logger.info("Model load finished: %s", self.model_id)

    def transcribe(self, audio_path: str) -> dict[str, Any]:
        """Transcribe an audio file and return structured results."""
        validated_path = validate_audio_path(audio_path)
        self.load_model()

        assert self._pipe is not None  # noqa: S101 — guaranteed after load_model

        temp_path: Path | None = None
        inference_path = validated_path

        _logger.info(
            "Transcription started: %s (normalize=%s, batch_size=%s)",
            validated_path,
            self.convert_to_16k_mono_wav,
            self.batch_size,
        )

        try:
            if self.convert_to_16k_mono_wav:
                temp_path = convert_to_temp_wav_16k_mono(str(validated_path))
                inference_path = temp_path
                _logger.info("Using normalized temp WAV: %s", temp_path)

            result = self._pipe(
                str(inference_path),
                batch_size=self.batch_size,
                return_timestamps=self.return_timestamps,
                generate_kwargs={
                    "language": self.language,
                    "task": "transcribe",
                    "condition_on_prev_tokens": False,
                },
            )
        except Exception:
            _logger.exception("Transcription failed: %s", validated_path)
            raise
        else:
            _logger.info("Transcription finished: %s", validated_path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
                _logger.debug("Removed temp WAV: %s", temp_path)

        response: dict[str, Any] = {
            "text": result["text"].strip(),
            "audio_path": str(validated_path),
            "model_id": self.model_id,
        }

        if self.return_timestamps and "chunks" in result:
            response["chunks"] = result["chunks"]

        return response
