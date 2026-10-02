import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


@dataclass
class Config:
    device: str
    stt_binary: str
    stt_model: str
    stt_threads: int
    ollama_base_url: str
    ollama_model: str
    ollama_embed_model: str
    piper_voice: str
    default_location: str
    backend_host: str
    backend_port: int
    wake_enabled: bool
    wake_model: str
    wake_threshold: float
    wake_backend: str
    follow_up_window_s: float
    raw: dict


_config: Optional[Config] = None


def get_config() -> Config:
    """Loads .env + config/<DEVICE>.yaml once and caches the result.
    DEVICE is the single switch that picks both the yaml file and,
    via src/io/build_hardware_io, the hardware backend."""
    global _config
    if _config is not None:
        return _config

    device = os.getenv("DEVICE", "laptop").strip().lower()
    if device not in ("laptop", "raspberrypi"):
        raise ValueError(
            f"Unknown DEVICE '{device}' in .env — expected 'laptop' or 'raspberrypi'"
        )

    yaml_path = ROOT_DIR / "config" / f"{device}.yaml"
    with open(yaml_path, "r") as f:
        raw = yaml.safe_load(f)

    # .env values override config/<device>.yaml when set — swap a model or
    # binary with a one-line .env edit, no yaml or code changes needed.
    # Pathlib join with an absolute path returns the absolute path unchanged,
    # so both absolute paths (laptop Windows paths) and relative paths (Pi
    # paths relative to project root) work correctly.
    stt_binary = os.getenv("STT_BINARY", raw["stt_binary"])
    stt_model = os.getenv("STT_MODEL", raw["stt_model"])
    piper_voice = os.getenv("PIPER_VOICE", raw["piper_voice"])

    wake_cfg = raw.get("wake_word", {})
    _config = Config(
        device=device,
        stt_binary=str(ROOT_DIR / stt_binary),
        stt_model=str(ROOT_DIR / stt_model),
        stt_threads=int(os.getenv("STT_THREADS", raw.get("stt_threads", 4))),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", raw.get("ollama_base_url", "http://localhost:11434")),
        ollama_model=os.getenv("OLLAMA_MODEL", raw.get("ollama_model", "llama3.2:3b")),
        ollama_embed_model=os.getenv("OLLAMA_EMBED_MODEL", raw.get("ollama_embed_model", "nomic-embed-text")),
        piper_voice=str(ROOT_DIR / piper_voice),
        default_location=os.getenv("DEFAULT_LOCATION", raw.get("default_location", "Bengaluru")),
        backend_host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        backend_port=int(os.getenv("BACKEND_PORT", "8000")),
        wake_enabled=os.getenv("WAKE_ENABLED", str(wake_cfg.get("enabled", False))).lower() == "true",
        wake_model=os.getenv("WAKE_MODEL", wake_cfg.get("model", "hey_jarvis")),
        wake_threshold=float(os.getenv("WAKE_THRESHOLD", wake_cfg.get("threshold", 0.5))),
        wake_backend=os.getenv("WAKE_BACKEND", wake_cfg.get("backend", "onnx")),
        follow_up_window_s=float(os.getenv("FOLLOW_UP_WINDOW_S", raw.get("follow_up_window_s", 15.0))),
        raw=raw,
    )
    return _config
