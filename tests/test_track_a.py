"""Track A tests — the deterministic star of the demo (CLAUDE.md §2, §9)."""
from __future__ import annotations

import base64

from app.authorization import authorize_content, sha256_hex
from app.decision import decide
from app.registry import LocalRegistry
from app.schemas import ContentUpdate
from app.verification import verify_content

AUTHENTIC = b"Platform 2: Train to Central departs 10:45."
TAMPERED = b"Platform 2: FREE WIFI click http://evil.example to claim."


def _update(content: bytes, content_id: str = "CNT-001") -> ContentUpdate:
    return ContentUpdate(
        device_id="SG-RNP-001",
        content_id=content_id,
        content_bytes_b64=base64.b64encode(content).decode("ascii"),
        source="usb",
    )


def test_sha256_is_deterministic():
    assert sha256_hex(AUTHENTIC) == sha256_hex(AUTHENTIC)
    assert sha256_hex(AUTHENTIC) != sha256_hex(TAMPERED)


def test_authorize_stores_hash():
    reg = LocalRegistry()
    record = authorize_content(reg, "CNT-001", AUTHENTIC)
    assert reg.get_authorized_hash("CNT-001") == record.content_hash
    assert record.content_hash == sha256_hex(AUTHENTIC)


def test_match_allows_render():
    reg = LocalRegistry()
    authorize_content(reg, "CNT-001", AUTHENTIC)
    result = verify_content(reg, _update(AUTHENTIC))
    assert result.match is True
    assert result.action == "render"

    decision = decide("SG-RNP-001", result)
    assert decision.decision == "render"
    assert decision.recommended_action.value == "render"


def test_mismatch_blocks_with_fallback():
    reg = LocalRegistry()
    authorize_content(reg, "CNT-001", AUTHENTIC)
    result = verify_content(reg, _update(TAMPERED))
    assert result.match is False
    assert result.action == "block"

    decision = decide("SG-RNP-001", result)
    assert decision.decision == "block"
    assert decision.recommended_action.value == "safe_fallback"
    assert "hash_mismatch" in decision.reasons


def test_unknown_content_is_blocked():
    reg = LocalRegistry()  # nothing authorized
    result = verify_content(reg, _update(AUTHENTIC, content_id="CNT-999"))
    assert result.authorized_hash is None
    assert result.match is False
    assert result.action == "block"

    decision = decide("SG-RNP-001", result)
    assert decision.decision == "block"
    assert "unknown_content" in decision.reasons


def test_reauthorization_updates_hash():
    reg = LocalRegistry()
    authorize_content(reg, "CNT-001", AUTHENTIC)
    authorize_content(reg, "CNT-001", TAMPERED)  # authority re-blesses new bytes
    assert reg.get_authorized_hash("CNT-001") == sha256_hex(TAMPERED)
