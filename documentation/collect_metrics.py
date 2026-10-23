"""Collect every number the report needs, from the real system.

Writes documentation/metrics.json (consumed by make_diagrams.py + make_report.py).
Run with the demo up:  python run_demo.py   then   python documentation/collect_metrics.py
"""
from __future__ import annotations

import base64
import http.client
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).with_name("metrics.json")

from app.authorization import authorize_content          # noqa: E402
from app.demo_scenarios import (                         # noqa: E402
    AUTHENTIC,
    BASELINE_CONTENT_ID,
    SCENARIOS,
    TERMINAL_ORDER,
)
from app.deps import anomaly_model, audit_store, registry, shap_explainer  # noqa: E402
from app.pipeline import run_analysis                    # noqa: E402
from app.schemas import AnalyzeRequest                   # noqa: E402


def ms(samples: list[float]) -> dict:
    s = sorted(samples)
    return {
        "mean": round(statistics.mean(samples), 3),
        "median": round(statistics.median(samples), 3),
        "p95": round(s[max(0, int(0.95 * len(s)) - 1)], 3),
        "min": round(min(samples), 3),
        "max": round(max(samples), 3),
        "n": len(samples),
    }


def bench_pipeline() -> dict:
    """Server-side cost of one decision (no HTTP, no socket)."""
    results = {}
    for sid in TERMINAL_ORDER:
        sc = SCENARIOS[sid]
        events, content = sc.build()
        req = AnalyzeRequest(device_id=sc.device_id, events=events, content_update=content)
        run_analysis(req)  # warm-up
        t = []
        for _ in range(40):
            s = time.perf_counter()
            run_analysis(req)
            t.append((time.perf_counter() - s) * 1000)
        results[sid] = ms(t)
    return results


def bench_http() -> dict:
    """Client-observed latency to the REST API (keep-alive, IPv4 literal)."""
    body = json.dumps({
        "device_id": "SG-RNP-001",
        "content_update": {
            "device_id": "SG-RNP-001",
            "content_id": "CNT-001",
            "content_bytes_b64": base64.b64encode(b"EVIL").decode(),
            "source": "usb",
        },
    }).encode()

    def run(host: str, path: str, payload: bytes | None, n: int) -> list[float]:
        out = []
        for _ in range(n):          # fresh connection each time = worst case
            c = http.client.HTTPConnection(host, 8000, timeout=30)
            t = time.perf_counter()
            c.request("POST" if payload else "GET", path,
                      body=payload, headers={"content-type": "application/json"} if payload else {})
            c.getresponse().read()
            out.append((time.perf_counter() - t) * 1000)
            c.close()
        return out

    keep = http.client.HTTPConnection("127.0.0.1", 8000, timeout=30)
    ka = []
    for _ in range(50):
        t = time.perf_counter()
        keep.request("POST", "/analyze", body=body, headers={"content-type": "application/json"})
        keep.getresponse().read()
        ka.append((time.perf_counter() - t) * 1000)
    keep.close()

    return {
        "analyze_keepalive_ipv4": ms(ka),
        "analyze_fresh_ipv4": ms(run("127.0.0.1", "/analyze", body, 15)),
        "analyze_fresh_localhost": ms(run("localhost", "/analyze", body, 15)),
        "health_fresh_localhost": ms(run("localhost", "/health", None, 10)),
    }


def scenario_outcomes() -> list[dict]:
    """What each attack did end-to-end: decision, risk, SHAP drivers."""
    rows = []
    for sid in TERMINAL_ORDER:
        sc = SCENARIOS[sid]
        events, content = sc.build()
        req = AnalyzeRequest(device_id=sc.device_id, events=events, content_update=content)
        res = run_analysis(req)
        top = res.xai_explanation.top_factors if res.xai_explanation else []
        rows.append({
            "id": sid,
            "title": sc.title,
            "decision": res.decision.decision,
            "command": res.decision.recommended_action,
            "risk": res.risk_score.score,
            "level": res.risk_score.level,
            "reasons": res.decision.reasons,
            "verified_match": res.verification_result.match if res.verification_result else None,
            "hash_action": res.verification_result.action if res.verification_result else None,
            "shap": [{"name": f.name, "impact": round(f.impact, 3)} for f in top],
            "events": sorted({e.event_type.value for e in events}),
        })
    return rows


def main() -> None:
    # Authorize exactly the bytes the baseline scenario will deliver, so a
    # genuine update really is a hash match (otherwise we would measure a
    # false positive instead of the true positive).
    authorize_content(registry, BASELINE_CONTENT_ID, AUTHENTIC)

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pipeline_latency_ms": bench_pipeline(),
        "http_latency_ms": bench_http(),
        "scenarios": scenario_outcomes(),
        "audit_rows": audit_store.count(),
    }
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print(json.dumps(data["http_latency_ms"], indent=2))
    for r in data["scenarios"]:
        print(f"  {r['id']:10} {r['decision']:7} risk={r['risk']:3} {r['level']:7} "
              f"match={r['verified_match']} shap0={r['shap'][0]['name'] if r['shap'] else '-'}")


if __name__ == "__main__":
    main()
