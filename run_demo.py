"""One-command launcher for the SignGuard live demo.

Starts everything from a single terminal:
  1. Mosquitto (native, LAN-open via mosquitto.conf) so the ESP32 can connect
  2. the FastAPI app + in-process MQTT orchestrator (the brain)
  3. opens the dashboard in your browser

    python run_demo.py

Ctrl+C stops the API and shuts the broker down. Set MOSQUITTO_EXE if Mosquitto
is installed somewhere non-standard; set SIGNGUARD_HTTP_PORT to change the port.
"""
from __future__ import annotations

import os
import pathlib
import socket
import subprocess
import sys
import threading
import time
import webbrowser

ROOT = pathlib.Path(__file__).resolve().parent
CONF = ROOT / "mosquitto.conf"
HTTP_PORT = int(os.environ.get("SIGNGUARD_HTTP_PORT", "8000"))

_MOSQ_CANDIDATES = [
    os.environ.get("MOSQUITTO_EXE"),
    r"C:\Program Files\mosquitto\mosquitto.exe",
    r"C:\Program Files (x86)\mosquitto\mosquitto.exe",
    "mosquitto",  # PATH (Linux/mac)
]


def _find_mosquitto() -> str | None:
    for cand in _MOSQ_CANDIDATES:
        if not cand:
            continue
        if cand == "mosquitto" or pathlib.Path(cand).exists():
            return cand
    return None


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def _start_broker() -> subprocess.Popen | None:
    if _port_open("localhost", 1883):
        print("[demo] broker already listening on :1883 — reusing it")
        return None
    exe = _find_mosquitto()
    if exe is None:
        print("[demo] WARNING: mosquitto.exe not found — live triggers will be "
              "disabled. Install it or set MOSQUITTO_EXE.")
        return None
    print(f"[demo] starting Mosquitto: {exe} -c {CONF}")
    proc = subprocess.Popen([exe, "-c", str(CONF), "-v"])
    for _ in range(20):
        if _port_open("localhost", 1883):
            print("[demo] broker up on :1883")
            return proc
        time.sleep(0.25)
    print("[demo] WARNING: broker did not open :1883 in time")
    return proc


def _open_browser() -> None:
    # Wait until the app is actually serving before opening the browser — the
    # first boot imports scikit-learn/SHAP and trains the model (several seconds).
    for _ in range(60):  # up to ~30s
        if _port_open("localhost", HTTP_PORT):
            break
        time.sleep(0.5)
    else:
        print(f"[demo] server didn't come up on :{HTTP_PORT} in time")
        return
    time.sleep(0.4)
    print(f"[demo] opening http://localhost:{HTTP_PORT}/")
    webbrowser.open(f"http://localhost:{HTTP_PORT}/")


def main() -> None:
    broker = _start_broker()
    threading.Thread(target=_open_browser, daemon=True).start()

    # Import after the broker is up so the app's startup hook connects cleanly.
    import uvicorn

    print(f"[demo] dashboard -> http://localhost:{HTTP_PORT}/   (Ctrl+C to stop)")
    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=HTTP_PORT, log_level="warning")
    finally:
        if broker is not None:
            print("[demo] stopping broker…")
            broker.terminate()


if __name__ == "__main__":
    sys.exit(main())
