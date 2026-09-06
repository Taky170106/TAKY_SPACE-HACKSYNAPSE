"""
SignGuard AI - live hardware attack demo (real ESP-12E LCD).

Shows the core story on the PHYSICAL sign, step by step:
  1. Authorised content        -> LCD shows the real bus info (green LED)
  2. ATTACK, SignGuard OFF      -> LCD is HIJACKED to the attacker's message
  3. SAME ATTACK, SignGuard ON  -> hash mismatch -> BLOCKED: LCD "TAMPER
                                   DETECTED" + buzzer, original content preserved

No Raspberry Pi needed - this drives the exact same backend pipeline the Pi
would (SHA-256 verify -> AI risk -> decision -> MQTT -> ESP). Just run:

    python run_demo.py          # in one terminal (backend + broker)
    python attack_demo.py       # in another

Press Enter to advance through each step so you can narrate it.
"""
import sys
import time
import requests

API = "http://localhost:8000"
DEVICE = "SG-RNP-001"

# The genuine content the transport authority blessed (the "before").
AUTHORIZED = "TNSTC Route 101|Next bus 10:30"
# What the attacker tries to put on the sign instead (the "hijack").
ATTACKER = "PLATFORM CHANGED|Board Track 9 NOW"


def post(path, **body):
    r = requests.post(API + path, json=body, timeout=10)
    r.raise_for_status()
    return r.json()


def wait(msg="   >> Press Enter to continue..."):
    try:
        input(msg)
    except EOFError:
        time.sleep(2)


def line(c="-"):
    print(c * 60)


def main():
    print()
    line("=")
    print("  SignGuard AI  -  LIVE ATTACK DEMO on the real ESP-12E LCD")
    line("=")

    # sanity: backend up?
    try:
        requests.get(API + "/health", timeout=5)
    except Exception:
        print("\n[!] Backend not reachable at", API)
        print("    Start it first:  python run_demo.py")
        sys.exit(1)

    # --- 0. establish the authorised baseline -------------------------
    print("\n[0] Authorising the genuine content with the authority...")
    post("/demo/authorize-content", content=AUTHORIZED)
    print("    Authorised:", AUTHORIZED.replace("|", " / "))
    wait()

    # --- 1. genuine content, SignGuard ON -----------------------------
    line()
    print("[1] Genuine update (SignGuard ON) -> should DISPLAY on the sign.")
    r = post("/ingest/usb", device_id=DEVICE, content=AUTHORIZED,
             source="usb", serial="GENUINE-001", protected=True)
    print("    decision:", r.get("decision"), "| verified:", r.get("verified"),
          "| LCD notified:", r.get("hardware_notified"))
    print("    >>> LOOK AT THE LCD:  shows the real bus info, GREEN LED.")
    wait()

    # --- 2. ATTACK with SignGuard OFF ---------------------------------
    line()
    print("[2] ATTACK - SignGuard OFF.  Attacker swaps the file on the USB.")
    print("    Fake content:", ATTACKER.replace("|", " / "))
    r = post("/ingest/usb", device_id=DEVICE, content=ATTACKER,
             source="usb", serial="EVIL-666", protected=False)
    print("    decision:", r.get("decision"), "(no verification done)")
    print("    >>> LOOK AT THE LCD:  it is HIJACKED - the fake message is now")
    print("        on the public sign. THE ATTACK SUCCEEDED. (no protection)")
    wait()

    # --- 3. SAME ATTACK with SignGuard ON -----------------------------
    line()
    print("[3] SAME ATTACK - SignGuard ON.  Same fake file, now protected.")
    r = post("/ingest/usb", device_id=DEVICE, content=ATTACKER,
             source="usb", serial="EVIL-666", protected=True)
    print("    decision:", r.get("decision"), "| verified:", r.get("verified"),
          "| action:", r.get("recommended_action"), "| risk:", r.get("risk"))
    print("    >>> LOOK AT THE LCD:  'TAMPER DETECTED' + BUZZER, RED LED.")
    print("        The attacker's message is BLOCKED; original content is safe.")
    wait()

    # --- 4. restore -------------------------------------------------
    line()
    print("[4] Restoring the genuine content on the sign...")
    post("/ingest/usb", device_id=DEVICE, content=AUTHORIZED,
         source="usb", serial="GENUINE-001", protected=True)
    print("    >>> LCD back to the real bus info, GREEN LED.")
    line("=")
    print("  Done. Same attack: WITHOUT SignGuard it wins, WITH SignGuard it's blocked.")
    line("=")


if __name__ == "__main__":
    main()
