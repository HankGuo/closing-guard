PY := .venv/bin/python
PIP := .venv/bin/pip
JAVA_HOME ?= $(shell /usr/libexec/java_home -v 17 2>/dev/null)

.PHONY: demo setup models serve stop api web test e2e eval android screenshots slides video clean

demo:
	bash scripts/quickstart.sh

setup:
	@if command -v uv >/dev/null 2>&1; then \
		uv venv --python 3.11 .venv && \
		uv pip install --python .venv/bin/python -r server/requirements-dev.txt; \
	else \
		python3 -m venv .venv && \
		.venv/bin/python -m pip install -U pip && \
		.venv/bin/python -m pip install -r server/requirements-dev.txt; \
	fi
	cd web && npm install

models:
	scripts/download_models.sh

serve:
	scripts/run_models.sh

stop:
	scripts/stop_models.sh

api:
	cd server && ../$(PY) -m uvicorn app.main:app --host 127.0.0.1 --port 8010

web:
	cd web && npm run build

test:
	$(PY) -m pytest -q server/tests -m "not e2e"

e2e:
	CG_E2E=1 $(PY) -m pytest -q server/tests/test_api_e2e.py

eval:
	$(PY) scripts/eval.py

android:
	cd android && JAVA_HOME="$(JAVA_HOME)" ./gradlew assembleDebug

screenshots:
	node tools/web_demo.cjs

slides:
	$(PY) tools/make_slides.py

video:
	$(PY) tools/make_video.py

clean:
	rm -rf runs/ses_* runs/closing_guard.db runs/video
