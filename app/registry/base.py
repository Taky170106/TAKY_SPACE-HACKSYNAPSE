"""HashRegistry interface — CLAUDE.md §8.

Keep this interface clean so a real chain *could* be swapped in later, but the
only implementation for this build is LocalRegistry. Do NOT integrate a real
chain now.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import ContentRecord


class HashRegistry(ABC):
    """Stores the transport-authority-authorized hash for each content_id."""

    @abstractmethod
    def authorize(self, record: ContentRecord) -> None:
        """Record `content_id -> content_hash` as authorized."""

    @abstractmethod
    def get_authorized_hash(self, content_id: str) -> str | None:
        """Return the authorized hash for `content_id`, or None if unknown."""
