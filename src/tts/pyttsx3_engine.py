import logging

import pyttsx3

logger = logging.getLogger(__name__)


class PyttSX3Engine:
    """Windows SAPI TTS — no model files needed.
    Picks the first female/Zira voice available; falls back to default."""

    def speak(self, text: str):
        engine = pyttsx3.init()
        _set_female_voice(engine)
        engine.setProperty("rate", 150)
        engine.say(text)
        engine.runAndWait()
        engine.stop()


def _set_female_voice(engine) -> None:
    voices = engine.getProperty("voices")
    # Prefer Zira (Windows 10/11 female en-US), then any voice with 'female' or 'zira' in id/name
    for voice in voices:
        name = (voice.name or "").lower()
        vid = (voice.id or "").lower()
        if "zira" in name or "zira" in vid:
            engine.setProperty("voice", voice.id)
            logger.info("TTS voice: %s", voice.name)
            return
    for voice in voices:
        name = (voice.name or "").lower()
        vid = (voice.id or "").lower()
        if "female" in name or "female" in vid or "hazel" in name or "susan" in name or "aria" in name:
            engine.setProperty("voice", voice.id)
            logger.info("TTS voice: %s", voice.name)
            return
    logger.info("No female voice found — using default (%s)", voices[0].name if voices else "none")
