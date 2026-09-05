"""AuditRecord — one immutable row per /analyze decision (Phase 4, §11).

Kept out of the frozen schemas/models.py (§13) because this is a new Phase 4
type, not part of the §6/§7 wire contracts. It flattens the four AnalyzeResponse
objects into a single, queryable audit row.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas import (
    Decision,
    RiskScore,
    VerificationResult,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditRecord(BaseModel):
    """A flat, persisted summary of one analysis outcome.

    `id` is assigned by the store on insert (None until then). Everything else is
    derived from the AnalyzeResponse so the trail is self-contained.
    """

    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=_utcnow)

    device_id: str
    content_id: Optional[str] = None

    # Track A — content integrity (None when no content_update was supplied).
    verified_match: Optional[bool] = None
    verification_action: Optional[str] = None

    # Track B + fusion — risk (None when nothing produced a score).
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None

    # The final call the engine made.
    decision: str
    recommended_action: str
    reasons: list[str] = Field(default_factory=list)

    event_count: int = 0

    @classmethod
    def from_analysis(
        cls,
        *,
        device_id: str,
        verification: VerificationResult | None,
        risk: RiskScore | None,
        decision: Decision,
        content_id: str | None = None,
        event_count: int = 0,
    ) -> "AuditRecord":
        """Build an AuditRecord from the pieces /analyze already computed."""
        return cls(
            device_id=device_id,
            content_id=content_id,
            verified_match=None if verification is None else verification.match,
            verification_action=None if verification is None else verification.action,
            risk_score=None if risk is None else risk.score,
            risk_level=None if risk is None else risk.level.value,
            decision=decision.decision,
            recommended_action=decision.recommended_action.value,
            reasons=list(decision.reasons),
            event_count=event_count,
        )
