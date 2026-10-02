"""
Quick pipeline test: wake word -> STT -> hardcoded reply -> Windows TTS
Run from project root: python test_pipeline.py

No LLM needed. No piper model needed.
Press Ctrl+C to stop.
"""

import subprocess
import tempfile
import queue
import threading
import time
import numpy as np
import sounddevice as sd
import wave
import pyttsx3
from openwakeword.model import Model

# ── Config ──────────────────────────────────────────────────────────────────
WHISPER_BINARY = r"D:\Arjun\makeathon\whisper-blas-x64\whisper-cli.exe"
WHISPER_MODEL  = r"D:\Arjun\makeathon\whisper-blas-x64\ggml-base.en.bin"
WAKE_MODEL     = "hey_jarvis"
WAKE_THRESHOLD = 0.5
SAMPLE_RATE    = 16000
BLOCK_MS       = 80        # openWakeWord chunk size
BLOCK_SAMPLES  = int(SAMPLE_RATE * BLOCK_MS / 1000)  # 1280

# Hardcoded responses keyed on simple keyword match
RESPONSES = {
    "hello":    "Hello! How can I help you?",
    "hi":       "Hi there! What do you need?",
    "weather":  "I'm running offline right now, I can't check the weather.",
    "name":     "I'm your on-device AI companion.",
    "who":      "I'm your on-device AI companion.",
    "time":     f"It is {time.strftime('%I:%M %p')}.",
    "date":     f"Today is {time.strftime('%A, %B %d')}.",
    "note":     "Got it, I've noted that down.",
    "remember": "Got it, I'll remember that.",
}
DEFAULT_RESPONSE = "I heard you. I'm just running in test mode right now."

# ── Helpers ──────────────────────────────────────────────────────────────────
_audio_q: queue.Queue = queue.Queue()
_muted = False


def _audio_callback(indata, frames, time_info, status):
    if not _muted:
        _audio_q.put(indata[:, 0].copy())


def transcribe(audio: np.ndarray) -> str:
    """Write float32 audio to temp WAV, run whisper-cli, return text."""
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
        with wave.open(f, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(pcm.tobytes())

    result = subprocess.run(
        [WHISPER_BINARY, "-m", WHISPER_MODEL, "-f", wav_path, "--no-timestamps", "-t", "4"],
        capture_output=True, text=True, timeout=30,
    )
    lines = [l.strip() for l in result.stdout.splitlines() if l.strip() and not l.startswith("[")]
    return " ".join(lines).strip()


def pick_response(text: str) -> str:
    lower = text.lower()
    for keyword, reply in RESPONSES.items():
        if keyword in lower:
            return reply
    return DEFAULT_RESPONSE


def speak(text: str):
    print(f"[TTS] {text}")
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    engine.say(text)
    engine.runAndWait()


# ── Main loop ────────────────────────────────────────────────────────────────
def main():
    detector = Model(wakeword_models=[WAKE_MODEL], inference_framework="onnx")
    print(f"Listening for wake word '{WAKE_MODEL}'... (Ctrl+C to stop)\n")

    buffer = np.array([], dtype=np.float32)
    awake = False
    awake_frames = []
    silence_count = 0
    SILENCE_LIMIT = 20  # ~1.6s of silence after speech

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                        blocksize=BLOCK_SAMPLES, callback=_audio_callback):
        while True:
            try:
                chunk = _audio_q.get(timeout=1.0)
            except queue.Empty:
                continue

            if not awake:
                # Feed 80ms int16 chunk to wake word detector
                chunk_i16 = (np.clip(chunk, -1.0, 1.0) * 32767).astype(np.int16)
                preds = detector.predict(chunk_i16)
                score = max(preds.values(), default=0.0)

                if score >= WAKE_THRESHOLD:
                    print(f"\n[WAKE] Detected! (score={score:.2f}) — listening for your query...")
                    awake = True
                    awake_frames = [chunk]
                    silence_count = 0
                    # Reset detector buffers so stale state doesn't re-trigger
                    try:
                        detector.reset()
                    except AttributeError:
                        for buf in getattr(detector, "prediction_buffer", {}).values():
                            buf.clear()
            else:
                # Collecting utterance
                awake_frames.append(chunk)
                is_silent = np.abs(chunk).mean() < 0.01
                if is_silent:
                    silence_count += 1
                else:
                    silence_count = 0

                if silence_count >= SILENCE_LIMIT:
                    audio = np.concatenate(awake_frames)
                    print(f"[STT] Transcribing {len(audio)/SAMPLE_RATE:.1f}s of audio...")
                    text = transcribe(audio)
                    print(f"[STT] Heard: '{text}'")

                    if text.strip():
                        reply = pick_response(text)
                        speak(reply)
                    else:
                        print("[STT] Nothing heard.")

                    print(f"\nListening for wake word again...\n")
                    awake = False
                    awake_frames = []
                    silence_count = 0


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
