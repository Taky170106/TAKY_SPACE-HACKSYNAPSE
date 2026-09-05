"""
SignGuard AI - USB attack demo - NodeMCU ESP-12E (ESP8266) output node.

MicroPython for ESP8266. No sensors - this board only reacts to what SignGuard
(demo_trigger.py OR the Layer 2 brain) decides after the SHA-256 check. It
subscribes to signguard/commands and shows the result physically:

  render        -> LCD "SYSTEM SECURE"   / green LED on,  buzzer off
  safe_fallback -> LCD "TAMPER DETECTED" / red LED blink, buzzer beeps
  isolate       -> LCD "!! LOCKED !!"    / red LED solid, long beep (spare)

Upload as main.py so it auto-runs on boot. Also upload: config.py (from
config.example.py), lcd_api.py, i2c_lcd.py. Requires umqtt.simple.

WIRING (NodeMCU ESP-12E)   D-label -> GPIO
------------------------------------------
LCD (I2C backpack): VCC->3V3/VIN  GND->GND  SDA->D2(GPIO4)  SCL->D1(GPIO5)
Buzzer:              +  ->D5(GPIO14)   -  ->GND
Green LED:  D6(GPIO12) -> 220ohm -> LED(+) -> LED(-) -> GND
Red LED:    D7(GPIO13) -> 220ohm -> LED(+) -> LED(-) -> GND
"""
import time
import json
import network
from machine import Pin, PWM
from umqtt.simple import MQTTClient
from i2c_lcd import I2cLcd

import config as cfg

# ESP8266 has no hardware I2C peripheral id - use software I2C. Newer
# MicroPython exposes SoftI2C; fall back to the legacy I2C on older builds.
try:
    from machine import SoftI2C as _I2C
except ImportError:
    from machine import I2C as _I2C

# --- Hardware setup ---------------------------------------------------
i2c = _I2C(scl=Pin(cfg.I2C_SCL), sda=Pin(cfg.I2C_SDA), freq=100000)
lcd = I2cLcd(i2c, cfg.LCD_ADDR, cfg.LCD_ROWS, cfg.LCD_COLS)
# Buzzer driven with PWM (a real tone) so it sounds on BOTH active and passive
# buzzers. duty 0 = silent, duty 700 = loud tone at ~2 kHz.
buzzer = PWM(Pin(cfg.BUZZER_PIN))
buzzer.freq(2000)
buzzer.duty(0)
led_green = Pin(cfg.LED_GREEN_PIN, Pin.OUT)
led_red = Pin(cfg.LED_RED_PIN, Pin.OUT)
led_green.value(0)
led_red.value(0)


def buz(on):
    buzzer.duty(700 if on else 0)

STATES = {
    "render":        ("SYSTEM SECURE", "Content verified"),
    "safe_fallback": ("TAMPER DETECTED", "Update blocked"),
    "isolate":       ("!! LOCKED !!", "Maintenance req."),
    # "unverified" = SignGuard OFF: the attacker's content is shown, no check.
    # The LCD text is supplied by the command payload (line1/line2).
    "unverified":    ("SignGuard OFF", "unprotected"),
}

mode = "render"
mode_since = time.ticks_ms()
cur_lines = STATES["render"]


def lcd_show(line1, line2):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:cfg.LCD_COLS])
    lcd.move_to(0, 1)
    lcd.putstr(line2[:cfg.LCD_COLS])


def set_mode(m, l1=None, l2=None):
    global mode, mode_since, cur_lines
    lines = (l1, l2 or "") if l1 is not None else STATES.get(m, ("SIGNGUARD", m))
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
        blink = (t % 500) < 250
        led_red.value(1 if blink else 0)
        # pulsing beep (250 ms on / 250 ms off) for the whole tamper alarm,
        # until a 'render' command clears it.
        buz(blink)
    elif mode == "isolate":
        led_green.value(0)
        led_red.value(1)
        buz((t % 1200) < 800)
    elif mode == "unverified":
        # SignGuard OFF: no monitoring at all -> both LEDs dark, no buzzer,
        # while the attacker's fake message sits on the sign.
        led_green.value(0)
        led_red.value(0)
        buz(False)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        lcd_show("SignGuard", "WiFi...")
        wlan.connect(cfg.WIFI_SSID, cfg.WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("[esp8266] Wi-Fi:", wlan.ifconfig()[0])


def connect_mqtt():
    client = MQTTClient(cfg.DEVICE_ID, cfg.BROKER_IP,
                        port=cfg.BROKER_PORT, keepalive=60)
    client.set_callback(on_command)
    client.connect()
    client.subscribe(cfg.TOPIC_COMMANDS)
    print("[esp8266] MQTT connected + subscribed:", cfg.BROKER_IP)
    return client


def main():
    lcd_show("SignGuard", "starting...")
    connect_wifi()
    client = connect_mqtt()
    set_mode("render")     # default: secure, until an attack is triggered
    print("[esp8266] ready. waiting for commands.")

    while True:
        try:
            client.check_msg()   # non-blocking; triggers on_command on arrival
            update_actuators()
            time.sleep(0.02)
        except OSError as e:
            print("[esp8266] MQTT error, reconnecting:", e)
            lcd_show("SignGuard", "reconnecting..")
            time.sleep(2)
            try:
                client = connect_mqtt()
                lcd_show(cur_lines[0], cur_lines[1])
            except Exception:
                pass


main()
