"""SignGuard AI — Raspberry Pi configuration.

Edit BROKER_HOST before running. If Mosquitto runs ON the Pi itself,
"localhost" works. If it runs on your laptop, use that laptop's LAN IP
(find it on the broker host with:  hostname -I ).
"""

BROKER_HOST = "192.168.1.100"   # <-- change to your broker's LAN IP
BROKER_PORT = 1883

DEVICE_ID = "SG-RNP-001"        # this Pi's signage node id

# SignGuard backend (FastAPI) URL for the USB DETECTOR (pi_usb_detector.py).
# If the backend runs on the laptop, use its LAN IP + port 8000.
API_URL = "http://192.168.1.100:8000"   # <-- change to your laptop backend

TOPIC_EVENTS = "signguard/events"
TOPIC_COMMANDS = "signguard/commands"

# Serials of USB sticks you trust (maintenance drives). Anything not in
# this set is reported as unauthorized_usb.
# Find a stick's serial with it plugged in:
#   udevadm info -q property -n /dev/sda | grep ID_SERIAL_SHORT
AUTHORIZED_USB_SERIALS = {
    # "0123456789ABCDEF",
}
