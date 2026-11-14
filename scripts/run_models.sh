#!/usr/bin/env bash
# Start the local MiniCPM model servers used by Closing Guard.
# No cloud calls are made by this script or by the application.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${CG_MODELS_DIR:-$HOME/.cache/closing-guard/models}"
LOG_DIR="$ROOT/runs/logs"
PID_FILE="$ROOT/runs/models.pids"
mkdir -p "$LOG_DIR"

VLM_PORT="${CG_VLM_PORT:-8081}"
OCR_PORT="${CG_OCR_PORT:-8082}"
THREADS="${CG_THREADS:-6}"

if ! command -v llama-server >/dev/null 2>&1; then
  echo "llama-server not found. Install it with: brew install llama.cpp" >&2
  exit 1
fi

if [ ! -f "$MODELS_DIR/MiniCPM-V-4_7-1B-Q4_K_M.gguf" ] || \
   [ ! -f "$MODELS_DIR/mmproj-v47-f16.gguf" ] || \
   [ ! -f "$MODELS_DIR/MiniCPM-OCR-1_0-Q8_0.gguf" ] || \
   [ ! -f "$MODELS_DIR/mmproj-ocr-4x.gguf" ] || \
   [ ! -f "$MODELS_DIR/MiniCPM-OCR-Jev-Q4_K_M.gguf" ] || \
   [ ! -f "$MODELS_DIR/mmproj-jev-f16.gguf" ]; then
  echo "Model files missing under $MODELS_DIR" >&2
  echo "Run: CG_MODELS_DIR=$MODELS_DIR scripts/download_models.sh" >&2
  exit 1
fi

start_one() {
  local name="$1"
  local port="$2"
  local model="$3"
  local mmproj="$4"
  local ctx="${5:-8192}"
  local log="$LOG_DIR/$name.log"
  if curl -sf "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
    echo "$name already healthy on :$port"
    return 0
  fi
  echo "starting $name on :$port ..."
  nohup llama-server \
    -m "$MODELS_DIR/$model" \
    --mmproj "$MODELS_DIR/$mmproj" \
    --host 127.0.0.1 --port "$port" \
    -c "$ctx" -t "$THREADS" \
    >"$log" 2>&1 &
  echo "$! $name $port" >>"$PID_FILE"
  for _ in $(seq 1 120); do
    if curl -sf "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
      echo "$name ready"
      return 0
    fi
    sleep 1
  done
  echo "$name failed to start; see $log" >&2
  return 1
}

: >"$PID_FILE"
start_one vlm "$VLM_PORT" "MiniCPM-V-4_7-1B-Q4_K_M.gguf" "mmproj-v47-f16.gguf" 8192
start_one ocr "$OCR_PORT" "MiniCPM-OCR-1_0-Q8_0.gguf" "mmproj-ocr-4x.gguf" 8192
start_one jev "${CG_JEV_PORT:-8083}" "MiniCPM-OCR-Jev-Q4_K_M.gguf" "mmproj-jev-f16.gguf" 32768

echo
echo "VLM  : http://127.0.0.1:$VLM_PORT"
echo "OCR  : http://127.0.0.1:$OCR_PORT"
echo "JEV  : http://127.0.0.1:${CG_JEV_PORT:-8083}"
echo "PIDs : $PID_FILE"
echo "Logs : $LOG_DIR"
