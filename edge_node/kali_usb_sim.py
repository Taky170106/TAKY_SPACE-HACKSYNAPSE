#!/usr/bin/env python3
"""
SignGuard — Kali-side simulated USB (attacker/operator).

Runs on the Kali VM (or any machine). It "inserts a USB stick" by writing a
content file into the shared pendrive folder that the USB detector watches.
No real device is needed — this is the controlled-lab origin of the attack.

    Kali VM  ->  writes pendrive/content.txt  ->  USB DETECTOR picks it up  -> ...

Usage (on the folder the detector watches, e.g. a share mounted on both sides):
    python -m edge_node.kali_usb_sim --attack                       # default attacker text
    python -m edge_node.kali_usb_sim --attack "BUS 101 CANCELLED|LEAVE THE AREA"
    python -m edge_node.kali_usb_sim --genuine "TNSTC Route 101|Next 10:30"
    python -m edge_node.kali_usb_sim --attack --path /mnt/share/pendrive
"""
from __future__ import annotations

import argparse
import pathlib

DEFAULT_DIR = "pendrive"
DEFAULT_ATTACK = "ALL SERVICES CANCELLED|LEAVE THE AREA"
DEFAULT_GENUINE = "TNSTC Route 101|Next 10:30"


def write_usb(folder: pathlib.Path, text: str) -> pathlib.Path:
    folder.mkdir(parents=True, exist_ok=True)
    f = folder / "content.txt"
    f.write_text(text, encoding="utf-8")
    return f


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulated USB writer (Kali side).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--attack", nargs="?", const=DEFAULT_ATTACK, metavar="TEXT",
                   help="write attacker content onto the 'USB'")
    g.add_argument("--genuine", nargs="?", const=DEFAULT_GENUINE, metavar="TEXT",
                   help="write authorized content onto the 'USB'")
    ap.add_argument("--path", default=DEFAULT_DIR, help="pendrive folder the detector watches")
    args = ap.parse_args()

    text = args.attack if args.attack is not None else args.genuine
    kind = "ATTACKER" if args.attack is not None else "AUTHORIZED"
    f = write_usb(pathlib.Path(args.path), text)
    print(f"[kali-usb] inserted {kind} USB -> {f}")
    print(f"[kali-usb] content: {text.replace(chr(10),' / ')!r}")
    print("[kali-usb] the USB detector will read this and POST it to SignGuard.")


if __name__ == "__main__":
    main()
