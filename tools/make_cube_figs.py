"""3D raster-block figures (dynamic = smooth, static = heterogeneous) for Study 1 slides.
Writes assets/img/cube_dynamic.png and cube_static.png (transparent).
Usage: python3 tools/make_cube_figs.py"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import Polygon

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "img"
th = np.linspace(0, 2 * np.pi, 500)
r = 1 + 0.18 * np.sin(2 * th + .4) + 0.10 * np.cos(3 * th) + 0.06 * np.sin(5 * th + 1) + 0.04 * np.cos(7 * th) + 0.03 * np.sin(11 * th)
bx, by = 0.8 * r * np.cos(th), 1.0 * r * np.sin(th)
basin = MPath(np.c_[bx, by])
n = 120
xs, ys = np.meshgrid(np.linspace(-1.25, 1.25, n), np.linspace(-1.25, 1.25, n))
inside = basin.contains_points(np.c_[xs.ravel(), ys.ravel()]).reshape(xs.shape)

def smooth(seed, k=6):
    g = np.random.default_rng(seed); f = np.zeros_like(xs)
    for _ in range(k):
        c1, c2, s, a = g.uniform(-1, 1), g.uniform(-1, 1), g.uniform(.3, .7), g.uniform(-1, 1)
        f += a * np.exp(-((xs - c1) ** 2 + (ys - c2) ** 2) / (2 * s * s))
    return f

def cube(name, field, cmap):
    fig = plt.figure(figsize=(2.4, 2.8), dpi=250)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 2.4); ax.set_ylim(0, 2.8)
    d = .26                                       # depth
    x0, y0, w = .35, .45, 1.9                     # front face
    ax.add_patch(Polygon([(x0 - d, y0 + d), (x0, y0), (x0, y0 + w), (x0 - d, y0 + w + d)], fc="#8E9A96", ec="#1F2D2A", lw=1.6))
    ax.add_patch(Polygon([(x0 - d, y0 + d), (x0, y0), (x0 + w, y0), (x0 + w - d, y0 + d)], fc="#5F6B67", ec="#1F2D2A", lw=1.6))
    ax.add_patch(Polygon([(x0, y0), (x0 + w, y0), (x0 + w, y0 + w), (x0, y0 + w)], fc="#F7F8F7", ec="none"))
    m = np.ma.masked_where(~inside, field)
    ax.imshow(m, extent=(x0 + .02, x0 + w - .02, y0 + .02, y0 + w - .02), origin="lower", cmap=cmap, interpolation="nearest", zorder=3)
    for t in (.25, .5, .75):                      # dotted grid
        ax.plot([x0 + t * w] * 2, [y0, y0 + w], ls=(0, (1, 2)), color="#1F2D2A", lw=1, zorder=4)
        ax.plot([x0, x0 + w], [y0 + t * w] * 2, ls=(0, (1, 2)), color="#1F2D2A", lw=1, zorder=4)
    ax.add_patch(Polygon([(x0, y0), (x0 + w, y0), (x0 + w, y0 + w), (x0, y0 + w)], fc="none", ec="#1F2D2A", lw=1.8, zorder=5))
    fig.savefig(OUT / name, transparent=True); plt.close(fig); print("wrote", name)

cube("cube_dynamic.png", smooth(3) + .4 * ys, "viridis")
rng = np.random.default_rng(9)
cube("cube_static.png", smooth(5, 5) + .9 * rng.standard_normal(xs.shape), "YlOrBr_r")
