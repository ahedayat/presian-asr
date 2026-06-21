"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL_ID = os.getenv("MODEL_ID", "C1Tech/whisper_small_persian")
DEVICE = os.getenv("DEVICE", "cpu")
TORCH_DTYPE = os.getenv("TORCH_DTYPE", "float32")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "fa")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
