# SignGuard — UPDATES LOG

A running log of every change. Newest first. (No PDFs — this file is the record.)

---

## 2026-09-xx — Wired the secure layer into the main app + dashboard

- `app/deps.py`: swapped `registry = LocalRegistry(...)` → `registry = ChainRegistry()`.
  Because `ChainRegistry` implements the same `HashRegistry` interface, the whole
  pipeline (`/analyze`, dashboard, signage) now uses **signed + on-chain**
  authorizations with no other code changes. Every `/authorize` now Ed25519-signs the
  hash and appends a chain block to `data/chain/ledger.json`.
- `app/main.py`: added `GET /chain` (list blocks) and `GET /chain/verify`
  (recompute + prove integrity).
- `app/web/dashboard.py`: added an **⛓ on-chain** status chip in the nav that polls
  `/chain/verify` every 4 s and shows `N blocks ✓ signed` (or `✗ tampered`).
- Tests: full suite **46 passing** (41 existing + 5 secure/chain).

---

## 2026-09-xx — Digital signatures + on-chain registry (NEW secure layer)

**Goal:** add the two "NOT YET WIRED" items from `SYSTEM_DEEP_DIVE.md` — digital
signatures and an on-chain registry — **without touching the existing `app/main.py`**.
Delivered as new, separate modules and a separate entrypoint.

**New files (all additive):**
- `app/crypto/signing.py` — Ed25519 authority keypair (auto-generated + saved to
  `data/keys/authority_ed25519.key/.pub`); `sign_hex()`, `verify_hex()`, `public_hex()`.
- `app/chain/ledger.py` — real tamper-evident **hash-linked blockchain** persisted to
  `data/chain/ledger.json`. Each `Block` links to the previous via `prev_hash`;
  `block_hash = SHA-256(index, timestamp, content_id, content_hash, signature, pubkey,
  authorized_by, prev_hash)`. `verify_chain()` recomputes every hash + link and detects
  any edit/reorder.
- `app/chain/registry.py` — `ChainRegistry` (implements the existing
  `HashRegistry` interface). Every authorization is **SHA-256 hashed → Ed25519 signed →
  appended as a chain block**. `verify()` returns integrity + signature + chain validity.
- `app/secure_main.py` — **NEW separate FastAPI app** (does not replace `app/main.py`):
  `POST /authorize`, `POST /verify`, `GET /chain`, `GET /chain/verify`, `GET /health`.
- `tests/test_secure_chain.py` — 5 tests: genuine→render, tampered→block, unknown→block,
  signature valid + blocks chained, chain-tamper detected. **All passing.**

**What this proves now (real, in code):**
- Authenticity: an attacker who can write to the registry still can't forge an
  "authorized" record — the Ed25519 signature won't verify without the authority key.
- Tamper-evidence: editing any past authorization breaks the chain (`verify_chain`).

**How to run the secure layer (separate from the main app):**
```
python -m uvicorn app.secure_main:app --port 8010
# authorize:
curl -X POST localhost:8010/authorize -H "content-type: application/json" \
     -d "{\"content_id\":\"CNT-001\",\"content_bytes_b64\":\"aGVsbG8=\"}"
# verify genuine (render) / tampered (block):
curl -X POST localhost:8010/verify -H "content-type: application/json" \
     -d "{\"content_id\":\"CNT-001\",\"content_bytes_b64\":\"aGVsbG8=\"}"
curl localhost:8010/chain/verify
```

**Still not wired (honest):** QEMU/Kali/pendrive virtual USB lab; reading+hashing a real
inserted USB's content; a *distributed* multi-node blockchain (this ledger is a local,
single-writer chain); wiring the secure layer into the ESP8266 command path.

---

## 2026-08-xx — Baseline system (already built before this log)

- `app/` FastAPI "Layer 2" brain: `/authorize`, `/analyze`, `/audit`, dashboard `/`,
  signage `/signage`, WebSocket `/ws`.
- Track A: SHA-256 verification vs SQLite registry (`app/registry/local.py`).
- Track B: Isolation Forest (`app/ml_engine/model.py`) + SHAP (`app/xai/explain.py`),
  7 features (`app/features/engineer.py`), risk scoring (`app/scoring/score.py`),
  decision engine (`app/decision/engine.py`, thresholds 50 / 80).
- Append-only audit trail (`app/audit/`).
- In-process MQTT orchestrator (`app/orchestrator.py`) on topics
  `signguard/events|content|commands`.
- `usb_demo/` standalone ESP8266 (ESP-12E) hardware demo: `laptop/demo_trigger.py`
  (SHA-256 text + MQTT) → `esp8266/main.py` firmware (LCD + green/red LED + buzzer).
- Web console + full-screen passenger signage; `run_demo.py` one-command launch.
- Tests: `tests/test_track_a|track_b|api|audit|scoring|demo` (41 passing).
- See `SYSTEM_DEEP_DIVE.md` for the full code-grounded description.
