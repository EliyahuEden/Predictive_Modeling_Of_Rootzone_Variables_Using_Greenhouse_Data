# -*- coding: utf-8 -*-
"""Regenerate poster figures with larger typography.

The figure sizes, plot areas, bars, colors, points, and data values are kept
consistent with the embedded V4 poster images. Only text sizing is increased.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "poster" / "_figs"
OUT.mkdir(parents=True, exist_ok=True)

PAGE = "#FCFCF7"
DEEP = "#2F3C1C"
OLIVE = "#5B6F2A"
OLIVE_DK = "#4A5D25"
SAGE = "#AEBE9D"
GOLD = "#E2AA2C"
GRID = "#D9DDC7"
PALE = "#F0F1E7"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.titleweight": "bold",
        "axes.labelweight": "bold",
        "axes.edgecolor": OLIVE,
        "axes.labelcolor": DEEP,
        "xtick.color": DEEP,
        "ytick.color": DEEP,
    }
)


def save(fig, name):
    fig.savefig(OUT / name, dpi=100, facecolor=PAGE)
    plt.close(fig)


def make_walk_forward():
    fig = plt.figure(figsize=(12.3, 7.5), dpi=100)
    fig.patch.set_facecolor(PAGE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1230)
    ax.set_ylim(750, 0)
    ax.axis("off")
    ax.set_facecolor(PAGE)

    ax.text(
        58,
        54,
        "Walk-forward validation",
        ha="left",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=DEEP,
    )

    # Walk-forward: each training window grows by exactly one test fold, so a
    # given Test block ends precisely where the next (lower) Train block ends.
    rows = [
        (103, 82, 405, 137),
        (103, 228, 523, 137),
        (103, 374, 641, 137),
        (103, 519, 759, 137),
    ]
    tests = [
        (508, 82, 118, 137),
        (626, 228, 118, 137),
        (744, 374, 118, 137),
        (862, 519, 118, 137),
    ]
    for i, (x, y, w, h) in enumerate(rows, start=1):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0,rounding_size=7",
                linewidth=0,
                facecolor=OLIVE,
            )
        )
        ax.text(
            x + w / 2,
            y + h / 2,
            f"Train {i}",
            ha="center",
            va="center",
            fontsize=36,
            fontweight="bold",
            color="white",
        )
    for x, y, w, h in tests:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0,rounding_size=7",
                linewidth=0,
                facecolor=GOLD,
            )
        )
        ax.text(
            x + w / 2,
            y + h / 2,
            "Test",
            ha="center",
            va="center",
            fontsize=32,
            fontweight="bold",
            color=DEEP,
        )

    legend_x = 770
    ax.add_patch(
        FancyBboxPatch(
            (legend_x, 91),
            64,
            48,
            boxstyle="round,pad=0,rounding_size=6",
            linewidth=0,
            facecolor=OLIVE,
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (legend_x, 157),
            64,
            48,
            boxstyle="round,pad=0,rounding_size=6",
            linewidth=0,
            facecolor=GOLD,
        )
    )
    ax.text(841, 115, "Training window (past)", va="center", fontsize=18, fontweight="bold", color=DEEP)
    ax.text(841, 181, "Prediction target (future)", va="center", fontsize=18, fontweight="bold", color=DEEP)

    ax.add_patch(
        FancyArrowPatch(
            (108, 678),
            (1138, 678),
            arrowstyle="-|>",
            mutation_scale=24,
            linewidth=3.3,
            color=DEEP,
        )
    )
    ax.text(615, 711, "Time →", ha="center", va="center", fontsize=27, fontweight="bold", color=DEEP)
    save(fig, "walk_forward_validation_v2.png")


def make_micro_accuracy():
    data = [
        ("Air temperature", 0.9722779273928853, OLIVE),
        ("Internal radiation", 0.9661048390436027, OLIVE),
        ("ET₀", 0.9730268180369538, OLIVE),
        ("Soil temperature", 0.9209212712107425, OLIVE),
        ("Relative humidity", 0.8606287867079798, SAGE),
    ]

    fig = plt.figure(figsize=(12.3, 7.5), dpi=100)
    fig.patch.set_facecolor(PAGE)
    fig.text(
        0.5,
        0.935,
        "Stage 1 — Microclimate model accuracy",
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=DEEP,
    )
    ax = fig.add_axes([0.32, 0.14, 0.63, 0.75])
    ax.set_facecolor(PAGE)
    labels = [d[0] for d in data]
    values = [d[1] for d in data]
    colors = [d[2] for d in data]
    y = np.arange(len(labels))

    ax.barh(y, [1] * len(y), color=PALE, height=0.62, edgecolor="none", zorder=1)
    ax.barh(y, values, color=colors, height=0.62, edgecolor="none", zorder=2)
    ax.set_xlim(0, 1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=27, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("Walk-forward R²", fontsize=27, fontweight="bold", labelpad=9)
    ax.set_xticks(np.arange(0, 1.01, 0.2))
    ax.tick_params(axis="x", labelsize=24, width=2.0, length=6)
    ax.tick_params(axis="y", width=2.0, length=5)
    ax.grid(axis="x", color=GRID, linewidth=1.6)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["bottom", "left"]:
        ax.spines[spine].set_color(OLIVE)
        ax.spines[spine].set_linewidth(2.2)
    for yi, value in zip(y, values):
        ax.text(
            min(value - 0.025, 0.95),
            yi,
            f"{value:.2f}",
            ha="right",
            va="center",
            fontsize=25,
            fontweight="bold",
            color="white",
        )
    save(fig, "micro_climate_accuracy_v2.png")


def gap_bin(hours):
    if hours <= 2:
        return "0-2 h"
    if hours <= 8:
        return "2-8 h"
    if hours <= 24:
        return "8-24 h"
    return "24 h+"


def make_parity(target):
    if target == "ph":
        path = ROOT / "plots" / "PH& EC_Results_48H_Version" / "MODEL_EXPORTS" / "v8_final_unified_model_48h_no_rh_eval_ph.csv"
        true_col, pred_col = "ph_true", "ph_pred"
        title = "pH — Predicted vs Measured"
        xlabel, ylabel = "Measured pH", "Predicted pH"
        lim = (3.8, 11.15)
        ticks = np.arange(4, 12, 1)
        stat = "R² = 0.93\nMAE = 0.33\nn = 57"
        outfile = "ph_predicted_vs_measured_v2.png"
    else:
        path = ROOT / "plots" / "PH& EC_Results_48H_Version" / "MODEL_EXPORTS" / "v8_final_unified_model_48h_no_rh_eval_ec.csv"
        true_col, pred_col = "ec_true", "ec_pred"
        title = "EC — Predicted vs Measured"
        xlabel, ylabel = "Measured EC (mS/cm)", "Predicted EC (mS/cm)"
        lim = (-0.25, 5.38)
        ticks = np.arange(0, 6, 1)
        stat = "R² = 0.98\nMAE = 0.127 mS/cm\nn = 57"
        outfile = "ec_predicted_vs_measured_v2.png"

    df = pd.read_csv(path)
    df["gap_bin"] = df["gap_hours"].map(gap_bin)
    colors = {
        "0-2 h": OLIVE_DK,
        "2-8 h": "#6F7E3A",
        "8-24 h": SAGE,
        "24 h+": GOLD,
    }

    fig = plt.figure(figsize=(9.6, 9), dpi=100)
    fig.patch.set_facecolor(PAGE)
    ax = fig.add_axes([0.12, 0.13, 0.78, 0.78])
    ax.set_facecolor(PAGE)
    for label in ["0-2 h", "2-8 h", "8-24 h", "24 h+"]:
        sub = df[df["gap_bin"] == label]
        ax.scatter(
            sub[true_col],
            sub[pred_col],
            s=135,
            c=colors[label],
            edgecolors="white",
            linewidths=1.2,
            label=label,
            zorder=3,
        )
    ax.plot(lim, lim, linestyle="--", color="#9EA583", linewidth=2.5, zorder=2)
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.grid(True, color=GRID, linewidth=1.25)
    ax.tick_params(labelsize=22, width=1.8, length=6)
    ax.set_xlabel(xlabel, fontsize=24, fontweight="bold", labelpad=7)
    ax.set_ylabel(ylabel, fontsize=24, fontweight="bold", labelpad=7)
    ax.set_title(title, fontsize=32, fontweight="bold", color=DEEP, pad=18)
    for spine in ax.spines.values():
        spine.set_color(OLIVE)
        spine.set_linewidth(2.2)
    ax.text(
        0.04,
        0.96,
        stat,
        transform=ax.transAxes,
        va="top",
        fontsize=26,
        fontweight="bold",
        color=DEEP,
        linespacing=1.25,
        bbox=dict(boxstyle="round,pad=0.6", fc="#F3F0DC", ec="#7A8A4E", lw=2.2),
    )
    leg = ax.legend(
        title="Forecast gap",
        loc="lower right",
        fontsize=22,
        title_fontsize=24,
        frameon=True,
        facecolor=PAGE,
        edgecolor=GRID,
        markerscale=1.4,
        borderpad=0.9,
        labelspacing=0.65,
        handletextpad=0.9,
    )
    for text in leg.get_texts():
        text.set_color(DEEP)
    leg.get_title().set_color(DEEP)
    save(fig, outfile)


def make_feature_importance():
    path = ROOT / "plots" / "PH& EC_Results_48H_Version" / "MODEL_EXPORTS" / "v8_final_unified_model_48h_no_rh_fi_xgb_by_target.csv"
    fi = pd.read_csv(path, index_col=0)
    fi["mean"] = fi.mean(axis=1)
    top = fi.sort_values("mean", ascending=False).head(10)
    labels = [
        "ET₀ per hour",
        "EC₀ × 48 h salt",
        "Anchor pH (t₀)",
        "Anchor EC (t₀)",
        "Soil temp. (mean)",
        "EC drive (log)",
        "Climate demand × soil",
        "Salt buildup (history)",
        "Climate demand pull",
        "Crop stage × salt conc.",
    ]
    values = top["mean"].to_numpy()
    colors = [GOLD, GOLD, GOLD] + [OLIVE] * 7

    fig = plt.figure(figsize=(12.3, 9), dpi=100)
    fig.patch.set_facecolor(PAGE)
    ax = fig.add_axes([0.39, 0.12, 0.55, 0.78])
    ax.set_facecolor(PAGE)
    y = np.arange(len(labels))
    ax.barh(y, values, color=colors, height=0.70, edgecolor="none")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=26, fontweight="bold")
    for tick in ax.get_yticklabels():
        if len(tick.get_text()) >= 22:
            tick.set_fontsize(24)
    ax.invert_yaxis()
    ax.set_xlim(0, 0.117)
    ax.set_xticks(np.arange(0, 0.12, 0.02))
    ax.tick_params(axis="x", labelsize=24, width=2.0, length=6)
    ax.tick_params(axis="y", width=2.0, length=5)
    ax.set_xlabel("Mean model feature importance", fontsize=27, fontweight="bold", labelpad=8)
    ax.set_title("Most informative features", fontsize=36, fontweight="bold", color=DEEP, pad=17)
    ax.grid(axis="x", color=GRID, linewidth=1.6)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(OLIVE)
        ax.spines[spine].set_linewidth(2.2)
    save(fig, "feature_importance_model.png")


if __name__ == "__main__":
    make_walk_forward()
    make_micro_accuracy()
    make_parity("ph")
    make_parity("ec")
    make_feature_importance()
