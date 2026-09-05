"""MQTT connection + topic constants shared by the edge simulators (§4).

Topics are FROZEN (CLAUDE.md §4). The edge node duplicates only these string
constants; it must never import from app/ (the two talk only over MQTT).
"""
from __future__ import annotations

import os

BROKER_HOST = os.environ.get("SIGNGUARD_MQTT_HOST", "localhost")
BROKER_PORT = int(os.environ.get("SIGNGUARD_MQTT_PORT", "1883"))

# FROZEN topic names — must match app/ ingestion and decision publisher.
TOPIC_EVENTS = "signguard/events"
TOPIC_CONTENT = "signguard/content"
TOPIC_COMMANDS = "signguard/commands"
