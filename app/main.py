"""Layer 2 FastAPI app — API + live attack-demo dashboard.

  * Track A (content integrity): authorize -> verify -> decide (§2).
  * Track B (risk/XAI): Isolation Forest + SHAP, fused into risk (§9).
  * Phase 4: append-only audit trail (§11), exposed at GET /audit.
  * Demo layer: a web dashboard (GET /) + an in-process MQTT orchestrator that
    turns edge telemetry into commands, so the webpage display AND the ESP32
    hardware react to the same attack in real time.
"""
from __future__ import annotations

import asyncio
import base64
import os

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.audit import AuditRecord
from app.authorization import authorize_content
from app.demo_scenarios import (
    AUTHENTIC_TEXT,
    BASELINE_CONTENT_ID,
    MANUAL_DEVICE,
    MANUAL_HW_LABEL,
    ORDER,
    SCENARIOS,
    classify_credentials,
    login_events,
    manual_content,
    manual_scenario,
)
from app.deps import audit_store, registry
from app.fallback import safe_fallback_content
from app.orchestrator import Orchestrator, _authorize_baseline
from app.pipeline import run_analysis
from app.schemas import AnalyzeRequest, AnalyzeResponse, ContentUpdate, EventType, SecurityEvent
from app.web import dashboard, lab, signage
from app.web.live import (
    ConnectionManager,
    build_decision_payload,
    build_unprotected_payload,
)

app = FastAPI(
    title="SignGuard AI — Layer 2",
    version="0.1.0",
    description="Content-integrity verification + attack-context intelligence.",
)

# --------------------------------------------------------------------------- #
# Live demo wiring — orchestrator (MQTT brain) + WebSocket fan-out to browsers
# --------------------------------------------------------------------------- #
_MQTT_HOST = os.environ.get("SIGNGUARD_MQTT_HOST", "localhost")
_MQTT_PORT = int(os.environ.get("SIGNGUARD_MQTT_PORT", "1883"))

manager = ConnectionManager()
_demo: dict = {
    "orchestrator": None,
    "loop": None,
    "broker": False,
    "active": {},
    "authorized_content": AUTHENTIC_TEXT,  # the "before" content the authority blessed
}


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _content_update(text: str) -> ContentUpdate:
    return ContentUpdate(
        device_id=MANUAL_DEVICE,
        content_id=BASELINE_CONTENT_ID,
        content_bytes_b64=_b64(text),
        source="usb",
    )


def _on_analysis(device_id: str, result: AnalyzeResponse) -> None:
    """Orchestrator hook (runs on paho's thread) -> broadcast to browsers."""
    scenario = _demo["active"].get(device_id)
    payload = build_decision_payload(device_id, result, scenario)
    loop = _demo["loop"]
    if loop is not None:
        asyncio.run_coroutine_threadsafe(manager.broadcast(payload), loop)


@app.on_event("startup")
async def _start_orchestrator() -> None:
    _demo["loop"] = asyncio.get_running_loop()
    _authorize_baseline()
    orch = Orchestrator(host=_MQTT_HOST, port=_MQTT_PORT, on_analysis=_on_analysis)
    _demo["orchestrator"] = orch
    _demo["broker"] = orch.start_background()
    if _demo["broker"]:
        print("[main] orchestrator connected to broker — live demo ready")
    else:
        print("[main] broker unreachable — dashboard loads, live triggers disabled")


@app.on_event("shutdown")
async def _stop_orchestrator() -> None:
    orch = _demo["orchestrator"]
    if orch is not None:
        orch.stop()


# --------------------------------------------------------------------------- #
# Authorization endpoint (transport authority blesses content)
# --------------------------------------------------------------------------- #
class AuthorizeRequest(BaseModel):
    content_id: str
    content_bytes_b64: str
    authorized_by: str = "transport_authority"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "signguard-layer2"}


@app.post("/authorize")
def authorize(req: AuthorizeRequest) -> dict[str, str]:
    """Authorize content: hash its bytes and store the record in the registry."""
    try:
        content_bytes = base64.b64decode(req.content_bytes_b64, validate=True)
    except Exception as exc:  # noqa: BLE001 - surface bad base64 clearly
        raise HTTPException(status_code=400, detail=f"invalid base64: {exc}")

    record = authorize_content(
        registry, req.content_id, content_bytes, req.authorized_by
    )
    return {
        "content_id": record.content_id,
        "content_hash": record.content_hash,
        "authorized_by": record.authorized_by,
    }


# --------------------------------------------------------------------------- #
# /analyze — the FROZEN Layer 1 contract (§7)
# --------------------------------------------------------------------------- #
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """Full picture for one device/situation (§7 contract).

    Delegates to the shared `run_analysis` pipeline so the REST and MQTT paths
    can never diverge: Track A (deterministic hash verification, §2) runs first,
    Track B assesses attack context (Isolation Forest + SHAP), risk fuses them
    (§9), the decision engine calls it, and the outcome is written to the audit
    trail (§11).
    """
    return run_analysis(req)


@app.get("/fallback")
def fallback() -> dict[str, str]:
    """The trusted content the edge must show on a block (§10)."""
    return {"content": safe_fallback_content()}


@app.get("/audit", response_model=list[AuditRecord])
def audit(device_id: str | None = None, limit: int = 100) -> list[AuditRecord]:
    """The append-only audit trail: one record per /analyze decision (§11).

    Newest first. Optionally filter by `device_id`; `limit` caps the page size.
    """
    limit = max(1, min(limit, 1000))
    return audit_store.list(device_id=device_id, limit=limit)


@app.get("/chain")
def chain() -> list[dict]:
    """The on-chain authorization ledger (signed, hash-linked blocks)."""
    from dataclasses import asdict
    return [asdict(b) for b in registry.ledger.blocks()]


@app.get("/chain/verify")
def chain_verify() -> dict:
    """Recompute the whole chain: proves no authorization was tampered with."""
    ok, msg = registry.ledger.verify_chain()
    return {"valid": ok, "message": msg, "blocks": len(registry.ledger.blocks())}


# --------------------------------------------------------------------------- #
# Live demo — dashboard page, scenario catalog, attack trigger, WebSocket
# --------------------------------------------------------------------------- #
@app.get("/", response_class=HTMLResponse)
def dashboard_page() -> str:
    """The live attack-demo dashboard (presenter control)."""
    return dashboard.render()


@app.get("/signage", response_class=HTMLResponse)
def signage_page() -> str:
    """Full-screen passenger signage — project this on the big screen (press F11)."""
    return signage.render()


@app.get("/lab", response_class=HTMLResponse)
def lab_page() -> str:
    """Web hardware lab: virtual Raspberry Pi + USB upload + ESP-12E LCD."""
    return lab.render()


@app.get("/demo/scenarios")
def demo_scenarios() -> list[dict]:
    """Catalog of the baseline + attacks, in display order (drives the buttons)."""
    out = []
    for sid in ORDER:
        s = SCENARIOS[sid]
        out.append(
            {
                "id": s.id,
                "title": s.title,
                "device_id": s.device_id,
                "vector": s.vector,
                "icon": s.icon,
                "expected": s.expected,
                "event_types": [e[0].value for e in s.raw_events],
                "has_content": s.has_content,
                "tampered": s.tampered_content if s.has_content else None,
            }
        )
    return out


class AttackRequest(BaseModel):
    protected: bool = True
    content: str | None = None  # custom content the tampered update tries to show


@app.post("/demo/attack/{scenario_id}")
async def trigger_attack(
    scenario_id: str, req: AttackRequest = AttackRequest()
) -> dict:
    """Fire a scenario, WITHOUT (protected=false) or WITH (protected=true) SignGuard.

    Runs the real pipeline in-process for a reliable, instant dashboard update,
    and — when protected and the broker is up — also publishes the resulting
    command to `signguard/commands` so the ESP32 signage reacts too. An optional
    `content` overrides what the tampered update tries to display.
    """
    scenario = SCENARIOS.get(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"unknown scenario: {scenario_id}")

    protected = req.protected
    device_id = scenario.device_id
    authorized = _demo["authorized_content"]              # "before" content
    is_attack = scenario.tampered_content                 # baseline is not an attack
    # "after" content: the presenter's chosen tampered text, else the default.
    after_text = (
        req.content.strip()
        if (req.content and req.content.strip())
        else scenario.attacker_message
    )

    _demo["active"][device_id] = scenario
    hardware = False

    if is_attack and not protected:
        # WITHOUT SignGuard: no verification — the attacker's content is shown.
        payload = build_unprotected_payload(
            scenario, authentic_text=authorized, attacker_text=after_text
        )
    else:
        # Baseline (always) OR a protected attack: run the real pipeline.
        # Baseline pushes the authorized content (-> render); an attack pushes the
        # tampered content (-> hash mismatch -> block).
        events, _ = scenario.build()
        content = _content_update(after_text if is_attack else authorized)
        result = run_analysis(
            AnalyzeRequest(device_id=device_id, content_update=content, events=events)
        )
        payload = build_decision_payload(
            device_id,
            result,
            scenario,
            authentic_text=authorized,
            attacker_text=after_text if is_attack else None,
        )
        orch = _demo["orchestrator"]
        if is_attack and orch is not None and _demo["broker"]:
            orch.publish_command(
                device_id,
                result.decision.recommended_action,
                attack=scenario.hw_label or None,
            )
            hardware = True

    await manager.broadcast(payload)

    return {
        "triggered": scenario.id,
        "protected": protected,
        "device_id": device_id,
        "title": scenario.title,
        "decision": payload["decision"],
        "risk": payload["risk"],
        "hardware_notified": hardware,
    }


class UsbIngestRequest(BaseModel):
    device_id: str = MANUAL_DEVICE
    content_id: str = BASELINE_CONTENT_ID
    content: str                      # raw text read from the USB
    source: str = "usb"              # usb / wireless / admin_panel
    serial: str | None = None        # USB serial, if the detector has it
    protected: bool = True           # SignGuard ON (verify) or OFF (show as-is)


@app.post("/ingest/usb")
async def ingest_usb(req: UsbIngestRequest) -> dict:
    """Real edge path: a USB detector reads a pendrive, sends its content here.

    protected=True  -> full pipeline (SHA-256 verify -> AI -> decision -> audit);
                       a tampered file is BLOCKED and the sign keeps the verified
                       (original) content via safe fallback.
    protected=False -> SignGuard OFF: no check, the uploaded content is shown.
    If the broker is up, publishes the MQTT command so the ESP-12E reacts.
    """
    import base64 as _b64
    scenario = manual_scenario(req.content)
    _demo["active"][req.device_id] = scenario
    hardware = False

    if not req.protected:
        payload = build_unprotected_payload(
            scenario, authentic_text=_demo["authorized_content"], attacker_text=req.content
        )
        await manager.broadcast(payload)
        return {"device_id": req.device_id, "protected": False, "verified": None,
                "decision": "displayed", "recommended_action": "render",
                "risk": 0, "hardware_notified": False}

    content_b64 = _b64.b64encode(req.content.encode("utf-8")).decode("ascii")
    events = [
        SecurityEvent(device_id=req.device_id, event_type=EventType.unauthorized_usb,
                      authorized=False, data={"serial": req.serial or "unknown"}),
        SecurityEvent(device_id=req.device_id, event_type=EventType.content_received,
                      authorized=False, data={"content_id": req.content_id, "source": req.source}),
    ]
    content = ContentUpdate(device_id=req.device_id, content_id=req.content_id,
                            content_bytes_b64=content_b64, source=req.source)
    result = run_analysis(
        AnalyzeRequest(device_id=req.device_id, content_update=content, events=events)
    )
    payload = build_decision_payload(
        req.device_id, result, scenario,
        authentic_text=_demo["authorized_content"], attacker_text=req.content,
    )
    orch = _demo["orchestrator"]
    if orch is not None and _demo["broker"]:
        if result.decision.decision == "render":
            # genuine content: show the real authorized text on the LCD
            l1, _, l2 = _demo["authorized_content"].replace("\n", "|").partition("|")
            orch.publish_command(req.device_id, result.decision.recommended_action,
                                 line1=l1[:16], line2=l2[:16])
        else:
            orch.publish_command(req.device_id, result.decision.recommended_action,
                                 attack="USB TAMPER")
        hardware = True

    await manager.broadcast(payload)
    return {
        "device_id": req.device_id, "protected": True,
        "verified": result.verification_result.match if result.verification_result else None,
        "decision": result.decision.decision,
        "recommended_action": result.decision.recommended_action.value,
        "risk": result.risk_score.score if result.risk_score else 0,
        "hardware_notified": hardware,
    }


class ContentRequest(BaseModel):
    content: str


@app.post("/demo/authorize-content")
async def authorize_demo_content(req: ContentRequest) -> dict:
    """Set the 'before' content the authority has blessed (drives the BEFORE panel).

    Re-authorizes it in the registry so baseline/legit pushes match, and any
    different (tampered) content will hash-mismatch.
    """
    text = req.content if req.content.strip() else AUTHENTIC_TEXT
    _demo["authorized_content"] = text
    authorize_content(registry, BASELINE_CONTENT_ID, text.encode("utf-8"), "transport_authority")
    await manager.broadcast({"type": "authorized", "authentic_text": text})
    return {"authorized": True, "authentic_text": text}


class LoginRequest(BaseModel):
    user: str
    password: str


class PublishRequest(BaseModel):
    content: str
    protected: bool = True


@app.post("/demo/login")
def demo_login(req: LoginRequest) -> dict:
    """Manual credential attack, step 1 — the presenter logs into the panel.

    Weak/default passwords are flagged as a credential attack; the session is
    still 'granted' (attacker got in) so the next step can prove that content
    integrity blocks the upload anyway — defense in depth.
    """
    flag = classify_credentials(req.user, req.password)
    granted = flag in ("valid", "default")
    _demo["session"] = {
        "granted": granted,
        "flag": flag,
        "events": [e.model_dump(mode="json") for e in login_events(req.user, flag)],
        "user": req.user,
    }
    notes = {
        "valid": "Operator authenticated.",
        "default": "Access granted via DEFAULT credentials — flagged as suspicious.",
        "invalid": "Access denied — invalid credentials.",
    }
    return {"granted": granted, "flag": flag, "note": notes[flag]}


@app.post("/demo/publish")
async def demo_publish(req: PublishRequest) -> dict:
    """Manual credential attack, step 2 — push content from the admin panel."""
    session = _demo.get("session")
    if not session or not session.get("granted"):
        raise HTTPException(status_code=403, detail="Log in first (access not granted).")

    scenario = manual_scenario(req.content)
    _demo["active"][MANUAL_DEVICE] = scenario
    authorized = _demo["authorized_content"]
    hardware = False

    if not req.protected:
        payload = build_unprotected_payload(
            scenario, authentic_text=authorized, attacker_text=req.content
        )
    else:
        events = [SecurityEvent.model_validate(e) for e in session["events"]]
        content = manual_content(req.content)
        result = run_analysis(
            AnalyzeRequest(device_id=MANUAL_DEVICE, content_update=content, events=events)
        )
        payload = build_decision_payload(
            MANUAL_DEVICE, result, scenario, authentic_text=authorized,
            attacker_text=req.content,
        )
        orch = _demo["orchestrator"]
        if orch is not None and _demo["broker"]:
            orch.publish_command(
                MANUAL_DEVICE, result.decision.recommended_action, attack=MANUAL_HW_LABEL
            )
            hardware = True

    await manager.broadcast(payload)
    return {
        "protected": req.protected,
        "credential_flag": session["flag"],
        "decision": payload["decision"],
        "risk": payload["risk"],
        "hardware_notified": hardware,
    }


@app.websocket("/ws")
async def ws(websocket: WebSocket) -> None:
    """Push live decisions to the dashboard."""
    await manager.connect(websocket)
    await websocket.send_json({"type": "status", "broker": _demo["broker"]})
    try:
        while True:
            await websocket.receive_text()  # keepalive; we don't expect input
    except WebSocketDisconnect:
        manager.disconnect(websocket)
