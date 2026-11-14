import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import CameraCard from "../components/CameraCard";
import VerdictBadge from "../components/VerdictBadge";
import type { CheckpointState, Session } from "../types";

function fmt(ts: string | null | undefined) {
  if (!ts) return "—";
  return ts.replace("T", " ").slice(0, 19);
}

export default function SessionPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<{ text: string; error?: boolean } | null>(null);
  const [note, setNote] = useState("");
  const [loadError, setLoadError] = useState("");

  async function load() {
    try {
      const data = await api.getSession(id);
      setSession(data);
      setSelected((prev) => {
        if (prev && data.checkpoints.some((c) => c.config.id === prev)) return prev;
        const next = data.checkpoints.find((c) => c.status !== "pass" && c.status !== "confirmed");
        return next?.config.id ?? data.checkpoints[0]?.config.id ?? "";
      });
    } catch (err) {
      setLoadError((err as Error).message);
    }
  }

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 8000);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const current: CheckpointState | undefined = useMemo(
    () => session?.checkpoints.find((c) => c.config.id === selected) ?? session?.checkpoints[0],
    [session, selected],
  );

  const done = (session?.progress.pass ?? 0) + (session?.progress.confirmed ?? 0);
  const total = session?.checkpoints.length ?? 0;
  const pct = total ? Math.round((done / total) * 100) : 0;
  const needsConfirm = session
    ? session.checkpoints.filter(
        (c) => c.config.critical && c.evidence?.verdict === "pass" && !c.evidence.human_action,
      ).length
    : 0;

  async function capture(blob: Blob, source: string) {
    if (!session || !current) return;
    setBusy(true);
    setToast(null);
    try {
      const res = await api.capture(session.id, current.config.id, blob, source);
      const label = res.verdict === "pass" ? "通过" : res.verdict === "fail" ? "未通过" : "待确认";
      setToast({ text: `${current.config.name}：${label}。${res.reason}`, error: res.verdict !== "pass" });
      await load();
      setNote("");
    } catch (err) {
      setToast({ text: (err as Error).message, error: true });
    } finally {
      setBusy(false);
    }
  }

  async function confirm(action: "confirm" | "reject" | "resolved") {
    if (!session || !current) return;
    setBusy(true);
    try {
      await api.confirm(session.id, current.config.id, action, note);
      setToast({ text: action === "reject" ? "已驳回，请重拍或整改。" : "已记录人工动作。" });
      await load();
      setNote("");
    } catch (err) {
      setToast({ text: (err as Error).message, error: true });
    } finally {
      setBusy(false);
    }
  }

  async function complete() {
    if (!session) return;
    setBusy(true);
    try {
      await api.complete(session.id);
      navigate(`/report/${session.id}`);
    } catch (err) {
      setToast({ text: (err as Error).message, error: true });
    } finally {
      setBusy(false);
    }
  }

  if (loadError) return <div className="card pad" style={{ color: "var(--red)" }}>{loadError}</div>;
  if (!session) return <div className="card pad muted">加载中…</div>;

  return (
    <>
      <div className="session-head">
        <div>
          <div className="eyebrow">CLOSING CHECK · {session.status === "completed" ? "已闭环" : "进行中"}</div>
          <h2 style={{ marginTop: 6 }}>{session.store_name}</h2>
          <div className="small muted">
            {session.checklist_name} · 检查人 {session.operator} · 创建于 {fmt(session.created_at)}
          </div>
        </div>
        <div className="row">
          {session.status === "completed" ? (
            <button className="btn btn-primary" onClick={() => navigate(`/report/${session.id}`)}>查看台账</button>
          ) : (
            <button className="btn btn-primary" onClick={complete} disabled={busy || done < total || needsConfirm > 0}>
              {needsConfirm > 0 ? `还有 ${needsConfirm} 项待人工确认` : "完成并生成台账"}
            </button>
          )}
        </div>
      </div>

      <div className="row between small muted" style={{ marginBottom: 8 }}>
        <span>进度 {done}/{total}{needsConfirm > 0 ? ` · ${needsConfirm} 项关键结果待人工确认` : ""}</span>
        <span>{pct}%</span>
      </div>
      <div className="progress" style={{ marginBottom: 14 }}><div style={{ width: `${pct}%` }} /></div>

      {current && (
        <div className={`result-strip ${current.status}`}>
          <div className="row between">
            <div className="row" style={{ gap: 8 }}>
              <b>{current.config.name}</b>
              <VerdictBadge status={current.status} />
            </div>
            <span className="small muted">{current.evidence ? `置信度 ${current.evidence.confidence.toFixed(2)}` : "尚未检查"}</span>
          </div>
          <div className="small" style={{ marginTop: 4, opacity: 0.85 }}>
            {current.evidence?.reason ?? current.config.instruction}
          </div>
        </div>
      )}

      <div className="session-grid">
        <div className="stack">
          {session.status === "open" && current ? (
            <CameraCard
              checkpoint={current.config}
              busy={busy}
              onCapture={(blob, source) => { void capture(blob, source); }}
            />
          ) : (
            <div className="card pad">
              <h3>检查已闭环</h3>
              <p className="muted small">台账已经生成。你仍然可以查看每一张证据照片和哈希链。</p>
              <button className="btn btn-primary" onClick={() => navigate(`/report/${session.id}`)}>打开台账</button>
            </div>
          )}

          {current?.evidence && (
            <div className={`verdict-box ${current.status === "confirmed" ? "pass" : current.status}`}>
              <div className="row between">
                <div className="verdict-title">
                  {current.config.name} · <VerdictBadge status={current.status} />
                </div>
                <span className="small muted">置信度 {current.evidence.confidence.toFixed(2)}</span>
              </div>
              <div className="verdict-reason">{current.evidence.reason}</div>
              <img className="evidence-preview" src={`/api/evidence/${current.evidence.id}/image`} alt={current.config.name} />
              <div className="kv">
                <span className="k">时间</span><span className="v">{fmt(current.evidence.captured_at)}</span>
                <span className="k">来源</span><span className="v">{current.evidence.source}</span>
                {current.evidence.quality && (
                  <>
                    <span className="k">画质</span>
                    <span className="v">模糊 {current.evidence.quality.blur} · 亮度 {current.evidence.quality.brightness}</span>
                  </>
                )}
                {current.evidence.cv?.delta !== null && current.evidence.cv?.delta !== undefined && (
                  <>
                    <span className="k">几何差</span>
                    <span className="v">{current.evidence.cv.delta}°（{current.evidence.cv.reason}）</span>
                  </>
                )}
                {current.evidence.ocr && (
                  <>
                    <span className="k">OCR</span>
                    <span className="v">{current.evidence.ocr.reading ?? "未识别"} {current.evidence.ocr.unit ?? ""}</span>
                  </>
                )}
                {current.evidence.ocr?.jev?.prob_1 !== null && current.evidence.ocr?.jev?.prob_1 !== undefined && (
                  <>
                    <span className="k">Jev</span>
                    <span className="v">一致性 {Number(current.evidence.ocr.jev.prob_1).toFixed(2)}</span>
                  </>
                )}
              </div>
              <div className="row wrap" style={{ marginTop: 12 }}>
                {(current.status === "fail" || current.status === "unsure") && (
                  <>
                    <input
                      className="input"
                      style={{ maxWidth: 260 }}
                      placeholder="人工备注（例如：已关阀并复查）"
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                    />
                    <button className="btn btn-sm" onClick={() => confirm("resolved")} disabled={busy}>整改完成</button>
                    <button className="btn btn-sm btn-ghost" onClick={() => confirm("confirm")} disabled={busy}>人工确认通过</button>
                    <button className="btn btn-sm btn-danger" onClick={() => confirm("reject")} disabled={busy}>驳回</button>
                  </>
                )}
                {current.status === "pass" && current.config.critical && !current.evidence.human_action && (
                  <>
                    <span className="small" style={{ color: "#fcd34d" }}>
                      AI 建议通过，但这是关键项，必须人工确认后才能闭环。
                    </span>
                    <input
                      className="input"
                      style={{ maxWidth: 260 }}
                      placeholder="确认备注（可选）"
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                    />
                    <button className="btn btn-sm btn-primary" onClick={() => confirm("confirm")} disabled={busy}>人工确认通过</button>
                    <button className="btn btn-sm btn-danger" onClick={() => confirm("reject")} disabled={busy}>驳回/重拍</button>
                  </>
                )}
                {current.status === "pass" && (!current.config.critical || current.evidence.human_action) && (
                  <span className="small muted">本项已通过。如需复核，可以重新拍照覆盖。</span>
                )}
                {current.status === "confirmed" && (
                  <span className="small muted">已人工确认。{current.evidence.human_note}</span>
                )}
              </div>
              {current.status === "fail" && <div className="small" style={{ color: "#fca5a5", marginTop: 8 }}>{current.config.remediation}</div>}
            </div>
          )}
        </div>

        <div className="card pad">
          <div className="row between" style={{ marginBottom: 12 }}>
            <h3>检查清单</h3>
            <span className="small muted">{session.checklist_name}</span>
          </div>
          <div className="checklist">
            {session.checkpoints.map((cp, i) => (
              <div
                key={cp.config.id}
                className={`check-item ${cp.config.id === current?.config.id ? "active" : ""}`}
                onClick={() => setSelected(cp.config.id)}
              >
                <div className="check-index">{i + 1}</div>
                <div className="grow">
                  <div className="check-name">{cp.config.name}</div>
                  <div className="check-sub">{cp.evidence ? fmt(cp.evidence.captured_at) : "尚未检查"}</div>
                </div>
                <VerdictBadge status={cp.status} />
              </div>
            ))}
          </div>
          <div className="small muted" style={{ marginTop: 14, lineHeight: 1.7 }}>
            提示：每一项都可以重新拍照。系统会保留每次证据，最终台账使用最近一次结论。
            所有“未通过/待确认”项必须人工确认或整改后才能闭环。
          </div>
          {session.chain_hash && (
            <div className="small" style={{ marginTop: 10 }}>
              链哈希：<span className="mono">{session.chain_hash.slice(0, 24)}…</span>
            </div>
          )}
        </div>
      </div>

      {toast && (
        <div className={`toast ${toast.error ? "error" : ""}`} onClick={() => setToast(null)}>
          {toast.text}
        </div>
      )}
    </>
  );
}
