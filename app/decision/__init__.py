"""Decision engine — CLAUDE.md §9. Hash result gates everything (§2)."""
from app.decision.engine import CRITICAL_THRESHOLD, RISK_THRESHOLD, decide

__all__ = ["decide", "RISK_THRESHOLD", "CRITICAL_THRESHOLD"]
