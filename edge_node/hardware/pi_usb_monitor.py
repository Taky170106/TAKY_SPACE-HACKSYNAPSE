#!/usr/bin/env python3
"""
SignGuard AI — Raspberry Pi USB monitor.

Watches the OS USB subsystem with udev. When a USB device is inserted it
checks the device serial against an authorized whitelist and publishes a
security_event to MQTT:

  - known serial   -> usb_connected     (authorized: true)
  - unknown serial -> unauthorized_usb  (authorized: false)

Matches CLAUDE.md #6 security_event schema. Topic: signguard/events.

Run:  python3 pi_usb_monitor.py
(You may need sudo depending on your udev permissions.)
"""
import json
from datetime import datetime, timezone

import pyudev
import paho.mqtt.client as mqtt

import pi_config as cfg


def iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_event(event_type, authorized, data):
    return {
        "device_id": cfg.DEVICE_ID,
        "event_type": event_type,
        "authorized": authorized,
        "timestamp": iso_now(),
        "data": data,
    }


def main():
    # CallbackAPIVersion.VERSION2 keeps this working on paho-mqtt 2.x (the
    # version `requirements.txt` installs); the legacy call raised on 2.x.
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2, client_id=f"{cfg.DEVICE_ID}-usb"
    )
    client.connect(cfg.BROKER_HOST, cfg.BROKER_PORT, keepalive=60)
    client.loop_start()
    print(f"[usb] connected to broker {cfg.BROKER_HOST}:{cfg.BROKER_PORT}")

    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="usb")
    print("[usb] monitoring USB subsystem... insert a device to test")

    for device in iter(monitor.poll, None):
        # React only to whole-device additions (ignore per-interface noise).
        if device.action != "add":
            continue
        if device.get("DEVTYPE") != "usb_device":
            continue

        serial = device.get("ID_SERIAL_SHORT") or device.get("ID_SERIAL") or "unknown"
        vendor = device.get("ID_VENDOR") or "unknown"
        model = device.get("ID_MODEL") or "unknown"

        authorized = serial in cfg.AUTHORIZED_USB_SERIALS
        event_type = "usb_connected" if authorized else "unauthorized_usb"

        event = make_event(
            event_type,
            authorized,
            {"serial": serial, "vendor": vendor, "model": model},
        )
        client.publish(cfg.TOPIC_EVENTS, json.dumps(event), qos=1)
        tag = "authorized" if authorized else "UNAUTHORIZED"
        print(f"[usb] {event_type}: {vendor} {model} serial={serial} ({tag})")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[usb] stopped")
