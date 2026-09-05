"""Track B tests — ingestion, features, IsolationForest, SHAP (Phase 2)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.features import FEATURE_ORDER, build_feature_vector
from app.ingestion import EventStore, load_events_from_file
from app.ml_engine import AnomalyModel
from app.schemas import EventType, SecurityEvent
from app.xai import ShapExplainer

NOW = datetime(2026, 8, 21, 10, 0, 0, tzinfo=timezone.utc)


def _ev(device_id: str, et: EventType, offset_s: int, authorized: bool = False) -> SecurityEvent:
    return SecurityEvent(
        device_id=device_id,
        event_type=et,
        authorized=authorized,
        timestamp=NOW + timedelta(seconds=offset_s),
    )


# --------------------------------------------------------------------------- #
# Store / windowing
# --------------------------------------------------------------------------- #
def test_recent_excludes_future_and_old_events():
    store = EventStore()
    store.add(_ev("D1", EventType.login_failure, -600))  # 10 min ago (outside 5min)
    store.add(_ev("D1", EventType.login_failure, -60))   # inside
    store.add(_ev("D1", EventType.login_failure, +120))  # in the future vs `now`

    recent = store.recent("D1", 300, now=NOW)
    assert len(recent) == 1  # only the -60s event is within (now-300s, now]


def test_last_authorized_update_is_now_aware():
    store = EventStore()
    store.add(_ev("D1", EventType.content_hash_match, -120, authorized=True))
    store.add(_ev("D1", EventType.content_hash_match, +600, authorized=True))  # future
    # As of NOW, the future update must be ignored.
    assert store.last_authorized_update("D1", now=NOW) == NOW - timedelta(seconds=120)


# --------------------------------------------------------------------------- #
# Feature engineering
# --------------------------------------------------------------------------- #
def test_feature_vector_shape_and_counts():
    store = EventStore()
    for i in range(3):
        store.add(_ev("D1", EventType.login_failure, -10 * i))
    store.add(_ev("D1", EventType.unauthorized_usb, -5))
    store.add(_ev("D1", EventType.content_hash_mismatch, -3))

    fv = build_feature_vector(store, "D1", now=NOW)
    assert set(fv.features) == set(FEATURE_ORDER)
    assert fv.features["failed_logins_5min"] == 3.0
    assert fv.features["unknown_usb_detected"] == 1.0
    assert fv.features["content_hash_mismatch"] == 1.0
    # trust drops from penalties (3*0.05 + 0.20 usb + 0.30 mismatch)
    assert fv.features["device_trust_score"] < 1.0


# --------------------------------------------------------------------------- #
# Model + SHAP (train once, reuse across tests)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def model() -> AnomalyModel:
    return AnomalyModel()


@pytest.fixture(scope="module")
def explainer(model: AnomalyModel) -> ShapExplainer:
    return ShapExplainer(model)


def test_healthy_device_is_not_anomalous(model: AnomalyModel):
    store = EventStore()
    store.add(_ev("D1", EventType.content_hash_match, -30, authorized=True))
    fv = build_feature_vector(store, "D1", now=NOW)
    result = model.score(fv)
    assert result.is_anomaly is False
    assert result.anomaly_score < 0.5
    assert result.model == "isolation_forest"


def test_attack_device_is_anomalous(model: AnomalyModel):
    store = EventStore()
    store.add(_ev("D1", EventType.unauthorized_usb, -20))
    store.add(_ev("D1", EventType.content_hash_mismatch, -10))
    fv = build_feature_vector(store, "D1", now=NOW)
    result = model.score(fv)
    assert result.is_anomaly is True
    assert result.anomaly_score > 0.5


def test_shap_explains_attack_with_signed_factors(explainer: ShapExplainer):
    store = EventStore()
    store.add(_ev("D1", EventType.unauthorized_usb, -20))
    store.add(_ev("D1", EventType.content_hash_mismatch, -10))
    fv = build_feature_vector(store, "D1", now=NOW)

    ex = explainer.explain(fv, top_k=3)
    assert ex.explains == "ai_threat_assessment"
    assert 1 <= len(ex.top_factors) <= 3
    # ranked by |impact| descending
    impacts = [abs(f.impact) for f in ex.top_factors]
    assert impacts == sorted(impacts, reverse=True)
    # an attack signal should surface as pushing toward anomaly (positive impact)
    names = {f.name: f.impact for f in ex.top_factors}
    attack_signals = {"unknown_usb_detected", "content_hash_mismatch", "device_trust_score"}
    assert any(names.get(n, 0) > 0 for n in attack_signals)


def test_all_sample_attack_devices_flagged(model: AnomalyModel):
    """The known-attack devices in the sample data must all be flagged anomalous."""
    store = EventStore()
    load_events_from_file(store)
    checks = {
        "SG-RNP-003": datetime(2026, 8, 21, 10, 10, 4, tzinfo=timezone.utc),
        "SG-RNP-004": datetime(2026, 8, 21, 10, 15, 30, tzinfo=timezone.utc),
        "SG-RNP-005": datetime(2026, 8, 21, 10, 20, 40, tzinfo=timezone.utc),
        "SG-RNP-006": datetime(2026, 8, 21, 10, 25, 10, tzinfo=timezone.utc),
    }
    for dev, now in checks.items():
        fv = build_feature_vector(store, dev, now=now)
        assert model.score(fv).is_anomaly is True, f"{dev} should be anomalous"
