"""Whisper-based automatic speech recognition engine."""

from pathlib import Path
from typing import Union

import numpy as np
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from persian_asr_app.config import DEFAULT_LANGUAGE, DEVICE, MODEL_ID, TORCH_DTYPE
from persian_asr_app.core.audio_utils import SAMPLE_RATE, ensure_mono, load_audio


def _resolve_dtype(dtype_name: str) -> torch.dtype:
    mapping = {
        "float32": torch.float32,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
    }
    return mapping.get(dtype_name.lower(), torch.float32)


class ASREngine:
    """CPU-first Whisper ASR engine backed by Hugging Face Transformers."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        device: str = DEVICE,
        torch_dtype_name: str = TORCH_DTYPE,
        language: str = DEFAULT_LANGUAGE,
    ) -> None:
        self.model_id = model_id
        self.device = device
        self.torch_dtype = _resolve_dtype(torch_dtype_name)
        self.language = language
        self._pipe = None

    def load(self) -> None:
        """Load the model and processor into memory."""
        if self._pipe is not None:
            return

        processor = AutoProcessor.from_pretrained(self.model_id)
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_id,
            torch_dtype=self.torch_dtype,
            low_cpu_mem_usage=True,
        )
        model.to(self.device)

        self._pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            dtype=self.torch_dtype,
            device=self.device,
        )

    @property
    def is_loaded(self) -> bool:
        return self._pipe is not None

    def transcribe(self, audio: Union[str, Path, np.ndarray]) -> str:
        """Transcribe audio from a file path or numpy waveform."""
        if self._pipe is None:
            raise RuntimeError("ASR engine not loaded. Call load() first.")

        if isinstance(audio, (str, Path)):
            waveform = load_audio(str(audio))
        else:
            waveform = ensure_mono(audio)

        result = self._pipe(
            {"raw": waveform, "sampling_rate": SAMPLE_RATE},
            generate_kwargs={"language": self.language, "task": "transcribe"},
        )
        return result["text"].strip()
