"""
SignGuard AI - USB attack demo - NodeMCU ESP-12E (ESP8266) output node.

FLEXIBLE / DEMO-PROOF firmware. It never gets stuck and always demos:

  * Multi Wi-Fi + multi broker  : scans config.WIFI_NETWORKS / BROKER_CANDIDATES
                                  and joins whatever is live. No single hardcoded
                                  network. Keeps retrying in the background.
  * OFFLINE DEMO mode           : if no network/broker, it does NOT freeze on
                                  "WiFi..."; it shows OFFLINE READY and the FLASH
                                  button still drives LCD + buzzer.
  * FLASH button (GPIO0 / D3)   : press to cycle SECURE -> TAMPER (buzzer) ->
                                  LOCKED -> SECURE, with zero laptop/network.
  * Auto-reconnect              : the moment the broker is reachable it goes LIVE
                                  and reacts to signguard/commands as before.

Commands (when LIVE):
  render        -> LCD "SYSTEM SECURE" (or line1/line2) / green LED, buzzer off
  safe_fallback -> LCD "TAMPER DETECTED" / red LED blink, pulsing buzzer
  isolate       -> LCD "!! LOCKED !!"    / red LED solid, long beep
  unverified    -> LCD attacker text     / no LEDs, no buzzer (SignGuard OFF)

Upload as main.py. Also upload: config.py, lcd_api.py, i2c_lcd.py, umqtt.simple.

WIRING (NodeMCU ESP-12E)   D-label -> GPIO
LCD (I2C): VCC->3V3/VIN GND->GND SDA->D2(GPIO4) SCL->D1(GPIO5)
Buzzer: + ->D5(GPIO14)  - ->GND   |  Green LED D6(GPIO12)  Red LED D7(GPIO13)
FLASH button: onboard (GPIO0) - no wiring needed.
"""
import time
import json
import network
from machine import Pin, PWM
from umqtt.simple import MQTTClient
from i2c_lcd import I2cLcd

import config as cfg

try:
    from machine import SoftI2C as _I2C
except ImportError:
    from machine import I2C as _I2C

# --- Hardware setup ---------------------------------------------------
i2c = _I2C(scl=Pin(cfg.I2C_SCL), sda=Pin(cfg.I2C_SDA), freq=100000)
lcd = I2cLcd(i2c, cfg.LCD_ADDR, cfg.LCD_ROWS, cfg.LCD_COLS)
# PWM buzzer => a real tone, works on BOTH active and passive buzzers.
buzzer = PWM(Pin(cfg.BUZZER_PIN))
buzzer.freq(2000)
buzzer.duty(0)
led_green = Pin(cfg.LED_GREEN_PIN, Pin.OUT)
led_red = Pin(cfg.LED_RED_PIN, Pin.OUT)
led_green.value(0)
led_red.value(0)
button = Pin(cfg.BUTTON_PIN, Pin.IN, Pin.PULL_UP)   # pressed = 0


def buz(on):
    buzzer.duty(700 if on else 0)


STATES = {
    "render":        ("SYSTEM SECURE", "Content verified"),
    "safe_fallback": ("TAMPER DETECTED", "Update blocked"),
    "isolate":       ("!! LOCKED !!", "Maintenance req."),
    "unverified":    ("SignGuard OFF", "unprotected"),
}
# order the FLASH button walks through
BUTTON_CYCLE = ["render", "safe_fallback", "isolate"]

mode = "render"
mode_since = time.ticks_ms()
cur_lines = STATES["render"]
good_lines = STATES["render"]     # last VERIFIED content, used for fast fallback
online = False
client = None

# Timing for the tamper alarm (ms)
BUZZ_MS = 1200        # buzzer sounds for ~1.2 seconds
TAMPER_SHOW_MS = 1500 # show "TAMPER DETECTED" briefly, then fall back to content

# helper lists (support old single-value configs too)
NETWORKS = getattr(cfg, "WIFI_NETWORKS", None) or [(cfg.WIFI_SSID, cfg.WIFI_PASS)]
BROKERS = getattr(cfg, "BROKER_CANDIDATES", None) or [cfg.BROKER_IP]
AUTO_DEMO = getattr(cfg, "AUTO_DEMO", False)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)


def lcd_show(line1, line2):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:cfg.LCD_COLS])
    lcd.move_to(0, 1)
    lcd.putstr(line2[:cfg.LCD_COLS])


def set_mode(m, l1=None, l2=None):
    global mode, mode_since, cur_lines, good_lines
    lines = (l1, l2 or "") if l1 is not None else STATES.get(m, ("SIGNGUARD", m))
    # remember the last VERIFIED content so a tamper can fall back to it fast
    if m == "render":
        good_lines = lines
    if m != mode or lines != cur_lines:
        mode = m
        cur_lines = lines
        mode_since = time.ticks_ms()
        lcd_show(lines[0], lines[1])
        print("[esp8266] mode:", m)


def on_command(topic, msg):
    try:
        payload = json.loads(msg)
    except Exception:
        return
    if payload.get("device_id") not in (cfg.DEVICE_ID, None, "all"):
        return
    cmd = payload.get("command")
    if cmd in STATES:
        set_mode(cmd, payload.get("line1"), payload.get("line2"))


def update_actuators():
    t = time.ticks_diff(time.ticks_ms(), mode_since)
    if mode == "render":
        led_green.value(1)
        led_red.value(0)
        buz(False)
    elif mode == "safe_fallback":
        led_green.value(0)
        blink = (t % 400) < 200
        led_red.value(1 if blink else 0)
        buz(blink if t < BUZZ_MS else False)   # buzzer only for the first 1 s
        if t > TAMPER_SHOW_MS:
            # fast fallback: revert the sign to the last VERIFIED content
            set_mode("render", good_lines[0], good_lines[1])
    elif mode == "isolate":
        led_green.value(0)
        led_red.value(1)
        buz((t % 1200) < 800)
    elif mode == "unverified":
        led_green.value(0)
        led_red.value(0)
        buz(False)


# --- Networking (non-blocking-ish, best effort) -----------------------
def try_go_online():
    """Scan known networks, join one, connect to a candidate broker.
    Returns True only when MQTT is connected + subscribed."""
    global client
    try:
        if not wlan.isconnected():
            try:
                visible = [n[0].decode("utf-8", "replace") for n in wlan.scan()]
            except Exception:
                visible = []
            for ssid, pw in NETWORKS:
                if ssid in visible:
                    print("[esp8266] joining", ssid)
                    wlan.connect(ssid, pw)
                    for _ in range(16):          # wait up to ~8s
                        if wlan.isconnected():
                            break
                        time.sleep(0.5)
                if wlan.isconnected():
                    break
        if not wlan.isconnected():
            return False
        print("[esp8266] Wi-Fi:", wlan.ifconfig()[0])
        for ip in BROKERS:
            try:
                c = MQTTClient(cfg.DEVICE_ID, ip, port=cfg.BROKER_PORT, keepalive=60)
                c.set_callback(on_command)
                c.connect()
                c.subscribe(cfg.TOPIC_COMMANDS)
                client = c
                print("[esp8266] MQTT LIVE via", ip)
                return True
            except Exception as e:
                print("[esp8266] broker", ip, "no:", e)
        return False
    except Exception as e:
        print("[esp8266] net error:", e)
        return False


# --- Button (manual demo, works online or offline) --------------------
_last_btn = 1
_last_btn_ms = 0
_btn_idx = 0


def handle_button():
    global _last_btn, _last_btn_ms, _btn_idx
    v = button.value()
    now = time.ticks_ms()
    if v == 0 and _last_btn == 1 and time.ticks_diff(now, _last_btn_ms) > 250:
        _last_btn_ms = now
        _btn_idx = (_btn_idx + 1) % len(BUTTON_CYCLE)
        set_mode(BUTTON_CYCLE[_btn_idx])
        print("[esp8266] button ->", BUTTON_CYCLE[_btn_idx])
    _last_btn = v


def main():
    global online
    lcd_show("SignGuard", "starting...")
    # one quick attempt so we usually come up LIVE
    online = try_go_online()
    if online:
        set_mode("render")
        print("[esp8266] READY (LIVE). waiting for commands.")
    else:
        set_mode("render")
        lcd_show("OFFLINE READY", "FLASH=demo")
        print("[esp8266] READY (OFFLINE). FLASH button drives the demo.")

    last_try = time.ticks_ms()
    auto_last = time.ticks_ms()
    auto_idx = 0

    while True:
        handle_button()

        if online:
            try:
                client.check_msg()
            except OSError as e:
                print("[esp8266] MQTT lost:", e)
                online = False
                try:
                    client.disconnect()
                except Exception:
                    pass
        else:
            # retry the network every ~10s WITHOUT blocking the demo
            if time.ticks_diff(time.ticks_ms(), last_try) > 10000:
                last_try = time.ticks_ms()
                if try_go_online():
                    online = True
                    set_mode(mode)          # re-render current state on the LCD
                    print("[esp8266] reconnected -> LIVE")
            # optional hands-free demo when offline
            if AUTO_DEMO and time.ticks_diff(time.ticks_ms(), auto_last) > 4000:
                auto_last = time.ticks_ms()
                auto_idx = (auto_idx + 1) % len(BUTTON_CYCLE)
                set_mode(BUTTON_CYCLE[auto_idx])

        update_actuators()
        time.sleep(0.02)


main()
