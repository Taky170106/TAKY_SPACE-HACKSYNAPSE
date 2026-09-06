# SignGuard AI - ESP32 configuration TEMPLATE.
# Copy this file to config.py on the ESP32 and fill in your values.

WIFI_SSID = "your-wifi"
WIFI_PASS = "your-password"

# LAN IP of the machine running Mosquitto (broker host: hostname -I).
BROKER_IP = "192.168.1.100"
BROKER_PORT = 1883

DEVICE_ID = "SG-ESP-001"
TOPIC_COMMANDS = "signguard/commands"

# --- I2C for the 16x2 LCD backpack ---
I2C_SDA = 21
I2C_SCL = 22
LCD_ADDR = 0x27     # common for PCF8574; some boards are 0x3F.
                    # Run the scan snippet in SETUP.md to confirm yours.
LCD_ROWS = 2
LCD_COLS = 16

# --- Buzzer ---
BUZZER_PIN = 26     # active buzzer (+ to pin, - to GND)

# --- Status LEDs (optional) ---
# green = SYSTEM SECURE, red = TAMPER/attack. Long leg (+) to the pin
# through a ~220-330 ohm resistor, short leg (-) to GND.
# Set a pin to None to disable that LED.
GREEN_LED_PIN = 25
RED_LED_PIN = 33
