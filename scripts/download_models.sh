#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."

# Override to put model files on a different drive if your primary drive is
# low on space — the LLM alone is ~2GB. Update LLM_MODEL/PIPER_VOICE in .env
# to match if you do (see .env.example). e.g.:
#   MODELS_DIR=/d/hackathon_models bash scripts/download_models.sh
MODELS_DIR="${MODELS_DIR:-models}"
mkdir -p "$MODELS_DIR/piper"

# Learned the hard way: a completely full C:\ during setup caused a
# `bad allocation` crash loading a perfectly valid GGUF (Windows had no room
# left to grow its pagefile), on top of the more obvious truncated-download
# failure. Warn early rather than let either happen silently.
avail_kb=$(df -Pk "$MODELS_DIR" 2>/dev/null | awk 'NR==2 {print $4}')
if [ -n "${avail_kb:-}" ] && [ "$avail_kb" -lt 3145728 ]; then
  echo "WARNING: only $((avail_kb / 1024))MB free on the drive holding '$MODELS_DIR'."
  echo "The LLM download alone is ~2GB. Consider pointing elsewhere, e.g.:"
  echo "  MODELS_DIR=/d/hackathon_models bash $0"
  echo ""
fi

download() {
  local url="$1" out="$2"
  echo "Downloading: $out"
  if curl -fL --progress-bar -o "$out" "$url"; then
    return 0
  fi
  rm -f "$out"
  return 1
}

# --- LLM (GGUF) --------------------------------------------------------
# Filename must match llm_model in config/laptop.yaml and config/raspberrypi.yaml
# (or LLM_MODEL in .env, if MODELS_DIR is not the default "models" dir).
LLM_FILE="$MODELS_DIR/llama-3.2-3b-instruct.Q4_K_M.gguf"
LLM_PRIMARY="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
LLM_FALLBACK="https://huggingface.co/unsloth/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"

if [ -f "$LLM_FILE" ]; then
  echo "Already have $LLM_FILE, skipping."
elif download "$LLM_PRIMARY" "$LLM_FILE"; then
  echo "Got LLM from bartowski/Llama-3.2-3B-Instruct-GGUF."
elif download "$LLM_FALLBACK" "$LLM_FILE"; then
  echo "Got LLM from unsloth/Llama-3.2-3B-Instruct-GGUF (fallback mirror)."
else
  echo "FAILED to download the LLM GGUF from either mirror. Download manually from:"
  echo "  $LLM_PRIMARY"
fi

# --- Piper voices --------------------------------------------------------
# medium = used by config/laptop.yaml, low = used by config/raspberrypi.yaml
# (a faster/smaller voice for the Pi's more limited CPU budget).
declare -A PIPER_VOICE_DIRS=(
  ["en_US-lessac-medium"]="en/en_US/lessac/medium"
  ["en_US-lessac-low"]="en/en_US/lessac/low"
)

for voice in "${!PIPER_VOICE_DIRS[@]}"; do
  dir="${PIPER_VOICE_DIRS[$voice]}"
  for ext in onnx onnx.json; do
    out="$MODELS_DIR/piper/${voice}.${ext}"
    url="https://huggingface.co/rhasspy/piper-voices/resolve/main/${dir}/${voice}.${ext}"
    if [ -f "$out" ]; then
      echo "Already have $out, skipping."
    else
      download "$url" "$out" || echo "FAILED: $url"
    fi
  done
done

# Sanity check — during setup, the medium and low lessac voices were observed
# to sometimes report identical sizes on the HF side; flag it rather than
# silently trusting it.
if [ -f "$MODELS_DIR/piper/en_US-lessac-medium.onnx" ] && [ -f "$MODELS_DIR/piper/en_US-lessac-low.onnx" ]; then
  size_medium=$(wc -c < "$MODELS_DIR/piper/en_US-lessac-medium.onnx")
  size_low=$(wc -c < "$MODELS_DIR/piper/en_US-lessac-low.onnx")
  if [ "$size_medium" -eq "$size_low" ]; then
    echo ""
    echo "WARNING: en_US-lessac-medium.onnx and en_US-lessac-low.onnx are the same"
    echo "size ($size_medium bytes) — double check they're actually distinct voices."
  fi
fi

# --- faster-whisper STT model --------------------------------------------
# Pre-cache both sizes now (one online download each) so src/stt/whisper_engine.py
# can load with local_files_only=True at runtime and never call huggingface.co
# again — otherwise it silently re-validates against the Hub on every startup,
# which is exactly the kind of unexpected network call this project is meant
# to avoid.
echo ""
if conda run -n compliance-ai python -c "import faster_whisper" >/dev/null 2>&1; then
  echo "Pre-caching faster-whisper STT models (tiny.en, base.en)..."
  cat > /tmp/_precache_whisper.py <<'PYEOF'
from faster_whisper import WhisperModel

for size in ("tiny.en", "base.en"):
    print(f"  caching {size}...")
    WhisperModel(size, device="cpu", compute_type="int8")
print("Done.")
PYEOF
  conda run -n compliance-ai python /tmp/_precache_whisper.py
  rm -f /tmp/_precache_whisper.py
else
  echo "Skipping faster-whisper pre-cache — 'compliance-ai' conda env / faster-whisper"
  echo "not found. It will download itself on first real run instead (one-time)."
fi
echo ""
echo "Optional smaller LLM for a lower-RAM Raspberry Pi (not downloaded by default):"
echo "  https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
echo "  (if you switch to it, update llm_model in config/raspberrypi.yaml to match)"

if [ "$MODELS_DIR" != "models" ]; then
  echo ""
  echo "MODELS_DIR was set to '$MODELS_DIR' — update .env to match (config.py"
  echo "resolves absolute paths as-is, so an absolute MODELS_DIR works directly):"
  echo "  LLM_MODEL=$MODELS_DIR/llama-3.2-3b-instruct.Q4_K_M.gguf"
  echo "  PIPER_VOICE=$MODELS_DIR/piper/en_US-lessac-medium.onnx"
fi
