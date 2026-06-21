# Phase 01 — CLI ASR Engine

This phase implements the core automatic speech recognition (ASR) engine and a command-line interface for transcription. No PyQt UI is included yet.

## Goals

- Provide a **testable, CPU-first** ASR core independent of the desktop UI.
- Transcribe Persian audio via CLI: `python -m persian_asr_app.main --audio path/to/file.mp3`.
- Validate audio inputs and surface clear errors for missing files, unsupported formats, and gated Hugging Face models.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  main.py (CLI entry point)                              │
│    --audio path/to/file.mp3  →  print transcription     │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
                     core/asr_engine.py
                     ASREngine.load_model()  (lazy, cached)
                     ASREngine.transcribe()   → dict
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        config.py                 audio_utils.py
     MODEL_ID, DEVICE,           validate_audio_path()
     DEFAULT_LANGUAGE             load_audio() (helpers)
              │
              ▼
   Hugging Face Transformers
   AutoProcessor + AutoModelForSpeechSeq2Seq + pipeline
   Model: C1Tech/whisper_small_persian
```

### Layer responsibilities

| Module | Responsibility |
|--------|----------------|
| `config.py` | Default model ID, device (`cpu`), language (`fa`); loads `.env` |
| `core/asr_engine.py` | Lazy model load; run ASR pipeline; return structured dict |
| `core/audio_utils.py` | Validate file paths and extensions; audio loading helpers |
| `main.py` | CLI argument parsing and transcription output |

The PyQt worker (`workers/transcription_worker.py`) will call `ASREngine.transcribe()` in a later UI phase without importing heavy model code at module level in the UI layer.

## CPU-first decision

Inference defaults to **CPU** with **`torch.float32`**:

- Predictable behavior on machines without a GPU.
- No automatic CUDA detection — the engine never switches to GPU on its own.
- Model loading uses `low_cpu_mem_usage=True` and `use_safetensors=True` to reduce peak RAM during load.

These defaults can be overridden via environment variables in `config.py` (`DEVICE`, `MODEL_ID`), but the implementation does not add GPU-specific code paths.

## Model and generation settings

- **Model:** `C1Tech/whisper_small_persian` (Whisper small fine-tuned for Persian)
- **Pipeline task:** `automatic-speech-recognition`
- **Generate kwargs:**
  - `language="fa"`
  - `task="transcribe"`
  - `condition_on_prev_tokens=False`

## Transcription result

`ASREngine.transcribe(audio_path)` returns:

```python
{
    "text": str,           # stripped transcription
    "chunks": list | None, # present when return_timestamps=True
    "audio_path": str,     # resolved absolute path
    "model_id": str,
}
```

The model is loaded on the first `transcribe()` call (or an explicit `load_model()`) and cached on the engine instance.

## ffmpeg dependency

Non-WAV formats (`.mp3`, `.m4a`, `.flac`, `.ogg`, `.aac`) require **ffmpeg** for decoding. Install on Ubuntu:

```bash
sudo apt update
sudo apt install -y ffmpeg
```

Without ffmpeg, loading compressed audio may fail at runtime even when the file extension is valid.

## Supported audio formats

`.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.aac`

Validation happens in `validate_audio_path()` before transcription starts.

## Hugging Face authentication

If the model is gated, accept the license on the model page and authenticate:

```bash
huggingface-cli login
```

Or set `HF_TOKEN` in `.env`. Without access, `load_model()` raises a `RuntimeError` with setup instructions.

## CLI usage

Transcribe a file:

```bash
python -m persian_asr_app.main --audio path/to/audio.mp3
```

Or after installation:

```bash
persian-asr --audio path/to/audio.mp3
```

Without `--audio`, the app prints a short message that the desktop UI is not implemented yet.

First run downloads model weights from Hugging Face (requires network access).

## Testing strategy

Unit tests **do not download the model**. They mock the Transformers pipeline and model loaders:

- `test_audio_utils.py` — path validation (missing file, bad extension, valid file)
- `test_asr_engine.py` — lazy load caching, structured return dict, generate kwargs, gated-model error message

Run:

```bash
pytest
```

## Phase 01 deliverables

- [x] `ASREngine` with lazy `load_model()` and `transcribe()` returning a dict
- [x] `validate_audio_path()` with clear errors
- [x] CLI mode in `main.py`
- [x] Unit tests with mocked pipeline (no network/GPU)
- [x] Phase documentation

## Next phase (Phase 02 — PyQt UI)

Planned work:

- Implement `MainWindow` with file picker and transcript display
- Connect `TranscriptionWorker` via `QThread`
- Show loading/progress during model load and transcription
