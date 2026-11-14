import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import type { Health, Session } from "../types";

interface Checklist {
  id: string;
  name: string;
  description: string;
  checkpoints: number;
}

export default function Home() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<Health | null>(null);
  const [checklists, setChecklists] = useState<Checklist[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [store, setStore] = useState("");
  const [operator, setOperator] = useState("店员");
  const [checklist, setChecklist] = useState("restaurant_closing");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
    fetch("/api/checklists").then((r) => r.json()).then(setChecklists).catch(() => setChecklists([]));
    api.sessions().then(setSessions).catch(() => setSessions([]));
  }, []);

  async function start(e: FormEvent) {
    e.preventDefault();
    if (!store.trim()) {
      setError("请先填写门店名称");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const session = await api.createSession({
        store_name: store.trim(),
        checklist_id: checklist,
        operator: operator.trim() || "店员",
      });
      navigate(`/session/${session.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section className="hero">
        <div>
          <div className="eyebrow">MiniCPM × Agent · 闭店安全</div>
          <h1>让最后一盏灯，<br />关得明白。</h1>
          <p className="lead">
            757 万家餐饮商户，87.2% 的餐饮火灾发生在 300㎡ 以下的小店。
            打烊前的最后十分钟，不该只靠一张纸质表。
            用旧手机和本地 MiniCPM，把“三关一闭”做成一条可核验、可追溯的任务链。
          </p>
          <div className="hero-actions">
            <a className="btn btn-primary" href="#start">开始一次闭店检查</a>
            <button className="btn btn-ghost" onClick={() => navigate("/about")}>了解它怎么工作</button>
          </div>
          <div className="stats">
            <div className="stat"><b>0</b><span>新增硬件</span></div>
            <div className="stat"><b>100%</b><span>本地推理</span></div>
            <div className="stat"><b>4 项</b><span>可核验检查点</span></div>
          </div>
        </div>
        <div className="hero-visual" aria-hidden>
          <div className="orb" />
          <div className="phone one"><div className="cam" /><div className="tag">旧手机 · 采集</div></div>
          <div className="phone two"><div className="cam" /><div className="tag">本地模型 · 核验</div></div>
        </div>
      </section>

      <div className="section-title" id="start">
        <div>
          <h2>开始一次闭店检查</h2>
          <p>模型只在本机运行；照片保存在本项目的 runs/ 目录，不上传云端。</p>
        </div>
        <div className="health small">
          <span className={`health-dot ${health?.ok ? "ok" : "bad"}`} />
          {health?.ok ? "VLM + OCR 在线" : "模型未连接，请先运行 scripts/run_models.sh"}
        </div>
      </div>

      <div className="grid-2">
        <form className="card pad stack" onSubmit={start}>
          <div>
            <label className="label">门店名称</label>
            <input className="input" value={store} onChange={(e) => setStore(e.target.value)} placeholder="例如：老张牛肉面（XX 路店）" />
          </div>
          <div className="grid-2">
            <div>
              <label className="label">检查人</label>
              <input className="input" value={operator} onChange={(e) => setOperator(e.target.value)} />
            </div>
            <div>
              <label className="label">检查表</label>
              <select className="select" value={checklist} onChange={(e) => setChecklist(e.target.value)}>
                {checklists.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}（{c.checkpoints} 项）</option>
                ))}
              </select>
            </div>
          </div>
          {error && <div className="small" style={{ color: "var(--red)" }}>{error}</div>}
          <button className="btn btn-primary" disabled={busy}>{busy ? "创建中…" : "创建检查任务"}</button>
          <div className="small muted">
            提示：演示时可以在摄像头卡片里选择“使用样张”，也可以直接上传真实照片。样张路径会写入台账，便于复核。
          </div>
        </form>

        <div className="card pad">
          <div className="row between" style={{ marginBottom: 12 }}>
            <h3>最近的检查</h3>
            <span className="small muted">{sessions.length} 条</span>
          </div>
          {sessions.length === 0 && <div className="small muted">还没有记录。创建第一张闭店台账。</div>}
          <div className="stack">
            {sessions.slice(0, 6).map((s) => (
              <button
                key={s.id}
                className="check-item"
                onClick={() => navigate(s.status === "completed" ? `/report/${s.id}` : `/session/${s.id}`)}
                style={{ textAlign: "left", width: "100%" }}
              >
                <div className="check-index">{s.status === "completed" ? "✓" : "•"}</div>
                <div className="grow">
                  <div className="check-name">{s.store_name}</div>
                  <div className="check-sub">{s.checklist_name} · {s.created_at.replace("T", " ").slice(0, 16)}</div>
                </div>
                <span className={`badge ${s.status === "completed" ? "pass" : "pending"}`}>
                  {s.status === "completed" ? "已闭环" : "进行中"}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="section-title">
        <div>
          <h2>为什么不是“又一个摄像头”</h2>
          <p>不是被动监控，而是带着人完成一项有物理后果的任务。</p>
        </div>
      </div>
      <div className="grid-3">
        <div className="card feature">
          <div className="icon">⌁</div>
          <h3>AI 有权说“不”</h3>
          <p>照片里看不到阀门、角度不对、有明火，系统不会让你点“完成”。先整改，再重拍，再复核。</p>
        </div>
        <div className="card feature">
          <div className="icon">◎</div>
          <h3>混合核验，不迷信大模型</h3>
          <p>CV 看几何角度，MiniCPM-V 1B 看语义，MiniCPM-OCR 读表计；不确定就转人工，绝不猜。</p>
        </div>
        <div className="card feature">
          <div className="icon">⛓</div>
          <h3>一份能复核的台账</h3>
          <p>每张照片、每条结论、每次人工确认都写入哈希链；扫码即可复核，照片被换过就会露馅。</p>
        </div>
      </div>

      <div className="section-title">
        <div>
          <h2>本地模型状态</h2>
          <p>没有云 API，没有 token 账单；模型跑在这台 Mac 或店里的小主机上。</p>
        </div>
      </div>
      <div className="grid-2">
        {health ? Object.entries(health.models).map(([key, m]) => (
          <div className="card pad" key={key}>
            <div className="row between">
              <div>
                <div className="small muted">{key.toUpperCase()}</div>
                <div style={{ fontWeight: 800, marginTop: 4 }}>{m.name}</div>
              </div>
              <span className={`badge ${m.ok ? "pass" : "fail"}`}>{m.ok ? "在线" : "离线"}</span>
            </div>
          </div>
        )) : <div className="card pad muted">模型服务未连接。运行 <span className="mono">scripts/run_models.sh</span> 后刷新。</div>}
      </div>
    </>
  );
}
