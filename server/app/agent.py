"""The Closing Guard agent: capture -> verify -> re-check -> evidence ledger."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from PIL import Image

from . import config, cv, db, jev, llama, ocr, report
from .checklists import load_checklist
from .schemas import (
    CheckpointConfig,
    CheckpointState,
    EvidenceOut,
    SessionOut,
)

MAX_IMAGE_EDGE = 1600


def _prepare_image(image_bytes: bytes) -> bytes:
    """Normalise to RGB JPEG, cap the long edge, and strip EXIF."""

    from io import BytesIO

    with Image.open(BytesIO(image_bytes)) as im:
        im = im.convert("RGB")
        im.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)
        out = BytesIO()
        im.save(out, format="JPEG", quality=90, optimize=True)
        return out.getvalue()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _crop_bytes(image_bytes: bytes, roi: list[float]) -> bytes:
    from io import BytesIO

    with Image.open(BytesIO(image_bytes)) as im:
        w, h = im.size
        x, y, rw, rh = roi
        box = (max(0, int(x * w)), max(0, int(y * h)), min(w, int((x + rw) * w)), min(h, int((y + rh) * h)))
        crop = im.crop(box)
        out = BytesIO()
        crop.save(out, format="PNG")
        return out.getvalue()


def _chain_hash(prev_hash: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    record_hash = _sha256(canonical.encode("utf-8"))
    return _sha256((prev_hash + record_hash).encode("utf-8"))


def _chain_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "session_id": record["session_id"],
        "checkpoint_id": record["checkpoint_id"],
        "image_sha256": record["image_sha256"],
        "captured_at": record["captured_at"],
        "source": record["source"],
        "verdict": record["verdict"],
        "confidence": record["confidence"],
        "reason": record["reason"],
    }


def _reference_bytes(checkpoint: CheckpointConfig) -> bytes | None:
    if not checkpoint.reference:
        return None
    path = Path(checkpoint.reference)
    if not path.is_absolute():
        path = config.DATA_DIR / path
    if not path.exists():
        return None
    return path.read_bytes()


def _fuse(
    checkpoint: CheckpointConfig,
    quality: dict[str, Any],
    cv_result: dict[str, Any] | None,
    vlm_result: dict[str, Any] | None,
    ocr_result: dict[str, Any] | None,
) -> tuple[str, float, str]:
    if not quality["ok"]:
        return "unsure", 0.0, quality["reason"] or "画面质量不合格，请重拍"

    if checkpoint.method in {"vlm", "angle_vlm"} and vlm_result is not None:
        verdict = vlm_result["verdict"]
        confidence = float(vlm_result.get("confidence", 0.0))
        reason = vlm_result.get("reason") or ""

        if verdict == "fail":
            return "fail", confidence, reason or "模型判断不符合闭店标准"

        # Geometry cross-check: if the handle clearly moved away from the
        # known-good reference, do not accept a semantic "pass".
        if (
            cv_result
            and cv_result.get("delta") is not None
            and cv_result.get("confidence", 0.0) >= config.CV_MIN_CONFIDENCE
        ):
            tolerance = (
                checkpoint.angle.tolerance
                if checkpoint.angle
                else config.ANCHOR_ANGLE_TOLERANCE
            )
            if cv_result["delta"] > tolerance:
                return (
                    "fail",
                    min(confidence, cv_result.get("confidence", 0.0)),
                    f"几何交叉检查未通过：{cv_result.get('reason', '')}",
                )

        if verdict == "pass" and confidence >= config.VLM_MIN_CONFIDENCE:
            return "pass", confidence, reason or "模型判断符合闭店标准"
        return "unsure", confidence, reason or "模型置信度不足，请重拍或人工确认"

    if checkpoint.method == "ocr" and ocr_result is not None:
        if ocr_result.get("conflict"):
            return "unsure", float(ocr_result.get("confidence", 0.0)), ocr_result["reason"]
        reading = ocr_result.get("reading")
        jev_result = ocr_result.get("jev") or {}
        prob = jev_result.get("prob_1")
        if reading and prob is not None and float(prob) < config.JEV_REVIEW_SCORE:
            return "unsure", float(prob), "Jev 一致性分数很低，读数与图像可能不一致，请人工确认"
        if reading and prob is not None and float(prob) < config.JEV_MIN_SCORE:
            return "unsure", float(prob), "Jev 一致性分数未达自动接受阈值，请人工确认读数"
        if reading and float(ocr_result.get("confidence", 0.0)) >= 0.7:
            confidence = max(float(ocr_result.get("confidence", 0.0)), float(prob or 0.0))
            reason = ocr_result["reason"]
            if prob is not None:
                reason = f"{reason}；Jev 一致性 {float(prob):.2f}"
            return "pass", confidence, reason
        return (
            "unsure",
            float(ocr_result.get("confidence", 0.0)),
            ocr_result.get("reason") or "读数置信度不足，请人工确认",
        )

    return "unsure", 0.0, "没有可用的核验结果"


async def process_capture(
    session_id: str,
    checkpoint: CheckpointConfig,
    image_bytes: bytes,
    *,
    source: str = "camera",
    roi: list[float] | None = None,
) -> EvidenceOut:
    session = db.get_session(session_id)
    if not session:
        raise ValueError("session not found")
    if session["status"] != "open":
        raise ValueError("session is not open")

    prepared = _prepare_image(image_bytes)
    image_hash = _sha256(prepared)
    captured_at = db.now_iso()
    evidence_id = db.new_id("ev")
    session_dir = config.RUNS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    image_path = session_dir / f"{checkpoint.id}_{int(time.time() * 1000)}.jpg"
    image_path.write_bytes(prepared)

    quality = cv.quality(prepared)
    cv_result: dict[str, Any] | None = None
    vlm_result: dict[str, Any] | None = None
    ocr_result: dict[str, Any] | None = None

    if quality["ok"]:
        if checkpoint.method in {"angle_vlm", "vlm"}:
            reference = _reference_bytes(checkpoint) if checkpoint.method == "angle_vlm" else None
            if checkpoint.method == "angle_vlm":
                cv_result = cv.valve_geometry(
                    prepared,
                    reference,
                    roi=roi,
                    tolerance=checkpoint.angle.tolerance if checkpoint.angle else None,
                )
            prompt = (
                checkpoint.vlm_prompt.strip()
                + "\n请只输出 JSON："
                + '{"verdict":"pass|fail|unsure","confidence":0到1,"reason":"一句话"}。'
                + "不确定时用 unsure，不要猜测。reason 必须用简体中文。"
            )
            vlm_result = await llama.vlm_verdict(
                llama.b64(prepared),
                prompt,
                reference_b64=llama.b64(reference) if reference else None,
            )
        elif checkpoint.method == "ocr":
            ocr_result = await ocr.verify_reading(
                llama.b64(prepared),
                expected_unit=checkpoint.ocr.unit if checkpoint.ocr else None,
                instruction=checkpoint.ocr_prompt,
            )
            # Jev checks the OCR candidate against the meter/label region.
            if ocr_result.get("reading"):
                candidate = " ".join(
                    str(part)
                    for part in (ocr_result.get("reading"), ocr_result.get("unit"))
                    if part
                )
                crop = (
                    _crop_bytes(prepared, checkpoint.ocr.roi)
                    if checkpoint.ocr and checkpoint.ocr.roi
                    else prepared
                )
                ocr_result["jev"] = await jev.score(crop, candidate)

    verdict, confidence, reason = _fuse(checkpoint, quality, cv_result, vlm_result, ocr_result)
    if cv_result and cv_result.get("flame", {}).get("suspected"):
        verdict = "fail"
        confidence = max(confidence, 0.85)
        reason = "火焰颜色交叉检查：画面中检测到明火/高饱和火焰色，燃气未关闭"

    # The hash chain is session-wide, not per-checkpoint: every new piece of
    # evidence extends the last evidence of the session.
    session_evidence = db.list_evidence(session_id)
    previous = session_evidence[-1] if session_evidence else None
    prev_hash = previous["chain_hash"] if previous else _sha256(session_id.encode("utf-8"))
    record: dict[str, Any] = {
        "id": evidence_id,
        "session_id": session_id,
        "checkpoint_id": checkpoint.id,
        "image_path": str(image_path),
        "image_sha256": image_hash,
        "captured_at": captured_at,
        "source": source,
        "quality": quality,
        "cv": cv_result,
        "vlm": vlm_result,
        "ocr": ocr_result,
        "verdict": verdict,
        "confidence": round(confidence, 3),
        "reason": reason,
        "human_action": None,
        "human_note": None,
        "prev_hash": prev_hash,
    }
    record["chain_hash"] = _chain_hash(prev_hash, _chain_payload(record))
    saved = db.add_evidence(record)
    db.add_event(
        session_id,
        "capture",
        {
            "checkpoint_id": checkpoint.id,
            "evidence_id": evidence_id,
            "verdict": verdict,
            "confidence": confidence,
        },
    )
    return EvidenceOut.model_validate(saved)


def session_state(session_id: str) -> SessionOut:
    session = db.get_session(session_id)
    if not session:
        raise ValueError("session not found")
    checklist = load_checklist(session["checklist_id"])
    states: list[CheckpointState] = []
    progress = {"pass": 0, "fail": 0, "unsure": 0, "pending": 0, "confirmed": 0}
    for checkpoint in checklist.checkpoints:
        latest = db.latest_evidence(session_id, checkpoint.id)
        if latest:
            evidence = EvidenceOut.model_validate(latest)
            status = evidence.verdict
            if evidence.human_action in {"confirm", "resolved"}:
                status = "confirmed"
            elif evidence.human_action == "reject":
                status = "fail"
        else:
            evidence = None
            status = "pending"
        progress[status] = progress.get(status, 0) + 1
        states.append(CheckpointState(config=checkpoint, evidence=evidence, status=status))

    return SessionOut(
        id=session["id"],
        store_name=session["store_name"],
        checklist_id=session["checklist_id"],
        checklist_name=checklist.name,
        operator=session["operator"],
        status=session["status"],
        created_at=session["created_at"],
        completed_at=session["completed_at"],
        chain_hash=session["chain_hash"],
        checkpoints=states,
        progress=progress,
    )


def confirm(session_id: str, checkpoint_id: str, action: str, note: str) -> EvidenceOut:
    latest = db.latest_evidence(session_id, checkpoint_id)
    if not latest:
        raise ValueError("no evidence for this checkpoint")
    db.set_human_action(latest["id"], action, note)
    db.add_event(
        session_id,
        "human_confirm",
        {"checkpoint_id": checkpoint_id, "action": action, "note": note},
    )
    updated = db.get_evidence(latest["id"])
    return EvidenceOut.model_validate(updated)


def complete(session_id: str) -> SessionOut:
    session = db.get_session(session_id)
    if not session:
        raise ValueError("session not found")
    checklist = load_checklist(session["checklist_id"])
    unresolved: list[str] = []
    for checkpoint in checklist.checkpoints:
        latest = db.latest_evidence(session_id, checkpoint.id)
        if not latest:
            unresolved.append(f"{checkpoint.name}：未检查")
            continue
        if latest["verdict"] in {"fail", "unsure"} and latest["human_action"] not in {
            "confirm",
            "resolved",
        }:
            unresolved.append(f"{checkpoint.name}：{latest['verdict']} 未人工确认")
        elif (
            checkpoint.critical
            and latest["verdict"] == "pass"
            and latest["human_action"] not in {"confirm", "resolved"}
        ):
            unresolved.append(f"{checkpoint.name}：关键项 AI 通过，但仍需人工确认")
    if unresolved:
        raise ValueError("存在未闭环项：" + "；".join(unresolved))

    evidence = db.list_evidence(session_id)
    chain_hash = evidence[-1]["chain_hash"] if evidence else _sha256(session_id.encode())
    db.set_session_status(
        session_id,
        "completed",
        completed_at=db.now_iso(),
        chain_hash=chain_hash,
    )
    pdf_path = report.write_report(session_id)
    db.set_session_status(session_id, "completed", report_path=str(pdf_path))
    db.add_event(session_id, "completed", {"chain_hash": chain_hash, "report": str(pdf_path)})
    return session_state(session_id)


def verify_chain(session_id: str) -> dict[str, Any]:
    session = db.get_session(session_id)
    if not session:
        raise ValueError("session not found")
    evidence = db.list_evidence(session_id)
    prev = _sha256(session_id.encode("utf-8"))
    ok = True
    for item in evidence:
        expected = _chain_hash(prev, _chain_payload(item))
        if expected != item["chain_hash"]:
            ok = False
            break
        prev = item["chain_hash"]
    return {
        "valid": ok,
        "count": len(evidence),
        "chain_hash": prev,
        "session_chain_hash": session.get("chain_hash"),
        "matches_session": bool(session.get("chain_hash") and prev == session["chain_hash"]),
    }
