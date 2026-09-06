"""Real-hardware edge clients (Raspberry Pi + ESP32).

These run ON the devices, not in CI. They publish the SAME frozen MQTT shapes as
the simulators (CLAUDE.md §4/§6) so Layer 2 cannot tell hardware from simulator.
The Pi scripts (CPython) reuse edge_node.mqtt_config; the ESP32 script is
standalone MicroPython with its own config.py.
"""
