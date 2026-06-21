# Phase 00 — Project Setup

This phase establishes the initial project skeleton for the Persian ASR desktop application.

## Goals

- Create a maintainable **src-layout** Python package (`persian_asr_app`).
- Separate **ASR core** logic from **UI** and **background workers**.
- Default to **CPU** inference (`DEVICE=cpu`, `TORCH_DTYPE=float32`).
- Wire up dependencies, tests, linting, and documentation.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  main.py (entry point)                                  │
└──────────────────────────┬──────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ui/main_window    workers/           config.py
   (Phase 1+)        transcription_worker
                           │
                           ▼
                     core/asr_engine
                           │
                           ▼
                     core/audio_utils
```

### Layer responsibilities

| Layer | Module | Responsibility |
|-------|--------|----------------|
| Config | `config.py` | Model ID, device, dtype, language; loads `.env` |
| Core | `core/asr_engine.py` | Load Whisper model; transcribe audio |
| Core | `core/audio_utils.py` | Load/resample audio to 16 kHz mono |
| Workers | `workers/transcription_worker.py` | Run transcription off the UI thread (PyQt signals) |
| UI | `ui/main_window.py` | Desktop interface (placeholder in Phase 0) |

The UI must not import heavy model code at module level in future phases; workers call into `ASREngine` on a background thread.

## Configuration

Settings live in `config.py` and can be overridden via environment variables or `.env`:

```python
MODEL_ID = "C1Tech/whisper_small_persian"
DEVICE = "cpu"
TORCH_DTYPE = "float32"
DEFAULT_LANGUAGE = "fa"
```

## ASR engine

`ASREngine` in `core/asr_engine.py`:

1. Loads `AutoProcessor` and `AutoModelForSpeechSeq2Seq` from Hugging Face.
2. Builds a Transformers ASR `pipeline` on the configured device.
3. Accepts a file path or numpy waveform and returns transcribed Persian text.

Model weights are downloaded on first `load()`; ensure Hugging Face authentication is configured if the model is gated.

## Testing strategy

- **`test_audio_utils.py`** — unit tests for mono conversion and constants (no model download).
- **`test_asr_engine.py`** — mocks Transformers pipeline/model loading; verifies transcribe flow without GPU or network.

Run:

```bash
pytest
```

## Tooling

| Tool | Purpose |
|------|---------|
| `pytest` | Unit tests |
| `ruff` | Linting and import sorting |
| `python-dotenv` | Load `.env` at startup |

## Phase 0 deliverables

- [x] `pyproject.toml` with runtime and dev dependencies
- [x] src-layout package structure
- [x] CPU-first `ASREngine` and `audio_utils`
- [x] Worker stub with PyQt signals
- [x] UI placeholder module
- [x] Minimal `main.py` startup message
- [x] README setup instructions
- [x] Initial unit tests

## Next phase (Phase 01 — UI)

Planned work:

- Implement `MainWindow` with file picker and transcript display
- Connect `TranscriptionWorker` via `QThread`
- Show loading/progress states during model load and transcription
- Optional: record-from-microphone support

## Setup checklist

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -e ".[dev]"`
3. `sudo apt install -y ffmpeg` (Ubuntu)
4. `huggingface-cli login` (if required)
5. `cp .env.example .env` (optional)
6. `python -m persian_asr_app.main`
7. `pytest`
