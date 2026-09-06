"""
SignGuard AI - USB attack demo - ESP32 output node (MicroPython).

No sensors. This board only reacts to what the laptop-side demo_trigger.py
decides after checking the SHA-256 hash. It subscribes to
signguard/commands and shows the result physically:

  render        -> LCD "SYSTEM SECURE"   / green LED on,  buzzer off
  safe_fallback -> LCD "TAMPER DETECTED" / red LED blink, buzzer beeps
  isolate       -> LCD "!! LOCKED !!"    / red LED solid, long beep (spare)

Upload as main.py so it auto-runs on boot. Also upload: config.py (from
config.example.py), lcd_api.py, i2c_lcd.py. Requires umqtt.simple.

WIRING
------
LCD (I2C backpack): VCC->5V(VIN)  GND->GND  SDA->GPIO21  SCL->GPIO22
Buzzer:              +  ->GPIO26       -  ->GND
Green LED:  GPIO27 -> 220ohm -> LED(+) -> LED(-) -> GND
Red LED:    GPIO14 -> 220ohm -> LED(+) -> LED(-) -> GND
"""
import time
import json
import network
from machine import Pin, I2C
from umqtt.simple import MQTTClient
from i2c_lcd import I2cLcd

import config as cfg

# --- Hardware setup ---------------------------------------------------
i2c = I2C(0, scl=Pin(cfg.I2C_SCL), sda=Pin(cfg.I2C_SDA), freq=100000)
lcd = I2cLcd(i2c, cfg.LCD_ADDR, cfg.LCD_ROWS, cfg.LCD_COLS)
buzzer = Pin(cfg.BUZZER_PIN, Pin.OUT)
led_green = Pin(cfg.LED_GREEN_PIN, Pin.OUT)
led_red = Pin(cfg.LED_RED_PIN, Pin.OUT)
buzzer.value(0)
led_green.value(0)
led_red.value(0)

STATES = {
    "render":        ("SYSTEM SECURE", "Content verified"),
    "safe_fallback": ("TAMPER DETECTED", "Update blocked"),
    "isolate":       ("!! LOCKED !!", "Maintenance req."),
}

mode = "render"
mode_since = time.ticks_ms()


def lcd_show(line1, line2):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:cfg.LCD_COLS])
    lcd.move_to(0, 1)
    lcd.putstr(line2[:cfg.LCD_COLS])


def set_mode(m):
    global mode, mode_since
    if m != mode:
        mode = m
        mode_since = time.ticks_ms()
        l1, l2 = STATES[m]
        lcd_show(l1, l2)
        print("[esp32] mode:", m)


def on_command(topic, msg):
    try:
        payload = json.loads(msg)
    except Exception:
        return
    if payload.get("device_id") not in (cfg.DEVICE_ID, None, "all"):
        return
    cmd = payload.get("command")
    if cmd in STATES:
        set_mode(cmd)


def update_actuators():
    t = time.ticks_diff(time.ticks_ms(), mode_since)
    if mode == "render":
        led_green.value(1)
        led_red.value(0)
        buzzer.value(0)
    elif mode == "safe_fallback":
        led_green.value(0)
        blink = (t % 500) < 250
        led_red.value(1 if blink else 0)
        buzzer.value(1 if blink else 0)
    elif mode == "isolate":
        led_green.value(0)
        led_red.value(1)
        buzzer.value(1 if (t % 1200) < 800 else 0)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        lcd_show("SignGuard", "WiFi...")
        wlan.connect(cfg.WIFI_SSID, cfg.WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("[esp32] Wi-Fi:", wlan.ifconfig()[0])


def connect_mqtt():
    client = MQTTClient(cfg.DEVICE_ID, cfg.BROKER_IP,
                        port=cfg.BROKER_PORT, keepalive=60)
    client.set_callback(on_command)
    client.connect()
    client.subscribe(cfg.TOPIC_COMMANDS)
    print("[esp32] MQTT connected + subscribed:", cfg.BROKER_IP)
    return client


def main():
    lcd_show("SignGuard", "starting...")
    connect_wifi()
    client = connect_mqtt()
    set_mode("render")     # default: secure, until an attack is triggered
    print("[esp32] ready. waiting for commands.")

    while True:
        try:
            client.check_msg()   # non-blocking; triggers on_command on arrival
            update_actuators()
            time.sleep(0.02)
        except OSError as e:
            print("[esp32] MQTT error, reconnecting:", e)
            lcd_show("SignGuard", "reconnecting..")
            time.sleep(2)
            try:
                client = connect_mqtt()
                l1, l2 = STATES[mode]
                lcd_show(l1, l2)
            except Exception:
                pass


main()
