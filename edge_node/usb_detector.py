#!/usr/bin/env python3
"""
SignGuard — USB detector (edge).

Watches a mount/folder that represents an inserted USB pendrive (in the demo this
is a shared folder written by the Kali VM). When a content file appears/changes,
it reads the text, and POSTs it to the SignGuard backend at /ingest/usb over HTTP.

The backend then does SHA-256 verify + AI + decision and publishes the MQTT
command to the ESP-12E. This closes the diagram:

    Kali VM -> simulated USB -> USB DETECTOR -> HTTP -> FastAPI -> ... -> ESP

Usage:
    python -m edge_node.usb_detector                       # watch ./pendrive/content.txt
    python -m edge_node.usb_detector --path D:/shared/usb  # watch a folder
    python -m edge_node.usb_detector --once                # send once and exit
    python -m edge_node.usb_detector --api http://localhost:8000
"""
from __future__ import annotations

import argparse
import pathlib
import time

import urllib.request
import json

DEFAULT_API = "http://localhost:8000"
DEFAULT_FILE = "pendrive/content.txt"


def read_content(path: pathlib.Path) -> str | None:
    if path.is_dir():
        # first .txt file in the folder = the "content" on the stick
        files = sorted(path.glob("*.txt"))
        path = files[0] if files else None
    if not path or not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace").strip()


def post_ingest(api: str, content: str, serial: str) -> dict:
    body = json.dumps({"content": content, "source": "usb", "serial": serial}).encode()
    req = urllib.request.Request(
        api.rstrip("/") + "/ingest/usb", data=body,
        headers={"content-type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def announce(result: dict) -> None:
    v = result.get("verified")
    tag = "VERIFIED" if v else ("TAMPERED" if v is False else "?")
    print(f"[usb-detector] {tag}  decision={result.get('decision')}  "
          f"risk={result.get('risk')}  hardware={result.get('hardware_notified')}")


def main() -> None:
    ap = argparse.ArgumentParser(description="SignGuard USB detector -> HTTP -> FastAPI")
    ap.add_argument("--path", default=DEFAULT_FILE, help="file or folder representing the USB")
    ap.add_argument("--api", default=DEFAULT_API, help="SignGuard backend base URL")
    ap.add_argument("--serial", default="USB-DEMO-001", help="USB serial to report")
    ap.add_argument("--once", action="store_true", help="send once and exit")
    ap.add_argument("--interval", type=float, default=1.0, help="poll seconds")
    args = ap.parse_args()

    path = pathlib.Path(args.path)
    print(f"[usb-detector] watching {path}  ->  {args.api}/ingest/usb")

    last = None
    while True:
        content = read_content(path)
        if content is not None and (content != last or args.once):
            last = content
            preview = content.replace("\n", " / ")[:48]
            print(f"[usb-detector] USB content read: {preview!r}")
            try:
                announce(post_ingest(args.api, content, args.serial))
            except Exception as e:  # noqa: BLE001
                print(f"[usb-detector] POST failed: {e}")
            if args.once:
                return
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[usb-detector] stopped")
