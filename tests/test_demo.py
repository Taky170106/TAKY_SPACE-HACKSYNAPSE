"""Tests for the demo layer: scenarios, dashboard, and the trigger endpoint."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.demo_scenarios import ORDER, SCENARIOS
from app.main import app

client = TestClient(app)


def test_scenarios_build_fresh_events_and_content():
    usb = SCENARIOS["usb"]
    events, content = usb.build()
    assert [e.event_type.value for e in events] == [
        "unauthorized_usb",
        "content_received",
        "content_hash_mismatch",
    ]
    assert content is not None
    assert content.content_id == "CNT-101"
    # Tampered content carries the attacker's message.
    import base64
    assert base64.b64decode(content.content_bytes_b64) == usb.attacker_message.encode()

    # Credential attack now uploads tampered content too (defense in depth).
    _, cred_content = SCENARIOS["credential"].build()
    assert cred_content is not None


def test_dashboard_page_serves():
    r = client.get("/")
    assert r.status_code == 200
    assert "SignGuard AI" in r.text
    assert "/ws" in r.text  # wires up the live socket


def test_scenarios_endpoint_lists_buttons_in_order():
    r = client.get("/demo/scenarios")
    assert r.status_code == 200
    body = r.json()
    # Credential is a manual attack, so it is not a scenario button.
    assert [s["id"] for s in body] == ORDER
    assert len(body) == 3
    assert "credential" not in [s["id"] for s in body]
    usb = next(s for s in body if s["id"] == "usb")
    assert usb["device_id"] == "SG-RNP-001"
    assert usb["tampered"] is True


def test_authorize_content_and_baseline_renders_on_and_off():
    # Presenter chooses the "before" (authorized) content.
    r = client.post("/demo/authorize-content", json={"content": "MY ROUTE 42\nNext: 09:15"})
    assert r.status_code == 200
    assert r.json()["authentic_text"].startswith("MY ROUTE 42")

    # Baseline is not an attack -> it renders whether SignGuard is ON or OFF.
    on = client.post("/demo/attack/baseline", json={"protected": True})
    off = client.post("/demo/attack/baseline", json={"protected": False})
    assert on.json()["decision"] == "render"
    assert off.json()["decision"] == "render"


def test_manual_default_credentials_are_flagged_and_content_blocked():
    # Step 1: log in with default creds -> granted but flagged.
    r = client.post("/demo/login", json={"user": "admin", "password": "admin"})
    body = r.json()
    assert body["granted"] is True
    assert body["flag"] == "default"

    # Step 2: push malicious content with SignGuard on -> blocked.
    r = client.post("/demo/publish", json={"content": "NEXT BUS CANCELLED", "protected": True})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "block"
    assert body["credential_flag"] == "default"


def test_manual_valid_operator_can_publish_authorized_content():
    import base64
    from app.demo_scenarios import AUTHENTIC_TEXT, BASELINE_CONTENT_ID

    # The transport authority authorizes the genuine content (done at startup live).
    client.post(
        "/authorize",
        json={
            "content_id": BASELINE_CONTENT_ID,
            "content_bytes_b64": base64.b64encode(AUTHENTIC_TEXT.encode()).decode(),
        },
    )
    client.post("/demo/login", json={"user": "operator", "password": "transit2026"})
    r = client.post("/demo/publish", json={"content": AUTHENTIC_TEXT, "protected": True})
    assert r.json()["decision"] == "render"


def test_manual_publish_requires_login():
    # A fresh invalid login leaves no granted session.
    client.post("/demo/login", json={"user": "mallory", "password": "wrongpass"})
    r = client.post("/demo/publish", json={"content": "hi", "protected": True})
    assert r.status_code == 403


def test_trigger_unknown_scenario_404():
    r = client.post("/demo/attack/does-not-exist")
    assert r.status_code == 404


def test_trigger_without_signguard_shows_attacker_content():
    """protected=false -> attacker succeeds, no block, no hardware needed."""
    r = client.post("/demo/attack/usb", json={"protected": False})
    assert r.status_code == 200
    body = r.json()
    assert body["protected"] is False
    assert body["decision"] == "displayed"
    assert body["hardware_notified"] is False


def test_trigger_with_signguard_blocks_and_works_without_broker():
    """protected=true runs in-process (reliable) even with no broker connected."""
    r = client.post("/demo/attack/usb", json={"protected": True})
    assert r.status_code == 200
    body = r.json()
    assert body["protected"] is True
    assert body["decision"] == "block"
    assert body["risk"] > 0
    # No broker in tests -> hardware simply isn't notified (webpage still works).
    assert body["hardware_notified"] is False


def test_trigger_with_custom_tampered_content():
    """A custom content override is what the tampered update tries to display."""
    r = client.post(
        "/demo/attack/usb", json={"protected": False, "content": "PLATFORM CHANGED TO 9"}
    )
    assert r.status_code == 200
    # WITHOUT SignGuard, the attacker's chosen content is shown on the display.
    # (Broadcast payload carries it; here we just assert the call succeeded.)
    assert r.json()["decision"] == "displayed"
