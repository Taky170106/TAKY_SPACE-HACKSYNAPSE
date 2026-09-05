"""Authorization: the transport authority blesses a piece of content.

Hash the authorized bytes with SHA-256, build a ContentRecord, and store it in
the HashRegistry. This is the ground truth that verification compares against.
"""
from __future__ import annotations

import hashlib

from app.registry.base import HashRegistry
from app.schemas import ContentRecord


def sha256_hex(content_bytes: bytes) -> str:
    """Deterministic SHA-256 hex digest — the one primitive of Track A (§2)."""
    return hashlib.sha256(content_bytes).hexdigest()


def authorize_content(
    registry: HashRegistry,
    content_id: str,
    content_bytes: bytes,
    authorized_by: str = "transport_authority",
) -> ContentRecord:
    """Hash `content_bytes`, store the record, and return it."""
    record = ContentRecord(
        content_id=content_id,
        content_hash=sha256_hex(content_bytes),
        authorized_by=authorized_by,
    )
    registry.authorize(record)
    return record
