"""ChainRegistry — a HashRegistry backed by the on-chain ledger + Ed25519 signing.

Drop-in compatible with app.registry.base.HashRegistry (authorize / get_authorized_hash),
but every authorization is (a) digitally signed by the authority and (b) written as a
new block in the tamper-evident chain. Verification checks integrity, signature, and
chain validity together.
"""
from __future__ import annotations

import hashlib

from app.chain.ledger import Ledger
from app.crypto.signing import ensure_keys, public_hex, sign_hex, verify_hex
from app.registry.base import HashRegistry
from app.schemas import ContentRecord


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ChainRegistry(HashRegistry):
    def __init__(
        self, ledger_path: str = "data/chain/ledger.json", key_dir: str = "data/keys"
    ) -> None:
        self.keys = ensure_keys(key_dir)
        self.pubkey = public_hex(self.keys.public)
        self.ledger = Ledger(ledger_path)

    # -- HashRegistry interface ----------------------------------------- #
    def authorize(self, record: ContentRecord) -> None:
        signature = sign_hex(self.keys.private, record.content_hash)
        self.ledger.append(
            content_id=record.content_id,
            content_hash=record.content_hash,
            signature=signature,
            pubkey=self.pubkey,
            authorized_by=record.authorized_by,
        )

    def get_authorized_hash(self, content_id: str) -> str | None:
        block = self.ledger.latest_for(content_id)
        return block.content_hash if block else None

    # -- convenience + verification ------------------------------------- #
    def authorize_content(
        self, content_id: str, content_bytes: bytes,
        authorized_by: str = "transport_authority",
    ) -> dict:
        h = sha256_hex(content_bytes)
        signature = sign_hex(self.keys.private, h)
        block = self.ledger.append(content_id, h, signature, self.pubkey, authorized_by)
        return {
            "content_id": content_id, "content_hash": h, "signature": signature,
            "pubkey": self.pubkey, "block_index": block.index,
            "block_hash": block.block_hash, "prev_hash": block.prev_hash,
        }

    def verify(self, content_id: str, content_bytes: bytes) -> dict:
        computed = sha256_hex(content_bytes)
        block = self.ledger.latest_for(content_id)
        chain_ok, chain_msg = self.ledger.verify_chain()

        if block is None:
            return {
                "content_id": content_id, "computed_hash": computed,
                "integrity_match": False, "signature_valid": False,
                "chain_valid": chain_ok, "chain_message": chain_msg,
                "action": "block", "reason": "unknown_content",
            }

        integrity = computed == block.content_hash
        sig_ok = verify_hex(block.pubkey, block.content_hash, block.signature)
        # ALLOW only if content matches, the authority signature is valid, AND the
        # chain itself hasn't been tampered with.
        action = "render" if (integrity and sig_ok and chain_ok) else "block"
        reason = "ok" if action == "render" else (
            "hash_mismatch" if not integrity else
            "bad_signature" if not sig_ok else "chain_tampered"
        )
        return {
            "content_id": content_id, "computed_hash": computed,
            "authorized_hash": block.content_hash, "signature": block.signature,
            "pubkey": block.pubkey, "block_index": block.index,
            "integrity_match": integrity, "signature_valid": sig_ok,
            "chain_valid": chain_ok, "chain_message": chain_msg,
            "action": action, "reason": reason,
        }
