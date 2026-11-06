"""Realistic-looking synthetic basin (illustrative, not data) for the Study 4 problem slide.
Terrain = fractal noise inside an irregular basin outline; depressions are filled toward a single
outlet, D8 flow directions and flow accumulation give a dendritic river network.
Writes assets/img/basin_network.png and prints marker coordinates (image pixels) as JSON.
Usage: python3 tools/make_basin_network.py"""
import heapq, json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, LightSource
from matplotlib.path import Path as MPath

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "img"
N = 320
rng = np.random.default_rng(7)

def fractal(beta, seed):
    g = np.random.default_rng(seed)
    f = np.fft.fftfreq(N)[:, None] ** 2 + np.fft.fftfreq(N)[None, :] ** 2
    f[0, 0] = 1
    spec = (g.standard_normal((N, N)) + 1j * g.standard_normal((N, N))) / f ** (beta / 2)
    z = np.real(np.fft.ifft2(spec)); return (z - z.mean()) / z.std()

# basin outline: irregular blob, outlet at the bottom middle
th = np.linspace(0, 2 * np.pi, 800, endpoint=False)
r = 1 + .06 * np.cos(2 * th) + .05 * np.cos(3 * th + 1.2) + .05 * np.sin(5 * th + 2) + .02 * np.sin(11 * th) + .012 * np.sin(23 * th + 1)
r *= 1 - .22 * np.exp(-((th - 3 * np.pi / 2) ** 2) / .5)
r *= 1 + .10 * np.exp(-((th - 3 * np.pi / 2) ** 2) / .03)     # spout at the outlet
cx, cy, R = N / 2, N * .47, N * .44
bx, by = cx + R * r * np.cos(th), cy - R * r * np.sin(th)
yy, xx = np.mgrid[0:N, 0:N]
mask = MPath(np.c_[bx, by]).contains_points(np.c_[xx.ravel() + .5, yy.ravel() + .5]).reshape(N, N)
k0 = int(np.argmin(np.abs(th - 3 * np.pi / 2))); oy, ox = int(by[k0]) - 2, int(bx[k0])
while not mask[oy, ox]: oy -= 1

dist = np.hypot(xx - ox, yy - oy) / N
P = np.c_[xx.ravel() + .5, yy.ravel() + .5]; edge = np.full(len(P), 1e9)
for k in range(0, len(bx), 50):
    d = np.hypot(P[:, :1] - bx[None, k:k + 50], P[:, 1:] - by[None, k:k + 50]).min(1); edge = np.minimum(edge, d)
edge = (edge / N).reshape(N, N)
ridge = np.exp(-edge / .035) * (np.hypot(xx - ox, yy - oy) > N * .06)
z = .55 * fractal(2.4, 3) + .22 * fractal(1.9, 5) + .06 * fractal(1.2, 9) + 6.0 * dist ** .8 + 1.4 * ridge

# priority-flood from the outlet (epsilon fill) -> every basin cell drains to the outlet
nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
filled = np.full((N, N), np.inf); rec = -np.ones((N, N, 2), int)
filled[oy, ox] = z[oy, ox]; pq = [(z[oy, ox], oy, ox)]; seen = np.zeros((N, N), bool); seen[oy, ox] = True
order = []
while pq:
    h, i, j = heapq.heappop(pq); order.append((i, j))
    for di, dj in nb:
        a, b = i + di, j + dj
        if 0 <= a < N and 0 <= b < N and mask[a, b] and not seen[a, b]:
            seen[a, b] = True
            filled[a, b] = max(z[a, b], h + 1e-4)
            rec[a, b] = (i, j)
            heapq.heappush(pq, (filled[a, b], a, b))
acc = np.zeros((N, N))
acc[mask] = 1
for i, j in reversed(order):
    a, b = rec[i, j]
    if a >= 0: acc[a, b] += acc[i, j]

# render
W = 1200; S = W / N
fig = plt.figure(figsize=(W / 200, W / 200), dpi=200)
ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, N); ax.set_ylim(N, 0)
ls = LightSource(azdeg=315, altdeg=40)
terrain = LinearSegmentedColormap.from_list("t", ["#E9F1DD", "#D4E5C2", "#BFD7AA", "#C9D8A8", "#E4E2C4"])
zz = 1.2 * fractal(2.6, 3) + .35 * fractal(1.8, 5) + 1.5 * dist
rgb = ls.shade(zz, cmap=terrain, blend_mode="soft", vert_exag=6)
rgba = np.dstack([rgb[..., :3], mask.astype(float)])
ax.imshow(rgba, extent=(0, N, N, 0), interpolation="bilinear")
T = 90
down = {}
for i, j in order:
    a_, b_ = rec[i, j]
    if a_ >= 0: down[(i, j)] = (a_, b_)
chan = acc >= T
has_up = np.zeros((N, N), bool)
for (i, j), (a_, b_) in down.items():
    if chan[i, j]: has_up[a_, b_] = True
heads = [(i, j) for i, j in order if chan[i, j] and not has_up[i, j]]
heads.sort(key=lambda c: -acc[c])
done = np.zeros((N, N), bool)
def smooth(c, k=5):
    if len(c) < 3: return c
    pad = np.r_[[c[0]] * k, c, [c[-1]] * k]; ker = np.ones(2 * k + 1) / (2 * k + 1)
    out = np.c_[np.convolve(pad[:, 0], ker, 'valid'), np.convolve(pad[:, 1], ker, 'valid')]
    out[0], out[-1] = c[0], c[-1]; return out
segs, lws = [], []
for h in sorted(heads, key=lambda c: -acc[c]):
    path = [h]; cur = h
    while cur in down and not done[cur]:
        done[cur] = True; cur = down[cur]; path.append(cur)
        if done[cur]: break
    pts = np.array([(j + .5, i + .5) for i, j in path], float)
    sm = smooth(pts, 4)
    w = np.array([acc[c] for c in path])
    for k in range(len(sm) - 1):
        segs.append([tuple(sm[k]), tuple(sm[k + 1])]); lws.append(.45 + .55 * np.log1p(w[k] / T) ** 1.45)
ax.add_collection(LineCollection(segs, colors="#2A78CF", linewidths=lws, capstyle="round", joinstyle="round"))
ax.plot(np.r_[bx, bx[0]], np.r_[by, by[0]], color="#1E5A2C", lw=3.2)
fig.savefig(OUT / "basin_network.png", transparent=True); plt.close(fig)

# marker positions: outlet + gauges on mid/large streams spread over the basin
cand = [(acc[i, j], i, j) for i, j in order if acc[i, j] >= 400]
picked = [(oy, ox)]
for _, i, j in sorted(cand, key=lambda c: -c[0]):
    if all(np.hypot(i - a, j - b) > 55 for a, b in picked): picked.append((i, j))
    if len(picked) == 7: break
pts = [dict(x=round((j + .5) * S), y=round((i + .5) * S)) for i, j in picked]
print(json.dumps(dict(size=W, outlet=pts[0], gauges=pts[1:])))
