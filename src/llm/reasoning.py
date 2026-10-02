import requests
from typing import List, Optional

from . import prompts

INTENT_LABELS = ("note", "action_item", "recall_query", "online_factual_query", "chit_chat")


class Reasoner:
    """All reasoning runs through Ollama's local REST API (localhost:11434).
    No data leaves the device — Ollama is llama.cpp packaged as a local server.
    """

    def __init__(self, base_url: str, model: str, embed_model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embed_model = embed_model

    def _complete(self, prompt: str, max_tokens: int = 200) -> str:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": max_tokens,
                    "stop": ["\n", "</s>"],
                },
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()

    def classify_intent(self, text: str, history: str = "") -> str:
        prompt = prompts.INTENT_PROMPT.format(text=text, history=history or "(none yet)")
        result = self._complete(prompt, max_tokens=16).lower().strip()
        for label in INTENT_LABELS:
            if label in result:
                return label
        return "chit_chat"

    def extract_location(self, text: str) -> Optional[str]:
        prompt = prompts.LOCATION_PROMPT.format(text=text)
        location = self._complete(prompt, max_tokens=10).strip()
        return location if location and location.lower() != "none" else None

    def answer_recall(self, query: str, similar_notes: List[str], history: str = "") -> str:
        context = "\n".join(f"- {note}" for note in similar_notes) or "(no relevant notes found)"
        prompt = prompts.RECALL_PROMPT.format(context=context, query=query, history=history or "(none yet)")
        return self._complete(prompt, max_tokens=150)

    def phrase_online_reply(self, query: str, fact: str) -> str:
        prompt = prompts.ONLINE_REPLY_PROMPT.format(query=query, fact=fact)
        return self._complete(prompt, max_tokens=100)

    def chat_reply(self, text: str, history: str = "") -> str:
        prompt = prompts.CHAT_PROMPT.format(text=text, history=history or "(none yet)")
        return self._complete(prompt, max_tokens=150)

    def embed(self, text: str) -> List[float]:
        resp = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.embed_model, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
