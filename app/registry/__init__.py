"""HashRegistry — the authorized-content store (CLAUDE.md §8)."""
from app.registry.base import HashRegistry
from app.registry.local import LocalRegistry

__all__ = ["HashRegistry", "LocalRegistry"]
