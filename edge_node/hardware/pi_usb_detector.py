#!/usr/bin/env python3
"""
SignGuard AI — Raspberry Pi USB DETECTOR (reads the real pendrive).

Upgrade of pi_usb_monitor.py. On a REAL USB insertion it:
  1. detects the insert via udev,
  2. waits for the OS to auto-mount the stick,
  3. reads the signage content file from the stick,
  4. POSTs the content to the SignGuard backend at /ingest/usb (HTTP).

The backend then does SHA-256 verify + AI + decision and publishes the MQTT
command that lights up the ESP-12E (LCD + buzzer). This matches the diagram:

    Pendrive -> Pi USB DETECTOR -> HTTP -> FastAPI -> decision -> MQTT -> ESP-12E

Put a file named `signage.txt` (or any .txt) on the USB stick. Two LCD lines:
split with '|', e.g.  TNSTC Route 101|Next 10:30

Run on the Pi:  python3 pi_usb_detector.py
(sudo may be needed for udev; ensure API_URL points at the laptop backend.)

Requires: pyudev, and the backend reachable over HTTP. No paho needed here —
the backend publishes the MQTT command.
"""
import json
import time
import urllib.request
import glob
import os

import pyudev

import pi_config as cfg

# Where the SignGuard backend runs. If the backend is on the laptop, use its LAN
# IP, e.g. "http://192.168.7.174:8000". Falls back to the broker host.
API_URL = getattr(cfg, "API_URL", f"http://{cfg.BROKER_HOST}:8000")
CONTENT_NAMES = ("signage.txt", "content.txt")   # preferred filenames on the stick
MOUNT_WAIT_S = 8                                  # how long to wait for auto-mount


def find_mountpoint(devnode: str) -> str | None:
    """Return the mount path for a block device (parses /proc/mounts)."""
    try:
        with open("/proc/mounts") as f:
            for line in f:
                dev, mnt = line.split()[0], line.split()[1]
                if dev == devnode:
                    return mnt.replace("\\040", " ")
    except Exception:
        pass
    return None


def read_stick_content(mountpoint: str) -> str | None:
    """Read the signage content file from the mounted stick."""
    for name in CONTENT_NAMES:
        p = os.path.join(mountpoint, name)
        if os.path.exists(p):
            return open(p, encoding="utf-8", errors="replace").read().strip()
    # fall back to the first .txt on the stick
    txts = sorted(glob.glob(os.path.join(mountpoint, "*.txt")))
    if txts:
        return open(txts[0], encoding="utf-8", errors="replace").read().strip()
    return None


def post_ingest(content: str, serial: str) -> dict:
    body = json.dumps({"content": content, "source": "usb", "serial": serial}).encode()
    req = urllib.request.Request(
        API_URL.rstrip("/") + "/ingest/usb", data=body,
        headers={"content-type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def handle_partition(devnode: str, serial: str) -> None:
    # wait for auto-mount
    mnt = None
    for _ in range(MOUNT_WAIT_S * 2):
        mnt = find_mountpoint(devnode)
        if mnt:
            break
        time.sleep(0.5)
    if not mnt:
        print(f"[pi-usb] {devnode} not auto-mounted; mount it and retry.")
        return

    content = read_stick_content(mnt)
    if content is None:
        print(f"[pi-usb] no signage.txt/.txt found on {mnt}")
        return

    preview = content.replace("\n", " / ")[:48]
    print(f"[pi-usb] read from stick: {preview!r}  -> POST /ingest/usb")
    try:
        r = post_ingest(content, serial)
        verd = "VERIFIED" if r.get("verified") else "TAMPERED"
        print(f"[pi-usb] {verd}  decision={r.get('decision')}  risk={r.get('risk')}  "
              f"hardware={r.get('hardware_notified')}")
    except Exception as e:  # noqa: BLE001
        print(f"[pi-usb] POST failed: {e}")


def main():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="block")   # partitions mount as block devices
    print(f"[pi-usb] detector ready -> {API_URL}/ingest/usb")
    print("[pi-usb] insert a USB stick with signage.txt on it...")

    for device in iter(monitor.poll, None):
        if device.action != "add":
            continue
        if device.get("DEVTYPE") != "partition":
            continue
        devnode = device.device_node                       # e.g. /dev/sda1
        serial = device.get("ID_SERIAL_SHORT") or "unknown"
        authorized = serial in cfg.AUTHORIZED_USB_SERIALS
        tag = "authorized" if authorized else "UNAUTHORIZED"
        print(f"[pi-usb] USB inserted: {devnode} serial={serial} ({tag})")
        handle_partition(devnode, serial)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[pi-usb] stopped")
