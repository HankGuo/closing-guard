# Prior art and originality boundary

Closing Guard is not the first project to use old phones as cameras, and it is
not the first "three-off-one-close" tool. The originality claim is narrower and
defensible: **a task-conducting, local-first closing agent with cross-checked
verification, mandatory human confirmation, and a hash-chained evidence ledger,
designed for small shops with zero hardware budget.**

## Prior art

| Work | What it does | What we do differently |
|---|---|---|
| [S1 家庭视觉助手降本实践](https://openbmb.cn/blog/minicpm-spark-program-s1-winners) | Mac mini + cameras + lightweight detector + MiniCPM-V; 720 → 60–70 calls/day; daily digest | Active, guided procedure; per-item verification; re-check/remediation; human sign-off; no passive digest |
| [CheckFlow](https://apps.apple.com/cn/app/checkflow-%E9%97%A8%E5%BA%97%E5%B7%A1%E6%A3%80%E6%A3%80%E6%9F%A5%E8%A1%A8/id6787944505) / 问卷星 | Digital checklist + photo evidence | The model checks the photo content; an unverified item cannot be submitted |
| Mall "三关一闭" platforms, e.g. [金和](http://jinher.com/Article/index/id/534/aid/47126), [润欣 2026 procurement](https://www.coopaa.com/notice-29502546.html) | Sensors + cloud + property staff + annual fee | Zero hardware, local, merchant-owned; phones are the terminals |
| [2022 valve inspection patent](https://www.jigao616.com/zhuanlijieshao_34255706.aspx) | Markers + fixed camera + reference matching + server | Markerless, handheld, multimodal, edge inference |
| [福建移动 视联网+AI](https://www.cnii.com.cn/gxxww/rmydb/202512/t20251212_702455.html) | 4MP cameras + AI gas-valve state recognition, ~1200 restaurants | Operator/regulator-scale, cloud, fixed views; ours is a small-shop, local, zero-wiring tool |
| [Sentinel](https://github.com/suzuran0y/cctv-smartphone-ai-monitoring) / OpenClaw / [MiniCPM-V-Apps](https://github.com/OpenBMB/MiniCPM-V-Apps) | Old-phone camera node / general agent / on-device chat | A vertical closing state machine + evidence chain + critical-item human confirmation; not a general framework |
| 明厨亮灶 / 美团免费摄像头 | Cloud cameras + food-safety AI during business | Closing safety, local, no video upload; complementary |

## What is original here

1. **Task-conducting UI**: the agent leads a physical closing procedure, not a
   passive monitor or a chat box.
2. **Cross-checked verification**: CV geometry + flame colours + 1B semantics +
   OCR, with an explicit "unsure → re-shoot → human" path.
3. **Critical-item human confirmation**: even a confident 1B `pass` cannot close
   a gas valve / panel / lock without a human action. The ledger records both.
4. **Session-wide hash chain** with a QR verification page and a PDF ledger.
5. **Legacy-phone tiering**: the Android app is a thin WebView shell; the heavy
   models run on a local hub; the same UI works on a 2016+ phone, emulator, or
   desktop browser.
6. **Open, reproducible test harness**: real local models, real Android WebView
   e2e, and a labelled adversarial pilot set.

## What we do **not** claim

- Not "the first" old-phone camera project.
- Not "the first" three-off-one-close tool.
- Not a certified fire/gas/electrical safety system.
- Not a replacement for a property inspection or a licensed professional.
- Not a statistically significant benchmark (8 images).

## Code, data, and licenses

- Application code: written from scratch for this repository, Apache-2.0.
- Dependencies: `llama.cpp` (MIT), FastAPI (MIT), React (MIT), OpenCV
  (Apache-2.0), WeasyPrint (BSD), SQLite (public domain).
- Model weights: downloaded from OpenBMB/ModelScope under their own licenses;
  not committed.
- Sample photos: Wikimedia Commons, attribution and licenses in
  `data/README.md`. They are test fixtures, not part of the Apache-2.0 code.
- No code from the S1 winners, CheckFlow, Sentinel, OpenClaw, or the 2022 patent
  is copied. They are cited as prior art only.
