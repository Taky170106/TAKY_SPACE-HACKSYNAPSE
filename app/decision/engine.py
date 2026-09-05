"""Decision engine — CLAUDE.md §9.

The ONE invariant (§2): a hash MISMATCH is blocked immediately and never waits
for the ML model. Risk only refines what happens when the hash MATCHES.

Rules:
  IF hash == MISMATCH            -> BLOCK + SAFE_FALLBACK  (do NOT wait for ML)
  IF hash == MATCH, risk < thr   -> RENDER
  IF risk >= critical_threshold  -> ISOLATE + ESCALATE
  (unauthorized_usb / repeated attacks raise risk upstream in scoring)
"""
from __future__ import annotations

from app.schemas import CommandType, Decision, RiskScore, VerificationResult

RISK_THRESHOLD = 50       # MATCH + risk below this -> render
CRITICAL_THRESHOLD = 80   # risk at/above this -> isolate + escalate


def decide(
    device_id: str,
    verification: VerificationResult | None,
    risk: RiskScore | None = None,
) -> Decision:
    """Fuse the deterministic hash result with (optional) risk into a command."""
    reasons: list[str] = []

    # --- Track A gate: hash mismatch is terminal, ML is irrelevant here. ------
    if verification is not None and not verification.match:
        reasons.append("hash_mismatch")
        if verification.authorized_hash is None:
            reasons.append("unknown_content")
        return Decision(
            device_id=device_id,
            decision="block",
            recommended_action=CommandType.safe_fallback,
            reasons=reasons,
        )

    score = risk.score if risk is not None else 0

    # --- Critical risk -> isolate the update channel + escalate. -------------
    if score >= CRITICAL_THRESHOLD:
        reasons.append("critical_risk")
        return Decision(
            device_id=device_id,
            decision="isolate",
            recommended_action=CommandType.isolate,
            reasons=reasons,
        )

    # --- Elevated (but not critical) risk on matched content -> block. --------
    if score >= RISK_THRESHOLD:
        reasons.append("elevated_risk")
        return Decision(
            device_id=device_id,
            decision="block",
            recommended_action=CommandType.safe_fallback,
            reasons=reasons,
        )

    # --- Verified content, acceptable risk -> render. ------------------------
    if verification is not None and verification.match:
        reasons.append("hash_match")
    reasons.append("risk_acceptable")
    return Decision(
        device_id=device_id,
        decision="render",
        recommended_action=CommandType.render,
        reasons=reasons,
    )
