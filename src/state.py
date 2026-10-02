import asyncio
from dataclasses import asdict, dataclass, field
from typing import Optional


class Stage:
    """Plain string constants (not an Enum) so they serialize to JSON
    for the WebSocket feed with no extra conversion step."""

    IDLE = "idle"
    WAITING_FOR_WAKE = "waiting_for_wake"
    LISTENING = "listening"
    MUTED = "muted"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    ONLINE_LOOKUP = "online_lookup"
    SPEAKING = "speaking"
    FOLLOW_UP = "follow_up"


@dataclass
class AppState:
    stage: str = Stage.IDLE
    muted: bool = False
    last_transcript: str = ""
    last_reply: str = ""
    transcript_log: list = field(default_factory=list)
    notes_count: int = 0
    last_online_query: Optional[str] = None
    mic_energy: float = 0.0


class StateBroadcaster:
    """The orchestrator runs in a background worker thread and calls update()
    directly from there; call_soon_threadsafe hands each snapshot off to the
    asyncio loop that serves the FastAPI WebSocket, so this is safe to call
    from any thread once bind_loop() has run."""

    def __init__(self):
        self.state = AppState()
        self._subscribers = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        q.put_nowait(self.snapshot())
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)

    def snapshot(self) -> dict:
        return asdict(self.state)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self.state, key, value)
        snap = self.snapshot()
        for q in list(self._subscribers):
            if self.loop:
                self.loop.call_soon_threadsafe(q.put_nowait, snap)
            else:
                q.put_nowait(snap)


broadcaster = StateBroadcaster()
