# SignGuard AI — Project Status

**Team TAKY_SPACE · VIT · IEEE HackSynapse 2026**
_Blockchain-anchored content-integrity system for public-transport signage._
_Last updated: 2026-09-06_

---

## Summary

A public-transport sign only shows content that is **cryptographically proven
authentic**. Every update (USB / Wi-Fi / admin panel) is hashed (SHA-256) and
checked against an **Ed25519-signed, hash-linked on-chain registry**; an
**Isolation-Forest + SHAP** layer scores and explains the surrounding attack
context; a decision engine renders / blocks / isolates, logs an audit record,
and drives a real **ESP-12E** sign (LCD + buzzer + LEDs) over MQTT.

**Status: working end-to-end in software AND on real hardware. 46/46 tests pass.**

---

## ✅ Done

### Software — backend ("the brain")
- FastAPI app (REST + WebSocket); routes: `/analyze`, `/authorize`, `/audit`,
  `/chain`, `/chain/verify`, `/ingest/usb`, `/demo/*`, web pages.
- **Track A — Content Integrity (deterministic):** SHA-256 verification +
  **Ed25519 digital signatures** + **hash-linked on-chain ledger**
  (`verify_chain()` detects any edit).
- **Track B — Attack Context (AI):** Isolation Forest risk score (0–100) +
  **SHAP** per-feature explanations.
- Decision engine (render / block / isolate) + safe fallback + append-only
  audit trail.
- MQTT orchestrator (Mosquitto broker, native Windows, `0.0.0.0:1883`).
- **46 automated tests, all passing.**
- Key invariant: cryptography decides block/allow; AI only assesses & explains.

### Web UI (cyberpunk-SOC theme)
- `/` — security-operations dashboard (risk, SHAP, audit, before/after panels).
- `/signage` — full-screen passenger display.
- `/lab` — hardware lab (Raspberry-Pi + USB + ESP-12E visualisation) → drives
  the real LCD via `/ingest/usb`.

### Real hardware — ESP-12E (NodeMCU)
- Live LCD (16×2 I²C) + PWM buzzer + green/red LEDs over MQTT.
- **Self-recovering firmware:** multi-Wi-Fi + multi-broker auto-scan, OFFLINE
  demo mode, auto-reconnect (never hangs on "WiFi...").
- **FLASH button** = manual demo with no laptop/Wi-Fi (SECURE → TAMPER → LOCKED).
- Timings: buzzer **1.2 s**; `TAMPER DETECTED` shows **2.5 s** then auto-falls
  back to the original content; render shows "SYSTEM SECURE" (1.5 s) then reveals
  real content.
- Device `SG-RNP-001`; pins: LCD SDA=D2/GPIO4, SCL=D1/GPIO5, buzzer=D5/GPIO14,
  green=D6/GPIO12, red=D7/GPIO13, FLASH button=GPIO0.

### The attack demo (the money moment)
- `attack_demo.py` — same USB attack twice: **SignGuard OFF → sign hijacked to
  fake content**; **SignGuard ON → blocked** (`TAMPER DETECTED` + buzzer, then
  fallback to original) on the physical LCD. **No Raspberry Pi required.**

### Git — pushed per team member
- Repo: `github.com/Taky170106/TAKY_SPACE-HACKSYNAPSE`
- Branches: **backend** (Tamizh), **frontend** (Ajay), **hardware** (Akash),
  **simulator** (Lokesh Kumar), merged into **main**.
- Secrets kept out of git (Wi-Fi config, Ed25519 private key, runtime ledger).
- Commits dated Sep 5–6, 2026.

### Documents
- PPT (IEEE template): added Wi-Fi-attack slide + "SignGuard 2.0" comparison
  table + **Morph transitions** (`SignGuard - morph.pptx`).
- `PROJECT_REFERENCE.md` (every file documented), `SYSTEM_DEEP_DIVE.md`,
  `HARDWARE.md`, `ESP_INTEGRATION.md`, `UPDATES.md`, Round-3 roadmap/plan,
  mentor explanation script, review docs.
- Strong 4–5 line problem statement + two-track model write-up.

---

## Architecture & the vulnerability (summary)

**Architecture in one line:** Wi-Fi/USB (attack surface) → SignGuard (trust
boundary) → SHA-256 (integrity gate) → AI/XAI (context) → Decision Engine
(block) → MQTT (response) → ESP-12E (makes the attack visible).

**Where the vulnerability is:** transport signage trusts the *update channel*,
not the *content*. Reaching the update interface (USB / rogue Wi-Fi / admin
panel with default creds) is treated as permission to change what the public
sees — there is no integrity gate between the interface and the screen.

**How we solve it (two tracks):**
- **Track A — Content Integrity (deterministic):** every update is untrusted
  until its SHA-256 fingerprint matches the **Ed25519-signed, on-chain**
  authorized hash. Mismatch/unknown → block + safe fallback. Cryptography is
  the gate; the AI cannot weaken it.
- **Track B — Attack Context (AI, explain-only):** Isolation Forest risk (0–100)
  + SHAP explanations assess and escalate, but never override Track A.

**vs existing solutions:** TLS secures the *channel* not the content; CMS logins
fall to stolen/default creds; code-signing verifies the *app* not each update;
SIEM is detective + black-box. SignGuard is **preventive at the content layer**,
with a signed on-chain record and a guaranteed physical safe state.

**Code map (the whole decision runs through `run_analysis()` — app/pipeline.py:20):**
`verify_content()` (verification/verify.py:16) · `sign_hex()`/`verify_hex()`
(crypto/signing.py:66/71) · `Ledger.verify_chain()` (chain/ledger.py:100) ·
`AnomalyModel.score()` (ml_engine/model.py:82) · `ShapExplainer.explain()`
(xai/explain.py:32) · `compute_risk()` (scoring/score.py:47) · `decide()`
(decision/engine.py:20) · `safe_fallback_content()` (fallback/safe.py:16) ·
`AuditStore.record()` (audit/store.py:47) · `Orchestrator.publish_command()`
(orchestrator.py:152).

> Full detail in **ARCHITECTURE_AND_SECURITY.md**.

## ⏳ Not yet done (Round-3 roadmap)
- **Real Solidity smart contract** (currently a local hash-linked ledger).
- **Real USB on a physical Raspberry Pi** (detector code exists: `pi_usb_detector.py`).
- **MQTT security:** TLS + authentication + replay-nonce protection.
- Optional: Merkle-anchored audit, fleet/multi-node SOC, key rotation/PKI,
  quantified evaluation (detection rate / false-positive / latency).

---

## How to run
```bash
python run_demo.py       # backend + broker + dashboard -> http://localhost:8000
python attack_demo.py    # live attack on the real LCD (hijack vs block)
python -m pytest tests/ -q   # 46 passing
```
Hosts: `/` (dashboard) · `/signage` · `/lab`. LAN access via the laptop's IP:8000
(same Wi-Fi, allow inbound TCP 8000 + 1883).

## Known operational notes
- Keep the laptop **and** ESP on **one** 2.4 GHz network the whole demo
  (SSID "Why", broker `10.41.149.144`). Switching networks drops the ESP; a
  reset reconnects it, or use the FLASH button offline.
- Faint LCD text = the contrast **potentiometer** on the I²C backpack (hardware,
  turn the screw) — not a software setting.
- `run_demo.py` has no auto-reload; keep its terminal open during the demo.
