import type { Health, Session } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/api/health"),
  sessions: () => request<Session[]>("/api/sessions"),
  getSession: (id: string) => request<Session>(`/api/sessions/${id}`),
  createSession: (payload: { store_name: string; checklist_id: string; operator: string }) =>
    request<Session>("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  capture: (id: string, checkpointId: string, file: Blob, source: string, roi?: number[]) => {
    const form = new FormData();
    form.append("checkpoint_id", checkpointId);
    form.append("source", source);
    if (roi) form.append("roi", JSON.stringify(roi));
    form.append("file", file, "capture.jpg");
    return request<{ id: string; verdict: string; reason: string; confidence: number }>(
      `/api/sessions/${id}/capture`,
      { method: "POST", body: form },
    );
  },
  confirm: (id: string, checkpointId: string, action: "confirm" | "reject" | "resolved", note: string) =>
    request(`/api/sessions/${id}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ checkpoint_id: checkpointId, action, note }),
    }),
  complete: (id: string) =>
    request<Session>(`/api/sessions/${id}/complete`, { method: "POST" }),
  verify: (id: string) =>
    request<{ valid: boolean; count: number; chain_hash: string; matches_session: boolean }>(
      `/api/verify/${id}`,
    ),
  samples: () => request<{ name: string; url: string }[]>("/api/samples"),
};
