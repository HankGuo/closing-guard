"""Runtime configuration for Closing Guard.

All paths can be overridden with environment variables so that the same code
runs on a laptop, a shop mini-PC, or an Android emulator test harness.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "server" / "app"
TEMPLATE_DIR = APP_DIR / "templates"
WEB_DIST = BASE_DIR / "web" / "dist"
DATA_DIR = Path(os.getenv("CG_DATA_DIR", BASE_DIR / "data"))
RUNS_DIR = Path(os.getenv("CG_RUNS_DIR", BASE_DIR / "runs"))
CHECKLIST_DIR = Path(os.getenv("CG_CHECKLIST_DIR", BASE_DIR / "config" / "checklists"))
MODELS_DIR = Path(
    os.getenv("CG_MODELS_DIR", str(Path.home() / ".cache" / "closing-guard" / "models"))
)

for _p in (DATA_DIR, RUNS_DIR, CHECKLIST_DIR, MODELS_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# Local model servers.  These are *local* HTTP services started by
# `scripts/run_models.sh`; no cloud API is involved.
VLM_URL = os.getenv("CG_VLM_URL", "http://127.0.0.1:8081")
OCR_URL = os.getenv("CG_OCR_URL", "http://127.0.0.1:8082")
JEV_URL = os.getenv("CG_JEV_URL", "http://127.0.0.1:8083")

VLM_MODEL = os.getenv("CG_VLM_MODEL", "MiniCPM-V-4.7-1B")
OCR_MODEL = os.getenv("CG_OCR_MODEL", "MiniCPM-OCR-1.0")
JEV_MODEL = os.getenv("CG_JEV_MODEL", "MiniCPM-OCR-Jev")

# Public base URL is used for the QR code in the PDF report.  It can be a
# LAN address in a real shop, or http://localhost:8000 in the emulator demo.
PUBLIC_BASE_URL = os.getenv("CG_PUBLIC_BASE_URL", "http://localhost:8000")

# Image-quality gates.  They are intentionally conservative: a bad image
# should become "unsure" and be re-captured rather than silently passed.
QUALITY_MIN_BLUR = float(os.getenv("CG_QUALITY_MIN_BLUR", "15"))
QUALITY_MIN_BRIGHTNESS = float(os.getenv("CG_QUALITY_MIN_BRIGHTNESS", "20"))
QUALITY_MAX_BRIGHTNESS = float(os.getenv("CG_QUALITY_MAX_BRIGHTNESS", "252"))
QUALITY_MIN_CONTRAST = float(os.getenv("CG_QUALITY_MIN_CONTRAST", "12"))

# Fusion thresholds.
VLM_MIN_CONFIDENCE = float(os.getenv("CG_VLM_MIN_CONFIDENCE", "0.55"))
JEV_MIN_SCORE = float(os.getenv("CG_JEV_MIN_SCORE", "0.80"))
JEV_REVIEW_SCORE = float(os.getenv("CG_JEV_REVIEW_SCORE", "0.20"))
ANCHOR_ANGLE_TOLERANCE = float(os.getenv("CG_ANGLE_TOLERANCE", "12"))
CV_MIN_CONFIDENCE = float(os.getenv("CG_CV_MIN_CONFIDENCE", "0.35"))

VERSION = "0.1.2"
