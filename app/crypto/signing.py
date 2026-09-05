"""Ed25519 digital signatures for the transport authority.

The authority holds a private key; it signs the SHA-256 fingerprint of approved
content. Anyone with the public key can verify that a hash was really approved by
the authority — so an attacker can't forge an "authorized" record even if they can
write to the registry.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


@dataclass
class AuthorityKeys:
    private: Ed25519PrivateKey
    public: Ed25519PublicKey


def ensure_keys(key_dir: str = "data/keys") -> AuthorityKeys:
    """Load the authority keypair, generating + saving it once if absent."""
    d = pathlib.Path(key_dir)
    d.mkdir(parents=True, exist_ok=True)
    priv_path = d / "authority_ed25519.key"
    pub_path = d / "authority_ed25519.pub"

    if priv_path.exists():
        private = serialization.load_pem_private_key(priv_path.read_bytes(), password=None)
    else:
        private = Ed25519PrivateKey.generate()
        priv_path.write_bytes(
            private.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        public = private.public_key()
        pub_path.write_bytes(
            public.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return AuthorityKeys(private=private, public=private.public_key())


def public_hex(public: Ed25519PublicKey) -> str:
    """Raw 32-byte Ed25519 public key as hex (compact, storable in the ledger)."""
    raw = public.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return raw.hex()


def _public_from_hex(pub_hex: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))


def sign_hex(private: Ed25519PrivateKey, message: str) -> str:
    """Sign a message (e.g. a content hash) -> hex signature."""
    return private.sign(message.encode("utf-8")).hex()


def verify_hex(pub_hex: str, message: str, signature_hex: str) -> bool:
    """Verify a hex signature over `message` with the hex public key."""
    try:
        _public_from_hex(pub_hex).verify(
            bytes.fromhex(signature_hex), message.encode("utf-8")
        )
        return True
    except Exception:
        return False
