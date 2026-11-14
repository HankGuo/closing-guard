from app.agent import _chain_hash, _chain_payload


def record():
    return {
        "id": "ev_1",
        "session_id": "ses_1",
        "checkpoint_id": "gas_valve",
        "image_sha256": "a" * 64,
        "captured_at": "2026-11-14T00:00:00+00:00",
        "source": "sample",
        "verdict": "pass",
        "confidence": 0.8,
        "reason": "test",
    }


def test_chain_is_deterministic():
    payload = _chain_payload(record())
    assert _chain_hash("seed", payload) == _chain_hash("seed", payload)


def test_chain_depends_on_previous_hash():
    payload = _chain_payload(record())
    assert _chain_hash("seed-a", payload) != _chain_hash("seed-b", payload)


def test_chain_depends_on_payload():
    payload = _chain_payload(record())
    changed = dict(payload)
    changed["verdict"] = "fail"
    assert _chain_hash("seed", payload) != _chain_hash("seed", changed)
