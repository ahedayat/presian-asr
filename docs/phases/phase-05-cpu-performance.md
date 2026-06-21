# Phase 05 — CPU Performance, Audio Robustness, and Long-Audio Policy

This phase improves CPU-first inference reliability, adds ffmpeg-based audio normalization, surfaces duration and long-file warnings in the UI, and introduces file logging without recording transcription text.

## Goals

| Area | Change |
|------|--------|
| **Audio metadata** | Estimate duration via ffprobe (librosa fallback); show in UI after file selection |
| **Normalization** | Optional ffmpeg conversion to temporary 16 kHz mono WAV before inference |
| **CPU runtime** | `batch_size=1`, optional `TORCH_NUM_THREADS`, float32 only, cached model |
| **Long audio** | Configurable threshold warning; no silent failure; chunking not implemented yet |
| **Logging** | Rotating log file under `logs/persian_asr.log` |
| **Privacy** | Transcription text is not written to logs by default |

CPU-first remains mandatory. No GPU, no cloud inference, offline after the model is downloaded.

## CPU limitations

Whisper small on CPU is practical for short clips (roughly a few minutes). Longer files scale roughly linearly with duration and can:

- Take many minutes or hours to finish
- Use large amounts of RAM when the full waveform is processed at once
- Fail with out-of-memory or internal pipeline errors on very long inputs

The app does **not** implement audio chunking yet. A single file is passed to the Hugging Face ASR pipeline in one call. For files above the configured threshold (default **30 minutes**), the UI shows a persistent warning and asks for confirmation before starting transcription.

### Runtime settings (`.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `ASR_BATCH_SIZE` | `1` | Pipeline batch size; keep at 1 on desktop CPU |
| `TORCH_NUM_THREADS` | (unset) | Optional cap on PyTorch intra-op threads |
| `CONVERT_TO_16K_MONO_WAV` | `true` | Normalize input via ffmpeg before inference |
| `LONG_AUDIO_THRESHOLD_MINUTES` | `30` | UI warning threshold |

`TORCH_DTYPE` remains `float32` in code. Float16 is not used on CPU.

The model is loaded once per `ASREngine` instance and reused across transcriptions (`ASREngine._pipe` cache).

## ffmpeg usage

When `CONVERT_TO_16K_MONO_WAV=true` (default), `ASREngine.transcribe()` calls:

```python
convert_to_temp_wav_16k_mono(input_path) -> Path
```

Implementation (`core/audio_utils.py`):

1. Validate extension and file existence
2. Create a temp `.wav` with `tempfile.mkstemp`
3. Run ffmpeg: mono (`-ac 1`), 16 kHz (`-ar 16000`), PCM s16le
4. Pass the temp path to the pipeline
5. Delete the temp file in a `finally` block (success or failure)

Requires **ffmpeg** on `PATH`. If ffmpeg is missing and normalization is enabled, transcription fails with an explicit error instead of silently using a mismatched format.

Duration estimation prefers **ffprobe** when available; otherwise **librosa** is used.

## Long-audio policy

| Scenario | Behavior |
|----------|----------|
| Duration known, below threshold | Show `مدت زمان: MM:SS`; no warning |
| Duration known, above threshold | Orange warning label + dialog on selection; confirm again before transcribe |
| Duration unknown | Warning that long files may fail; chunking not supported |
| Transcription error | Error dialog + log entry with path (not transcript text) |

**Chunking:** Not implemented in this phase. Future chunking should split on silence or fixed windows, transcribe segments with `batch_size=1`, and merge text with documented overlap handling.

## Logging

- Module: `persian_asr_app/app_logging.py`
- File: `logs/persian_asr.log` (relative to project root)
- Rotation: 5 MB × 3 backups
- Initialized in `main.py` for both GUI and CLI

Logged events include:

- Logging startup
- Model load start / finish / failure
- Transcription start / finish / failure (audio **path** only)
- Temp WAV creation and cleanup (debug)
- Optional `torch.set_num_threads` value

**Privacy:** Log messages intentionally avoid transcription content. Do not add debug logging of `result["text"]` without an explicit opt-in setting.

## Architecture (unchanged layering)

```
MainWindow
  ├─ estimate_audio_duration / validate on file pick
  ├─ long-audio warning UI
  └─ TranscriptionWorker → ASREngine.transcribe()
                              ├─ convert_to_temp_wav_16k_mono (optional)
                              ├─ pipeline(batch_size=1, float32)
                              └─ temp file cleanup (finally)
```

## Testing

- Extension validation parametrized across all supported formats
- `build_ffmpeg_convert_command` argument construction
- Mocked ffmpeg subprocess for temp WAV conversion
- Mocked ASR pipeline (no model download)
- Logging setup writes to a temporary directory in tests

Run:

```bash
pytest
```

## Out of scope (unchanged)

- GPU / CUDA
- Cloud APIs
- Automatic chunking for hour-long files
- Microphone capture
- Packaging / installer
