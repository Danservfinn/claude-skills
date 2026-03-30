#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="$HOME/.openclaw/envs/suno-clone"
PY311="/opt/homebrew/opt/python@3.11/bin/python3.11"

echo "=== Suno Clone Setup ==="

# System deps
echo "[1/4] System dependencies..."
for pkg in ffmpeg chromaprint yt-dlp; do
  if brew list "$pkg" &>/dev/null; then
    echo "  $pkg already installed"
  else
    echo "  Installing $pkg..."
    brew install "$pkg"
  fi
done

if ! command -v fpcalc &>/dev/null; then
  echo "ERROR: fpcalc not found after chromaprint install"
  exit 1
fi
echo "  fpcalc OK"

# Python venv
echo "[2/4] Python venv (3.11)..."
mkdir -p "$(dirname "$VENV_DIR")"
if [ ! -d "$VENV_DIR" ]; then
  uv venv --python "$PY311" "$VENV_DIR"
else
  echo "  Venv already exists"
fi
source "$VENV_DIR/bin/activate"

# Core analysis
echo "[3/4] Core packages..."
uv pip install essentia librosa soundfile pyacoustid numpy requests pyyaml scikit-learn

python -c "
from essentia.standard import MonoLoader, RhythmExtractor2013, KeyExtractor
print('  essentia OK')
"
python -c "
import librosa, soundfile, acoustid
print('  librosa + soundfile + pyacoustid OK')
"

# MLX + structure analysis
echo "[4/4] MLX + structure packages..."
uv pip install demucs-mlx
python -c "import demucs_mlx; print('  demucs-mlx OK')"

uv pip install allin1 2>/dev/null && \
  python -c "import allin1; print('  allin1 OK')" 2>/dev/null || \
  echo "  WARN: allin1 install failed — will use fallback segmenter"

# Directory setup
mkdir -p "$HOME/.openclaw/data/suno-clone" /tmp/suno-clone

echo ""
echo "=== Setup Complete ==="
echo "Venv: $VENV_DIR"
echo "Data: $HOME/.openclaw/data/suno-clone"
echo "Activate: source $VENV_DIR/bin/activate"
