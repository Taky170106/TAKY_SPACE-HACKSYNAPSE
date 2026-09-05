"""Windowed feature engineering (§11 features) → feature_vector (§6).

Turns a device's recent event history into the exact seven features the model
consumes. FEATURE_ORDER is the single source of truth for column order — the ML
engine and SHAP explainer both import it so vectors never get misaligned.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.ingestion.store import EventStore
from app.schemas import EventType, FeatureVector

# FROZEN order of the §6 feature_vector.features keys.
FEATURE_ORDER: tuple[str, ...] = (
    "failed_logins_5min",
    "unknown_usb_detected",
    "wireless_anomaly",
    "content_hash_mismatch",
    "events_per_minute",
    "time_since_authorized_update",
    "device_trust_score",
)

WINDOW_SECONDS = 300  # "5min"
# Cap for time_since_authorized_update when a device has no authorized update on record.
_NO_UPDATE_SECONDS = 86_400  # 24h

# Trust penalties per suspicious event in the window (device_trust_score starts at 1.0).
_TRUST_PENALTY = {
    EventType.login_failure: 0.05,
    EventType.default_credential_attempt: 0.15,
    EventType.unauthorized_usb: 0.20,
    EventType.unauthorized_wireless: 0.15,
    EventType.content_hash_mismatch: 0.30,
    EventType.display_tamper: 0.25,
}


def build_feature_vector(
    store: EventStore,
    device_id: str,
    now: datetime | None = None,
    window_seconds: int = WINDOW_SECONDS,
) -> FeatureVector:
    now = now or datetime.now(timezone.utc)
    events = store.recent(device_id, window_seconds, now=now)

    def count(et: EventType) -> int:
        return sum(1 for e in events if e.event_type == et)

    failed_logins = count(EventType.login_failure)
    unknown_usb = 1 if count(EventType.unauthorized_usb) else 0
    wireless_anomaly = 1 if count(EventType.unauthorized_wireless) else 0
    hash_mismatch = 1 if count(EventType.content_hash_mismatch) else 0

    window_minutes = max(window_seconds / 60.0, 1e-9)
    events_per_minute = round(len(events) / window_minutes, 3)

    last_update = store.last_authorized_update(device_id, now=now)
    if last_update is None:
        time_since_update = float(_NO_UPDATE_SECONDS)
    else:
        time_since_update = max((now - last_update).total_seconds(), 0.0)

    trust = 1.0
    for e in events:
        trust -= _TRUST_PENALTY.get(e.event_type, 0.0)
    device_trust_score = round(min(max(trust, 0.0), 1.0), 3)

    features = {
        "failed_logins_5min": float(failed_logins),
        "unknown_usb_detected": float(unknown_usb),
        "wireless_anomaly": float(wireless_anomaly),
        "content_hash_mismatch": float(hash_mismatch),
        "events_per_minute": float(events_per_minute),
        "time_since_authorized_update": float(time_since_update),
        "device_trust_score": float(device_trust_score),
    }
    return FeatureVector(device_id=device_id, window="5min", features=features)


def to_row(fv: FeatureVector) -> list[float]:
    """Feature vector -> model input row in FEATURE_ORDER."""
    return [float(fv.features.get(name, 0.0)) for name in FEATURE_ORDER]
