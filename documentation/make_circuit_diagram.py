"""Circuit / wiring diagram for the SignGuard AI edge node (NodeMCU ESP-12E).

    python documentation/make_circuit_diagram.py

Writes documentation/figures/fig11_circuit.png (200 dpi) — the authoritative
wiring reference. Pin numbers come from usb_demo/esp8266/config.example.py:

    LCD I2C  SDA -> D2 / GPIO4,  SCL -> D1 / GPIO5,  addr 0x27 (PCF8574)
    Buzzer +      -> D5 / GPIO14 (PWM 2 kHz, duty 700, 1.2 s alarm)
    Green LED     -> D6 / GPIO12 (220 ohm series)
    Red LED       -> D7 / GPIO13 (220 ohm series)
    FLASH button  -> D3 / GPIO0  (onboard, no wiring)

All D-pins and the 3V3/GND used here sit on the RIGHT edge of the NodeMCU
header (as on the physical board); the LCD signals therefore route over the
top of the module. The common ground rail and the pin table sit BELOW the
circuit so nothing overlaps.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

HERE = Path(__file__).parent
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)

INK = "#1f2937"
BLUE = "#2563eb"    # I2C signal
RED = "#dc2626"     # power (+3V3) and the red LED branch
BLACK = "#111827"   # ground
AMBER = "#d97706"   # buzzer drive
GREY = "#6b7280"
LIGHT = "#f3f4f6"
GREEN_LED = "#16a34a"

RAIL_Y = 5.05       # common ground rail
BOARD = (5.3, 5.4, 2.8, 3.9)   # x, y, w, h  -> top edge at 9.3
BX, BY, BW, BH = BOARD
BR = BX + BW        # board right edge (8.1)


def wire(ax, pts, color=INK, lw=1.6):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, zorder=3,
            solid_capstyle="round", solid_joinstyle="round")


def pin(ax, x, y, label, side="right", color=INK):
    ax.plot([x], [y], "o", ms=5.5, color=color, zorder=5)
    dx = 0.12 if side == "left" else -0.12
    ax.text(x + dx, y, label, ha="left" if side == "left" else "right",
            va="center", fontsize=7.8, color=INK, weight="bold", zorder=6)


def led_symbol(ax, x, y, color):
    ax.add_patch(Polygon([[x, y - 0.13], [x, y + 0.13], [x + 0.3, y]],
                         closed=True, facecolor=color, edgecolor=INK, lw=1.1, zorder=4))
    ax.plot([x + 0.3, x + 0.3], [y - 0.15, y + 0.15], color=INK, lw=1.6, zorder=4)
    ax.annotate("", xy=(x + 0.52, y + 0.30), xytext=(x + 0.34, y + 0.15),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.0))
    ax.annotate("", xy=(x + 0.58, y + 0.20), xytext=(x + 0.42, y + 0.05),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.0))


def resistor(ax, x, y, w=0.62):
    ax.add_patch(FancyBboxPatch((x, y - 0.11), w, 0.22,
                                boxstyle="round,pad=0.01,rounding_size=0.05",
                                facecolor="white", edgecolor=INK, lw=1.2, zorder=4))
    ax.text(x + w / 2, y, "220\u03a9", ha="center", va="center",
            fontsize=7.2, color=INK, zorder=5)


def build():
    fig, ax = plt.subplots(figsize=(13.2, 10.0))
    ax.set_xlim(0, 13.2)
    ax.set_ylim(1.85, 10.6)
    ax.axis("off")

    ax.text(6.6, 10.35, "Circuit Diagram \u2014 SignGuard AI Edge Node (NodeMCU ESP-12E)",
            ha="center", fontsize=14, weight="bold", color=INK)
    ax.text(6.6, 10.08, "16\u00d72 I2C LCD (PCF8574 @ 0x27) \u00b7 buzzer \u00b7 green/red LED pair \u00b7 onboard FLASH button",
            ha="center", fontsize=9, color=GREY)

    # ------------------------------------------------------------------ #
    # NodeMCU board (centre)
    # ------------------------------------------------------------------ #
    ax.add_patch(FancyBboxPatch((BX, BY), BW, BH,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor=LIGHT, edgecolor=INK, lw=1.8, zorder=2))
    ax.text(BX + BW / 2, 9.05, "NodeMCU ESP-12E", ha="center",
            fontsize=10.5, weight="bold", color=INK, zorder=3)
    ax.text(BX + BW / 2, 8.84, "(ESP8266 \u00b7 MicroPython)", ha="center",
            fontsize=7.8, color=GREY, zorder=3)
    # ESP-12E shield
    ax.add_patch(Rectangle((6.35, 7.9), 1.4, 0.75, facecolor="#d1d5db",
                           edgecolor=GREY, lw=0.8, zorder=3))
    ax.text(7.05, 8.28, "ESP8266EX", ha="center", va="center",
            fontsize=7.2, color=INK, zorder=4)
    # onboard FLASH button
    ax.add_patch(FancyBboxPatch((5.55, 6.95), 1.5, 0.6,
                                boxstyle="round,pad=0.01,rounding_size=0.06",
                                facecolor="white", edgecolor=INK, lw=1.1, zorder=4))
    ax.text(6.30, 7.32, "FLASH button", ha="center", va="center",
            fontsize=7.2, weight="bold", color=INK, zorder=5)
    ax.text(6.30, 7.10, "GPIO0 / D3 \u00b7 onboard", ha="center", va="center",
            fontsize=6.6, color=GREY, zorder=5)
    ax.text(6.30, 6.78, "no external wiring",
            ha="center", va="center", fontsize=6.5, color=GREY, style="italic", zorder=5)
    # USB connector on the bottom edge
    ax.add_patch(Rectangle((6.35, BY - 0.14), 0.9, 0.28, facecolor="#9ca3af",
                           edgecolor=INK, lw=1.0, zorder=4))
    ax.text(6.80, 5.78, "USB \u2192 5 V in / flash", ha="center",
            fontsize=7.2, color=GREY, zorder=4)

    # right-edge pins (top -> bottom): D1 D2 3V3 D5 D6 D7
    pin(ax, BR, 8.8, "D1 / SCL", "right", BLUE)
    pin(ax, BR, 8.2, "D2 / SDA", "right", BLUE)
    pin(ax, BR, 7.6, "3V3", "right", RED)
    pin(ax, BR, 6.9, "D5 (buz)", "right", AMBER)
    pin(ax, BR, 6.3, "D6 (grn)", "right", GREEN_LED)
    pin(ax, BR, 5.7, "D7 (red)", "right", RED)
    # left-edge GND -> straight down to the rail
    pin(ax, BX, 6.6, "GND", "left", BLACK)
    wire(ax, [(BX, 6.6), (BX, RAIL_Y)], BLACK)

    # ------------------------------------------------------------------ #
    # LCD module (top-left) — header pins GND VCC SDA SCL on the top edge
    # ------------------------------------------------------------------ #
    lx, ly, lw_, lh = 1.1, 7.95, 3.0, 1.25
    ax.add_patch(FancyBboxPatch((lx, ly), lw_, lh,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                facecolor="white", edgecolor=INK, lw=1.6, zorder=2))
    ax.add_patch(Rectangle((lx + 0.18, ly + 0.13), lw_ - 0.36, 0.74,
                           facecolor="#0f172a", edgecolor=INK, lw=0.8, zorder=3))
    ax.text(lx + lw_ / 2, ly + 0.60, "SYSTEM SECURE", ha="center", va="center",
            fontsize=7.4, color="#4ade80", family="monospace", zorder=4)
    ax.text(lx + lw_ / 2, ly + 0.33, "Content verified", ha="center", va="center",
            fontsize=6.8, color="#e5e7eb", family="monospace", zorder=4)
    ax.text(lx + lw_ / 2, ly + 1.03, "16\u00d72 LCD + I2C backpack", ha="center",
            va="center", fontsize=8.2, weight="bold", color=INK, zorder=4)

    lcd = {"GND": 1.6, "VCC": 2.3, "SDA": 3.0, "SCL": 3.65}
    for name, px in lcd.items():
        ax.plot([px], [ly + lh], "o", ms=5, color=INK, zorder=5)
        ax.text(px, ly + lh + 0.07, name, ha="center", va="bottom",
                fontsize=7, color=INK, zorder=5)

    # LCD wiring — planar routes over the top of the board, zero crossings
    # LCD GND: left, down, onto the rail
    wire(ax, [(lcd["GND"], 9.2), (0.55, 9.2), (0.55, RAIL_Y)], BLACK)
    # VCC: highest channel -> far-right drop -> 3V3
    wire(ax, [(lcd["VCC"], 9.2), (lcd["VCC"], 9.9), (9.25, 9.9),
              (9.25, 7.6), (BR, 7.6)], RED)
    # SDA: middle channel -> drop right of SCL -> D2
    wire(ax, [(lcd["SDA"], 9.2), (lcd["SDA"], 9.75), (8.95, 9.75),
              (8.95, 8.2), (BR, 8.2)], BLUE)
    # SCL: lowest channel -> first drop -> D1
    wire(ax, [(lcd["SCL"], 9.2), (lcd["SCL"], 9.55), (8.7, 9.55),
              (8.7, 8.8), (BR, 8.8)], BLUE)

    # ------------------------------------------------------------------ #
    # Buzzer (right, upper)
    # ------------------------------------------------------------------ #
    zx, zy, zw, zh = 9.6, 7.55, 1.7, 0.9
    ax.add_patch(FancyBboxPatch((zx, zy), zw, zh,
                                boxstyle="round,pad=0.02,rounding_size=0.18",
                                facecolor="#fef3c7", edgecolor=AMBER, lw=1.6, zorder=2))
    ax.text(zx + zw / 2, zy + 0.60, "BUZZER", ha="center", va="center",
            fontsize=9, weight="bold", color=INK, zorder=3)
    ax.text(zx + zw / 2, zy + 0.30, "2 kHz \u00b7 1.2 s alarm", ha="center",
            va="center", fontsize=6.9, color=GREY, zorder=3)
    ax.plot([zx], [zy + 0.55], "o", ms=5, color=AMBER, zorder=5)
    ax.text(zx - 0.12, zy + 0.55, "+", ha="right", va="center", fontsize=11,
            weight="bold", color=AMBER, zorder=5)
    ax.plot([zx + zw], [zy + 0.35], "o", ms=5, color=BLACK, zorder=5)
    ax.text(zx + zw + 0.12, zy + 0.35, "\u2212", ha="left", va="center", fontsize=11,
            weight="bold", color=BLACK, zorder=5)

    # D5 -> buzzer +
    wire(ax, [(BR, 6.9), (9.45, 6.9), (9.45, zy + 0.55), (zx, zy + 0.55)], AMBER)
    ax.text(9.18, 7.25, "D5 / GPIO14 (PWM)", fontsize=7, color=AMBER,
            rotation=90, ha="right", va="center")
    # buzzer - -> down to the rail (right-hand gutter)
    wire(ax, [(zx + zw, zy + 0.35), (11.6, zy + 0.35), (11.6, RAIL_Y)], BLACK)

    # ------------------------------------------------------------------ #
    # LED branches (right, below the buzzer)
    # ------------------------------------------------------------------ #
    gy = 6.3   # green = D6
    wire(ax, [(BR, gy), (8.95, gy)], GREEN_LED)
    resistor(ax, 8.95, gy)
    wire(ax, [(9.57, gy), (9.9, gy)], GREEN_LED)
    led_symbol(ax, 9.9, gy, GREEN_LED)
    wire(ax, [(10.2, gy), (10.55, gy), (10.55, RAIL_Y)], BLACK)
    ax.text(9.9, gy + 0.42, "green = secure", fontsize=7, color=GREEN_LED, ha="center")

    ry = 5.7   # red = D7
    wire(ax, [(BR, ry), (8.85, ry)], RED)
    resistor(ax, 8.85, ry)
    wire(ax, [(9.47, ry), (9.8, ry)], RED)
    led_symbol(ax, 9.8, ry, RED)
    wire(ax, [(10.1, ry), (10.3, ry), (10.3, RAIL_Y)], BLACK)
    ax.text(9.8, ry - 0.42, "red = tamper", fontsize=7, color=RED, ha="center")

    # ------------------------------------------------------------------ #
    # Common ground rail
    # ------------------------------------------------------------------ #
    wire(ax, [(0.55, RAIL_Y), (11.6, RAIL_Y)], BLACK, lw=2.4)
    ax.text(0.62, 4.80, "GND rail (common)", fontsize=7.6, color=BLACK, style="italic")

    # ------------------------------------------------------------------ #
    # Automatic-alarm note (below the LCD, above the legend)
    # ------------------------------------------------------------------ #
    ax.add_patch(FancyBboxPatch((0.9, 6.95), 4.1, 0.9,
                                boxstyle="round,pad=0.04,rounding_size=0.08",
                                facecolor="#fffbeb", edgecolor=AMBER, lw=1.2, zorder=2))
    ax.text(2.95, 7.68, "Automatic alarm \u2014 buzzer on USB insert", ha="center",
            fontsize=8.2, weight="bold", color=INK, zorder=3)
    ax.text(2.95, 7.30,
            "USB stick inserted \u2192 detector POSTs /ingest/usb\n"
            "\u2192 SHA-256 mismatch vs signed ledger\n"
            "\u2192 MQTT signguard/commands: safe_fallback\n"
            "\u2192 firmware buzzes D5 for 1.2 s + red LED blinks",
            ha="center", va="center", fontsize=6.9, color=INK, zorder=3, linespacing=1.45)

    # ------------------------------------------------------------------ #
    # Wire legend
    # ------------------------------------------------------------------ #
    ax.add_patch(FancyBboxPatch((0.9, 5.12), 3.35, 1.55,
                                boxstyle="round,pad=0.04,rounding_size=0.08",
                                facecolor="white", edgecolor=GREY, lw=1.0, zorder=2))
    ax.text(1.08, 6.50, "Wire legend", fontsize=8, weight="bold", color=INK, zorder=3)
    for i, (c, lab) in enumerate([(RED, "+3V3 power"), (BLACK, "GND"),
                                  (BLUE, "I2C signal (SDA / SCL)"),
                                  (GREEN_LED, "green LED drive (D6)"),
                                  (AMBER, "buzzer drive (D5)")]):
        yy = 6.30 - i * 0.19
        ax.plot([1.1, 1.55], [yy, yy], color=c, lw=2, zorder=3)
        ax.text(1.68, yy, lab, fontsize=7.1, color=INK, va="center", zorder=3)
    ax.text(1.08, 5.26, "Red LED (D7) is wired exactly like green:\n220\u03a9 + LED to the GND rail.",
            fontsize=6.6, color=GREY, style="italic", zorder=3, linespacing=1.35)

    # ------------------------------------------------------------------ #
    # Pin map table (bottom, below the rail)
    # ------------------------------------------------------------------ #
    rows = [
        ("LCD \u2014 I2C data",  "SDA", "D2",  "GPIO4",  "software I2C, 100 kHz"),
        ("LCD \u2014 I2C clock", "SCL", "D1",  "GPIO5",  "backpack PCF8574, addr 0x27"),
        ("LCD \u2014 supply",    "VCC", "3V3", "\u2014",  "backpack also tolerates 5 V"),
        ("LCD \u2014 ground",    "GND", "GND", "\u2014",  "common rail"),
        ("Buzzer \u2014 +",      "I/O", "D5",  "GPIO14", "PWM 2 kHz, duty 700 = on, 1.2 s"),
        ("Buzzer \u2014 \u2212", "GND", "GND", "\u2014",  "common rail"),
        ("Green LED",       "anode", "D6", "GPIO12", "220\u03a9 series; lit = secure"),
        ("Red LED",         "anode", "D7", "GPIO13", "220\u03a9 series; blink = tamper"),
        ("FLASH button",       "\u2014", "D3", "GPIO0", "onboard; pressed = LOW, demo cycle"),
    ]
    cols = ["Component", "Signal", "NodeMCU pin", "GPIO", "Note"]
    xs = [0.9, 4.1, 5.35, 6.95, 8.35]
    ytop = 4.62
    ax.add_patch(Rectangle((0.8, ytop - 0.34), 11.9, 0.34, facecolor=LIGHT,
                           edgecolor=GREY, lw=0.8, zorder=2))
    for x, c in zip(xs, cols):
        ax.text(x, ytop - 0.17, c, fontsize=8, weight="bold", color=INK, zorder=3)
    for i, row in enumerate(rows):
        yy = ytop - 0.60 - i * 0.265
        for x, cell in zip(xs, row):
            ax.text(x, yy, cell, fontsize=7.4, color=INK, zorder=3)

    out = FIG / "fig11_circuit.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  ->", out)


if __name__ == "__main__":
    build()
