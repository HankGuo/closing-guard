"""Async client for the local llama.cpp MiniCPM-V server."""

from __future__ import annotations

import base64
import json
import re
from typing import Any

import httpx

from . import config

# GBNF grammar for the verdict object.  It forces a valid enum and a 0..1
# confidence even when a small model is tempted to answer in prose.
VERDICT_GRAMMAR = r"""
root ::= "{" ws "\"verdict\"" ws ":" ws verdict ws "," ws "\"confidence\"" ws ":" ws num ws "," ws "\"reason\"" ws ":" ws str ws "}"
verdict ::= "\"pass\"" | "\"fail\"" | "\"unsure\""
num ::= "0" | "1" | "0." [0-9]+ | "1.0"
str ::= "\"" [^"\\]* "\""
ws ::= [ \t\n]*
"""


def b64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("ascii")


def _image_part(image_b64: str) -> dict[str, Any]:
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
    }


async def chat(
    url: str,
    model: str,
    messages: list[dict[str, Any]],
    *,
    max_tokens: int = 192,
    temperature: float = 0.0,
    grammar: str | None = None,
    response_format: dict[str, Any] | None = None,
    timeout: float = 180.0,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    if grammar:
        payload["grammar"] = grammar
    if response_format:
        payload["response_format"] = response_format

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{url}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    return {
        "content": content,
        "timings": data.get("timings", {}),
        "usage": data.get("usage", {}),
        "raw": data,
    }


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _normalise_verdict(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"pass", "passed", "ok", "closed", "safe", "true"}:
        return "pass"
    if text in {"fail", "failed", "open", "unsafe", "false"}:
        return "fail"
    return "unsure"


def _normalise_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number > 1.0:
        number = number / 100.0
    return max(0.0, min(1.0, number))


async def vlm_verdict(
    image_b64: str,
    prompt: str,
    *,
    reference_b64: str | None = None,
    grammar: str | None = VERDICT_GRAMMAR,
    url: str | None = None,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    if reference_b64:
        content.append({"type": "text", "text": "参考图（该检查点的合格状态）："})
        content.append(_image_part(reference_b64))
        content.append({"type": "text", "text": "当前画面："})
    content.append(_image_part(image_b64))
    content.append({"type": "text", "text": prompt})

    messages = [{"role": "user", "content": content}]
    last_error = ""
    for attempt in range(2):
        try:
            result = await chat(
                url or config.VLM_URL,
                config.VLM_MODEL,
                messages,
                max_tokens=192,
                grammar=grammar if attempt == 0 else None,
            )
            parsed = _extract_json(result["content"])
            if parsed is None:
                last_error = f"无法解析模型输出：{result['content'][:120]}"
                continue
            return {
                "verdict": _normalise_verdict(parsed.get("verdict", parsed.get("state"))),
                "confidence": _normalise_confidence(parsed.get("confidence", 0)),
                "reason": str(parsed.get("reason", "")).strip(),
                "observations": parsed.get("observations", []) if isinstance(parsed.get("observations"), list) else [],
                "raw": result["content"],
                "timings": result.get("timings", {}),
            }
        except Exception as exc:  # noqa: BLE001 - surface the real error to the agent
            last_error = f"{type(exc).__name__}: {exc}"
    return {
        "verdict": "unsure",
        "confidence": 0.0,
        "reason": last_error or "模型未返回可用结论",
        "observations": [],
        "raw": None,
        "timings": {},
    }


async def health(url: str | None = None) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{url or config.VLM_URL}/health")
            return {"ok": resp.status_code == 200, "status": resp.json()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
