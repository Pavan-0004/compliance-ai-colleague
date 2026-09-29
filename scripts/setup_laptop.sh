#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

# llama-cpp-python has no wheels on PyPI (source dist only there), so a plain
# pip install tries to compile it — which needs Visual Studio's C++ build
# tools on Windows and fails without them. Installing from its own prebuilt
# CPU wheel index first avoids that entirely. Python 3.11/3.12 is the safest
# bet for prebuilt wheels across every dependency here (validated on 3.12);
# very new Python versions (e.g. 3.14) commonly lack wheels for these
# compiled packages for months after release.
LLAMA_CPP_WHEEL_INDEX="https://abetlen.github.io/llama-cpp-python/whl/cpu"
ENV_NAME="compliance-ai"

avail_kb=$(df -Pk . 2>/dev/null | awk 'NR==2 {print $4}')
if [ -n "${avail_kb:-}" ] && [ "$avail_kb" -lt 3145728 ]; then
  echo "WARNING: only $((avail_kb / 1024))MB free on this drive. The conda env,"
  echo "pip cache, and model files together need several GB. If this drive is"
  echo "tight, point conda/pip at a roomier one before continuing, e.g.:"
  echo "  conda config --append envs_dirs D:/conda_envs"
  echo "  conda config --append pkgs_dirs D:/conda_pkgs"
  echo "  export PIP_CACHE_DIR=D:/pip_cache"
  echo ""
fi

if command -v conda >/dev/null 2>&1; then
  if ! conda env list | grep -q "^${ENV_NAME} "; then
    conda create -n "$ENV_NAME" python=3.12 -y
  fi
  PIP="conda run -n $ENV_NAME pip"
  echo "Using conda env '$ENV_NAME'. Activate it yourself with: conda activate $ENV_NAME"
else
  echo "conda not found — falling back to a plain venv."
  echo "Make sure this venv's Python is 3.11 or 3.12 (not 3.13+) for best wheel availability."
  python -m venv .venv
  if [ -f .venv/Scripts/activate ]; then
    source .venv/Scripts/activate   # Windows (Git Bash)
  else
    source .venv/bin/activate       # macOS/Linux
  fi
  PIP="pip"
fi

$PIP install --upgrade pip
$PIP install llama-cpp-python --prefer-binary --extra-index-url "$LLAMA_CPP_WHEEL_INDEX"
$PIP install -r requirements.txt

echo ""
echo "Backend dependencies installed."
echo "Next: run scripts/download_models.sh for model download pointers,"
echo "then (after activating the environment) run 'python -m src.main' to start the backend."
