"""MiniCPM-OCR Jev: candidate-vs-image consistency scoring.

Jev is a 2B decision model.  It takes the original region image, a rendered
image of the candidate OCR text, and the candidate text, and returns
`prob_1` = P(candidate is consistent with the original).  We use it as an OCR
correctness gate: high score -> accept, low score -> human review.

The engine is the official llama.cpp decision-model endpoint `/v1/systemone`
(started by `scripts/run_models.sh` on :8083).  No cloud call.
"""
from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

from . import config

_FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_candidate(text: str, width: int, height: int) -> bytes:
    """Render the candidate OCR text into a white image, similar to a document."""
    w = max(320, int(width))
    h = max(90, int(height))
    im = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(im)
    font = _font(max(28, min(56, int(h * 0.45))))
    draw.text((20, max(12, int(h * 0.18))), text, font=font, fill="black")
    out = BytesIO()
    im.save(out, format="PNG")
    return out.getvalue()


def _data_url(data: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


async def score(original_png: bytes, text: str) -> dict:
    """Return `{prob_1, error}` for one OCR candidate."""
    if not text.strip():
        return {"prob_1": None, "error": "empty candidate text"}
    try:
        with Image.open(BytesIO(original_png)) as im:
            w, h = im.size
    except Exception:
        w, h = 760, 140
    render = render_candidate(text, w, h)
    body = {
        "state": text,
        "files": [_data_url(original_png), _data_url(render)],
        "questions": {"consistency": {"type": "choice", "criteria": {"0": None, "1": None}}},
    }
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(f"{config.JEV_URL}/v1/systemone", json=body)
            resp.raise_for_status()
            payload = resp.json()
        probs = payload["answers"]["consistency"]["probabilities"]
        return {"prob_1": float(probs["1"]), "raw": payload}
    except Exception as exc:  # noqa: BLE001 - surface a clear fallback
        return {"prob_1": None, "error": f"{type(exc).__name__}: {exc}"}


async def health() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{config.JEV_URL}/health")
            return {"ok": resp.status_code == 200, "status": resp.json()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
