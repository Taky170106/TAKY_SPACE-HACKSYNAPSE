#!/usr/bin/env python3
"""
SignGuard AI — USB attack demo — Step A: authorize the real content.

Run this ONCE, before the demo, while the sign is showing legitimate content.
It hashes data/authorized_content.txt and stores that hash as the trusted
fingerprint that every later update gets checked against.

This mirrors CLAUDE.md's Content Authorization module (SHA-256 -> content
record) in a minimal, standalone form for a fast hardware-only demo.

Run:  python3 authorize_content.py
"""
import hashlib
import json
from datetime import datetime, timezone

from mqtt_config import AUTHORIZED_HASH_FILE

CONTENT_PATH = "data/authorized_content.txt"


def sha256_of_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    content_hash = sha256_of_file(CONTENT_PATH)
    record = {
        "content_id": "CNT-001",
        "content_hash": content_hash,
        "authorized_by": "transport_authority",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(AUTHORIZED_HASH_FILE, "w") as f:
        json.dump(record, f, indent=2)

    print("=" * 52)
    print(" CONTENT AUTHORIZED")
    print("=" * 52)
    print(f" content_id : {record['content_id']}")
    print(f" hash       : {content_hash}")
    print(f" authorized : {record['authorized_by']}")
    print(f" stored at  : {AUTHORIZED_HASH_FILE}")
    print("=" * 52)
    print("\nThe sign is now considered SECURE for this content.")
    print("Run demo_trigger.py --normal or --attack to test it.\n")


if __name__ == "__main__":
    main()
