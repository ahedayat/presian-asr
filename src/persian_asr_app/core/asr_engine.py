"""Whisper-based automatic speech recognition engine."""

from __future__ import annotations

from typing import Any

import torch
from huggingface_hub.errors import GatedRepoError, HfHubHTTPError
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from persian_asr_app.config import DEFAULT_LANGUAGE, DEVICE, MODEL_ID
from persian_asr_app.core.audio_utils import validate_audio_path

TORCH_DTYPE = torch.float32


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
    ) -> None:
        self.model_id = model_id
        self.device = device
        self.language = language
        self.return_timestamps = return_timestamps
        self._pipe: Any | None = None

    @property
    def is_loaded(self) -> bool:
        return self._pipe is not None

    def load_model(self) -> None:
        """Load the model and processor into memory (cached after first call)."""
        if self._pipe is not None:
            return

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
            raise _format_model_access_error(self.model_id, exc) from exc
        except HfHubHTTPError as exc:
            if exc.response is not None and exc.response.status_code in {401, 403}:
                raise _format_model_access_error(self.model_id, exc) from exc
            raise RuntimeError(
                f"Failed to download model '{self.model_id}': {exc}"
            ) from exc
        except OSError as exc:
            error_text = str(exc).lower()
            if "gated" in error_text or "401" in error_text or "403" in error_text:
                raise _format_model_access_error(self.model_id, exc) from exc
            raise RuntimeError(
                f"Failed to load model '{self.model_id}': {exc}"
            ) from exc

    def transcribe(self, audio_path: str) -> dict[str, Any]:
        """Transcribe an audio file and return structured results."""
        validated_path = validate_audio_path(audio_path)
        self.load_model()

        assert self._pipe is not None  # noqa: S101 — guaranteed after load_model

        result = self._pipe(
            str(validated_path),
            return_timestamps=self.return_timestamps,
            generate_kwargs={
                "language": self.language,
                "task": "transcribe",
                "condition_on_prev_tokens": False,
            },
        )

        response: dict[str, Any] = {
            "text": result["text"].strip(),
            "audio_path": str(validated_path),
            "model_id": self.model_id,
        }

        if self.return_timestamps and "chunks" in result:
            response["chunks"] = result["chunks"]

        return response
