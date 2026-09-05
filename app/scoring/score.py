"""Risk fusion — CLAUDE.md §9 (§11 scoring).

Combines three sources into a single 0..100 risk score:
  * the deterministic hash result  (content_hash_mismatch)
  * rule signals from recent events (unauthorized_usb, default creds, wireless)
  * the AI anomaly assessment       (ai_anomaly, scaled)

This does NOT decide content integrity — a hash mismatch already blocks upstream
(§2). Risk refines what happens around a MATCH and drives isolate/escalate.
"""
from __future__ import annotations

from app.schemas import (
    AnomalyResult,
    EventType,
    RiskLevel,
    RiskScore,
    SecurityEvent,
    VerificationResult,
)

# Frozen default weights (§9).
WEIGHTS = {
    "content_hash_mismatch": 40,
    "unauthorized_usb": 20,
    "default_credential_attempt": 15,
    "wireless_anomaly": 10,
    "ai_anomaly": 15,  # scaled by anomaly_score
}

# Score -> level thresholds (aligned with the decision engine).
_LOW_MAX = 24
_MEDIUM_MAX = 49
_HIGH_MAX = 79  # >= 80 is critical


def _level(score: int) -> RiskLevel:
    if score <= _LOW_MAX:
        return RiskLevel.low
    if score <= _MEDIUM_MAX:
        return RiskLevel.medium
    if score <= _HIGH_MAX:
        return RiskLevel.high
    return RiskLevel.critical


def compute_risk(
    device_id: str,
    verification: VerificationResult | None = None,
    events: list[SecurityEvent] | None = None,
    anomaly: AnomalyResult | None = None,
) -> RiskScore:
    events = events or []
    types = {e.event_type for e in events}
    breakdown: dict[str, int] = {}

    # --- Hash result (deterministic) -----------------------------------------
    if verification is not None and not verification.match:
        breakdown["content_hash_mismatch"] = WEIGHTS["content_hash_mismatch"]

    # --- Rule signals from recent events -------------------------------------
    if EventType.unauthorized_usb in types:
        breakdown["unauthorized_usb"] = WEIGHTS["unauthorized_usb"]
    if EventType.default_credential_attempt in types:
        breakdown["default_credential_attempt"] = WEIGHTS["default_credential_attempt"]
    if EventType.unauthorized_wireless in types:
        breakdown["wireless_anomaly"] = WEIGHTS["wireless_anomaly"]

    # --- AI anomaly (scaled) -------------------------------------------------
    if anomaly is not None and anomaly.anomaly_score > 0:
        ai_points = round(WEIGHTS["ai_anomaly"] * anomaly.anomaly_score)
        if ai_points > 0:
            breakdown["ai_anomaly"] = ai_points

    score = min(sum(breakdown.values()), 100)

    return RiskScore(
        device_id=device_id,
        score=score,
        level=_level(score),
        breakdown=breakdown,
    )
