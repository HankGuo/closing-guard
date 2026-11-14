import { useCallback, useEffect, useRef, useState } from "react";
import type { CheckpointConfig } from "../types";

interface Props {
  checkpoint: CheckpointConfig;
  busy: boolean;
  onCapture: (blob: Blob, source: string) => void;
}

interface Sample {
  name: string;
  url: string;
}

const SAMPLE_PREFIX: Record<string, RegExp> = {
  gas_valve: /^gas_(valve|stove)/,
  power_panel: /^power_panel/,
  door_lock: /^door_/,
  gas_meter: /^(gas_meter|water_meter)/,
};

export default function CameraCard({ checkpoint, busy, onCapture }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState("");
  const [torch, setTorch] = useState(false);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [ready, setReady] = useState(false);

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setReady(false);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function start() {
      setError("");
      if (!navigator.mediaDevices?.getUserMedia) {
        setError("当前浏览器不支持摄像头，请上传照片。");
        return;
      }
      if (!window.isSecureContext) {
        setError("当前页面不是安全上下文（HTTPS/localhost），摄像头被浏览器禁用；请改用 localhost 或上传照片。");
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" }, width: { ideal: 1600 }, height: { ideal: 1200 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => undefined);
        }
        setReady(true);
      } catch (err) {
        setError(`摄像头不可用：${(err as Error).message}。可以直接上传照片。`);
      }
    }
    start();
    return () => {
      cancelled = true;
      stop();
    };
  }, [stop]);

  useEffect(() => {
    fetch("/api/samples")
      .then((r) => (r.ok ? r.json() : []))
      .then(setSamples)
      .catch(() => setSamples([]));
  }, []);

  const pattern = SAMPLE_PREFIX[checkpoint.id];
  const usableSamples = pattern ? samples.filter((s) => pattern.test(s.name)) : samples;

  const capture = () => {
    const video = videoRef.current;
    if (!video || !ready) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 960;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => blob && onCapture(blob, "camera"), "image/jpeg", 0.9);
  };

  const toggleTorch = async () => {
    const track = streamRef.current?.getVideoTracks?.()[0];
    if (!track) return;
    try {
      await track.applyConstraints({ advanced: [{ torch: !torch } as MediaTrackConstraintSet] });
      setTorch(!torch);
    } catch {
      setError("这台设备不支持手电控制，请用外部照明。");
    }
  };

  const onFile = (file: File | undefined) => {
    if (file) onCapture(file, "upload");
  };

  const onSample = async (url: string) => {
    const res = await fetch(url);
    const blob = await res.blob();
    onCapture(blob, "sample");
  };

  return (
    <div className="card camera-card">
      <div className="camera-stage">
        <video ref={videoRef} playsInline muted autoPlay />
        {!ready && (
          <div className="placeholder">
            <div>
              <div style={{ fontSize: 34, marginBottom: 8 }}>◉</div>
              <div>正在打开摄像头…</div>
              <div className="small" style={{ marginTop: 6 }}>{error || "首次使用请允许摄像头权限"}</div>
            </div>
          </div>
        )}
        {ready && (
          <div className="guide">
            <span className="corner tl" />
            <span className="corner tr" />
            <span className="corner bl" />
            <span className="corner br" />
            <span className="lbl">{checkpoint.name} · 对准取景框</span>
          </div>
        )}
      </div>
      <div className="camera-bar">
        <button className="btn btn-primary" onClick={capture} disabled={!ready || busy}>
          {busy ? "核验中…" : "拍照核验"}
        </button>
        <button className="btn btn-ghost btn-sm" onClick={toggleTorch} disabled={!ready}>
          {torch ? "关闭手电" : "打开手电"}
        </button>
        <label className="btn btn-ghost btn-sm" style={{ margin: 0 }}>
          上传照片
          <input
            type="file"
            accept="image/*"
            capture="environment"
            style={{ display: "none" }}
            onChange={(e) => onFile(e.target.files?.[0])}
          />
        </label>
        {usableSamples.length > 0 && (
          <select
            className="select btn-sm"
            style={{ width: 150 }}
            defaultValue=""
            onChange={(e) => e.target.value && onSample(e.target.value)}
            aria-label="使用样张"
          >
            <option value="">使用样张…</option>
            {usableSamples.map((s) => (
              <option key={s.name} value={s.url}>{s.name}</option>
            ))}
          </select>
        )}
        <div className="spacer" />
        <span className="small muted">{checkpoint.method === "ocr" ? "OCR 读数" : checkpoint.method === "angle_vlm" ? "几何 + 视觉" : "视觉核验"}</span>
      </div>
      <div className="pad" style={{ paddingTop: 0 }}>
        <div className="small muted">{checkpoint.instruction}</div>
      </div>
    </div>
  );
}
