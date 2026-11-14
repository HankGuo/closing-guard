"""Real Android WebView + real MiniCPM end-to-end test.

Drives the actual WebView through CDP:
  * creates a session through the same HTTP API the UI uses,
  * selects real sample images in the UI,
  * waits for the real local model verdicts,
  * confirms critical items,
  * completes the session and verifies the hash chain.

No model, image, or API response is mocked.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.cdp import CDP  # noqa: E402

SHOTS = ROOT / "docs" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)


def adb_shot(name: str) -> None:
    data = subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True, check=True).stdout
    (SHOTS / name).write_bytes(data)
    print(f"screenshot: {SHOTS / name}")


async def state(cdp: CDP, sid: str) -> dict:
    return await cdp.eval(f"fetch('/api/sessions/{sid}').then(r=>r.json())")


def cp_state(s: dict, cp: str) -> dict:
    return next(c for c in s["checkpoints"] if c["config"]["id"] == cp)


async def wait_evidence(cdp: CDP, sid: str, cp: str, before_id: str | None, timeout: float = 120) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = await state(cdp, sid)
        ev = cp_state(s, cp).get("evidence")
        if ev and ev["id"] != before_id:
            return ev
        await asyncio.sleep(1)
    raise TimeoutError(f"no new evidence for {cp}; last state={json.dumps(s, ensure_ascii=False)[:800]}")


async def click_text(cdp: CDP, needle: str) -> bool:
    expr = f"""(() => {{
      const nodes = [...document.querySelectorAll('button, .check-item, a')];
      const el = nodes.find(n => (n.textContent || '').includes({json.dumps(needle, ensure_ascii=False)}));
      if (!el) return false;
      el.click();
      return true;
    }})()"""
    return bool(await cdp.eval(expr))


async def choose_sample(cdp: CDP, url: str) -> bool:
    expr = f"""(() => {{
      const sel = document.querySelector('select[aria-label="使用样张"]');
      if (!sel) return false;
      sel.value = {json.dumps(url)};
      sel.dispatchEvent(new Event('change', {{bubbles: true}}));
      return true;
    }})()"""
    return bool(await cdp.eval(expr))


async def confirm(cdp: CDP, sid: str, cp: str, note: str = "端到端测试人工复核") -> dict:
    return await cdp.eval(
        f"""fetch('/api/sessions/{sid}/confirm', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{checkpoint_id: {json.dumps(cp)}, action: 'confirm', note: {json.dumps(note, ensure_ascii=False)}}})
        }}).then(r => r.json())"""
    )


async def capture(cdp: CDP, sid: str, cp: str, sample: str) -> dict:
    s = await state(cdp, sid)
    before = (cp_state(s, cp).get("evidence") or {}).get("id")
    await click_text(cdp, {
        "gas_valve": "燃气总阀",
        "power_panel": "配电箱",
        "door_lock": "后门/总门门锁",
        "gas_meter": "燃气表读数",
    }[cp])
    await asyncio.sleep(0.6)
    if not await choose_sample(cdp, sample):
        raise RuntimeError("sample selector not found")
    ev = await wait_evidence(cdp, sid, cp, before)
    print(f"{cp} <- {sample}: {ev['verdict']} ({ev['confidence']}) {ev['reason'][:90]}")
    return ev


async def main() -> None:
    async with CDP() as cdp:
        print("title:", await cdp.eval("document.title"))
        sid = await cdp.eval(
            """(async () => {
              const r = await fetch('/api/sessions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                  store_name: '老张牛肉面（演示店）',
                  checklist_id: 'restaurant_closing',
                  operator: '店员小王'
                })
              });
              const s = await r.json();
              location.href = '/session/' + s.id;
              return s.id;
            })()"""
        )
        print("session:", sid)
        await asyncio.sleep(2)
        await click_text(cdp, "燃气总阀")
        adb_shot("android_01_session.png")

        # 1) gas valve: fail (open flame) -> re-check pass -> human confirm.
        ev = await capture(cdp, sid, "gas_valve", "/samples/gas_stove_flame.jpg")
        assert ev["verdict"] == "fail", ev
        adb_shot("android_02_gas_fail.png")
        ev = await capture(cdp, sid, "gas_valve", "/samples/gas_valve_closed.jpg")
        assert ev["verdict"] == "pass", ev
        await confirm(cdp, sid, "gas_valve")
        adb_shot("android_03_gas_pass.png")

        # 2) power panel: model may be unsure; human confirmation is required.
        ev = await capture(cdp, sid, "power_panel", "/samples/power_panel_off.jpg")
        assert ev["verdict"] in {"pass", "unsure"}, ev
        await confirm(cdp, sid, "power_panel", "演示：人工确认总闸已断开")
        adb_shot("android_04_panel.png")

        # 3) door lock: fail (open padlock) -> pass (locked) -> confirm.
        ev = await capture(cdp, sid, "door_lock", "/samples/door_unlocked.jpg")
        assert ev["verdict"] == "fail", ev
        ev = await capture(cdp, sid, "door_lock", "/samples/door_locked.jpg")
        assert ev["verdict"] == "pass", ev
        await confirm(cdp, sid, "door_lock")
        adb_shot("android_05_door.png")

        # 4) meter OCR.
        ev = await capture(cdp, sid, "gas_meter", "/samples/gas_meter_card.jpg")
        assert ev["verdict"] == "pass", ev
        adb_shot("android_06_meter.png")

        # 5) complete + verify.
        result = await cdp.eval(f"fetch('/api/sessions/{sid}/complete', {{method:'POST'}}).then(async r => ({{status:r.status, body: await r.json()}}))")
        print("complete:", result["status"])
        assert result["status"] == 200, result
        await cdp.eval(f"location.href='/report/{sid}'")
        await asyncio.sleep(2)
        adb_shot("android_07_report.png")
        verify = await cdp.eval(f"fetch('/api/verify/{sid}').then(r=>r.json())")
        print("verify:", json.dumps(verify, ensure_ascii=False))
        assert verify["valid"] is True
        print("ANDROID_E2E_OK", sid)


if __name__ == "__main__":
    asyncio.run(main())
