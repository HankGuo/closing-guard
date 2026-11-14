# Safety, privacy, and limits

## What this is

A **local-first assistant** for the closing routine of a small shop. It guides a
person through a checklist, checks the photos with local models, asks for a
re-shoot when unsure, and produces an evidence ledger.

## What this is not

- Not a fire alarm, gas detector, or electrical safety device.
- Not a certified inspection.
- Not a replacement for a licensed electrician, gas engineer, or fire officer.
- Not an autonomous system that can close a store without a human.

## Non-negotiable rules in the code

1. A critical checkpoint (`gas_valve`, `power_panel`, `door_lock`) **cannot** be
   closed by a model `pass` alone. `agent.complete()` returns HTTP 409 until a
   human action is recorded.
2. A `fail` cannot be closed by a human action alone: the checkpoint must be
   re-captured and pass. An `unsure` can be closed by a human `confirm` or
   `resolved` action.
3. A suspected flame (CV colour cross-check) forces `fail`, even if the 1B says
   `pass`.
4. A low-quality image becomes `unsure` before any model call.
5. Jev never forces a safety FAIL. A low Jev consistency score makes the OCR
   reading `unsure`; a human must confirm the digits.
5. The report contains an explicit disclaimer and a "not a guarantee" statement.

## Observed model limitations

- **Power panel:** the 1B model can confidently misread breaker handle
  positions. In one run it returned `pass` (0.8) on a panel with most handles
  up/ON; in another run the same image returned `unsure`. It is not trusted as
  the sole judge. Mandatory human confirmation is the mitigation; a CV handle
  detector is on the roadmap.
- **Meter last digit:** a rolling digit is not a stable reading. OCR returns
  `unsure` and the operator must confirm. Jev catches gross mismatches
  (test card 0.983 vs real water meter 0.004), but it is a consistency model,
  not a metering certificate.
- **Low light / occlusion:** quality and CV confidence gates intentionally
  produce `unsure` rather than a guess.
- **Language:** the 1B sometimes answers in English even when asked for Chinese.
  The verdict JSON is still parsed; the report may contain mixed language.

## Physical safety

- If you smell gas, see a flame, or see damaged wiring: **evacuate, do not
  operate electrical switches, call 119 / the gas utility.** Do not rely on this
  software.
- Do not use a live gas line for a mock/demo. Use a disconnected cylinder or a
  photo.
- Old phone batteries can swell. Do not leave a swollen phone charging. Prefer a
  timer/smart plug, charge limiting, or a removable battery for fixed nodes.
- Mount phones away from heat, water, and moving machinery.

## Privacy

- All inference and evidence storage are local. No cloud API, no video upload.
- The sample dataset contains no customers. In a real store, avoid capturing
  faces; if unavoidable, blur them before sharing or exporting.
- The SQLite DB and images live under `runs/`. Protect the host disk; back up
  only encrypted copies.
- The local API has no authentication. Bind it to `127.0.0.1` or a trusted LAN;
  do not expose `:8010` to the internet.

## Evidence integrity

- Each image is hashed (SHA-256) after normalization; the verdict and metadata
  are chained. `GET /api/verify/{id}` recomputes the chain.
- This detects casual edits, not a determined attacker with host access. For
  stronger guarantees, add a trusted timestamp (RFC 3161) or a hardware-backed
  signature. See `SECURITY.md`.

## Responsible disclosure

If you find a failure that could produce a false PASS, please open a private
security advisory with the image, checkpoint, model version, prompt, and output.
We will add it to the adversarial set and document it.
