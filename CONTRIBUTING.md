# Contributing

Thanks for helping. Closing Guard is a safety-adjacent project: please keep the
human-in-the-loop guarantees intact.

## Setup

```bash
make setup
make models
make serve      # terminal 1
make web        # build the UI
make api        # terminal 2
```

## Before a PR

```bash
make test       # unit tests, no model servers required
make e2e        # requires live model servers on :8010 + :8081 + :8082
cd web && npm run build
ruff check server scripts tools
```

- Do not add mocks that pretend to be model output. If a test needs a model,
  mark it `e2e` and document the prerequisite.
- Do not commit model weights, APKs, videos, or `runs/` data.
- Do not weaken the rule "critical items require human confirmation".
- New sample images must have a clear license and attribution in `data/README.md`.

## Commit style

Conventional commits are appreciated (`feat:`, `fix:`, `docs:`, `test:`).
