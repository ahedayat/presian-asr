# Phase 03 — Background Threading for ML Inference

This phase refactors the PyQt6 desktop app so Whisper transcription never blocks the UI thread. The `ASREngine` API is unchanged; only how and where it is invoked differs.

## Why ML inference must not run on the UI thread

PyQt6 (like Qt generally) uses a single **GUI event loop** on the main thread. That loop handles painting, input, timers, and signal delivery to widgets. Any long-running synchronous work on that thread — model download, weight loading, audio decoding, or Whisper forward pass — **freezes the window**: buttons stop responding, the OS may mark the app as “not responding”, and status text cannot update.

Speech recognition on CPU is inherently slow (seconds to minutes depending on file length and hardware). Running `ASREngine.transcribe()` directly from a button slot would block the event loop for the entire duration.

The fix is the standard Qt pattern:

1. Keep widgets and slots on the **main thread**.
2. Move a `QObject` worker to a **`QThread`**.
3. Connect `QThread.started` → `worker.run()`.
4. Have the worker emit **signals** (`progress`, `finished`, `failed`) back to the main thread.
5. Update the UI only in slots connected to those signals.

Signals queued across threads are thread-safe in Qt; direct widget access from the worker thread is not.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Main thread (UI)                                            │
│    MainWindow                                                │
│      - file picker, buttons, result text, status label       │
│      - owns one shared ASREngine (model loaded once, reused)   │
│      - slots: _on_transcription_progress / finished / failed   │
└────────────────────────────┬─────────────────────────────────┘
                             │ signals (queued)
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  QThread                                                     │
│    TranscriptionWorker.run()                                 │
│      engine.transcribe(audio_path)  ← CPU-only, no GPU       │
└──────────────────────────────────────────────────────────────┘
```

### Components

| File | Role |
|------|------|
| `workers/transcription_worker.py` | `TranscriptionWorker(QObject)` — runs `transcribe()` off the UI thread |
| `ui/main_window.py` | Creates `QThread`, moves worker, connects signals, manages busy state |
| `core/asr_engine.py` | Unchanged CPU-first engine; pipeline cached after first load |

### Worker signals

| Signal | Payload | When |
|--------|---------|------|
| `started` | — | Worker `run()` begins |
| `progress` | `str` | Status message for the UI |
| `finished` | `dict` | Full result from `ASREngine.transcribe()` |
| `failed` | `str` | Error message from any exception |

The main window passes its existing `ASREngine` instance into the worker so the model is **not** reloaded for every transcription.

## Thread lifecycle and cleanup

When the user clicks **تبدیل به متن**:

1. Buttons enter a busy state (select/transcribe/copy/clear disabled; **لغو** enabled).
2. A new `QThread` and `TranscriptionWorker` are created.
3. `worker.moveToThread(thread)`; `thread.started` → `worker.run`.
4. On `finished` or `failed`, the worker calls `thread.quit()`.
5. `worker.deleteLater()` and `thread.deleteLater()` run after quit.
6. `thread.finished` → `_cleanup_thread()` which calls `thread.wait()` and clears references.

This avoids starting a second job while the previous thread is still running and ensures objects are destroyed on the correct thread.

## Cancellation (current limitation)

A **لغو** (Cancel) button is provided, but it implements **UI-level cancellation only**:

- Clicking cancel sets an internal `_transcription_cancelled` flag.
- The background thread **continues** until `transcribe()` completes; the worker is **not** forcibly stopped.
- When the worker eventually emits `finished` or `failed`, the main window **ignores** the result and does not show an error dialog for failures after cancel.
- The status label explains that processing continues in the background.

**Hard cancellation is not supported yet** because:

- Python threads cannot be safely killed mid-inference.
- Interrupting PyTorch/Transformers inside a forward pass could corrupt state or leak resources.
- A future phase could add cooperative cancellation (e.g. periodic checks + process isolation), but that is out of scope here.

Do not call `terminate()` on `QThread` for ML work.

## UI behavior during transcription

| Control | Idle | Transcribing | After cancel (still running) |
|---------|------|--------------|------------------------------|
| انتخاب فایل صوتی | enabled | disabled | disabled |
| تبدیل به متن | enabled if file selected | disabled | disabled |
| لغو | disabled | enabled | disabled |
| کپی / پاک کردن | enabled | disabled | disabled |
| Status label | ready / file selected | progress messages | “لغو شد — …” |

On failure (without cancel), a `QMessageBox` shows the error string.

## Testing

Lightweight unit tests in `tests/test_transcription_worker.py`:

- Mock `ASREngine.transcribe()` — no real model or `QThread` timing tests.
- Call `worker.run()` synchronously on the test thread and collect signal emissions.
- Cover success (`finished`), failure (`failed`), and `started` / `progress` emissions.

Full GUI/thread integration is validated manually by running the desktop app.

## Constraints preserved

- **CPU-only** — `ASREngine` still uses `device="cpu"` from config; no GPU path added.
- **Engine API unchanged** — worker calls `transcribe(audio_path)` and forwards the returned dict.
- **Model reuse** — one `ASREngine` on `MainWindow`, shared across jobs.

## Phase 03 deliverables

- [x] `TranscriptionWorker` with `started`, `progress`, `finished`, `failed` signals
- [x] `MainWindow` refactored to `QThread` + safe signal wiring and cleanup
- [x] Busy UI state and status updates during inference
- [x] UI-level cancel button with documented limitation
- [x] Worker unit tests with mocked engine
- [x] Phase documentation

## Next steps

- Cooperative cancellation or subprocess-based isolation for true stop
- Progress bar tied to chunk timestamps or pipeline callbacks
- Queue multiple files without blocking the UI
