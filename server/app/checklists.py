"""Checklist loading and validation."""

from __future__ import annotations

from pathlib import Path

import yaml

from . import config
from .schemas import ChecklistConfig


def list_checklists() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for path in sorted(config.CHECKLIST_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            out.append(
                {
                    "id": data["id"],
                    "name": data["name"],
                    "description": data.get("description", ""),
                    "checkpoints": len(data.get("checkpoints", [])),
                }
            )
        except Exception:
            continue
    return out


def load_checklist(checklist_id: str) -> ChecklistConfig:
    path: Path = config.CHECKLIST_DIR / f"{checklist_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"checklist not found: {checklist_id}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ChecklistConfig.model_validate(data)
