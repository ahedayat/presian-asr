# Phase 04 — Export, Timing, Model Status, and Timestamps

This phase adds practical export and usability features to the PyQt6 desktop app while keeping `ASREngine` independent from the UI layer.

## Features added

| Feature | Description |
|---------|-------------|
| **ذخیره متن** | Save transcription to a UTF-8 `.txt` file via `QFileDialog.getSaveFileName` |
| **Processing time** | Measured in the worker, shown in the status label, included in exports |
| **Model status** | Label shows not loaded / loading / ready; optional **بارگذاری مدل** preload |
| **Approximate timestamps** | Checkbox enables chunked output with `[MM:SS.ss - MM:SS.ss]` lines |

CPU-first remains the default. No GPU, microphone recording, or packaging changes.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Main thread (UI) — MainWindow                                  │
│    - model status label, preload button                         │
│    - timestamps checkbox, save / copy / clear buttons           │
│    - owns one shared ASREngine                                  │
└────────────┬───────────────────────────────┬────────────────────┘
             │ signals                       │ signals
             ▼                               ▼
┌────────────────────────────┐   ┌────────────────────────────────┐
│  QThread                   │   │  QThread                       │
│    ModelLoadWorker.run()   │   │    TranscriptionWorker.run()   │
│      engine.load_model()   │   │      engine.transcribe()       │
└────────────────────────────┘   └────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  core/transcription_format.py (no PyQt)                         │
│    format_timestamp, format_display_text, format_export_text      │
└─────────────────────────────────────────────────────────────────┘
```

`ASREngine` is unchanged at the API level. Formatting logic lives in `core/transcription_format.py` so the CLI and tests can reuse it without importing PyQt.

## Export format

When the user clicks **ذخیره متن**, the app writes a UTF-8 `.txt` file:

```
--- Persian ASR ---
فایل صوتی: /path/to/audio.wav
مدل: C1Tech/whisper_small_persian
زمان پردازش: 12.3 ثانیه
---

[transcription body]
```

- **Encoding:** UTF-8 (Persian text preserved as-is).
- **Metadata:** Audio path, model id, and processing time appear in the header when available.
- **Body:** Matches what is shown in the result area — plain text by default, or timestamped lines when the checkbox was enabled.

If the user omits `.txt` in the save dialog, the extension is appended automatically.

## Approximate timestamps

- Checkbox label: **نمایش زمان‌بندی تقریبی** (default: unchecked).
- When checked, `TranscriptionWorker` sets `engine.return_timestamps = True` before calling `transcribe()`.
- Whisper returns `chunks` with `(start, end)` pairs; each line is formatted as:

  ```
  [00:01.20 - 00:03.50] متن
  ```

- If chunks are missing or empty, the UI falls back to plain `result["text"]` (same behavior in export).

Timestamps are approximate segment boundaries from the model, not word-level alignment.

## Processing time

- Measured in `TranscriptionWorker.run()` with `time.perf_counter()` around `engine.transcribe()`.
- Includes model load on the first run (because `transcribe()` calls `load_model()` internally).
- After a successful job, the status label shows e.g. `تبدیل با موفقیت انجام شد (12.3 ثانیه)`.
- The same value is written to the export header as `زمان پردازش`.

## Model status and preload

| State | Label text | Preload button |
|-------|------------|----------------|
| Not loaded | `مدل: بارگذاری نشده` | Enabled |
| Loading | `مدل: در حال بارگذاری...` | Disabled |
| Ready | `مدل: آماده` | Disabled |

**بارگذاری مدل** starts a dedicated `ModelLoadWorker` on a `QThread`, calling `engine.load_model()` off the UI thread. The window stays responsive during download and weight loading.

- Preload and transcription cannot run concurrently on the same engine; buttons are disabled while either job is active.
- Transcription still works without preload — the first transcribe will load the model in the transcription worker thread.
- After any successful load (preload or transcribe), the status switches to **مدل: آماده**.

## Files touched

| Path | Role |
|------|------|
| `core/transcription_format.py` | Display and export formatting |
| `workers/model_load_worker.py` | Background model preload |
| `workers/transcription_worker.py` | `return_timestamps`, `processing_time` |
| `ui/main_window.py` | New controls, save dialog, status updates |

## Testing

```bash
pytest tests/test_transcription_format.py tests/test_model_load_worker.py tests/test_transcription_worker.py -v
```

Unit tests cover formatting helpers, model-load worker signals, and transcription worker timing / timestamp flag behavior (with mocked engine).

## Out of scope (this phase)

- GPU / CUDA
- Microphone capture
- SRT/VTT subtitle export
- Installer / packaging
- Cooperative cancellation inside `transcribe()` (unchanged from Phase 03)
