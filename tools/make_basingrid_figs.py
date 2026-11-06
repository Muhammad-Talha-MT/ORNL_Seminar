"""Illustrative figures for the BASINGRID and Basin2Vec slides (concept art, not data).
Writes transparent PNGs to assets/img/bg_*.png.
Usage: python3 tools/make_basingrid_figs.py"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.path import Path as MPath
from matplotlib.transforms import Affine2D

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "img"
ELEV = LinearSegmentedColormap.from_list("elev", ["#6FA35A", "#B9C56B", "#D9B26F", "#A0714B", "#EDEDED"])
LC = ListedColormap(["#2E7D32", "#9CCC65", "#E6C35C", "#B0413E", "#3F7FBF"])

# basin outline (same family as make_concept_figs)
th = np.linspace(0, 2 * np.pi, 600)
r = 1 + 0.18 * np.sin(2 * th + .4) + 0.10 * np.cos(3 * th) + 0.06 * np.sin(5 * th + 1) + 0.04 * np.cos(7 * th) + 0.025 * np.sin(13 * th)
bx, by = 0.82 * r * np.cos(th), 1.0 * r * np.sin(th)
basin = MPath(np.c_[bx, by])
X0, X1, Y0, Y1 = bx.min() - .12, bx.max() + .12, by.min() - .12, by.max() + .12
S = max(X1 - X0, Y1 - Y0); cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
X0, X1, Y0, Y1 = cx - S / 2, cx + S / 2, cy - S / 2, cy + S / 2   # square window

def field(n, k, seed, trend=0.0):
    g = np.random.default_rng(seed)
    xs, ys = np.meshgrid(np.linspace(X0, X1, n), np.linspace(Y0, Y1, n))
    f = np.zeros_like(xs)
    for _ in range(k):
        c1, c2, s, a = g.uniform(X0, X1), g.uniform(Y0, Y1), g.uniform(.25, .6), g.uniform(-1, 1)
        f += a * np.exp(-((xs - c1) ** 2 + (ys - c2) ** 2) / (2 * s * s))
    return xs, ys, f + trend * (ys - Y0)

def inside(xs, ys):
    return basin.contains_points(np.c_[xs.ravel(), ys.ravel()]).reshape(xs.shape)

def fig(w=3, h=3):
    f = plt.figure(figsize=(w, h), dpi=220)
    ax = f.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_aspect("equal")
    ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1)
    return f, ax

def save(f, name):
    f.savefig(OUT / name, transparent=True); plt.close(f); print("wrote", name)

def grid_lines(ax, n, color="#ffffff", lw=.5, rot=0):
    t = Affine2D().rotate_deg_around(cx, cy, rot) + ax.transData
    for v in np.linspace(X0 - S, X1 + S, int(n * 3) + 1):
        ax.plot([v, v], [Y0 - S, Y1 + S], color=color, lw=lw, transform=t)
    for v in np.linspace(Y0 - S, Y1 + S, int(n * 3) + 1):
        ax.plot([X0 - S, X1 + S], [v, v], color=color, lw=lw, transform=t)

def frame(ax, color="#1F2D2A", lw=1.6):
    ax.plot([X0, X1, X1, X0, X0], [Y0, Y0, Y1, Y1, Y0], color=color, lw=lw)

# ---------- precipitation, native (fine) and 64x64 ----------
_, _, P_hi = field(256, 7, 3, .9)
_, _, LC_raw = field(256, 9, 8)
LC_hi = np.digitize(LC_raw, np.quantile(LC_raw, [.3, .55, .8, .93]))
_, _, T_hi = field(256, 6, 5, 1.6)

def coarsen(a, n, mode="mean"):
    k = a.shape[0] // n
    b = a[:n * k, :n * k].reshape(n, k, n, k)
    if mode == "mean":
        return b.mean(axis=(1, 3))
    out = np.zeros((n, n), int)
    for i in range(n):
        for j in range(n):
            out[i, j] = np.bincount(b[i, :, j, :].ravel().astype(int), minlength=5).argmax()
    return out

def show(ax, a, cmap, vmin=None, vmax=None, mask=True):
    n = a.shape[0]
    xs, ys = np.meshgrid(np.linspace(X0, X1, n), np.linspace(Y0, Y1, n))
    m = np.ma.masked_where(~inside(xs, ys), a) if mask else a
    ax.imshow(m, extent=(X0, X1, Y0, Y1), origin="lower", cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")

for name, arr, cmap, mode, vr in [("precip", P_hi, "Blues", "mean", (P_hi.min(), P_hi.max())),
                                   ("landcover", LC_hi, LC, "mode", (0, 4)),
                                   ("topo", T_hi, ELEV, "mean", (T_hi.min(), T_hi.max()))]:
    # "64" panel is drawn at 32 cells so the pixelation reads at slide size
    for tag, a in (("native", arr), ("64", coarsen(arr, 32, mode))):
        f, ax = fig()
        show(ax, a, cmap, *vr)
        ax.plot(bx, by, color="#1F2D2A", lw=1.4)
        save(f, f"bg_{name}_{tag}.png")

# ---------- vector basin and binary mask ----------
f, ax = fig()
ax.fill(bx, by, color="#4E8F5A", alpha=.85); ax.plot(bx, by, color="#1F2D2A", lw=1.8)
save(f, "bg_basin_vector.png")
n = 32
xs, ys = np.meshgrid(np.linspace(X0, X1, n), np.linspace(Y0, Y1, n))
M = inside(xs, ys).astype(float)
f, ax = fig()
ax.imshow(M, extent=(X0, X1, Y0, Y1), origin="lower", cmap="gray", vmin=0, vmax=1, interpolation="nearest")
frame(ax)
save(f, "bg_mask.png")

# ---------- heterogeneous source grids (different CRS / resolution) ----------
for name, arr, cmap, gn, rot in [("src_precip", coarsen(P_hi, 16), "Blues", 16, 12),
                                 ("src_landcover", LC_hi, LC, 48, 0),
                                 ("src_topo", coarsen(T_hi, 64), ELEV, 28, -8)]:
    f, ax = fig()
    t = Affine2D().rotate_deg_around(cx, cy, rot) + ax.transData
    im = ax.imshow(arr, extent=(X0, X1, Y0, Y1), origin="lower", cmap=cmap, interpolation="nearest",
                   vmin=(0 if name == "src_landcover" else None), vmax=(4 if name == "src_landcover" else None))
    im.set_transform(t)
    grid_lines(ax, gn / 3, "#ffffff", .35, rot)
    ax.set_xlim(X0 - .25, X1 + .25); ax.set_ylim(Y0 - .25, Y1 + .25)
    save(f, f"bg_{name}.png")

# ---------- common grid: same three, aligned on one grid ----------
f, ax = fig()
show(ax, coarsen(P_hi, 16), "Blues", mask=False)
for v in np.linspace(X0, X1, 17):
    ax.plot([v, v], [Y0, Y1], color="#ffffff", lw=.6)
for v in np.linspace(Y0, Y1, 17):
    ax.plot([X0, X1], [v, v], color="#ffffff", lw=.6)
frame(ax)
save(f, "bg_common_grid.png")

# ---------- window over basin (unmasked) ----------
f, ax = fig()
show(ax, coarsen(T_hi, 32), ELEV, mask=False)
ax.plot(bx, by, color="#1F2D2A", lw=1.6); frame(ax, "#C0392B", 2.4)
save(f, "bg_window.png")
f, ax = fig()
show(ax, coarsen(T_hi, 32), ELEV)
ax.plot(bx, by, color="#1F2D2A", lw=1.4); frame(ax, "#8A9590", 1.2)
save(f, "bg_tensor.png")
