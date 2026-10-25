"""07 — 캐노피 대체 판독(i-Tree 아님): 무작위 500점 · 고해상도 영상 조각

i-Tree Canopy와 같은 방식(경계 안 무작위 점 · Tree/Non-Tree · SE = √(p(1−p)/N))을
Esri World Imagery 위에서 판독자(AI · Claude)가 점마다 보고 분류한다. i-Tree 결과가 아니며 .itrcnpy는 없다.

산출
  outputs/canopy_points_dongtan.csv   점 번호 · 위경도 (분류는 판독 후 data/canopy_ai_reading.json)
  outputs/canopy_sheets/sheet_XX.png  25점씩 조각(중앙 십자 = 판독 위치, 한 조각 = 약 60m)
"""
import io
import math
import csv

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from shapely import contains_xy

from common import OUT, site_geom, T_UTM_4326

SID = "dongtan"
N = 500
SEED = 20261025
Z = 18
CHIP_M = 60          # 조각 한 변(m)
CHIP_PX = 180        # 출력 조각 크기(px)
TILE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

g = site_geom(SID, 32652)
rng = np.random.default_rng(SEED)
minx, miny, maxx, maxy = g.bounds
pts = []
while len(pts) < N:
    x, y = rng.uniform(minx, maxx, 4000), rng.uniform(miny, maxy, 4000)
    ok = contains_xy(g, x, y)
    pts += list(zip(x[ok], y[ok]))
pts = pts[:N]
lon, lat = T_UTM_4326.transform(np.array([p[0] for p in pts]), np.array([p[1] for p in pts]))
with open(OUT / f"canopy_points_{SID}.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "lat", "lon", "utm_x", "utm_y"])
    for i in range(N):
        w.writerow([i + 1, round(lat[i], 7), round(lon[i], 7), round(pts[i][0], 1), round(pts[i][1], 1)])


def tile_xy(la, lo, z):
    n = 2 ** z
    x = (lo + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(la))) / math.pi) / 2 * n
    return x, y


# 대상지 전체 모자이크(z18)
la0, la1 = lat.min() - 0.0008, lat.max() + 0.0008
lo0, lo1 = lon.min() - 0.0010, lon.max() + 0.0010
xa, ya = tile_xy(la1, lo0, Z)
xb, yb = tile_xy(la0, lo1, Z)
tx0, ty0, tx1, ty1 = int(xa), int(ya), int(xb), int(yb)
mosaic = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
s = requests.Session()
s.headers["User-Agent"] = "ndvi-dashboard-coursework"
n_t = 0
for tx in range(tx0, tx1 + 1):
    for ty in range(ty0, ty1 + 1):
        r = s.get(TILE.format(z=Z, y=ty, x=tx), timeout=60)
        r.raise_for_status()
        mosaic.paste(Image.open(io.BytesIO(r.content)).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
        n_t += 1
print("tiles", n_t, mosaic.size)

mpp = 156543.03392 * math.cos(math.radians((la0 + la1) / 2)) / 2 ** Z     # m / px
half = int(round(CHIP_M / mpp / 2))
sheets = OUT / "canopy_sheets"
sheets.mkdir(exist_ok=True)
for f in sheets.glob("*.png"):
    f.unlink()
try:
    font = ImageFont.truetype("arialbd.ttf", 18)
except OSError:
    font = ImageFont.load_default()
COLS, ROWS = 5, 5
for sh in range(math.ceil(N / (COLS * ROWS))):
    page = Image.new("RGB", (COLS * (CHIP_PX + 6), ROWS * (CHIP_PX + 6)), "white")
    for k in range(COLS * ROWS):
        i = sh * COLS * ROWS + k
        if i >= N:
            break
        px, py = tile_xy(lat[i], lon[i], Z)
        cx, cy = (px - tx0) * 256, (py - ty0) * 256
        chip = mosaic.crop((int(cx - half), int(cy - half), int(cx + half), int(cy + half))).resize((CHIP_PX, CHIP_PX), Image.LANCZOS)
        d = ImageDraw.Draw(chip)
        c = CHIP_PX // 2
        for col, wd in (("black", 4), ("#ff2020", 2)):
            d.line([(c - 22, c), (c - 6, c)], fill=col, width=wd); d.line([(c + 6, c), (c + 22, c)], fill=col, width=wd)
            d.line([(c, c - 22), (c, c - 6)], fill=col, width=wd); d.line([(c, c + 6), (c, c + 22)], fill=col, width=wd)
        d.rectangle([0, 0, 46, 22], fill="black")
        d.text((4, 1), str(i + 1), fill="yellow", font=font)
        page.paste(chip, ((k % COLS) * (CHIP_PX + 6), (k // COLS) * (CHIP_PX + 6)))
    page.save(sheets / f"sheet_{sh + 1:02d}.png")
print("sheets", sh + 1, f"mpp {mpp:.2f} · chip {CHIP_M}m")
