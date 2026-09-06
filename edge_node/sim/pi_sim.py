#!/usr/bin/env python3
"""
SignGuard — VIRTUAL Raspberry Pi USB detector (no hardware needed).

Simulates a Raspberry Pi edge node. It watches a virtual USB image file
(pendrive.img). When you "insert" a stick (insert_usb.py writes the image), the
virtual Pi "mounts" it, reads the signage content, and POSTs it to the SignGuard
backend at /ingest/usb — exactly like the real Pi detector, but with zero
hardware. Prints Raspberry-Pi-style logs so it reads convincingly on a panel.

    insert_usb.py  ->  pendrive.img  ->  [VIRTUAL PI]  ->  HTTP  ->  FastAPI  -> ESP/signage

Run:
    python -m edge_node.sim.pi_sim
    python -m edge_node.sim.pi_sim --api http://localhost:8000
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_IMG = HERE / "pendrive.img"
DEFAULT_API = "http://localhost:8000"
MAGIC = b"SGUSB1\n"   # tiny header so we know a stick is "present"


def read_image(img: pathlib.Path):
    """Return (serial, content) if a stick is present in the image, else None."""
    if not img.exists():
        return None
    raw = img.read_bytes()
    if not raw.startswith(MAGIC):
        return None
    body = raw[len(MAGIC):]
    try:
        meta = json.loads(body.decode("utf-8"))
        return meta.get("serial", "SIM-USB-0001"), meta.get("content", "")
    except Exception:
        return "SIM-USB-0001", body.decode("utf-8", "replace")


def post_ingest(api: str, content: str, serial: str) -> dict:
    body = json.dumps({"content": content, "source": "usb", "serial": serial}).encode()
    req = urllib.request.Request(
        api.rstrip("/") + "/ingest/usb", data=body,
        headers={"content-type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def boot_banner(api: str) -> None:
    print("=" * 56)
    print(" SignGuard Edge Node  —  Raspberry Pi (virtual)")
    print("=" * 56)
    for line in (
        "[    0.000000] Booting Linux on physical CPU 0x0",
        "[    1.204813] usbcore: registered new interface driver usb-storage",
        "[    1.910042] systemd[1]: Started SignGuard USB detector.",
        f"[  ok  ] backend  : {api}/ingest/usb",
        "[  ok  ] udev     : monitoring block subsystem",
    ):
        print(line); time.sleep(0.15)
    print("[pi] insert a USB stick with insert_usb.py ...\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Virtual Raspberry Pi USB detector.")
    ap.add_argument("--img", default=str(DEFAULT_IMG), help="virtual pendrive image")
    ap.add_argument("--api", default=DEFAULT_API, help="SignGuard backend base URL")
    ap.add_argument("--interval", type=float, default=0.5)
    args = ap.parse_args()

    img = pathlib.Path(args.img)
    boot_banner(args.api)

    last_sig = None
    while True:
        stick = read_image(img)
        sig = img.stat().st_mtime if img.exists() else None
        if stick and sig != last_sig:
            last_sig = sig
            serial, content = stick
            preview = content.replace("\n", " / ")[:48]
            print(f"[pi] udev: USB inserted  serial={serial}  (/dev/sda1)")
            print(f"[pi] mount /dev/sda1 -> /media/pi/SIGNAGE  (read signage.txt)")
            print(f"[pi] content read: {preview!r}")
            print(f"[pi] POST -> {args.api}/ingest/usb")
            try:
                r = post_ingest(args.api, content, serial)
                verd = "VERIFIED  ✓" if r.get("verified") else "TAMPERED  ✗"
                print(f"[pi] SignGuard: {verd}   decision={r.get('decision')}   "
                      f"risk={r.get('risk')}   ESP={'notified' if r.get('hardware_notified') else 'n/a'}\n")
            except Exception as e:  # noqa: BLE001
                print(f"[pi] POST failed (is the backend running?): {e}\n")
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[pi] shutting down")
