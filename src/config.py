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
    stt_model: str
    llm_model: str
    llm_context: int
    piper_voice: str
    default_location: str
    backend_host: str
    backend_port: int
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

    # .env values (LLM_MODEL, STT_MODEL, etc.) override config/<device>.yaml
    # when set, so swapping a model is a one-line .env edit with no yaml or
    # code changes needed. Unset .env vars fall back to the yaml as before.
    llm_model = os.getenv("LLM_MODEL", raw["llm_model"])
    piper_voice = os.getenv("PIPER_VOICE", raw["piper_voice"])

    _config = Config(
        device=device,
        stt_model=os.getenv("STT_MODEL", raw["stt_model"]),
        llm_model=str(ROOT_DIR / llm_model),
        llm_context=int(os.getenv("LLM_CONTEXT", raw["llm_context"])),
        piper_voice=str(ROOT_DIR / piper_voice),
        default_location=os.getenv("DEFAULT_LOCATION", raw.get("default_location", "Bengaluru")),
        backend_host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        backend_port=int(os.getenv("BACKEND_PORT", "8000")),
        raw=raw,
    )
    return _config
