"""Content simulator — publishes content_updates to signguard/content (§11).

Two modes to drive the Track A demo:
    --mode authentic   publish content whose bytes match what was authorized
    --mode tampered    publish attacker-modified bytes (hash will MISMATCH)

Usage:
    python -m edge_node.content_simulator --content-id CNT-001 --mode authentic
    python -m edge_node.content_simulator --content-id CNT-001 --mode tampered
"""
from __future__ import annotations

import argparse
import base64
import json
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from edge_node.mqtt_config import BROKER_HOST, BROKER_PORT, TOPIC_CONTENT

# The "authorized" content the transport authority blessed (demo baseline).
AUTHENTIC_CONTENT = b"Platform 2: Train to Central departs 10:45."
TAMPERED_CONTENT = b"Platform 2: FREE WIFI click http://evil.example to claim."


def _connect() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edge-content-sim")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    return client


def publish(device_id: str, content_id: str, content: bytes, source: str) -> None:
    update = {
        "device_id": device_id,
        "content_id": content_id,
        "content_bytes_b64": base64.b64encode(content).decode("ascii"),
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    client = _connect()
    try:
        client.publish(TOPIC_CONTENT, json.dumps(update), qos=1)
        print(f"[content] {content_id} via {source} ({len(content)} bytes) -> {TOPIC_CONTENT}")
    finally:
        client.loop_stop()
        client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a content update over MQTT.")
    parser.add_argument("--device-id", default="SG-RNP-001")
    parser.add_argument("--content-id", default="CNT-001")
    parser.add_argument("--mode", choices=["authentic", "tampered"], default="authentic")
    parser.add_argument("--source", default="usb")
    args = parser.parse_args()

    content = AUTHENTIC_CONTENT if args.mode == "authentic" else TAMPERED_CONTENT
    publish(args.device_id, args.content_id, content, args.source)


if __name__ == "__main__":
    main()
