"""Render the CONUS river + USGS streamgage map used on the "gauge gap" slide.

Data (download once, pass the folder as the first argument):
  - Rivers: USGS National Atlas 1:1,000,000 hydrography, lower 48
    https://prd-tnm.s3.amazonaws.com/StagedProducts/Small-scale/data/Hydrography/hydr48m010g.gdb_nt00893.tar.gz
    (extract so that <data>/hydr/hydr48m010g.gdb exists)
  - Outline: US Census cartographic boundary, states 1:5M
    https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_5m.zip  -> <data>/states.zip
  - Gauges: USGS NWIS site service, one RDB file per state in <data>/nwis/,
    active stream sites with daily discharge:
    https://waterservices.usgs.gov/nwis/site/?format=rdb&stateCd=XX&siteType=ST&siteStatus=active&hasDataTypeCd=dv&parameterCd=00060

Writes assets/img/us_rivers.jpg (land + rivers on the slide green) and assets/img/us_gauges.png
(gauge dots only, transparent) with identical extent, so they can be stacked.
Usage: python3 tools/make_us_map.py <data-folder>"""
import glob, io, pathlib, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

data = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "img"
CRS = "EPSG:5070"                       # CONUS Albers equal area
W_IN, DPI = 16, 220                     # 3520 px wide

# ---- outline ----
states = gpd.read_file(f"zip://{data/'states.zip'}")
states = states[~states.STUSPS.isin(["AK", "HI", "PR", "VI", "GU", "MP", "AS"])].to_crs(CRS)
land = states.dissolve()
xmin, ymin, xmax, ymax = land.total_bounds
pad = 40_000
xmin, ymin, xmax, ymax = xmin - pad, ymin - pad, xmax + pad, ymax + pad
H_IN = W_IN * (ymax - ymin) / (xmax - xmin)

def canvas():
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax); ax.set_aspect("equal")
    return fig, ax

# ---- rivers ----
gdb = glob.glob(str(data / "hydr" / "*.gdb"))[0]
streams = pyogrio.read_dataframe(gdb, layer="Stream", columns=["Strahler", "Feature"])
streams = streams[streams.Feature.isin(["Stream", "Artificial Path", "Stream/River", "Canal", "Connector"]) | True]
streams = streams.to_crs(CRS)
print("stream segments:", len(streams))

fig, ax = canvas()
land.plot(ax=ax, color="#2F6A5C", edgecolor="none", alpha=.55)
states.boundary.plot(ax=ax, color="#ffffff", linewidth=.25, alpha=.18)
order = streams.Strahler.clip(lower=1, upper=9).fillna(1).astype(int).to_numpy()
for o in range(1, 10):
    sub = streams[order == o]
    if sub.empty:
        continue
    lines = []
    for geom in sub.geometry:
        for part in getattr(geom, "geoms", [geom]):
            c = np.asarray(part.coords)[:, :2]
            if len(c) > 1:
                lines.append(c)
    lw = .18 + .16 * (o - 1) ** 1.35
    a = min(1, .45 + .07 * o)
    ax.add_collection(LineCollection(lines, colors="#5FD3F3", linewidths=lw, alpha=a, capstyle="round"))
fig.savefig(OUT / "us_rivers.png", transparent=True); plt.close(fig)
# flatten onto the slide green as a JPEG (smaller, the slide area behind it is green anyway)
from PIL import Image
im = Image.open(OUT / "us_rivers.png").convert("RGBA")
bg = Image.new("RGBA", im.size, (5, 74, 55, 255)); bg.alpha_composite(im)
bg.convert("RGB").resize((2800, round(2800 * im.height / im.width)), Image.LANCZOS).save(OUT / "us_rivers.jpg", quality=90)
(OUT / "us_rivers.png").unlink()
print("wrote us_rivers.jpg")

# ---- gauges ----
frames = []
for f in sorted(glob.glob(str(data / "nwis" / "*.rdb"))):
    txt = "\n".join(l for l in open(f, encoding="utf-8", errors="replace") if not l.startswith("#"))
    if not txt.strip():
        continue
    df = pd.read_csv(io.StringIO(txt), sep="\t", dtype=str).iloc[1:]   # drop the RDB format row
    frames.append(df[["site_no", "dec_lat_va", "dec_long_va"]])
g = pd.concat(frames).drop_duplicates("site_no").dropna()
g = gpd.GeoDataFrame(g, geometry=gpd.points_from_xy(g.dec_long_va.astype(float), g.dec_lat_va.astype(float)), crs="EPSG:4326").to_crs(CRS)
g = g[g.within(land.geometry.iloc[0].buffer(5_000))]
print("gauges:", len(g))
fig, ax = canvas()
ax.scatter(g.geometry.x, g.geometry.y, s=7, c="#FFC000", edgecolors="#7A5A00", linewidths=.25, zorder=3)
fig.savefig(OUT / "us_gauges.png", transparent=True); plt.close(fig)
gi = Image.open(OUT / "us_gauges.png"); gi.resize((2800, round(2800 * gi.height / gi.width)), Image.LANCZOS).save(OUT / "us_gauges.png")
(OUT / "us_gauges_count.txt").write_text(str(len(g)))
print("wrote us_gauges.png")
