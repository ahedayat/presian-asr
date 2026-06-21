# Persian ASR Desktop Application

A Persian automatic speech recognition (ASR) desktop app built with **PyQt6** and **Hugging Face Transformers**, using the [`C1Tech/whisper_small_persian`](https://huggingface.co/C1Tech/whisper_small_persian) model.

The ASR core is separated from the UI so inference logic can be tested and maintained independently of the desktop interface.

## Requirements

- Python 3.10+
- Ubuntu (or another Linux distro) with **ffmpeg** for audio decoding
- A Hugging Face account with access to the model (if gated)

## Setup

### 1. Create a virtual environment

```bash
cd persian-asr-pyqt
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

Install the package in editable mode with development tools:

```bash
pip install -e ".[dev]"
```

For a runtime-only install (no pytest/ruff):

```bash
pip install -e .
```

### 3. Install ffmpeg (Ubuntu)

```bash
sudo apt update
sudo apt install -y ffmpeg
```

ffmpeg is used by librosa and related audio tooling to read common audio formats.

### 4. Hugging Face login (gated model access)

If the model requires authentication, log in before first run:

```bash
pip install huggingface_hub
huggingface-cli login
```

Alternatively, copy the example env file and set your token:

```bash
cp .env.example .env
# Edit .env and set HF_TOKEN=hf_...
```

You can also export the token:

```bash
export HF_TOKEN=hf_...
```

### 5. Configure environment (optional)

```bash
cp .env.example .env
```

Defaults are CPU-first:

| Variable | Default |
|----------|---------|
| `MODEL_ID` | `C1Tech/whisper_small_persian` |
| `DEVICE` | `cpu` |
| `TORCH_DTYPE` | `float32` |
| `DEFAULT_LANGUAGE` | `fa` |

## Run the application

Phase 0 ships a minimal entry point that prints a startup message:

```bash
python -m persian_asr_app.main
```

Or use the console script after installation:

```bash
persian-asr
```

## Run tests

```bash
pytest
```

## Run linting

```bash
ruff check src tests
```

## Project layout

```
src/persian_asr_app/
├── main.py              # Application entry point
├── config.py            # Model and runtime settings
├── core/
│   ├── asr_engine.py    # Hugging Face Whisper ASR engine
│   └── audio_utils.py   # Audio loading helpers
├── ui/
│   └── main_window.py   # PyQt6 UI (future phase)
└── workers/
    └── transcription_worker.py  # Background transcription worker
```

See [docs/phases/phase-00-setup.md](docs/phases/phase-00-setup.md) for phase documentation.

## License

Add your license here.
