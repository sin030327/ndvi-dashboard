"""05 — 대시보드 데이터(data.js) 내보내기"""
import json

from shapely.geometry import shape

from common import ROOT, OUT, DATA, SITES, QUERIED_ON, site_geom

sat = json.loads((OUT / "satellite.json").read_text(encoding="utf-8"))
ccs = json.loads((OUT / "ccs.json").read_text(encoding="utf-8"))
roads = json.loads((OUT / "roads.json").read_text(encoding="utf-8"))
roads_geo = json.loads((OUT / "roads.geojson").read_text(encoding="utf-8"))
lu_geo = json.loads((OUT / "plan_landuse.geojson").read_text(encoding="utf-8"))
campus_roads = json.loads((DATA / "campus_roads.geojson").read_text(encoding="utf-8"))
sites_geo = json.loads((DATA / "sites.geojson").read_text(encoding="utf-8"))


def rings_latlng(g):
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    return [[[round(y, 6), round(x, 6)] for x, y in p.exterior.coords] for p in polys]


def round_geo(gj, nd=6):
    def r(c):
        return [r(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], nd), round(c[1], nd)]
    for f in gj["features"]:
        f["geometry"]["coordinates"] = r(f["geometry"]["coordinates"])
    return gj


out = {"queried_on": QUERIED_ON, "sites": {}, "ccs": {k: v for k, v in ccs.items() if k != "sites"}}
for sid, meta in SITES.items():
    g = site_geom(sid, 4326)
    props = next(f["properties"] for f in sites_geo["features"] if f["properties"]["id"] == sid)
    c = g.centroid
    s = {"id": sid, **meta, "area_ha": props["area_ha"], "boundary_src": props["source"],
         "center": [round(c.y, 6), round(c.x, 6)], "boundary": rings_latlng(g),
         "sat": sat[sid], "ccs": ccs["sites"][sid]}
    if sid == "dongtan":
        s["roads"] = {**roads, "geo": round_geo(roads_geo), "landuse": round_geo(lu_geo)}
    else:
        s["campus_roads"] = round_geo(campus_roads)
    out["sites"][sid] = s

txt = "window.DASH = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"
(ROOT / "data.js").write_text(txt, encoding="utf-8")
print("data.js", round(len(txt.encode()) / 1024), "KB")
