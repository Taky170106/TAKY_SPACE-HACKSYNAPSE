#!/usr/bin/env python3
"""
SignGuard — "insert a USB stick" into the virtual pendrive (no hardware).

Writes content into pendrive.img with a serial. The virtual Pi (pi_sim.py) sees
the new image and reads it, exactly like plugging a real stick into a real Pi.

    python -m edge_node.sim.insert_usb --attack        # tampered stick -> BLOCK
    python -m edge_node.sim.insert_usb --genuine        # authorized stick -> RENDER
    python -m edge_node.sim.insert_usb --attack "BUS 101 CANCELLED|LEAVE THE AREA"
    python -m edge_node.sim.insert_usb --genuine "TNSTC Route 101|Next 10:30" --serial MAINT-01
"""
from __future__ import annotations

import argparse
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_IMG = HERE / "pendrive.img"
MAGIC = b"SGUSB1\n"
DEFAULT_ATTACK = "ALL SERVICES CANCELLED|LEAVE THE AREA"
DEFAULT_GENUINE = "TNSTC Route 101|Next 10:30"


def write_stick(img: pathlib.Path, content: str, serial: str) -> None:
    meta = {"serial": serial, "content": content, "files": ["signage.txt"]}
    img.write_bytes(MAGIC + json.dumps(meta).encode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Insert a virtual USB stick.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--attack", nargs="?", const=DEFAULT_ATTACK, metavar="TEXT")
    g.add_argument("--genuine", nargs="?", const=DEFAULT_GENUINE, metavar="TEXT")
    ap.add_argument("--img", default=str(DEFAULT_IMG))
    ap.add_argument("--serial", default=None, help="USB serial (default depends on kind)")
    args = ap.parse_args()

    if args.attack is not None:
        content, serial = args.attack, args.serial or "ATTACKER-USB-666"
        kind = "ATTACKER"
    else:
        content, serial = args.genuine, args.serial or "MAINT-USB-001"
        kind = "AUTHORIZED"

    write_stick(pathlib.Path(args.img), content, serial)
    print(f"[insert-usb] plugged in {kind} stick  serial={serial}")
    print(f"[insert-usb] signage.txt = {content.replace(chr(10), ' / ')!r}")
    print("[insert-usb] the virtual Pi will detect and read it now.")


if __name__ == "__main__":
    main()
