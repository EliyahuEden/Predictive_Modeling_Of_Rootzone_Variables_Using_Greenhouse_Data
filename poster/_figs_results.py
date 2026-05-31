"""Generate the four NEW figures for the Root-zone Model Results card (08):
  walk-forward index-based time series:  wf_ph_index.png, wf_ec_index.png
  holdout parity scatters (poster style): holdout_ph_parity.png, holdout_ec_parity.png
All in the poster palette (#FCFCF7 background, olive/sage/gold), index-based x-axis.
Run:  py -X utf8 poster/_figs_results.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"C:\Users\User\Desktop\Predictive_Modeling_Of_Rootzone_Variables_Using_Greenhouse_Data"
EXP  = os.path.join(ROOT, "scripts", "exports")
OUT  = os.path.join(ROOT, "poster", "_figs")
os.makedirs(OUT, exist_ok=True)

# ---------- palette (matches existing parity plots) ----------
PAGE = "#FCFCF7"   # card background
INK  = "#2E3517"   # measured line / darkest
DEEP = "#3D4A1F"   # titles, labels, ticks
OLIVE= "#5E6E2E"   # spines / borders
GRID = "#D8DEC4"   # gridlines
DIAG = "#9AA17F"   # diagonal reference
PRED = "#C49A2B"   # predicted line (gold)
ERRC = "#6B7C3A"   # faint error connectors
GAP_COLORS = ["#3D4A1F", "#6E7F39", "#AEBE8E", "#E2A92C"]  # 0-2 / 2-8 / 8-24 / 24+ h
GAP_LABELS = ["0-2 h", "2-8 h", "8-24 h", "24 h+"]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.weight": "bold"})


def gap_bin(g):
    if g <= 2:  return 0
    if g <= 8:  return 1
    if g <= 24: return 2
    return 3


def style_axes(ax):
    ax.set_facecolor(PAGE)
    ax.set_axisbelow(True)
    ax.grid(True, color=GRID, alpha=0.7, lw=0.9)
    for s in ax.spines.values():
        s.set_color(OLIVE)
        s.set_linewidth(1.3)
    ax.tick_params(colors=DEEP, labelsize=12)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontweight("bold")


# ---------- walk-forward time series (index-based) ----------
def timeseries(df, tcol, pcol, ylab, title, fname, legloc="upper right"):
    yt = df[tcol].values
    yp = df[pcol].values
    x = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(6.6, 4.5), dpi=200)
    fig.patch.set_facecolor(PAGE)
    style_axes(ax)
    for xi, a, b in zip(x, yt, yp):                      # faint error connectors
        ax.plot([xi, xi], [a, b], color=ERRC, alpha=0.28, lw=1.0, zorder=1)
    ax.plot(x, yt, color=INK, lw=1.7, marker="o", ms=3.4, mfc=INK,
            mec="white", mew=0.5, zorder=3, label="Measured")
    ax.plot(x, yp, color=PRED, lw=1.7, ls="--", marker="o", ms=3.4, mfc=PRED,
            mec="white", mew=0.5, zorder=2, label="Predicted")
    ax.set_xlabel("Measurement index", fontsize=13, color=DEEP, fontweight="bold")
    ax.set_ylabel(ylab, fontsize=13, color=DEEP, fontweight="bold")
    ax.set_title(title, fontsize=15.5, color=DEEP, fontweight="bold", pad=8)
    ax.margins(x=0.02)
    leg = ax.legend(loc=legloc, fontsize=11, frameon=True, framealpha=0.95,
                    handlelength=1.8, borderpad=0.5)
    leg.get_frame().set_edgecolor(OLIVE)
    leg.get_frame().set_facecolor(PAGE)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), facecolor=PAGE)
    plt.close(fig)
    print("saved", fname)


# ---------- holdout parity scatter (matches existing style) ----------
def parity(df, tcol, pcol, lab, title, fname, metric_lines):
    t = df[tcol].values
    p = df[pcol].values
    g = df["gap_h"].values
    fig, ax = plt.subplots(figsize=(5.7, 5.35), dpi=200)
    fig.patch.set_facecolor(PAGE)
    style_axes(ax)
    lo = min(t.min(), p.min())
    hi = max(t.max(), p.max())
    pad = (hi - lo) * 0.09
    lo -= pad; hi += pad
    ax.plot([lo, hi], [lo, hi], ls="--", color=DIAG, lw=1.8, zorder=1)
    for b in range(4):
        m = np.array([gap_bin(gi) == b for gi in g])
        if m.any():
            ax.scatter(t[m], p[m], s=78, c=GAP_COLORS[b], edgecolors="white",
                       linewidths=0.8, zorder=3, label=GAP_LABELS[b])
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_aspect("equal")
    ax.set_xlabel(f"Measured {lab}", fontsize=13, color=DEEP, fontweight="bold")
    ax.set_ylabel(f"Predicted {lab}", fontsize=13, color=DEEP, fontweight="bold")
    ax.set_title(title, fontsize=15.5, color=DEEP, fontweight="bold", pad=8)
    ax.text(0.04, 0.96, metric_lines, transform=ax.transAxes, ha="left", va="top",
            fontsize=14, color=DEEP, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", fc="#F4F1DF", ec=OLIVE, lw=1.6))
    leg = ax.legend(title="Forecast gap", loc="lower right", fontsize=10,
                    title_fontsize=11, frameon=True, framealpha=0.95)
    leg.get_frame().set_edgecolor(OLIVE)
    leg.get_frame().set_facecolor(PAGE)
    plt.setp(leg.get_title(), color=DEEP, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), facecolor=PAGE)
    plt.close(fig)
    print("saved", fname)


ph = pd.read_csv(os.path.join(EXP, "v8_final_unified_model_48h_no_rh_eval_ph.csv"))
ec = pd.read_csv(os.path.join(EXP, "v8_final_unified_model_48h_no_rh_eval_ec.csv"))
ho = pd.read_csv(os.path.join(EXP, "v8_final_unified_model_48h_no_rh_holdout_detail.csv"))

timeseries(ph, "ph_true", "ph_pred", "pH",          "pH — Predicted vs Measured", "wf_ph_index.png")
timeseries(ec, "ec_true", "ec_pred", "EC (mS/cm)",  "EC — Predicted vs Measured", "wf_ec_index.png", legloc="upper left")
parity(ho, "ph_true", "ph_pred", "pH",         "pH — Holdout",  "holdout_ph_parity.png", "R² = 0.93\nMAE = 0.29")
parity(ho, "ec_true", "ec_pred", "EC (mS/cm)", "EC — Holdout",  "holdout_ec_parity.png", "R² = 0.95\nMAE = 0.131 mS/cm")
print("done")
