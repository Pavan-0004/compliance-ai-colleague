INTENT_PROMPT = """You are the intent classifier for a private, on-device AI colleague.
Classify the following utterance into exactly one label:
note, action_item, recall_query, online_factual_query, chit_chat

Rules:
- note: a statement worth remembering (a decision, fact, or detail from a conversation).
- action_item: a task or follow-up someone needs to do.
- recall_query: a question asking to recall something said earlier — either a
  stored note, or something from the recent conversation itself (e.g. "what did
  I just ask you").
- online_factual_query: a question about real-time public facts (weather, news, date/time) — never personal or confidential.
- chit_chat: anything else (greetings, small talk, unclear).

Examples:
Utterance: "Remember that the Henderson account renewal deadline is next Friday."
Label: note

Utterance: "What was my previous question?"
Label: recall_query

Utterance: "What did we decide about the Henderson account?"
Label: recall_query

Utterance: "Call the client back tomorrow morning."
Label: action_item

Utterance: "What's the weather like today?"
Label: online_factual_query

Utterance: "Hey, how's it going?"
Label: chit_chat

Recent conversation (for context only, may be empty):
{history}

Utterance: "{text}"
Label:"""

LOCATION_PROMPT = """Extract a single city or place name mentioned in this text, or say "none" if there isn't one.
Do not guess or invent a place that isn't in the text.

Text: "What's the weather like in Chicago tomorrow?"
Place: Chicago

Text: "What's the weather like today?"
Place: none

Text: "{text}"
Place:"""

RECALL_PROMPT = """You are a private, on-device memory assistant. Answer the question using
ONLY the recent conversation and stored notes below.

If the question asks about the conversation itself (e.g. "what was my
previous question", "what did I just say"), the answer is the text of the
relevant "User:" line in the transcript below — NOT the "Colleague:" reply
that followed it. Quote that line back directly rather than treating this
as something to search for. Otherwise, use the stored notes. If neither
contains the answer, say so honestly instead of guessing.

Recent conversation:
{history}

Stored notes:
{context}

Question: {query}
Answer:"""

ONLINE_REPLY_PROMPT = """A user asked a factual question. Here is the looked-up fact. Phrase a short,
natural spoken reply using it. Output only the words to speak — no stage
directions, tone descriptions, or parentheticals.

Question: {query}
Fact: {fact}
Reply:"""

CHAT_PROMPT = """You are a concise, professional on-device AI colleague. Use the recent
conversation for context if it's relevant; otherwise ignore it.

Recent conversation:
{history}

User: {text}
Reply:"""
