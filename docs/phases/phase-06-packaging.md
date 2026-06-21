# Phase 06 — Local Packaging and Distribution

This phase documents how to run the Persian ASR PyQt app in development and on a local Ubuntu machine, how Hugging Face model caching works, and optional PyInstaller packaging. **Model weights are not bundled** in the executable or repository.

## Goals

| Area | Approach |
|------|----------|
| **Development** | Editable install + helper scripts under `scripts/` |
| **Production / local** | Same Python env or optional PyInstaller binary; model fetched at first run |
| **Model storage** | Standard Hugging Face Hub cache (`~/.cache/huggingface/hub`) |
| **Inference** | CPU-only (`DEVICE=cpu`, float32) |
| **Audio** | **ffmpeg** must be installed on the system (not bundled in this phase) |

## Development run

Use a virtual environment at the project root and install the package in editable mode.

```bash
cd /path/to/persian_asr
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional environment file:

```bash
cp .env.example .env
# Edit MODEL_ID, HF_TOKEN, etc.
```

Verify the environment:

```bash
./scripts/check_env.sh
```

Run the desktop app:

```bash
./scripts/run_app.sh
```

Run a one-off CLI transcription:

```bash
./scripts/run_cli.sh path/to/audio.mp3
```

Equivalent commands without scripts:

```bash
python -m persian_asr_app.main              # GUI
python -m persian_asr_app.main --audio file # CLI
persian-asr                                 # GUI (console script)
```

## Production / local run

For day-to-day use on Ubuntu, the recommended path is a **dedicated virtual environment** with a runtime install (no dev tools):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
sudo apt install -y ffmpeg
./scripts/check_env.sh
./scripts/run_app.sh
```

If the model is gated, authenticate once before the first transcription:

```bash
huggingface-cli login
# or set HF_TOKEN in .env
```

After the first successful model download, the app works offline for transcription (network is only needed again for model updates or cache clears).

### Optional: PyInstaller one-file / one-folder build

PyInstaller is **optional**. Transformers, PyTorch, and PyQt6 are large and sometimes need extra hidden imports or system libraries; treat a frozen build as experimental until validated on your target Ubuntu version.

Install PyInstaller in the same venv:

```bash
pip install pyinstaller
```

Build from the project root using the minimal spec (does **not** include model weights):

```bash
pyinstaller persian_asr.spec
```

Artifacts land in `dist/`:

- `dist/persian-asr/` — one-folder bundle (easier to debug)
- Or adjust the spec for `--onefile` if you accept slower startup

Run the frozen app:

```bash
./dist/persian-asr/persian-asr
```

The frozen binary still downloads or reads the model from the **Hugging Face cache** on first run. Set cache location explicitly if needed:

```bash
export HF_HOME="$HOME/.cache/huggingface"
export TRANSFORMERS_CACHE="$HF_HOME/hub"
```

Do not add model checkpoints to `datas=` in the spec file. Bundling Whisper weights would inflate the binary by hundreds of MB and fight Hub updates.

If PyInstaller fails on missing modules, add targeted `hiddenimports` to `persian_asr.spec` rather than switching packaging tools in this phase.

## Hugging Face cache behavior

Model loading uses Transformers `from_pretrained()` with the default Hub cache:

| Variable | Typical value | Role |
|----------|---------------|------|
| `HF_HOME` | `~/.cache/huggingface` | Root for Hub assets |
| `HUGGINGFACE_HUB_CACHE` | `$HF_HOME/hub` | Snapshot storage (override with `HF_HOME` / Hub env docs) |
| `HF_TOKEN` | (optional) | Auth for gated models |

Default model ID: `C1Tech/whisper_small_persian` (see `config.py` / `.env`).

**First run:** The engine downloads processor and model files on the first `load_model()` / transcription. This can take several minutes on a slow connection.

**Later runs:** Files are read from disk cache; no re-download unless the cache is cleared or the model revision changes.

**Clear cache (force re-download):**

```bash
rm -rf ~/.cache/huggingface/hub/models--C1Tech--whisper_small_persian
```

**Offline use:** After a successful download, disconnecting from the network is fine as long as the cache entry exists and `MODEL_ID` is unchanged.

The application does not ship weights inside the repo, the venv, or the PyInstaller bundle.

## ffmpeg requirement

Audio normalization (`CONVERT_TO_16K_MONO_WAV=true`, default) and duration probing use **ffmpeg** / **ffprobe** on `PATH`.

Ubuntu install:

```bash
sudo apt update
sudo apt install -y ffmpeg
```

Verify:

```bash
ffmpeg -version
ffprobe -version
```

ffmpeg is **not** bundled in Phase 06. End users must install it separately unless a future phase adds static ffmpeg binaries to an installer.

To disable ffmpeg-based normalization (not recommended for arbitrary formats):

```bash
CONVERT_TO_16K_MONO_WAV=false
```

WAV files at 16 kHz mono may still transcribe without conversion, but mp3/m4a/etc. depend on librosa/ffmpeg behavior.

## Helper scripts

| Script | Purpose |
|--------|---------|
| `scripts/check_env.sh` | Python version, ffmpeg, torch, transformers, PyQt6 |
| `scripts/run_app.sh` | Launch GUI (`python -m persian_asr_app.main`) |
| `scripts/run_cli.sh` | CLI transcription with `--audio` |

All scripts:

- Resolve paths relative to the repository root
- Activate `.venv` when present
- Load `.env` when present

## Architecture (packaging view)

```
User machine
├── System: ffmpeg, Python 3.10+
├── venv or dist/persian-asr/     ← app code + PyTorch + PyQt6
├── ~/.cache/huggingface/hub/   ← C1Tech/whisper_small_persian (not in repo)
└── logs/persian_asr.log          ← runtime logs (no transcript text)
```

## Out of scope

- GPU / CUDA builds
- Bundling model weights in the executable
- Bundling ffmpeg (future installer work)
- Debian packages, Snap, or Flatpak
- Automatic chunking for very long files (see Phase 05)

## Testing before release

```bash
./scripts/check_env.sh
pytest
./scripts/run_cli.sh tests/fixtures/sample.wav   # if you add a fixture
./scripts/run_app.sh
```

Confirm first-run download, second-run cache reuse, and transcription of at least one supported format.
