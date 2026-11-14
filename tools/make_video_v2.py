#!/usr/bin/env python3
"""Closing Guard — demo video v2 (real UI footage + captions + single narrator).

Why v2: the v1 video relied on slides; v2 uses recorded product footage.
v2 uses the recorded product flow (tools/record_flow.cjs) as primary footage,
adds short captions, and one calm male narration. No slide decks.

Usage:
  python tools/make_video_v2.py
Output:
  dist/demo_v2.mp4 (1280x720, ~60s)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / "runs" / "video" / "flow_real.mp4"
OUTDIR = ROOT / "runs" / "video" / "v2"
DIST = ROOT / "dist"
TTS_DIR = OUTDIR / "tts"
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
W, H = 1280, 720

OUTDIR.mkdir(parents=True, exist_ok=True)
TTS_DIR.mkdir(parents=True, exist_ok=True)
DIST.mkdir(exist_ok=True)

INK = (16, 18, 20)
PAPER = (250, 249, 246)
ACCENT = (46, 160, 132)


def font(size: int):
    return ImageFont.truetype(FONT, size)


def text_size(draw, text, f):
    box = draw.textbbox((0, 0), text, font=f)
    return box[2] - box[0], box[3] - box[1]


def card(path: Path, lines, bg=INK, fg=PAPER, accent=None, footer=None):
    """Full-frame title/end/eval card."""
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    y = H // 2 - len(lines) * 70
    for text, size, color, weight in lines:
        f = font(size)
        tw, th = text_size(d, text, f)
        d.text(((W - tw) // 2, y), text, font=f, fill=color)
        y += th + (56 if size >= 60 else 30)
    if accent:
        d.rectangle([(W // 2 - 40, H // 2 + 150), (W // 2 + 40, H // 2 + 154)], fill=accent)
    if footer:
        f = font(20)
        tw, th = text_size(d, footer, f)
        d.text(((W - tw) // 2, H - 70), footer, font=f, fill=(150, 150, 150))
    img.save(path)


def caption_png(path: Path, text: str):
    """Bottom caption bar with semi-transparent backdrop."""
    bar_h = 96
    img = Image.new("RGBA", (W, bar_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(30)
    tw, th = text_size(d, text, f)
    pad = 28
    bw, bh = tw + pad * 2, th + pad
    x0 = (W - bw) // 2
    y0 = (bar_h - bh) // 2
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=10, fill=(10, 12, 14, 190))
    d.text((x0 + pad, y0 + pad // 2 - 2), text, font=f, fill=(240, 240, 240, 255))
    img.save(path)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def tts(name: str, text: str) -> Path:
    mp3 = TTS_DIR / f"{name}.mp3"
    if not mp3.exists():
        run([
            str(ROOT / ".venv" / "bin" / "edge-tts"),
            "--voice", "zh-CN-YunyangNeural",
            "--rate=-8%",
            "--text", text,
            "--write-media", str(mp3),
        ])
    return mp3


def trim_with_caption(src: Path, start: float, dur: float, caption: str | None, out: Path):
    cap = None
    if caption:
        cap = out.with_suffix(".cap.png")
        caption_png(cap, caption)
    vf = []
    inputs = ["-ss", str(start), "-t", str(dur), "-i", str(src)]
    if cap:
        inputs += ["-i", str(cap)]
        vf = ["-filter_complex",
              f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1[v];"
              f"[v][1:v]overlay=0:{H-96}:format=auto[vout]",
              "-map", "[vout]"]
    run(["ffmpeg", "-y", *inputs, *vf,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", "25", "-an", str(out)])


def main():
    if not FLOW.exists():
        sys.exit("缺少 runs/video/flow_real.mp4，先运行 node tools/record_flow.cjs")

    # 卡片
    card(OUTDIR / "s1_title.png", [
        ("打烊  Closing Guard", 64, PAPER, "bold"),
        ("一个会拒绝签字的闭店安全 Agent", 30, (170, 180, 178), "regular"),
    ], accent=ACCENT)

    card(OUTDIR / "s4_numbers.png", [
        ("8 张对抗样本 · 判定准确率", 26, (110, 116, 114), "regular"),
        ("87.5%", 132, INK, "bold"),
        ("false pass = 0    平均 3.0 秒", 30, (70, 76, 74), "regular"),
    ], bg=PAPER, fg=INK, footer="M1 16GB · 本地 llama.cpp · 无云 API")

    card(OUTDIR / "s6_end.png", [
        ("样张与模拟器演示", 30, (170, 180, 178), "regular"),
        ("尚未进入真实门店", 22, (140, 148, 146), "regular"),
        ("github.com/HankGuo/closing-guard", 26, PAPER, "regular"),
    ], accent=ACCENT)

    # 旁白
    lines = {
        "l1": "街边小店的闭店检查，常常只留下一张没人核验的照片。",
        "l2": "打烊，是一个会拒绝签字的闭店安全 Agent。",
        "l3": "模型逐项判断，关键项必须人工确认，不合格就重拍。",
        "l4": "最后生成带哈希链和二维码的台账，扫码就能复核。",
        "l5": "当前为样张与模拟器演示，尚未进入真实门店。",
    }
    for k, v in lines.items():
        tts(k, v)

    # 片段
    segs = []

    def still(png: Path, dur: float, out: Path, caption: str | None = None):
        cap = None
        if caption:
            cap = out.with_suffix(".cap.png")
            caption_png(cap, caption)
        if cap:
            run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", str(png), "-i", str(cap),
                 "-filter_complex", f"[1:v]scale={W}:-1[c];[0:v][c]overlay=0:{H-96}:format=auto[v]",
                 "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                 "-pix_fmt", "yuv420p", "-r", "25", "-an", str(out)])
        else:
            run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", str(png),
                 "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                 "-pix_fmt", "yuv420p", "-r", "25", "-an", str(out)])

    still(OUTDIR / "s1_title.png", 3.0, OUTDIR / "a1.mp4")
    segs.append(OUTDIR / "a1.mp4")

    trim_with_caption(FLOW, 8.0, 22.0, "以前闭店：拍张照，发群里", OUTDIR / "a2.mp4")
    segs.append(OUTDIR / "a2.mp4")

    trim_with_caption(FLOW, 55.0, 16.0, "AI 判不合格：必须重拍或整改，不能点完成", OUTDIR / "a3.mp4")
    segs.append(OUTDIR / "a3.mp4")

    trim_with_caption(FLOW, 170.0, 14.0, "每项留证据，最后出一份带哈希链的台账", OUTDIR / "a3b.mp4")
    segs.append(OUTDIR / "a3b.mp4")

    still(OUTDIR / "s4_numbers.png", 5.0, OUTDIR / "a4.mp4")
    segs.append(OUTDIR / "a4.mp4")

    # Web 端真实截图（真实样张上传，非模拟器虚拟相机）
    for name, out in [("web_04_gas_confirm.png", "a5.mp4"), ("web_08_report.png", "a6.mp4")]:
        src = ROOT / "docs" / "screenshots" / name
        run(["ffmpeg", "-y", "-loop", "1", "-t", "3.2", "-i", str(src),
             "-vf", f"scale=-2:{H-40},pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x101214",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", "-r", "25", "-an", str(OUTDIR / out)])
        segs.append(OUTDIR / out)

    still(OUTDIR / "s6_end.png", 5.0, OUTDIR / "a7.mp4")
    segs.append(OUTDIR / "a7.mp4")

    # 拼接视频
    concat_list = OUTDIR / "concat.txt"
    concat_list.write_text("".join(f"file '{s}'\n" for s in segs))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c", "copy", str(OUTDIR / "video_silent.mp4")])

    total = sum(
        float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=nw=1:nk=1", str(s)],
                             capture_output=True, text=True).stdout.strip())
        for s in segs
    )

    # 音轨：静音底 + 旁白按时间点插入
    offsets = {"l1": 4.0, "l2": 8.0, "l3": 30.0, "l4": 48.0, "l5": 58.0}
    inputs = ["-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=44100:cl=stereo"]
    filters = []
    for i, (key, off) in enumerate(offsets.items(), start=1):
        inputs += ["-i", str(TTS_DIR / f"{key}.mp3")]
        filters.append(f"[{i}:a]adelay={int(off*1000)}|{int(off*1000)},volume=1.0[a{i}]")
    mix_inputs = "[0:a]" + "".join(f"[a{i}]" for i in range(1, len(offsets) + 1))
    filters.append(f"{mix_inputs}amix=inputs={len(offsets)+1}:duration=first:dropout_transition=0[aout]")

    run(["ffmpeg", "-y", *inputs,
         "-i", str(OUTDIR / "video_silent.mp4"),
         "-filter_complex", ";".join(filters),
         "-map", f"{len(offsets)+1}:v", "-map", "[aout]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
         str(DIST / "demo_v2.mp4")])

    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(DIST / "demo_v2.mp4")],
                         capture_output=True, text=True).stdout.strip()
    print(f"完成：dist/demo_v2.mp4（{float(dur):.1f}s）")


if __name__ == "__main__":
    main()
