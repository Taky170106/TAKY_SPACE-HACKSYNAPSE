"""Layer 2 MQTT orchestrator — the live bridge that closes the loop (§4/§11).

Subscribes to the edge's telemetry, runs the shared analysis pipeline, and
publishes a command back to the signage:

    signguard/events   ─┐
    signguard/content  ─┴─►  run_analysis()  ──►  signguard/commands

This is what makes `display.py` (and the ESP32) react on their own. It reuses
the exact same `run_analysis` pipeline as `POST /analyze`, so REST and MQTT can
never disagree. Content integrity still gates everything (§2); the audit trail
(§11) is written by the pipeline for every decision, regardless of transport.

Run it (with the broker up):
    python -m app.orchestrator                 # authorizes the demo baseline too
    python -m app.orchestrator --no-baseline   # don't seed a baseline authorization
"""
from __future__ import annotations

import argparse
import base64
import json
import sys

from pydantic import ValidationError

# Windows consoles default to cp1252; force UTF-8 so glyphs render.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - best-effort
    pass

from app.authorization import authorize_content
from app.deps import registry
from app.ingestion import EventStore
from app.pipeline import run_analysis
from app.schemas import AnalyzeRequest, Command, CommandType, ContentUpdate, SecurityEvent

# FROZEN topics (§4). Duplicated as string constants (do not import edge_node).
TOPIC_EVENTS = "signguard/events"
TOPIC_CONTENT = "signguard/content"
TOPIC_COMMANDS = "signguard/commands"

# The content the transport authority has blessed for the demo baseline — kept
# in one place (demo_scenarios) so authorization and the scenarios never drift.
from app.demo_scenarios import AUTHENTIC as DEMO_BASELINE_CONTENT
from app.demo_scenarios import BASELINE_CONTENT_ID as DEMO_BASELINE_CONTENT_ID

# How far back to look for a device's events when scoring (matches Track B window).
WINDOW_SECONDS = 24 * 3600


class Orchestrator:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        on_analysis=None,
    ) -> None:
        self.host = host
        self.port = port
        self.store = EventStore()
        self._last_command: dict[str, str] = {}
        self._last_content: dict[str, ContentUpdate] = {}
        self._client = None
        # Optional callback fired for EVERY analysis: on_analysis(device_id, result).
        # Used by the web dashboard to push live updates; hardware command publishing
        # below stays deduped so the signage isn't spammed.
        self._on_analysis = on_analysis

    # -- MQTT plumbing ----------------------------------------------------- #
    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        client.subscribe(TOPIC_EVENTS, qos=1)
        client.subscribe(TOPIC_CONTENT, qos=1)
        print(f"[orchestrator] subscribed to {TOPIC_EVENTS} + {TOPIC_CONTENT}")

    def _on_message(self, client, userdata, msg) -> None:
        if msg.topic == TOPIC_EVENTS:
            self._handle_event(msg.payload)
        elif msg.topic == TOPIC_CONTENT:
            self._handle_content(msg.payload)

    # -- Message handlers -------------------------------------------------- #
    def _handle_event(self, payload: bytes) -> None:
        try:
            event = SecurityEvent.model_validate_json(payload)
        except ValidationError:
            print("[orchestrator] dropped malformed event")
            return
        self.store.add(event)
        print(f"[event] {event.device_id:<10} {event.event_type.value}")
        self._decide_and_publish(event.device_id, anchor=event.timestamp)

    def _handle_content(self, payload: bytes) -> None:
        try:
            content = ContentUpdate.model_validate_json(payload)
        except ValidationError:
            print("[orchestrator] dropped malformed content update")
            return
        self._last_content[content.device_id] = content
        size = len(base64.b64decode(content.content_bytes_b64))
        print(f"[content] {content.device_id:<10} {content.content_id} ({size} bytes)")
        self._decide_and_publish(content.device_id, anchor=content.timestamp)

    # -- The decision + publish loop --------------------------------------- #
    def _decide_and_publish(self, device_id: str, anchor) -> None:
        events = self.store.recent(device_id, WINDOW_SECONDS, now=anchor)
        req = AnalyzeRequest(
            device_id=device_id,
            content_update=self._last_content.get(device_id),
            events=events,
        )
        result = run_analysis(req)
        decision = result.decision
        command = decision.recommended_action

        # Fire the live callback on EVERY analysis (dashboard updates every time).
        if self._on_analysis is not None:
            try:
                self._on_analysis(device_id, result)
            except Exception as exc:  # noqa: BLE001 - never let a UI hook break the loop
                print(f"[orchestrator] on_analysis hook error: {exc}")

        # Only publish a hardware command on a state change, so the signage
        # (ESP32 LCD / buzzer) isn't spammed with identical commands.
        if self._last_command.get(device_id) == command.value:
            return
        self._last_command[device_id] = command.value

        self._publish_command(device_id, command)
        risk = result.risk_score.score if result.risk_score else 0
        print(
            f"[layer2] {device_id:<10} -> {decision.decision.upper()} "
            f"(risk {risk}, {', '.join(decision.reasons)})"
        )

    def _publish_command(
        self, device_id: str, command: CommandType, attack: str | None = None,
        line1: str | None = None, line2: str | None = None,
    ) -> None:
        cmd = Command(device_id=device_id, command=command)
        # Keep the frozen Command fields; add optional extras on the wire so the
        # ESP LCD can show the attack label and the real content lines.
        payload = json.loads(cmd.model_dump_json())
        if attack:
            payload["attack"] = attack
        if line1 is not None:
            payload["line1"] = line1
            payload["line2"] = line2 or ""
        self._client.publish(TOPIC_COMMANDS, json.dumps(payload), qos=1)

    def publish_command(
        self, device_id: str, command: CommandType, attack: str | None = None,
        line1: str | None = None, line2: str | None = None,
    ) -> None:
        """Publish a command to the signage (used by the dashboard trigger)."""
        if self._client is not None:
            self._publish_command(device_id, command, attack, line1, line2)

    def inject(self, scenario, now=None) -> None:
        """Publish a scenario's events + content onto the broker (demo trigger).

        Flows through the normal path — the orchestrator receives its own
        published messages, analyses them, and drives hardware + dashboard.
        """
        events, content = scenario.build(now)
        for ev in events:
            self._client.publish(TOPIC_EVENTS, ev.model_dump_json(), qos=1)
        if content is not None:
            self._client.publish(TOPIC_CONTENT, content.model_dump_json(), qos=1)

    def _build_client(self):
        import paho.mqtt.client as mqtt

        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id="layer2-orchestrator"
        )
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        return client

    # -- Lifecycle --------------------------------------------------------- #
    def start_background(self, retries: int = 10, delay: float = 0.5) -> bool:
        """Connect + start paho's own network thread (non-blocking).

        Retries so it survives a broker that is still coming up. Returns True on
        success, False if the broker never became reachable.
        """
        import time

        self._client = self._build_client()
        for attempt in range(1, retries + 1):
            try:
                self._client.connect(self.host, self.port, keepalive=60)
                self._client.loop_start()
                return True
            except OSError as exc:
                print(f"[orchestrator] broker not ready ({attempt}/{retries}): {exc}")
                time.sleep(delay)
        return False

    def stop(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()

    def run(self) -> None:
        self._client = self._build_client()
        self._client.connect(self.host, self.port, keepalive=60)
        print("[orchestrator] running — Ctrl+C to stop")
        try:
            self._client.loop_forever()
        except KeyboardInterrupt:
            print("\n[orchestrator] shutting down")
            self._client.disconnect()


def _authorize_baseline() -> None:
    record = authorize_content(
        registry, DEMO_BASELINE_CONTENT_ID, DEMO_BASELINE_CONTENT, "transport_authority"
    )
    print(
        f"[orchestrator] authorized baseline {record.content_id} "
        f"({record.content_hash[:12]}…)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Layer 2 MQTT orchestrator.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="do not seed the demo baseline authorization",
    )
    args = parser.parse_args()

    if not args.no_baseline:
        _authorize_baseline()

    Orchestrator(host=args.host, port=args.port).run()


if __name__ == "__main__":
    main()
