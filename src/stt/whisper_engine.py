import logging

import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class WhisperEngine:
    """Local speech-to-text only — never uploads audio anywhere. Model size
    is picked per-platform in config/*.yaml (base.en on laptop, tiny.en on Pi).

    faster-whisper fetches its model from Hugging Face on first use and
    caches it locally, but by default it still calls out to huggingface.co
    on every startup afterwards just to revalidate the cache — which is
    exactly the kind of silent network call this project's compliance-safe
    story is supposed to rule out. Once the model is cached (see
    scripts/download_models.sh), we load with local_files_only=True so
    startup never touches the network at all; only a genuinely missing
    cache falls back to an online, one-time download.
    """

    def __init__(self, model_size: str = "base.en", device: str = "cpu", compute_type: str = "int8"):
        try:
            self.model = WhisperModel(
                model_size, device=device, compute_type=compute_type, local_files_only=True
            )
        except Exception:
            logger.warning(
                "STT model '%s' not found in local cache — downloading once from "
                "Hugging Face. Re-run scripts/download_models.sh to pre-cache it "
                "so future startups stay fully offline.",
                model_size,
            )
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(audio, language="en", beam_size=1)
        return " ".join(seg.text.strip() for seg in segments).strip()
