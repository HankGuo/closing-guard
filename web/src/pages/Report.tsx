import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import VerdictBadge from "../components/VerdictBadge";
import type { Session } from "../types";

export default function ReportPage() {
  const { id = "" } = useParams();
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getSession(id).then(setSession).catch((e) => setError((e as Error).message));
  }, [id]);

  if (error) return <div className="card pad" style={{ color: "var(--red)" }}>{error}</div>;
  if (!session) return <div className="card pad muted">加载中…</div>;

  const p = session.progress;
  return (
    <>
      <div className="session-head">
        <div>
          <div className="eyebrow">EVIDENCE LEDGER</div>
          <h2 style={{ marginTop: 6 }}>{session.store_name} · 闭店安全台账</h2>
          <div className="small muted">
            {session.checklist_name} · {session.operator} · {session.created_at.replace("T", " ").slice(0, 16)}
          </div>
        </div>
        <div className="row">
          <a className="btn btn-primary" href={`/api/sessions/${session.id}/report.pdf`} target="_blank" rel="noreferrer">下载 PDF</a>
          <Link className="btn btn-ghost" to={`/verify/${session.id}`}>复核证据链</Link>
        </div>
      </div>

      <div className="summary-grid" style={{ marginBottom: 18 }}>
        <div className="summary-cell"><b style={{ color: "var(--green)" }}>{p.pass ?? 0}</b><span>通过</span></div>
        <div className="summary-cell"><b style={{ color: "var(--red)" }}>{p.fail ?? 0}</b><span>未通过</span></div>
        <div className="summary-cell"><b style={{ color: "var(--amber)" }}>{p.unsure ?? 0}</b><span>待确认</span></div>
        <div className="summary-cell"><b>{p.confirmed ?? 0}</b><span>人工确认</span></div>
      </div>

      <div className="report-cards">
        {session.checkpoints.map((cp) => (
          <div className="card pad report-card" key={cp.config.id}>
            <div className="row between">
              <b>{cp.config.name}</b>
              <VerdictBadge status={cp.status} />
            </div>
            {cp.evidence && (
              <a href={`/api/evidence/${cp.evidence.id}/image`} target="_blank" rel="noreferrer">
                <img className="report-card-img" src={`/api/evidence/${cp.evidence.id}/image`} alt={cp.config.name} />
              </a>
            )}
            <div className="small" style={{ marginTop: 8 }}>{cp.evidence?.reason ?? "尚未检查"}</div>
            {cp.evidence?.human_action && (
              <div className="small" style={{ color: "var(--teal)", marginTop: 4 }}>
                人工动作：{cp.evidence.human_action}{cp.evidence.human_note ? ` · ${cp.evidence.human_note}` : ""}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="card pad report-table">
        <div className="row between" style={{ marginBottom: 10 }}>
          <h3>逐项证据</h3>
          <span className={`badge ${session.status === "completed" ? "pass" : "pending"}`}>
            {session.status === "completed" ? "已闭环" : "进行中"}
          </span>
        </div>
        <table className="table">
          <thead>
            <tr><th>检查点</th><th>照片</th><th>结论</th><th>说明</th><th>人工动作</th></tr>
          </thead>
          <tbody>
            {session.checkpoints.map((cp) => (
              <tr key={cp.config.id}>
                <td><b>{cp.config.name}</b><div className="small muted">{cp.config.method}</div></td>
                <td>
                  {cp.evidence ? (
                    <a href={`/api/evidence/${cp.evidence.id}/image`} target="_blank" rel="noreferrer">
                      <img className="thumb" src={`/api/evidence/${cp.evidence.id}/image`} alt={cp.config.name} />
                    </a>
                  ) : <span className="muted small">—</span>}
                </td>
                <td><VerdictBadge status={cp.status} /></td>
                <td className="small" style={{ maxWidth: 360 }}>
                  {cp.evidence?.reason ?? "尚未检查"}
                  {cp.evidence?.ocr?.jev?.prob_1 !== null && cp.evidence?.ocr?.jev?.prob_1 !== undefined && (
                    <div className="muted">Jev 一致性 {Number(cp.evidence.ocr.jev.prob_1).toFixed(2)}</div>
                  )}
                </td>
                <td className="small">{cp.evidence?.human_action ?? "—"}{cp.evidence?.human_note ? ` · ${cp.evidence.human_note}` : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card pad" style={{ marginTop: 16 }}>
        <div className="grid-2">
          <div>
            <h3>证据链</h3>
            <p className="small muted">
              每张照片的 SHA-256 与判定结论依次串成哈希链。校验接口会重算图片哈希与整条链；照片被替换、记录被删改都会报 valid=false。
            </p>
            <div className="kv">
              <span className="k">最终链哈希</span><span className="v mono">{session.chain_hash ?? "未完成"}</span>
              <span className="k">证据数量</span><span className="v">{session.checkpoints.filter((c) => c.evidence).length}</span>
              <span className="k">状态</span><span className="v">{session.status}</span>
            </div>
          </div>
          <div className="verdict-box pass">
            <div className="verdict-title">这份台账能证明什么？</div>
            <div className="verdict-reason">
              它证明“在某个时间、某台设备上，有人对这几个检查点拍了照，模型给出了结论，并且有人做了最终确认”。
              它不证明“绝对安全”，也不替代消防/燃气/市场监管的法定检查。
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
