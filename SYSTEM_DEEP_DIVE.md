# SignGuard — SYSTEM DEEP DIVE (code-grounded)

> This document describes **only what the code in this repo actually does**. Where
> the slides/workflow docs disagree, the code wins and the discrepancy is noted.
> Anything not present in code is marked **[NOT IMPLEMENTED / PLANNED]**.

There are **two independent stacks** in this repo:

- **A) `app/` — the FastAPI "Layer 2" brain + web console.** Started by `run_demo.py`.
  Does SHA-256 verification, the AI (Isolation Forest + SHAP), risk scoring, the
  decision engine, an audit trail, an in-process MQTT orchestrator, and serves the
  dashboard + signage web pages.
- **B) `usb_demo/` — a standalone ESP8266 hardware demo.** Driven by
  `usb_demo/laptop/demo_trigger.py`. Pure SHA-256 (text) + MQTT + ESP8266 firmware.
  **No FastAPI, no AI.** This is the path that lights up the physical LCD/LEDs/buzzer.

They share one MQTT topic (`signguard/commands`) and one `DEVICE_ID` (`SG-RNP-001`),
so a single flashed ESP reacts to either stack.

---

## 1. What actually runs — processes started by `run_demo.py`

`run_demo.py` (`main()`):
1. `_start_broker()` — if nothing is on `localhost:1883`, it spawns **Mosquitto**
   as a subprocess: `mosquitto.exe -c mosquitto.conf -v` (path auto-found; env
   `MOSQUITTO_EXE` overrides). If `:1883` is already open it reuses it.
2. A background thread `_open_browser()` polls `http://localhost:<port>/` and opens
   the browser once it responds.
3. `uvicorn.run("app.main:app", host="0.0.0.0", port=8000)` — the FastAPI app.

On FastAPI startup, `app/main.py` `@app.on_event("startup") _start_orchestrator()`:
- calls `_authorize_baseline()` (`app/orchestrator.py`) — hashes the demo baseline
  content into the registry so genuine content renders,
- constructs `Orchestrator(...)` and calls `start_background()` which connects a
  paho MQTT client and **subscribes to `signguard/events` + `signguard/content`**.

So one `python run_demo.py` gives you: **Mosquitto** + **Uvicorn/FastAPI (app.main)**
+ the **in-process MQTT orchestrator** + a **browser tab**. The ESP8266 hardware demo
(`usb_demo/`) is a **separate** manual path (see §11 / DEMO SCOPE).

**[NOT IMPLEMENTED / PLANNED]:** `run_demo.py` does **not** start any QEMU VM, Kali
image, USB detector, or the `usb_demo/` scripts. Those are run by hand.

---

## 2. Physical vs virtual architecture

| Element | Physical / Virtual | Grounded in |
|---|---|---|
| Laptop (broker + FastAPI + dashboard) | Physical | `run_demo.py`, `mosquitto.conf` |
| **NodeMCU ESP-12E (ESP8266)** output node | **Physical** | `usb_demo/esp8266/main.py`, `config.py` (real Wi-Fi `GCRG IT`, `BROKER_IP=192.168.7.174`) |
| 16×2 I²C LCD (addr 0x27) | Physical | `esp8266/config.py` `LCD_ADDR`, `i2c_lcd.py` |
| Buzzer (GPIO14/D5), Green LED (GPIO12/D6), Red LED (GPIO13/D7) | Physical | `esp8266/config.py`, `esp8266/main.py update_actuators()` |
| CP210x USB-serial driver (`usb_demo/esp8266/driver/extracted/…`) | Physical (flashing driver) | files present |
| ESP32 variant (`usb_demo/esp32/`, `edge_node/hardware/esp32/`) | Physical, **alternate/unused for the live wiring** | files present; the wired board is the ESP8266 |
| QEMU VM, Kali Linux, virtual USB `pendrive.img` | **[NOT IMPLEMENTED / PLANNED]** | `grep -riE "qemu|kali|pendrive|\.img"` → **no matches** in code |
| Raspberry Pi USB monitor (`edge_node/hardware/pi_usb_monitor.py`) | Physical, Linux-only, **not started by run_demo** | file present, uses `pyudev` |

**Discrepancy:** slides mention ESP32 and a virtual USB lab (QEMU/Kali/pendrive).
The wired, configured board is the **ESP8266 ESP-12E**, and there is **no virtual lab
in the repo** — the "USB attack" is *simulated in software* by `demo_trigger.py`.

---

## 3. Every API endpoint (`app/main.py`)

All routes are on the FastAPI `app`. JSON bodies are Pydantic models from
`app/schemas/models.py`.

| Method | Path | Input | Calls | Output |
|---|---|---|---|---|
| GET | `/health` | — | — | `{"status":"ok","service":"signguard-layer2"}` |
| POST | `/authorize` | `{content_id, content_bytes_b64, authorized_by?}` | `authorize_content()` (`app/authorization/authorize.py`) → `registry.authorize()` | `{content_id, content_hash, authorized_by}` |
| POST | `/analyze` | `AnalyzeRequest{device_id, content_update?, events[]}` | `run_analysis()` (`app/pipeline.py`) | `AnalyzeResponse{verification_result, risk_score, xai_explanation, decision}` |
| GET | `/fallback` | — | `safe_fallback_content()` (`app/fallback/safe.py`) | `{"content": "...safe text..."}` |
| GET | `/audit` | `?device_id=&limit=` | `audit_store.list()` (`app/audit/store.py`) | `list[AuditRecord]` |
| GET | `/` | — | `dashboard.render()` (`app/web/dashboard.py`) | HTML console |
| GET | `/signage` | — | `signage.render()` (`app/web/signage.py`) | HTML full-screen sign |
| GET | `/demo/scenarios` | — | reads `SCENARIOS`/`ORDER` (`app/demo_scenarios.py`) | list of scenario cards |
| POST | `/demo/attack/{scenario_id}` | `AttackRequest{protected, content?}` | in-process `run_analysis()` (+ `orchestrator.publish_command` if broker) | `{decision, risk, hardware_notified,…}` |
| POST | `/demo/authorize-content` | `{content}` | `authorize_content()` + broadcast | `{authorized, authentic_text}` |
| POST | `/demo/login` | `{user, password}` | `classify_credentials()` (`app/demo_scenarios.py`) | `{granted, flag, note}` |
| POST | `/demo/publish` | `{content, protected}` | `run_analysis()` + broadcast | `{decision, risk, credential_flag,…}` |
| WS | `/ws` | — | `ConnectionManager` (`app/web/live.py`) | pushes `status` + `decision` JSON |

Callers: the **web console** (`app/web/dashboard.py` JS) calls `/demo/*` and `/ws`;
the **signage page** (`app/web/signage.py`) uses `/ws` only; `/authorize` + `/analyze`
+ `/audit` are the REST contract (also exercised by `tests/`).

---

## 4. MQTT internals

Topic constants: `app/orchestrator.py` (`TOPIC_EVENTS`, `TOPIC_CONTENT`,
`TOPIC_COMMANDS`), `edge_node/mqtt_config.py`, `usb_demo/laptop/mqtt_config.py`,
`usb_demo/esp8266/config.py`.

| Topic | Publisher(s) | Subscriber(s) | Payload (schema) |
|---|---|---|---|
| `signguard/events` | `edge_node/event_simulator.py`, `edge_node/hardware/pi_usb_monitor.py`, `app/main.py` demo inject | `Orchestrator._handle_event` (`app/orchestrator.py`), `app/ingestion/subscriber.py IngestionService` | `SecurityEvent{device_id,event_type,authorized,timestamp,data}` |
| `signguard/content` | `edge_node/content_simulator.py` | `Orchestrator._handle_content` | `ContentUpdate{device_id,content_id,content_bytes_b64,source,timestamp}` |
| `signguard/commands` | `Orchestrator.publish_command` (`app/`), **`usb_demo/laptop/demo_trigger.py publish_command`** | `edge_node/display.py`, **`usb_demo/esp8266/main.py on_command`**, `edge_node/hardware/esp32/main.py` | `Command{device_id,command,timestamp}` (+ optional `attack`, and `line1/line2` from demo_trigger) |

Example command bytes actually published by `demo_trigger.py`:
```json
{"device_id":"SG-RNP-001","command":"safe_fallback","timestamp":"2026-...Z"}
```
and for authorized content it adds `"line1"/"line2"` for the LCD.

**Note:** the `app/` web "SignGuard OFF" (unprotected) path in `/demo/attack`
**does not publish MQTT** — it only broadcasts to the browser over `/ws`. The
firmware's `"unverified"` LCD state therefore has **no publisher** in `app/`.

---

## 5. SHA-256 integrity

**Two implementations (by stack):**

**A) `app/` stack**
- Generation: `sha256_hex(content_bytes)` = `hashlib.sha256(bytes).hexdigest()`
  (`app/authorization/authorize.py`).
- Store: `LocalRegistry` (`app/registry/local.py`) → SQLite table `content_records
  (content_id PK, content_hash, authorized_by, timestamp)`. **Default DB path is
  `":memory:"`** (`app/deps.py`, `SIGNGUARD_DB` env overrides) → **authorizations do
  not persist across restart** unless the env var points to a file.
- Comparison: `verify_content()` (`app/verification/verify.py`):
  ```python
  computed  = sha256_hex(base64.b64decode(update.content_bytes_b64))
  authorized = registry.get_authorized_hash(update.content_id)
  match = authorized is not None and computed == authorized
  action = "render" if match else "block"
  ```
  **Unknown `content_id` → `authorized is None` → mismatch → block** (never renders
  unauthorized bytes).

**B) `usb_demo/` stack (the hardware demo)**
- `authorize_content.py`: hashes the **file bytes** of `data/authorized_content.txt`
  → writes `data/authorized_hash.json` (`content_id, content_hash, authorized_by,
  timestamp`).
- `demo_trigger.py`: `sha256_of_text(text)` hashes the **UTF-8 text string**;
  `--unauthorized` compares the attacker's hash to `authorized_hash.json` and, on
  mismatch, publishes `safe_fallback`. (Minor discrepancy: `authorize_content.py`
  hashes file bytes vs `demo_trigger.store_authorized` hashes the text — the demo is
  self-consistent when you use `demo_trigger --authorized`.)

**Match path:** `render` (+`line1/line2` in usb_demo). **Mismatch path:** `block`/
`safe_fallback` → safe fallback shown.

---

## 6. AI internals (`app/` only)

- **Features** (`app/features/engineer.py`, `FEATURE_ORDER`, exactly 7):
  `failed_logins_5min, unknown_usb_detected, wireless_anomaly,
  content_hash_mismatch, events_per_minute, time_since_authorized_update,
  device_trust_score`. Window = **300 s** (`WINDOW_SECONDS`). `device_trust_score`
  starts at 1.0 minus penalties (`_TRUST_PENALTY`: mismatch −0.30, usb −0.20,
  tamper −0.25, wireless −0.15, default-creds −0.15, login-fail −0.05).
- **Model** (`app/ml_engine/model.py`, `AnomalyModel`):
  `IsolationForest(n_estimators=200, contamination=0.03, random_state=42)`, trained
  **once at construction** on a 1000-row synthetic healthy baseline (`_normal_baseline`,
  seeded RNG 42).
  Anomaly score = `1 / (1 + exp(decision_function / sigma))` (calibrated 0–1).
- **Score → risk** (`app/scoring/score.py`, `compute_risk`, `WEIGHTS`):
  `content_hash_mismatch +40, unauthorized_usb +20, default_credential_attempt +15,
  wireless_anomaly +10, ai_anomaly = round(15 × anomaly_score)`, capped at 100.
  Levels: low ≤24, medium ≤49, high ≤79, critical ≥80.
- **SHAP** (`app/xai/explain.py`, `ShapExplainer`): `shap.TreeExplainer(forest)`,
  impacts sign-flipped (`_ANOMALY_SIGN = -1.0`) so +impact = toward anomaly; returns
  top-k (default 5) factors.

**The AI never blocks** — it only produces `risk_score` + `xai_explanation`
(`app/pipeline.py run_analysis`). **[NOT USED in `usb_demo/`]** — the hardware demo
has no AI at all.

---

## 7. Decision engine (`app/decision/engine.py`, `decide()`)

Thresholds (module constants): `RISK_THRESHOLD = 50`, `CRITICAL_THRESHOLD = 80`.

```
if verification is not None and not verification.match:      # hash MISMATCH
        return BLOCK, recommended_action = safe_fallback     # (first, ignores AI)
score = risk.score if risk else 0
if score >= 80:  return ISOLATE, recommended_action = isolate
if score >= 50:  return BLOCK,   recommended_action = safe_fallback
else:            return RENDER,  recommended_action = render
```

Safe-fallback content: `safe_fallback_content()` (`app/fallback/safe.py`); the edge
shows its own local fallback text regardless (see §10), so a compromised channel
can't suppress it.

---

## 8. Audit trail (`app/audit/`)

- Written in `app/pipeline.py run_analysis()` via `audit_store.record(AuditRecord.from_analysis(...))`
  **on every `/analyze` call** (after the decision).
- Fields (`AuditRecord`, `app/audit/records.py`): `id, timestamp, device_id,
  content_id, verified_match, verification_action, risk_score, risk_level,
  decision, recommended_action, reasons[], event_count`.
- Store (`app/audit/store.py AuditStore`): SQLite table `audit_records`,
  **INSERT-only** (no update/delete), indexed on `device_id`. **Default DB
  `":memory:"`** (`SIGNGUARD_AUDIT_DB` overrides) → not persistent by default.
- Read via `GET /audit`. **`usb_demo/` has no audit trail.**

---

## 9. Dashboard + signage (`app/web/`)

- `GET /` → `dashboard.render()` (`app/web/dashboard.py`): the console (attack
  buttons, ON/OFF toggle, before/after, manual credential panel). Its JS calls
  `/demo/scenarios`, `/demo/attack/{id}`, `/demo/login`, `/demo/publish`, and opens
  `/ws`.
- `GET /signage` → `signage.render()` (`app/web/signage.py`): full-screen sign; JS
  opens `/ws` and switches on `p.mode`:
  - `render` → shows `p.authentic_text` (verified content),
  - `blocked` → shows the safe fallback + "TAMPERING DETECTED — REVERTED",
  - `unprotected` → shows `p.attacker_text` (SignGuard OFF).
- `/ws` (`app/web/live.py ConnectionManager`) pushes `{"type":"status",broker}` on
  connect and `{"type":"decision",...}` per analysis. Payload built by
  `build_decision_payload` / `build_unprotected_payload` (`app/web/live.py`).
- **Verified vs fallback selection is in the browser JS** based on `mode` — it is not
  the ESP firmware choosing content for the web sign.

---

## 10. ESP firmware state machine (`usb_demo/esp8266/main.py`)

1. **Boot:** init SoftI2C LCD, buzzer, green/red LED (all off); `lcd_show("SignGuard","starting...")`.
2. **Wi-Fi:** `connect_wifi()` blocks until `WLAN` connected (creds from `config.py`).
3. **MQTT:** `connect_mqtt()` → `MQTTClient(DEVICE_ID, BROKER_IP)`, `set_callback(on_command)`,
   `subscribe(TOPIC_COMMANDS)`.
4. **Default:** `set_mode("render")` → LCD `SYSTEM SECURE / Content verified`.
5. **Loop:** `client.check_msg()` (non-blocking) + `update_actuators()` every 20 ms.
6. **Message parse** (`on_command`): JSON; ignore unless `device_id` ∈ {ours, None, "all"};
   if `command` in `STATES` → `set_mode(cmd, line1, line2)`.
7. **LCD/actuator states** (`update_actuators`):
   - `render` → green LED on, red off, buzzer off.
   - `safe_fallback` → green off; red LED **and buzzer blink together** at 500 ms
     (250 ms on/off) — `blink = (t % 500) < 250`.
   - `isolate` → red solid, buzzer beeps `(t % 1200) < 800`.
   - `unverified` → all off (LCD shows attacker text). **(no `app/` publisher — §4)**
8. **Reconnect:** on `OSError`, `lcd_show("...reconnecting..")`, retry.

**Discrepancy vs slides:** there is **no 5-second buzzer timer and no automatic
return to NORMAL**. The board stays in whatever mode the last command set; the buzzer
simply blinks while the mode is `safe_fallback`. It returns to `render` only when a
`render` command arrives.

---

## 11. One complete end-to-end trace — a USB/tamper attack

**What the repo actually supports** is a *software-simulated* tamper (no physical
USB read). Two real routes:

**Route B — hardware demo (`usb_demo/`, the one that drives the physical sign):**
1. Operator ran `authorize_content.py` (or `demo_trigger.py --authorized`) → hash in
   `usb_demo/laptop/data/authorized_hash.json` (currently `91d30028…277f`).
2. Presenter runs `python demo_trigger.py --unauthorized "BUS 101 CANCELLED|LEAVE THE AREA"`.
3. `do_unauthorized()` → `sha256_of_text(attacker_text)` → compares to
   `authorized["content_hash"]` → **mismatch**.
4. `publish_command("safe_fallback")` → paho publishes to `signguard/commands` on the
   broker (`mqtt_config.BROKER_HOST:1883`).
5. ESP8266 `on_command()` parses it → `set_mode("safe_fallback")`.
6. `update_actuators()` → **red LED + buzzer blink**, LCD `TAMPER DETECTED / Update blocked`.
   (No AI, no audit in this route.)

**Route A — `app/` software stack (dashboard "Malicious USB"):**
1. Browser `POST /demo/attack/usb` → `app/main.py trigger_attack()`.
2. Builds a scenario (`app/demo_scenarios.py`, tampered `ContentUpdate` + events
   incl. `unauthorized_usb`, `content_hash_mismatch`) → `run_analysis()` (`app/pipeline.py`).
3. `verify_content()` → mismatch; `build_feature_vector` → `AnomalyModel.score` →
   `ShapExplainer.explain` → `compute_risk` (~71/high) → `decide()` → **BLOCK / safe_fallback**.
4. `audit_store.record(...)` writes the row.
5. If broker connected, `orchestrator.publish_command(device, safe_fallback, attack="USB TAMPER")`
   → `signguard/commands` → ESP8266 reacts (same as above, LCD line 2 = attack label).
6. `build_decision_payload` broadcast on `/ws` → dashboard + `/signage` flip to BLOCKED.

**[NOT IMPLEMENTED / PLANNED]:** a real USB insertion being read on the signage
device and its file hashed. `edge_node/hardware/pi_usb_monitor.py` (Linux/pyudev)
detects USB *insertion events* and publishes `unauthorized_usb` to `signguard/events`,
but it does **not** read/hash the pendrive's content, and it is not launched by
`run_demo.py`.

---

## DEMO SCOPE (what runs end-to-end today ≈ 20–30%)

**Slice 1 — Software brain + web console + AI (no hardware needed):**
```
cd D:\J.ACKTHON
python -m pip install -r requirements.txt        # first time
python run_demo.py                               # broker + FastAPI + browser
```
Show: open `http://localhost:8000/` → toggle **SignGuard OFF**, click **Malicious USB**
(attacker text shows) → toggle **ON**, click it again (BLOCKED, risk score, SHAP,
audit). Open `http://localhost:8000/signage` for the big screen. Manual credential
attack: log in `admin`/`admin`, Publish → blocked. `GET /audit` shows the log.

**Slice 2 — Physical ESP8266 sign (real LCD/LED/buzzer):**
```
# broker running (run_demo.py or mosquitto). ESP8266 flashed with usb_demo/esp8266/*
cd D:\J.ACKTHON\usb_demo\laptop
python demo_trigger.py --show            # sign shows authorized content (green)
python demo_trigger.py --unauthorized    # HASH MISMATCH -> red LED + buzzer, LCD TAMPER
python demo_trigger.py --authorized "NEXT BUS 11:00|PLATFORM 2"   # accepted, green
```
Requires: ESP8266 flashed (`config.py` Wi-Fi + `BROKER_IP` = laptop LAN IP), laptop and
ESP on the same Wi-Fi, broker reachable on `:1883`.

**Verified working:** SHA-256 verify/mismatch, AI risk + SHAP, decision engine, audit
trail, MQTT command → ESP8266 LCD/LED/buzzer, dashboard + signage, 4 pytest suites
(`tests/test_track_a|track_b|api|audit|demo|scoring`).

## NOT YET WIRED (do not claim as live)
- **QEMU + Kali + virtual USB `pendrive.img` lab** — not in the repo at all.
- **Reading & hashing an actual inserted USB's content** on the device (only insertion
  *events* exist, Linux-only, not auto-started).
- **Digital signatures / PKI** — no signing anywhere.
- **On-chain / distributed blockchain registry** — the "ledger" is SQLite
  (`app/`) or a JSON file (`usb_demo/`), in-memory by default in `app/`.
- **Persistence by default** — `app/` registry + audit are `":memory:"` unless
  `SIGNGUARD_DB` / `SIGNGUARD_AUDIT_DB` are set.
- **ESP32 board** — code exists (`usb_demo/esp32/`, `edge_node/hardware/esp32/`) but
  the wired/configured board is the **ESP8266 ESP-12E**.
- **Firmware auto-reset / 5-second buzzer timeout** — not implemented.
