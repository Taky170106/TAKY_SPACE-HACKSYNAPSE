# SignGuard AI - USB attack demo - NodeMCU ESP-12E (ESP8266) config TEMPLATE.
# Copy this file to config.py on the board and fill in your values.
#
# Pins are GPIO NUMBERS (not the D-labels printed on the NodeMCU). Mapping for
# your wiring:
#   D1 = GPIO5  -> LCD SCL
#   D2 = GPIO4  -> LCD SDA
#   D5 = GPIO14 -> Buzzer +
#   D6 = GPIO12 -> Green LED +
#   D7 = GPIO13 -> Red LED +

WIFI_SSID = "your-wifi"
WIFI_PASS = "your-password"

# LAN IP of the laptop running Mosquitto (find it with: ipconfig).
BROKER_IP = "192.168.12.81"
BROKER_PORT = 1883

DEVICE_ID = "SG-RNP-001"      # must match laptop/mqtt_config.py DEVICE_ID
TOPIC_COMMANDS = "signguard/commands"

# --- I2C for the 16x2 LCD backpack (software I2C on ESP8266) ---
I2C_SDA = 4     # D2
I2C_SCL = 5     # D1
LCD_ADDR = 0x27    # if blank/garbled, try 0x3F (run the scan in SETUP.md)
LCD_ROWS = 2
LCD_COLS = 16

# --- Actuators ---
BUZZER_PIN = 14     # D5
LED_GREEN_PIN = 12  # D6, lit = system secure
LED_RED_PIN = 13    # D7, lit/blinking = tamper detected
