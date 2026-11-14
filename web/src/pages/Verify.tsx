import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";

export default function VerifyPage() {
  const { id = "" } = useParams();
  const [result, setResult] = useState<{ valid: boolean; count: number; chain_hash: string; matches_session: boolean } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.verify(id).then(setResult).catch((e) => setError((e as Error).message));
  }, [id]);

  return (
    <div style={{ maxWidth: 760, margin: "40px auto" }}>
      <div className="card pad">
        <div className="eyebrow">CHAIN VERIFICATION</div>
        <h2 style={{ margin: "8px 0 14px" }}>证据链复核</h2>
        {error && <div style={{ color: "var(--red)" }}>{error}</div>}
        {!result && !error && <div className="muted">正在重算哈希链…</div>}
        {result && (
          <>
            <div className={`verdict-box ${result.valid ? "pass" : "fail"}`}>
              <div className="verdict-title" style={{ fontSize: 20 }}>
                {result.valid ? "✓ 证据链完整" : "✕ 证据链不匹配"}
              </div>
              <div className="verdict-reason">
                {result.valid
                  ? `共 ${result.count} 条证据，按顺序重算后与台账记录一致。`
                  : "重算结果与台账不一致，照片或记录可能被修改过。"}
              </div>
            </div>
            <div className="kv" style={{ marginTop: 16 }}>
              <span className="k">证据数量</span><span className="v">{result.count}</span>
              <span className="k">重算哈希</span><span className="v mono">{result.chain_hash}</span>
              <span className="k">会话记录</span><span className="v">{result.matches_session ? "一致" : "未完成/不一致"}</span>
            </div>
            <div className="row" style={{ marginTop: 18 }}>
              <Link className="btn" to={`/report/${id}`}>返回台账</Link>
              <Link className="btn btn-ghost" to="/">首页</Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
