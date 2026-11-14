"""Build the narrated demo video from slides, screen recordings, and edge-tts.

This is an open-source pipeline: FFmpeg (editing/compositing), PIL (slides),
edge-tts (voice), and the real screen recordings produced by Playwright/adb.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "docs" / "slides"
VIDEO = ROOT / "runs" / "video"
AUDIO = VIDEO / "audio"
DIST = ROOT / "dist"
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
EDGE = ROOT / ".venv" / "bin" / "edge-tts"
VOICE = "zh-CN-XiaoxiaoNeural"

AUDIO.mkdir(parents=True, exist_ok=True)
DIST.mkdir(exist_ok=True)

SECTIONS = [
    (
        "01_title",
        "slide_01_title.png",
        "晚上十点，最后一位客人走了。接下来十分钟，决定这家店今晚安不安全。",
    ),
    (
        "02_problem",
        "slide_02_problem.png",
        "中国有七百五十七万家餐饮商户。近三年，餐饮场所火灾四点二一万起，一百八十七人死亡，直接财产损失七点九三亿元。其中百分之八十七点二，发生在三百平米以下的小店。"
        "商场里的三关一闭，有物业逐店检查。街边小店呢？一张纸质表，拍张照，阀门到底关没关，没人知道。传感器加云平台加年费，小店也装不起。",
    ),
    (
        "03_solution",
        "slide_03_solution.png",
        "所以我们做了打烊，Closing Guard。用抽屉里的旧手机，加上本地 MiniCPM，把闭店检查变成一条 Agent 任务链。"
        "旧手机负责看、拍、说话；本地 hub 负责理解。MiniCPM-V 4.7 1B 判断阀门、门锁、配电箱的语义状态；MiniCPM-OCR 1.0 读取表计；OpenCV 做几何和火焰交叉检查。"
        "模型不确定，就要求重拍；发现异常，就要求整改；关键项就算 AI 说通过，也必须人工确认。最后生成一份带哈希链的台账。",
    ),
    (
        "04_architecture",
        "slide_04_architecture.png",
        "所有推理都在本地，没有云 API，没有视频上传。手机通过 localhost 访问 hub；模型输出被语法约束成 JSON；每一条证据都写入 SQLite 和一条会话级哈希链。",
    ),
    (
        "04b_jev",
        "slide_04b_jev.png",
        "OCR 还有一个刹车：Jev。它把候选读数渲染回图片，和原图比对，给出一致性分数。测试卡零点九八，自动接受；真实水表零点零零四，转人工。Jev 不做安全判官，低分只让读数变成 unsure。",
    ),
    (
        "05_demo_title",
        "slide_05_demo.png",
        "下面看真实链路。桌面端先走一遍，再在 Android WebView 里走一遍。没有 mock，每一步都有证据。",
    ),
    (
        "06_results",
        "slide_06_results.png",
        "我们没有 mock。单元测试八项；HTTP 端到端测试跑真实模型；Android WebView 端到端测试通过 CDP 驱动真实 UI，最后哈希链 valid。"
        "八张对抗样本，判定准确率百分之八十七点五，false pass 零，平均三秒。但这不是统计显著的 benchmark；配电箱的 ON 图，1B 曾经给出过错误的 pass。所以关键项必须人工确认。",
    ),
    (
        "07_prior_art",
        "slide_07_prior_art.png",
        "旧手机做摄像头不新，三关一闭不新，AI 看阀门也有专利。我们的原创性在于：面向小店的零硬件形态、主动引导的任务闭环、CV 加 OCR 加 1B 的交叉核验、以及可追溯的证据链。",
    ),
    (
        "08_safety",
        "slide_08_safety.png",
        "它不是安全保证，不替代法定检查。闻到燃气味，请立即撤离并拨打一一九。",
    ),
    (
        "09_closing",
        "slide_09_closing.png",
        "旧手机不是电子垃圾，它可以是最后一分钟的证人。打烊 Closing Guard，代码和测试都在 GitHub。",
    ),
]

DEMO_A = (
    "先看桌面端。选择门店，创建任务。相机对准燃气阀，拍照。1B 判断阀门关闭，几何检查通过，人工确认。"
    "配电箱、门锁、燃气表，逐项完成。最后生成台账，扫码就能复核哈希链。"
)
DEMO_B = (
    "这是 Android 端，同一个系统跑在模拟器里。明火照片被火焰交叉检查拦下，AI 拒绝通过；换成合格照片，复查通过。"
    "开锁的挂锁被判 fail，上锁后 pass。注意：关键项的 AI 通过，仍然需要人工确认。"
)


def run(cmd: list[str], **kw) -> None:
    print("$", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, **kw)


def duration(path: Path) -> float:
    out = subprocess.check_output(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]
    )
    return float(json.loads(out)["format"]["duration"])


def tts(name: str, text: str) -> Path:
    out = AUDIO / f"{name}.mp3"
    if not out.exists():
        for attempt in range(3):
            try:
                run([str(EDGE), "--voice", VOICE, "--rate=+5%", "--text", text, "--write-media", str(out)])
                break
            except subprocess.CalledProcessError:
                if attempt == 2:
                    raise
    print(f"audio {name}: {duration(out):.1f}s")
    return out


def slide_segment(name: str, image: Path, audio: Path) -> Path:
    out = VIDEO / f"seg_{name}.mp4"
    run(
        [
            FFMPEG, "-y", "-loop", "1", "-framerate", "30", "-i", str(image),
            "-i", str(audio), "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest",
            "-r", "30", str(out),
        ]
    )
    return out


def demo_segments() -> list[Path]:
    desktop = sorted(VIDEO.glob("page@*.webm"), key=lambda p: p.stat().st_mtime)[-1]
    android = VIDEO / "android_demo.mp4"
    a1 = tts("05a_desktop", DEMO_A)
    a2 = tts("05b_android", DEMO_B)

    desk = VIDEO / "desk_fast.mp4"
    run([FFMPEG, "-y", "-i", str(desktop), "-vf", "setpts=0.40*PTS,fps=30,scale=1440:900", "-an", str(desk)])
    phone = VIDEO / "phone_fast.mp4"
    run([
        FFMPEG, "-y", "-i", str(android), "-vf",
        "setpts=0.66*PTS,fps=30,scale=-2:900,pad=1440:900:(ow-iw)/2:(oh-ih)/2:color=0x07110f",
        "-an", str(phone),
    ])

    def combine(video: Path, audio: Path, out: Path) -> Path:
        vdur = duration(video)
        adur = duration(audio)
        total = max(vdur, adur) + 0.5
        run([
            FFMPEG, "-y", "-i", str(video), "-i", str(audio), "-filter_complex",
            "[0:v]tpad=stop_mode=clone:stop_duration=10[v]", "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac",
            "-b:a", "192k", "-t", f"{total:.3f}", str(out),
        ])
        return out

    return [
        combine(desk, a1, VIDEO / "seg_05a_demo_desktop.mp4"),
        combine(phone, a2, VIDEO / "seg_05b_demo_android.mp4"),
    ]


def main() -> None:
    if not EDGE.exists():
        print("edge-tts not found; run: uv pip install edge-tts", file=sys.stderr)
        sys.exit(1)
    segments: list[Path] = []
    for name, image, text in SECTIONS:
        audio = tts(name, text)
        segments.append(slide_segment(name, SLIDES / image, audio))
    segments.extend(demo_segments())
    # Rebuild the list in presentation order.
    order = ["01_title", "02_problem", "03_solution", "04_architecture", "04b_jev",
             "05_demo_title", "05a_demo_desktop", "05b_demo_android",
             "06_results", "07_prior_art", "08_safety", "09_closing"]
    by_name = {p.stem.replace("seg_", ""): p for p in segments}
    ordered = [by_name[n] for n in order]
    concat = VIDEO / "final_concat.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in ordered), encoding="utf-8")
    out = DIST / "demo.mp4"
    run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out),
    ])
    print(f"final: {out} ({out.stat().st_size/1e6:.1f} MB, {duration(out):.1f}s)")


if __name__ == "__main__":
    main()
