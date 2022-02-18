"""Transcription command line application."""

import sys

from understory import voice

if __name__ == "__main__":
    print("\r\n\r\n".join(". ".join(phrases) + "." for phrases in voice.transcribe()))
    sys.exit()
