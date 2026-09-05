"""Live WebSocket plumbing + payload building for the dashboard."""
from __future__ import annotations

from typing import Any

from app.demo_scenarios import AUTHENTIC_TEXT, Scenario
from app.schemas import AnalyzeResponse

# Human labels for the risk breakdown bars (the deterministic "why").
_RISK_LABELS = {
    "content_hash_mismatch": "Hash mismatch",
    "unauthorized_usb": "Unauthorized USB",
    "default_credential_attempt": "Default credentials",
    "wireless_anomaly": "Wireless anomaly",
    "ai_anomaly": "AI anomaly (behaviour)",
}


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[Any] = set()

    async def connect(self, ws) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws) -> None:
        self.active.discard(ws)

    async def broadcast(self, message: dict) -> None:
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.active.discard(ws)


def _breakdown(result: AnalyzeResponse) -> list[dict]:
    if not result.risk_score:
        return []
    items = [
        {"label": _RISK_LABELS.get(k, k), "points": v}
        for k, v in result.risk_score.breakdown.items()
    ]
    return sorted(items, key=lambda x: x["points"], reverse=True)


def _timeline(blocked: bool) -> list[str]:
    if blocked:
        return [
            "Content received",
            "SHA-256 fingerprint computed",
            "Hash MISMATCH vs authorized",
            "Authorization FAILED",
            "Content BLOCKED",
            "Safe fallback activated",
            "Security incident recorded",
        ]
    return [
        "Content received",
        "SHA-256 fingerprint computed",
        "Hash MATCH — authorized",
        "Content rendered",
    ]


def build_decision_payload(
    device_id: str,
    result: AnalyzeResponse,
    scenario: Scenario | None,
    *,
    authentic_text: str | None = None,
    attacker_text: str | None = None,
) -> dict:
    """Protected outcome (SignGuard ON) for the dashboard."""
    decision = result.decision
    command = decision.recommended_action.value
    blocked = decision.decision != "render"
    risk = result.risk_score.score if result.risk_score else 0
    level = result.risk_score.level.value if result.risk_score else "low"

    xai = []
    if result.xai_explanation:
        xai = [
            {"name": f.name, "impact": round(f.impact, 3)}
            for f in result.xai_explanation.top_factors[:4]
        ]

    if attacker_text is None and scenario is not None:
        attacker_text = scenario.attacker_text

    return {
        "type": "decision",
        "protected": True,
        "mode": "blocked" if blocked else "render",
        "device_id": device_id,
        "scenario_id": scenario.id if scenario else None,
        "title": scenario.title if scenario else device_id,
        "icon": scenario.icon if scenario else "",
        "decision": decision.decision,
        "command": command,
        "risk": risk,
        "level": level,
        "reasons": decision.reasons,
        "breakdown": _breakdown(result),
        "xai": xai,
        "timeline": _timeline(blocked),
        "attacker_text": attacker_text,
        "authentic_text": authentic_text or AUTHENTIC_TEXT,
    }


def build_unprotected_payload(
    scenario: Scenario,
    *,
    authentic_text: str | None = None,
    attacker_text: str | None = None,
) -> dict:
    """WITHOUT SignGuard: no verification, the attacker's content is displayed."""
    return {
        "type": "decision",
        "protected": False,
        "mode": "unprotected",
        "device_id": scenario.device_id,
        "scenario_id": scenario.id,
        "title": scenario.title,
        "icon": scenario.icon,
        "decision": "displayed",
        "command": "render",
        "risk": 0,
        "level": "low",
        "reasons": ["no_integrity_check"],
        "breakdown": [],
        "xai": [],
        "timeline": [
            "Content received",
            "No integrity verification",
            "Content displayed (UNVERIFIED)",
        ],
        "attacker_text": attacker_text if attacker_text is not None else scenario.attacker_text,
        "authentic_text": authentic_text or AUTHENTIC_TEXT,
    }
