"""FastAPI application and HTTP API for Closing Guard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import agent, config, db, jev, llama, ocr, report
from .checklists import list_checklists
from .schemas import ConfirmRequest, SessionCreate, SessionOut

app = FastAPI(
    title="Closing Guard",
    version=config.VERSION,
    description="Local-first closing-safety agent powered by MiniCPM.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()


@app.get("/api/health")
async def health() -> dict[str, Any]:
    vlm = await llama.health()
    ocr_health = await ocr.health()
    jev_health = await jev.health()
    return {
        "ok": vlm.get("ok", False) and ocr_health.get("ok", False) and jev_health.get("ok", False),
        "version": config.VERSION,
        "models": {
            "vlm": {"name": config.VLM_MODEL, **vlm},
            "ocr": {"name": config.OCR_MODEL, **ocr_health},
            "jev": {"name": config.JEV_MODEL, **jev_health},
        },
    }


@app.get("/api/checklists")
def checklists() -> list[dict[str, Any]]:
    return list_checklists()


@app.get("/api/sessions")
def sessions() -> list[dict[str, Any]]:
    rows = db.list_sessions()
    out = []
    for row in rows:
        item = dict(row)
        try:
            from .checklists import load_checklist

            item["checklist_name"] = load_checklist(row["checklist_id"]).name
        except Exception:
            item["checklist_name"] = row["checklist_id"]
        out.append(item)
    return out


@app.post("/api/sessions", response_model=SessionOut)
def create_session(payload: SessionCreate) -> SessionOut:
    try:
        session = db.create_session(payload.store_name, payload.checklist_id, payload.operator)
        return agent.session_state(session["id"])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str) -> SessionOut:
    try:
        return agent.session_state(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/capture")
async def capture(
    session_id: str,
    checkpoint_id: str = Form(...),
    source: str = Form("camera"),
    roi: str | None = Form(None),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    from .checklists import load_checklist

    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    checklist = load_checklist(session["checklist_id"])
    checkpoint = next((c for c in checklist.checkpoints if c.id == checkpoint_id), None)
    if checkpoint is None:
        raise HTTPException(status_code=404, detail="checkpoint not found")
    data = await file.read()
    if len(data) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="image too large (max 12MB)")
    parsed_roi = None
    if roi:
        try:
            parsed_roi = [float(x) for x in json.loads(roi)]
        except Exception:
            parsed_roi = None
    try:
        evidence = await agent.process_capture(
            session_id, checkpoint, data, source=source, roi=parsed_roi
        )
        return evidence.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/confirm")
def confirm(session_id: str, payload: ConfirmRequest) -> dict[str, Any]:
    try:
        evidence = agent.confirm(session_id, payload.checkpoint_id, payload.action, payload.note)
        return evidence.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/complete", response_model=SessionOut)
def complete(session_id: str) -> SessionOut:
    try:
        return agent.complete(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/evidence/{evidence_id}/image")
def evidence_image(evidence_id: str) -> FileResponse:
    ev = db.get_evidence(evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="evidence not found")
    path = Path(ev["image_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(path, media_type="image/jpeg")


@app.get("/api/sessions/{session_id}/report.pdf")
def report_pdf(session_id: str) -> FileResponse:
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    if not session.get("report_path"):
        try:
            path = report.write_report(session_id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    else:
        path = Path(session["report_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="report not found")
    return FileResponse(path, media_type="application/pdf", filename=f"{session_id}.pdf")


@app.get("/api/sessions/{session_id}/report.html", response_class=HTMLResponse)
def report_html(session_id: str) -> HTMLResponse:
    try:
        return HTMLResponse(report.report_html(session_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/verify/{session_id}")
def verify(session_id: str) -> dict[str, Any]:
    try:
        return agent.verify_chain(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/samples")
def samples() -> list[dict[str, str]]:
    root = config.DATA_DIR / "samples"
    if not root.exists():
        return []
    return [
        {"name": p.name, "url": f"/samples/{p.name}"}
        for p in sorted(root.glob("*"))
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]


# Static assets: sample images and the built web app.
_samples_dir = config.DATA_DIR / "samples"
if _samples_dir.exists():
    app.mount("/samples", StaticFiles(directory=str(_samples_dir)), name="samples")

_dist = config.WEB_DIST
if _dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="assets")


@app.get("/{full_path:path}", response_class=HTMLResponse)
def spa(full_path: str) -> Any:
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "not found"}, status_code=404)
    index = _dist / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<h1>Closing Guard API</h1><p>Web build not found. Run <code>cd web && npm run build</code>.</p>",
        status_code=200,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
