"""Application entry point."""

from __future__ import annotations

import argparse
import sys

from persian_asr_app.app_logging import setup_logging
from persian_asr_app.core.asr_engine import ASREngine


def run_cli(audio_path: str) -> None:
    """Transcribe an audio file and print the result."""
    setup_logging()
    engine = ASREngine()
    result = engine.transcribe(audio_path)
    print(result["text"])


def run_gui() -> None:
    """Launch the PyQt6 desktop application."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication

    from persian_asr_app.ui.main_window import MainWindow

    setup_logging()

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Persian ASR — transcribe audio files from the command line or desktop UI.",
    )
    parser.add_argument(
        "--audio",
        type=str,
        help="Path to an audio file (.wav, .mp3, .m4a, .flac, .ogg, .aac)",
    )
    args = parser.parse_args()

    if args.audio:
        run_cli(args.audio)
        return

    run_gui()


if __name__ == "__main__":
    main()
