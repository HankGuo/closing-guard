"""Generate the 1440x900 slides used by the demo video."""
from __future__ import annotations

from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "slides"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1440, 900

BG = (7, 17, 15)
PANEL = (15, 33, 30)
PANEL2 = (19, 42, 38)
LINE = (31, 58, 53)
TEXT = (233, 245, 241)
MUTED = (143, 176, 168)
TEAL = (45, 212, 191)
GREEN = (52, 211, 153)
AMBER = (251, 191, 36)
RED = (248, 113, 113)

FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"


def f(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(FONT, size)


def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # subtle grid
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=(10, 25, 22), width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=(10, 25, 22), width=1)
    # corner glow
    d.ellipse([-260, -320, 520, 260], fill=(9, 38, 33))
    d.ellipse([W - 420, H - 260, W + 220, H + 260], fill=(9, 30, 40))
    d.rectangle([0, 0, W, 6], fill=TEAL)
    # logo
    d.rounded_rectangle([64, 54, 112, 102], radius=12, fill=TEAL)
    d.text((88, 78), "打", font=f(28, True), fill=(4, 33, 29), anchor="mm")
    d.text((128, 64), "打烊 · Closing Guard", font=f(26, True), fill=TEXT)
    d.text((128, 98), "MINICPM ON-DEVICE SAFETY AGENT", font=f(12), fill=MUTED)
    d.text((W - 64, 78), "S2 · 进阶挑战", font=f(16), fill=MUTED, anchor="rm")
    return im, d


def title_slide() -> None:
    im, d = base()
    d.text((72, 220), "让最后一盏灯，", font=f(78, True), fill=TEXT)
    d.text((72, 320), "关得明白。", font=f(78, True), fill=TEAL)
    d.text((76, 450), "旧手机 × 本地 MiniCPM 的闭店安全 Agent", font=f(28), fill=MUTED)
    d.rounded_rectangle([72, 540, 520, 604], radius=12, fill=PANEL2, outline=LINE)
    d.text((96, 572), "0 新增硬件  ·  100% 本地推理  ·  4 项核验", font=f(18), fill=TEXT)
    d.text((76, 690), "MiniCPM-V 4.7 1B  +  MiniCPM-OCR 1.0  +  OpenCV", font=f(20), fill=TEAL)
    # right phone silhouettes
    for x, y, s in ((900, 210, 1.0), (1110, 300, 0.86)):
        d.rounded_rectangle([x, y, x + int(180 * s), y + int(330 * s)], radius=26, fill=(10, 26, 23), outline=(45, 85, 76), width=2)
        d.ellipse([x + int(70 * s), y + int(130 * s), x + int(110 * s), y + int(170 * s)], outline=TEAL, width=3)
        d.text((x + int(90 * s), y + int(280 * s)), "旧手机 · 采集", font=f(12), fill=MUTED, anchor="mm")
    im.save(OUT / "slide_01_title.png")


def problem() -> None:
    im, d = base()
    d.text((72, 150), "为什么是现在", font=f(18, True), fill=TEAL)
    d.text((72, 190), "小店最后十分钟，没人替它看一眼", font=f(44, True), fill=TEXT)
    stats = [("757.77 万", "餐饮商户（2025）"), ("87.2%", "火灾发生在 300㎡ 以下"), ("4.21 万起", "近三年餐饮火灾"), ("7.93 亿元", "直接财产损失")]
    for i, (num, lab) in enumerate(stats):
        x = 72 + (i % 2) * 650
        y = 300 + (i // 2) * 190
        d.rounded_rectangle([x, y, x + 600, y + 150], radius=16, fill=PANEL, outline=LINE)
        d.text((x + 28, y + 30), num, font=f(44, True), fill=TEAL)
        d.text((x + 28, y + 98), lab, font=f(18), fill=MUTED)
    d.text((72, 710), "商场“三关一闭”有物业逐店检查；街边店只有一张纸质表，照片里阀门关没关，没人知道。", font=f(20), fill=TEXT)
    d.text((72, 750), "传感器 + 云平台 + 年费：小店装不起。", font=f(20), fill=AMBER)
    im.save(OUT / "slide_02_problem.png")


def solution() -> None:
    im, d = base()
    d.text((72, 150), "我们的做法", font=f(18, True), fill=TEAL)
    d.text((72, 190), "把“拍照留痕”变成“可核验的任务链”", font=f(40, True), fill=TEXT)
    cols = [
        ("01  旧手机", "相机 / 屏幕 / 喇叭 / 电池\n不用买新硬件，Android 7+ 就能用", TEAL),
        ("02  本地 MiniCPM", "1B 看语义，OCR 读表计\nOpenCV 做几何与火焰交叉检查", GREEN),
        ("03  证据台账", "AI 建议 + 人工确认\nSHA-256 链 + 二维码复核", AMBER),
    ]
    for i, (title, body, color) in enumerate(cols):
        x = 72 + i * 452
        d.rounded_rectangle([x, 300, x + 410, 560], radius=18, fill=PANEL, outline=LINE)
        d.text((x + 26, 326), title, font=f(26, True), fill=color)
        for j, line in enumerate(body.split("\n")):
            d.text((x + 26, 390 + j * 34), line, font=f(17), fill=TEXT)
    d.rounded_rectangle([72, 620, 1368, 748], radius=18, fill=(8, 32, 29), outline=(45, 100, 88))
    d.text((100, 650), "AI 有权说“不”：看不到、看不清、角度不对、有明火 —— 不让你点完成。", font=f(24, True), fill=TEAL)
    d.text((100, 700), "关键项即使 AI 判 pass，也必须人工确认；台账记录“AI 建议 + 人签字”。", font=f(18), fill=MUTED)
    im.save(OUT / "slide_03_solution.png")


def architecture() -> None:
    im, d = base()
    d.text((72, 150), "架构", font=f(18, True), fill=TEAL)
    d.text((72, 190), "所有推理都在本地；没有云 API，没有视频上传", font=f(38, True), fill=TEXT)

    def box(x, y, w, h, title, lines, color=TEAL):
        d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=PANEL, outline=LINE, width=2)
        d.text((x + 20, y + 18), title, font=f(22, True), fill=color)
        for i, line in enumerate(lines):
            d.text((x + 20, y + 60 + i * 28), line, font=f(15), fill=MUTED)

    box(70, 300, 330, 210, "旧手机 / 模拟器", ["Camera + WebView", "Android 7+ · minSdk 24", "localhost + adb reverse"], GREEN)
    box(500, 260, 390, 290, "本地 hub", ["FastAPI Agent", "MiniCPM-V 4.7 1B :8081", "MiniCPM-OCR 1.0 :8082", "OpenCV / SQLite", "PDF + 哈希链"], TEAL)
    box(990, 300, 370, 210, "证据台账", ["逐项照片 + 模型结论", "人工确认 + SHA-256 链", "二维码复核"], AMBER)
    d.line([(400, 405), (495, 405)], fill=TEAL, width=3)
    d.polygon([(495, 405), (480, 396), (480, 414)], fill=TEAL)
    d.line([(890, 405), (985, 405)], fill=TEAL, width=3)
    d.polygon([(985, 405), (970, 396), (970, 414)], fill=TEAL)
    d.text((70, 600), "手机只是眼睛和手；模型、证据、报告都在本地 hub。", font=f(20), fill=TEXT)
    d.text((70, 650), "模型服务：llama.cpp Metal / CPU；JSON verdict 由 GBNF 语法约束。", font=f(17), fill=MUTED)
    d.text((70, 690), "旧手机不需要编译 llama.cpp；2016 年后的设备也能当终端。", font=f(17), fill=MUTED)
    im.save(OUT / "slide_04_architecture.png")


def jev() -> None:
    im, d = base()
    d.text((72, 150), "OCR 的刹车", font=f(18, True), fill=TEAL)
    d.text((72, 190), "Jev：把候选读数渲染回去，再和原图比对", font=f(38, True), fill=TEXT)
    # flow boxes
    steps = [
        ("原图区域", "表计 / 单据裁剪"),
        ("候选文本", "OCR 读数 + 单位"),
        ("渲染图", "候选文本画回图片"),
        ("Jev 打分", "0–1 一致性"),
    ]
    for i, (title, sub) in enumerate(steps):
        x = 72 + i * 330
        d.rounded_rectangle([x, 300, x + 290, 430], radius=14, fill=PANEL, outline=LINE)
        d.text((x + 20, 320), title, font=f(20, True), fill=TEAL if i < 3 else AMBER)
        d.text((x + 20, 362), sub, font=f(15), fill=MUTED)
        if i < 3:
            d.line([(x + 290, 365), (x + 320, 365)], fill=TEAL, width=3)
            d.polygon([(x + 320, 365), (x + 308, 357), (x + 308, 373)], fill=TEAL)
    d.rounded_rectangle([72, 500, 680, 700], radius=16, fill=(8, 40, 32), outline=(45, 120, 95))
    d.text((100, 528), "0.983", font=f(64, True), fill=GREEN)
    d.text((100, 610), "测试卡：自动接受", font=f(18), fill=TEXT)
    d.rounded_rectangle([740, 500, 1368, 700], radius=16, fill=(40, 18, 16), outline=(120, 55, 45))
    d.text((768, 528), "0.004", font=f(64, True), fill=RED)
    d.text((768, 610), "真实水表：转人工", font=f(18), fill=TEXT)
    d.text((72, 750), "Jev 不做安全判官：低分只让读数 unsure，不会自动判 FAIL。", font=f(17), fill=AMBER)
    im.save(OUT / "slide_04b_jev.png")


def demo_title() -> None:
    im, d = base()
    d.text((72, 250), "真实链路演示", font=f(64, True), fill=TEXT)
    d.text((72, 350), "桌面端 · Android WebView · 真实 MiniCPM 推理", font=f(28), fill=TEAL)
    d.text((72, 470), "明火 → FAIL  ·  合格 → PASS  ·  开锁 → FAIL  ·  上锁 → PASS", font=f(22), fill=MUTED)
    d.text((72, 540), "没有 mock，没有云 API；每一步都有证据。", font=f(20), fill=TEXT)
    im.save(OUT / "slide_05_demo.png")


def results() -> None:
    im, d = base()
    d.text((72, 145), "测试结果", font=f(18, True), fill=TEAL)
    d.text((72, 182), "8 张对抗样本：87.5%，0 false pass，平均 3.0s", font=f(36, True), fill=TEXT)
    rows = [
        ("gas_valve", "明火 / 合格", "fail / pass", "CV 火焰拦截"),
        ("power_panel", "OFF / ON", "pass / unsure", "1B 不可靠，人工确认"),
        ("door_lock", "开锁 / 上锁", "fail / pass", "语义清晰"),
        ("gas_meter", "测试卡 / 真实水表", "pass / unsure", "末位滚动，人工确认"),
    ]
    d.rounded_rectangle([72, 270, 1368, 540], radius=16, fill=PANEL, outline=LINE)
    d.text((100, 292), "Checkpoint", font=f(15, True), fill=MUTED)
    d.text((400, 292), "样本", font=f(15, True), fill=MUTED)
    d.text((700, 292), "Actual", font=f(15, True), fill=MUTED)
    d.text((1000, 292), "说明", font=f(15, True), fill=MUTED)
    for i, row in enumerate(rows):
        y = 342 + i * 48
        d.text((100, y), row[0], font=f(17, True), fill=TEXT)
        d.text((400, y), row[1], font=f(17), fill=MUTED)
        d.text((700, y), row[2], font=f(17), fill=TEAL)
        d.text((1000, y), row[3], font=f(15), fill=MUTED)
    d.text((72, 600), "单元测试 8 passed  ·  HTTP e2e 1 passed  ·  Android WebView e2e valid=true", font=f(18), fill=TEXT)
    d.text((72, 650), "小样本试点，不是统计显著 benchmark；模型的失败模式必须被看见。", font=f(17), fill=AMBER)
    d.text((72, 700), "所以：关键项 AI 通过，仍然需要人工确认。", font=f(20, True), fill=TEAL)
    im.save(OUT / "slide_06_results.png")


def prior_art() -> None:
    im, d = base()
    d.text((72, 145), "原创性边界", font=f(18, True), fill=TEAL)
    d.text((72, 182), "不碰瓷，也不抄袭；把 prior art 写进 README", font=f(38, True), fill=TEXT)
    rows = [
        ("S1 家庭视觉助手", "被动监控 + 日报", "主动引导 + 逐项核验 + 签字"),
        ("CheckFlow / 问卷星", "拍照留痕", "模型判断内容，未核验不能提交"),
        ("商场三关一闭平台", "传感器 + 云 + 年费", "零硬件、本地、商户自用"),
        ("2022 阀门专利", "贴标记 + 固定摄像头", "无标记、手持、多模态、边缘"),
    ]
    d.rounded_rectangle([72, 280, 1368, 610], radius=16, fill=PANEL, outline=LINE)
    d.text((100, 304), "已有工作", font=f(15, True), fill=MUTED)
    d.text((560, 304), "它做了什么", font=f(15, True), fill=MUTED)
    d.text((940, 304), "我们的差别", font=f(15, True), fill=MUTED)
    for i, row in enumerate(rows):
        y = 356 + i * 56
        d.text((100, y), row[0], font=f(16, True), fill=TEXT)
        d.text((560, y), row[1], font=f(15), fill=MUTED)
        d.text((940, y), row[2], font=f(15), fill=TEAL)
    d.text((72, 680), "代码从零写；只引用，不复制。", font=f(20, True), fill=TEXT)
    im.save(OUT / "slide_07_prior_art.png")


def safety() -> None:
    im, d = base()
    d.text((72, 150), "边界", font=f(18, True), fill=RED)
    d.text((72, 190), "它不是安全保证", font=f(48, True), fill=TEXT)
    bullets = [
        ("01", "模型会错", "1B 曾在 ON 配电箱上给出错误 pass；关键项强制人工确认。"),
        ("02", "OCR 末位不可信", "真实水表滚动位读成 0.0562；系统返回 unsure，要求人工确认。"),
        ("03", "不替代法定检查", "闻到燃气味/看见明火：立即撤离，拨打 119，不要依赖软件。"),
    ]
    for i, (num, title, body) in enumerate(bullets):
        y = 310 + i * 140
        d.rounded_rectangle([72, y, 1368, y + 112], radius=14, fill=PANEL, outline=LINE)
        d.text((98, y + 22), num, font=f(18, True), fill=RED)
        d.text((160, y + 20), title, font=f(24, True), fill=TEXT)
        d.text((160, y + 62), body, font=f(16), fill=MUTED)
    d.text((72, 760), "辅助检查与记录工具 · 不构成任何形式的安全保证", font=f(18), fill=AMBER)
    im.save(OUT / "slide_08_safety.png")


def closing() -> None:
    im, d = base()
    d.text((72, 220), "旧手机不是电子垃圾，", font=f(52, True), fill=TEXT)
    d.text((72, 300), "它可以是最后一分钟的证人。", font=f(52, True), fill=TEAL)
    d.text((72, 430), "打烊 · Closing Guard", font=f(30, True), fill=TEXT)
    d.text((72, 480), "github.com/HankGuo/closing-guard", font=f(22), fill=MUTED)
    d.text((72, 540), "Apache-2.0  ·  MiniCPM Spark Program S2  ·  On-Device Agent Challenge", font=f(16), fill=MUTED)
    qr = qrcode.make("https://github.com/HankGuo/closing-guard").resize((210, 210))
    im.paste(qr, (1130, 520))
    im.save(OUT / "slide_09_closing.png")


if __name__ == "__main__":
    title_slide()
    problem()
    solution()
    architecture()
    jev()
    demo_title()
    results()
    prior_art()
    safety()
    closing()
    print("slides written to", OUT)
