"""Async client for the local MiniCPM-OCR 1.0 server."""

from __future__ import annotations

import re
from typing import Any

import httpx

from . import config
from .llama import chat

READING_RE = re.compile(r"(?<![\d.])(\d{3,9}(?:\.\d{1,3})?)(?![\d.])")
UNIT_RE = re.compile(r"(m\s*[³3]|立方米|°\s*C|℃|MPa|kPa|kWh|L|升)")


def _normalise_number(text: Any) -> str | None:
    if text is None:
        return None
    value = str(text).replace(",", "").strip()
    match = re.search(r"\d{1,9}(?:\.\d{1,3})?", value)
    if not match:
        return None
    candidate = match.group(0)
    # A long integer with no decimal is usually a serial/model number, not a
    # meter reading.  Do not let it overwrite a decimal reading.
    if "." not in candidate and len(candidate) >= 8:
        return None
    return candidate


async def raw_text(image_b64: str) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Text Recognition:"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                },
            ],
        }
    ]
    result = await chat(
        config.OCR_URL,
        config.OCR_MODEL,
        messages,
        max_tokens=512,
        timeout=240,
    )
    return result["content"]


async def extract(image_b64: str, fields: list[str], instruction: str = "") -> dict[str, Any]:
    keys = ", ".join(f'"{field}"' for field in fields)
    prompt = instruction.strip() or (
        f"Extract the {keys}. Format the output as a JSON object with keys: {keys}. "
        'If an item is not in the image, use "###".'
    )
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                },
            ],
        }
    ]
    result = await chat(
        config.OCR_URL,
        config.OCR_MODEL,
        messages,
        max_tokens=256,
        response_format={"type": "json_object"},
        timeout=240,
    )
    text = result["content"].strip()
    import json

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {}
    return {"text": text, "parsed": parsed, "timings": result.get("timings", {})}


async def verify_reading(
    image_b64: str,
    *,
    raw: str | None = None,
    structured: dict[str, Any] | None = None,
    expected_unit: str | None = None,
    instruction: str = "",
) -> dict[str, Any]:
    """Read a meter and cross-check raw OCR against structured extraction."""

    if raw is None:
        raw = await raw_text(image_b64)
    if structured is None:
        structured = (await extract(image_b64, ["reading", "unit"], instruction))["parsed"]

    reading_struct = _normalise_number(structured.get("reading"))
    reading_raw = _normalise_number(raw)
    unit = structured.get("unit") or ""
    unit_match = UNIT_RE.search(str(unit)) or UNIT_RE.search(raw)
    unit = unit_match.group(1).replace(" ", "") if unit_match else None
    if unit == "m3":
        unit = "m³"

    conflict = bool(reading_struct and reading_raw and reading_struct != reading_raw)
    if reading_struct and reading_raw:
        if reading_struct == reading_raw:
            confidence = 0.9
        elif "." in reading_struct and "." in reading_raw:
            conflict = True
            confidence = 0.45
        else:
            confidence = 0.6
    elif reading_struct or reading_raw:
        confidence = 0.55
    else:
        confidence = 0.0

    reason_parts: list[str] = []
    if not (reading_struct or reading_raw):
        reason_parts.append("未识别到读数")
    if conflict:
        reason_parts.append(f"原始 OCR 与结构化结果不一致（{reading_raw} vs {reading_struct}）")
    if expected_unit and unit and expected_unit not in unit:
        reason_parts.append(f"单位不符合预期（{unit}）")

    return {
        "reading": reading_struct or reading_raw,
        "unit": unit,
        "raw_text": raw,
        "structured": structured,
        "conflict": conflict,
        "confidence": round(confidence, 2),
        "reason": "；".join(reason_parts) or "读数已识别，建议人工确认末位",
    }


async def health() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{config.OCR_URL}/health")
            return {"ok": resp.status_code == 200, "status": resp.json()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
