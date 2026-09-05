"""A minimal, real blockchain-style ledger, persisted to JSON.

Each Block = one authorization event. block_hash = SHA-256 over the block's
fields INCLUDING prev_hash, so the blocks form a chain. Any change to a past
block (or a reorder) changes its block_hash and breaks the next block's
prev_hash link — detectable by verify_chain().
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

GENESIS_PREV = "0" * 64


@dataclass
class Block:
    index: int
    timestamp: str
    content_id: str
    content_hash: str        # SHA-256 of the authorized content
    signature: str           # Ed25519 signature over content_hash (hex)
    pubkey: str              # authority Ed25519 public key (hex)
    authorized_by: str
    prev_hash: str
    block_hash: str = ""

    def compute_hash(self) -> str:
        payload = {
            "index": self.index,
            "timestamp": self.timestamp,
            "content_id": self.content_id,
            "content_hash": self.content_hash,
            "signature": self.signature,
            "pubkey": self.pubkey,
            "authorized_by": self.authorized_by,
            "prev_hash": self.prev_hash,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Ledger:
    """Append-only, hash-linked ledger persisted to a JSON file."""

    def __init__(self, path: str = "data/chain/ledger.json") -> None:
        self._path = pathlib.Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._blocks: list[Block] = []
        if self._path.exists():
            for raw in json.loads(self._path.read_text(encoding="utf-8")):
                self._blocks.append(Block(**raw))

    # -- writes ---------------------------------------------------------- #
    def append(
        self, content_id: str, content_hash: str, signature: str,
        pubkey: str, authorized_by: str = "transport_authority",
    ) -> Block:
        with self._lock:
            prev = self._blocks[-1].block_hash if self._blocks else GENESIS_PREV
            b = Block(
                index=len(self._blocks),
                timestamp=_utcnow(),
                content_id=content_id,
                content_hash=content_hash,
                signature=signature,
                pubkey=pubkey,
                authorized_by=authorized_by,
                prev_hash=prev,
            )
            b.block_hash = b.compute_hash()
            self._blocks.append(b)
            self._persist()
            return b

    def _persist(self) -> None:
        self._path.write_text(
            json.dumps([asdict(b) for b in self._blocks], indent=2), encoding="utf-8"
        )

    # -- reads ----------------------------------------------------------- #
    def blocks(self) -> list[Block]:
        return list(self._blocks)

    def latest_for(self, content_id: str) -> Block | None:
        for b in reversed(self._blocks):
            if b.content_id == content_id:
                return b
        return None

    def verify_chain(self) -> tuple[bool, str]:
        """Recompute every block hash + prev link. Returns (ok, message)."""
        prev = GENESIS_PREV
        for i, b in enumerate(self._blocks):
            if b.index != i:
                return False, f"block {i}: bad index {b.index}"
            if b.prev_hash != prev:
                return False, f"block {i}: prev_hash broken (chain tampered)"
            if b.compute_hash() != b.block_hash:
                return False, f"block {i}: block_hash mismatch (content tampered)"
            prev = b.block_hash
        return True, f"chain valid ({len(self._blocks)} block(s))"
