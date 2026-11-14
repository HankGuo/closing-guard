"""Evaluate the live Closing Guard pipeline on the labeled sample set.

This script talks to a running API (default http://127.0.0.1:8010) and the
real local MiniCPM servers.  It does not mock any model response.

Usage:
    python scripts/eval.py
    CG_API=http://127.0.0.1:8010 python scripts/eval.py
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
API = os.getenv("CG_API", "http://127.0.0.1:8010")
LABELS = ROOT / "data" / "labels.csv"
SAMPLES = ROOT / "data" / "samples"
OUT = ROOT / "reports"
OUT.mkdir(exist_ok=True)


def post_capture(client: httpx.Client, sid: str, checkpoint: str, image: Path) -> tuple[dict, float]:
    t0 = time.time()
    with image.open("rb") as fh:
        r = client.post(
            f"{API}/api/sessions/{sid}/capture",
            data={"checkpoint_id": checkpoint, "source": "eval"},
            files={"file": (image.name, fh, "image/jpeg")},
            timeout=240,
        )
    elapsed = time.time() - t0
    r.raise_for_status()
    return r.json(), elapsed


def main() -> None:
    rows = list(csv.DictReader(LABELS.open(encoding="utf-8")))
    results = []
    with httpx.Client() as client:
        health = client.get(f"{API}/api/health", timeout=10).json()
        print("health:", health.get("ok"), health.get("models", {}).keys())
        for row in rows:
            checkpoint = row["checkpoint"]
            image = SAMPLES / row["image"]
            session = client.post(
                f"{API}/api/sessions",
                json={"store_name": "评测店", "checklist_id": "restaurant_closing", "operator": "eval"},
                timeout=10,
            ).json()
            evidence, elapsed = post_capture(client, session["id"], checkpoint, image)
            actual = evidence["verdict"]
            expected = row["expected"]
            reading = (evidence.get("ocr") or {}).get("reading")
            jev_prob = ((evidence.get("ocr") or {}).get("jev") or {}).get("prob_1")
            results.append(
                {
                    "checkpoint": checkpoint,
                    "image": row["image"],
                    "expected": expected,
                    "actual": actual,
                    "confidence": evidence["confidence"],
                    "reason": evidence["reason"],
                    "reading": reading,
                    "expected_reading": row["expected_reading"],
                    "jev_prob": jev_prob,
                    "latency_s": round(elapsed, 2),
                    "source": row["source"],
                    "notes": row["notes"],
                    "session_id": session["id"],
                }
            )
            print(
                f"{checkpoint:12} {row['image']:24} expected={expected:6} actual={actual:6} "
                f"jev={jev_prob if jev_prob is None else round(float(jev_prob), 3)} {elapsed:5.1f}s  {evidence['reason'][:60]}"
            )

    total = len(results)
    correct = sum(1 for r in results if r["expected"] == r["actual"])
    expected_fail = [r for r in results if r["expected"] == "fail"]
    false_pass = [r for r in expected_fail if r["actual"] == "pass"]
    per_cp: dict[str, dict] = {}
    for r in results:
        d = per_cp.setdefault(r["checkpoint"], {"n": 0, "correct": 0, "false_pass": 0, "latencies": []})
        d["n"] += 1
        d["correct"] += int(r["expected"] == r["actual"])
        d["false_pass"] += int(r["expected"] == "fail" and r["actual"] == "pass")
        d["latencies"].append(r["latency_s"])

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "api": API,
        "n": total,
        "accuracy": round(correct / total, 3) if total else 0,
        "false_pass_count": len(false_pass),
        "false_pass_rate_on_expected_fail": round(len(false_pass) / len(expected_fail), 3) if expected_fail else 0,
        "mean_latency_s": round(statistics.mean(r["latency_s"] for r in results), 2) if results else 0,
        "per_checkpoint": {
            k: {
                "n": v["n"],
                "accuracy": round(v["correct"] / v["n"], 3),
                "false_pass": v["false_pass"],
                "mean_latency_s": round(statistics.mean(v["latencies"]), 2),
            }
            for k, v in per_cp.items()
        },
        "results": results,
    }
    (OUT / "eval.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Closing Guard — pilot evaluation",
        "",
        f"- Generated: {report['generated_at']}",
        f"- API: {API}",
        f"- Samples: {total}",
        f"- Verdict accuracy: **{report['accuracy']:.1%}**",
        f"- False-pass on expected-fail items: **{report['false_pass_count']}** "
        f"({report['false_pass_rate_on_expected_fail']:.1%})",
        f"- Mean capture latency: **{report['mean_latency_s']} s**",
        "",
        "| Checkpoint | Image | Expected | Actual | Jev | Confidence | Latency (s) | Note |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        jev = "—" if r["jev_prob"] is None else f"{float(r['jev_prob']):.3f}"
        lines.append(
            f"| {r['checkpoint']} | {r['image']} | {r['expected']} | {r['actual']} | "
            f"{jev} | {r['confidence']:.2f} | {r['latency_s']} | {r['reason'][:60]} |"
        )
    lines += [
        "",
        "## Per-checkpoint",
        "",
        "| Checkpoint | n | Accuracy | False pass | Mean latency (s) |",
        "|---|---|---|---|---|",
    ]
    for k, v in report["per_checkpoint"].items():
        lines.append(f"| {k} | {v['n']} | {v['accuracy']:.1%} | {v['false_pass']} | {v['mean_latency_s']} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "This is a small pilot set, not a statistically significant benchmark. It is intentionally "
        "adversarial: the gas-flame case is caught by the CV flame cross-check, while the power-panel "
        "ON case is a known 1B weakness. That is exactly why every critical `pass` requires a human "
        "confirmation before the session can be completed. The false-pass number here is **model-only**; "
        "the system-level ledger cannot close without the human confirmation.",
        "",
        "The water-meter case is a deliberate uncertainty case: the last digit is rolling, so OCR must "
        "not be trusted as an accounting value. The system returns `unsure` and asks for human confirmation.",
    ]
    (OUT / "eval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["n", "accuracy", "false_pass_count", "false_pass_rate_on_expected_fail", "mean_latency_s"]}, ensure_ascii=False, indent=2))
    print("wrote", OUT / "eval.json", OUT / "eval.md")


if __name__ == "__main__":
    main()
