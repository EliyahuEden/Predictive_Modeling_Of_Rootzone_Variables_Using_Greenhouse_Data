# -*- coding: utf-8 -*-
"""Two-stage prediction pipeline diagram for the poster Method card.
Wide-short banner (ratio ~0.3866) to drop into the arch slot W=32.05 H=12.39 cm.
Goal this revision: MUCH bigger, readable in-box text -> wide boxes, minimal
internal padding (text fills the box), fonts pushed to the width cap, bold heads,
big bold title. Single-row 5-box pipeline + 2 support inputs feeding Stage 2.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ----- palette (poster olive/sage/gold) -----
PAGE      = "#FCFCF7"
DEEP      = "#3D4A1F"
OLIVE     = "#5E6E2E"
OLIVE_DK  = "#4A5320"
SAGE_FILL = "#E7ECD6"
IO_FILL   = "#FFFFFF"
OUT_FILL  = "#4F5E26"
ARROW     = "#6B7C3A"

TFS = 31    # title
RS  = 2.2   # corner rounding
LW  = 3.2   # box border
FILLW = 0.92 # target fraction of each box width occupied by text
FILLH = 0.88 # target fraction of each box height occupied by text
LS = 1.02    # line spacing

fig = plt.figure(figsize=(15.0, 5.8), dpi=200)
fig.patch.set_facecolor(PAGE)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor(PAGE)
ax.set_xlim(0, 150)
ax.set_ylim(0, 58)
ax.set_aspect("equal")
ax.axis("off")

fig.canvas.draw()
RENDERER = fig.canvas.get_renderer()
_origin = ax.transData.transform((0, 0))
_one_x = ax.transData.transform((1, 0))
_one_y = ax.transData.transform((0, 1))
PPDX = _one_x[0] - _origin[0]
PPDY = _one_y[1] - _origin[1]


def box(x, y, w, h, head, sub, fc, ec, tc, lw=LW):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={RS}",
        linewidth=lw, edgecolor=ec, facecolor=fc,
        mutation_aspect=1.0, zorder=3))
    cx = x + w / 2.0
    cy = y + h / 2.0
    if sub:
        head_base = 20.0
        sub_base = 15.5
        head_text = ax.text(cx, cy, head, ha="center", va="center",
                            fontsize=head_base, color=tc, fontweight="bold",
                            linespacing=LS, zorder=4)
        sub_text = ax.text(cx, cy, sub, ha="center", va="center",
                           fontsize=sub_base, color=tc, style="italic",
                           fontweight="bold", linespacing=LS, zorder=4)

        head_extent = head_text.get_window_extent(RENDERER)
        sub_extent = sub_text.get_window_extent(RENDERER)
        gap_px = 0.055 * h * PPDY
        combined_w = max(head_extent.width, sub_extent.width)
        combined_h = head_extent.height + sub_extent.height + gap_px
        scale = min(w * PPDX * FILLW / combined_w,
                    h * PPDY * FILLH / combined_h)

        head_text.set_fontsize(head_base * scale)
        sub_text.set_fontsize(sub_base * scale)
        head_extent = head_text.get_window_extent(RENDERER)
        sub_extent = sub_text.get_window_extent(RENDERER)
        head_h = head_extent.height / PPDY
        sub_h = sub_extent.height / PPDY
        gap = gap_px / PPDY
        total_h = head_h + sub_h + gap
        top = cy + total_h / 2.0
        head_text.set_position((cx, top))
        head_text.set_va("top")
        sub_text.set_position((cx, top - head_h - gap))
        sub_text.set_va("top")
    else:
        text = ax.text(cx, cy, head, ha="center", va="center",
                       fontsize=20.0, color=tc, fontweight="bold",
                       linespacing=LS, zorder=4)
        extent = text.get_window_extent(RENDERER)
        scale = min(w * PPDX * FILLW / extent.width,
                    h * PPDY * FILLH / extent.height)
        text.set_fontsize(20.0 * scale)


def harrow(x0, x1, y):
    ax.add_patch(FancyArrowPatch(
        (x0, y), (x1, y), arrowstyle="-|>", mutation_scale=26,
        lw=3.4, color=ARROW, shrinkA=0, shrinkB=0, zorder=2))


def varrow(x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=26,
        lw=3.4, color=ARROW, shrinkA=0, shrinkB=0, zorder=2))


# ----- geometry -----
MARGIN = 1.2
GAP    = 2.8
WB     = (150 - 2 * MARGIN - 4 * GAP) / 5.0     # 27.28
MY     = 30.0          # main row bottom
MH     = 21.0          # main/support box height
SY     = 2.0           # support row bottom
xs = [MARGIN + i * (WB + GAP) for i in range(5)]
cy = MY + MH / 2.0

# main pipeline boxes (short wrapped lines so the font can be large)
box(xs[0], MY, WB, MH, "External\nweather &\nradiation", None,
    IO_FILL, OLIVE_DK, DEEP)
box(xs[1], MY, WB, MH, "Stage 1\nMicroclimate\nmodel", "LightGBM",
    SAGE_FILL, OLIVE, DEEP)
box(xs[2], MY, WB, MH, "Internal\ngreenhouse\nclimate", None,
    IO_FILL, OLIVE_DK, DEEP)
box(xs[3], MY, WB, MH, "Stage 2\nRoot-zone\nmodel", "XGBoost + Huber",
    SAGE_FILL, OLIVE, DEEP)
box(xs[4], MY, WB, MH, "Root-zone\npH & EC", None,
    OUT_FILL, OUT_FILL, "white")

# horizontal arrows between main boxes
for i in range(4):
    harrow(xs[i] + WB + 0.15, xs[i + 1] - 0.15, cy)

# support inputs below Stage 2
s2c = xs[3] + WB / 2.0
SW = WB
SH = MH
sa_x = s2c - GAP / 2.0 - SW
sb_x = s2c + GAP / 2.0
box(sa_x, SY, SW, SH, "Irrigation &\nfertigation", None,
    IO_FILL, OLIVE_DK, DEEP)
box(sb_x, SY, SW, SH, "Crop state +\nlast pH / EC", None,
    IO_FILL, OLIVE_DK, DEEP)

# upward arrows into Stage 2 bottom (slight inward angle, like reference)
varrow(sa_x + SW / 2.0, SY + SH + 0.15, xs[3] + WB * 0.34, MY - 0.15)
varrow(sb_x + SW / 2.0, SY + SH + 0.15, xs[3] + WB * 0.66, MY - 0.15)

# title
ax.text(75, 54.8, "Two-stage prediction pipeline", ha="center", va="center",
        fontsize=TFS, color=DEEP, fontweight="bold", zorder=5)

import os
os.makedirs("poster/_figs", exist_ok=True)
fig.savefig("poster/_figs/architecture_xgboost.png", dpi=200, facecolor=PAGE)
fig.savefig("poster/Architecture_Diagram_xgboost.png", dpi=200, facecolor=PAGE)
from PIL import Image
im = Image.open("poster/_figs/architecture_xgboost.png")
print("saved architecture_xgboost.png", im.size, "ratio", round(im.size[1] / im.size[0], 4))
