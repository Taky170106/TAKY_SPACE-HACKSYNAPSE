"""On-chain authorization registry (local hash-linked blockchain) — NEW, separate.

A tamper-evident append-only chain: each block links to the previous via prev_hash,
and each block stores the content hash + the authority's Ed25519 signature. Editing
any past block breaks the chain, which `verify_chain()` detects.
"""
from app.chain.ledger import Block, Ledger
from app.chain.registry import ChainRegistry

__all__ = ["Block", "Ledger", "ChainRegistry"]
