import time

from .audio.capture import AudioCapture
from .config import get_config
from .io import build_hardware_io
from .llm.graph import build_conversation_graph
from .llm.reasoning import Reasoner
from .memory.store import MemoryStore
from .state import Stage, broadcaster
from .stt.whisper_engine import WhisperEngine
from .tts.piper_engine import PiperEngine


class Orchestrator:
    """Ties mic -> STT -> local LLM -> memory/online routing -> TTS together.
    Runs in a background thread (see server.py); talks to hardware only
    through the HardwareIO interface, so this class is identical on laptop
    and Raspberry Pi."""

    def __init__(self):
        self.config = get_config()
        self.hardware = build_hardware_io(self.config)
        self.audio = AudioCapture(hardware=self.hardware)
        self.stt = WhisperEngine(self.config.stt_model)
        self.reasoner = Reasoner(self.config.llm_model, self.config.llm_context)
        self.memory = MemoryStore()
        self.tts = PiperEngine(self.config.piper_voice)
        self.hardware.on_mute_change(self._on_mute_change)

        # Intent routing + multi-turn conversation memory now live in a
        # LangGraph graph (src/llm/graph.py) instead of an if/elif chain.
        # Its checkpointer persists conversation state to data/conversation.db,
        # keyed by a daily thread_id, so "what did I just ask" works without
        # any cloud call.
        self.graph = build_conversation_graph(
            reasoner=self.reasoner,
            memory=self.memory,
            set_stage=self._set_stage,
            default_location=self.config.default_location,
        )

    def _on_mute_change(self, muted: bool):
        self._set_stage(Stage.MUTED if muted else Stage.LISTENING)

    def _set_stage(self, stage: str):
        self.hardware.set_indicator(stage)
        broadcaster.update(stage=stage, muted=self.hardware.muted)

    def run(self):
        self.hardware.start()
        broadcaster.update(notes_count=self.memory.count())
        self._set_stage(Stage.LISTENING)

        for segment in self.audio.stream_utterances():
            if self.hardware.muted:
                continue

            self._set_stage(Stage.TRANSCRIBING)
            text = self.stt.transcribe(segment)
            if not text.strip():
                self._set_stage(Stage.LISTENING)
                continue

            broadcaster.update(last_transcript=text)
            self._set_stage(Stage.THINKING)
            self._handle_utterance(text)
            self._set_stage(Stage.MUTED if self.hardware.muted else Stage.LISTENING)

    def _handle_utterance(self, text: str):
        # One thread_id per calendar day: conversational short-term memory
        # resets daily rather than growing forever, while long-term notes
        # (memory/store.py) are unaffected and persist indefinitely.
        thread_id = time.strftime("%Y-%m-%d")
        result = self.graph.invoke(
            {"text": text},
            config={"configurable": {"thread_id": thread_id}},
        )
        reply = result["reply"]

        self._set_stage(Stage.SPEAKING)
        broadcaster.update(last_reply=reply)
        self._append_log(text, reply)
        self.tts.speak(reply)

    def _append_log(self, user_text: str, reply: str):
        log = broadcaster.state.transcript_log + [
            {"user": user_text, "assistant": reply, "ts": time.time()}
        ]
        broadcaster.update(transcript_log=log[-50:])
