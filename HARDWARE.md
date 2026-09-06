  # SignGuard AI — Hardware Guide
### Blockchain-based content integrity system for public transport

Everything you need to do with the physical kit, start to finish. For the deeper
board-setup notes see `edge_node/hardware/SETUP.md`; this file is the practical
checklist for the demo.

---

## 1. The kit and who does what

| Device | Role | Talks on |
|--------|------|----------|
| **Laptop** (or Pi) | Runs the **broker + Layer 2 brain + dashboard** | serves `:8000`, MQTT `:1883` |
| **Raspberry Pi** | **Detection gateway** — real USB detection (pyudev) | publishes `signguard/events` |
| **ESP32 + 16×2 I²C LCD + buzzer** | **Signage output** — shows status, blocks, alarms | subscribes `signguard/commands` |

**Flow:** attack happens → Layer 2 decides (SHA-256 + AI) → command on
`signguard/commands` → **ESP32 LCD shows the result + buzzer sounds**.

The ESP32 has **no sensors** — it is the passenger-facing sign. The attack can come
from the Pi (real USB), the web dashboard, or the software simulators; the ESP32
reacts to all of them identically because they all go through Layer 2.

---

## 2. What the LCD shows

| Layer 2 command | Severity | LCD line 1 | LCD line 2 | Buzzer |
|-----------------|----------|-----------|-----------|--------|
| `render` | NORMAL | `SYSTEM SECURE` | `Route 101  OK` | silent |
| `safe_fallback` | CRITICAL | `TAMPER DETECTED` | **the attack label** | short beeps |
| `isolate` | CRITICAL | `CRITICAL ALERT` | the attack label | long beep |

The **attack label** is sent by Layer 2 on the wire (`"attack"` field) so the sign
names what was blocked:

| Attack | LCD line 2 |
|--------|-----------|
| Malicious USB | `USB TAMPER` |
| Rogue Wi-Fi | `ROGUE WIFI` |
| Compromised admin credentials | `ADMIN BREACH` |

---

## 3. One-time setup

### 3a. Broker host (your laptop)
The broker must be reachable from the Pi and ESP32 over Wi-Fi. It already listens
on `0.0.0.0:1883` via `mosquitto.conf`.

- **Broker IP (this laptop, Wi-Fi):** `10.63.29.144` — use this everywhere below.
  (Re-check anytime with `ipconfig` on Windows / `hostname -I` on Linux.)
- Easiest launch — the one-command demo also starts the broker:
  ```powershell
  python run_demo.py
  ```
  Or start just the broker:
  ```powershell
  & "C:\Program Files\mosquitto\mosquitto.exe" -c "D:\J.ACKTHON\mosquitto.conf" -v
  ```
- Watch every message live (great on a second screen during the demo):
  ```powershell
  & "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -t "signguard/#" -v
  ```

### 3b. ESP32 (signage node)

**Wire it**
```
LCD  VCC -> 5V (VIN)    GND -> GND    SDA -> GPIO21    SCL -> GPIO22
Buzzer +  -> GPIO26           -  -> GND
```
Common ground between the LCD, buzzer, and ESP32.

**Flash MicroPython** (once, from the laptop)
```bash
pip install esptool mpremote
esptool.py --chip esp32 erase_flash
esptool.py --chip esp32 write_flash -z 0x1000 esp32-<version>.bin   # from micropython.org
```

**Find the LCD I²C address** (REPL via `mpremote`)
```python
from machine import Pin, I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
print([hex(a) for a in i2c.scan()])     # 0x27 or 0x3f
```
If it prints `0x3f`, set `LCD_ADDR = 0x3F` in `config.py`.

**Configure + upload**
```bash
cp edge_node/hardware/esp32/config.example.py config.py
#   edit config.py:  WIFI_SSID, WIFI_PASS, BROKER_IP = "10.63.29.144", DEVICE_ID = "SG-ESP-001"
mpremote mip install umqtt.simple
mpremote fs cp config.py :config.py
mpremote fs cp edge_node/hardware/esp32/lcd_api.py :lcd_api.py
mpremote fs cp edge_node/hardware/esp32/i2c_lcd.py :i2c_lcd.py
mpremote fs cp edge_node/hardware/esp32/main.py :main.py
```
On power-up it auto-runs `main.py`; the LCD should show `SYSTEM SECURE / Route 101 OK`
once it joins Wi-Fi and the broker.

### 3c. Raspberry Pi (real USB detection) — optional
```bash
sudo apt update && sudo apt install -y mosquitto-clients
pip3 install -r edge_node/hardware/requirements.txt
#   edit edge_node/hardware/pi_config.py:  BROKER_HOST = "10.63.29.144"
sudo python3 edge_node/hardware/pi_usb_monitor.py
```
Plugging in an unknown USB stick publishes an `unauthorized_usb` event. (Skip this
board if you only want the dashboard + ESP32 demo — the web buttons cover USB too.)

---

## 4. Smoke-test the ESP32 alone (no Layer 2 needed)

Publish a fake command from the laptop and watch the sign react:
```powershell
& "C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t signguard/commands `
  -m '{"device_id":"SG-ESP-001","command":"safe_fallback","attack":"USB TAMPER"}'
```
LCD → `TAMPER DETECTED / USB TAMPER`, buzzer beeps. Try `render` and `isolate` too.
When it reacts correctly, the output node is done.

---

## 5. Run the full demo

1. **Laptop:** `python run_demo.py` (broker + Layer 2 + dashboard open at `http://localhost:8000`).
2. **ESP32:** powered on, LCD showing `SignGuard: OK` (connected to broker `10.63.29.144`).
3. *(Optional)* **Pi:** `pi_usb_monitor.py` running.
4. On the dashboard:
   - Leave **SignGuard OFF**, run **Malicious USB** → attacker content shows (webpage).
   - Flip **SignGuard ON**, run the **same attack** → webpage reverts to the verified
     content **and the ESP32 LCD shows `TAMPER DETECTED / USB TAMPER`** with the buzzer.
   - **Manual credential attack:** log in with `admin`/`admin`, Publish "NEXT BUS CANCELLED"
     → BLOCKED, LCD shows `ADMIN BREACH`.
5. *(With the Pi)* Insert an unauthorized USB → same block reaches the ESP32. **The money moment.**

> Choose what a tampered update tries to display using the **“Tampered content to display”**
> box on the dashboard — whatever you type is what the attacker’s content becomes.

---

## 6. Troubleshooting

| Symptom | Fix |
|---------|-----|
| LCD blank / garbled | Wrong `LCD_ADDR` — rerun the I²C scan; try `0x3F`. Check 5V + common ground. |
| ESP32 won't connect | Verify `WIFI_SSID/PASS` and `BROKER_IP = 10.63.29.144`; laptop firewall must allow inbound `1883`. |
| No LCD reaction | Confirm broker on `0.0.0.0:1883` (not localhost-only) and `DEVICE_ID` matches (`SG-ESP-001`) or is broadcast. |
| Pi `pi_usb_monitor` errors | Needs Linux + `pyudev`; run with `sudo` for udev permissions. paho 2.x is already handled. |
| Broker unreachable from ESP32 | You're likely on a different Wi-Fi or the laptop IP changed — re-check `ipconfig` and update `BROKER_IP`. |

If a board misbehaves on stage, the **software path covers everything** — keep the
dashboard (and `python demo_attacks.py`) ready and the demo continues unchanged.
