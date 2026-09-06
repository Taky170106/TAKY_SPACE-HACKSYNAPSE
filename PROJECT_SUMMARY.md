# SignGuard AI — Project Summary
### Blockchain-based content integrity system for public transport

**What it does:** stops public-transport digital signage from ever showing
tampered or attacker-controlled content. Every content update is verified by a
cryptographic fingerprint (SHA-256) against an authorized record; anything that
doesn't match is blocked and a safe fallback is shown, while an AI layer scores
and explains the surrounding attack behaviour.

---

## Components we are using

| Component | Qty | Purpose |
|-----------|-----|---------|
| ESP32 dev board | 1 | IoT signage controller; Wi-Fi + MQTT |
| 16×2 I²C LCD | 1 | Shows security status / alert |
| Active buzzer | 1 | Audible alarm on a critical threat |
| Breadboard + jumper wires | 1 set | Wiring |
| USB cable | 1 | Power + program the ESP32 |
| Laptop | 1 | Runs the MQTT broker + SignGuard backend + dashboard |
| *(optional)* Raspberry Pi | 1 | Real USB-insertion detection |

---

## How it works (end to end)

```
Attack (USB / Wi-Fi / admin creds)  ->  SHA-256 integrity check
   -> hash mismatch -> BLOCK + safe fallback
   -> Layer 2: AI anomaly detection -> risk score -> XAI explanation -> decision
   -> MQTT command  ->  ESP32 (LCD + buzzer)  &  big-screen signage
```

- **Content integrity (SHA-256)** decides block/allow — deterministic, never waits for AI.
- **AI (Isolation Forest)** assesses attack context; **XAI** explains why; **risk score** grades severity.
- **MQTT (Mosquitto)** carries events and commands in real time.
- **ESP32 + LCD + buzzer** is the physical signage response.

---

## What we have built (done)

- ✅ **Layer 2 backend** (FastAPI): authorize → verify (SHA-256) → AI risk + XAI → decision.
- ✅ **Append-only audit trail** of every decision (`/audit`).
- ✅ **MQTT orchestrator** — turns events into commands that drive the hardware.
- ✅ **Live web console** with **before/after** and a **SignGuard ON/OFF** toggle:
  - OFF → attacker's content is shown; ON → tampered update blocked, reverts to verified.
  - Choose the **before (authorized)** and **after (tampered)** content.
  - Incident panel, risk-contribution bars, AI evidence, audit timeline.
- ✅ **Three attacks:** Malicious USB, Unauthorized wireless (buttons) + **manual credential attack** (log in with `admin`/`admin` and try to publish).
- ✅ **Big-screen passenger signage** page (`/signage`) for projecting to the audience.
- ✅ **ESP32 firmware** — LCD shows `SYSTEM SECURE` / `TAMPER DETECTED` + the attack name, buzzer alarms. paho-mqtt 2.x fixed.
- ✅ **41/41 automated tests passing.**

**Remaining:** flash the real ESP32/Pi and run the physical demo (software path already covers everything).

---

## How to run

```powershell
python run_demo.py            # starts broker + backend + presenter dashboard
```
- **Presenter dashboard:** http://localhost:8000/
- **Big screen (project this):** http://localhost:8000/signage  (press F11)
- Terminal-only fallback: `python demo_attacks.py`

Hardware: see **`HARDWARE.md`** (wiring, flashing, `BROKER_IP`, LCD labels).

---

## 5-minute demo flow

1. Show the big **/signage** screen — genuine TNSTC Route 101 content, "System Secure".
2. **SignGuard OFF** → run **Malicious USB** → the big screen shows the attacker's fake message.
3. **SignGuard ON** → run the same attack → **TAMPERING BLOCKED**, screen reverts to verified content; ESP32 LCD shows `TAMPER DETECTED / USB TAMPER` + buzzer.
4. **Manual credential attack:** log in `admin`/`admin` (flagged), publish "NEXT BUS CANCELLED" → blocked; LCD shows `ADMIN BREACH`.
5. Open the incident → risk score, contribution bars, AI evidence, audit trail.

**One line:** SignGuard verifies content → blocks tampering → the AI analyzes and explains → MQTT delivers the alert → the ESP32 and the big screen physically show the security response.
