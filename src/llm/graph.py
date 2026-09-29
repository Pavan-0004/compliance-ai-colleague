from pathlib import Path
from typing import Annotated, Callable, List, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from ..online.weather_lookup import get_weather
from ..state import Stage, broadcaster

CONVERSATION_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "conversation.db"
MAX_HISTORY_TURNS = 8

# SqliteSaver.from_conn_string() is a generator-based context manager; if
# nothing keeps a reference to the CM object itself (only the yielded
# checkpointer), Python garbage-collects the generator, which runs its
# cleanup code and closes the sqlite connection out from under us. This
# list just keeps every CM alive for the process lifetime.
_open_checkpointer_cms = []


class Turn(TypedDict):
    user: str
    assistant: str


def _trim_history(existing: List[Turn], new: List[Turn]) -> List[Turn]:
    """Custom reducer for the history field: append then cap length, so an
    all-day continuous-listening session doesn't grow the checkpointed state
    (and the SQLite file backing it) without bound."""
    return (existing + new)[-MAX_HISTORY_TURNS:]


class ConversationState(TypedDict):
    text: str
    intent: str
    reply: str
    history: Annotated[List[Turn], _trim_history]


def _format_history(history: List[Turn]) -> str:
    if not history:
        return "(no earlier turns yet)"
    lines = [f'User: {t["user"]}\nColleague: {t["assistant"]}' for t in history]
    return "\n".join(lines)


def build_conversation_graph(
    reasoner,
    memory,
    set_stage: Callable[[str], None],
    default_location: str,
    db_path: Path = CONVERSATION_DB_PATH,
):
    """Replaces the old if/elif intent routing with an explicit stateful
    graph. The SqliteSaver checkpointer persists conversation state (keyed
    by thread_id — see orchestrator.py) to a local file, entirely offline,
    so multi-turn context (e.g. "what was my previous question") survives
    across turns and process restarts without any cloud service."""

    def classify_node(state: ConversationState) -> dict:
        history = _format_history(state.get("history", []))
        intent = reasoner.classify_intent(state["text"], history=history)
        return {"intent": intent}

    def note_node(state: ConversationState) -> dict:
        text = state["text"]
        embedding = reasoner.embed(text)
        memory.add_note(text, embedding, kind=state["intent"])
        broadcaster.update(notes_count=memory.count())
        reply = "Got it, I've noted that down."
        return {"reply": reply, "history": [{"user": text, "assistant": reply}]}

    def recall_node(state: ConversationState) -> dict:
        text = state["text"]
        history = _format_history(state.get("history", []))
        query_embedding = reasoner.embed(text)
        similar_notes = memory.search(query_embedding, top_k=5)
        reply = reasoner.answer_recall(text, similar_notes, history=history)
        return {"reply": reply, "history": [{"user": text, "assistant": reply}]}

    def online_node(state: ConversationState) -> dict:
        text = state["text"]
        set_stage(Stage.ONLINE_LOOKUP)
        broadcaster.update(last_online_query=text)
        location = reasoner.extract_location(text) or default_location
        fact = get_weather(location)
        reply = reasoner.phrase_online_reply(text, fact)
        broadcaster.update(last_online_query=None)
        return {"reply": reply, "history": [{"user": text, "assistant": reply}]}

    def chitchat_node(state: ConversationState) -> dict:
        text = state["text"]
        history = _format_history(state.get("history", []))
        reply = reasoner.chat_reply(text, history=history)
        return {"reply": reply, "history": [{"user": text, "assistant": reply}]}

    def route_intent(state: ConversationState) -> str:
        return {
            "note": "note",
            "action_item": "note",
            "recall_query": "recall",
            "online_factual_query": "online",
        }.get(state["intent"], "chitchat")

    graph = StateGraph(ConversationState)
    graph.add_node("classify", classify_node)
    graph.add_node("note", note_node)
    graph.add_node("recall", recall_node)
    graph.add_node("online", online_node)
    graph.add_node("chitchat", chitchat_node)

    graph.set_entry_point("classify")
    graph.add_conditional_edges(
        "classify",
        route_intent,
        {"note": "note", "recall": "recall", "online": "online", "chitchat": "chitchat"},
    )
    graph.add_edge("note", END)
    graph.add_edge("recall", END)
    graph.add_edge("online", END)
    graph.add_edge("chitchat", END)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    checkpointer_cm = SqliteSaver.from_conn_string(str(db_path))
    checkpointer = checkpointer_cm.__enter__()
    _open_checkpointer_cms.append(checkpointer_cm)
    return graph.compile(checkpointer=checkpointer)
