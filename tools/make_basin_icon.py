"""Clean basin icon (dark-green wavy outline, light-blue stream network) for the descriptor slide.
Writes assets/img/basin_icon.png (transparent, 300 dpi). Usage: python3 tools/make_basin_icon.py"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "img"
th = np.linspace(0, 2 * np.pi, 1200)
r = 1 + .10 * np.sin(2 * th + .2) + .07 * np.cos(3 * th + .5) + .03 * np.sin(13 * th) + .015 * np.sin(23 * th + 1.3)
x, y = 1.05 * r * np.cos(th), .88 * r * np.sin(th)
def pl(*pts): return np.array(pts, float)
streams = [  # (polyline, lw)
 (pl((-.78,-.52),(-.5,-.3),(-.25,-.08),(0,.08),(.22,.2),(.45,.3),(.62,.36)), 3.6),
 (pl((-.5,-.3),(-.58,-.05),(-.62,.2),(-.55,.42)), 2.2),
 (pl((-.25,-.08),(-.28,.18),(-.2,.42),(-.12,.6)), 2.4),
 (pl((-.2,.3),(-.35,.4),(-.45,.55)), 1.6),
 (pl((0,.08),(.08,-.12),(.28,-.2),(.45,-.2)), 2.0),
 (pl((.22,.2),(.3,.42),(.42,.58)), 1.8),
 (pl((.1,.3),(0.0,.45),(.02,.62)), 1.5),
 (pl((.45,.3),(.58,.18),(.72,.12)), 1.6),
 (pl((.36,-.2),(.45,-.36),(.58,-.42)), 1.4),
 (pl((-.12,.6),(-.2,.7)), 1.2), (pl((-.12,.6),(0,.72)), 1.2),
 (pl((.62,.36),(.7,.46)), 1.2), (pl((.62,.36),(.78,.34)), 1.2),
]
fig = plt.figure(figsize=(3.3, 2.9), dpi=300)
ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_aspect("equal")
ax.set_xlim(x.min() - .06, x.max() + .06); ax.set_ylim(y.min() - .06, y.max() + .06)
ax.fill(x, y, color="#ffffff")
for p, lw in streams:
    ax.plot(p[:, 0], p[:, 1], color="#3FA0E8", lw=lw * 2.2, solid_capstyle="round", solid_joinstyle="round")
ax.plot(x, y, color="#12402F", lw=7.5, solid_joinstyle="round")
fig.savefig(OUT / "basin_icon.png", transparent=True); print("ok")
