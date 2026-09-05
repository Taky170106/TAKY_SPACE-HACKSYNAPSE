"""Shared analysis pipeline — the single source of truth for one decision.

Both the REST endpoint (`POST /analyze`) and the MQTT orchestrator call
`run_analysis()` so the two transports can never diverge. This runs Track A
(deterministic hash verification, §2), Track B (Isolation Forest + SHAP), risk
fusion (§9), the decision engine, and writes the append-only audit record (§11).
"""
from __future__ import annotations

from app.audit import AuditRecord
from app.decision import decide
from app.deps import anomaly_model, audit_store, registry, shap_explainer
from app.features import build_feature_vector
from app.ingestion import EventStore
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.scoring import compute_risk
from app.verification import verify_content


def run_analysis(req: AnalyzeRequest) -> AnalyzeResponse:
    """Full picture for one device/situation, with the decision persisted."""
    # --- Track A: content integrity (never gated by ML, §2) ------------------
    verification = None
    if req.content_update is not None:
        verification = verify_content(registry, req.content_update)

    # --- Track B: attack-context intelligence over the supplied events -------
    anomaly = None
    xai_explanation = None
    if req.events:
        store = EventStore()
        store.add_many(req.events)
        now = max(e.timestamp for e in req.events)
        feature_vector = build_feature_vector(store, req.device_id, now=now)
        anomaly = anomaly_model.score(feature_vector)
        xai_explanation = shap_explainer.explain(feature_vector)

    # --- Convergence: fuse hash + rule signals + AI anomaly into risk (§9) ----
    risk = compute_risk(req.device_id, verification, req.events, anomaly)

    decision = decide(req.device_id, verification, risk=risk)

    # --- Phase 4: persist an immutable audit record of this outcome (§11) -----
    audit_store.record(
        AuditRecord.from_analysis(
            device_id=req.device_id,
            verification=verification,
            risk=risk,
            decision=decision,
            content_id=(
                req.content_update.content_id
                if req.content_update is not None
                else None
            ),
            event_count=len(req.events),
        )
    )

    return AnalyzeResponse(
        device_id=req.device_id,
        verification_result=verification,
        risk_score=risk,
        xai_explanation=xai_explanation,
        decision=decision,
    )
