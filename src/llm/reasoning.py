from typing import List, Optional

import llama_cpp
from llama_cpp import Llama, LlamaGrammar

from . import prompts

INTENT_LABELS = ("note", "action_item", "recall_query", "online_factual_query", "chit_chat")

# Constrains classify_intent's output to exactly one of INTENT_LABELS at the
# token level. Needed because this is an Instruct-tuned model: even with
# few-shot examples and max_tokens capped short, it tends to answer with
# hedging/explanation ("Based on the rules, the utterance...") rather than a
# bare label, which the plain prompt-based approach can't reliably prevent.
_INTENT_GRAMMAR = LlamaGrammar.from_string(
    "root ::= " + " | ".join(f'"{label}"' for label in INTENT_LABELS)
)


class Reasoner:
    """All reasoning/decision-making lives here, entirely on-device via
    llama.cpp. Nothing in this class ever makes a network call — the one
    permitted online call (weather) lives in src/online/weather_lookup.py
    and is only invoked by the orchestrator after this class classifies an
    utterance as online_factual_query.

    Note: llama-cpp-python's completion/embedding call signatures have
    changed across versions — check `pip show llama-cpp-python` against
    this code if you hit an AttributeError/TypeError here.
    """

    def __init__(self, model_path: str, n_ctx: int = 2048):
        # pooling_type defaults to NONE (one embedding per input token, not
        # per input string) — MEAN gives a single fixed-length vector per
        # call, which is what memory/embeddings.py's cosine_similarity expects.
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            embedding=True,
            pooling_type=llama_cpp.LLAMA_POOLING_TYPE_MEAN,
            verbose=False,
        )

    def _complete(self, prompt: str, max_tokens: int = 200, grammar: Optional[LlamaGrammar] = None) -> str:
        # This Instruct-tuned model reliably answers on the first line, then
        # tends to append unwanted meta-commentary or stage directions after
        # a newline (e.g. "Paris\nAnswer: Paris", "...today?\nNote: I am a
        # private assistant..."). All our replies are short spoken lines, so
        # stopping at the first newline is exactly what we want, not a
        # compromise.
        # Default temperature (0.8) is tuned for creative chat, not for
        # grounded answers that must stick to the given history/notes/fact —
        # observed to cause the same prompt+context to sometimes ignore the
        # provided context and improvise a plausible-sounding wrong answer.
        out = self.llm(prompt, max_tokens=max_tokens, stop=["</s>", "\n"], grammar=grammar, temperature=0.2)
        return out["choices"][0]["text"].strip()

    def classify_intent(self, text: str, history: str = "") -> str:
        prompt = prompts.INTENT_PROMPT.format(text=text, history=history or "(none yet)")
        result = self._complete(prompt, max_tokens=16, grammar=_INTENT_GRAMMAR).lower()
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
        return self.llm.embed(text)
