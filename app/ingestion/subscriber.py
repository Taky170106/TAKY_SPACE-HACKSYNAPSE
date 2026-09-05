"""MQTT ingestion — subscribe, validate, normalize, store (§11 ingestion).

Subscribes to signguard/events, validates each payload into a SecurityEvent
(dropping malformed messages), and stores it. Offline dev seeds the same store
from data/sample_events.json without a broker (CLAUDE.md §12).
"""
from __future__ import annotations

import json
import pathlib

from pydantic import ValidationError

from app.ingestion.store import EventStore
from app.schemas import SecurityEvent

# FROZEN topic (§4) — duplicated here rather than importing edge_node (separate component).
TOPIC_EVENTS = "signguard/events"

DEFAULT_SAMPLE = pathlib.Path(__file__).resolve().parents[2] / "data" / "sample_events.json"


def load_events_from_file(store: EventStore, path: pathlib.Path = DEFAULT_SAMPLE) -> int:
    """Seed `store` from a JSON array of events. Returns count ingested."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    count = 0
    for item in raw:
        try:
            store.add(SecurityEvent.model_validate(item))
            count += 1
        except ValidationError as exc:
            print(f"[ingestion] dropped invalid event: {exc.error_count()} error(s)")
    return count


class IngestionService:
    """Live MQTT ingestion into an EventStore. Optional — Track B works offline."""

    def __init__(self, store: EventStore, host: str = "localhost", port: int = 1883) -> None:
        self.store = store
        self.host = host
        self.port = port
        self._client = None

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        client.subscribe(TOPIC_EVENTS, qos=1)
        print(f"[ingestion] subscribed to {TOPIC_EVENTS}")

    def _on_message(self, client, userdata, msg) -> None:
        try:
            event = SecurityEvent.model_validate_json(msg.payload)
        except ValidationError:
            print("[ingestion] dropped malformed event")
            return
        self.store.add(event)

    def start(self) -> None:
        # Imported here so Track B has no hard dependency on paho when run offline.
        import paho.mqtt.client as mqtt

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="layer2-ingestion")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.connect(self.host, self.port, keepalive=60)
        self._client.loop_start()

    def stop(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
