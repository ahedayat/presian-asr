"""Application entry point."""

import argparse

from persian_asr_app import __version__
from persian_asr_app.core.asr_engine import ASREngine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Persian ASR — transcribe audio files from the command line.",
    )
    parser.add_argument(
        "--audio",
        type=str,
        help="Path to an audio file (.wav, .mp3, .m4a, .flac, .ogg, .aac)",
    )
    args = parser.parse_args()

    if args.audio:
        engine = ASREngine()
        result = engine.transcribe(args.audio)
        print(result["text"])
        return

    print(
        f"Persian ASR Desktop Application v{__version__}\n"
        "The desktop UI is not implemented yet.\n"
        "Transcribe from the CLI with: python -m persian_asr_app.main --audio path/to/audio.mp3"
    )


if __name__ == "__main__":
    main()
