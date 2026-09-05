"""Demo scenarios + manual credential-attack helpers.

Drives the web dashboard and the terminal walkthrough. Events are re-timestamped
to "now" at build time so Track B's window always sees them. Each attack carries
the attacker's message (for the "WITHOUT SignGuard" scene) and a short hardware
label so the ESP32 LCD can show what kind of attack was blocked.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.schemas import ContentUpdate, EventType, SecurityEvent

# The genuine content the transport authority blessed.
BASELINE_CONTENT_ID = "CNT-101"
AUTHENTIC_TEXT = "TNSTC  •  Route 101\nRanipet → Vellore\nNext Bus: 10:30 AM"
AUTHENTIC = AUTHENTIC_TEXT.encode("utf-8")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


RawEvent = tuple[EventType, bool, dict]
E = EventType


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    device_id: str
    vector: str
    raw_events: list[RawEvent]
    tampered_content: bool
    attacker_message: str = ""
    has_content: bool = True
    expected: str = ""
    icon: str = ""
    hw_label: str = ""            # short label for the ESP32 LCD (16 chars max)

    def build(
        self, now: datetime | None = None
    ) -> tuple[list[SecurityEvent], ContentUpdate | None]:
        now = now or _utcnow()
        n = len(self.raw_events)
        events = [
            SecurityEvent(
                device_id=self.device_id,
                event_type=etype,
                authorized=authorized,
                timestamp=now - timedelta(seconds=(n - i)),
                data=data,
            )
            for i, (etype, authorized, data) in enumerate(self.raw_events)
        ]
        content = None
        if self.has_content:
            payload = self.attacker_message.encode("utf-8") if self.tampered_content else AUTHENTIC
            content = ContentUpdate(
                device_id=self.device_id,
                content_id=BASELINE_CONTENT_ID,
                content_bytes_b64=_b64(payload),
                source="usb",
                timestamp=now,
            )
        return events, content

    @property
    def attacker_text(self) -> str | None:
        if not self.has_content:
            return None
        return self.attacker_message if self.tampered_content else AUTHENTIC_TEXT


SCENARIOS: dict[str, Scenario] = {
    "baseline": Scenario(
        id="baseline",
        title="Baseline — authorized content",
        device_id="SG-RNP-001",
        vector="Transport authority pushes genuine, authorized content.",
        icon="✓",
        raw_events=[
            (E.login_success, True, {"user": "operator"}),
            (E.content_received, True, {"content_id": "CNT-101", "source": "network"}),
            (E.content_hash_match, True, {"content_id": "CNT-101"}),
        ],
        tampered_content=False,
        expected="RENDER — hash matches the authorized fingerprint.",
        hw_label="",
    ),
    "usb": Scenario(
        id="usb",
        title="Malicious USB / content replacement",
        device_id="SG-RNP-001",
        vector="Attacker plugs an unknown USB stick and swaps the content file.",
        icon="⚡",
        raw_events=[
            (E.unauthorized_usb, False, {"vendor": "unknown"}),
            (E.content_received, False, {"content_id": "CNT-101", "source": "usb"}),
            (E.content_hash_mismatch, False, {"content_id": "CNT-101"}),
        ],
        tampered_content=True,
        attacker_message="⚠ SYSTEM COMPROMISED\nUNAUTHORIZED MESSAGE",
        expected="BLOCK — SHA-256 mismatch (Track A). Safe fallback + incident.",
        hw_label="USB TAMPER",
    ),
    "wireless": Scenario(
        id="wireless",
        title="Unauthorized wireless update",
        device_id="SG-RNP-001",
        vector="Rogue access point pushes an unauthorized content update.",
        icon="📶",
        raw_events=[
            (E.wireless_activity, True, {"ssid": "transit-mgmt"}),
            (E.unauthorized_wireless, False, {"ssid": "rogue-ap", "rssi": -42}),
            (E.content_received, False, {"content_id": "CNT-101", "source": "wireless"}),
            (E.content_hash_mismatch, False, {"content_id": "CNT-101"}),
        ],
        tampered_content=True,
        attacker_message="⚠ ALL SERVICES\nCANCELLED",
        expected="BLOCK — authorization + integrity fail. Safe fallback + incident.",
        hw_label="ROGUE WIFI",
    ),
    # Credential attack is demonstrated MANUALLY via the operator panel (see the
    # manual_* helpers below), but the scripted scenario is kept for the terminal
    # walkthrough and tests.
    "credential": Scenario(
        id="credential",
        title="Compromised admin credentials",
        device_id="SG-RNP-001",
        vector="Attacker gets an admin session and uploads modified content.",
        icon="🔑",
        raw_events=[
            (E.login_failure, False, {"user": "admin"}),
            (E.login_failure, False, {"user": "admin"}),
            (E.default_credential_attempt, False, {"user": "admin", "password": "admin"}),
            (E.login_success, False, {"user": "admin"}),
            (E.content_received, False, {"content_id": "CNT-101", "source": "admin_panel"}),
            (E.content_hash_mismatch, False, {"content_id": "CNT-101"}),
        ],
        tampered_content=True,
        attacker_message="Route 101\nNEXT BUS CANCELLED",
        expected="BLOCK — a valid session can't authorize un-blessed content.",
        hw_label="ADMIN BREACH",
    ),
}

# Web dashboard buttons (credential is manual, so it's not a button).
ORDER = ["baseline", "usb", "wireless"]
# Terminal walkthrough covers everything.
TERMINAL_ORDER = ["baseline", "usb", "wireless", "credential"]


# --------------------------------------------------------------------------- #
# Manual credential attack — a real login + content-push the presenter drives
# --------------------------------------------------------------------------- #
MANUAL_DEVICE = "SG-RNP-001"
MANUAL_HW_LABEL = "ADMIN BREACH"

# The one legitimate operator credential.
VALID_CREDS = {("operator", "transit2026")}
# Weak/guessable passwords that mark a default-credential attempt.
_WEAK_PASSWORDS = {"admin", "password", "1234", "12345", "root", "toor", "admin123", "default"}


def classify_credentials(user: str, password: str) -> str:
    """Return 'valid' | 'default' | 'invalid' for a login attempt."""
    if (user, password) in VALID_CREDS:
        return "valid"
    if password.lower() in _WEAK_PASSWORDS:
        return "default"
    return "invalid"


def login_events(user: str, flag: str, now: datetime | None = None) -> list[SecurityEvent]:
    """Security events produced by a manual login attempt."""
    now = now or _utcnow()

    def mk(etype: EventType, auth: bool, data: dict, off: int) -> SecurityEvent:
        return SecurityEvent(
            device_id=MANUAL_DEVICE,
            event_type=etype,
            authorized=auth,
            timestamp=now - timedelta(seconds=off),
            data=data,
        )

    if flag == "valid":
        return [mk(E.login_success, True, {"user": user}, 1)]
    if flag == "default":
        return [
            mk(E.login_failure, False, {"user": user}, 5),
            mk(E.login_failure, False, {"user": user}, 4),
            mk(E.default_credential_attempt, False, {"user": user, "password": "***"}, 3),
            mk(E.login_success, False, {"user": user}, 1),
        ]
    # invalid — access denied, no session established
    return [
        mk(E.login_failure, False, {"user": user}, 3),
        mk(E.login_failure, False, {"user": user}, 2),
        mk(E.login_failure, False, {"user": user}, 1),
    ]


def manual_content(text: str, now: datetime | None = None) -> ContentUpdate:
    """A content update carrying whatever the operator typed."""
    return ContentUpdate(
        device_id=MANUAL_DEVICE,
        content_id=BASELINE_CONTENT_ID,
        content_bytes_b64=_b64(text.encode("utf-8")),
        source="admin_panel",
        timestamp=now or _utcnow(),
    )


def manual_scenario(text: str) -> Scenario:
    """A lightweight Scenario so the dashboard payload can show the typed content."""
    return Scenario(
        id="credential-manual",
        title="Compromised admin credentials",
        device_id=MANUAL_DEVICE,
        vector="Manual admin login + content upload.",
        raw_events=[],
        tampered_content=(text.strip() != AUTHENTIC_TEXT.strip()),
        attacker_message=text,
        has_content=True,
        icon="🔑",
        hw_label=MANUAL_HW_LABEL,
    )
