"""Transcription command line application."""

import logging
import sys

from understory import voice

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING, filename="run.log", filemode="w", force=True
    )
    print(voice.transcribe())
    sys.exit()
