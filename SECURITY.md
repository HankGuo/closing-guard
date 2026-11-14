# Security policy

Closing Guard is a local-first prototype. It is **not** a certified fire,
gas, or electrical safety system.

## Reporting

Please open a private security advisory on GitHub if you find a vulnerability
that could cause a false PASS, evidence tampering, or local data exposure.
Do not include real customer photos or store credentials in a public issue.

## Scope

- Local HTTP API (`:8010`) has no authentication; bind it to localhost or a
  trusted LAN only.
- The Android WebView loads `http://localhost:8000` through `adb reverse`; do
  not expose that port to the public internet.
- Evidence is stored under `runs/`; protect the host disk and back it up.
- The hash chain detects accidental or simple tampering; it is not a substitute
  for a trusted timestamping service or a hardware root of trust.

## Safety reports

If you find a model failure that could produce a false PASS, please include the
image, checkpoint, model version, and the exact verdict. We will add it to the
adversarial set and document it.
