# Jarvis — Personal Offline AI Companion
## Setup Guide

Everything runs **100% on-device** — no cloud, no internet required after setup.

---

## What You Need to Download

### 1. Python 3.11 or 3.12
- https://www.python.org/downloads/
- During install: ✅ check **"Add Python to PATH"**

### 2. Node.js (for the frontend dashboard)
- https://nodejs.org/en/download — download the **LTS** version

### 3. Ollama (runs the LLM locally)
- https://ollama.com/download — download for Windows
- After installing, open a terminal and pull the two models:
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 4. Whisper.cpp (offline speech-to-text)
Download the pre-built Windows binary + model:
- **Binary (whisper-blas-x64):** https://github.com/ggerganov/whisper.cpp/releases — download `whisper-blas-x64.zip` from the latest release
- **Model file:** https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin

Extract the zip and place the model inside the extracted folder:
```
D:\Arjun\makeathon\whisper-blas-x64\
    whisper-cli.exe
    ggml-base.en.bin
```

> **Note:** Update `config/laptop.yaml` with your actual path if you extract elsewhere.

### 5. Piper TTS Voice Model (offline text-to-speech)
Download **both files** (the model + its config sidecar):

| File | Link |
|---|---|
| `en_US-amy-medium.onnx` (63 MB) | https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx |
| `en_US-amy-medium.onnx.json` (4 KB) | https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json |

Place both files in:
```
models/piper/
    en_US-amy-medium.onnx
    en_US-amy-medium.onnx.json
```

### 6. openWakeWord — Hey Jarvis model
The wake word model downloads automatically the first time you run the backend. No manual download needed.

---

## Project Setup

### Step 1 — Clone the repo
```bash
git clone https://github.com/<your-username>/compliance-ai-colleague.git
cd compliance-ai-colleague
```

### Step 2 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Install frontend dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 4 — Update config for your machine
Edit `config/laptop.yaml` and set your actual Whisper paths:
```yaml
stt_binary: D:/your-path/whisper-blas-x64/whisper-cli.exe
stt_model:  D:/your-path/whisper-blas-x64/ggml-base.en.bin
```

Everything else in the config can stay as-is.

---

## Folder Structure After Setup

```
compliance-ai-colleague/
├── config/
│   └── laptop.yaml          # main config — update whisper paths here
├── models/
│   └── piper/
│       ├── en_US-amy-medium.onnx
│       └── en_US-amy-medium.onnx.json
├── src/                     # Python backend
├── frontend/                # React dashboard
├── data/                    # created automatically (SQLite memory + conversation DB)
└── requirements.txt
```

---

## How to Run

You need **3 terminals** open at the same time.

### Terminal 1 — Start Ollama (LLM server)
```bash
ollama serve
```
> If you see "address already in use" — Ollama is already running, skip this step.

### Terminal 2 — Start the Python backend
```bash
cd compliance-ai-colleague
python -m src.main
```

Wait for these 3 lines in the logs before continuing:
```
Piper ready — greeting will play instantly on wake
Wake word model ready — threshold=0.30
LLM graph ready (model=llama3.2:3b, ...)
Application startup complete.
```

### Terminal 3 — Start the frontend dashboard
```bash
cd compliance-ai-colleague/frontend
npm run dev
```

Open your browser at **http://localhost:5173**

---

## How to Use

1. Open http://localhost:5173 in your browser
2. Say **"Hey Jarvis"** — you'll hear "Hey, what's up?"
3. Ask your question (speak naturally)
4. Jarvis will transcribe → reason → reply with voice
5. After the reply, **ask follow-up questions directly** — no need to say "Hey Jarvis" again (15-second window)
6. After 15 seconds of silence, it goes back to waiting for the wake word
7. Press **F9** or click Mute to mute/unmute the mic

---

## Pipeline Flow

```
👂 Wake Word  →  🎙️ Listening  →  📝 Transcribe  →  🧠 Reasoning  →  🔊 Speaking
                                                                            ↓
                                               💬 Follow-up window (15s)  ←←←
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `FileNotFoundError: whisper-cli.exe` | Update `stt_binary` path in `config/laptop.yaml` |
| `FileNotFoundError: en_US-amy-medium.onnx` | Download Piper model files into `models/piper/` |
| `Connection refused` on LLM calls | Run `ollama serve` in a separate terminal |
| Wake word never triggers | Check mic is not muted; lower `threshold` to `0.2` in `config/laptop.yaml` |
| Frontend shows "Connecting to backend…" | Make sure `python -m src.main` is running |
| Male voice heard | Old backend process running — kill it and restart |

---

## Models Used

| Component | Model | Size | Source |
|---|---|---|---|
| Wake Word | openWakeWord `hey_jarvis` | ~10 MB | Auto-downloaded |
| Speech-to-Text | Whisper `base.en` | ~74 MB | HuggingFace |
| LLM | Llama 3.2 3B (Q4_K_M) | ~2 GB | Ollama |
| Embeddings | nomic-embed-text | ~274 MB | Ollama |
| Text-to-Speech | Piper `en_US-amy-medium` | ~63 MB | HuggingFace |

**Total disk space required:** ~2.5 GB

---

## Hardware Requirements (Laptop)

| Spec | Minimum | Recommended |
|---|---|---|
| RAM | 6 GB | 8 GB+ |
| CPU | 4-core | 6-core+ |
| Storage | 3 GB free | 5 GB free |
| Mic | Any built-in mic | External USB mic |
| OS | Windows 10/11 | Windows 11 |
