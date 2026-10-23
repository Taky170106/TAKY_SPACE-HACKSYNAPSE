# SignGuard AI — Architecture, Vulnerability & Approach

**Team TAKY_SPACE · VIT · IEEE HackSynapse 2026**
Where the attack happens, how we stop it, our approach vs. existing solutions,
and the exact **code functions** that implement each step.

---

## 1. System architecture (end to end)

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ ATTACK SURFACE  (physical + network, in the field)                         │
 │   USB port     rogue Wi-Fi update link     admin panel / default creds     │
 └───────────────┬──────────────────────────────────────────────────────────┘
                 │  a content update arrives (bytes) + surrounding events
                 ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ EDGE NODE   real ESP-12E  |  web /lab Pi-sim  |  edge_node/ software sims   │
 │   sends update to the backend over HTTP (/ingest/usb) or MQTT              │
 └───────────────┬──────────────────────────────────────────────────────────┘
                 ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ SIGNGUARD BACKEND  (FastAPI)  ── the TRUST BOUNDARY ──                      │
 │                                                                            │
 │  TRACK A (deterministic gate)      TRACK B (AI context, explain-only)      │
 │  ─ SHA-256 of the bytes            ─ Isolation Forest risk 0–100           │
 │  ─ compare to AUTHORIZED hash      ─ SHAP per-feature explanation          │
 │    (Ed25519-signed, on-chain)                                              │
 │            │                                   │                           │
 │            └──────────────┬────────────────────┘                          │
 │                           ▼                                                │
 │              RISK FUSION  →  DECISION ENGINE  →  render / block / isolate   │
 │                           │                                                │
 │              SAFE FALLBACK + APPEND-ONLY AUDIT                             │
 └───────────────┬──────────────────────────────────────────────────────────┘
                 ▼  MQTT  signguard/commands
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ ESP-12E SIGN   LCD + buzzer + LEDs   (render / TAMPER+buzzer / lock)        │
 └──────────────────────────────────────────────────────────────────────────┘
        + Web console (/) · passenger sign (/signage) · lab (/lab) via WebSocket
```

**One sentence:** Wi-Fi/USB is the *attack surface* → SignGuard is the *trust
boundary* → SHA-256 is the *integrity gate* → AI/XAI is *context* → Decision
Engine *blocks* → MQTT *carries the response* → ESP-12E *makes the attack visible*.

---

## 2. Where the vulnerability occurs

The weakness is **not** a bug in one product — it is a **design gap** in how
transport signage is built today:

| # | Vulnerability | Where it lives | Why it's exploitable |
|---|---|---|---|
| V1 | **Unauthenticated content path** | USB port, Wi-Fi update link, admin panel | Physically reachable, weakly secured; anyone who reaches it can submit an update. |
| V2 | **Trust of the channel, not the content** | The sign controller | It verifies *that an update arrived*, never *whether the bytes are the approved bytes*. |
| V3 | **No integrity gate before the screen** | Between the update interface and the display | Reaching the interface = permission to change what the public sees. |
| V4 | **Default / weak admin credentials** | Admin panel login | `admin/admin`-style access lets an attacker "legitimately" push content. |
| V5 | **No tamper-evident record** | Audit / logging | Even if noticed, there's no immutable proof of what changed and when. |

**The core line:** *reaching the update interface must not mean the attacker can
make unauthorized content trusted.* Today that is false — SignGuard makes it true.

---

## 3. How we solve it (our approach)

**Zero-trust content integrity + explainable attack context + tamper-evident
audit + a physical safe state.** Two tracks:

- **Track A — Content Integrity (deterministic / cryptographic).** Every update
  is untrusted until its **SHA-256** fingerprint matches the **authorized**
  fingerprint, which is **Ed25519-signed** and stored in a **hash-linked
  on-chain ledger**. Match → render; mismatch or unknown → **block + safe
  fallback**. This gate is pure cryptography — the AI cannot weaken it.

- **Track B — Attack Context (AI / explainable).** An **Isolation Forest** turns
  the surrounding events (USB inserts, failed logins, rogue Wi-Fi, credential
  attempts) into a **0–100 risk**, and **SHAP** explains *why*. This assesses and
  escalates (e.g. `isolate` on critical risk) but **never overrides** Track A.

**Invariant:** *Cryptography decides block/allow. AI only assesses and explains.*

Result: even a full breach of the update path cannot put attacker content on the
sign — the worst case is a blocked update and a trusted fallback, all recorded.

---

## 4. Existing solutions — and why they fall short

| Existing approach | What it does | Gap SignGuard closes |
|---|---|---|
| **TLS / HTTPS on the update link** | Encrypts the channel, authenticates the server | Protects *transport*, not *content*. A compromised admin panel still pushes "valid" TLS traffic with fake content. |
| **CMS user logins / RBAC** | Restricts who can post | Falls to stolen/default creds (V4); once in, content is trusted. |
| **OS / code signing (e.g., signed firmware)** | Verifies the *software* image | Verifies the app, not each *content update* shown on the sign. |
| **Generic SIEM / anomaly detection** | Flags suspicious behaviour | Detective, not preventive; usually a black box, and doesn't gate the display. |
| **Manual monitoring** | Staff watch the signs | Doesn't scale to thousands of unattended displays; slow. |

**SignGuard's differentiator:** a **per-update cryptographic content gate** at
the sign's trust boundary, **plus** explainable AI context, **plus** an on-chain
tamper-evident record, **plus** a guaranteed **physical safe state** on the
hardware. It is **preventive at the content layer**, not just channel security or
after-the-fact detection.

---

## 5. The vulnerability → solution → CODE mapping

The whole decision runs through one function, `run_analysis()`
(`app/pipeline.py:20`), which both `POST /analyze` and the MQTT orchestrator call
so the two transports can never diverge.

| Step | Vuln addressed | Function (file:line) | What it does |
|---|---|---|---|
| **Compute fingerprint** | V2 | `sha256_hex()` `app/authorization/authorize.py:14`, `app/chain/registry.py:18` | SHA-256 of the incoming bytes. |
| **Verify vs authorized** | V2, V3 | `verify_content()` `app/verification/verify.py:16` | Compares computed hash to the authorized hash; unknown id = mismatch (never render unknown bytes). |
| **Authorized hash source** | V1, V2 | `ChainRegistry.get_authorized_hash()` `app/chain/registry.py:41`; `authorize()` `:31`; `verify()` `:59` | The signed, on-chain root of trust for "approved" content. |
| **Digital signature** | V1, V5 | `ensure_keys()` `app/crypto/signing.py:26`, `sign_hex()` `:66`, `verify_hex()` `:71` | Ed25519 signs each authorized fingerprint; only the authority key can bless content. |
| **Tamper-evident chain** | V5 | `Ledger.append()` `app/chain/ledger.py:64`, `Block.compute_hash()` `:32`, `verify_chain()` `:100` | Hash-links every authorization; any edit breaks the chain. |
| **Feature extraction** | V1, V4 | `build_feature_vector()` `app/features/engineer.py:40` | Turns the last 5 min of events (USB, logins, wireless…) into the model input. |
| **Anomaly score** | V1, V4 | `AnomalyModel.score()` `app/ml_engine/model.py:82` | Isolation Forest → 0–100 threat context. |
| **Explainability** | (trust/UX) | `ShapExplainer.explain()` `app/xai/explain.py:32` | SHAP per-feature reasons for the score (threat score only, never the hash). |
| **Risk fusion** | V1, V4 | `compute_risk()` `app/scoring/score.py:47` | Combines hash result + rule signals + AI anomaly into one 0–100 risk. |
| **Decision** | V2, V3 | `decide()` `app/decision/engine.py:20` | Hash mismatch → block (terminal); critical risk → isolate; elevated → block; else render. |
| **Safe state** | V3 | `safe_fallback_content()` `app/fallback/safe.py:16` | The trusted content shown when an update is blocked. |
| **Immutable audit** | V5 | `AuditStore.record()` `app/audit/store.py:47` | Append-only log of every decision (device, hashes, risk, action). |
| **Drive the sign** | (response) | `Orchestrator.publish_command()` `app/orchestrator.py:152`; `_publish_command()` `:137` | Publishes `render/safe_fallback/isolate/unverified` (+ content lines) to the ESP over MQTT. |
| **Edge intake** | V1 | `ingest_usb()` `app/main.py` (`/ingest/usb`) | Real USB detector path: verify → AI → decide → MQTT → ESP. |

### Exact call order inside `run_analysis()` (app/pipeline.py)
```python
verification   = verify_content(registry, req.content_update)      # Track A gate
feature_vector = build_feature_vector(store, device_id, now=now)   # Track B features
anomaly        = anomaly_model.score(feature_vector)               # Track B score
xai            = shap_explainer.explain(feature_vector)            # Track B explain
risk           = compute_risk(device_id, verification, events, anomaly)  # fuse
decision       = decide(device_id, verification, risk=risk)        # render/block/isolate
audit_store.record(AuditRecord.from_analysis(...))                 # immutable log
```

The **hardware reaction** to `decision` lives in the firmware
`usb_demo/esp8266/main.py`: `on_command()` receives the MQTT command,
`set_mode()` switches state, and `update_actuators()` drives the LCD, LEDs and
buzzer (TAMPER = 1.2 s buzzer, then fast fallback to the original content).

---

## 6. Why this is strong (attack walk-through)

1. Attacker reaches the Wi-Fi update path or plugs in a USB (V1) — **allowed to
   *reach*, by assumption**.
2. They submit modified passenger info. `verify_content()` computes its SHA-256
   and finds **no match** to the Ed25519-signed on-chain hash (V2, V3 closed).
3. `decide()` returns **block**; `safe_fallback_content()` keeps the real content
   on the screen; `AuditStore.record()` logs it (V5 closed).
4. `compute_risk()` + `AnomalyModel` + SHAP explain the context; critical
   patterns trigger `isolate`.
5. MQTT drives the ESP-12E: **`TAMPER DETECTED` + buzzer**, then back to the
   authorized content — the attack is **blocked and made visible**.

Even with stolen admin creds (V4), the pushed content still must match the
**signed** authorized hash — which the attacker cannot forge without the
authority's private key.

---

## 7. Honest limits (Round-3 roadmap)
- On-chain ledger is **local / single-writer** → moving to a real **Solidity**
  smart contract.
- USB attack is currently software-driven → **real USB on a Raspberry Pi**
  (`edge_node/hardware/pi_usb_detector.py` already written).
- MQTT is open for the demo → add **TLS + auth + replay-nonce**.
- A stolen authority **private key** defeats any signature scheme → mitigated by
  key rotation / hardware-backed keys (not eliminated).
```
