"""The star of the demo: deterministic content-integrity verification.

Compute SHA-256 of the received content, compare to the authorized hash from the
registry. MATCH -> render, MISMATCH (or unknown content) -> block. This NEVER
waits for the ML model (CLAUDE.md §2).
"""
from __future__ import annotations

import base64

from app.authorization import sha256_hex
from app.registry.base import HashRegistry
from app.schemas import ContentUpdate, VerificationResult


def verify_content(
    registry: HashRegistry, update: ContentUpdate
) -> VerificationResult:
    """Verify a received content_update against the authorized hash."""
    content_bytes = base64.b64decode(update.content_bytes_b64)
    computed = sha256_hex(content_bytes)
    authorized = registry.get_authorized_hash(update.content_id)

    # Unknown content_id is treated as a mismatch: never render unauthorized bytes.
    match = authorized is not None and computed == authorized

    return VerificationResult(
        content_id=update.content_id,
        computed_hash=computed,
        authorized_hash=authorized,
        match=match,
        action="render" if match else "block",
    )
