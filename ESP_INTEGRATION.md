# SignGuard — ESP-12E Hardware Setup & Integration

Connect a real ESP-12E (NodeMCU) + 16×2 I²C LCD + buzzer + 2 LEDs to the lab.
The lab page (`/lab`) and dashboard send an MQTT command; the ESP reacts on the LCD.

    Web /lab (Pi + USB)  ->  FastAPI  ->  MQTT signguard/commands  ->  ESP-12E (LCD + buzzer)

## 1. Parts
- NodeMCU **ESP-12E (ESP8266)** + micro-USB cable
- 16×2 **I²C LCD** (PCF8574 backpack, addr 0x27 or 0x3F)
- Active **buzzer**
- **Green LED** + **Red LED** (+ 2× 220Ω resistors)
- Breadboard + jumper wires

## 2. Wiring (GPIO numbers, not D-labels)
| From ESP | Pin | To |
|---|---|---|
| LCD VCC | 3V3 / VIN(5V) | LCD power |
| LCD GND | GND | LCD ground |
| LCD SDA | **D2 = GPIO4** | LCD SDA |
| LCD SCL | **D1 = GPIO5** | LCD SCL |
| Buzzer + | **D5 = GPIO14** | buzzer +, buzzer − → GND |
| Green LED | **D6 = GPIO12** | → 220Ω → LED+ , LED− → GND |
| Red LED | **D7 = GPIO13** | → 220Ω → LED+ , LED− → GND |

(These match `usb_demo/esp8266/config.py` — no code change needed.)

## 3. Flash MicroPython (one time, from the laptop)
```powershell
pip install esptool mpremote
esptool.py --chip esp8266 erase_flash
esptool.py --chip esp8266 --port COM5 write_flash 0 esp8266-<version>.bin
```
Download the ESP8266 build from micropython.org. Find the COM port in Device Manager
(if it's not detected, install the CP210x driver in `usb_demo/esp8266/driver/`).

## 4. Configure + upload the firmware
```powershell
cd usb_demo\esp8266
copy config.example.py config.py     # then edit config.py:
#   WIFI_SSID / WIFI_PASS  = your Wi-Fi
#   BROKER_IP              = your LAPTOP's LAN IP (run `ipconfig`, IPv4)
#   DEVICE_ID  = "SG-RNP-001"   (must match — do not change)
#   LCD_ADDR   = 0x27           (if blank/garbled, use 0x3F)

mpremote mip install umqtt.simple
mpremote fs cp config.py :config.py
mpremote fs cp lcd_api.py :lcd_api.py
mpremote fs cp i2c_lcd.py :i2c_lcd.py
mpremote fs cp main.py :main.py
```
Power-cycle the ESP. The LCD should show `SYSTEM SECURE / Content verified` once it
joins Wi-Fi and the broker, and the **green LED** lights.

> Find the LCD address if unsure — REPL (`mpremote`):
> `from machine import Pin,SoftI2C; print([hex(a) for a in SoftI2C(scl=Pin(5),sda=Pin(4)).scan()])`

## 5. Run the whole system
```powershell
cd D:\J.ACKTHON
python run_demo.py            # broker + backend + dashboard on the laptop
```
- Laptop, Pi-lab (browser), and ESP must be on the **same Wi-Fi**.
- The laptop firewall must allow inbound **TCP 1883** (MQTT).

## 6. Demo it (the panel moment)
Open `http://localhost:8000/lab`:
1. Type/authorize your original content, e.g. `TNSTC Route 101|Next 10:30` → **Set as AUTHORIZED**.
2. **SignGuard ON**, upload a genuine file → **Insert USB into Pi** →
   ESP LCD shows the **real content** (`TNSTC Route 101 / Next 10:30`), **green LED**.
3. **SignGuard ON**, upload a **tampered** file → Insert →
   hash mismatch → ESP LCD shows **`TAMPER DETECTED`**, **red LED**, **buzzer beeps**;
   the sign never shows the attacker's message. Dashboard shows risk + SHAP + audit.
4. **SignGuard OFF**, same tampered file → no protection (for contrast).

## 7. What the ESP does per command (firmware: `usb_demo/esp8266/main.py`)
| MQTT command | LCD | LEDs | Buzzer |
|---|---|---|---|
| `render` (+line1/line2) | your content | green on | off |
| `safe_fallback` | `TAMPER DETECTED / Update blocked` | red blink | beeps |
| `isolate` | `!! LOCKED !!` | red solid | long beep |

Topic: `signguard/commands` · device id: `SG-RNP-001`.

## 8. Troubleshooting
| Problem | Fix |
|---|---|
| LCD blank/garbled | Wrong `LCD_ADDR` → try `0x3F`; check 3V3/GND + SDA/SCL. |
| ESP won't connect | Verify `WIFI_SSID/PASS` and `BROKER_IP` (laptop IPv4); same Wi-Fi. |
| No LCD reaction | Broker must bind `0.0.0.0:1883` (it does via `mosquitto.conf`); firewall allow 1883; `DEVICE_ID` = `SG-RNP-001`. |
| `hardware: not connected` on /lab | ESP not on the broker yet — it says "delivered" once the ESP is subscribed. |
| COM port missing | Install CP210x driver from `usb_demo/esp8266/driver/`. |
