"""
Voice input/output.

"""

import logging
import pathlib
import queue
import subprocess
import sys

import fifteen_ai
import gtts
import playsound
import pyttsx3
import sounddevice
import vosk

# from understory import web

vosk.SetLogLevel(-1)

data_dir = pathlib.Path(__file__).parent
vosk_base_url = "https://alphacephei.com/vosk/models/"
vosk_archive_name = "vosk-model-small-en-us-0.15.zip"
vosk_model_dir = data_dir / "model"


def install():
    """Ensure the models are present."""
    if vosk_model_dir.exists():
        return
    logging.debug("installing Vosk model")
    web.download(f"{vosk_base_url}/{vosk_archive_name}", data_dir / vosk_archive_name)
    subprocess.run(["unzip", vosk_archive_name], cwd=data_dir)
    subprocess.run(["mv", vosk_archive_name[:-4], "model"], cwd=data_dir)


def speak(message, character="system"):
    """Play message in character's voice."""
    audio = data_dir / "speech.wav"
    if character == "system":
        pyttsx3.init().save_to_file(message, audio)
    elif character == "google":
        gtts.gTTS(message).save(audio)
    else:
        fifteen_ai.tts(message, character, filename=audio)
    playsound.playsound(audio)
    audio.unlink()


def transcribe():
    """
    Return a list of phrasal voice inputs.

    - say "try again" to try the previous phrase again
    - say "new paragraph" to start a new paragraph
    - say "finished" when done

    """
    install()

    phrases = []
    paragraphs = []

    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    device = None
    device_info = sounddevice.query_devices(device, "input")
    samplerate = int(device_info["default_samplerate"])

    with sounddevice.RawInputStream(
        samplerate=samplerate,
        blocksize=8000,
        device=device,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        rec = vosk.KaldiRecognizer(vosk.Model(str(vosk_model_dir)), samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                words = rec.Result()[14:-3]
                if words == "try again":
                    phrases.pop()
                elif words == "new paragraph":
                    paragraphs.append(phrases)
                    phrases = []
                    print(" " * 13 + "\n", end="\r", file=sys.stderr)
                elif words == "finished":
                    if phrases:
                        paragraphs.append(phrases)
                    print("", end="\r", file=sys.stderr)
                    return paragraphs
                else:
                    if words:
                        phrases.append(words)
                        print(words, file=sys.stderr)
            else:
                words = rec.PartialResult()[17:-3]
                if words.endswith("wait try again"):
                    rec.Reset()
                print(words, end="\r", file=sys.stderr)


if __name__ == "__main__":
    print(transcribe())
