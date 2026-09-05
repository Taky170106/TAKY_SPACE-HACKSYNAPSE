"""Scoring — risk fusion (hash + AI anomaly + rule signals). (§11)"""
from app.scoring.score import WEIGHTS, compute_risk

__all__ = ["WEIGHTS", "compute_risk"]
