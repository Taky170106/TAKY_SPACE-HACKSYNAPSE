"""
SignGuard AI — USB attack demo — shared MQTT config (laptop side).

Edit BROKER_HOST if the broker runs on a different machine than this script.
Must match BROKER_IP in esp32/config.py and DEVICE_ID in esp32/config.py.
"""

BROKER_HOST = "localhost"    # or the broker machine's LAN IP
BROKER_PORT = 1883

DEVICE_ID = "SG-RNP-001"     # must match esp32/config.py DEVICE_ID
                             # (same signage id the full Layer 2 brain drives,
                             #  so one ESP32 flash works for both demo paths)
TOPIC_COMMANDS = "signguard/commands"

AUTHORIZED_HASH_FILE = "data/authorized_hash.json"
