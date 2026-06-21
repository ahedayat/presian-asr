# Phase 02 — PyQt6 MVP UI

This phase adds a minimal Persian/RTL desktop interface for file-based transcription. The core ASR engine from Phase 01 is unchanged and remains independent of the UI.

## Goals

- Launch a PyQt6 window when the app runs without `--audio`.
- Let users pick an audio file, transcribe it, and view/copy the result.
- Keep transcription on the CPU via the existing `ASREngine`.
- Run inference off the UI thread so the window stays responsive during model load and transcription.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  main.py                                                │
│    --audio path  →  CLI (print transcription)           │
│    (no --audio)  →  run_gui() → MainWindow              │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
                  ui/main_window.py
                  file picker, result view, actions
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
   workers/transcription_worker.py   core/asr_engine.py
   QThread background run            ASREngine.transcribe()
```

The UI layer imports `ASREngine` only through `TranscriptionWorker`. Model loading and inference logic stay in `core/`.

## UI features

| Element | Persian label | Behavior |
|---------|---------------|----------|
| Window title | تبدیل گفتار فارسی به متن | RTL layout direction |
| Header | تبدیل گفتار فارسی به متن | Section title |
| File button | انتخاب فایل صوتی | Opens `QFileDialog` for audio files |
| Path label | — | Shows selected file path |
| Transcribe button | تبدیل به متن | Disabled until a file is selected |
| Result area | — | Read-only `QTextEdit` with RTL text |
| Copy button | کپی متن | Copies result to clipboard |
| Clear button | پاک کردن | Resets file selection and output |
| Status label | — | Shows ready / busy / success / error state |

Supported formats: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.aac`.

Errors (invalid file, model access, ffmpeg missing, etc.) are shown in a `QMessageBox`.

## How to run

### Desktop UI

```bash
python -m persian_asr_app.main
```

Or after installation:

```bash
persian-asr
```

1. Click **انتخاب فایل صوتی** and choose an audio file.
2. Click **تبدیل به متن**. The first run may download the model from Hugging Face.
3. Read the transcription in the result area.
4. Use **کپی متن** to copy the text, or **پاک کردن** to start over.

### CLI (unchanged)

```bash
python -m persian_asr_app.main --audio path/to/audio.mp3
```

## Styling

The window uses a small built-in stylesheet: light background, readable 12–18px fonts, blue action buttons, and a bordered result area. Layout and text alignment follow RTL conventions.

## Out of scope (this phase)

- GPU usage
- Microphone recording
- Packaging / installers
- Progress bars or timestamps in the UI

## Phase 02 deliverables

- [x] `MainWindow` with file picker, transcription, copy, and clear
- [x] `main.py` launches GUI when `--audio` is omitted
- [x] Background transcription via `TranscriptionWorker` + `QThread`
- [x] Minimal RTL-friendly stylesheet
- [x] Phase documentation

## Next steps

- Microphone capture and live transcription
- Packaging (e.g. PyInstaller) for distribution
- Optional progress indicator during long transcriptions
