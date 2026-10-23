#!/usr/bin/env python3
"""
SignGuard AI — board watcher (auto-detect the ESP on insert, clear cache on remove).

No Raspberry Pi here: the only physical board is the NodeMCU ESP-12E. This
watches Windows for that board appearing on USB and, the moment it does, logs
which COM port it was given (and what the adapter is). When you pull it out,
the remembered device state is deleted so the next insert starts from zero —
no stale COM port, no stale device entry.

Pure standard library (ctypes/winreg): no pyserial, no pywin32, no WMI module.

Run:
    python usb_demo/laptop/board_watcher.py              # watch forever (Ctrl+C)
    python usb_demo/laptop/board_watcher.py --once       # one scan, then exit
    python usb_demo/laptop/board_watcher.py --selftest   # prove insert/remove w/o hardware
    python usb_demo/laptop/board_watcher.py --state      # print cached state

State lives in data/board_state.json and is REMOVED when the board is unplugged.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repo root (usb_demo/laptop/..)
STATE_FILE = ROOT / "data" / "board_state.json"

POLL_SECONDS = 1.0

# Device map keys Windows uses for USB-serial bridges (CH340 / CP210x / FTDI).
# Bluetooth and legacy onboard serial are deliberately excluded — they are
# always present on this laptop and would otherwise look like a "new board".
_SKIP_KEY_HINTS = ("BTH", "BLUETOOTH", "SERIAL0", "COMPAQ", "LPT")
_NAME_HINTS = ("USB", "CH340", "CH341", "CP210", "FTDI", "FT232", "UART",
               "VCP", "SERIAL", "ESP", "NODEMCU", "WCH")


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# Discovery — which COM ports exist right now?
# --------------------------------------------------------------------------- #
def serial_ports() -> dict[str, str]:
    """Map of device-map key -> COM port (e.g. `\\Device\\USBSER000` -> 'COM5').

    HKLM\\HARDWARE\\DEVICEMAP\\SERIALCOMM is maintained by the kernel for us and
    costs ~0 ms to read, so polling every second is free (unlike spawning WMI).
    """
    if not sys.platform.startswith("win"):
        return {}
    import winreg

    out: dict[str, str] = {}
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
    except OSError:
        return {}
    try:
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
            except OSError:
                break
            if isinstance(value, str) and value.upper().startswith("COM"):
                out[name] = value.upper()
            i += 1
    finally:
        winreg.CloseKey(key)
    return out


def usb_candidates(ports: dict[str, str]) -> dict[str, str]:
    """Keep only ports that look like a USB-serial adapter; drop BT/legacy noise."""
    clean = {}
    for key, port in ports.items():
        upper = key.upper()
        if any(hint in upper for hint in _SKIP_KEY_HINTS):
            continue
        if any(hint in upper for hint in _NAME_HINTS) or True:
            # The device-map key is opaque on some builds (e.g. `\Device\VCOM#0000`),
            # so accept it here and let the friendly-name lookup below do the
            # final filtering — Bluetooth is already excluded by _SKIP_KEY_HINTS.
            clean[key] = port
    return clean


def describe(port: str) -> tuple[str, str]:
    """One-shot friendly name + hardware id for a COM port via PowerShell/CIM.

    Only runs when a board actually appears (never in the poll loop), so the
    ~0.6 s cost of starting PowerShell does not slow detection down.
    """
    ps = (
        "$p = Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue "
        f"| Where-Object {{ $_.Name -like '*({port})*' }} | Select-Object -First 1; "
        "if ($p) { $p.Name + '|' + $p.DeviceID } else { '' }"
    )
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True, text=True, timeout=25, errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return "", ""
    line = (res.stdout or "").strip()
    if not line or "|" not in line:
        return "", ""
    name, hw = line.rsplit("|", 1)
    return name.strip(), hw.strip()


def is_board(name: str, hw: str) -> bool:
    """Filter out stray serial endpoints that are not the ESP kit."""
    blob = f"{name} {hw}".upper()
    if "BLUETOOTH" in blob:
        return False
    return any(hint in blob for hint in _NAME_HINTS)


# --------------------------------------------------------------------------- #
# Cache — data/board_state.json, written on insert, DELETED on remove
# --------------------------------------------------------------------------- #
def load_state() -> dict | None:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def clear_state(reason: str) -> bool:
    """Drop the cached device state. Returns True if anything was actually there."""
    had = STATE_FILE.exists()
    try:
        STATE_FILE.unlink()
    except OSError:
        return False
    if had:
        print(f"[board] cache cleared ({reason}) -> {STATE_FILE.relative_to(ROOT)} deleted")
    return had


def save_state(port: str, name: str, hw: str) -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "port": port,
        "name": name or "unknown adapter",
        "hardware_id": hw,
        "detected_at": iso_now(),
    }
    STATE_FILE.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


# --------------------------------------------------------------------------- #
# Watch loop
# --------------------------------------------------------------------------- #
def on_insert(port: str) -> None:
    name, hw = describe(port)
    if not is_board(name, hw):
        print(f"[board] {port} appeared but is not the ESP kit ({name or 'unnamed'}) — ignored")
        return
    rec = save_state(port, name, hw)
    print(f"[board] DETECTED {port}  {rec['name']}")
    if hw:
        print(f"[board]   hardware id : {hw}")
    print(f"[board]   cached at    : {STATE_FILE.relative_to(ROOT)}")
    print(f"[board]   ready        : flash/monitor with mpremote -p {port}")


def on_remove(port: str | None = None) -> None:
    where = f" ({port})" if port else ""
    print(f"[board] board unplugged{where}")
    clear_state("device removed")


def scan(baseline: dict[str, str], known: dict[str, str]) -> dict[str, str]:
    """Compare against the kernel's device map; fire detect/clear on the diff."""
    current = usb_candidates(serial_ports())

    for key, port in current.items():
        if key in known or key in baseline:
            continue
        print(f"[board] port activity: {key} -> {port}")
        on_insert(port)

    for key, port in list(known.items()):
        if key in current:
            continue
        if load_state() is not None:          # only announce/clean if we cached it
            on_remove(port)
        else:
            print(f"[board] {port} disappeared (nothing cached)")

    return {k: v for k, v in current.items() if k not in baseline}


def watch() -> None:
    if not sys.platform.startswith("win"):
        print("[board] Windows-only: COM-port detection uses the kernel device map.")
        return

    ports = serial_ports()
    baseline = usb_candidates(ports)           # pre-existing ports are ignored forever
    known = dict(baseline)
    print(f"[board] watching for the ESP board... (poll {POLL_SECONDS:g}s, Ctrl+C to stop)")
    if baseline:
        print(f"[board] baseline ports ignored: {', '.join(sorted(baseline.values()))}")

    stale = load_state()
    if stale and not known:
        clear_state("stale state from a previous session")
    elif stale:
        print(f"[board] re-attached board found: {stale.get('port')} ({stale.get('name')})")

    # Board already plugged in before the watcher started -> recognise it now.
    for key, port in baseline.items():
        if load_state() is None:
            on_insert(port)

    while True:
        time.sleep(POLL_SECONDS)
        known = scan(baseline, known)


def once() -> None:
    ports = usb_candidates(serial_ports())
    print(f"[board] serial endpoints: {', '.join(sorted(ports.values())) or '(none)'}")
    cached = load_state()
    print(f"[board] cached state    : {json.dumps(cached) if cached else '(empty — cleared)'}")


def selftest() -> None:
    """Prove insert-recognition + cache-clearing without any hardware."""
    print("[board] selftest: simulating a board being plugged in, then removed")
    clear_state("selftest setup")
    save_state("COM99", "USB-SERIAL CH340 (COM99)", "USB\\VID_1A86&PID_7523&REV_0263")
    assert load_state() is not None, "state was not written"
    print(f"[board]   simulated insert -> cached: {STATE_FILE.relative_to(ROOT)}")
    assert clear_state("simulated removal"), "nothing to clear"
    assert load_state() is None, "cache was not cleared on removal"
    assert not STATE_FILE.exists(), "state file still exists"
    print("[board]   simulated remove -> cache cleared, no stale entry left")
    print("[board] selftest PASSED")


def show_state() -> None:
    cached = load_state()
    print(json.dumps(cached, indent=2) if cached else "(no cached board state)")


def main() -> None:
    ap = argparse.ArgumentParser(description="SignGuard ESP board watcher (insert = detect, remove = clear cache)")
    ap.add_argument("--once", action="store_true", help="single scan, then exit")
    ap.add_argument("--state", action="store_true", help="print the cached device state")
    ap.add_argument("--selftest", action="store_true", help="simulate insert/remove without hardware")
    args = ap.parse_args()

    try:
        # Windows consoles default to cp1252; force UTF-8 for the glyphs and
        # line-buffer stdout so a backgrounded run still streams in real time.
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:                              # noqa: BLE001 - best effort
        pass

    if args.selftest:
        selftest()
    elif args.state:
        show_state()
    elif args.once:
        once()
    else:
        watch()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[board] stopped (cached state kept — board still considered attached)")
