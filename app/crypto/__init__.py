"""Digital-signature layer (Ed25519) for authorized content — NEW, separate.

Adds authenticity (WHO signed) on top of SHA-256 integrity (WHAT the content is).
Does not modify the original app/ modules.
"""
from app.crypto.signing import (
    AuthorityKeys,
    ensure_keys,
    public_hex,
    sign_hex,
    verify_hex,
)

__all__ = ["AuthorityKeys", "ensure_keys", "public_hex", "sign_hex", "verify_hex"]
