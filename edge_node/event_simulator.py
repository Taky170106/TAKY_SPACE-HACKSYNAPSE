"""Event simulator — publishes security_events to signguard/events (§11).

Replays data/sample_events.json (or a --file) onto the broker so Layer 2 can be
exercised end-to-end without real hardware.

Usage:
    python -m edge_node.event_simulator                # replay sample events
    python -m edge_node.event_simulator --delay 0.5    # slower, for the demo
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import paho.mqtt.client as mqtt

from edge_node.mqtt_config import BROKER_HOST, BROKER_PORT, TOPIC_EVENTS

DEFAULT_FILE = pathlib.Path(__file__).resolve().parents[1] / "data" / "sample_events.json"


def _connect() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edge-event-sim")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    return client


def replay(path: pathlib.Path, delay: float) -> None:
    events = json.loads(path.read_text(encoding="utf-8"))
    client = _connect()
    try:
        for ev in events:
            payload = json.dumps(ev)
            client.publish(TOPIC_EVENTS, payload, qos=1)
            print(f"[event] {ev['device_id']:<10} {ev['event_type']}")
            time.sleep(delay)
    finally:
        client.loop_stop()
        client.disconnect()
    print(f"Published {len(events)} events to {TOPIC_EVENTS}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay security events over MQTT.")
    parser.add_argument("--file", type=pathlib.Path, default=DEFAULT_FILE)
    parser.add_argument("--delay", type=float, default=0.2, help="seconds between events")
    args = parser.parse_args()
    replay(args.file, args.delay)


if __name__ == "__main__":
    main()
