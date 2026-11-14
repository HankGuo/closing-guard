# Testing

## Principles

- **No mocked model responses.** The e2e tests require the real `llama-server`
  processes and the real GGUF weights.
- **No mocked camera.** The Android camera test uses the emulator's real
  `getUserMedia` path; the desktop demo uses Chromium's fake camera device fed a
  real valve photo.
- The only synthetic *image* is `data/samples/gas_meter_card.jpg`, an OCR test
  card. It is labelled as synthetic in `data/README.md`.
- The emulator is a real Android runtime (API 34, arm64), not a mock API.

## Test matrix

| Test | Command | Result (2026-11-14) |
|---|---|---|
| Unit: CV quality/angle/flame, chain hash | `make test` | **8 passed** |
| HTTP e2e: real models, confirm, complete, verify, PDF | `CG_E2E=1 pytest -q server/tests/test_api_e2e.py` | **1 passed in 14.38s** |
| Android WebView e2e: real UI + real models + chain | `python scripts/android_e2e.py` | **ANDROID_E2E_OK**; `valid=true` |
| Android camera path | UI "拍照核验" on emulator | `source=camera`, quality ok, verdict fail (virtual scene) |
| Jev OCR gate | `gas_meter_card.jpg` / `water_meter.jpg` | card **0.983** → pass; water meter **0.004** → unsure |
| Pilot evaluation | `python scripts/eval.py` | **8 samples, 87.5%, 0 false pass**（延迟以 `reports/eval.json` 为准，每次运行不同） |
| Web build | `cd web && npm run build` | passed |

## Environment used

- macOS 26.6.2, Apple M1, 16GB unified memory.
- `llama.cpp` 1.0.0 (Homebrew), Metal backend.
- Python 3.11.5 in `.venv`.
- Android SDK 34, emulator 37.2.13, `sdk_gphone64_arm64` (API 34, arm64-v8a),
  1080x2400.
- Models: MiniCPM-V 4.7 1B Q4_K_M (641MiB) + mmproj f16 (1.0GiB);
  MiniCPM-OCR 1.0 Q8_0 (774MiB) + mmproj 4x (859MiB);
  MiniCPM-OCR Jev Q4_K_M (1.2GiB) + mmproj f16 (640MiB).

## Reproduce

```bash
# terminal 1: model servers
make models
make serve

# terminal 2: API + web
make web
make api          # http://127.0.0.1:8010

# terminal 3: tests
make test
CG_E2E=1 pytest -q server/tests/test_api_e2e.py
python scripts/eval.py
```

### Android WebView e2e

```bash
# terminal 1: API on :8010 and models on :8081/:8082
# terminal 2: emulator
emulator -avd cg_api34 -no-snapshot -no-audio -no-window \
  -gpu swiftshader_indirect -camera-back virtualscene -no-boot-anim

adb reverse tcp:8000 tcp:8010
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n com.closingguard.app/.MainActivity

PID=$(adb shell pidof com.closingguard.app | tr -d '\r')
adb forward tcp:9222 localabstract:webview_devtools_remote_$PID

source .venv/bin/activate
python scripts/android_e2e.py
```

The script prints each checkpoint verdict, takes screenshots into
`docs/screenshots/`, completes the session, and asserts `/api/verify` is valid.

## What the Android e2e actually asserts

1. Gas flame → `fail` (CV flame cross-check).
2. Gas valve closed → `pass`.
3. Power panel off → `pass` or `unsure` (1B is not trusted here).
4. Door unlocked → `fail`; door locked → `pass`.
5. Meter card → `pass` and OCR reading `00123.456`.
6. Completion is blocked until critical items are confirmed.
7. Completed session → PDF exists; `/api/verify/{id}` → `valid=true`,
   `matches_session=true`.

## Known test limitations

- The pilot set is **8 images**, intentionally adversarial, not statistically
  significant.
- The model server keeps a warm prompt cache; latency in a cold run will be
  higher (the gas-flame cold call was ~8.7s; the 1B vision encode alone is
  ~3–4.5s).
- The Android emulator camera is a virtual 3D scene, not a real valve. The
  camera *pipeline* is real; the material checks use real sample photos.
- No physical old phone was connected in this build. The APK targets
  `minSdk 24`; a real-device pass is listed in `ROADMAP.md`.
- Jev is integrated for OCR only; the VLM verdicts are not scored by Jev.
- The model still runs on the local hub, not inside the phone; see `ROADMAP.md`.
