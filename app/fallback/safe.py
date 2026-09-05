"""Safe fallback content — CLAUDE.md §10.

On any block the display must show a VERIFIED trusted message — never blank,
never attacker content. This text is trusted by construction (it lives in our
source, not in any update channel).
"""
from __future__ import annotations

SAFE_FALLBACK_TEXT = (
    "Official Service Information\n"
    "Content update temporarily unavailable.\n"
    "Please contact official authorities for assistance."
)


def safe_fallback_content() -> str:
    """Return the trusted fallback message to render on a block."""
    return SAFE_FALLBACK_TEXT
