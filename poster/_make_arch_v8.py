# -*- coding: utf-8 -*-
"""Architecture diagram v8 -- SAME single-row layout & box sizes as
_make_architecture.py, but: (1) algorithm sub-labels removed (no LightGBM /
Gradient Boosting + Huber), (2) each box's text auto-scaled up to nearly fill
its box. Nothing else changes.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

PAGE="#FCFCF7"; DEEP="#3D4A1F"; OLIVE="#5E6E2E"; OLIVE_DK="#4A5320"
SAGE_FILL="#E7ECD6"; IO_FILL="#FFFFFF"; OUT_FILL="#4F5E26"; ARROW="#6B7C3A"

TFS=31; RS=2.2; LW=3.2
FILLW=0.90; FILLH=0.88; LS=1.03

fig=plt.figure(figsize=(15.0,5.8),dpi=200); fig.patch.set_facecolor(PAGE)
ax=fig.add_axes([0,0,1,1]); ax.set_facecolor(PAGE)
ax.set_xlim(0,150); ax.set_ylim(0,58); ax.set_aspect("equal"); ax.axis("off")
fig.canvas.draw()
RND=fig.canvas.get_renderer()
_o=ax.transData.transform((0,0)); _x=ax.transData.transform((1,0)); _y=ax.transData.transform((0,1))
PPDX=_x[0]-_o[0]; PPDY=_y[1]-_o[1]

def rect(x,y,w,h,fc,ec,lw=LW):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={RS}",
        linewidth=lw,edgecolor=ec,facecolor=fc,mutation_aspect=1.0,zorder=3))

def fit_head(x,y,w,h,text,tc):
    cx,cy=x+w/2.0,y+h/2.0
    t=ax.text(cx,cy,text,ha="center",va="center",fontsize=20,fontweight="bold",
              color=tc,linespacing=LS,zorder=4)
    e=t.get_window_extent(RND)
    sc=min(w*PPDX*FILLW/e.width, h*PPDY*FILLH/e.height)
    t.set_fontsize(20*sc)

def harrow(x0,x1,y):
    ax.add_patch(FancyArrowPatch((x0,y),(x1,y),arrowstyle="-|>",mutation_scale=26,
        lw=3.4,color=ARROW,shrinkA=0,shrinkB=0,zorder=2))
def varrow(x0,y0,x1,y1):
    ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle="-|>",mutation_scale=26,
        lw=3.4,color=ARROW,shrinkA=0,shrinkB=0,zorder=2))

# ---- geometry (IDENTICAL to _make_architecture.py) ----
MARGIN=1.2; GAP=2.8
WB=(150-2*MARGIN-4*GAP)/5.0      # 27.28
MY=30.0; MH=21.0; SY=2.0
xs=[MARGIN+i*(WB+GAP) for i in range(5)]
cy=MY+MH/2.0

mains=[
    ("External\nweather &\nradiation", IO_FILL, OLIVE_DK, DEEP),
    ("Stage 1\nMicro-climate\nmodel",    SAGE_FILL, OLIVE,    DEEP),
    ("Internal\ngreenhouse\nclimate",    IO_FILL, OLIVE_DK, DEEP),
    ("Stage 2\nRoot-zone\nmodel",        SAGE_FILL, OLIVE,    DEEP),
    ("Root-zone\npH & EC",               OUT_FILL, OUT_FILL, "white"),
]
for i,(txt,fc,ec,tc) in enumerate(mains):
    rect(xs[i],MY,WB,MH,fc,ec)
for i in range(4):
    harrow(xs[i]+WB+0.15, xs[i+1]-0.15, cy)

# support inputs below Stage 2
s2c=xs[3]+WB/2.0; SW=WB; SH=MH
sa_x=s2c-GAP/2.0-SW; sb_x=s2c+GAP/2.0
rect(sa_x,SY,SW,SH,IO_FILL,OLIVE_DK); rect(sb_x,SY,SW,SH,IO_FILL,OLIVE_DK)
varrow(sa_x+SW/2.0, SY+SH+0.15, xs[3]+WB*0.34, MY-0.15)
varrow(sb_x+SW/2.0, SY+SH+0.15, xs[3]+WB*0.66, MY-0.15)

# text (auto-fit)
for i,(txt,fc,ec,tc) in enumerate(mains):
    fit_head(xs[i],MY,WB,MH,txt,tc)
fit_head(sa_x,SY,SW,SH,"Irrigation &\nfertigation",DEEP)
fit_head(sb_x,SY,SW,SH,"Crop state ·\nlast pH / EC",DEEP)

ax.text(75,54.8,"Two-stage prediction pipeline",ha="center",va="center",
        fontsize=TFS,color=DEEP,fontweight="bold",zorder=5)

os.makedirs("poster/_figs",exist_ok=True)
fig.savefig("poster/_figs/architecture_v8.png",dpi=200,facecolor=PAGE)
fig.savefig("poster/Architecture_Diagram_v8.png",dpi=200,facecolor=PAGE)
from PIL import Image
im=Image.open("poster/_figs/architecture_v8.png")
print("saved architecture_v8.png",im.size,"ratio",round(im.size[1]/im.size[0],4))
