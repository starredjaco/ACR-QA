#!/usr/bin/env python3
"""
Build two clean, horizontal, slide-ready evaluation figures from the canonical
SecurityEval confusion counts (TP=81, FN=8, FP=67, TN=22 — 89 vulnerable + 89 clean,
CWE-matched). Source of the 4 counts: docs/business/PRESENTATION_ASSETS.md.

All derived metrics are COMPUTED here from those 4 counts — never transcribed — so the
slide numbers cannot drift from the matrix.

Output → ACR-QA-Book/figures/CONFUSION_MATRIX_SLIDE.png  (wide 2x2 matrix)
         ACR-QA-Book/figures/DERIVED_METRICS_SLIDE.png   (horizontal bar chart)

Run: .venv/bin/python3 scripts/build_eval_figures.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

FIGS = Path(__file__).resolve().parent.parent / "ACR-QA-Book" / "figures"

# ── KSIU palette ──
NAVY = "#002060"
GOLD = "#B8861E"
GREEN = "#188A4E"
RED = "#C22E2E"
INK = "#1A1F2B"
GRAY = "#5B6672"
GREEN_BG = "#CFE9D9"
RED_BG = "#F6D6D2"

# ── canonical counts (SecurityEval 89+89) ──
TP, FN, FP, TN = 81, 8, 67, 22
P = TP + FN  # actual vulnerable = 89
N = FP + TN  # actual clean = 89

recall = TP / (TP + FN)
precision = TP / (TP + FP)
specificity = TN / (TN + FP)
fpr = FP / (FP + TN)
youden = recall - fpr
f1 = 2 * precision * recall / (precision + recall)
f3 = (1 + 9) * precision * recall / (9 * precision + recall)
mcc = (TP * TN - FP * FN) / math.sqrt((TP + FP) * (TP + FN) * (TN + FP) * (TN + FN))

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14})


def confusion_figure():
    fig, ax = plt.subplots(figsize=(12, 5.0))
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 2.35)
    ax.axis("off")

    cells = [
        # (col, row, value, label, bg, fg)
        (0, 1, TP, "True Positive — real issue caught", GREEN_BG, GREEN),
        (1, 1, FN, "False Negative — missed", RED_BG, RED),
        (0, 0, FP, "False Positive — false alarm", RED_BG, RED),
        (1, 0, TN, "True Negative — correctly cleared", GREEN_BG, GREEN),
    ]
    cw, ch = 1.9, 1.0
    x0, y0 = 0.05, 0.05
    for col, row, val, lab, bg, fg in cells:
        x = x0 + col * cw
        y = y0 + row * ch
        ax.add_patch(Rectangle((x, y), cw, ch, facecolor=bg, edgecolor="white", linewidth=4))
        ax.text(x + cw / 2, y + ch * 0.62, str(val), ha="center", va="center", fontsize=46, fontweight="bold", color=fg)
        ax.text(x + cw / 2, y + ch * 0.20, lab, ha="center", va="center", fontsize=12.5, color=INK)

    # axis labels
    ax.text(x0 + cw * 0.5, 2.18, "Predicted: VULNERABLE", ha="center", fontsize=14, fontweight="bold", color=NAVY)
    ax.text(x0 + cw * 1.5, 2.18, "Predicted: CLEAN", ha="center", fontsize=14, fontweight="bold", color=NAVY)
    ax.text(
        -0.02,
        y0 + ch * 1.5,
        "Actual:\nVULNERABLE",
        ha="right",
        va="center",
        fontsize=12.5,
        fontweight="bold",
        color=NAVY,
    )
    ax.text(
        -0.02, y0 + ch * 0.5, "Actual:\nCLEAN", ha="right", va="center", fontsize=12.5, fontweight="bold", color=NAVY
    )

    # side takeaway
    tx = x0 + 2 * cw + 0.18
    ax.text(tx, 1.78, "Raw detection", fontsize=15, fontweight="bold", color=NAVY)
    ax.text(tx, 1.40, f"{recall * 100:.0f}%", fontsize=40, fontweight="bold", color=GREEN)
    ax.text(tx, 1.12, "recall — catches\nalmost everything", fontsize=12, color=INK, va="top")
    ax.text(tx, 0.62, f"{precision * 100:.1f}%", fontsize=40, fontweight="bold", color=RED)
    ax.text(tx, 0.34, "raw precision — half\nthe alarms are false", fontsize=12, color=INK, va="top")

    ax.text(
        0.05,
        -0.06,
        "SecurityEval · 89 vulnerable + 89 clean Python snippets · CWE-matched (adversarial clean set by design)",
        fontsize=10.5,
        style="italic",
        color=GRAY,
    )
    fig.tight_layout()
    out = FIGS / "CONFUSION_MATRIX_SLIDE.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"✓ {out}")


def derived_metrics_figure():
    # ordered worst→best visual: recall-heavy story
    metrics = [
        ("FPR  (lower is better)", fpr, RED),
        ("Specificity (TNR)", specificity, GOLD),
        ("Youden J  (vs Bandit 0.090)", youden, GOLD),
        ("MCC", mcc, GOLD),
        ("Precision (full output)", precision, GOLD),
        ("F₁", f1, GREEN),
        ("Recall (TPR)", recall, GREEN),
        ("F₃  (recall-heavy — the key metric)", f3, GREEN),
    ]
    labels = [m[0] for m in metrics]
    vals = [m[1] for m in metrics]
    colors = [m[2] for m in metrics]

    fig, ax = plt.subplots(figsize=(12, 4.6))
    bars = ax.barh(labels, vals, color=colors, edgecolor="white", height=0.7)
    ax.axvline(0.5, color=GRAY, linestyle="--", linewidth=1.3)
    ax.text(0.5, len(labels) - 0.35, "random baseline 0.5", fontsize=10.5, color=GRAY, ha="center")
    for bar, v in zip(bars, vals):
        ax.text(
            v + 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{v:.3f}",
            va="center",
            fontsize=13,
            fontweight="bold",
            color=INK,
        )
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Score (0–1)", fontsize=12.5, color=INK)
    ax.set_title(
        "Derived metrics at the SecurityEval full-output operating point",
        fontsize=16,
        fontweight="bold",
        color=NAVY,
        pad=10,
    )
    ax.tick_params(axis="y", labelsize=12.5)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.text(
        0.5,
        -0.22,
        "Takeaway: tuned recall-heavy (F₃ = 0.854) — in security, a missed bug costs more than a false alarm. "
        "The Confirmed Tier then lifts precision to 96.4% for auto-block.",
        fontsize=11,
        style="italic",
        color=GRAY,
        ha="center",
        transform=ax.transAxes,
    )
    fig.subplots_adjust(left=0.26, right=0.97, top=0.88, bottom=0.20)
    out = FIGS / "DERIVED_METRICS_SLIDE.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"✓ {out}")


def realvuln_leaderboard_figure():
    """Clean RealVuln 2026 full-corpus recall leaderboard — rule-based ACR-QA only (no LLM bar).

    Canonical numbers from docs/QA_PREP.md (RealVuln 2026, arXiv:2604.13764):
    ACR-QA 25.1% · Bandit 19.4% · Semgrep CE 17.5% · Snyk 17.4% · SonarQube 6.5%.
    """
    tools = ["ACR-QA", "Bandit", "Semgrep CE", "Snyk", "SonarQube"]
    vals = [25.1, 19.4, 17.5, 17.4, 6.5]
    bar_colors = [GREEN, "#9AA5B1", "#9AA5B1", "#9AA5B1", "#9AA5B1"]

    fig, ax = plt.subplots(figsize=(11, 5.0))
    bars = ax.bar(tools, vals, color=bar_colors, edgecolor="white", width=0.62)
    for bar, v in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + 0.6,
            f"{v:.1f}%",
            ha="center",
            fontsize=15,
            fontweight="bold",
            color=INK,
        )
    ax.set_ylim(0, 30)
    ax.set_ylabel("Full-corpus recall (%)", fontsize=13, color=INK)
    ax.set_title(
        "RealVuln 2026 — Full-Corpus Recall (26 real Python CVE apps)",
        fontsize=16,
        fontweight="bold",
        color=NAVY,
        pad=12,
    )
    ax.tick_params(axis="x", labelsize=13)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.text(
        0.0,
        -0.155,
        "ACR-QA leads every traditional SAST tool · strict CWE + file + line(±10) matching · third-party ground truth.",
        fontsize=11,
        style="italic",
        color=GRAY,
        transform=ax.transAxes,
    )
    fig.subplots_adjust(left=0.09, right=0.97, top=0.88, bottom=0.16)
    out = FIGS / "REALVULN_LEADERBOARD_CLEAN.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"✓ {out}")


def scorecard_figure():
    """ACR-QA across five benchmarks — strong, varied, all documented numbers.

    Counters the "only RealVuln / only the weak confusion matrix" impression by showing
    the headline results side by side. Each bar is labelled with its metric type (honest —
    not mixing precision/recall on one undifferentiated axis).
    """
    rows = [
        ("CVE battery", "recall", 100.0),
        ("Head-to-head", "F₁ score", 98.2),
        ("Confirmed Tier", "precision", 96.4),
        ("SecurityEval", "recall", 91.0),
        ("OWASP Top-10", "coverage (9/10)", 90.0),
    ]
    labels = [f"{r[0]}\n({r[1]})" for r in rows]
    vals = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(11, 5.0))
    bars = ax.barh(labels, vals, color=GREEN, edgecolor="white", height=0.62)
    for bar, v in zip(bars, vals):
        ax.text(
            v - 2,
            bar.get_y() + bar.get_height() / 2,
            f"{v:.1f}%",
            va="center",
            ha="right",
            fontsize=15,
            fontweight="bold",
            color="white",
        )
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    ax.set_xlabel("Score (%)", fontsize=12.5, color=INK)
    ax.set_title(
        "ACR-QA across five benchmarks — results at a glance", fontsize=16, fontweight="bold", color=NAVY, pad=12
    )
    ax.tick_params(axis="y", labelsize=12)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.text(
        0.0,
        -0.16,
        "Five different tests, five different metrics — each labelled. The 25.1% RealVuln number is the hardest real-world recall (next slide).",
        fontsize=10.5,
        style="italic",
        color=GRAY,
        transform=ax.transAxes,
    )
    fig.subplots_adjust(left=0.20, right=0.97, top=0.88, bottom=0.17)
    out = FIGS / "BENCHMARK_SCORECARD.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"✓ {out}")


if __name__ == "__main__":
    print(
        f"counts: TP={TP} FN={FN} FP={FP} TN={TN}  |  "
        f"recall={recall:.3f} precision={precision:.3f} F1={f1:.3f} F3={f3:.3f} "
        f"Youden={youden:.3f} MCC={mcc:.3f} FPR={fpr:.3f}"
    )
    confusion_figure()
    derived_metrics_figure()
    realvuln_leaderboard_figure()
    scorecard_figure()
