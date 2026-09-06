# SignGuard AI — Progress Log
### Blockchain-based content integrity system for public transport

Status snapshot of the build so far. Source of truth for the design is
`CLAUDE.md` (frozen). This file just records **what exists and what's verified**.

Last updated: 2026-08-22

---

## Build phases at a glance

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Broker + FastAPI skeleton + schemas + sample data + edge simulators | ✅ Done |
| **Phase 1 (Track A)** | authorization → verification → decision → safe fallback | ✅ Done — demoable |
| **Hardware (final kit)** | Pi USB monitor + ESP32 LCD/buzzer output node | ✅ Bundle adopted (not runtime-tested here) |
| **Phase 2 (Track B)** | ingestion → features → IsolationForest → SHAP | ✅ Done — wired into `/analyze` |
| **Phase 3** | risk scoring → full decision engine | ✅ Done — `/analyze` returns all 4 fields |
| **Phase 4** | audit trail → full `/analyze` → end-to-end test | ✅ Done — every decision persisted, `GET /audit` exposes the trail |

---

## Phase 0 — Foundation ✅

- **Broker: native Mosquitto** (no Docker — see the Broker section below). `docker-compose.yml` is kept as a fallback but is **no longer the chosen path**.
- **`mosquitto.conf`** (repo root) — binds `0.0.0.0:1883`, `allow_anonymous true` so Pi/ESP32 connect over Wi-Fi. `persistence false`, `log_dest stdout` (Docker-only `persistence_location /mosquitto/data/` removed so it runs natively on Windows).
- **`requirements.txt`** — the frozen §5 stack (FastAPI, pydantic v2, paho-mqtt, scikit-learn, shap, pytest…).
- **`app/schemas/`** — all §6 + §7 Pydantic v2 models in `models.py`, re-exported from `__init__.py`. Includes frozen `EventType` (12 values) and `CommandType` (3 values) enums, plus the `/analyze` request/response contract.
- **`app/` package skeleton** — every §11 directory exists: `schemas, registry, authorization, verification, fallback, ingestion, features, ml_engine, xai, scoring, decision, audit`.
- **`data/sample_events.json`** — 26 mixed events across 6 devices; **all 12 event_types covered** (benign + attack sequences).
- **Health check** — `GET /health` → `{"status":"ok"}`.

## Broker — native Mosquitto (Windows) ✅ (2026-08-22)

Switched from Docker to a **native Mosquitto** install on the dev machine.

- **Installed** Eclipse Mosquitto **2.1.2** via `winget` (`EclipseFoundation.Mosquitto`) → `C:\Program Files\mosquitto\`. Ships `mosquitto.exe`, `mosquitto_pub.exe`, `mosquitto_sub.exe`.
- **`mosquitto.conf` made native-safe** — removed the Docker container path `persistence_location /mosquitto/data/` (invalid on Windows); now `persistence false` + `log_dest stdout` + `listener 1883 0.0.0.0` + `allow_anonymous true`.
- **Verified**: launched with `mosquitto.exe -c mosquitto.conf -v` → broker binds **`0.0.0.0:1883`** (LAN-open), confirmed via `Get-NetTCPConnection`.
- **Dev broker LAN IP (Wi-Fi):** `10.63.29.144` → use as `BROKER_IP` in ESP32/Pi config.

**Run the broker (demo):**
```powershell
& "C:\Program Files\mosquitto\mosquitto.exe" -c "D:\J.ACKTHON\mosquitto.conf" -v
```

- **Auto-service sidelined ✅** — the winget install had registered a Windows **service** (`mosquitto`, **Automatic**, localhost-only) that grabbed port 1883. Ran (elevated) `Stop-Service mosquitto -Force; Set-Service mosquitto -StartupType Manual` → now **Stopped / Manual**, so port 1883 is free for the LAN broker and it won't auto-grab on reboot.
- **Live pub/sub verified ✅** — started `mosquitto.exe -c mosquitto.conf`, subscribed `signguard/#`, published to `signguard/events` → message received. Broker is fully working.

## Phase 1 — Track A (the deterministic star) ✅

The one rule (§2): content integrity is SHA-256, never waits for ML.

- **`app/registry/`** — `HashRegistry` interface + `LocalRegistry` (SQLite-backed, thread-safe). Only implementation, per §8.
- **`app/authorization/`** — SHA-256 hashing → `ContentRecord`.
- **`app/verification/`** — hash compare; unknown `content_id` is treated as a mismatch (never render unauthorized bytes).
- **`app/decision/`** — §9 engine; **hash mismatch blocks instantly before any ML** (§2 invariant), risk only refines a MATCH (render / block / isolate).
- **`app/fallback/`** — the trusted §10 message.
- **`app/main.py`** — `/health`, `/authorize`, `/analyze` (Track A wired; `risk_score`/`xai_explanation` return `null` until Phase 2–3, contract stays stable).

> Note: this went slightly beyond the "structure + schemas only" scope of an early prompt — Track A logic is built and tested. Flagged previously; kept because it's correct and passing.

## Phase 2 — Track B (attack-context intelligence) ✅

The probabilistic value-add. **Never gates content integrity** (§2) — it only
assesses how suspicious a device's recent behaviour looks.

- **`app/ingestion/`** — `EventStore` (in-memory, thread-safe, per-device history) + `IngestionService` (live MQTT subscribe/validate/store) + `load_events_from_file` (offline dev seed). Windowing bounds events on both sides of `now`.
- **`app/features/`** — windowed feature engineering → the exact 7 §6 features. `FEATURE_ORDER` is the single source of truth for column order (imported by ML + XAI so vectors never misalign).
- **`app/ml_engine/`** — `AnomalyModel` wrapping IsolationForest, trained at import on a synthetic healthy baseline (with realistic variance in every feature so attack signals are learnable). Calibrated 0..1 `anomaly_score` anchored at the model's own decision boundary.
- **`app/xai/`** — `ShapExplainer` (SHAP TreeExplainer) → top factors, oriented so **positive impact = toward anomaly**.
- **Wired into `/analyze`** — supplied `events` now produce a populated `xai_explanation`. `risk_score` still null (Phase 3).

**Behaviour verified against sample data:** healthy nodes score ~0.05 (not anomalous); all four attack devices (usb+mismatch, login burst, rogue-wifi+mismatch, tamper+usb+mismatch) score 0.67–0.78 and flag anomalous, with the correct SHAP drivers surfaced.

> Two bugs found & fixed while building: (1) event window included future events; (2) IsolationForest couldn't learn on constant-in-baseline incident features — fixed by giving the baseline realistic variance.

## Phase 3 — Risk scoring + decision fusion ✅

- **`app/scoring/`** — `compute_risk()` fuses hash result + rule signals + AI anomaly into a 0–100 `RiskScore` with `level` and `breakdown`, using the frozen §9 weights (mismatch 40, usb 20, default-creds 15, wireless 10, ai_anomaly ×15).
- **Decision engine** now consumes risk: hash mismatch still blocks first (§2); on a MATCH, risk ≥ 50 blocks, risk ≥ 80 isolates.
- **`/analyze` returns all four fields** — `verification_result`, `risk_score`, `xai_explanation`, `decision`. Verified end-to-end (tampered + attack events → score 71/high, block + safe_fallback).
- Also fixed the hardware paho-2.x bug (`pi_usb_monitor.py` now uses `CallbackAPIVersion.VERSION2`).

## Phase 4 — Audit trail ✅ (2026-08-22)

Every `/analyze` outcome is now persisted to an **append-only** trail, and a new
read endpoint exposes it. Audit is a sink — it never influences a decision.

- **`app/audit/records.py`** — `AuditRecord` (Pydantic), a flat row that collapses the four `AnalyzeResponse` objects into one queryable record (device, content_id, verified_match/action, risk score/level, decision, recommended_action, reasons, event_count, timestamp, auto `id`). `AuditRecord.from_analysis(...)` builds it from what `/analyze` already computed. Kept **out of the frozen `schemas/models.py`** (§13) since it isn't a §6/§7 wire contract.
- **`app/audit/store.py`** — `AuditStore`, SQLite-backed + thread-safe (mirrors `LocalRegistry`; `check_same_thread=False` + lock). **Append-only** (INSERT only — no update/delete). `record()` assigns the `id`; `list(device_id=, limit=)` returns newest-first; `count()`; indexed on `device_id`.
- **`app/deps.py`** — new `audit_store` singleton. Own DB (`SIGNGUARD_AUDIT_DB`, defaults `:memory:`) so it never shares a connection with the registry.
- **`app/main.py`** — `/analyze` writes one `AuditRecord` per call (after the decision); new **`GET /audit?device_id=&limit=`** returns the trail (newest first, `limit` clamped 1–1000).
- **Verified end-to-end (live HTTP, not just TestClient):** authorize → analyze a tampered update → `block`/`safe_fallback` → `GET /audit` returns the row (`verified_match=false`, `risk_score=40/medium`, `decision=block`).

## Live demo dashboard + MQTT orchestrator ✅ (2026-08-22)

Closed the loop the prototype was missing and wrapped it in a one-command web
demo. Previously events and the display existed but nothing connected them; now
a web button drives an attack all the way to the signage — on the **webpage and
the ESP32 together**.

- **`app/orchestrator.py`** — the missing Layer-2 MQTT brain. Subscribes to
  `signguard/events` + `signguard/content`, runs the shared pipeline, and
  publishes a `Command` to `signguard/commands` (deduped per device so the ESP32
  isn't spammed). `start_background()` (retrying connect + `loop_start`),
  `inject(scenario)` (demo trigger), and an `on_analysis` hook for the dashboard.
- **`app/pipeline.py`** — extracted `run_analysis()` so REST (`/analyze`) and the
  MQTT orchestrator share ONE decision path (they can never diverge). Writes the
  audit record for every decision regardless of transport.
- **`app/demo_scenarios.py`** — the baseline + **four attacks** (USB, credential,
  rogue Wi-Fi, physical tamper) in one place, with events re-timestamped to *now*
  so Track B's window always sees them. Used by both the web and terminal demos.
- **`app/web/` + dashboard** — `GET /` serves a self-contained dashboard (attack
  buttons, a live "signage display" that flips RENDER→BLOCKED and shows the
  rejected attacker content, a risk gauge, SHAP factors, and an event log). Live
  updates over a **WebSocket** (`/ws`); `POST /demo/attack/{id}` fires a scenario;
  `GET /demo/scenarios` lists them.
- **`run_demo.py`** — one command starts **everything**: native Mosquitto
  (LAN-open), the FastAPI app + in-process orchestrator, and opens the browser.
- **`demo_attacks.py`** — reliable terminal walkthrough (in-process, no broker/
  server needed) that prints all five scenarios + the audit trail. The safe
  fallback if the broker/hardware misbehaves on demo day.

**Verified end-to-end (live broker + HTTP):** triggering an attack on the webpage
publishes real telemetry → orchestrator escalates `render`→`safe_fallback` on
`signguard/commands` (ESP32 reacts) → dashboard display flips to BLOCKED → audit
trail records it. Confirmed for USB, rogue Wi-Fi, and physical tamper.

**Before/after story (hackathon framing) ✅ (2026-08-22):** the dashboard has a
**protection toggle**. `POST /demo/attack/{id}?protected=false|true`:
- **OFF (WITHOUT SignGuard)** → no verification, the attacker's content is shown
  on the signage (attacker succeeds).
- **ON (WITH SignGuard)** → SHA-256 mismatch → **BLOCK** + safe fallback +
  incident + risk breakdown + AI evidence + audit timeline; the ESP32 is driven
  via `signguard/commands`.
The three problem-statement attacks (malicious USB, unauthorized wireless,
compromised admin credentials) **all BLOCK** with SignGuard on — the credential
case makes the defense-in-depth point (a valid session still can't authorize
un-blessed content). Content is TNSTC Route 101 signage. Protected triggers run
the pipeline **in-process** (reliable, no broker needed for the webpage); the
broker/ESP32 add the physical response.

**Manual credential attack ✅ (2026-08-22):** USB and wireless are one-click
buttons; the **credential attack is performed manually** in the dashboard's
operator panel. `POST /demo/login` classifies the typed credentials
(`valid` / `default` / `invalid` — default/weak passwords are flagged), and
`POST /demo/publish` pushes the typed content. Logging in with `admin`/`admin`
is *granted but flagged*, and the malicious upload is still **blocked** because
its hash isn't authorized — proving authentication and content integrity are
different security properties. Helpers live in `app/demo_scenarios.py`
(`classify_credentials`, `login_events`, `manual_content`, `manual_scenario`).

**UI ✅ (2026-08-22):** reworked into a **SaaS-style console** — framed app shell,
top nav with the tagline *“Blockchain-based content integrity system for public
transport”*, segmented `SignGuard OFF | ON` toggle, signage shown as a device,
incident panel with status pills, risk-contribution bars, AI evidence, and an
audit timeline.

## Edge simulators (Phase 0) ✅

- **`edge_node/event_simulator.py`** — replays `sample_events.json` to `signguard/events`.
- **`edge_node/content_simulator.py`** — publishes content to `signguard/content`, `--mode authentic|tampered`.
- **`edge_node/display.py`** — subscribes `signguard/commands`, prints RENDER / SAFE_FALLBACK / ISOLATE.
- **`edge_node/mqtt_config.py`** — frozen topic constants + broker host/port (env-overridable).

## Hardware — final kit ✅ (adopted from the `files.zip` bundle + `SETUP.md`)

**Kit: Raspberry Pi + ESP32 + 16x2 I2C LCD + buzzer.** Role split (per `edge_node/hardware/SETUP.md`):
- **Pi = detection gateway** — real USB detection (pyudev) + software-simulated attacks → publishes `signguard/events`.
- **ESP32 = signage output node** — subscribes `signguard/commands`, drives LCD + buzzer. **No sensors.**
- **Laptop/Pi** — broker + Layer 2 (+ Layer 1 dashboard).

Files under `edge_node/hardware/`:
- **`pi_usb_monitor.py`** + **`pi_config.py`** — udev USB watch; serials vs `AUTHORIZED_USB_SERIALS`; publishes `usb_connected` / `unauthorized_usb` (§6).
- **`esp32/main.py`** (MicroPython) — `render`→"SignGuard: OK", `safe_fallback`→"** BLOCKED **" + beeps, `isolate`→"!! ISOLATED !!" + long beep. Wiring: LCD SDA=GPIO21 SCL=GPIO22, buzzer=GPIO26.
- **`esp32/config.example.py`** → copy to `config.py` (Wi-Fi, `BROKER_IP`, `DEVICE_ID=SG-ESP-001`, I2C/LCD, buzzer pin).
- **`esp32/i2c_lcd.py`, `esp32/lcd_api.py`** — standard community HD44780/PCF8574 driver (not edited).
- **`requirements.txt`** (Pi: paho-mqtt, pyudev) + **`SETUP.md`** (full flash/run/wiring/demo steps).

> ✅ **paho 2.x fixed:** `pi_usb_monitor.py` now uses `mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=...)`, so it runs on paho-mqtt 2.x. All Layer 2 / edge / hardware MQTT clients use the VERSION2 API.
>
> **LCD is attack-aware:** the command published to `signguard/commands` carries an optional `attack` label (e.g. `USB TAMPER`, `ROGUE WIFI`, `ADMIN BREACH`). `esp32/main.py` shows it on LCD line 2, so the sign names which attack was blocked; the buzzer beeps on `safe_fallback`, long-beeps on `isolate`.

**Superseded & removed** (earlier HW-3/HW-4 built before the kit was finalized): `esp32_tamper.py` (LDR/vibration sensor), `pi_display.py` (Tkinter kiosk), `config.py` (old ESP32 tamper config), `authorized_usb.json` (replaced by `pi_config.py`). The old `mosquitto/config/` dir was replaced by root `mosquitto.conf`.

---

## How to use the system (native Mosquitto)

One-time setup:
```powershell
python -m pip install -r requirements.txt      # FastAPI, sklearn, shap, paho-mqtt, pytest…
```

### ⭐ The panel demo — one command
```powershell
python run_demo.py      # starts broker + API + orchestrator, opens the dashboard
```
Toggle **SignGuard OFF/ON** and run the same attack to show before/after. USB &
wireless are buttons; the **credential attack is manual** (operator panel — try
`admin`/`admin`, then Publish). The signage display (and any connected ESP32)
flips RENDER → BLOCKED live, and the LCD names the attack. For hardware, flash the
ESP32 with `BROKER_IP=10.63.29.144` first (`edge_node/hardware/SETUP.md`).
Reliable fallback with no broker/hardware:
```powershell
python demo_attacks.py  # terminal walkthrough of all 5 scenarios + audit trail
```

**Terminal 1 — MQTT broker** (native, no Docker):
```powershell
& "C:\Program Files\mosquitto\mosquitto.exe" -c "D:\J.ACKTHON\mosquitto.conf" -v
```

**Terminal 2 — Layer 2 API (the brain):**
```powershell
python -m uvicorn app.main:app --reload        # Swagger UI at http://localhost:8000/docs
```

**Terminals 3–5 — software edge node (drive a demo without hardware):**
```powershell
python -m edge_node.display                              # console signage screen
python -m edge_node.event_simulator                      # replay data/sample_events.json
python -m edge_node.content_simulator --mode tampered    # push attacker content -> BLOCK
```

**REST demo (Track A, no broker needed):**
```powershell
# authorize "hello" (base64 aGVsbG8=), then POST /analyze a matching vs tampered update
curl -X POST localhost:8000/authorize -H "content-type: application/json" -d '{"content_id":"CNT-001","content_bytes_b64":"aGVsbG8="}'
```

**Hardware demo:** set `BROKER_IP = 10.63.29.144` in the Pi/ESP32 config, then follow `edge_node/hardware/SETUP.md` (broker + API + Pi USB events + ESP32 LCD/buzzer).

Sanity-check the broker anytime:
```powershell
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -t 'signguard/#' -v
```

---

## Remaining work (what's left to do)

**All build phases (0–4) + the live demo, before/after, manual credential attack,
attack-aware LCD, and paho 2.x fix are done.** What remains is real-hardware bring-up:

1. **Live hardware end-to-end** — flash the ESP32 (`BROKER_IP = 10.63.29.144`) and run
   the Pi USB monitor on the same Wi-Fi. Not runtime-testable on this dev machine
   (pyudev = Linux-only, ESP32 = MicroPython-only). Verify the LCD shows the attack
   labels (`USB TAMPER` / `ROGUE WIFI` / `ADMIN BREACH`) and the buzzer fires.
2. *(Optional)* Migrate the two `@app.on_event` hooks to FastAPI lifespan handlers
   (deprecation warning only).

---

## Verification status

- ✅ **41/41 tests pass** (`python -m pytest -q`): Track A + Track B + Phase 3 scoring + API + Phase 4 audit + demo layer (scenario build, dashboard serves, button list, before/after trigger, custom tampered content, **authorize-content + baseline renders on & off**) + manual credential attack (default creds flagged + content blocked, valid operator renders authorized content, publish-requires-login 403).

**Before/after + presenter-chosen content ✅ (2026-08-22):** the dashboard shows a
**BEFORE (authorized) vs AFTER (result)** signage pair. The presenter chooses
**both**: ① authorized "before" content (`POST /demo/authorize-content` re-authorizes
it in the registry and updates the BEFORE panel) and ② tampered "after" content
(sent with the attack). With SignGuard **OFF** an attack shows the tampered content;
with it **ON** the AFTER panel shows *“tamper detected — reverted to verified
content.”* **Baseline is not an attack**, so it renders on both ON and OFF (fixes
the earlier on/off-not-working issue). Payload builders now take explicit
`authentic_text`/`attacker_text`. ESP32 LCD wording aligned to NORMAL / TAMPER
DETECTED / CRITICAL ALERT. **`HARDWARE.md`** (repo root) is the standalone hardware
guide (kit roles, wiring, flash/config, LCD attack-label table, demo run,
troubleshooting).
- ✅ Contract-checked: ESP32 command states == `CommandType` {render, safe_fallback, isolate}; `pi_usb_monitor` events validate against §6.
- ⚠️ Hardware **not runtime-tested here** — pyudev is Linux-only; ESP32 `main.py`/`i2c_lcd`/`lcd_api` are MicroPython-only. Need real devices + a running broker.
- ✅ **paho 2.x** — fixed in `pi_usb_monitor.py` (VERSION2 API); consistent across all MQTT clients.
- ✅ **Native Mosquitto 2.1.2 installed** (replaces Docker) and verified listening on `0.0.0.0:1883`. One elevated step pending to sideline the auto-started localhost-only service (see Broker section). Track A is also demoable over REST without a broker (`data/`-first per §12).

---

## Repository layout (current)

```
J.ACKTHON/
├── CLAUDE.md                     # frozen source of truth
├── PROGRESS.md                   # this file
├── README.md
├── requirements.txt
├── docker-compose.yml            # broker (mounts ./mosquitto.conf)
├── mosquitto.conf                # broker config, 0.0.0.0:1883
├── .gitignore
├── data/sample_events.json
├── app/                          # LAYER 2 (the brain)
│   ├── main.py  deps.py
│   ├── schemas/  (models.py)                 ✅
│   ├── registry/ (base.py, local.py)         ✅
│   ├── authorization/ (authorize.py)         ✅
│   ├── verification/ (verify.py)             ✅
│   ├── fallback/ (safe.py)                   ✅
│   ├── decision/ (engine.py)                 ✅
│   ├── ingestion/ (store.py, subscriber.py)  ✅
│   ├── features/  (engineer.py)              ✅
│   ├── ml_engine/ (model.py)                 ✅
│   ├── xai/ (explain.py)                     ✅
│   ├── scoring/ (score.py)                   ✅
│   ├── audit/ (records.py, store.py)         ✅
│   ├── pipeline.py  (shared run_analysis)    ✅
│   ├── orchestrator.py (MQTT brain)          ✅
│   ├── demo_scenarios.py (baseline+4 attacks)✅
│   ├── web/ (dashboard.py, live.py)          ✅
├── edge_node/                    # IoT component (MQTT only, never merged)
│   ├── event_simulator.py  content_simulator.py  display.py  mqtt_config.py
│   └── hardware/                 # final kit (from files.zip bundle)
│       ├── SETUP.md  pi_config.py  pi_usb_monitor.py  requirements.txt
│       └── esp32/ (main.py, config.example.py, i2c_lcd.py, lcd_api.py)
├── run_demo.py                   # one-command launcher (broker+API+browser)
├── demo_attacks.py               # terminal walkthrough (in-process)
└── tests/ (…track_a, track_b, api, audit, demo)   ✅ 35 passing
```

---

> **Next steps** are consolidated in the **Remaining work** section above.
