# SignGuard AI — Complete Project Reference

**Blockchain-anchored content-integrity system for public-transport signage.**
Team **TAKY_SPACE** · VIT · IEEE HackSynapse 2026.

This document lists **every file** in the project, what it does, and how the
pieces connect. It is the single source of truth for the whole codebase
(software + hardware + simulators).

---

## 1. What the system does (one paragraph)

A public-transport sign only shows content that has been cryptographically
authorised. Every proposed update (from USB, wireless, or an admin panel) is
**hashed (SHA-256)** and checked against an **Ed25519-signed, hash-linked
on-chain registry**. In parallel, an **Isolation-Forest** model scores the
*context* (0–100 risk) and **SHAP** explains it. A **decision engine** then
chooses `render` (show), `block` (safe fallback to the last good content) or
`isolate` (lock). Decisions are written to an **append-only audit trail** and
pushed over **MQTT** to a real **ESP-12E** signage node (LCD + buzzer + LEDs).
The crypto hash is the deterministic gate; the AI only scores and explains.

---

## 2. Architecture & data flow

```
 Attacker (USB / rogue Wi-Fi / admin creds)
        │
        ▼
 Edge node (real ESP-12E  OR  web /lab Pi-sim  OR  edge_node sims)
        │  content + events
        ▼
 FastAPI backend  ── /ingest/usb, /analyze, /authorize ──►  PIPELINE
        │                                                     │
        │   1. SHA-256 verify  vs  ChainRegistry (Ed25519 + hash-linked ledger)
        │   2. Feature engineering → Isolation-Forest score → SHAP explanation
        │   3. Decision engine (render / block / isolate) + safe fallback
        │   4. Append-only audit record
        ▼                                                     ▼
 MQTT (Mosquitto, signguard/commands) ───────────►  ESP-12E LCD + buzzer + LEDs
        │
        ▼
 Web console (/) · passenger sign (/signage) · hardware lab (/lab) via WebSocket
```

**Key invariant (CLAUDE.md §2):** SHAP explains the *AI threat score only* —
never the hash comparison. The hash check is deterministic; the AI is context.

---

## 3. Repository layout (top level)

| Path | Purpose |
|---|---|
| `app/` | FastAPI backend — the Layer-2 "brain" (crypto, AI, decision, audit, web) |
| `usb_demo/` | Real-hardware demo: ESP-12E / ESP32 firmware + laptop trigger |
| `edge_node/` | Software Pi / USB / Kali simulators + real-Pi detector |
| `tests/` | Pytest suite (46 tests) |
| `data/` | Runtime data — `sample_events.json` tracked; `keys/`, `chain/` git-ignored |
| `*.md` | Documentation (this file, README, deep-dive, hardware guides, changelog) |
| `run_demo.py` | One-command launcher: Mosquitto + backend + dashboard |
| `attack_demo.py` | Scripted live attack on the real LCD (hijack vs block) |
| `demo_attacks.py` | Older attack-scenario helper |
| `requirements.txt` | Python dependencies |
| `mosquitto.conf` / `docker-compose.yml` | Broker config / optional container stack |

---

## 4. `app/` — FastAPI backend (every file)

### Top-level
| File | What it does |
|---|---|
| `app/__init__.py` | Package marker. |
| `app/main.py` | **The FastAPI app.** Routes: `/health`, `/authorize`, `/analyze`, `/fallback`, `/audit`, `/chain`, `/chain/verify`, web pages `/`, `/signage`, `/lab`, and the edge path **`/ingest/usb`** (USB detector → verify/AI/decision → MQTT → ESP). Also `/demo/*` endpoints that drive the before/after attack demo. Holds the in-memory `_demo` state (authorized content, orchestrator, broker flag). |
| `app/deps.py` | Shared singletons used by API + tests: `registry = ChainRegistry()`, `audit_store`, `anomaly_model = AnomalyModel()`, `shap_explainer = ShapExplainer(...)`. Single source so everything uses the same instances. |
| `app/pipeline.py` | Orchestrates one analysis: features → model score → SHAP → decision → audit. Called by `/analyze` and `/ingest/usb`. |
| `app/orchestrator.py` | MQTT publisher. `publish_command(device_id, command, attack, line1, line2)` builds a `Command` and publishes to `signguard/commands` so the ESP LCD reacts. Tracks last command per device. |
| `app/secure_main.py` | **Separate** FastAPI app (port 8010) exposing the signing/chain API: `/authorize`, `/verify`, `/chain`, `/chain/verify`. Kept apart from the main demo app. |
| `app/demo_scenarios.py` | Canned attack scenarios (USB tamper, rogue wireless, admin creds) + `manual_scenario()` used by `/ingest/usb`. |

### `app/schemas/` — Pydantic models
| File | What it does |
|---|---|
| `schemas/__init__.py` | Re-exports the models. |
| `schemas/models.py` | All request/response types: `SecurityEvent`, `ContentUpdate`, `FeatureVector`, `XaiFactor`, `XaiExplanation`, `Decision`, `Command` + enums `EventType`, `CommandType` (`render`/`safe_fallback`/`isolate`/**`unverified`**), `RiskLevel`. |

### `app/crypto/` — digital signatures
| File | What it does |
|---|---|
| `crypto/__init__.py` | Exports signing helpers. |
| `crypto/signing.py` | **Ed25519** signing: `ensure_keys()` (creates `data/keys/authority_ed25519.*`), `sign_hex()`, `verify_hex()`, `public_hex()`. |

### `app/chain/` — on-chain registry (blockchain-style)
| File | What it does |
|---|---|
| `chain/__init__.py` | Exports `ChainRegistry`. |
| `chain/ledger.py` | `Block` dataclass + `Ledger`: JSON-persisted, **hash-linked** chain (`prev_hash`), `verify_chain()` detects any edit. Genesis prev = 64 zeros. Stored at `data/chain/ledger.json`. |
| `chain/registry.py` | `ChainRegistry(HashRegistry)`: `authorize()` **signs** a content hash and appends a block; `get_authorized_hash()`, `verify()` (integrity + signature + chain). Drop-in for the old `LocalRegistry`. |

### `app/registry/` — registry interface + local impl
| File | What it does |
|---|---|
| `registry/__init__.py` | Exports. |
| `registry/base.py` | `HashRegistry` abstract interface (authorize / get / verify). |
| `registry/local.py` | `LocalRegistry` — original SQLite-backed hash store (superseded by `ChainRegistry`, kept for reference/tests). |

### `app/features/` — feature engineering
| File | What it does |
|---|---|
| `features/__init__.py` | Exports. |
| `features/engineer.py` | `FEATURE_ORDER` (single source of column order), `to_row()`, `build_feature_vector()` — turns the last 5 min (`WINDOW_SECONDS=300`) of events for a device into the 7-feature vector the model consumes. |

### `app/ml_engine/` — anomaly model
| File | What it does |
|---|---|
| `ml_engine/__init__.py` | Exports `AnomalyModel`. |
| `ml_engine/model.py` | **Isolation Forest** (`n_estimators=200`, `contamination=0.03`, `random_state=42`), trained at construction on a synthetic "quiet" baseline. `score(fv)` → anomaly score + `is_anomaly`. Exposes `.forest` for SHAP. |

### `app/xai/` — explainability (recovered 2026-09-06)
| File | What it does |
|---|---|
| `xai/__init__.py` | Exports `ShapExplainer`. |
| `xai/explain.py` | **SHAP** `TreeExplainer` over the forest. `explain(fv, top_k)` → `XaiExplanation` with signed factors (positive = pushed toward anomaly). Explains the *threat score only*, never the hash. |

### `app/scoring/` — risk score
| File | What it does |
|---|---|
| `scoring/__init__.py` | Exports. |
| `scoring/score.py` | Converts model output + rule signals into a 0–100 risk (mismatch +40, usb +20, creds +15, wireless +10, ai ×15) and a `RiskLevel`. |

### `app/decision/` — decision engine
| File | What it does |
|---|---|
| `decision/__init__.py` | Exports. |
| `decision/engine.py` | Maps (hash match?, risk) → `render` / `block` / `isolate`. Thresholds `RISK_THRESHOLD=50`, `CRITICAL_THRESHOLD=80`. Hash mismatch always blocks. |

### `app/fallback/` — safe fallback
| File | What it does |
|---|---|
| `fallback/__init__.py` | Exports. |
| `fallback/safe.py` | Returns the last authorised (safe) content to display when an update is blocked. |

### `app/verification/` — integrity check
| File | What it does |
|---|---|
| `verification/__init__.py` | Exports. |
| `verification/verify.py` | SHA-256 of incoming content vs the registry's authorised hash → match / mismatch. |

### `app/authorization/`
| File | What it does |
|---|---|
| `authorization/__init__.py` | Exports. |
| `authorization/authorize.py` | `authorize_content()` — helper to sign + register the "blessed" baseline content. |

### `app/audit/` — append-only trail
| File | What it does |
|---|---|
| `audit/__init__.py` | Exports `AuditStore`. |
| `audit/records.py` | `AuditRecord` schema (device, decision, risk, timestamp, hashes). |
| `audit/store.py` | `AuditStore` — append-only store (in-memory or file via `SIGNGUARD_AUDIT_DB`). |

### `app/ingestion/` — event intake
| File | What it does |
|---|---|
| `ingestion/__init__.py` | Exports. |
| `ingestion/store.py` | `EventStore` — in-memory ring of `SecurityEvent`s per device. |
| `ingestion/subscriber.py` | `load_events_from_file()` (seeds from `data/sample_events.json`) + live MQTT `IngestionService` on `signguard/events`. |

### `app/web/` — UI (server-rendered HTML + WebSocket)
| File | What it does |
|---|---|
| `web/__init__.py` | Exports the routers. |
| `web/dashboard.py` | **Security-operations console** (`/`) — cyberpunk SOC theme; live risk, SHAP factors, audit feed, before/after attack panels. |
| `web/signage.py` | **Passenger sign** (`/signage`) — the big public display view. |
| `web/lab.py` | **Hardware lab** (`/lab`) — realistic Raspberry-Pi + USB-stick simulator that POSTs to `/ingest/usb`; visualises the ESP-12E reaction. Drives the real LCD. |
| `web/live.py` | WebSocket manager (`/ws`) broadcasting state to all open pages. |

---

## 5. `usb_demo/` — real hardware (ESP-12E / ESP32)

| File | What it does |
|---|---|
| `usb_demo/SETUP.md` | Step-by-step hardware bring-up guide. |
| `usb_demo/mosquitto.conf` | Broker config for the demo (binds `0.0.0.0:1883`). |
| `usb_demo/docker-compose.yml` | Optional containerised broker. |
| **`usb_demo/esp8266/main.py`** | **The ESP-12E firmware (primary hardware).** Self-recovering: multi-Wi-Fi + multi-broker scan, OFFLINE-demo mode, **FLASH-button** manual demo, auto-reconnect. Handles `render` (two-phase: SECURE banner → original content), `safe_fallback` (TAMPER + 1.2 s buzzer, auto-fallback after 2.5 s), `isolate`, `unverified` (hijack text). Timings: `BUZZ_MS=1200`, `TAMPER_SHOW_MS=2500`, `SECURE_BANNER_MS=1500`. |
| `usb_demo/esp8266/config.py` | **Real device config — GIT-IGNORED (holds Wi-Fi secret).** `WIFI_NETWORKS`, `BROKER_CANDIDATES`, pins, `DEVICE_ID=SG-RNP-001`. |
| `usb_demo/esp8266/config.example.py` | Committed template (placeholders) showing the flexible config structure. |
| `usb_demo/esp8266/i2c_lcd.py`, `lcd_api.py` | I²C 16×2 LCD driver (PCF8574 backpack, addr 0x27). |
| `usb_demo/esp8266/lib_umqtt/simple.py` | `umqtt.simple` MQTT client for MicroPython. |
| `usb_demo/esp8266/flash.ps1` | PowerShell helper to flash MicroPython + upload files. |
| `usb_demo/esp32/*` | ESP32 firmware variant (`main.py`, `config.example.py`, LCD drivers). |
| `usb_demo/laptop/demo_trigger.py` | Laptop-side script that publishes commands to the ESP (standalone of the backend). |
| `usb_demo/laptop/authorize_content.py` | Sets the authorised baseline for the laptop-only demo. |
| `usb_demo/laptop/mqtt_config.py` | Broker/device settings for the laptop trigger. |
| `usb_demo/laptop/requirements.txt` | Deps for the laptop trigger. |
| `usb_demo/laptop/data/authorized_content.txt` | The blessed "before" content. |
| `usb_demo/laptop/data/authorized_hash.json` | Its stored SHA-256. |
| `usb_demo/laptop/data/usb_attack_content.txt` | The attacker's fake content. |

**Wiring (NodeMCU ESP-12E):** LCD SDA=D2/GPIO4, SCL=D1/GPIO5; buzzer=D5/GPIO14;
green LED=D6/GPIO12; red LED=D7/GPIO13; FLASH button=GPIO0 (onboard).

---

## 6. `edge_node/` — software simulators + real-Pi detector

| File | What it does |
|---|---|
| `edge_node/__init__.py` | Package marker. |
| `edge_node/mqtt_config.py` | Broker/topic/device settings for the sims. |
| `edge_node/usb_detector.py` | Software USB detector — watches for a "pendrive", reads content, POSTs `/ingest/usb`. |
| `edge_node/display.py` | Console/software signage display driver. |
| `edge_node/content_simulator.py` | Emits content updates for testing. |
| `edge_node/event_simulator.py` | Replays `data/sample_events.json` onto the broker so the backend can be exercised offline. |
| `edge_node/kali_usb_sim.py` | Simulates the "Kali attacker" writing a malicious file to the pendrive. |
| `edge_node/sim/__init__.py` | Marker. |
| `edge_node/sim/pi_sim.py` | Virtual Raspberry Pi (uses a `pendrive.img`). |
| `edge_node/sim/insert_usb.py` | Simulates inserting the USB into the virtual Pi. |
| `edge_node/hardware/pi_usb_detector.py` | **Real Raspberry Pi** detector (pyudev): on real USB insert, mount → read → hash → POST `/ingest/usb`. |
| `edge_node/hardware/pi_usb_monitor.py`, `win_usb_monitor.py` | Platform USB-insertion monitors (Linux/Windows). |
| `edge_node/hardware/pi_config.py` | Pi-side config (`BROKER_HOST`, `API_URL`). |
| `edge_node/hardware/requirements.txt` | Pi deps (pyudev, requests). |
| `edge_node/hardware/SETUP.md` | Real-Pi setup guide. |
| `edge_node/hardware/esp32/*` | ESP32 firmware copy used with the Pi path. |

---

## 7. `tests/` — pytest suite (46 tests, all green)

| File | Covers |
|---|---|
| `tests/test_api.py` | FastAPI endpoints (`/authorize`, `/analyze`, `/ingest/usb`, etc.). |
| `tests/test_audit.py` | Append-only audit trail. |
| `tests/test_demo.py` | Demo scenarios / before-after flow. |
| `tests/test_scoring.py` | Risk-scoring rules. |
| `tests/test_secure_chain.py` | Ed25519 signing + hash-linked ledger + tamper detection. |
| `tests/test_track_a.py` | "Track A" — crypto/verification path. |
| `tests/test_track_b.py` | "Track B" — features + Isolation-Forest + **SHAP** + sample-event attack devices. |

Run: `python -m pytest tests/ -q`.

---

## 8. Documentation files

| File | Purpose |
|---|---|
| `README.md` | Project intro + quick start. |
| `PROJECT_REFERENCE.md` | **This file** — every-file reference. |
| `SYSTEM_DEEP_DIVE.md` | Deep technical walk-through grounded in the actual code. |
| `HARDWARE.md` | Hardware bill-of-materials + wiring. |
| `ESP_INTEGRATION.md` | ESP-12E setup + how the LCD reacts per command. |
| `UPDATES.md` | Running changelog of everything implemented. |
| `PROGRESS.md` | Status notes. |
| `PROJECT_SUMMARY.md` | Executive summary. |

---

## 9. How to run

```bash
# 1. Backend + broker + dashboard (one command)
python run_demo.py                 # http://localhost:8000  (/, /signage, /lab)

# 2. Live attack on the real LCD (in a second terminal)
python attack_demo.py              # genuine → hijack (OFF) → blocked (ON) → restore

# 3. Tests
python -m pytest tests/ -q         # 46 passing
```

**The core demo (money moment):** the *same* USB attack **hijacks the sign**
when SignGuard is OFF, and is **blocked on the physical LCD** (`TAMPER
DETECTED` + buzzer, then fallback to the original content) when it's ON — all
reflected live on the dashboard.

**Hardware-only fallback:** with no laptop/Wi-Fi, press the ESP's **FLASH
button** to cycle `SECURE → TAMPER (buzzer) → LOCKED → SECURE`.

---

## 10. MQTT topics & device

| Topic | Direction | Payload |
|---|---|---|
| `signguard/events` | edge → backend | `SecurityEvent` JSON |
| `signguard/content` | edge → backend | `ContentUpdate` JSON |
| `signguard/commands` | backend → ESP | `Command` (`render`/`safe_fallback`/`isolate`/`unverified`, + `line1`/`line2`) |

Device id: **`SG-RNP-001`**. Broker: Mosquitto on the laptop, `0.0.0.0:1883`.

---

## 11. Security notes

- **Never committed:** `usb_demo/esp8266/config.py` (Wi-Fi secret),
  `data/keys/` (Ed25519 **private key**), `data/chain/ledger.json` (runtime) —
  all git-ignored. Only `*.example.py` templates are tracked.
- The crypto hash is the **deterministic gate**; the AI never overrides it.
- Honest gaps (Round 3 roadmap): local single-writer chain (→ Solidity),
  software USB trigger (→ real Pi), open MQTT (→ TLS + auth + replay nonce).
