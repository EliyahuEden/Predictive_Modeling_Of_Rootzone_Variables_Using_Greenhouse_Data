"""Two-stage architecture diagram for the rootzone poster (BIG-TEXT version).
One full-width horizontal main pipeline (5 equal, aligned boxes); the two secondary
inputs sit directly below Stage 2 and feed it with short straight UPWARD arrows.
Text is large and box labels are wrapped to short lines so nothing overflows.
Input boxes = white + green border; model boxes = light green; output box = darker.
Canvas ratio ~0.387 fills the Method-card slot.  Run:  py -X utf8 poster/_make_architecture.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

PAGE      = "#FCFCF7"   # card background -> seamless blend
DEEP      = "#3D4A1F"   # deep green (titles / text)
OLIVE     = "#5E6E2E"   # model-box border
OLIVE_DK  = "#4A5320"   # input-box border
SAGE_FILL = "#E7ECD6"   # light green for model boxes
IO_FILL   = "#FFFFFF"   # input / intermediate boxes (white)
OUT_FILL  = "#4F5E26"   # final output box (darker, white text)
ARROW     = "#6B7C3A"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.weight": "bold"})

HFS, SFS, TFS = 19, 15, 26     # heading / sub-label / title font sizes (much bigger)

fig = plt.figure(figsize=(15.0, 5.8), dpi=200)   # ratio 0.3867 -> fills card slot
ax = fig.add_axes([0, 0, 1, 1])
fig.patch.set_facecolor(PAGE)
ax.set_facecolor(PAGE)
ax.set_xlim(0, 150)
ax.set_ylim(0, 58)
ax.set_aspect("equal")
ax.axis("off")

RS = 2.2  # corner rounding


def box(x, y, w, h, head, sub, fc, ec, tc, fs=HFS, subfs=SFS, lw=3.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle=f"round,pad=0,rounding_size={RS}",
                 linewidth=lw, edgecolor=ec, facecolor=fc,
                 mutation_aspect=1.0, zorder=3))
    cx = x + w / 2.0
    if sub:                                   # heading anchored to top, sub to bottom
        ax.text(cx, y + h - h * 0.15, head, ha="center", va="top",
                fontsize=fs, color=tc, linespacing=1.04, zorder=4)
        ax.text(cx, y + h * 0.15, sub, ha="center", va="bottom",
                fontsize=subfs, color=tc, style="italic", linespacing=1.04, zorder=4)
    else:
        ax.text(cx, y + h / 2.0, head, ha="center", va="center",
                fontsize=fs, color=tc, linespacing=1.04, zorder=4)


def harrow(x0, x1, y, ms=26, lw=3.4):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>",
                 mutation_scale=ms, linewidth=lw, color=ARROW, zorder=2))


def varrow(x, y0, y1, ms=24, lw=3.2):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>",
                 mutation_scale=ms, linewidth=lw, color=ARROW, zorder=2))


# ---------- main pipeline: 5 equal boxes, equal gaps, one horizontal line ----------
M, WG = 2.0, 4.5
WB = (150 - 2 * M - 4 * WG) / 5.0     # 25.6
MY, MH = 30.0, 21.0                   # main-row bottom, height (taller -> room for big text)
xs = [M + i * (WB + WG) for i in range(5)]

box(xs[0], MY, WB, MH, "External\nweather\n& radiation", None, IO_FILL, OLIVE_DK, DEEP)
box(xs[1], MY, WB, MH, "Stage 1\nMicro-climate\nmodel", "LightGBM", SAGE_FILL, OLIVE, DEEP)
box(xs[2], MY, WB, MH, "Internal\ngreenhouse\nclimate", None, IO_FILL, OLIVE_DK, DEEP)
box(xs[3], MY, WB, MH, "Stage 2\nRoot-zone\nmodel", "Gradient Boosting\n+ Huber", SAGE_FILL, OLIVE, DEEP)
box(xs[4], MY, WB, MH, "Root-zone\npH & EC", None, OUT_FILL, OUT_FILL, "#FFFFFF")

cy = MY + MH / 2.0
for i in range(4):
    harrow(xs[i] + WB, xs[i + 1], cy)

# ---------- secondary inputs: SAME SIZE as main boxes, directly below Stage 2 ----------
s2x = xs[3]
s2c = s2x + WB / 2.0
SW, SH = WB, MH
gap = WG
SY = MY - 6.0 - SH                    # 6-unit arrow gap below the main row
sa_x = s2c - gap / 2.0 - SW
sb_x = s2c + gap / 2.0
box(sa_x, SY, SW, SH, "Irrigation &\nfertigation", None, IO_FILL, OLIVE_DK, DEEP)
box(sb_x, SY, SW, SH, "Crop state ·\nlast pH / EC", None, IO_FILL, OLIVE_DK, DEEP)
la_x = (s2x + (sa_x + SW)) / 2.0
ra_x = (sb_x + (s2x + WB)) / 2.0
varrow(la_x, SY + SH, MY)
varrow(ra_x, SY + SH, MY)

# ---------- title ----------
ax.text(75, 54.6, "Two-stage prediction pipeline",
        ha="center", va="center", fontsize=TFS, color=DEEP)

fig.savefig(r"poster/_figs/architecture.png", facecolor=PAGE)
print("saved poster/_figs/architecture.png")
