import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .orchestrator import Orchestrator
from .state import broadcaster

logging.basicConfig(level=logging.INFO)

_orchestrator: Optional[Orchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orchestrator
    broadcaster.bind_loop(asyncio.get_event_loop())
    _orchestrator = Orchestrator()
    threading.Thread(target=_orchestrator.run, daemon=True, name="orchestrator").start()
    yield


app = FastAPI(title="Compliance-Safe AI Colleague", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/state")
async def get_state():
    return broadcaster.snapshot()


@app.post("/api/mute")
async def toggle_mute():
    _orchestrator.hardware.toggle_mute()
    return broadcaster.snapshot()


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue = broadcaster.subscribe()
    try:
        while True:
            snapshot = await queue.get()
            await websocket.send_json(snapshot)
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.unsubscribe(queue)
