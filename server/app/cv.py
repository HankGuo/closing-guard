"""Image quality and classical-CV geometry checks.

The CV layer is intentionally a *cross-check*, not the sole judge.  It answers
one narrow question ("did the handle move relative to the reference?") and the
VLM answers the semantic question ("does this look closed?").  If either is
uncertain, the agent returns `unsure` and asks the operator to re-capture.
"""

from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np

from . import config


def decode(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("cannot decode image")
    return image


def quality(image_bytes: bytes) -> dict[str, Any]:
    image = decode(image_bytes)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())
    reasons: list[str] = []
    if blur < config.QUALITY_MIN_BLUR:
        reasons.append("画面模糊，请拿稳手机或重新对焦")
    if brightness < config.QUALITY_MIN_BRIGHTNESS:
        reasons.append("画面过暗，请打开手电或增加照明")
    if brightness > config.QUALITY_MAX_BRIGHTNESS:
        reasons.append("画面过亮/过曝，请避开直射灯光")
    if contrast < config.QUALITY_MIN_CONTRAST:
        reasons.append("画面对比度不足，请靠近检查点")
    return {
        "ok": not reasons,
        "blur": round(blur, 2),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "reason": "；".join(reasons),
    }


def flame_check(image_bytes: bytes) -> dict[str, Any]:
    """Conservative flame-colour detector.

    A small VLM can miss a blue burner flame in a dark photo.  Saturated blue
    and orange regions are a cheap, explainable cross-check; a suspected flame
    forces the gas-valve checkpoint to FAIL rather than PASS.
    """

    image = decode(image_bytes)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    blue = cv2.inRange(hsv, np.array([85, 80, 170]), np.array([140, 255, 255]))
    orange = cv2.inRange(hsv, np.array([0, 120, 170]), np.array([25, 255, 255]))
    area = float(image.shape[0] * image.shape[1])
    ratio = float((cv2.countNonZero(blue) + cv2.countNonZero(orange)) / area)
    return {
        "suspected": ratio > 0.004,
        "ratio": round(ratio, 4),
        "reason": "检测到高饱和火焰色区域" if ratio > 0.004 else "未检测到明显火焰色",
    }


def _crop_roi(image: np.ndarray, roi: list[float] | None) -> np.ndarray:
    h, w = image.shape[:2]
    if not roi:
        return image[int(h * 0.15) : int(h * 0.85), int(w * 0.15) : int(w * 0.85)]
    x, y, rw, rh = roi
    x0 = max(0, int(x * w))
    y0 = max(0, int(y * h))
    x1 = min(w, int((x + rw) * w))
    y1 = min(h, int((y + rh) * h))
    if x1 <= x0 or y1 <= y0:
        return image
    return image[y0:y1, x0:x1]


def dominant_angle(image_bytes: bytes, roi: list[float] | None = None) -> dict[str, Any]:
    """Return the dominant long-line angle inside the ROI.

    The angle is in degrees in [0, 180).  This is used only as a relative
    check against a reference image captured in the known-good state.
    """

    image = decode(image_bytes)
    crop = _crop_roi(image, roi)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 50, 150)
    h, w = gray.shape[:2]
    min_len = max(30, int(min(h, w) * 0.22))
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=max(25, int(min(h, w) * 0.12)),
        minLineLength=min_len,
        maxLineGap=max(8, int(min(h, w) * 0.04)),
    )
    if lines is None:
        return {"ok": False, "angle": None, "confidence": 0.0, "reason": "未检测到有效直线"}

    buckets: dict[int, float] = {}
    total = 0.0
    for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        length = math.hypot(x2 - x1, y2 - y1)
        if length < min_len:
            continue
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180.0
        # 2-degree buckets make the estimate robust to pixel noise.
        bucket = int(round(angle / 2.0)) * 2
        buckets[bucket] = buckets.get(bucket, 0.0) + length
        total += length

    if not buckets:
        return {"ok": False, "angle": None, "confidence": 0.0, "reason": "未检测到有效直线"}

    bucket, weight = max(buckets.items(), key=lambda kv: kv[1])
    confidence = min(1.0, weight / total) if total else 0.0
    return {
        "ok": True,
        "angle": float(bucket % 180),
        "confidence": round(confidence, 3),
        "reason": f"主方向约 {bucket % 180}°",
    }


def angle_delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    d = abs((a - b) % 180.0)
    return float(min(d, 180.0 - d))


def valve_geometry(
    current_bytes: bytes,
    reference_bytes: bytes | None,
    roi: list[float] | None = None,
    tolerance: float | None = None,
) -> dict[str, Any]:
    tolerance = config.ANCHOR_ANGLE_TOLERANCE if tolerance is None else tolerance
    current = dominant_angle(current_bytes, roi)
    flame = flame_check(current_bytes)
    if not current["ok"]:
        return {
            "ok": False,
            "angle": None,
            "reference_angle": None,
            "delta": None,
            "confidence": current["confidence"],
            "reason": current["reason"],
            "flame": flame,
        }
    if reference_bytes is None:
        return {
            "ok": True,
            "angle": current["angle"],
            "reference_angle": None,
            "delta": None,
            "confidence": current["confidence"],
            "reason": "无参考图，仅记录主方向",
            "flame": flame,
        }
    reference = dominant_angle(reference_bytes, roi)
    delta = angle_delta(current["angle"], reference.get("angle"))
    passed = delta is not None and delta <= tolerance
    return {
        "ok": passed,
        "angle": current["angle"],
        "reference_angle": reference.get("angle"),
        "delta": round(delta, 2) if delta is not None else None,
        "confidence": min(current["confidence"], reference.get("confidence", 0.0)),
        "reason": (
            f"与参考图夹角差 {delta:.1f}°（容差 {tolerance:.0f}°）"
            if delta is not None
            else "参考图未检测到有效直线"
        ),
        "flame": flame,
    }
