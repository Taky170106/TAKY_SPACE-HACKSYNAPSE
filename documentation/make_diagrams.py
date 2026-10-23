"""Generate every figure the ISWE415L report needs.

    python documentation/make_diagrams.py

Outputs PNG files into documentation/figures/ (200 dpi, embedded by make_report.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = Path(__file__).parent
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
METRICS = json.loads((HERE / "metrics.json").read_text(encoding="utf-8"))

INK = "#1f2937"
BLUE = "#2563eb"
GREEN = "#16a34a"
RED = "#dc2626"
AMBER = "#d97706"
GREY = "#6b7280"
LIGHT = "#f3f4f6"


def box(ax, x, y, w, h, text, fc="white", ec=INK, fs=9, weight="normal", tc=INK, lw=1.3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, weight=weight, zorder=3, linespacing=1.35)


def arrow(ax, p1, p2, text="", color=INK, style="-|>", fs=7.6, rad=0.0, lw=1.4,
          tdx=0.0, tdy=0.06, ha="center", bg=True):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=13,
                                 color=color, linewidth=lw, zorder=4,
                                 connectionstyle=f"arc3,rad={rad}"))
    if text:
        mx, my = (p1[0] + p2[0]) / 2 + tdx, (p1[1] + p2[1]) / 2 + tdy
        ax.text(mx, my, text, fontsize=fs, color=color, ha=ha, va="center", zorder=5,
                bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none", alpha=0.92) if bg else None)


def canvas(w=13, h=7.4, xlim=(0, 13), ylim=(0, 7.4)):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.savefig(FIG / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  ->", FIG / name)


# --------------------------------------------------------------------------- #
# Figure 1 — High-Level Design (black box)
# --------------------------------------------------------------------------- #
def fig_hld():
    fig, ax = canvas()
    ax.text(6.5, 7.1, "Figure 1: High-Level Design (Black-Box) — SignGuard AI",
            ha="center", fontsize=13, weight="bold", color=INK)
    ax.text(6.5, 6.78, "Every arrow is a message on the wire; the box internals are deliberately hidden (Section 3.2 opens the box).",
            ha="center", fontsize=8.4, color=GREY)

    # Left: sources
    box(ax, 0.25, 5.05, 3.0, 0.95, "UNKNOWN USB STICK\n(attacker replaces the file)", fc="#fee2e2", ec=RED, fs=8.6)
    box(ax, 0.25, 3.85, 3.0, 0.95, "ROGUE WI-FI / DEFAULT-CRED\nADMIN PANEL", fc="#fee2e2", ec=RED, fs=8.6)
    box(ax, 0.25, 2.65, 3.0, 0.95, "TRANSPORT AUTHORITY\nblesses genuine content", fc="#dcfce7", ec=GREEN, fs=8.6)
    box(ax, 0.25, 1.35, 3.0, 0.95, "EDGE SENSOR / SIMULATOR\nUSB events, security events", fc=LIGHT, ec=GREY, fs=8.6)

    # Centre: the system
    box(ax, 4.35, 2.15, 4.5, 3.6,
         "SignGuard Layer 2\n(the trust boundary)\n\n"
         "• SHA-256 content integrity\n"
         "• Ed25519-signed hash ledger\n"
         "• Isolation Forest + SHAP\n"
         "• Risk fusion & decision\n"
         "• Append-only audit",
         fc="#eef2ff", ec=BLUE, fs=9.4, weight="bold")
    ax.text(6.6, 1.98, "POST /analyze  ·  REST + WebSocket", ha="center", fontsize=7.8, color=BLUE)

    # Right: outputs
    box(ax, 9.9, 4.55, 2.85, 1.0, "MQTT COMMAND\nrender | safe_fallback | isolate", fc="#fef3c7", ec=AMBER, fs=8.4)
    box(ax, 9.9, 3.3, 2.85, 1.0, "ESP-12E SIGNAGE\nLCD + 2 LEDs + buzzer", fc="#fef3c7", ec=AMBER, fs=8.6)
    box(ax, 9.9, 2.1, 2.85, 1.0, "AUDIT TRAIL + LEDGER\nGET /audit  ·  GET /chain", fc=LIGHT, ec=GREY, fs=8.4)
    box(ax, 9.9, 0.9, 2.85, 1.0, "SAFE FALLBACK TEXT\nshown to the public", fc=LIGHT, ec=GREY, fs=8.4)

    # Inputs
    arrow(ax, (3.25, 5.52), (4.35, 4.95), "content bytes (tampered)", color=RED, tdy=0.22)
    arrow(ax, (3.25, 4.32), (4.35, 4.25), "content bytes (wireless / panel)", color=RED, tdy=0.16)
    arrow(ax, (3.25, 3.12), (4.35, 3.55), "authorized hash", color=GREEN, tdy=-0.2)
    arrow(ax, (3.25, 1.82), (4.35, 2.75), "event stream", color=GREY, tdy=0.16)

    # Outputs
    arrow(ax, (8.85, 5.1), (9.9, 5.05), "decision", color=AMBER, tdy=0.2)
    arrow(ax, (8.85, 4.4), (9.9, 3.85), "", color=AMBER)
    arrow(ax, (8.85, 3.4), (9.9, 2.6), "record", color=GREY)
    arrow(ax, (8.85, 2.5), (9.9, 1.4), "", color=GREY)
    save(fig, "fig1_hld.png")


# --------------------------------------------------------------------------- #
# Figure 2 — Low-Level Design (inside the box)
# --------------------------------------------------------------------------- #
def fig_lld():
    fig, ax = canvas()
    ax.text(6.5, 7.1, "Figure 2: Low-Level Design — modules inside Layer 2",
            ha="center", fontsize=13, weight="bold", color=INK)
    ax.text(6.5, 6.8, "Single entry point: run_analysis() (app/pipeline.py) — REST and MQTT can never diverge.",
            ha="center", fontsize=8.4, color=GREY)

    # Track A (top lane)
    ax.add_patch(Rectangle((0.3, 5.0), 12.4, 1.45, facecolor="#f0fdf4", edgecolor=GREEN,
                           linewidth=1.2, linestyle="--", zorder=1))
    ax.text(0.5, 6.16, "TRACK A — deterministic content integrity (never waits for ML)",
            fontsize=8.8, weight="bold", color=GREEN, zorder=3)
    box(ax, 0.6, 5.2, 2.5, 0.8, "authorization/\nauthorize.py\nSHA-256 → ContentRecord", fc="white", ec=GREEN, fs=8.1)
    box(ax, 3.5, 5.2, 2.5, 0.8, "chain/ledger + registry\nEd25519 sign, hash-linked\nverify_chain()", fc="white", ec=GREEN, fs=8.1)
    box(ax, 6.4, 5.2, 2.5, 0.8, "verification/\nverify.py\nmatch | mismatch", fc="white", ec=GREEN, fs=8.1)
    box(ax, 9.3, 5.2, 3.1, 0.8, "decision/engine.py\nMISMATCH → block\n(terminal, no ML)", fc="#dcfce7", ec=GREEN, fs=8.1, weight="bold")
    arrow(ax, (3.1, 5.6), (3.5, 5.6))
    arrow(ax, (6.0, 5.6), (6.4, 5.6), "hash")
    arrow(ax, (8.9, 5.6), (9.3, 5.6), "result")

    # Track B (bottom lane)
    ax.add_patch(Rectangle((0.3, 2.7), 12.4, 1.7, facecolor="#eff6ff", edgecolor=BLUE,
                           linewidth=1.2, linestyle="--", zorder=1))
    ax.text(0.5, 4.16, "TRACK B — probabilistic attack context (assesses & explains, never gates integrity)",
            fontsize=8.8, weight="bold", color=BLUE, zorder=3)
    box(ax, 0.6, 3.0, 2.1, 0.85, "ingestion/\nEventStore\n(MQTT subscribe)", fc="white", ec=BLUE, fs=8.1)
    box(ax, 3.0, 3.0, 2.1, 0.85, "features/\n7-feature\nwindowed vector", fc="white", ec=BLUE, fs=8.1)
    box(ax, 5.4, 3.0, 2.1, 0.85, "ml_engine/\nIsolationForest\nanomaly 0..1", fc="white", ec=BLUE, fs=8.1)
    box(ax, 7.8, 3.0, 2.1, 0.85, "xai/\nSHAP\ntop factors", fc="white", ec=BLUE, fs=8.1)
    box(ax, 10.2, 3.0, 2.2, 0.85, "scoring/\n0..100 + level", fc="white", ec=BLUE, fs=8.1)
    for a, b in [(2.7, 3.0), (5.1, 5.4), (7.5, 7.8), (9.9, 10.2)]:
        arrow(ax, (a, 3.42), (b, 3.42))

    # Fusion + outputs
    box(ax, 3.4, 1.15, 3.0, 0.9, "risk fusion\n(frozen §9 weights)", fc="#fef3c7", ec=AMBER, fs=8.6)
    box(ax, 6.9, 1.15, 3.0, 0.9, "decision engine\nrender | block | isolate", fc="#fef3c7", ec=AMBER, fs=8.6, weight="bold")
    box(ax, 0.6, 0.35, 2.5, 0.62, "fallback/safe.py", fc=LIGHT, ec=GREY, fs=8.3)
    box(ax, 3.4, 0.35, 2.5, 0.62, "audit/store.py (SQLite)", fc=LIGHT, ec=GREY, fs=8.3)
    box(ax, 6.9, 0.35, 2.6, 0.62, "orchestrator (MQTT out)", fc=LIGHT, ec=GREY, fs=8.3)
    box(ax, 10.0, 0.35, 2.4, 0.62, "web/* pages + /ws", fc=LIGHT, ec=GREY, fs=8.3)

    arrow(ax, (7.6, 3.0), (6.6, 2.05), "anomaly_score", color=BLUE, rad=-0.15, tdx=-0.45, tdy=0.1)
    arrow(ax, (8.7, 5.2), (5.6, 2.05), "MATCH", color=GREEN, rad=0.18, tdx=1.1, tdy=0.5)
    arrow(ax, (6.4, 1.6), (6.9, 1.6), "risk")
    arrow(ax, (8.4, 1.15), (8.4, 0.97), "")
    arrow(ax, (5.0, 1.15), (4.9, 0.97), "")
    arrow(ax, (6.9, 1.4), (3.1, 0.97), "", rad=0.1)
    save(fig, "fig2_lld.png")


# --------------------------------------------------------------------------- #
# Figure 3 — Deployment architecture
# --------------------------------------------------------------------------- #
def fig_arch():
    fig, ax = canvas()
    ax.text(6.5, 7.1, "Figure 3: System Architecture — three planes on one LAN",
            ha="center", fontsize=13, weight="bold", color=INK)

    lanes = [("EDGE / SENSOR PLANE", 4.95, "#f0fdf4", GREEN),
             ("BROKER PLANE", 3.05, "#fef3c7", AMBER),
             ("SERVER PLANE (Layer 2)", 0.6, "#eef2ff", BLUE)]
    for name, y, fc, ec in lanes:
        ax.add_patch(Rectangle((0.3, y), 12.4, 1.75 if y > 4 else 2.2, facecolor=fc,
                               edgecolor=ec, linewidth=1.2, zorder=1))
        ax.text(0.45, y + (1.6 if y > 4 else 2.05), name, fontsize=8.6, weight="bold", color=ec, zorder=3)

    box(ax, 0.7, 5.15, 2.7, 0.95, "USB monitor\nwin_usb_monitor.py\n(insert → event)", fc="white", ec=GREEN, fs=8.2)
    box(ax, 3.7, 5.15, 2.7, 0.95, "Board watcher\nboard_watcher.py\n(insert → detect COM)", fc="white", ec=GREEN, fs=8.2)
    box(ax, 6.7, 5.15, 2.7, 0.95, "Event / content\nsimulators", fc="white", ec=GREEN, fs=8.2)
    box(ax, 9.7, 5.15, 2.7, 0.95, "ESP-12E node\n(browses broker IP)", fc="white", ec=GREEN, fs=8.2)

    box(ax, 3.4, 3.25, 6.0, 1.1, "MOSQUITTO BROKER   0.0.0.0:1883   (LAN-open, anonymous)\n"
                                 "signguard/events  ·  signguard/content  ·  signguard/commands",
         fc="white", ec=AMBER, fs=9, weight="bold")

    box(ax, 0.7, 1.6, 3.2, 1.1, "FastAPI  0.0.0.0:8000\n/analyze /authorize /audit\n/chain /demo/* /ingest/usb", fc="white", ec=BLUE, fs=8.4)
    box(ax, 4.3, 1.6, 3.2, 1.1, "Pipeline run_analysis()\nTrack A + Track B + fusion", fc="white", ec=BLUE, fs=8.4)
    box(ax, 7.9, 1.6, 2.0, 1.1, "SQLite\naudit.db", fc="white", ec=BLUE, fs=8.4)
    box(ax, 10.3, 1.6, 2.1, 1.1, "Ledger\nledger.json", fc="white", ec=BLUE, fs=8.4)
    box(ax, 4.3, 0.75, 5.9, 0.62, "Web UI:  /   ·   /signage   ·   /lab   ·   /chain/view   ·   /docs   ·   ws:/ws", fc="white", ec=GREY, fs=8.4)

    for x in (2.05, 5.05, 8.05, 11.05):
        arrow(ax, (x, 5.15), (6.4 if x < 6.4 else 6.4, 4.35), "publish", color=AMBER, fs=7, rad=0.05)
    arrow(ax, (4.4, 4.35), (4.4, 3.25), "", color=AMBER)
    arrow(ax, (8.4, 4.35), (8.4, 4.35), "")
    arrow(ax, (5.4, 3.25), (3.0, 2.7), "subscribe", color=BLUE, rad=0.1, tdy=-0.28)
    arrow(ax, (7.6, 3.25), (9.6, 2.7), "commands", color=AMBER, rad=-0.1, tdy=-0.28)
    arrow(ax, (3.9, 2.15), (4.3, 2.15))
    arrow(ax, (7.5, 2.15), (7.9, 2.15))
    arrow(ax, (9.9, 2.15), (10.3, 2.15))
    arrow(ax, (7.2, 1.6), (7.2, 1.37), "")
    save(fig, "fig3_architecture.png")


# --------------------------------------------------------------------------- #
# Figure 4 — Sequence diagram (the malicious-USB attack)
# --------------------------------------------------------------------------- #
def fig_sequence():
    fig, ax = canvas(13, 7.8, (0, 13), (0, 7.8))
    ax.text(6.5, 7.5, "Figure 4: Sequence Diagram — malicious USB insertion (end to end)",
            ha="center", fontsize=13, weight="bold", color=INK)

    actors = [
        (1.1, "Attacker /\nUSB stick"),
        (3.1, "Edge monitor\n(win_usb_monitor)"),
        (5.1, "MQTT broker\n:1883"),
        (7.1, "Layer 2\nrun_analysis()"),
        (9.1, "Ledger +\nAudit store"),
        (11.6, "ESP-12E sign\nLCD + buzzer"),
    ]
    for x, name in actors:
        box(ax, x - 0.95, 6.25, 1.9, 0.72, name, fc=LIGHT, ec=INK, fs=7.8, weight="bold")
        ax.plot([x, x], [1.0, 6.25], color=GREY, linewidth=1.1, linestyle=(0, (4, 3)), zorder=1)

    steps = [
        (1.1, 3.1, 5.72, "1  plug in unknown stick", RED),
        (3.1, 5.1, 5.34, "2  signguard/events: unauthorized_usb + content_received", GREY),
        (5.1, 7.1, 4.96, "3  events + tampered content (b64)", BLUE),
        (7.1, 9.1, 4.58, "4  SHA-256(bytes) vs signed hash", GREEN),
        (9.1, 7.1, 4.20, "5  MISMATCH  (verify_chain OK, hash differs)", RED),
        (7.1, 7.1, 3.82, "6  IsolationForest score + SHAP factors  →  risk 71/100 (high)", BLUE),
        (7.1, 9.1, 3.44, "7  audit row: block / risk 71 / hash_mismatch", GREY),
        (7.1, 5.1, 3.06, "8  signguard/commands: safe_fallback + attack label", AMBER),
        (5.1, 11.6, 2.68, "9  command received", AMBER),
        (11.6, 11.6, 2.30, "10  LCD: TAMPER DETECTED / USB TAMPER · red LED · buzzer 1.2 s", RED),
        (7.1, 5.1, 1.92, "11  safe-fallback text to the web sign", GREY),
        (5.1, 3.1, 1.54, "12  state reset on removal → watcher cache cleared", GREY),
    ]
    for x1, x2, y, label, col in steps:
        arrow(ax, (x1, y), (x2 - (0.12 if x2 > x1 else -0.12) if x1 != x2 else x2 + 0.0, y),
              color=col, fs=7.4, rad=0.0, lw=1.3)
        if x1 == x2:
            ax.plot([x1], [y], marker="o", color=col, markersize=6, zorder=5)
        ax.text(min(x1, x2) + 0.18, y + 0.17, label, fontsize=7.4, color=col, ha="left", zorder=6)

    ax.add_patch(Rectangle((6.7, 2.14), 0.8, 3.9, facecolor="#fee2e2", edgecolor="none", alpha=0.35, zorder=0))
    ax.text(7.1, 6.06, "Track A gate = steps 4–5 (ML only refines a MATCH)", fontsize=7.4,
            color=RED, ha="center", style="italic")
    save(fig, "fig4_sequence.png")


# --------------------------------------------------------------------------- #
# Figure 5 — Decision flow (two-track gate)
# --------------------------------------------------------------------------- #
def fig_flow():
    fig, ax = canvas(11.5, 7.2, (0, 11.5), (0, 7.2))
    ax.text(5.75, 6.9, "Figure 5: Decision flow — the hash gate runs first, ML only refines a match",
            ha="center", fontsize=12.5, weight="bold", color=INK)

    def diamond(cx, cy, w, h, text):
        ax.add_patch(plt.Polygon([(cx, cy + h), (cx + w, cy), (cx, cy - h), (cx - w, cy)],
                                 facecolor="#fef3c7", edgecolor=AMBER, linewidth=1.4, zorder=2))
        ax.text(cx, cy, text, ha="center", va="center", fontsize=8.4, zorder=3, linespacing=1.35)

    box(ax, 4.35, 6.05, 2.8, 0.6, "content update arrives", fc=LIGHT, ec=INK, fs=8.8)
    diamond(5.75, 5.05, 1.85, 0.62, "SHA-256 matches an\nauthorized signed hash?")
    box(ax, 0.5, 3.55, 2.9, 0.85, "BLOCK → safe_fallback\nreason: hash_mismatch\n(+40 risk points)", fc="#fee2e2", ec=RED, fs=8.5, weight="bold")
    box(ax, 4.35, 3.75, 2.8, 0.62, "Track B: Isolation Forest\n→ anomaly 0..1", fc="#eff6ff", ec=BLUE, fs=8.3)
    diamond(5.75, 2.5, 1.85, 0.6, "risk score")
    box(ax, 8.3, 4.35, 2.7, 0.8, "ISOLATE → isolate\nreason: critical_risk\n(≥ 80)", fc="#ffedd5", ec=AMBER, fs=8.5, weight="bold")
    box(ax, 8.3, 3.05, 2.7, 0.8, "BLOCK → safe_fallback\nreason: elevated_risk\n(50–79)", fc="#fee2e2", ec=RED, fs=8.5, weight="bold")
    box(ax, 0.5, 1.45, 2.9, 0.8, "RENDER verified content\nreason: hash_match +\nrisk_acceptable (< 50)", fc="#dcfce7", ec=GREEN, fs=8.5, weight="bold")
    box(ax, 4.35, 0.4, 2.8, 0.62, "audit row + MQTT command", fc=LIGHT, ec=GREY, fs=8.4)

    arrow(ax, (5.75, 6.05), (5.75, 5.67))
    arrow(ax, (3.9, 5.05), (3.4, 4.4), "NO  (terminal:\nML never consulted)", color=RED, tdx=-0.35, tdy=0.32, fs=7.6)
    arrow(ax, (5.75, 4.43), (5.75, 4.37), "YES", color=GREEN, tdx=0.42, tdy=0.0, fs=7.8)
    arrow(ax, (7.15, 5.05), (9.0, 4.9), "NO update", color=GREY, fs=7.6, tdy=0.2)
    arrow(ax, (7.15, 2.6), (9.0, 3.25), "≥ 80", color=AMBER, fs=7.8, tdx=0.1, tdy=0.28)
    arrow(ax, (3.9, 2.5), (3.4, 1.85), "50–79", color=RED, fs=7.8, tdx=-0.2, tdy=0.3)
    arrow(ax, (5.75, 3.75), (5.75, 3.12), "", color=BLUE)
    arrow(ax, (4.35, 2.5), (3.4, 1.95), "< 50", color=GREEN, fs=7.8, tdx=-0.2, tdy=0.3)
    arrow(ax, (1.95, 3.55), (1.95, 2.25), "", color=RED)
    arrow(ax, (1.95, 1.45), (4.9, 1.02), "", color=GREEN, rad=-0.1)
    arrow(ax, (9.6, 3.05), (6.5, 1.02), "", color=RED, rad=0.15)
    arrow(ax, (9.6, 4.35), (6.7, 1.02), "", color=AMBER, rad=0.18)
    save(fig, "fig5_decision_flow.png")


# --------------------------------------------------------------------------- #
# Figure 6 — risk scores (real measurements)
# --------------------------------------------------------------------------- #
def fig_risk():
    rows = METRICS["scenarios"]
    labels = ["Baseline\n(authorized)", "Malicious\nUSB", "Rogue\nWi-Fi", "Default-cred\nadmin"]
    keys = ["baseline", "usb", "wireless", "credential"]
    vals = [next(r["risk"] for r in rows if r["id"] == k) for k in keys]
    cols = [GREEN if v < 25 else AMBER if v < 50 else RED for v in vals]

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    bars = ax.bar(labels, vals, color=cols, width=0.58, edgecolor=INK, linewidth=0.9, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2.4, str(v), ha="center",
                fontsize=11, weight="bold", color=INK)
    for y, lab, c in [(24, "low ≤ 24", GREEN), (49, "medium ≤ 49", AMBER),
                      (79, "high ≤ 79", RED), (80, "critical ≥ 80", "#7c3aed")]:
        ax.axhline(y, color=c, linestyle="--", linewidth=1.1, alpha=0.75, zorder=2)
        ax.text(3.62, y + 1.5, lab, fontsize=7.8, color=c, ha="right")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Risk score (0–100)", fontsize=10)
    ax.set_title("Figure 6: Measured risk score per scenario (live /analyze runs)",
                 fontsize=12, weight="bold", pad=14)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "fig6_risk.png")


# --------------------------------------------------------------------------- #
# Figure 7 — latency
# --------------------------------------------------------------------------- #
def fig_latency():
    h = METRICS["http_latency_ms"]
    p = METRICS["pipeline_latency_ms"]
    items = [
        ("Pipeline only\n(run_analysis, n=40)", p["usb"]["median"]),
        ("HTTP keep-alive\n127.0.0.1 (n=50)", h["analyze_keepalive_ipv4"]["median"]),
        ("HTTP new conn.\n127.0.0.1 (n=15)", h["analyze_fresh_ipv4"]["median"]),
        ("HTTP new conn.\nlocalhost → ::1 (n=15)", h["analyze_fresh_localhost"]["median"]),
    ]
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    names = [i[0] for i in items]
    vals = [i[1] for i in items]
    cols = [GREEN, GREEN, AMBER, RED]
    bars = ax.bar(names, vals, color=cols, width=0.55, edgecolor=INK, linewidth=0.9, zorder=3)
    ax.set_yscale("log")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.15, f"{v:,.1f} ms", ha="center",
                fontsize=9.5, weight="bold", color=INK)
    ax.set_ylabel("Median end-to-end latency (ms, log scale)", fontsize=10)
    ax.set_title("Figure 7: Decision latency — pipeline vs transport (measured)",
                 fontsize=12, weight="bold", pad=14)
    ax.grid(axis="y", alpha=0.25, which="both", zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize=8.4)
    fig.tight_layout()
    save(fig, "fig7_latency.png")


# --------------------------------------------------------------------------- #
# Figure 8 — SHAP explanation for the USB attack
# --------------------------------------------------------------------------- #
def fig_shap():
    usb = next(r for r in METRICS["scenarios"] if r["id"] == "usb")
    fac = usb["shap"]
    names = [f["name"].replace("_", " ") for f in fac][::-1]
    vals = [f["impact"] for f in fac][::-1]
    cols = [RED if v > 0 else GREEN for v in vals]

    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.barh(names, vals, color=cols, edgecolor=INK, linewidth=0.8, height=0.6, zorder=3)
    for y, v in enumerate(vals):
        ax.text(v + (0.12 if v >= 0 else -0.12), y, f"{v:+.2f}",
                va="center", ha="left" if v >= 0 else "right", fontsize=8.8, weight="bold")
    ax.axvline(0, color=INK, linewidth=1.1)
    ax.set_xlabel("SHAP impact on the anomaly assessment (points toward 'suspicious' →)", fontsize=9.5)
    ax.set_title(f"Figure 8: SHAP explanation of the malicious-USB assessment (risk {usb['risk']}/100)",
                 fontsize=12, weight="bold", pad=14)
    ax.grid(axis="x", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=8.8)
    fig.tight_layout()
    save(fig, "fig8_shap.png")


# --------------------------------------------------------------------------- #
# Figure 9 — outcomes (verification vs decision)
# --------------------------------------------------------------------------- #
def fig_outcomes():
    rows = METRICS["scenarios"]
    keys = ["baseline", "usb", "wireless", "credential"]
    names = ["Baseline", "Malicious USB", "Rogue Wi-Fi", "Default-cred admin"]
    risk = [next(r["risk"] for r in rows if r["id"] == k) for k in keys]
    dec = [next(r["decision"] for r in rows if r["id"] == k) for k in keys]
    match = [next(r["verified_match"] for r in rows if r["id"] == k) for k in keys]

    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    x = range(len(keys))
    bars = ax.bar(x, risk, color=[GREEN if m else RED for m in match], width=0.55,
                  edgecolor=INK, linewidth=0.9, zorder=3)
    for i, (b, d, m) in enumerate(zip(bars, dec, match)):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 2.2, d.upper(),
                ha="center", fontsize=9.5, weight="bold",
                color=GREEN if d == "render" else RED)
        ax.text(b.get_x() + b.get_width() / 2, 3, "MATCH" if m else "MISMATCH",
                ha="center", fontsize=8, color="white", weight="bold",
                rotation=90 if not m else 0)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Risk score", fontsize=10)
    ax.set_title("Figure 9: Verification outcome vs. final decision (4 scenarios, 4 correct)",
                 fontsize=12, weight="bold", pad=14)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "fig9_outcomes.png")


# --------------------------------------------------------------------------- #
# Figure 10 — test suite
# --------------------------------------------------------------------------- #
def fig_tests():
    files = ["test_track_a", "test_track_b", "test_scoring", "test_secure_chain",
             "test_audit", "test_demo", "test_api"]
    counts = [6, 6, 8, 6, 5, 11, 4]
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    bars = ax.barh(files[::-1], counts[::-1], color=BLUE, edgecolor=INK,
                   linewidth=0.8, height=0.6, zorder=3)
    for b, c in zip(bars, counts[::-1]):
        ax.text(c + 0.15, b.get_y() + b.get_height() / 2, f"{c} passed",
                va="center", fontsize=9, weight="bold", color=INK)
    ax.set_xlim(0, 13)
    ax.set_xlabel("Number of test cases", fontsize=9.5)
    ax.set_title("Figure 10: Automated test suite — 46/46 passing (7 modules)",
                 fontsize=12, weight="bold", pad=14)
    ax.grid(axis="x", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=9)
    fig.tight_layout()
    save(fig, "fig10_tests.png")


if __name__ == "__main__":
    print("building figures…")
    fig_hld()
    fig_lld()
    fig_arch()
    fig_sequence()
    fig_flow()
    fig_risk()
    fig_latency()
    fig_shap()
    fig_outcomes()
    fig_tests()
    print("done:", len(list(FIG.glob('*.png'))), "figures")
