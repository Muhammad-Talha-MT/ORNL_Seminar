"""Concept figures for the lumped-vs-distributed slide (illustrative, not data).
Writes transparent PNGs to assets/img/: basin_lumped.png, basin_distributed.png,
field_precip.png, field_topo.png, field_landcover.png, field_streams.png.
Usage: python3 tools/make_concept_figs.py"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
ELEV = LinearSegmentedColormap.from_list('elev', ['#6FA35A', '#B9C56B', '#D9B26F', '#A0714B', '#EDEDED'])
from matplotlib.path import Path as MPath

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "img"
rng = np.random.default_rng(11)

# ---- basin outline: a smooth irregular blob, outlet at the bottom ----
th = np.linspace(0, 2 * np.pi, 400)
r = 1 + 0.18 * np.sin(2 * th + .4) + 0.10 * np.cos(3 * th) + 0.06 * np.sin(5 * th + 1) + 0.04 * np.cos(7 * th)
bx, by = 0.82 * r * np.cos(th), 1.0 * r * np.sin(th)
basin = MPath(np.c_[bx, by])

# ---- dendritic stream network grown from the outlet ----
segs = []
def grow(x, y, ang, L, depth):
    if depth == 0 or L < .05:
        return
    nx, ny = x + L * np.cos(ang), y + L * np.sin(ang)
    if not basin.contains_point((nx, ny)):
        return
    segs.append(((x, y), (nx, ny), depth))
    for s in (-1, 1):
        if rng.random() < .96:
            grow(nx, ny, ang + s * rng.uniform(.3, .6), L * rng.uniform(.66, .82), depth - 1)
k = int(np.argmin(by)); ox, oy = bx[k], by[k] + .03
grow(ox, oy, np.pi / 2, .36, 8)

def draw_streams(ax, color="#2E7FC1", scale=1.0):
    for (x0, y0), (x1, y1), d in segs:
        ax.plot([x0, x1], [y0, y1], color=color, lw=scale * (.5 + .45 * d), solid_capstyle="round")

def new_ax(w=4, h=4.6):
    fig = plt.figure(figsize=(w, h), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(bx.min() - .08, bx.max() + .08); ax.set_ylim(by.min() - .08, by.max() + .08)
    return fig, ax

def save(fig, name):
    fig.savefig(OUT / name, transparent=True); plt.close(fig); print("wrote", name)

# ---- smooth random fields on a grid, masked to the basin ----
n = 22
gx, gy = np.meshgrid(np.linspace(bx.min(), bx.max(), n), np.linspace(by.min(), by.max(), n))
inside = basin.contains_points(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape)
def smooth_field(k=6, seed=0):
    g = np.random.default_rng(seed)
    f = np.zeros_like(gx)
    for _ in range(k):
        cx, cy, s, a = g.uniform(bx.min(), bx.max()), g.uniform(by.min(), by.max()), g.uniform(.25, .6), g.uniform(-1, 1)
        f += a * np.exp(-((gx - cx) ** 2 + (gy - cy) ** 2) / (2 * s * s))
    return f
precip = smooth_field(7, 3) + .8 * (gy - gy.min())           # wetter toward the headwaters
topo = smooth_field(6, 5) + 1.6 * (gy - gy.min())             # higher upstream
lc = np.digitize(smooth_field(9, 8), np.quantile(smooth_field(9, 8)[inside], [.3, .55, .8, .93]))

def raster(ax, field, cmap, vmin=None, vmax=None, grid=True):
    m = np.ma.masked_where(~inside, field)
    ax.pcolormesh(gx, gy, m, cmap=cmap, vmin=vmin, vmax=vmax, shading="nearest",
                  edgecolors="#ffffff" if grid else "none", linewidth=.35 if grid else 0)
    ax.plot(bx, by, color="#1F2D2A", lw=1.4)

# lumped: outline + streams on white
fig, ax = new_ax()
ax.fill(bx, by, color="#ffffff"); ax.plot(bx, by, color="#1F2D2A", lw=1.8)
draw_streams(ax)
save(fig, "basin_lumped.png")

# distributed: topography raster + grid + streams
fig, ax = new_ax()
raster(ax, topo, ELEV)
draw_streams(ax, "#1E5FA8", .9)
save(fig, "basin_distributed.png")

# small panels
fig, ax = new_ax(2.2, 2.5); raster(ax, precip, "Blues"); save(fig, "field_precip.png")
fig, ax = new_ax(2.2, 2.5); raster(ax, topo, ELEV); save(fig, "field_topo.png")
lc_cmap = ListedColormap(["#2E7D32", "#9CCC65", "#E6C35C", "#B0413E", "#3F7FBF"])
fig, ax = new_ax(2.2, 2.5); raster(ax, lc, lc_cmap, 0, 4); save(fig, "field_landcover.png")
fig, ax = new_ax(2.2, 2.5); ax.fill(bx, by, color="#ffffff"); ax.plot(bx, by, color="#1F2D2A", lw=1.2); draw_streams(ax, "#2E7FC1", .7)
save(fig, "field_streams.png")
