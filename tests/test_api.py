"""API tests for /authorize and the /analyze contract (§7)."""
from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

AUTHENTIC = b"Platform 2: Train to Central departs 10:45."
TAMPERED = b"Platform 2: FREE WIFI click http://evil.example to claim."


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_authorize_then_analyze_match_renders():
    client.post(
        "/authorize",
        json={"content_id": "CNT-100", "content_bytes_b64": _b64(AUTHENTIC)},
    )
    r = client.post(
        "/analyze",
        json={
            "device_id": "SG-RNP-001",
            "content_update": {
                "device_id": "SG-RNP-001",
                "content_id": "CNT-100",
                "content_bytes_b64": _b64(AUTHENTIC),
                "source": "usb",
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    # Contract shape (§7): all four keys always present.
    assert set(body) == {
        "device_id",
        "verification_result",
        "risk_score",
        "xai_explanation",
        "decision",
    }
    assert body["verification_result"]["match"] is True
    assert body["decision"]["decision"] == "render"


def test_analyze_populates_xai_from_events():
    r = client.post(
        "/analyze",
        json={
            "device_id": "SG-RNP-006",
            "events": [
                {"device_id": "SG-RNP-006", "event_type": "unauthorized_usb",
                 "authorized": False, "timestamp": "2026-08-21T10:25:05Z", "data": {}},
                {"device_id": "SG-RNP-006", "event_type": "content_hash_mismatch",
                 "authorized": False, "timestamp": "2026-08-21T10:25:06Z", "data": {}},
            ],
        },
    )
    assert r.status_code == 200
    xai = r.json()["xai_explanation"]
    assert xai is not None
    assert xai["explains"] == "ai_threat_assessment"
    assert len(xai["top_factors"]) >= 1
    assert "impact" in xai["top_factors"][0]


def test_analyze_mismatch_blocks():
    client.post(
        "/authorize",
        json={"content_id": "CNT-101", "content_bytes_b64": _b64(AUTHENTIC)},
    )
    r = client.post(
        "/analyze",
        json={
            "device_id": "SG-RNP-001",
            "content_update": {
                "device_id": "SG-RNP-001",
                "content_id": "CNT-101",
                "content_bytes_b64": _b64(TAMPERED),
                "source": "usb",
            },
        },
    )
    body = r.json()
    assert body["verification_result"]["match"] is False
    assert body["decision"]["decision"] == "block"
    assert body["decision"]["recommended_action"] == "safe_fallback"
