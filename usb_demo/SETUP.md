# SignGuard AI — Content-Integrity Demo (IoT only, laptop-driven)

No Raspberry Pi. No FastAPI. No USB stick. The laptop plays "someone changing
the sign's content"; a NodeMCU ESP-12E (ESP8266) shows the physical result:
an **authorized** change updates the sign, an **unauthorized** change is blocked
with a buzzer + red LED. ~45 minutes end to end.

```
usb_demo/
├── docker-compose.yml + mosquitto.conf       (broker)
├── laptop/
│   ├── requirements.txt
│   ├── mqtt_config.py
│   ├── authorize_content.py      run ONCE before the demo
│   ├── demo_trigger.py           run LIVE during the demo
│   └── data/
│       ├── authorized_content.txt    the real transit message
│       ├── usb_attack_content.txt    the attacker's payload
│       └── authorized_hash.json      created by authorize_content.py
└── esp32/
    ├── config.example.py   -> copy to config.py
    ├── main.py
    ├── i2c_lcd.py
    └── lcd_api.py
```

---

## ⭐ NodeMCU ESP-12E (ESP8266) — YOUR BOARD (use this, not the ESP32 steps)

You have a NodeMCU ESP-12E (ESP8266), so use the ready-made **`esp8266/`** folder
and its one-command flasher. The Steps 1–5 below are the generic ESP32 version;
this block replaces Steps 1 and 3 for your board.

**Wiring (NodeMCU D-labels → GPIO):**
```
LCD  SDA -> D2      SCL -> D1      VCC -> 3V3 (or VIN)   GND -> GND
Buzzer +  -> D5                    -  -> GND
Green LED -> D6 -> 220ohm -> LED(+)   LED(-) -> GND
Red   LED -> D7 -> 220ohm -> LED(+)   LED(-) -> GND
```

**Flash + upload (one command):**
```powershell
# 1. install the CH340 USB-serial driver if the board doesn't appear as a COM port
# 2. copy the config template and edit it:
cd usb_demo\esp8266
copy config.example.py config.py      # edit WIFI_SSID / WIFI_PASS / BROKER_IP
# 3. run the flasher (auto-detects the port, or pass -Port COM5):
powershell -ExecutionPolicy Bypass -File flash.ps1
```
It erases the board, writes MicroPython v1.28.0 (already downloaded in
`esp8266/firmware/`), and uploads `umqtt`, the LCD drivers, `config.py`, and
`main.py`. Power-cycle → LCD shows **SYSTEM SECURE**, green LED on.

Then continue at **Step 2 (broker)** and **Step 4/5** below. The laptop side
(`demo_trigger.py`, the full-brain path) is identical — the board is just MQTT.

---

## Step 1 — Wire the ESP32 (15 min)   *(generic — ESP8266 users see the block above)*

```
LCD (I2C backpack): VCC -> 5V(VIN)   GND -> GND   SDA -> GPIO21   SCL -> GPIO22
Buzzer:              +  -> GPIO26         -  -> GND
Green LED: GPIO27 -> 220ohm resistor -> LED(+) -> LED(-) -> GND
Red LED:   GPIO14 -> 220ohm resistor -> LED(+) -> LED(-) -> GND
```
All grounds common on the breadboard. Power the ESP32 via USB from the power
bank or your laptop.

---

## Step 2 — Start the broker (2 min)

On the laptop:
```
docker compose up -d
```
Find your laptop's LAN IP (the ESP32 needs it): `hostname -I` (Linux/Mac) or
`ipconfig` (Windows). Put it in `esp32/config.py` as `BROKER_IP` in Step 3.

Optional but recommended — watch every message live in a second terminal:
```
mosquitto_sub -h localhost -t 'signguard/#' -v
```

---

## Step 3 — Flash the ESP32 (15 min, one time)

```
pip install esptool mpremote
esptool.py --chip esp32 erase_flash
esptool.py --chip esp32 write_flash -z 0x1000 esp32-<version>.bin
mpremote mip install umqtt.simple
```
Find the LCD's I2C address (usually 0x27, sometimes 0x3F):
```python
# in an mpremote REPL
from machine import Pin, I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
print([hex(a) for a in i2c.scan()])
```
Set `LCD_ADDR` in config.py to match if it's not 0x27.

Copy config, then upload all four files:
```
cp esp32/config.example.py esp32/config.py     # edit WIFI_SSID/PASS + BROKER_IP
mpremote fs cp esp32/config.py :config.py
mpremote fs cp esp32/lcd_api.py :lcd_api.py
mpremote fs cp esp32/i2c_lcd.py :i2c_lcd.py
mpremote fs cp esp32/main.py :main.py
mpremote run esp32/main.py       # watch it boot
```
On boot the LCD should show **SYSTEM SECURE** and the green LED should light.
It now auto-runs on every power-up (file is named main.py).

**Quick manual test (no laptop script needed yet):**
```
mosquitto_pub -h localhost -t signguard/commands \
  -m '{"device_id":"SG-RNP-001","command":"safe_fallback","timestamp":"now"}'
```
LCD should flip to **TAMPER DETECTED**, red LED blinks, buzzer beeps. Publish
`"command":"render"` to reset it to SECURE. If this works, the hardware side
is fully done.

---

## Step 4 — Authorize the real content (2 min, one time)

```
cd laptop
pip install -r requirements.txt
python3 authorize_content.py
```
This hashes `data/authorized_content.txt` and stores it as the trusted
fingerprint — mirrors SignGuard's real Content Authorization step.

---

## Step 5 — Rehearse the live demo (5 min) — laptop only, no USB

The scenario: an **authorized** person can change the sign's content; an
**unauthorized** change is blocked with an alarm. All from the laptop.

```
python3 demo_trigger.py --show                              # show current authorized content
python3 demo_trigger.py --authorized "NEXT BUS 11:00|PLATFORM 2"   # AUTHORIZED change -> accepted
python3 demo_trigger.py --unauthorized                     # UNAUTHORIZED change -> blocked + alarm
```

- `--authorized "L1|L2"` → the operator re-authorizes new content → the ESP
  **updates to the new message**, green LED, no alarm. (Use `|` between the two
  LCD lines; omit the text to be prompted.) The content genuinely changes.
- `--unauthorized` → the new content has no matching authorization → **hash
  mismatch** → the ESP shows the **safe fallback**, the **red LED blinks**, and
  the **buzzer sounds**. Optionally pass your own text: `--unauthorized "FAKE|MSG"`.
- `--show` → re-display whatever content is currently authorized (secure).

---

## Live demo script (what to say)

1. "Here's the sign with authorized transit content." → `--show` (green LED).
2. "An **authorized** operator updates it — say, a schedule change." →
   `--authorized "NEXT BUS 11:00|PLATFORM 2"`. The sign **changes** to the new
   message, still green/secure. "SignGuard re-authorized it — integrity intact."
3. "Now an **unauthorized** change — an attacker edits the content." →
   `--unauthorized`. The sign flips to **TAMPER DETECTED**, the **red LED
   blinks**, the **buzzer sounds**. "Blocked by a cryptographic hash check
   before it ever reached passengers — not a guess."
4. `--show` (or `--authorized ...`) to reset to a clean secure state.

> Authorized vs unauthorized is decided by SHA-256: an authorized operator can
> update the fingerprint, an attacker cannot — so their change fails the check.

---

## Optional upgrade — the FULL BRAIN (real AI + audit)

Everything above is the simple, bulletproof path (SHA-256 + a scripted
narrative). The **same wired + flashed ESP32** can also be driven by the real
SignGuard Layer 2 — Isolation Forest AI risk score + SHAP + append-only audit
trail — and even react to a **real USB stick physically inserted** into the
laptop. No Raspberry Pi.

From the project root (`D:\J.ACKTHON`):
```powershell
python run_demo.py        # broker + FastAPI + Layer 2 orchestrator + dashboard
```
Then in a second terminal, start the Windows USB monitor in event mode:
```powershell
python -m edge_node.hardware.win_usb_monitor --mode event
```
Now **physically plug a USB stick into the laptop** → the monitor emits the USB
attack telemetry → Layer 2 computes the risk, writes the audit record, decides
BLOCK, and publishes `safe_fallback` to `SG-RNP-001` → the ESP32 shows TAMPER.
**Pull the stick out** → authentic content is re-published → the ESP32 returns to
SYSTEM SECURE. The AI risk score, SHAP factors, and audit trail show live on the
dashboard at `http://localhost:8000`.

> Both paths publish to the **same** signage id (`SG-RNP-001`), so you only flash
> the ESP32 once. Use `--mode command` instead of `--mode event` to make the USB
> monitor drive the sign directly without the backend.

---

## If something misbehaves on stage

- ESP32 not reacting → check it's on the same Wi-Fi as the broker, and
  `BROKER_IP` in config.py is the broker machine's real LAN IP, not `localhost`.
- LCD blank/garbled → wrong I2C address; re-check Step 3's scan.
- No sound → active buzzer wired backwards, swap + and -.
- As a last resort, the `mosquitto_pub` command from Step 3 drives the ESP32
  directly — the demo can continue even if `demo_trigger.py` has an issue.
