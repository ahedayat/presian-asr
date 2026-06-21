"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL_ID = os.getenv("MODEL_ID", "C1Tech/whisper_small_persian")
DEVICE = os.getenv("DEVICE", "cpu")
TORCH_DTYPE = os.getenv("TORCH_DTYPE", "float32")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "fa")

# CPU performance: batch_size=1 is safest for desktop CPU inference.
ASR_BATCH_SIZE = int(os.getenv("ASR_BATCH_SIZE", "1"))

# Optional cap on PyTorch intra-op threads (empty = PyTorch default).
_torch_threads_raw = os.getenv("TORCH_NUM_THREADS", "").strip()
TORCH_NUM_THREADS: int | None = int(_torch_threads_raw) if _torch_threads_raw else None

# Normalize input audio to 16 kHz mono WAV via ffmpeg before inference.
CONVERT_TO_16K_MONO_WAV = os.getenv("CONVERT_TO_16K_MONO_WAV", "true").lower() in {
    "1",
    "true",
    "yes",
}

# Warn in the UI when audio exceeds this many minutes.
LONG_AUDIO_THRESHOLD_MINUTES = float(os.getenv("LONG_AUDIO_THRESHOLD_MINUTES", "30"))

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
