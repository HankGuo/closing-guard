# Benchmarks

> **口径说明**：本页的 7–8.4s 是**冷启动后单张图端到端**（含视觉编码）的实测；`reports/eval.md` 里的 1.4–4.5s 是 **8 张评测集在同一进程、warm cache 下逐样本**的耗时。两者不是同一口径，不要互相换算。以 `reports/eval.json` 为评测表唯一真源。


All numbers below were measured on the development machine unless stated
otherwise. They are **pilot numbers**, not a controlled benchmark across
hardware.

## Machine

- Apple M1 (8 cores: 4P + 4E), 16GB unified memory, macOS 26.6.2.
- `llama.cpp` 1.0.0 (Homebrew), Metal backend.
- Python 3.11.5.

## Model footprint

| Model | File(s) | Size | Runtime RAM (observed) |
|---|---|---|---|
| MiniCPM-V 4.7 1B | `MiniCPM-V-4_7-1B-Q4_K_M.gguf` + `mmproj-v47-f16.gguf` | 641MiB + 1.0GiB | ~5.1GB peak RSS (Metal) |
| MiniCPM-OCR 1.0 | `MiniCPM-OCR-1_0-Q8_0.gguf` + `mmproj-ocr-4x.gguf` | 774MiB + 859MiB | ~2–4GB class |
| MiniCPM-OCR Jev | `MiniCPM-OCR-Jev-Q4_K_M.gguf` + `mmproj-jev-f16.gguf` | 1.2GiB + 640MiB | 2-class decision model; ~2–3GB class |
| MiniCPM-V 4.7 35B-A3B | not used | ~16.6GB on-device pack | ≥12GB RAM; not suitable for 16GB M1/old phones |

## MiniCPM-V 4.7 1B on M1

| Metric | Value |
|---|---|
| Text generation | **60.9 tok/s** |
| Prompt processing (text) | **45.4 tok/s** |
| Vision encode | **3.1–4.5 s** per image |
| End-to-end single image (warm) | **7–8.4 s** |
| JSON verdict | works with GBNF grammar (`pass|fail|unsure`, 0..1 confidence) |
| Peak RSS | **~5.1GB** |

These are warm-cache measurements. A cold process load adds a few seconds.

## MiniCPM-OCR 1.0 on M1

| Metric | Value |
|---|---|
| Prompt processing | **156 tok/s** |
| Generation | **40 tok/s** |
| Synthetic gas-meter card | `reading=00123.456`, `unit=m³`, pass |
| Real water meter | `reading=0.056`（原始 OCR 文本 `0.0562`，归一化到 3 位小数）; returns **unsure** because the last digit is rolling |
| PDF/receipt text | strong on large Chinese text; not a substitute for a dedicated meter OCR + human confirmation |

## MiniCPM-OCR Jev on M1

| Candidate | Region | `prob_1` | Decision |
|---|---|---|---|
| `00123.456 m³` (correct) | synthetic gas-meter card crop | **0.983** | auto-accept |
| `00123.999 m³` (wrong digits) | same crop | **0.0035** | human review |
| `00123.456 m` (wrong unit) | same crop | 0.020 | human review |
| `0.056` (real water meter OCR) | real water meter crop | **0.004** | human review |

The engine is the official llama.cpp decision-model endpoint `/v1/systemone`
(`decision model type: openbmb-minicpm-ocr-jev`). It runs on the same M1, no
cloud call. The score is a consistency probability, not a truth guarantee; the
threshold is calibrated on the test card, not on a store.

## Pilot evaluation (`reports/eval.md`)

- 8 images, 4 checkpoints, 2 images per checkpoint.
- **Verdict accuracy: 87.5%**
- **False pass on expected-fail items: 0**
- Mean capture latency: 见 `reports/eval.json`（2026-11-14 运行为 **1.85 s**，warm cache；每次运行不同）
- The power-panel ON image returned `unsure` in the final run; in an earlier run
  the 1B returned `pass` with 0.8 confidence on the same ON panel. This variance
  is why critical items require human confirmation.
- Jev gave the OCR test card **0.983** and the real water meter **0.004**; the
  latter is routed to a human instead of being treated as a billing value.
- The gas-flame image is caught by the CV flame check even when the 1B says pass.

## Android

| Item | Value |
|---|---|
| Emulator | `sdk_gphone64_arm64`, Android 14 / API 34, arm64-v8a, 1080x2400 |
| App | WebView shell, `minSdk 24`, APK ~3.0MB |
| WebView | Chromium 113 (emulator image) |
| Camera | virtual scene; `getUserMedia` works; `source=camera` evidence produced |
| On-device LLM | **not benchmarked on the phone**; the models run on the local hub. The official MiniCPM-V-Apps Android demo exists; a phone-side 1B benchmark is on the roadmap. |

## Reproduce

```bash
# 1B text
llama-cli -m models/MiniCPM-V-4_7-1B-Q4_K_M.gguf -p "你好" -n 64 -t 6

# 1B vision + JSON grammar
llama-mtmd-cli -m models/MiniCPM-V-4_7-1B-Q4_K_M.gguf \
  --mmproj models/mmproj-v47-f16.gguf \
  --image data/samples/gas_valve_closed.jpg \
  -p "判断阀门是否关闭，只输出 JSON" -n 128 --temp 0

# OCR
llama-mtmd-cli -m models/MiniCPM-OCR-1_0-Q8_0.gguf \
  --mmproj models/mmproj-ocr-4x.gguf \
  --image data/samples/gas_meter_card.jpg \
  -p "Text Recognition:" -n 256 --temp 0

# Jev
curl -s http://127.0.0.1:8083/v1/models
# Full pilot
make e2e
make eval
```
