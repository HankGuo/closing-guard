"""HTML/PDF evidence ledger generation."""

from __future__ import annotations

import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import qrcode
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image

from . import config, db
from .checklists import load_checklist

env = Environment(
    loader=FileSystemLoader(str(config.TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)
LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def fmt_ts(value: str | None) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return value


def _thumb_data_uri(path: str, max_edge: int = 640) -> str:
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
        out = BytesIO()
        im.save(out, format="JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def _qr_data_uri(text: str) -> str:
    img = qrcode.make(text, box_size=6, border=2)
    out = BytesIO()
    img.save(out, format="PNG")
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def build_context(session_id: str) -> dict[str, Any]:
    session = db.get_session(session_id)
    if not session:
        raise ValueError("session not found")
    checklist = load_checklist(session["checklist_id"])
    evidence = db.list_evidence(session_id)
    latest = {}
    for item in evidence:
        item["captured_at_fmt"] = fmt_ts(item.get("captured_at"))
        latest[item["checkpoint_id"]] = item

    items = []
    for checkpoint in checklist.checkpoints:
        ev = latest.get(checkpoint.id)
        items.append(
            {
                "config": checkpoint,
                "evidence": ev,
                "image": _thumb_data_uri(ev["image_path"]) if ev else None,
                "status": (ev["verdict"] if ev else "pending"),
                "human": (ev.get("human_action") if ev else None),
            }
        )
    counts = {"pass": 0, "fail": 0, "unsure": 0, "pending": 0}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    verify_url = f"{config.PUBLIC_BASE_URL}/verify/{session_id}"
    return {
        "session": session,
        "checklist": checklist,
        "items": items,
        "evidence": evidence,
        "counts": counts,
        "verify_url": verify_url,
        "qr": _qr_data_uri(verify_url),
        "generated_at": fmt_ts(db.now_iso()),
        "session_created_fmt": fmt_ts(session.get("created_at")),
        "session_completed_fmt": fmt_ts(session.get("completed_at")),
        "version": config.VERSION,
    }


def report_html(session_id: str) -> str:
    context = build_context(session_id)
    template = env.get_template("report.html")
    return template.render(**context)


def write_report(session_id: str) -> Path:
    session = db.get_session(session_id)
    if not session:
        raise ValueError("session not found")
    out_dir = config.RUNS_DIR / session_id
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "report.pdf"
    html = report_html(session_id)
    from weasyprint import HTML

    HTML(string=html, base_url=str(config.BASE_DIR)).write_pdf(str(pdf_path))
    return pdf_path
