"""Ganache-backed on-chain registry for SignGuard (Round-3 upgrade).

Compiles + deploys SignageRegistry.sol to a local EVM (Ganache at
http://127.0.0.1:8545) and exposes the SAME interface as the existing
ChainRegistry, so it is a drop-in replacement — the analysis pipeline does not
change. This is SEPARATE from the production local ledger; enable it explicitly.

    reg = GanacheRegistry()                 # connect + deploy (or attach)
    reg.authorize_content("route-101", b"TNSTC Route 101|Next 10:30")
    reg.get_authorized_hash("route-101")    # -> sha256 hex
    reg.verify("route-101", b"...bytes...") # -> {"match": bool, ...}
"""
from __future__ import annotations

import hashlib
import json
import pathlib

import os

from solcx import compile_standard, install_solc
from web3 import Web3

# Works with the Ganache CLI (default 8545) OR the Ganache GUI app (usually 7545).
# Override with:  set GANACHE_RPC=http://127.0.0.1:7545
RPC = os.environ.get("GANACHE_RPC", "http://127.0.0.1:8545")
SOL = pathlib.Path(__file__).with_name("SignageRegistry.sol")
DEPLOY_INFO = pathlib.Path(__file__).with_name("deployed.json")
SOLC_VERSION = "0.8.19"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compile() -> tuple[list, str]:
    install_solc(SOLC_VERSION)
    src = SOL.read_text(encoding="utf-8")
    out = compile_standard(
        {
            "language": "Solidity",
            "sources": {"SignageRegistry.sol": {"content": src}},
            "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}},
        },
        solc_version=SOLC_VERSION,
    )
    c = out["contracts"]["SignageRegistry.sol"]["SignageRegistry"]
    return c["abi"], c["evm"]["bytecode"]["object"]


class GanacheRegistry:
    def __init__(self, rpc: str = RPC, redeploy: bool = True) -> None:
        self.w3 = Web3(Web3.HTTPProvider(rpc))
        if not self.w3.is_connected():
            raise RuntimeError(f"Ganache not reachable at {rpc}. Start it: ganache -p 8545")
        self.authority = self.w3.eth.accounts[0]      # deployer = transport authority
        self.abi, bytecode = _compile()
        if redeploy or not DEPLOY_INFO.exists():
            self.address = self._deploy(bytecode)
        else:
            self.address = json.loads(DEPLOY_INFO.read_text())["address"]
        self.contract = self.w3.eth.contract(address=self.address, abi=self.abi)

    # -- deploy -------------------------------------------------------------
    def _deploy(self, bytecode: str) -> str:
        C = self.w3.eth.contract(abi=self.abi, bytecode=bytecode)
        tx = C.constructor().transact({"from": self.authority})
        rcpt = self.w3.eth.wait_for_transaction_receipt(tx)
        DEPLOY_INFO.write_text(json.dumps({
            "address": rcpt.contractAddress, "authority": self.authority,
            "deploy_tx": rcpt.transactionHash.hex(), "block": rcpt.blockNumber,
        }, indent=2))
        return rcpt.contractAddress

    # -- key helpers --------------------------------------------------------
    def _cid(self, content_id: str) -> bytes:
        return self.w3.keccak(text=content_id)                 # bytes32 key

    def _h32(self, content_bytes: bytes) -> bytes:
        return bytes.fromhex(sha256_hex(content_bytes))        # 32-byte sha256

    # -- same interface as ChainRegistry -----------------------------------
    def authorize_content(self, content_id: str, content_bytes: bytes,
                          authorized_by: str = "transport_authority") -> dict:
        tx = self.contract.functions.authorizeContent(
            self._cid(content_id), self._h32(content_bytes)
        ).transact({"from": self.authority})
        rcpt = self.w3.eth.wait_for_transaction_receipt(tx)
        return {"tx": rcpt.transactionHash.hex(), "block": rcpt.blockNumber,
                "content_hash": sha256_hex(content_bytes)}

    def get_authorized_hash(self, content_id: str) -> str | None:
        h = self.contract.functions.authorizedHash(self._cid(content_id)).call()
        h = h.hex()
        return None if int(h, 16) == 0 else h

    def verify(self, content_id: str, content_bytes: bytes) -> dict:
        computed = sha256_hex(content_bytes)
        on_chain = self.contract.functions.verify(
            self._cid(content_id), self._h32(content_bytes)
        ).call()
        return {"content_id": content_id, "computed_hash": computed,
                "authorized_hash": self.get_authorized_hash(content_id),
                "match": bool(on_chain), "action": "render" if on_chain else "block"}

    def log_decision(self, device_id: str, decision: str, risk: int) -> str:
        tx = self.contract.functions.logDecision(device_id, decision, int(risk)).transact(
            {"from": self.authority})
        return self.w3.eth.wait_for_transaction_receipt(tx).transactionHash.hex()
