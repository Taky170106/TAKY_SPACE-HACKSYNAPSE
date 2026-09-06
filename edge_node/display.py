"""Display client — subscribes signguard/commands, shows RENDER / FALLBACK (§11).

This is the signage screen. It obeys Layer 2 commands:
    render        -> show the authorized content
    safe_fallback -> show the trusted fallback message (never blank/attacker)
    isolate       -> lock the update channel + show fallback

The fallback text is duplicated here (not fetched over the update channel) so a
compromised channel can never suppress or alter it (CLAUDE.md §10).
"""
from __future__ import annotations

import json

import paho.mqtt.client as mqtt

from edge_node.mqtt_config import BROKER_HOST, BROKER_PORT, TOPIC_COMMANDS

SAFE_FALLBACK_TEXT = (
    "Official Service Information\n"
    "Content update temporarily unavailable.\n"
    "Please contact official authorities for assistance."
)


def _render_screen(text: str) -> None:
    print("\n" + "=" * 48)
    print(text)
    print("=" * 48 + "\n")


def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties) -> None:
    client.subscribe(TOPIC_COMMANDS, qos=1)
    print(f"[display] connected, listening on {TOPIC_COMMANDS}")


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
    try:
        cmd = json.loads(msg.payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        print("[display] ignored malformed command")
        return

    device_id = cmd.get("device_id", "?")
    command = cmd.get("command")

    if command == "render":
        _render_screen(f"[{device_id}] VERIFIED CONTENT\nShowing authorized content.")
    elif command == "safe_fallback":
        _render_screen(f"[{device_id}] SAFE FALLBACK\n{SAFE_FALLBACK_TEXT}")
    elif command == "isolate":
        _render_screen(
            f"[{device_id}] ISOLATED — update channel locked\n{SAFE_FALLBACK_TEXT}"
        )
    else:
        print(f"[display] unknown command: {command!r}")


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edge-display")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    print("[display] press Ctrl+C to stop")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[display] shutting down")
        client.disconnect()


if __name__ == "__main__":
    main()
