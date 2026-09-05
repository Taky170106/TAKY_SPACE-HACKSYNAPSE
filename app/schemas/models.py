"""Frozen data schemas — CLAUDE.md §6 / §7.

These Pydantic models are the seams between the three components. Do NOT add or
rename fields without human approval (CLAUDE.md §13).
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Enumerations (FROZEN vocabularies)
# --------------------------------------------------------------------------- #
class EventType(str, Enum):
    """Allowed security_event.event_type values — CLAUDE.md §6."""

    content_received = "content_received"
    content_hash_match = "content_hash_match"
    content_hash_mismatch = "content_hash_mismatch"
    usb_connected = "usb_connected"
    unauthorized_usb = "unauthorized_usb"
    wireless_activity = "wireless_activity"
    unauthorized_wireless = "unauthorized_wireless"
    login_success = "login_success"
    login_failure = "login_failure"
    default_credential_attempt = "default_credential_attempt"
    display_tamper = "display_tamper"
    safe_fallback_activated = "safe_fallback_activated"


class CommandType(str, Enum):
    """Allowed command values — CLAUDE.md §6."""

    render = "render"
    safe_fallback = "safe_fallback"
    isolate = "isolate"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# --------------------------------------------------------------------------- #
# Edge → Layer 2 messages
# --------------------------------------------------------------------------- #
class SecurityEvent(BaseModel):
    """topic: signguard/events"""

    device_id: str
    event_type: EventType
    authorized: bool = False
    timestamp: datetime = Field(default_factory=_utcnow)
    data: dict[str, Any] = Field(default_factory=dict)


class ContentUpdate(BaseModel):
    """topic: signguard/content"""

    device_id: str
    content_id: str
    content_bytes_b64: str
    source: str = "usb"
    timestamp: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Layer 2 internal objects
# --------------------------------------------------------------------------- #
class ContentRecord(BaseModel):
    """Created at authorization time, stored in HashRegistry."""

    content_id: str
    content_hash: str
    authorized_by: str = "transport_authority"
    timestamp: datetime = Field(default_factory=_utcnow)


class VerificationResult(BaseModel):
    content_id: str
    computed_hash: str
    authorized_hash: str | None
    match: bool
    action: Literal["render", "block"]


class FeatureVector(BaseModel):
    device_id: str
    window: str = "5min"
    features: dict[str, float] = Field(default_factory=dict)


class AnomalyResult(BaseModel):
    device_id: str
    anomaly_score: float
    is_anomaly: bool
    model: str = "isolation_forest"


class RiskScore(BaseModel):
    device_id: str
    score: int
    level: RiskLevel
    breakdown: dict[str, int] = Field(default_factory=dict)


class XaiFactor(BaseModel):
    name: str
    impact: float


class XaiExplanation(BaseModel):
    """Explains the AI assessment, NOT the hash comparison — CLAUDE.md §2."""

    device_id: str
    explains: Literal["ai_threat_assessment"] = "ai_threat_assessment"
    top_factors: list[XaiFactor] = Field(default_factory=list)


class Decision(BaseModel):
    device_id: str
    decision: Literal["render", "block", "isolate"]
    recommended_action: CommandType
    reasons: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Layer 2 → Edge message
# --------------------------------------------------------------------------- #
class Command(BaseModel):
    """topic: signguard/commands"""

    device_id: str
    command: CommandType
    timestamp: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# REST /analyze contract — CLAUDE.md §7 (FROZEN, consumed by Layer 1)
# --------------------------------------------------------------------------- #
class AnalyzeRequest(BaseModel):
    """Input to POST /analyze.

    A content_update triggers Track A (hash verification); recent events feed
    Track B (attack-context intelligence).
    """

    device_id: str
    content_update: ContentUpdate | None = None
    events: list[SecurityEvent] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    device_id: str
    verification_result: VerificationResult | None = None
    risk_score: RiskScore | None = None
    xai_explanation: XaiExplanation | None = None
    decision: Decision | None = None
