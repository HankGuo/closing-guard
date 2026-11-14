"""SQLite persistence for sessions and evidence.

The database is deliberately simple and local: one file under `runs/`.  It is
the audit log of the closing procedure, not a multi-tenant service.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config

DB_PATH = Path(os.getenv("CG_DB_PATH", str(config.RUNS_DIR / "closing_guard.db")))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                store_name TEXT NOT NULL,
                checklist_id TEXT NOT NULL,
                operator TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                chain_hash TEXT,
                report_path TEXT
            );

            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                checkpoint_id TEXT NOT NULL,
                image_path TEXT NOT NULL,
                image_sha256 TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                source TEXT NOT NULL,
                quality_json TEXT,
                cv_json TEXT,
                vlm_json TEXT,
                ocr_json TEXT,
                verdict TEXT NOT NULL,
                confidence REAL NOT NULL,
                reason TEXT NOT NULL,
                human_action TEXT,
                human_note TEXT,
                chain_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_evidence_session
                ON evidence(session_id, captured_at);

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                ts TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload_json TEXT
            );
            """
        )


def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def create_session(store_name: str, checklist_id: str, operator: str) -> dict[str, Any]:
    session_id = new_id("ses")
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (id, store_name, checklist_id, operator, status, created_at)"
            " VALUES (?, ?, ?, ?, 'open', ?)",
            (session_id, store_name, checklist_id, operator, ts),
        )
        conn.execute(
            "INSERT INTO events (session_id, ts, kind, payload_json) VALUES (?, ?, ?, ?)",
            (session_id, ts, "session_created", json.dumps({"store_name": store_name})),
        )
    return get_session(session_id)  # type: ignore[return-value]


def get_session(session_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return _row(row)


def list_sessions(limit: int = 20) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def set_session_status(session_id: str, status: str, **fields: Any) -> None:
    allowed = {"completed_at", "chain_hash", "report_path"}
    sets = ["status = ?"]
    values: list[Any] = [status]
    for key, value in fields.items():
        if key in allowed:
            sets.append(f"{key} = ?")
            values.append(value)
    values.append(session_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE sessions SET {', '.join(sets)} WHERE id = ?", values)


def add_event(session_id: str, kind: str, payload: dict[str, Any] | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO events (session_id, ts, kind, payload_json) VALUES (?, ?, ?, ?)",
            (session_id, now_iso(), kind, json.dumps(payload or {}, ensure_ascii=False)),
        )


def add_evidence(record: dict[str, Any]) -> dict[str, Any]:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO evidence (
                id, session_id, checkpoint_id, image_path, image_sha256,
                captured_at, source, quality_json, cv_json, vlm_json, ocr_json,
                verdict, confidence, reason, human_action, human_note,
                chain_hash, prev_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["session_id"],
                record["checkpoint_id"],
                record["image_path"],
                record["image_sha256"],
                record["captured_at"],
                record["source"],
                json.dumps(record.get("quality"), ensure_ascii=False) if record.get("quality") else None,
                json.dumps(record.get("cv"), ensure_ascii=False) if record.get("cv") else None,
                json.dumps(record.get("vlm"), ensure_ascii=False) if record.get("vlm") else None,
                json.dumps(record.get("ocr"), ensure_ascii=False) if record.get("ocr") else None,
                record["verdict"],
                record["confidence"],
                record["reason"],
                record.get("human_action"),
                record.get("human_note"),
                record["chain_hash"],
                record["prev_hash"],
            ),
        )
    return get_evidence(record["id"])  # type: ignore[return-value]


def get_evidence(evidence_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
    return _evidence_row(row)


def list_evidence(session_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM evidence WHERE session_id = ? ORDER BY captured_at ASC, rowid ASC",
            (session_id,),
        ).fetchall()
    return [_evidence_row(r) for r in rows if r]  # type: ignore[misc]


def latest_evidence(session_id: str, checkpoint_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM evidence WHERE session_id = ? AND checkpoint_id = ?"
            " ORDER BY captured_at DESC, rowid DESC LIMIT 1",
            (session_id, checkpoint_id),
        ).fetchone()
    return _evidence_row(row)


def set_human_action(evidence_id: str, action: str, note: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE evidence SET human_action = ?, human_note = ? WHERE id = ?",
            (action, note, evidence_id),
        )


def update_evidence_chain(evidence_id: str, chain_hash: str, prev_hash: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE evidence SET chain_hash = ?, prev_hash = ? WHERE id = ?",
            (chain_hash, prev_hash, evidence_id),
        )


def _evidence_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if not row:
        return None
    data = dict(row)
    for key in ("quality_json", "cv_json", "vlm_json", "ocr_json"):
        raw = data.pop(key, None)
        out_key = key.replace("_json", "")
        data[out_key] = json.loads(raw) if raw else None
    return data
