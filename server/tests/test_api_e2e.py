"""Real HTTP end-to-end test. Requires CG_E2E=1 and live local model servers."""
import os
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
API = os.getenv("CG_API", "http://127.0.0.1:8010")
SAMPLES = ROOT / "data" / "samples"

pytestmark = pytest.mark.e2e


def capture(client, sid, checkpoint, image):
    with (SAMPLES / image).open("rb") as fh:
        r = client.post(
            f"{API}/api/sessions/{sid}/capture",
            data={"checkpoint_id": checkpoint, "source": "e2e"},
            files={"file": (image, fh, "image/jpeg")},
            timeout=240,
        )
    r.raise_for_status()
    return r.json()


def test_full_closing_loop():
    with httpx.Client(timeout=30) as client:
        health = client.get(f"{API}/api/health").json()
        assert health["ok"] is True

        session = client.post(
            f"{API}/api/sessions",
            json={"store_name": "pytest 演示店", "checklist_id": "restaurant_closing", "operator": "pytest"},
        ).json()
        sid = session["id"]

        gas_fail = capture(client, sid, "gas_valve", "gas_stove_flame.jpg")
        assert gas_fail["verdict"] == "fail"
        gas_pass = capture(client, sid, "gas_valve", "gas_valve_closed.jpg")
        assert gas_pass["verdict"] == "pass"

        panel = capture(client, sid, "power_panel", "power_panel_off.jpg")
        assert panel["verdict"] in {"pass", "unsure"}

        door_fail = capture(client, sid, "door_lock", "door_unlocked.jpg")
        assert door_fail["verdict"] == "fail"
        door_pass = capture(client, sid, "door_lock", "door_locked.jpg")
        assert door_pass["verdict"] == "pass"

        meter = capture(client, sid, "gas_meter", "gas_meter_card.jpg")
        assert meter["verdict"] == "pass"
        assert meter["ocr"]["reading"] == "00123.456"
        assert meter["ocr"]["jev"]["prob_1"] > 0.8

        # Completion is blocked until critical items get a human confirmation.
        blocked = client.post(f"{API}/api/sessions/{sid}/complete")
        assert blocked.status_code == 409

        for cp in ("gas_valve", "power_panel", "door_lock"):
            r = client.post(
                f"{API}/api/sessions/{sid}/confirm",
                json={"checkpoint_id": cp, "action": "confirm", "note": "pytest 人工复核"},
            )
            assert r.status_code == 200

        done = client.post(f"{API}/api/sessions/{sid}/complete")
        assert done.status_code == 200
        assert done.json()["status"] == "completed"

        verify = client.get(f"{API}/api/verify/{sid}").json()
        assert verify["valid"] is True
        assert verify["matches_session"] is True

        pdf = client.get(f"{API}/api/sessions/{sid}/report.pdf")
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF")
