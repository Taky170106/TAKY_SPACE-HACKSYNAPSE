# SignGuard AI — Layer 2 + Edge Node
### Blockchain-based content integrity system for public transport

Protects public-transport digital signage from showing tampered / attacker-controlled
content. See `CLAUDE.md` for the frozen design (source of truth).

**Core rule:** content integrity is deterministic (SHA-256) and never waits for ML.
- Hash **match** → verified → render.
- Hash **mismatch** → tampered → block instantly + safe fallback.

The AI (Isolation Forest) only assesses *attack context*; SHAP explains the AI —
neither decides content integrity.

## Build status
- ✅ **Phase 0** — schemas, FastAPI skeleton, sample events, edge simulators, display client, broker config.
- ✅ **Phase 1 (Track A)** — authorization → verification → decision → safe fallback. *Demoable.*
- ✅ **Phase 2 (Track B)** — ingestion → features → IsolationForest → SHAP (wired into `/analyze`).
- ✅ **Hardware kit** — Pi USB monitor + ESP32 LCD/buzzer output node. See `edge_node/hardware/SETUP.md`.
- ✅ **Phase 3** — risk scoring → decision fusion (`/analyze` returns all 4 fields).
- ✅ **Phase 4** — append-only audit trail; every `/analyze` decision is persisted and exposed via `GET /audit`.

See `PROGRESS.md` for the detailed status.

## Setup
```bash
python -m pip install -r requirements.txt      # scikit-learn/shap only needed from Phase 2
```

## ⭐ Live attack demo (one command)
```bash
python run_demo.py     # starts Mosquitto + API + orchestrator, opens the dashboard
```
**Before vs after:** toggle **SignGuard OFF** and run an attack — the attacker's
content is shown. Toggle **ON** and run the *same* attack — it's blocked, safe
fallback activates, and the incident is scored + audited.

- **Scenario buttons:** Malicious USB, Unauthorized wireless.
- **Manual credential attack:** log into the operator panel (try `admin` / `admin`)
  and publish content — a valid-but-default session still can't push content whose
  hash isn't authorized (defense in depth).

Use the **“Tampered content to display”** box to choose what a tampered update
tries to show. The webpage signage display — and any connected **ESP32 LCD/buzzer**
— react in real time; the LCD's second line names the blocked attack (e.g.
`USB TAMPER`, `ADMIN BREACH`). No broker/hardware handy? Use the terminal
walkthrough: `python demo_attacks.py`.

**Hardware:** see **`HARDWARE.md`** for the full Pi + ESP32 guide (wiring, flashing,
broker IP, LCD labels, demo run).

## Run the tests
```bash
python -m pytest -q
```

## Run Layer 2 (the API)
```bash
python -m uvicorn app.main:app --reload
# docs at http://localhost:8000/docs
```

### Track A demo over REST
```bash
# 1) Transport authority authorizes content (base64 of "hello" shown for brevity)
curl -X POST localhost:8000/authorize \
  -H "content-type: application/json" \
  -d '{"content_id":"CNT-001","content_bytes_b64":"aGVsbG8="}'

# 2) Analyze a matching update -> decision: render
# 3) Analyze a tampered update -> decision: block + safe_fallback
# 4) Every /analyze is recorded — read the trail:
curl localhost:8000/audit                       # newest first
curl "localhost:8000/audit?device_id=SG-RNP-001&limit=20"
```

## Run the software edge node (needs the MQTT broker)
```bash
# Native Mosquitto (Windows, no Docker):
# & "C:\Program Files\mosquitto\mosquitto.exe" -c mosquitto.conf -v
docker compose up -d                           # or start Mosquitto on :1883 via Docker
python -m edge_node.display                     # software signage screen (console)
python -m edge_node.event_simulator             # replay data/sample_events.json
python -m edge_node.content_simulator --mode tampered   # push attacker content
```

The edge node and Layer 2 **only** communicate over MQTT (topics in `CLAUDE.md §4`);
they are never run in the same process.

## Run the real hardware kit (Pi + ESP32 + LCD + buzzer)
See **`edge_node/hardware/SETUP.md`** for the full flash/wire/run/demo walkthrough.
The Pi publishes real `unauthorized_usb` events; the ESP32 drives the LCD + buzzer
from Layer 2's commands. The software simulators above stay as a stage fallback.
