"""01 — 대상지 경계 · 캠퍼스 도로(OSM) · i-Tree 업로드용 shapefile

산출
  data/sites.geojson                 대상지 2곳 경계(WGS84)
  data/raw/osm_campus_roads.json     천안캠퍼스 안 도로(OSM highway) — 대안 B·C 가로수 구간
  제출/i-Tree_경계/{site}_boundary.zip   i-Tree Canopy 'Load Shapefile Boundary' 업로드용
"""
import io
import json
import struct
import zipfile

import requests
from shapely.geometry import shape, mapping, Polygon, MultiPolygon, LineString
from shapely.ops import unary_union

from common import (DATA, RAW, SUBMIT, MASK_A, SITES, QUERIED_ON, T_5186_4326, T_4326_UTM,
                    cells_union, tf, write_json)

# ── 1. 동탄 후보지 A — 6주차 90m 셀(309개, 250.29ha)의 합집합 ─────────────
dongtan_5186 = cells_union(MASK_A)
dongtan = tf(dongtan_5186, T_5186_4326)

# ── 2. 천안캠퍼스 — OSM way 231288273 (Nominatim 조회본) ───────────────────
osm = json.loads((RAW / "osm_cheonan_campus.json").read_text(encoding="utf-8"))[0]
cheonan = shape(osm["geojson"])

feats = []
for sid, g, src in [("dongtan", dongtan, "6주차 후보지 A 90m 셀(EPSG:5186) 합집합 — mask_A.npy"),
                    ("cheonan", cheonan, "OpenStreetMap way 231288273 (Nominatim 조회 " + QUERIED_ON + ")")]:
    a = tf(g, T_4326_UTM).area / 1e4
    feats.append({"type": "Feature", "geometry": mapping(g),
                  "properties": {"id": sid, "name": SITES[sid]["name"], "area_ha": round(a, 2), "source": src}})
    print(sid, round(a, 2), "ha")
write_json(DATA / "sites.geojson", {"type": "FeatureCollection", "features": feats})

# ── 3. 캠퍼스 도로 — Overpass(OSM) highway ────────────────────────────────
roads_path = RAW / "osm_campus_roads.json"
if not roads_path.exists():
    minx, miny, maxx, maxy = cheonan.bounds
    q = f"""[out:json][timeout:60];
way["highway"]({miny},{minx},{maxy},{maxx});
out geom;"""
    for ep in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
               "https://overpass.private.coffee/api/interpreter"):
        try:
            r = requests.post(ep, data={"data": q}, timeout=120, headers={"User-Agent": "ndvi-dashboard-coursework"})
            r.raise_for_status()
            break
        except requests.RequestException as e:
            print("overpass retry:", ep, e)
    else:
        raise SystemExit("Overpass 서버 응답 없음")
    roads_path.write_text(r.text, encoding="utf-8")
ways = json.loads(roads_path.read_text(encoding="utf-8"))["elements"]
inside = []
for w in ways:
    if w.get("type") != "way" or "geometry" not in w:
        continue
    hw = w["tags"].get("highway", "")
    if hw in ("footway", "steps", "path", "pedestrian", "cycleway", "corridor", "elevator", "track"):
        continue
    ln = LineString([(p["lon"], p["lat"]) for p in w["geometry"]]).intersection(cheonan)
    if not ln.is_empty:
        inside.append({"type": "Feature", "geometry": mapping(ln),
                       "properties": {"osm_id": w["id"], "highway": hw, "name": w["tags"].get("name", "")}})
write_json(DATA / "campus_roads.geojson", {"type": "FeatureCollection", "features": inside})
print("campus roads", len(inside))


# ── 4. i-Tree 업로드용 shapefile (WGS84 폴리곤, 최소 구현) ──────────────────
PRJ = ('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],'
       'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]')


def rings(g):
    polys = [g] if isinstance(g, Polygon) else list(g.geoms)
    out = []
    for p in polys:
        ext = list(p.exterior.coords)
        if Polygon(ext).exterior.is_ccw:      # shapefile 외곽은 시계방향
            ext = ext[::-1]
        out.append(ext)
        for h in p.interiors:
            hc = list(h.coords)
            if not Polygon(hc).exterior.is_ccw:
                hc = hc[::-1]
            out.append(hc)
    return out


def shapefile_bytes(g, name):
    rs = rings(g)
    pts = [pt for r in rs for pt in r]
    minx, miny, maxx, maxy = g.bounds
    # 레코드 내용: type, bbox, numParts, numPoints, parts[], points[]
    content = struct.pack("<i4d2i", 5, minx, miny, maxx, maxy, len(rs), len(pts))
    idx = 0
    for r in rs:
        content += struct.pack("<i", idx)
        idx += len(r)
    for x, y in pts:
        content += struct.pack("<2d", x, y)
    rec = struct.pack(">2i", 1, len(content) // 2) + content

    def header(file_len_words):
        return (struct.pack(">7i", 9994, 0, 0, 0, 0, 0, file_len_words) +
                struct.pack("<2i4d4d", 1000, 5, minx, miny, maxx, maxy, 0, 0, 0, 0))
    shp = header((100 + len(rec)) // 2) + rec
    shx = header((100 + 8) // 2) + struct.pack(">2i", 50, len(content) // 2)
    # dbf: 필드 1개(NAME C 50) — 영문 이름(인코딩 문제 방지)
    nm = name.encode("ascii", "ignore")[:50].ljust(50)
    dbf = struct.pack("<4BIHH20x", 3, 126, 10, 19, 1, 32 + 32 + 1, 1 + 50)
    dbf += struct.pack("<11sc4xB15x", b"NAME", b"C", 50) + b"\r"
    dbf += b" " + nm + b"\x1a"
    return shp, shx, dbf


kit = SUBMIT / "i-Tree_경계"
kit.mkdir(exist_ok=True)
for sid, g, en in [("dongtan", dongtan, "Dongtan candidate site A"), ("cheonan", cheonan, "Sangmyung Univ Cheonan campus")]:
    shp, shx, dbf = shapefile_bytes(g, en)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for ext, b in [("shp", shp), ("shx", shx), ("dbf", dbf), ("prj", PRJ.encode())]:
            z.writestr(f"{sid}_boundary.{ext}", b)
    (kit / f"{sid}_boundary.zip").write_bytes(buf.getvalue())
    (kit / f"{sid}_boundary.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": mapping(g), "properties": {"name": en}}]}),
        encoding="utf-8")
print("i-Tree kit ->", kit)
