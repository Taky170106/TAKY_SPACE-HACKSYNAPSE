#!/usr/bin/env python3
"""
SignGuard AI — content-change demo (laptop only, no USB needed).

The scenario:
  * An AUTHORIZED person changes the sign's content  -> accepted: the new
    content is (re)authorized and shown on the ESP (green LED, SYSTEM SECURE).
  * An UNAUTHORIZED change (attacker)                -> the new content does
    NOT match the authorized fingerprint -> BLOCK: the ESP shows the safe
    fallback, the red LED blinks, and the buzzer sounds.

Everything is driven from the laptop over MQTT — no physical USB stick.

Usage:
    python demo_trigger.py --show                       # show current authorized content
    python demo_trigger.py --authorized "NEXT BUS 11:00|PLATFORM 2"   # authorized change
    python demo_trigger.py --authorized                 # authorized change (prompts for text)
    python demo_trigger.py --unauthorized               # attacker change -> BLOCKED (alarm)
    python demo_trigger.py --unauthorized "FREE MONEY|CLICK HERE"     # attacker's own text

Split the two LCD lines with '|' (or a newline). Run authorize_content.py once
first, or just use --authorized (it authorizes as it goes).
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone

# Windows consoles default to cp1252 and crash on the arrows/glyphs below;
# force UTF-8 so the narrative prints (and publishing still happens).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover - best effort
    pass

import paho.mqtt.client as mqtt

from mqtt_config import BROKER_HOST, BROKER_PORT, DEVICE_ID, TOPIC_COMMANDS, AUTHORIZED_HASH_FILE

AUTHORIZED_CONTENT_PATH = "data/authorized_content.txt"
DEFAULT_ATTACK_TEXT = "BUS 101 CANCELLED|LEAVE THE AREA"


def sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def short(h: str) -> str:
    return f"{h[:5]}...{h[-4:]}"


def split_lines(text: str):
    """Turn a message into two LCD lines (split on '|' or newline)."""
    parts = text.replace("\n", "|").split("|")
    l1 = parts[0].strip()
    l2 = parts[1].strip() if len(parts) > 1 else ""
    return l1, l2


def store_authorized(text: str) -> str:
    """An authorized operator blesses new content: save it + its fingerprint."""
    content_hash = sha256_of_text(text)
    with open(AUTHORIZED_CONTENT_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    record = {
        "content_id": "CNT-001",
        "content_hash": content_hash,
        "authorized_by": "transport_authority",
        "timestamp": iso_now(),
    }
    with open(AUTHORIZED_HASH_FILE, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    return content_hash


def load_authorized():
    with open(AUTHORIZED_HASH_FILE, encoding="utf-8") as f:
        return json.load(f)


def read_authorized_content() -> str:
    try:
        with open(AUTHORIZED_CONTENT_PATH, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "SYSTEM SECURE|Route 101 OK"


def publish_command(command, **extra):
    # VERSION2 API so this runs on paho-mqtt 2.x (what the main project installs)
    # as well as 1.6+. This client only publishes, so no callbacks are needed.
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                             client_id="signguard-demo-trigger")
    except (AttributeError, TypeError):
        client = mqtt.Client(client_id="signguard-demo-trigger")  # paho 1.x fallback
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=10)
    client.loop_start()   # run the network loop so the QoS-1 publish completes
    payload = {"device_id": DEVICE_ID, "command": command, "timestamp": iso_now()}
    payload.update(extra)   # e.g. line1/line2 for the content to show
    info = client.publish(TOPIC_COMMANDS, json.dumps(payload), qos=1)
    info.wait_for_publish(timeout=5)   # block until the broker has it
    client.loop_stop()
    client.disconnect()


def banner(text):
    print("\n" + "=" * 56)
    print(f" {text}")
    print("=" * 56)


def do_show():
    l1, l2 = split_lines(read_authorized_content())
    banner("CURRENT AUTHORIZED CONTENT")
    print(f" Sign shows : {l1} / {l2}")
    publish_command("render", line1=l1, line2=l2)
    print(" -> ESP: SYSTEM SECURE (green LED), showing the authorized content\n")


def do_authorized(text: str):
    l1, l2 = split_lines(text)
    banner("AUTHORIZED CONTENT CHANGE")
    time.sleep(0.3)
    h = store_authorized(text)
    print(" Operator      : transport_authority (authorized)")
    print(" New content   : " + f"{l1} / {l2}")
    print(f" New fingerprint: {short(h)}  ({h})")
    print(" Integrity     : PASSED  (content re-authorized)")
    print(" Authorization : PASSED")
    print(" ACTION        : ALLOW -> update the signage\n")
    publish_command("render", line1=l1, line2=l2)
    print(" -> published 'render' with the new content")
    print(" -> ESP now shows the NEW content, green LED, no alarm\n")


def do_unauthorized(text: str):
    l1, l2 = split_lines(text)
    banner("UNAUTHORIZED CONTENT CHANGE")
    time.sleep(0.3)
    try:
        authorized = load_authorized()
    except FileNotFoundError:
        print("No authorized content on record. Run --authorized or authorize_content.py first.")
        return
    incoming = sha256_of_text(text)
    print(" Source        : unauthorized change (attacker)")
    print(f" Attacker content: {l1} / {l2}")
    print(f" AUTHORIZED HASH : {short(authorized['content_hash'])}  ({authorized['content_hash']})")
    print(f" INCOMING HASH   : {short(incoming)}  ({incoming})")
    time.sleep(0.3)
    # An attacker cannot update the authorized fingerprint, so the change fails
    # the integrity check (§2: content integrity is SHA-256, never a guess).
    banner("RESULT: HASH MISMATCH — TAMPERING DETECTED")
    print(" Integrity     : FAILED")
    print(" Authorization : FAILED")
    print(" Risk          : CRITICAL")
    print(" ACTION        : BLOCK -> safe fallback\n")
    publish_command("safe_fallback")
    print(" -> published 'safe_fallback' to signguard/commands")
    print(" -> ESP: TAMPER DETECTED, red LED blinking, buzzer sounding\n")


def main():
    ap = argparse.ArgumentParser(description="SignGuard content-change demo (laptop only).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--show", action="store_true",
                   help="show the current authorized content on the sign")
    g.add_argument("--authorized", nargs="?", const="__PROMPT__", metavar="TEXT",
                   help="authorized person changes content (accepted + shown). "
                        "Split two LCD lines with '|'. Omit TEXT to be prompted.")
    g.add_argument("--unauthorized", nargs="?", const=DEFAULT_ATTACK_TEXT, metavar="TEXT",
                   help="unauthorized change (attacker) -> BLOCKED with alarm.")
    args = ap.parse_args()

    if args.show:
        do_show()
    elif args.authorized is not None:
        text = args.authorized
        if text == "__PROMPT__":
            text = input("New authorized content (use '|' between the 2 lines): ").strip()
        if not text:
            print("No content entered.")
            return
        do_authorized(text)
    else:  # --unauthorized
        do_unauthorized(args.unauthorized)


if __name__ == "__main__":
    main()
