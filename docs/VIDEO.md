# Demo video

**Rendered file:** `dist/demo.mp4` (not committed; attached to the `v0.1.2`
GitHub release). Length ~4 min 08 s, 1440×900, H.264/AAC, 7.1MB.

> The video is produced with an open-source pipeline: **FFmpeg** (editing,
> compositing, encoding), **Pillow** (slides), **edge-tts** (Chinese voiceover),
> and the real screen recordings from **Playwright** (desktop) and **adb
> screenrecord** (Android emulator).

## Storyboard

| Time | Section | Visual | Narration |
|---|---|---|---|
| 0:00 | Hook | title slide | “晚上十点，最后一位客人走了。接下来十分钟，决定这家店今晚安不安全。” |
| 0:08 | Problem | stats slide | 757.77 万商户；4.21 万起火灾；87.2% 在 300㎡ 以下；商场有物业，街边店只有一张纸 |
| 0:55 | Solution | three-column slide | 旧手机采集 + 本地 MiniCPM 核验 + 哈希链台账；“AI 有权说不” |
| 1:27 | Architecture | diagram | 本地 hub；VLM/OCR/OpenCV；SQLite + 哈希链；无云 API |
| 1:55 | Jev | Jev slide | OCR 候选渲染回图片 → 一致性分数；测试卡 0.983，真实水表 0.004 转人工 |
| 2:12 | Demo title | slide | 桌面端 + Android，真实链路，无 mock |
| 2:22 | Desktop demo | Playwright recording (accelerated) | 创建任务、相机对准阀门、逐项核验、人工确认、生成台账 |
| 2:48 | Android demo | adb screenrecord (accelerated, portrait) | 明火 → FAIL；合格 → PASS；开锁 → FAIL；上锁 → PASS；关键项人工确认 |
| 3:18 | Results | results slide | 8 samples, 87.5%, 0 false pass, 3.0s；Jev 0.983/0.004；unit/HTTP/Android e2e |
| 3:43 | Prior art | table slide | 旧手机摄像头/三关一闭/阀门专利都不新；原创性是组合与证据链 |
| 4:00 | Safety | safety slide | 不是安全保证；闻到燃气味撤离并拨打 119 |
| 4:08 | Closing | closing slide + QR | “旧手机不是电子垃圾，它可以是最后一分钟的证人。” |

## Production

```bash
# 1) slides
.venv/bin/python tools/make_slides.py

# 2) desktop recording + screenshots (needs a running API on :8010)
node tools/web_demo.cjs          # writes runs/video/page@*.webm

# 3) Android recording (needs the emulator + app + adb reverse/forward)
#    model servers: VLM :8081, OCR :8082, Jev :8083
adb shell screenrecord --time-limit 240 /sdcard/android_demo.mp4 &
.venv/bin/python scripts/android_e2e.py
adb shell pkill -INT screenrecord
adb pull /sdcard/android_demo.mp4 runs/video/android_demo.mp4

# 4) voice + edit
.venv/bin/python tools/make_video.py
```

The script uses `edge-tts` voice `zh-CN-XiaoxiaoNeural`. `dist/demo.mp4` is
ignored by git (large binary); upload it to the GitHub release and/or B站/知乎.

## Honesty notes

- The desktop demo uses Chromium's **fake camera device**, fed a real photo of a
  propane cylinder valve. The model and pipeline are real; the camera device is a
  browser test facility.
- The Android demo runs in a **real Android 14 emulator** with a virtual-scene
  camera; the material checks use real sample photos. No physical old phone was
  connected in this build.
- The video does not claim a real store pilot. It documents a runnable demo
  with emulator end-to-end tests and a real-image pilot evaluation.
