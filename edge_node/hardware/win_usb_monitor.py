#!/usr/bin/env python3
"""
SignGuard AI - Windows USB monitor (Pi-free real USB attack for the demo).

The Raspberry Pi detector (pi_usb_monitor.py) needs Linux + pyudev. This is the
same idea for a Windows laptop, standard library only (ctypes) - no pyudev, no
pywin32. It watches for removable USB drives being inserted/removed and drives
the SignGuard signage over MQTT. Physically plug in a stick -> the sign reacts.

Two modes:

  --mode command  (default) Publish the ESP32 command directly to
                  signguard/commands. Needs only the broker + ESP32 - the most
                  reliable path (no backend). Insert -> safe_fallback (TAMPER),
                  remove -> render (SECURE).

  --mode event    THE FULL BRAIN. Publish the full USB attack the way real
                  telemetry would arrive - the unauthorized_usb + content
                  events AND a tampered content update on the authorized
                  content id - to signguard/events + signguard/content, and let
                  Layer 2 (run_demo.py's orchestrator) decide: SHA-256 mismatch
                  -> BLOCK, plus IsolationForest risk score + audit trail, then
                  it publishes the command to the ESP32 itself. Remove the stick
                  -> authentic content is re-published -> render.

Run (on the laptop that also runs the broker):
    python -m edge_node.hardware.win_usb_monitor                 # simple
    python -m edge_node.hardware.win_usb_monitor --mode event    # full brain
        (start `python run_demo.py` first for --mode event)

Broker is on this same machine, so BROKER_HOST defaults to localhost.
Override with SIGNGUARD_MQTT_HOST / SIGNGUARD_MQTT_PORT.
"""
from __future__ import annotations

import os
import sys
import json
import time
import ctypes
import string
import base64
import argparse
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# --- Config (env-overridable) ----------------------------------------
BROKER_HOST = os.environ.get("SIGNGUARD_MQTT_HOST", "localhost")
BROKER_PORT = int(os.environ.get("SIGNGUARD_MQTT_PORT", "1883"))

TOPIC_EVENTS = "signguard/events"
TOPIC_CONTENT = "signguard/content"
TOPIC_COMMANDS = "signguard/commands"

# The signage node id, shared by the simple kit and the Layer 2 brain so one
# ESP32 flash reacts to both. Must match usb_demo/esp32/config.py DEVICE_ID.
DEVICE_ID = os.environ.get("SIGNGUARD_DEVICE_ID", "SG-RNP-001")
ATTACK_LABEL = "USB TAMPER"

# The authorized content id + genuine bytes the transport authority blessed.
# (Duplicated here on purpose - the edge side never imports app/.) Must match
# app/demo_scenarios.py BASELINE_CONTENT_ID + AUTHENTIC_TEXT so --mode event
# reverts to a HASH MATCH when the stick is removed.
CONTENT_ID = "CNT-101"
AUTHENTIC_TEXT = "TNSTC  •  Route 101\nRanipet → Vellore\nNext Bus: 10:30 AM"
TAMPERED_TEXT = "⚠ SYSTEM COMPROMISED\nUNAUTHORIZED MESSAGE"

# Volume serials of USB sticks you trust. Anything not here is an unauthorized
# USB -> tamper. Leave empty so EVERY inserted stick triggers the attack.
AUTHORIZED_USB_SERIALS: set[str] = set()

POLL_SECONDS = 1.0
DRIVE_REMOVABLE = 2   # GetDriveType return value for removable media


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def removable_drives() -> dict[str, str]:
    """Map of removable drive letter -> volume serial (hex). Windows only."""
    if not sys.platform.startswith("win"):
        return {}
    kernel32 = ctypes.windll.kernel32
    drives: dict[str, str] = {}
    bitmask = kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if not (bitmask >> i) & 1:
            continue
        root = f"{letter}:\\"
        if kernel32.GetDriveTypeW(root) != DRIVE_REMOVABLE:
            continue
        serial = ctypes.c_ulong(0)
        ok = kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(root), None, 0, ctypes.byref(serial),
            None, None, None, 0,
        )
        drives[letter] = f"{serial.value:08X}" if ok else "unknown"
    return drives


# --- Message builders -------------------------------------------------
def _event(event_type: str, authorized: bool, data: dict) -> str:
    return json.dumps({
        "device_id": DEVICE_ID,
        "event_type": event_type,
        "authorized": authorized,
        "timestamp": iso_now(),
        "data": data,
    })


def _content(text: str, source: str) -> str:
    return json.dumps({
        "device_id": DEVICE_ID,
        "content_id": CONTENT_ID,
        "content_bytes_b64": _b64(text),
        "source": source,
        "timestamp": iso_now(),
    })


def _command(command: str, attack: str = "") -> str:
    cmd = {"device_id": DEVICE_ID, "command": command}
    if attack:
        cmd["attack"] = attack
    return json.dumps(cmd)


# --- Publish flows ----------------------------------------------------
def attack_command(client) -> None:
    """Direct hardware: tell the sign it's a USB tamper."""
    client.publish(TOPIC_COMMANDS, _command("safe_fallback", ATTACK_LABEL), qos=1)
    print("[usb] --> command: safe_fallback (USB TAMPER) -> ESP32 TAMPER DETECTED")


def clear_command(client) -> None:
    client.publish(TOPIC_COMMANDS, _command("render"), qos=1)
    print("[usb] --> command: render -> ESP32 SYSTEM SECURE")


def attack_event(client) -> None:
    """Full brain: emit the USB attack telemetry; Layer 2 decides + blocks."""
    client.publish(TOPIC_EVENTS, _event("unauthorized_usb", False, {"vendor": "unknown"}), qos=1)
    client.publish(TOPIC_EVENTS, _event("content_received", False, {"content_id": CONTENT_ID, "source": "usb"}), qos=1)
    client.publish(TOPIC_EVENTS, _event("content_hash_mismatch", False, {"content_id": CONTENT_ID}), qos=1)
    client.publish(TOPIC_CONTENT, _content(TAMPERED_TEXT, "usb"), qos=1)
    print("[usb] --> events + tampered content -> Layer 2 (SHA-256 + AI + audit) blocks")


def clear_event(client) -> None:
    """Full brain: re-publish authentic content so Layer 2 renders again."""
    client.publish(TOPIC_CONTENT, _content(AUTHENTIC_TEXT, "network"), qos=1)
    print("[usb] --> authentic content re-published -> Layer 2 renders (SECURE)")


def main() -> None:
    ap = argparse.ArgumentParser(description="SignGuard Windows USB monitor")
    ap.add_argument("--mode", choices=("command", "event"), default="command",
                    help="command: drive the ESP32 directly (no backend). "
                         "event: full Layer 2 brain (run_demo.py must be up).")
    args = ap.parse_args()

    if not sys.platform.startswith("win"):
        print("[usb] Windows-only. On Linux use pi_usb_monitor.py.")
        return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{DEVICE_ID}-winusb")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    print(f"[usb] connected to broker {BROKER_HOST}:{BROKER_PORT}  (mode={args.mode})")
    print("[usb] monitoring removable drives... insert a USB stick to attack. Ctrl+C to stop.")

    fire_attack = attack_event if args.mode == "event" else attack_command
    fire_clear = clear_event if args.mode == "event" else clear_command

    known = removable_drives()
    while True:
        time.sleep(POLL_SECONDS)
        current = removable_drives()

        for letter, serial in current.items():
            if letter in known:
                continue
            authorized = serial in AUTHORIZED_USB_SERIALS
            print(f"[usb] inserted {letter}: serial={serial} "
                  f"({'authorized' if authorized else 'UNAUTHORIZED'})")
            if not authorized:
                fire_attack(client)

        for letter in list(known):
            if letter not in current:
                print(f"[usb] removed {letter}:")
                fire_clear(client)

        known = current


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[usb] stopped")
