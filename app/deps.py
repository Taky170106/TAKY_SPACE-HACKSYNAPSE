"""Shared singletons for the Layer 2 app (registry, etc.).

Kept tiny and importable so both the API and tests use the same instances.
"""
from __future__ import annotations

import os

from app.audit import AuditStore
from app.chain import ChainRegistry
from app.ml_engine import AnomalyModel
from app.xai import ShapExplainer

# Signed + on-chain registry: every authorization is Ed25519-signed by the
# authority and appended to a tamper-evident hash-linked ledger
# (data/chain/ledger.json). Drop-in for the old LocalRegistry (same interface).
registry = ChainRegistry()

# Append-only audit trail. Set SIGNGUARD_AUDIT_DB to persist to a file; defaults
# to its own in-memory DB so it never shares a connection with the registry.
_AUDIT_DB_PATH = os.environ.get("SIGNGUARD_AUDIT_DB", ":memory:")
audit_store = AuditStore(_AUDIT_DB_PATH)

# Track B singletons — the IsolationForest is trained once at import (fast), and
# the SHAP explainer wraps that same fitted forest.
anomaly_model = AnomalyModel()
shap_explainer = ShapExplainer(anomaly_model)
