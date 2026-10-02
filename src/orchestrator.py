import logging
import time
import uuid
from typing import Optional

from .audio.capture import AudioCapture, SILENCE_TIMEOUT
from .audio.wake_gate import WakeGate
from .audio.wake_word import WakeWordDetector
from .config import get_config
from .io import build_hardware_io
from .llm.graph import build_conversation_graph
from .llm.reasoning import Reasoner
from .memory.store import MemoryStore
from .state import Stage, broadcaster
from .stt.whisper_engine import WhisperEngine
from .tts.piper_engine import PiperEngine

logger = logging.getLogger(__name__)



class Orchestrator:
    def __init__(self):
        self.config = get_config()
        self.hardware = build_hardware_io(self.config)
        # 80ms blocks = openWakeWord's native chunk size.
        # Cuts wake word detection latency from ~500ms worst-case to ~80ms.
        self.audio = AudioCapture(hardware=self.hardware, block_duration=0.08, silence_duration_s=0.6)
        self.stt = WhisperEngine(
            binary=self.config.stt_binary,
            model=self.config.stt_model,
            n_threads=self.config.stt_threads,
        )
        self.tts = PiperEngine(model_path=self.config.piper_voice)
        self.hardware.on_mute_change(self._on_mute_change)

        # Wake-word gate — only wired when enabled in config
        self._wake_gate: Optional[WakeGate] = None
        if self.config.wake_enabled:
            detector = WakeWordDetector(
                model_name=self.config.wake_model,
                threshold=self.config.wake_threshold,
                inference_framework=self.config.wake_backend,
            )
            self._wake_gate = WakeGate(
                self.audio._q, detector,
                on_wake=self._on_wake_handler,
            )
            self.audio.set_wake_gate(self._wake_gate)

        self.audio.set_energy_callback(self._on_mic_energy)

        # LLM reasoning stack — falls back to keyword replies if Ollama is not running
        self._memory = MemoryStore()
        self._reasoner = Reasoner(
            base_url=self.config.ollama_base_url,
            model=self.config.ollama_model,
            embed_model=self.config.ollama_embed_model,
        )
        self._graph = build_conversation_graph(
            reasoner=self._reasoner,
            memory=self._memory,
            set_stage=self._set_stage,
            default_location=self.config.default_location,
        )
        self._thread_id = str(uuid.uuid4())
        logger.info("LLM graph ready (model=%s, thread=%s)", self.config.ollama_model, self._thread_id)

    def _flush_audio(self, duration_s: float = 0.8):
        """Drain mic and gate queues continuously for duration_s seconds.
        Keeps draining as new echo blocks arrive rather than one-shot flush."""
        import queue as _q
        deadline = time.monotonic() + duration_s
        while time.monotonic() < deadline:
            for q in [self.audio._q, self._wake_gate._out_q if self._wake_gate else None]:
                if q is None:
                    continue
                while True:
                    try:
                        q.get_nowait()
                    except _q.Empty:
                        break
            time.sleep(0.02)

    def _on_mic_energy(self, energy: float):
        if self.hardware.muted:
            return
        broadcaster.update(mic_energy=round(energy, 5))

    def _on_wake_handler(self):
        """Called from WakeGate thread — only updates stage/state.
        Greeting TTS is handled in the orchestrator thread via the
        None sentinel from stream_utterances(), avoiding COM thread issues."""
        self._set_stage(Stage.LISTENING)
        broadcaster.update(last_transcript="", last_reply="", mic_energy=0.0)

    def _on_mute_change(self, muted: bool):
        if muted:
            self._set_stage(Stage.MUTED)
        else:
            if self._wake_gate is not None:
                self._wake_gate.reset()
            self._set_stage(self._idle_stage())

    def _set_stage(self, stage: str):
        self.hardware.set_indicator(stage)
        broadcaster.update(stage=stage, muted=self.hardware.muted)

    def _idle_stage(self) -> str:
        return Stage.WAITING_FOR_WAKE if self._wake_gate else Stage.LISTENING

    def run(self):
        self.hardware.start()
        if self._wake_gate is not None:
            self._wake_gate.start()

        self._set_stage(self._idle_stage())

        for segment in self.audio.stream_utterances(
            follow_up_window_s=self.config.follow_up_window_s
        ):
            if self.hardware.muted:
                continue

            # None sentinel = fresh wake word fired. Play greeting.
            if segment is None:
                self.tts.speak("Hey, what's up?")
                self._flush_audio()
                continue

            # Follow-up window expired with no speech — close gate, go idle.
            if segment is SILENCE_TIMEOUT:
                logger.info("Follow-up window expired — returning to wake-word detection")
                if self._wake_gate is not None:
                    self._wake_gate.sleep()
                    self._flush_audio()
                self._set_stage(Stage.MUTED if self.hardware.muted else self._idle_stage())
                continue

            duration = len(segment) / 16000
            logger.info("Utterance captured — %.2fs of audio, running STT...", duration)
            self._set_stage(Stage.TRANSCRIBING)
            text = self.stt.transcribe(segment)
            logger.info("STT result: %r", text)

            if not text.strip() or '[blank_audio]' in text.lower():
                logger.warning("STT returned empty/blank — going back to idle")
                self._set_stage(self._idle_stage())
                continue

            broadcaster.update(last_transcript=text)
            self._set_stage(Stage.THINKING)
            self._handle_utterance(text)

            # Gate stays open for follow-up questions — don't call wake_gate.sleep().
            # SILENCE_TIMEOUT sentinel above handles the eventual close.
            self._flush_audio()   # still drain echo from TTS speaker
            self._set_stage(Stage.MUTED if self.hardware.muted else Stage.FOLLOW_UP)

    def _handle_utterance(self, text: str):
        try:
            result = self._graph.invoke(
                {"text": text},
                config={"configurable": {"thread_id": self._thread_id}},
            )
            reply = result["reply"]
        except Exception as exc:
            logger.warning("LLM graph failed (%s)", exc)
            reply = "Sorry, I'm having trouble with my reasoning engine right now."
        logger.info("Reply: %r", reply)

        self._set_stage(Stage.SPEAKING)
        broadcaster.update(last_reply=reply, mic_energy=0.0)
        self._append_log(text, reply)
        self.tts.speak(reply)

    def _append_log(self, user_text: str, reply: str):
        log = broadcaster.state.transcript_log + [
            {"user": user_text, "assistant": reply, "ts": time.time()}
        ]
        broadcaster.update(transcript_log=log[-50:])
