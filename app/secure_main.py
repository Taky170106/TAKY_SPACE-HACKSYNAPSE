"""SignGuard SECURE — FastAPI app with digital signatures + on-chain registry.

This is a NEW, SEPARATE entrypoint. It does not modify app/main.py. It layers
Ed25519 authority signatures and a tamper-evident hash-linked ledger on top of the
existing SHA-256 integrity idea.

Run:  python -m uvicorn app.secure_main:app --port 8010
Endpoints:
  GET  /health
  POST /authorize        {content_id, content_bytes_b64, authorized_by?}
  POST /verify           {content_id, content_bytes_b64}
  GET  /chain            -> all blocks
  GET  /chain/verify     -> {valid, message}
"""
from __future__ import annotations

import base64

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.chain.registry import ChainRegistry

app = FastAPI(title="SignGuard SECURE — signed + on-chain", version="1.0.0")
registry = ChainRegistry()  # data/chain/ledger.json + data/keys/authority_ed25519.*


class AuthorizeRequest(BaseModel):
    content_id: str
    content_bytes_b64: str
    authorized_by: str = "transport_authority"


class VerifyRequest(BaseModel):
    content_id: str
    content_bytes_b64: str


def _decode(b64: str) -> bytes:
    try:
        return base64.b64decode(b64, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"invalid base64: {exc}")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "signguard-secure", "authority_pubkey": registry.pubkey}


@app.post("/authorize")
def authorize(req: AuthorizeRequest) -> dict:
    """Sign the content hash with the authority key and append it to the chain."""
    return registry.authorize_content(req.content_id, _decode(req.content_bytes_b64), req.authorized_by)


@app.post("/verify")
def verify(req: VerifyRequest) -> dict:
    """Check integrity (hash) + authenticity (signature) + chain validity."""
    return registry.verify(req.content_id, _decode(req.content_bytes_b64))


@app.get("/chain")
def chain() -> list[dict]:
    from dataclasses import asdict
    return [asdict(b) for b in registry.ledger.blocks()]


@app.get("/chain/verify")
def chain_verify() -> dict:
    ok, msg = registry.ledger.verify_chain()
    return {"valid": ok, "message": msg}
