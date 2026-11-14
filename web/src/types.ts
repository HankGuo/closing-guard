export type VerdictLabel = "pass" | "fail" | "unsure" | "pending" | "confirmed";

export interface CheckpointConfig {
  id: string;
  name: string;
  instruction: string;
  method: "vlm" | "angle_vlm" | "ocr";
  remediation: string;
  critical: boolean;
}

export interface Evidence {
  id: string;
  checkpoint_id: string;
  image_path: string;
  captured_at: string;
  source: string;
  verdict: "pass" | "fail" | "unsure";
  confidence: number;
  reason: string;
  human_action: string | null;
  human_note: string | null;
  quality?: { ok: boolean; blur: number; brightness: number; contrast: number; reason: string };
  cv?: { ok: boolean; angle: number | null; delta: number | null; reason: string } | null;
  vlm?: { verdict: string; confidence: number; reason: string } | null;
  ocr?: {
    reading: string | null;
    unit: string | null;
    conflict: boolean;
    reason: string;
    jev?: { prob_1?: number | null; error?: string | null } | null;
  } | null;
}

export interface CheckpointState {
  config: CheckpointConfig;
  evidence: Evidence | null;
  status: VerdictLabel;
}

export interface Session {
  id: string;
  store_name: string;
  checklist_id: string;
  checklist_name: string;
  operator: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  chain_hash: string | null;
  checkpoints: CheckpointState[];
  progress: Record<string, number>;
}

export interface Health {
  ok: boolean;
  version: string;
  models: Record<string, { name: string; ok: boolean }>;
}
