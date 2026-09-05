# SignGuard AI - USB attack demo - ESP32 config TEMPLATE.
# Copy this file to config.py on the ESP32 and fill in your values.

WIFI_SSID = "your-wifi"
WIFI_PASS = "your-password"

# LAN IP of the machine running Mosquitto (find it with: hostname -I).
BROKER_IP = "192.168.1.100"
BROKER_PORT = 1883

DEVICE_ID = "SG-RNP-001"      # must match laptop/mqtt_config.py DEVICE_ID
                              # (SG-RNP-001 = the signage node used by BOTH the
                              #  simple demo_trigger AND the full Layer 2 brain)
TOPIC_COMMANDS = "signguard/commands"

# --- I2C for the 16x2 LCD backpack ---
I2C_SDA = 21
I2C_SCL = 22
LCD_ADDR = 0x27    # if blank/garbled, try 0x3F (see SETUP.md Step 2c)
LCD_ROWS = 2
LCD_COLS = 16

# --- Actuators ---
BUZZER_PIN = 26
LED_GREEN_PIN = 27    # lit = system secure
LED_RED_PIN = 14      # lit/blinking = tamper detected
