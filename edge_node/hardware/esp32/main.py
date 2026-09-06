"""
SignGuard AI - ESP32 signage output node (MicroPython).

No sensors. This board is the physical STATUS + ALARM output. It subscribes
to signguard/commands and reacts to whatever Layer 2 decides:

  render        -> LCD "SignGuard: OK / Route 101 OK",     buzzer silent
  safe_fallback -> LCD "** BLOCKED ** / <attack label>",   buzzer beeps
  isolate       -> LCD "!! ISOLATED !! / <attack label>",  buzzer long beep

The command JSON may carry an optional "attack" field (e.g. "USB TAMPER",
"ROGUE WIFI", "ADMIN BREACH"); when present it is shown on line 2 so the sign
tells you exactly which attack SignGuard just blocked.

Commands match CLAUDE.md #6. Upload as main.py so it auto-runs on boot.
Also upload: config.py (from config.example.py), lcd_api.py, i2c_lcd.py.
Requires umqtt.simple.

WIRING (16x2 LCD with I2C backpack + buzzer)
--------------------------------------------
LCD  VCC -> 5V (VIN)   GND -> GND   SDA -> GPIO21   SCL -> GPIO22
Buzzer   +  -> GPIO26        -  -> GND
Green LED +(long) -> GPIO25 via ~220-330 ohm resistor,  -(short) -> GND
Red   LED +(long) -> GPIO33 via ~220-330 ohm resistor,  -(short) -> GND
(LEDs are optional - set GREEN_LED_PIN/RED_LED_PIN to None in config to skip.
 If SDA/SCL at 5V worries you, use a logic level shifter; many kits run
 the backpack at 5V and wire straight to the ESP32 - test yours.)
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
buzzer.value(0)

# Optional status LEDs (green = secure, red = attack). Skip cleanly if unset.
green_led = Pin(cfg.GREEN_LED_PIN, Pin.OUT) if getattr(cfg, "GREEN_LED_PIN", None) is not None else None
red_led = Pin(cfg.RED_LED_PIN, Pin.OUT) if getattr(cfg, "RED_LED_PIN", None) is not None else None


def set_leds(secure):
    if green_led is not None:
        green_led.value(1 if secure else 0)
    if red_led is not None:
        red_led.value(0 if secure else 1)

# line1 per command; line2 is the default when no attack label is supplied.
STATES = {
    "render":        ("SYSTEM SECURE", "Route 101  OK"),
    "safe_fallback": ("TAMPER DETECTED", "Fallback active"),
    "isolate":       ("CRITICAL ALERT", "Channel locked"),
}

mode = "render"
mode_attack = ""
mode_since = time.ticks_ms()


def lcd_show(line1, line2):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:cfg.LCD_COLS])
    lcd.move_to(0, 1)
    lcd.putstr(line2[:cfg.LCD_COLS])


def set_mode(m, attack=""):
    global mode, mode_attack, mode_since
    if m != mode or attack != mode_attack:
        mode = m
        mode_attack = attack
        mode_since = time.ticks_ms()
        l1, default2 = STATES[m]
        # On a block/isolate, show WHICH attack; render always shows the route.
        line2 = attack if (attack and m != "render") else default2
        lcd_show(l1, line2)
        set_leds(m == "render")     # green when secure, red on block/isolate
        print("[esp32] mode:", m, "attack:", attack)


def on_command(topic, msg):
    try:
        payload = json.loads(msg)
    except Exception:
        return
    if payload.get("device_id") not in (cfg.DEVICE_ID, None, "all"):
        return
    cmd = payload.get("command")
    if cmd in STATES:
        set_mode(cmd, payload.get("attack", ""))


def update_buzzer():
    t = time.ticks_diff(time.ticks_ms(), mode_since)
    if mode == "render":
        buzzer.value(0)
    elif mode == "safe_fallback":
        buzzer.value(1 if (t % 500) < 250 else 0)     # short repeating beeps
    elif mode == "isolate":
        buzzer.value(1 if (t % 1200) < 800 else 0)    # long repeating beep


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
    set_mode("render")     # default state until Layer 2 says otherwise
    print("[esp32] running. waiting for commands.")

    while True:
        try:
            client.check_msg()     # non-blocking; fires on_command on a command
            update_buzzer()
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
