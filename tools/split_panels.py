"""Find white vertical gutters in a figure and report candidate split columns.
Usage: python3 tools/split_panels.py image.png lo:hi [lo:hi ...]   (fractions of width)
Prints, for each range, the centre of the widest run of near-white columns."""
import sys
import numpy as np
from PIL import Image

img = np.asarray(Image.open(sys.argv[1]).convert("L"), dtype=np.float32)
h, w = img.shape
ink = (img < 235).mean(axis=0)            # fraction of non-white pixels per column
for rng in sys.argv[2:]:
    lo, hi = (float(x) for x in rng.split(":"))
    a, b = int(lo * w), int(hi * w)
    seg = ink[a:b]
    thr = max(0.004, seg.min() + 0.004)
    best, cur, start, bs = 0, 0, 0, a
    for i, v in enumerate(seg):
        if v <= thr:
            if cur == 0: start = i
            cur += 1
            if cur > best: best, bs = cur, a + start
        else:
            cur = 0
    print(f"{sys.argv[1].split('/')[-1]} {rng}: split at x={bs + best // 2} (gutter {best}px, min ink {seg.min():.3f}) width={w}")
