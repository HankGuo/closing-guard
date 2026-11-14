"""Pydantic schemas shared by the API and the agent."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

VerdictLabel = Literal["pass", "fail", "unsure"]


class AngleSpec(BaseModel):
    expected: float = 90.0
    tolerance: float = 12.0


class OcrSpec(BaseModel):
    fields: list[str] = Field(default_factory=lambda: ["reading", "unit"])
    unit: str | None = None
    roi: list[float] | None = None


class CheckpointConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    instruction: str
    method: Literal["vlm", "angle_vlm", "ocr"] = "vlm"
    reference: str | None = None
    vlm_prompt: str = ""
    ocr_prompt: str = ""
    angle: AngleSpec | None = None
    ocr: OcrSpec | None = None
    remediation: str = "请调整角度或补光后重拍。"
    critical: bool = True


class ChecklistConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    version: int = 1
    description: str = ""
    checkpoints: list[CheckpointConfig]


class SessionCreate(BaseModel):
    store_name: str = Field(min_length=1, max_length=80)
    checklist_id: str = "restaurant_closing"
    operator: str = Field(default="店员", max_length=40)


class ConfirmRequest(BaseModel):
    checkpoint_id: str
    action: Literal["confirm", "reject", "resolved"]
    note: str = ""


class Verdict(BaseModel):
    verdict: VerdictLabel = "unsure"
    confidence: float = 0.0
    reason: str = ""
    observations: list[str] = Field(default_factory=list)
    raw: str | None = None


class QualityResult(BaseModel):
    ok: bool
    blur: float
    brightness: float
    contrast: float
    reason: str = ""


class CvResult(BaseModel):
    ok: bool = True
    angle: float | None = None
    reference_angle: float | None = None
    delta: float | None = None
    confidence: float = 0.0
    reason: str = ""
    flame: dict[str, Any] | None = None


class OcrResult(BaseModel):
    reading: str | None = None
    unit: str | None = None
    raw_text: str = ""
    structured: dict[str, Any] = Field(default_factory=dict)
    conflict: bool = False
    confidence: float = 0.0
    reason: str = ""
    jev: dict[str, Any] | None = None


class EvidenceOut(BaseModel):
    id: str
    session_id: str
    checkpoint_id: str
    image_path: str
    image_sha256: str
    captured_at: str
    source: str
    verdict: VerdictLabel
    confidence: float
    reason: str
    quality: QualityResult | None = None
    cv: CvResult | None = None
    vlm: Verdict | None = None
    ocr: OcrResult | None = None
    human_action: str | None = None
    human_note: str | None = None
    chain_hash: str
    prev_hash: str


class CheckpointState(BaseModel):
    config: CheckpointConfig
    evidence: EvidenceOut | None = None
    status: Literal["pending", "pass", "fail", "unsure", "confirmed"] = "pending"


class SessionOut(BaseModel):
    id: str
    store_name: str
    checklist_id: str
    checklist_name: str
    operator: str
    status: str
    created_at: str
    completed_at: str | None = None
    chain_hash: str | None = None
    checkpoints: list[CheckpointState]
    progress: dict[str, int]
