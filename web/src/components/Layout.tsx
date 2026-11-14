import { useEffect, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { api } from "../api";
import type { Health } from "../types";

export default function Layout() {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => {
    let alive = true;
    const load = () => api.health().then((h) => alive && setHealth(h)).catch(() => alive && setHealth(null));
    load();
    const timer = window.setInterval(load, 15000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  const online = Boolean(health?.ok);
  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">
            <div className="brand-mark">打</div>
            <div>
              <div className="brand-name">打烊 · Closing Guard</div>
              <div className="brand-sub">MiniCPM on-device safety agent</div>
            </div>
          </Link>
          <nav className="nav">
            <NavLink to="/" end>首页</NavLink>
            <NavLink to="/about">关于</NavLink>
            <span className="health" title={online ? "本地模型在线" : "本地模型未连接"}>
              <span className={`health-dot ${online ? "ok" : "bad"}`} />
              {online ? "本地模型在线" : "模型未连接"}
            </span>
          </nav>
        </div>
      </header>
      <main className="container">
        <Outlet />
      </main>
      <footer className="footer">
        打烊 Closing Guard · 本地 MiniCPM · 不上传视频 · Apache-2.0
      </footer>
    </div>
  );
}
