# Implementation Plan: The Compliance-Safe AI Colleague

Reference: see [claude.md](claude.md) Section 8 for the concept, business framing, and demo narrative this plan implements.

## 1. Goal

Build one codebase that runs on both a laptop (fast dev/iteration, demo fallback) and a Raspberry Pi (4/5, target/preferred hardware per the problem statement). The only difference between platforms is a swappable hardware backend (mic/LED/button) and model size; the reasoning pipeline, memory store, and business logic are identical.

## 2. Design Principle: Hardware Abstraction

All physical I/O (button, LED, microphone) sits behind a single interface so the rest of the app never branches on platform:

```
HardwareIO (abstract)
├── LaptopHardwareIO   -> keyboard key = mute toggle, terminal/OS notification or on-screen indicator = LED, default system mic
└── PiHardwareIO       -> gpiozero Button = mute, gpiozero LED = listening indicator, USB/I2S mic
```

A `config/*.yaml` file picks the backend and model sizes at startup (`--platform laptop|pi`), auto-detected by default (check for `/proc/device-tree/model` containing "Raspberry Pi").

## 3. Tech Stack

- **Language:** Python 3.11+ (only language with mature bindings for every piece below on both x86 laptops and Pi ARM64).
- **Audio capture:** `sounddevice` (cross-platform, works on Windows/Mac/Linux and Pi).
- **STT:** `faster-whisper` (CTranslate2-based, easy pip install, runs CPU-only) with model size `tiny.en`/`base.en` on Pi, `small.en`/`base.en` on laptop.
- **Reasoning (local LLM):** `llama-cpp-python` (wraps llama.cpp). Model: Llama-3.2-3B-Instruct or Phi-3-mini, GGUF, quantized Q4_K_M on Pi; can use a larger quant (Q5/Q8) or the same on laptop for faster iteration.
- **Memory store:** SQLite (`sqlite3`, stdlib) for structured notes/action items + a `vectors` table for embeddings (stored as BLOBs), cosine similarity computed in Python/numpy — no extra DB server needed.
- **Embeddings:** `llama-cpp-python` embedding mode on the same GGUF model, or a small ONNX sentence-transformer via `onnxruntime` if embedding quality on the tiny model is poor.
- **TTS:** `piper-tts` (pip-installable, has prebuilt ARM binaries for Pi and works on laptop).
- **GPIO (Pi only):** `gpiozero`.
- **Online lookup:** `requests` against a single weather/news API, isolated in its own module, only called for whitelisted factual-query intents.
- **Config:** `pyyaml`.

Everything above has a pure-Python or prebuilt-wheel path on both platforms — no compiling llama.cpp/whisper.cpp from source required, which matters for a one-day build.

## 4. Project Structure

```
compliance-safe-ai-colleague/
├── plan.md                     (this file)
├── claude.md                   (problem statement + concept)
├── README.md                   (setup + run instructions)
├── requirements.txt
├── config/
│   ├── laptop.yaml             (model paths/sizes, mic device, mute key binding)
│   └── raspberrypi.yaml        (model paths/sizes, GPIO pin numbers)
├── models/                     (gitignored; downloaded GGUF/whisper/piper models)
├── data/
│   └── memory.db               (gitignored; SQLite store, created at first run)
├── scripts/
│   ├── download_models.sh      (fetches quantized GGUF, whisper, piper voice)
│   ├── setup_laptop.sh
│   └── setup_pi.sh
└── src/
    ├── main.py                 (entrypoint: parse --platform, load config, start orchestrator)
    ├── orchestrator.py         (main loop: listen -> transcribe -> classify -> act -> respond)
    ├── config.py                (loads/validates yaml config, platform auto-detect)
    ├── audio/
    │   └── capture.py           (mic stream -> rolling buffer -> voice-activity segments)
    ├── stt/
    │   └── whisper_engine.py    (faster-whisper wrapper)
    ├── llm/
    │   ├── reasoning.py         (llama-cpp-python wrapper: load model, run prompts)
    │   └── prompts.py           (prompt templates: note-extraction, recall-answering, intent-classification)
    ├── memory/
    │   ├── store.py             (SQLite CRUD for notes/action items)
    │   └── embeddings.py        (embed text, similarity search for recall)
    ├── tts/
    │   └── piper_engine.py      (text -> speech playback)
    ├── online/
    │   └── weather_lookup.py    (single isolated online call, clearly logged/flagged)
    └── io/
        ├── hardware_interface.py (abstract base: mute state, set_listening_led, set_online_led)
        ├── pi_gpio.py            (gpiozero implementation)
        └── laptop_io.py          (keyboard + console/GUI indicator implementation)
```

## 5. Core Data Flow

1. `audio/capture.py` streams mic audio; voice-activity detection segments it into utterances (skip entirely if `hardware_interface` reports muted — no audio is even buffered while muted, satisfying "raw audio never leaves the device" / mute guarantee).
2. `stt/whisper_engine.py` transcribes each utterance segment to text, locally.
3. `llm/reasoning.py` classifies the utterance intent via a local prompt: `{note, action_item, recall_query, online_factual_query, chit_chat}`.
4. Routing:
   - `note` / `action_item` -> written to `memory/store.py` (with timestamp, embedding).
   - `recall_query` -> `memory/embeddings.py` finds top-k similar past notes -> `llm/reasoning.py` composes an answer from them (local RAG).
   - `online_factual_query` -> `hardware_interface.set_online_led(True)` -> `online/weather_lookup.py` fetches fact -> LLM phrases the reply -> LED reset. This is the one path allowed to touch the network, and it never sees stored memory or reasoning context beyond the single fact requested.
   - `chit_chat` -> direct local LLM reply, no storage.
5. `tts/piper_engine.py` speaks the reply.
6. `hardware_interface` LED reflects state throughout: listening (solid), processing (blink), online lookup (distinct color/pattern), muted (off).

## 6. Config Files (sketch)

`config/raspberrypi.yaml`:
```yaml
platform: raspberrypi
stt_model: tiny.en
llm_model: models/llama-3.2-3b-instruct.Q4_K_M.gguf
llm_context: 2048
embedding_model: same_as_llm
gpio:
  mute_button_pin: 17
  listening_led_pin: 27
  online_led_pin: 22
weather_api_key_env: WEATHER_API_KEY
```

`config/laptop.yaml`:
```yaml
platform: laptop
stt_model: base.en
llm_model: models/llama-3.2-3b-instruct.Q4_K_M.gguf
llm_context: 4096
embedding_model: same_as_llm
mute_key: "m"
weather_api_key_env: WEATHER_API_KEY
```

## 7. Build Phases (hackathon day)

1. **Scaffold + config loading** — repo structure, `config.py`, platform auto-detect, `requirements.txt`. Verify `main.py --platform laptop` and `--platform pi` both load without error (Pi backend stubbed until hardware is available).
2. **Local reasoning pipeline standalone** — get `stt/whisper_engine.py` and `llm/reasoning.py` each working from the command line on a sample audio file / text prompt, before wiring the full loop. Biggest latency-risk item; validate first.
3. **Memory store + recall** — `memory/store.py` + `memory/embeddings.py`, test note-in/recall-out with synthetic data.
4. **TTS + full orchestrator loop** — wire `orchestrator.py` end-to-end on laptop with `laptop_io.py` (keyboard mute + console LED simulation).
5. **Online lookup isolation** — add `online/weather_lookup.py` and the intent-routing branch; confirm it is the only module importing `requests`.
6. **Port to Pi** — implement `pi_gpio.py`, swap in Pi config, re-test the same orchestrator unchanged. Tune model sizes down if latency is too high.
7. **Demo polish** — LED patterns, mute-cut-buffering proof, scripted 90-second demo from claude.md Section 8.4.

## 8. Testing Checklist (maps to claude.md Section 5)

- [ ] Continuous local sensing visibly running (listening LED / indicator on laptop and Pi).
- [ ] Mute switch immediately stops audio buffering (verify by checking no audio frames are captured while muted, not just that transcription is suppressed).
- [ ] Listening indicator state changes correctly: listening / muted / processing / online-lookup.
- [ ] Full recall-domain interaction on-device: speak a note, later ask a recall question, get correct local RAG answer with no network call (verify via network monitor/log showing zero requests during this path).
- [ ] One online factual lookup (weather) clearly visually distinguished from local reasoning, and confirmed via log that only that module made a network call.
- [ ] Graceful fallback: ask something the small model can't handle well, confirm it says so honestly rather than hallucinating (per claude.md "good to have").
- [ ] Same orchestrator code runs unmodified on both `--platform laptop` and `--platform pi`, only config/backend differs.

## 9. Open Decisions Before Coding

- Exact Pi model/RAM available (4GB vs 8GB) — determines whether 3B Q4 model is comfortable or `tiny.en` + 1B model is safer for latency.
- Physical mic choice for Pi (USB mic vs I2S HAT) — affects `audio/capture.py` device selection only, not architecture.
- Whether embeddings come from the LLM itself (simpler, one model to load) or a separate small embedding model (better recall quality, more RAM) — recommend starting with LLM-based embeddings and only switching if recall quality is poor.
- Weather API provider/key (e.g., Open-Meteo, which needs no API key, is the simplest choice for a demo).
