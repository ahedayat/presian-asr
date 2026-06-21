# Minimal PyInstaller spec for Persian ASR (CPU, no bundled model weights).
# Build: pyinstaller persian_asr.spec
# Model C1Tech/whisper_small_persian is downloaded to the Hugging Face cache at runtime.

block_cipher = None

a = Analysis(
    ["src/persian_asr_app/main.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=[
        "persian_asr_app",
        "persian_asr_app.config",
        "persian_asr_app.app_logging",
        "persian_asr_app.core.asr_engine",
        "persian_asr_app.core.audio_utils",
        "persian_asr_app.core.transcription_format",
        "persian_asr_app.ui.main_window",
        "persian_asr_app.workers.model_load_worker",
        "persian_asr_app.workers.transcription_worker",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="persian-asr",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="persian-asr",
)
