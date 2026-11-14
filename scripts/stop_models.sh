#!/usr/bin/env bash
# Stop the local model servers started by run_models.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT/runs/models.pids"
if [ ! -f "$PID_FILE" ]; then
  echo "no pid file"
  exit 0
fi
while read -r pid name port; do
  if kill -0 "$pid" 2>/dev/null; then
    echo "stopping $name ($pid, :$port)"
    kill "$pid" 2>/dev/null || true
  fi
done <"$PID_FILE"
rm -f "$PID_FILE"
