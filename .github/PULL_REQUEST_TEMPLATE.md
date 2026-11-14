## What changed

## Why

## How it was tested

- [ ] `make test`
- [ ] `make e2e` (if the change touches capture/verdict/report)
- [ ] Web build (`cd web && npm run build`)
- [ ] Android build / emulator e2e (if the change touches the app)

## Safety checklist

- [ ] I did not weaken the "critical item requires human confirmation" rule.
- [ ] Any new sample image has a license and attribution in `data/README.md`.
- [ ] I did not add a mock that pretends to be model output.
