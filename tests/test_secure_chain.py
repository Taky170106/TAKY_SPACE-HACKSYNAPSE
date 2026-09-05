"""Tests for the signed + on-chain registry (new secure layer)."""
from __future__ import annotations

from app.chain.registry import ChainRegistry


def _reg(tmp_path):
    return ChainRegistry(
        ledger_path=str(tmp_path / "ledger.json"),
        key_dir=str(tmp_path / "keys"),
    )


def test_authorize_then_verify_genuine_renders(tmp_path):
    reg = _reg(tmp_path)
    reg.authorize_content("CNT-1", b"Route 101 - Next 10:30")
    r = reg.verify("CNT-1", b"Route 101 - Next 10:30")
    assert r["integrity_match"] and r["signature_valid"] and r["chain_valid"]
    assert r["action"] == "render"


def test_tampered_content_blocks(tmp_path):
    reg = _reg(tmp_path)
    reg.authorize_content("CNT-1", b"Route 101 - Next 10:30")
    r = reg.verify("CNT-1", b"ALL SERVICES CANCELLED")
    assert r["integrity_match"] is False
    assert r["action"] == "block" and r["reason"] == "hash_mismatch"


def test_unknown_content_blocks(tmp_path):
    reg = _reg(tmp_path)
    r = reg.verify("CNT-X", b"anything")
    assert r["action"] == "block" and r["reason"] == "unknown_content"


def test_signature_is_valid_and_chain_links(tmp_path):
    reg = _reg(tmp_path)
    reg.authorize_content("CNT-1", b"a")
    reg.authorize_content("CNT-2", b"b")
    blocks = reg.ledger.blocks()
    assert blocks[0].prev_hash == "0" * 64
    assert blocks[1].prev_hash == blocks[0].block_hash   # chained
    ok, _ = reg.ledger.verify_chain()
    assert ok


def test_chain_tamper_is_detected(tmp_path):
    reg = _reg(tmp_path)
    reg.authorize_content("CNT-1", b"a")
    reg.authorize_content("CNT-1", b"b")
    # Tamper with a past block's content in memory:
    reg.ledger.blocks()[0].content_hash = "deadbeef"
    reg.ledger._blocks[0].content_hash = "deadbeef"
    ok, msg = reg.ledger.verify_chain()
    assert ok is False
