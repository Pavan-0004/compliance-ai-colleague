# Compliance-Safe AI Colleague

An on-device meeting-memory and task assistant. All audio capture, transcription,
and reasoning run locally; the only network call is an isolated weather lookup
(`src/online/weather_lookup.py`).

See [claude.md](claude.md) for the problem statement and business framing, and
[plan.md](plan.md) for the full architecture and build plan this scaffold follows.

## Status

- [x] Project scaffold
- [x] Laptop backend pipeline (mic -> local STT -> local LLM -> local memory -> local TTS)
- [x] React dashboard (live pipeline status, transcript, mute control)
- [x] LangGraph conversation graph (`src/llm/graph.py`) — replaces the old if/elif
      intent routing and adds persistent multi-turn conversation memory (a local
      SQLite checkpointer, `data/conversation.db`, keyed by a daily thread_id) —
      platform-agnostic, so it applies to laptop and Pi identically
- [ ] Raspberry Pi GPIO backend (`src/io/pi_gpio.py` is a placeholder — next phase, see plan.md Phase 6)

## Quick start (laptop)

Requires Python 3.11/3.12 (see why below) and Node.js for the frontend.
Two backend paths — pick one:

### Option A: conda (recommended)

```bash
bash scripts/setup_laptop.sh     # creates+fills a 'compliance-ai' conda env
conda activate compliance-ai
bash scripts/download_models.sh  # downloads the LLM + Piper voice + STT models
python -m src.main                # starts the backend at http://127.0.0.1:8000
```

### Option B: plain venv

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash
# or: .venv\Scripts\Activate.ps1   # PowerShell
# or: source .venv/bin/activate    # macOS/Linux

# llama-cpp-python has no PyPI wheels at all (source dist only there), so a
# plain `pip install -r requirements.txt` tries to compile it from source —
# which needs a full C++ toolchain (Visual Studio Build Tools on Windows)
# most machines don't have. Install it from its own prebuilt CPU wheel index
# first to skip that entirely:
pip install llama-cpp-python --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
pip install -r requirements.txt

bash scripts/download_models.sh
python -m src.main
```

Then, in a second terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (default `http://127.0.0.1:5173`). It connects to the
backend's `/ws` WebSocket and shows, in real time: the current pipeline stage
(listening / muted / transcribing / reasoning / online lookup / speaking), a
mute button, the live conversation log, and the count of notes stored in local
memory.

Optionally copy `.env.example` to `.env` first to customize the device, default
weather location, or model paths — see the comments in that file. It works fine
with no `.env` at all (sane defaults apply).

### Why Python 3.11/3.12, not newer

Very new Python versions (3.13+) commonly lack prebuilt wheels for compiled
packages like `llama-cpp-python`/`faster-whisper` for months after release,
forcing pip to compile from source. Python 3.12 is what `scripts/setup_laptop.sh`
pins its conda env to, and is the safest bet for prebuilt wheels across every
dependency here.

### Low on disk space?

Both `scripts/setup_laptop.sh` and `scripts/download_models.sh` warn if the
target drive has less than ~3GB free (the LLM alone is ~2GB). If you hit that
warning, point things at a roomier drive instead of your primary one:

```bash
# Before setup_laptop.sh, if conda/pip's default drive is tight:
conda config --append envs_dirs D:/conda_envs
conda config --append pkgs_dirs D:/conda_pkgs
export PIP_CACHE_DIR=D:/pip_cache

# Before/instead of download_models.sh's default models/ dir:
MODELS_DIR=/d/hackathon_models bash scripts/download_models.sh
# then update .env to match (see .env.example):
#   LLM_MODEL=D:/hackathon_models/llama-3.2-3b-instruct.Q4_K_M.gguf
#   PIPER_VOICE=D:/hackathon_models/piper/en_US-lessac-medium.onnx
```

(This isn't hypothetical — during setup here, a completely full C:\ drive
caused a `bad allocation` crash loading a perfectly valid GGUF, because Windows
had no room left to grow its pagefile, on top of a more obvious truncated
download. Moving the model files to a drive with space fixed both.)

## One switch controls the platform

Everything is driven by a single line in `.env`:

```
DEVICE=laptop        # keyboard mute (F9) + on-screen indicator via the React dashboard
DEVICE=raspberrypi   # GPIO button + physical LED (Pi phase)
```

No other code changes are needed. `src/config.py` loads `config/<DEVICE>.yaml`, and
`src/io/__init__.py` picks the matching `HardwareIO` backend. `orchestrator.py` never
branches on platform — it only talks to whatever `HardwareIO` it was given.

## Raspberry Pi

Not implemented yet — `src/io/pi_gpio.py` currently raises `NotImplementedError`
by design, as a placeholder for the next build phase, and `scripts/setup_pi.sh`
is a stub describing what it will do. See `plan.md` Section 7 (Phase 6: Port to
Pi) for what's left: wiring `gpiozero` to the configured GPIO pins in
`config/raspberrypi.yaml`, and validating the same orchestrator/server/frontend
run unmodified with `DEVICE=raspberrypi`. Unverified beyond the architecture
being platform-agnostic by design: `llama-cpp-python`/`faster-whisper` wheel
availability on ARM, and whether the 3B model is comfortable on Pi-class RAM
(a 1B fallback is noted in `scripts/download_models.sh`'s output).

## Project layout

```
src/
  main.py, server.py, orchestrator.py, config.py, state.py
  audio/     mic capture + voice-activity segmentation
  stt/       faster-whisper wrapper
  llm/       llama-cpp-python wrapper + prompt templates + LangGraph conversation graph
  memory/    SQLite note store + embedding similarity search
  tts/       Piper wrapper
  online/    the one isolated network call (weather)
  io/        HardwareIO interface + laptop/pi backends
frontend/    React + Vite dashboard
config/      laptop.yaml / raspberrypi.yaml
scripts/     setup_laptop.sh, download_models.sh, setup_pi.sh (placeholder)
```
