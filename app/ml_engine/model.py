"""Anomaly model — IsolationForest over the §6 feature vector (§11 ml_engine).

CRITICAL (CLAUDE.md §2): this assesses *attack context* only. It NEVER decides
content integrity and is never on the path that blocks a hash mismatch. It just
answers "how unusual does this device's recent behaviour look?".

The model is trained at construction on a synthetic "normal" baseline (a quiet,
healthy signage node). Anomalous inputs — failed-login bursts, unknown USB,
hash mismatches, rogue wireless — fall outside that baseline and score high.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

from app.features.engineer import FEATURE_ORDER, to_row
from app.schemas import AnomalyResult, FeatureVector

_RNG = np.random.default_rng(42)  # deterministic baseline + model


def _normal_baseline(n: int = 1000) -> np.ndarray:
    """Sample n mostly-healthy node rows, in FEATURE_ORDER.

    Key detail: the incident features (usb / wireless / mismatch) and trust must
    have NON-ZERO variance, otherwise IsolationForest never learns to split on
    them and an attacker who flips them to 1 stays 'invisible' to the model. So a
    small fraction of benign windows carry a single minor incident, with trust
    correlated to it exactly as features.engineer computes trust. The dominant
    mode is still the perfectly healthy vector (all zeros, trust 1.0).
    """
    failed_logins = _RNG.poisson(0.3, n).astype(float)          # occasional typo
    unknown_usb = (_RNG.random(n) < 0.02).astype(float)         # rare benign USB
    wireless_anomaly = (_RNG.random(n) < 0.02).astype(float)    # rare stray AP
    hash_mismatch = (_RNG.random(n) < 0.01).astype(float)       # rare transient
    events_per_minute = np.clip(_RNG.normal(0.8, 0.4, n), 0, None)
    # Healthy nodes may have JUST been updated (≈0s) or be a couple of hours
    # stale — both normal. Uniform over 0..2h so small values aren't anomalies.
    time_since_update = np.clip(_RNG.uniform(0, 7200, n), 0, 86_400)
    # Trust mirrors features.engineer penalties, so it's correlated with incidents.
    device_trust = np.clip(
        1.0
        - 0.05 * failed_logins
        - 0.20 * unknown_usb
        - 0.15 * wireless_anomaly
        - 0.30 * hash_mismatch,
        0.0,
        1.0,
    )

    return np.column_stack(
        [
            failed_logins,
            unknown_usb,
            wireless_anomaly,
            hash_mismatch,
            events_per_minute,
            time_since_update,
            device_trust,
        ]
    ).astype(float)


class AnomalyModel:
    model_name = "isolation_forest"

    def __init__(self) -> None:
        assert len(FEATURE_ORDER) == 7  # guards against schema drift
        baseline = _normal_baseline()
        self._forest = IsolationForest(
            n_estimators=200,
            contamination=0.03,   # baseline is mostly inliers, a few minor incidents
            random_state=42,
        ).fit(baseline)

        # decision_function is centred on the inlier/outlier boundary at 0
        # (predict == -1 iff decision < 0). Use the spread of the normal cloud to
        # scale the score so a typical healthy point sits well below 0.5.
        d = self._forest.decision_function(baseline)
        self._sigma = float(d.std()) or 1e-6

    def score(self, fv: FeatureVector) -> AnomalyResult:
        row = np.array([to_row(fv)], dtype=float)
        decision = float(self._forest.decision_function(row)[0])
        is_anomaly = bool(self._forest.predict(row)[0] == -1)

        # Anchor at the model's own boundary: decision > 0 (inlier) -> score < 0.5,
        # decision < 0 (outlier) -> score > 0.5. Scale by the normal spread.
        anomaly_score = round(float(1.0 / (1.0 + np.exp(decision / self._sigma))), 4)

        return AnomalyResult(
            device_id=fv.device_id,
            anomaly_score=anomaly_score,
            is_anomaly=is_anomaly,
            model=self.model_name,
        )

    @property
    def forest(self) -> IsolationForest:
        return self._forest
