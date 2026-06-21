# Persian ASR Desktop Application

A Persian automatic speech recognition (ASR) desktop app built with **PyQt6** and **Hugging Face Transformers**, using the [`C1Tech/whisper_small_persian`](https://huggingface.co/C1Tech/whisper_small_persian) model.

The ASR core is separated from the UI so inference logic can be tested and maintained independently of the desktop interface. Inference is **CPU-first only**; model weights are **not** bundled and are loaded from the Hugging Face cache at runtime.

## Requirements

- Python 3.10+
- Ubuntu (primary target) or another Linux distro with **ffmpeg** on `PATH`
- A Hugging Face account with access to the model (if gated)

## Quick start (Ubuntu)

```bash
git clone <repo-url> persian_asr
cd persian_asr

python3 -m venv .venv
source .venv/bin/activate
pip install -e .

sudo apt update
sudo apt install -y ffmpeg

cp .env.example .env
# If the model is gated: huggingface-cli login  OR  set HF_TOKEN in .env

./scripts/check_env.sh
./scripts/run_app.sh
```

## Setup

### 1. Create a virtual environment

```bash
cd persian_asr
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

Development (tests and ruff):

```bash
pip install -e ".[dev]"
```

Runtime only:

```bash
pip install -e .
```

### 3. Install ffmpeg (Ubuntu)

```bash
sudo apt update
sudo apt install -y ffmpeg
```

ffmpeg is required for default audio normalization (16 kHz mono WAV) and reliable duration probing. It is **not** included in the Python package; install it separately unless you bundle it in a future installer.

### 4. Hugging Face login (gated model access)

If the model requires authentication, log in before the first run:

```bash
pip install huggingface_hub
huggingface-cli login
```

Or copy the example env file and set your token:

```bash
cp .env.example .env
# Edit .env and set HF_TOKEN=hf_...
```

You can also export the token:

```bash
export HF_TOKEN=hf_...
```

Accept the model terms on the Hugging Face model page when prompted.

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
| `CONVERT_TO_16K_MONO_WAV` | `true` |

See [docs/phases/phase-06-packaging.md](docs/phases/phase-06-packaging.md) for Hugging Face cache paths and optional PyInstaller builds.

## Run the application

Verify the environment:

```bash
./scripts/check_env.sh
```

### Desktop GUI

```bash
./scripts/run_app.sh
```

Equivalent:

```bash
python -m persian_asr_app.main
persian-asr
```

### CLI (single file)

```bash
./scripts/run_cli.sh path/to/audio.mp3
```

Equivalent:

```bash
python -m persian_asr_app.main --audio path/to/audio.mp3
```

Supported extensions: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.aac`.

### First run

The first transcription downloads the model into the Hugging Face cache (typically `~/.cache/huggingface/hub`). This is a one-time cost per machine unless the cache is cleared. Later runs use the cached files and work offline.

## Optional: PyInstaller bundle

For an experimental frozen build (model still **not** bundled):

```bash
pip install pyinstaller
pyinstaller persian_asr.spec
./dist/persian-asr/persian-asr
```

See [docs/phases/phase-06-packaging.md](docs/phases/phase-06-packaging.md) for details and limitations.

## Troubleshooting

### Gated model access

**Symptoms:** Errors mentioning gated repo, HTTP 401/403, or “Failed to load model” on first use.

**Fix:**

1. Open [C1Tech/whisper_small_persian](https://huggingface.co/C1Tech/whisper_small_persian) and accept the model terms while logged in.
2. Run `huggingface-cli login` or set `HF_TOKEN` in `.env`.
3. Retry transcription.

### ffmpeg missing

**Symptoms:** `ffmpeg not found` or normalization/conversion errors when `CONVERT_TO_16K_MONO_WAV=true` (default).

**Fix:**

```bash
sudo apt install -y ffmpeg
ffmpeg -version
```

Or set `CONVERT_TO_16K_MONO_WAV=false` in `.env` (WAV-only workflows; other formats may still need ffmpeg/librosa).

### Slow CPU inference

**Symptoms:** Transcription takes a long time even for short clips.

**Notes:** Whisper on CPU is expected to be slow compared to GPU. Keep clips short for interactive use. Optional tuning in `.env`:

- `ASR_BATCH_SIZE=1` (default; do not increase on CPU)
- `TORCH_NUM_THREADS=4` (adjust to your CPU core count)

Very long files (default warning above 30 minutes) are not chunked yet; they may take hours or run out of memory.

### First-run model download delay

**Symptoms:** App appears idle or “loading model” for several minutes on first transcription.

**Notes:** The Hub is downloading processor and weight files to `~/.cache/huggingface/hub`. Wait for the download to finish; subsequent runs are much faster. Ensure disk space and network access on first run.

### Unsupported audio file

**Symptoms:** `Unsupported audio format` or file-not-found errors.

**Fix:** Use one of: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.aac`. Convert other formats with ffmpeg, for example:

```bash
ffmpeg -i input.mkv -ac 1 -ar 16000 output.wav
./scripts/run_cli.sh output.wav
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
├── main.py              # GUI / CLI entry point
├── config.py            # Model and runtime settings
├── core/
│   ├── asr_engine.py    # Hugging Face Whisper ASR engine
│   └── audio_utils.py   # Audio loading and ffmpeg helpers
├── ui/
│   └── main_window.py   # PyQt6 desktop UI
└── workers/
    ├── model_load_worker.py
    └── transcription_worker.py

scripts/
├── check_env.sh         # Verify Python, ffmpeg, dependencies
├── run_app.sh           # Launch GUI
└── run_cli.sh           # CLI transcription
```

Phase documentation:

- [phase-00-setup.md](docs/phases/phase-00-setup.md)
- [phase-06-packaging.md](docs/phases/phase-06-packaging.md)

## License

Add your license here.
