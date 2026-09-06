"""SHAP explanation of the AI assessment (§11 xai).

IMPORTANT (CLAUDE.md §2): this explains ONLY the Isolation-Forest threat score —
the *context* around a content update — never the SHA-256 hash comparison. The
hash check is a deterministic gate; SHAP would be meaningless there.

Each factor's `impact` is signed so that POSITIVE = pushed the device TOWARD
anomaly (more suspicious), NEGATIVE = toward normal. Because Isolation-Forest's
decision_function is higher-for-normal, we flip the raw SHAP sign with
`_ANOMALY_SIGN` so the numbers read intuitively.
"""
from __future__ import annotations

import numpy as np
import shap

from app.features.engineer import FEATURE_ORDER, to_row
from app.ml_engine.model import AnomalyModel
from app.schemas import FeatureVector, XaiExplanation, XaiFactor

# IsolationForest.decision_function is LOWER for anomalies, so a feature that
# drives the score down (raw negative SHAP) is actually pushing toward "attack".
# Flip the sign so a positive impact means "more anomalous / more suspicious".
_ANOMALY_SIGN = -1.0


class ShapExplainer:
    def __init__(self, model: AnomalyModel) -> None:
        self._model = model
        self._explainer = shap.TreeExplainer(model.forest)

    def explain(self, fv: FeatureVector, top_k: int = 5) -> XaiExplanation:
        row = np.array([to_row(fv)], dtype=float)
        shap_values = self._explainer.shap_values(row)

        arr = np.asarray(shap_values)
        if arr.ndim == 2:
            arr = arr[0]
        else:
            arr = arr.ravel()
        arr = arr * _ANOMALY_SIGN

        factors = [
            XaiFactor(name=name, impact=round(float(val), 4))
            for name, val in zip(FEATURE_ORDER, arr)
        ]
        factors.sort(key=lambda f: abs(f.impact), reverse=True)

        return XaiExplanation(
            device_id=fv.device_id,
            explains="ai_threat_assessment",
            top_factors=factors[:top_k],
        )
