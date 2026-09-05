"""Phase 4 — audit trail tests: the AuditStore and the /audit endpoint (§11)."""
from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from app.audit import AuditRecord, AuditStore
from app.deps import audit_store
from app.main import app
from app.schemas import Decision, RiskLevel, RiskScore, VerificationResult

client = TestClient(app)

AUTHENTIC = b"Platform 2: Train to Central departs 10:45."
TAMPERED = b"Platform 2: FREE WIFI click http://evil.example to claim."


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _sample_record(device_id: str = "SG-RNP-900", decision: str = "block") -> AuditRecord:
    return AuditRecord.from_analysis(
        device_id=device_id,
        verification=VerificationResult(
            content_id="CNT-X",
            computed_hash="a" * 64,
            authorized_hash="b" * 64,
            match=False,
            action="block",
        ),
        risk=RiskScore(device_id=device_id, score=71, level=RiskLevel.high),
        decision=Decision(
            device_id=device_id,
            decision=decision,
            recommended_action="safe_fallback",
            reasons=["hash_mismatch"],
        ),
        content_id="CNT-X",
        event_count=2,
    )


# --------------------------------------------------------------------------- #
# AuditStore unit behaviour
# --------------------------------------------------------------------------- #
def test_store_assigns_id_and_roundtrips_fields():
    store = AuditStore(":memory:")
    saved = store.record(_sample_record())
    assert saved.id == 1

    (got,) = store.list()
    assert got.device_id == "SG-RNP-900"
    assert got.verified_match is False
    assert got.verification_action == "block"
    assert got.risk_score == 71
    assert got.risk_level == "high"
    assert got.decision == "block"
    assert got.recommended_action == "safe_fallback"
    assert got.reasons == ["hash_mismatch"]
    assert got.event_count == 2


def test_store_is_append_only_and_newest_first():
    store = AuditStore(":memory:")
    store.record(_sample_record(decision="render"))
    store.record(_sample_record(decision="block"))
    store.record(_sample_record(decision="isolate"))
    assert store.count() == 3
    rows = store.list()
    # Newest first.
    assert [r.decision for r in rows] == ["isolate", "block", "render"]
    # Monotonic, unique ids — nothing overwritten.
    assert [r.id for r in rows] == [3, 2, 1]


def test_store_filters_by_device_and_limit():
    store = AuditStore(":memory:")
    store.record(_sample_record(device_id="SG-A"))
    store.record(_sample_record(device_id="SG-B"))
    store.record(_sample_record(device_id="SG-A"))
    assert len(store.list(device_id="SG-A")) == 2
    assert len(store.list(device_id="SG-B")) == 1
    assert len(store.list(limit=1)) == 1


def test_record_handles_null_tracks():
    """A pure events-only analysis has no verification — nulls must persist."""
    store = AuditStore(":memory:")
    rec = AuditRecord.from_analysis(
        device_id="SG-C",
        verification=None,
        risk=None,
        decision=Decision(
            device_id="SG-C",
            decision="render",
            recommended_action="render",
            reasons=[],
        ),
    )
    store.record(rec)
    (got,) = store.list()
    assert got.verified_match is None
    assert got.verification_action is None
    assert got.risk_score is None
    assert got.risk_level is None
    assert got.decision == "render"


# --------------------------------------------------------------------------- #
# End-to-end: /analyze writes the trail, /audit reads it
# --------------------------------------------------------------------------- #
def test_analyze_writes_audit_row_that_audit_endpoint_returns():
    before = audit_store.count()

    client.post(
        "/authorize",
        json={"content_id": "CNT-AUD", "content_bytes_b64": _b64(AUTHENTIC)},
    )
    client.post(
        "/analyze",
        json={
            "device_id": "SG-AUDIT-1",
            "content_update": {
                "device_id": "SG-AUDIT-1",
                "content_id": "CNT-AUD",
                "content_bytes_b64": _b64(TAMPERED),
                "source": "usb",
            },
        },
    )

    assert audit_store.count() == before + 1

    r = client.get("/audit", params={"device_id": "SG-AUDIT-1"})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["device_id"] == "SG-AUDIT-1"
    assert row["content_id"] == "CNT-AUD"
    assert row["verified_match"] is False
    assert row["decision"] == "block"
    assert row["recommended_action"] == "safe_fallback"
    assert row["id"] is not None
