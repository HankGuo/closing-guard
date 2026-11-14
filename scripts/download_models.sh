#!/usr/bin/env bash
# Download the MiniCPM GGUF weights from ModelScope.
# Weights are not committed to git; this script is the reproducible path.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${CG_MODELS_DIR:-$HOME/.cache/closing-guard/models}"
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

fetch() {
  local url="$1" out="$2"
  if [ -f "$out" ]; then
    echo "exists: $out"
    return 0
  fi
  echo "downloading: $out"
  curl -L --retry 3 --max-time 3600 -C - -o "$out" "$url"
}

BASE_VLM="https://modelscope.cn/models/OpenBMB/MiniCPM-V-4.7-1B-gguf/resolve/master"
BASE_OCR="https://modelscope.cn/models/OpenBMB/MiniCPM-OCR-1.0-gguf/resolve/master"
BASE_JEV="https://modelscope.cn/models/OpenBMB/MiniCPM-OCR-Jev-gguf/resolve/master"

fetch "$BASE_VLM/MiniCPM-V-4_7-1B-Q4_K_M.gguf" "MiniCPM-V-4_7-1B-Q4_K_M.gguf"
fetch "$BASE_VLM/mmproj-model-f16.gguf" "mmproj-v47-f16.gguf"
fetch "$BASE_OCR/MiniCPM-OCR-1_0-Q8_0.gguf" "MiniCPM-OCR-1_0-Q8_0.gguf"
fetch "$BASE_OCR/mmproj-model-f16-4x.gguf" "mmproj-ocr-4x.gguf"
fetch "$BASE_JEV/MiniCPM-OCR-Jev-Q4_K_M.gguf" "MiniCPM-OCR-Jev-Q4_K_M.gguf"
fetch "$BASE_JEV/mmproj-model-f16.gguf" "mmproj-jev-f16.gguf"

ls -lh "$MODELS_DIR"
echo
echo "Done. Start the servers with: scripts/run_models.sh"
