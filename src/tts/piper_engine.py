import io
import wave

import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice


class PiperEngine:
    """Local text-to-speech only — the reply is synthesized and played
    on-device, never sent anywhere.

    Note: piper-tts's Python API has shifted across releases; check
    `pip show piper-tts` against this code if PiperVoice.load/synthesize_wav
    don't match what's installed. On piper-tts 1.8.0, `synthesize()` returns
    an iterable of raw AudioChunks instead of writing a WAV directly —
    `synthesize_wav()` is the one that still configures/writes a wave file.
    """

    def __init__(self, model_path: str):
        self.voice = PiperVoice.load(model_path)

    def speak(self, text: str):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            self.voice.synthesize_wav(text, wav_file)
        buf.seek(0)
        with wave.open(buf, "rb") as wav_file:
            audio = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)
            sd.play(audio, samplerate=wav_file.getframerate())
            sd.wait()
