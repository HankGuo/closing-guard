# Roadmap

## v0.2 — close the model gaps

- **Panel handle CV**: detect breaker handle positions (up/down) with a small
  detector or template matching; use the 1B only for semantic confirmation.
- **Jev threshold calibration**: collect 200+ real meter crops with ground
  truth, calibrate the auto-accept threshold per meter type; the current 0.8
  threshold is from the synthetic card, not a store.
- **Multi-frame consensus**: capture 3 frames per checkpoint and require
  agreement; detect the rolling meter digit.
- **Better reference alignment**: let the operator draw a ROI; compare angles
  relative to the pipe/handle, not the whole image.

## v0.3 — real devices and stores

- Physical old-phone pilot (Android 7/8/9, 3–4GB RAM), measuring camera low-light,
  thermal, battery, and WebView compatibility.
- On-phone llama.cpp path (Termux or a small JNI app) for offline/VLM
  inference; the hub remains the default. This is the main “on-device” gap.
- 3–5 real stores, 2 weeks, with a written consent and anonymized data.
- HTTPS on the LAN (self-signed/private CA) for non-localhost camera access.

## v0.4 — product

- Multi-store dashboard, per-store checklists, staff accounts.
- Insurer/property integration: export a signed evidence pack; webhook/email.
- Chain anchoring: RFC 3161 timestamp or a customer-provided signing key.
- i18n (English/Chinese), accessibility, larger touch targets.
- Android foreground service + offline queue.

## Research questions

- How much does the 1B's panel error rate drop with a CV handle detector?
- Can a 1B + reference image reliably distinguish "valve closed" from "valve
  open" across valve types?
- What is the minimum human confirmation UX that keeps completion rate high?
- Can a local 2B text model write the weekly risk summary without hallucinating?
