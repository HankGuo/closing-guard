#!/usr/bin/env bash
# Closing Guard — one-command local demo.
#
# What it does:
#   1. checks required tools (uv, node, llama-server, python3)
#   2. creates .venv and installs Python deps (skip if present)
#   3. downloads MiniCPM GGUF weights if missing (~5.5GB, skip if present)
#   4. builds the web UI (skip if web/dist exists)
#   5. starts model servers (:8081/:8082) and the API (:8010) in background
#   6. prints the URL when the API is ready
#
# Usage:
#   bash scripts/quickstart.sh              # full run
#   bash scripts/quickstart.sh --check      # only verify toolchain
#   bash scripts/quickstart.sh --no-models  # skip model download (if already present)
#
# Stop everything with: make stop && kill $(cat runs/api.pid)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODELS_DIR="${CG_MODELS_DIR:-$HOME/.cache/closing-guard/models}"
CHECK_ONLY=0
NO_MODELS=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    --no-models) NO_MODELS=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$1"; }
step() { printf '\n\033[1m%s\033[0m\n' "$1"; }

MISSING=0
need_soft() {
  if command -v "$1" >/dev/null 2>&1; then ok "$1"; else printf '  \033[33m!\033[0m %s 未安装（%s）\n' "$1" "$2"; fi
}
need() {
  if command -v "$1" >/dev/null 2>&1; then ok "$1"; else bad "$1 未安装${2:+（$2）}"; MISSING=1; fi
}

if uname -s 2>/dev/null | grep -qiE "mingw|msys|cygwin"; then
  printf '\n\033[33m检测到 Windows 环境\033[0m\n'
  echo "  官方只在 macOS / Linux（含 WSL2）上验证过。"
  echo "  Windows 请用 WSL2（Ubuntu）跑本脚本；Git Bash 下 llama.cpp 与路径处理未验证。"
  echo
fi

step "1/5 检查工具链"
need python3
need_soft uv "可选：没有 uv 会自动回退到 python3 -m venv"
need node "macOS: brew install node｜Ubuntu: apt install nodejs npm（需 ≥20）"
need npm
need llama-server "macOS: brew install llama.cpp｜Ubuntu: 源码编译或下载 release 二进制"
need_soft ffmpeg "可选，仅重新生成视频时需要"

if [ "$MISSING" -eq 1 ]; then
  echo
  echo "缺少依赖，先安装上面标 ✗ 的工具再重跑本脚本。" >&2
  exit 1
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
  echo
  ok "工具链完整（--check 模式，未做任何改动）"
  exit 0
fi

step "2/5 安装 Python 依赖"
if [ -x .venv/bin/python ] && .venv/bin/python -c "import fastapi, cv2, weasyprint" >/dev/null 2>&1; then
  ok ".venv 已就绪，跳过"
else
  rm -rf .venv
  if command -v uv >/dev/null 2>&1; then
    uv venv --python 3.11 .venv
    uv pip install --python .venv/bin/python -q -r server/requirements-dev.txt
  else
    python3 -m venv .venv
    .venv/bin/python -m pip install -q --upgrade pip
    .venv/bin/python -m pip install -q -r server/requirements-dev.txt
  fi
  ok "已创建 .venv 并安装依赖"
fi

step "3/5 准备模型权重"
if [ "$NO_MODELS" -eq 1 ]; then
  ok "--no-models，跳过下载"
elif [ -f "$MODELS_DIR/MiniCPM-V-4_7-1B-Q4_K_M.gguf" ] && \
     [ -f "$MODELS_DIR/mmproj-v47-f16.gguf" ] && \
     [ -f "$MODELS_DIR/MiniCPM-OCR-1_0-Q8_0.gguf" ] && \
     [ -f "$MODELS_DIR/mmproj-ocr-4x.gguf" ] && \
     [ -f "$MODELS_DIR/MiniCPM-OCR-Jev-Q4_K_M.gguf" ] && \
     [ -f "$MODELS_DIR/mmproj-jev-f16.gguf" ]; then
  ok "模型已下载，跳过（$MODELS_DIR）"
else
  echo "  下载约 5.5GB 到 $MODELS_DIR（首次较慢，可中断重跑）"
  CG_MODELS_DIR="$MODELS_DIR" bash scripts/download_models.sh
  ok "模型下载完成"
fi

step "4/5 构建 Web 界面"
if [ -f web/dist/index.html ]; then
  ok "web/dist 已存在，跳过"
else
  ( cd web && npm ci --silent && npm run build --silent )
  ok "前端构建完成"
fi

step "5/5 启动模型服务与 API"
if [ -f runs/models.pids ] && kill -0 "$(awk 'NR==1{print $1}' runs/models.pids)" 2>/dev/null; then
  ok "模型服务已在运行"
else
  CG_MODELS_DIR="$MODELS_DIR" bash scripts/run_models.sh
  ok "模型服务已启动（:8081 VLM / :8082 OCR / :8083 JEV）"
fi

mkdir -p runs/logs
if curl -fsS http://127.0.0.1:8010/api/health >/dev/null 2>&1; then
  ok "API 已在运行（:8010）"
  lsof -ti tcp:8010 -sTCP:LISTEN > runs/api.pid 2>/dev/null || true
else
  if lsof -ti tcp:8010 -sTCP:LISTEN >/dev/null 2>&1; then
    bad "8010 端口被占用但不是本项目的 API"
    exit 1
  fi
  ( cd server && exec ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 ) \
      > runs/logs/api.log 2>&1 &
  echo $! > runs/api.pid
  ok "API 启动中（日志 runs/logs/api.log）"
fi

echo
echo "  等待 API 就绪..."
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8010/api/health >/dev/null 2>&1; then
    printf '\n  \033[32m演示已就绪\033[0m → http://localhost:8010\n'
    printf '  停止：make stop && kill %s\n' "$(cat runs/api.pid 2>/dev/null || echo '')"
    exit 0
  fi
  sleep 1
done

echo
echo "  API 30 秒内未就绪，检查 runs/logs/api.log" >&2
exit 1
