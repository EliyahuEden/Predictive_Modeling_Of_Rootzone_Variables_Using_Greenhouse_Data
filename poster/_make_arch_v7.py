# -*- coding: utf-8 -*-
"""Architecture diagram v7 -- IDENTICAL layout/boxes to v6, but the text in EACH
box is auto-scaled up to nearly fill that box (no more empty padding).
Each box is measured with the renderer and its font grown to ~fill the box.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

PAGE="#FCFCF7"; DEEP="#3D4A1F"; OLIVE="#5E6E2E"; OLIVE_DK="#4A5320"
SAGE_FILL="#E7ECD6"; IO_FILL="#FFFFFF"; OUT_FILL="#4F5E26"; ARROW="#6B7C3A"

TITLE=38; RS=2.6; LW=3.4; ALW=3.6
FILLW=0.90; FILLH=0.86; LS=1.02       # fill targets (fraction of box) + line spacing

W_CV,H_CV = 150.0, 86.0
fig=plt.figure(figsize=(15.0,8.6),dpi=200); fig.patch.set_facecolor(PAGE)
ax=fig.add_axes([0,0,1,1]); ax.set_facecolor(PAGE)
ax.set_xlim(0,W_CV); ax.set_ylim(0,H_CV); ax.set_aspect("equal"); ax.axis("off")
fig.canvas.draw()
RND=fig.canvas.get_renderer()
_o=ax.transData.transform((0,0)); _x=ax.transData.transform((1,0)); _y=ax.transData.transform((0,1))
PPDX=_x[0]-_o[0]; PPDY=_y[1]-_o[1]      # pixels per data unit

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

def fit_headsub(x,y,w,h,head,sub,tc):
    cx=x+w/2.0; cy=y+h/2.0
    bh,bs=20.0,14.3                              # head:sub size ratio ~0.71
    th=ax.text(cx,cy,head,ha="center",va="center",fontsize=bh,fontweight="bold",
               color=tc,linespacing=LS,zorder=4)
    ts=ax.text(cx,cy,sub,ha="center",va="center",fontsize=bs,style="italic",
               color=tc,linespacing=LS,zorder=4)
    eh=th.get_window_extent(RND); es=ts.get_window_extent(RND)
    gap_px=0.07*h*PPDY
    combw=max(eh.width,es.width); combh=eh.height+es.height+gap_px
    sc=min(w*PPDX*FILLW/combw, h*PPDY*FILLH/combh)
    th.set_fontsize(bh*sc); ts.set_fontsize(bs*sc)
    eh=th.get_window_extent(RND); es=ts.get_window_extent(RND)
    hh=eh.height/PPDY; sh=es.height/PPDY; gp=gap_px/PPDY
    total=hh+sh+gp; top=cy+total/2.0
    th.set_position((cx,top));            th.set_va("top")
    ts.set_position((cx,top-hh-gp));      ts.set_va("top")

def arrow(x0,y0,x1,y1,scale=26,lw=ALW):
    ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle="-|>",mutation_scale=scale,
        lw=lw,color=ARROW,shrinkA=0,shrinkB=0,zorder=2))
def step_to(xs,ys,xend,yend):
    ax.plot(xs,ys,color=ARROW,lw=ALW,solid_capstyle="round",solid_joinstyle="round",zorder=2)
    arrow(xs[-1],ys[-1],xend,yend)

# ---- geometry (IDENTICAL to v6) ----
MARGIN,GAP=2.0,5.0
WB=(W_CV-2*MARGIN-2*GAP)/3.0
col=[MARGIN+i*(WB+GAP) for i in range(3)]; ccx=[c+WB/2.0 for c in col]
R1Y,BH=58.0,20.0; cy1=R1Y+BH/2.0
S2Y,S2H=30.0,20.0; RZY,RZH=6.0,18.0

# rectangles
rect(col[0],R1Y,WB,BH,IO_FILL,OLIVE_DK); rect(col[1],R1Y,WB,BH,SAGE_FILL,OLIVE); rect(col[2],R1Y,WB,BH,IO_FILL,OLIVE_DK)
rect(col[2],S2Y,WB,S2H,SAGE_FILL,OLIVE); rect(col[2],RZY,WB,RZH,OUT_FILL,OUT_FILL)
rect(col[0],30.0,WB,20.0,IO_FILL,OLIVE_DK); rect(col[0],6.0,WB,20.0,IO_FILL,OLIVE_DK)

# arrows (IDENTICAL to v6)
arrow(col[0]+WB,cy1,col[1],cy1); arrow(col[1]+WB,cy1,col[2],cy1)
arrow(ccx[2],R1Y,ccx[2],S2Y+S2H); arrow(ccx[2],S2Y,ccx[2],RZY+RZH)
arrow(col[0]+WB,44.0,col[2],44.0)
xr=col[1]+WB-1.5
step_to([col[0]+WB,xr,xr],[16.0,16.0,36.0],col[2],36.0)

# text (auto-fit per box)
fit_head(col[0],R1Y,WB,BH,"External\nweather &\nradiation",DEEP)
fit_headsub(col[1],R1Y,WB,BH,"Stage 1\nMicro-climate\nmodel","LightGBM",DEEP)
fit_head(col[2],R1Y,WB,BH,"Internal\ngreenhouse\nclimate",DEEP)
fit_headsub(col[2],S2Y,WB,S2H,"Stage 2\nRoot-zone\nmodel","Gradient Boosting + Huber",DEEP)
fit_head(col[2],RZY,WB,RZH,"Root-zone\npH & EC","white")
fit_head(col[0],30.0,WB,20.0,"Irrigation &\nfertigation",DEEP)
fit_head(col[0],6.0,WB,20.0,"Crop state ·\nlast pH / EC",DEEP)

ax.text(W_CV/2.0,82.0,"Two-stage prediction pipeline",ha="center",va="center",
        fontsize=TITLE,color=DEEP,fontweight="bold",zorder=5)

os.makedirs("poster/_figs",exist_ok=True)
fig.savefig("poster/_figs/architecture_v7.png",dpi=200,facecolor=PAGE)
fig.savefig("poster/Architecture_Diagram_v7.png",dpi=200,facecolor=PAGE)
from PIL import Image
im=Image.open("poster/_figs/architecture_v7.png")
print("saved architecture_v7.png",im.size,"ratio",round(im.size[1]/im.size[0],4))
