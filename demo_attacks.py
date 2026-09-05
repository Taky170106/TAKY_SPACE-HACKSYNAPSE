"""SignGuard AI - panel demo of the attack types (terminal walkthrough).

Runs the REAL analysis pipeline in-process (no broker, no server needed), so it
is the reliable way to show the panel how the system reacts to each attack:

    0) Baseline healthy signage            -> RENDER
    1) Malicious USB (tampered content)    -> BLOCK  (Track A: hash mismatch)
    2) Credential brute-force (no content) -> AI/Track B raises + explains risk
    3) Rogue Wi-Fi (tampered content)      -> BLOCK  (Track A: hash mismatch)
    4) Physical tamper (tampered content)  -> BLOCK  (hash mismatch, top risk)

For each it prints: what the sensors saw, the decision, the risk score, WHY the
AI flagged it (SHAP), and what the signage screen shows. Finally it prints the
append-only audit trail.

    python demo_attacks.py
"""
from __future__ import annotations

import sys

# Windows consoles default to cp1252; force UTF-8 so box/arrow glyphs render.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - best-effort; ASCII fallback still readable
    pass

from app.authorization import authorize_content
from app.demo_scenarios import (
    AUTHENTIC,
    BASELINE_CONTENT_ID,
    SCENARIOS,
    TERMINAL_ORDER,
)
from app.deps import audit_store, registry
from app.pipeline import run_analysis
from app.schemas import AnalyzeRequest

# What the signage screen shows for each command.
SCREEN = {
    "render": "VERIFIED - showing the authorized content.",
    "safe_fallback": "SAFE FALLBACK - 'Official Service Information / update unavailable'.",
    "isolate": "ISOLATED - update channel locked + safe fallback shown.",
}


def _rule(char: str = "-") -> str:
    return char * 66


def run_scenario(scenario_id: str) -> None:
    scenario = SCENARIOS[scenario_id]
    events, content = scenario.build()
    sensors = ", ".join(sorted({e.event_type.value for e in events})) or "(none)"
    content_label = (
        "(no content update - pure intrusion attempt)"
        if not scenario.has_content
        else ("TAMPERED - attacker bytes" if scenario.tampered_content else "authentic")
    )

    req = AnalyzeRequest(
        device_id=scenario.device_id, content_update=content, events=events
    )
    res = run_analysis(req)

    decision = res.decision.decision
    action = res.decision.recommended_action.value
    risk = res.risk_score.score if res.risk_score else 0
    level = res.risk_score.level.value if res.risk_score else "low"

    print(_rule())
    print(f"  {scenario.icon}  {scenario.title}   [device {scenario.device_id}]")
    print(_rule())
    print(f"  vector  : {scenario.vector}")
    print(f"  sensors : {sensors}")
    print(f"  content : {content_label}")
    print(f"  -> DECISION : {decision.upper()}  ->  {action}")
    print(f"  -> RISK     : {risk}/100 ({level})   reasons: {', '.join(res.decision.reasons)}")
    if res.xai_explanation and res.xai_explanation.top_factors:
        factors = ", ".join(
            f"{f.name} {f.impact:+.2f}" for f in res.xai_explanation.top_factors[:3]
        )
        print(f"  -> WHY (AI) : {factors}")
    print(f"  -> SCREEN   : {SCREEN.get(action, action)}")
    print()


def main() -> None:
    # The transport authority authorizes the genuine content once.
    authorize_content(registry, BASELINE_CONTENT_ID, AUTHENTIC, "transport_authority")

    print()
    print("#" * 66)
    print("#" + "SignGuard AI - Live Attack Demo".center(64) + "#")
    print("#" * 66)
    print()

    for sid in TERMINAL_ORDER:
        run_scenario(sid)

    print("#" * 66)
    print("#" + "AUDIT TRAIL (append-only, newest first)".center(64) + "#")
    print("#" * 66)
    for r in audit_store.list(limit=10):
        vm = "-" if r.verified_match is None else ("MATCH" if r.verified_match else "MISMATCH")
        risk = str(r.risk_score) if r.risk_score is not None else "-"
        print(
            f"  #{r.id:<3} {r.device_id:<11} {r.decision:<8} "
            f"risk={risk:<4} hash={vm}"
        )
    print()


if __name__ == "__main__":
    sys.exit(main())
