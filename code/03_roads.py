"""03 — 과제 ① 도로 위계: 6주차 대안 1안(대안 C · 절충)에 간선 3단 배치 · 용도지역별 도로율

규칙(사전 고정)
  배치간격  「도시·군계획시설의 결정·구조 및 설치기준에 관한 규칙」 제10조제3호 —
            주간선 1,000m · 보조간선 500m · 집산 250m 내외, 직교 격자(대상지 평탄지 → 격자형, 슬라이드 12)
  배치 범위 주간선 = 대상지 전체를 지나는 통과 간선 · 보조간선·집산 = 개발용지(주거·상업·공업) + 1셀(90m) 안
            150m 미만 토막은 삭제(주간선은 400m 미만 삭제)
  격자 원점 원점만 30m 단위로 탐색 — ① 개발 셀 중심이 도로에서 125m 안인 비율 최대
            → ② 제11조 기준 충족 개수 최대(용도 3 × 전체·간선) → ③ 도로 면적 최소
  횡단 구성 제10조제7호 — 보도·자전거도로·분리대·정차대 폭 포함 (아래 CROSS)
  도로율    제11조제1항 — 주거 15~30%(간선 8~15) · 상업 25~35%(간선 10~15) · 공업 8~20%(간선 4~10), 상한은 '미만'
            간선도로율 = 주간선 + 보조간선
"""
import json

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import LineString, MultiLineString, mapping, box
from shapely.ops import unary_union
import shapely

from common import (OUT, DATA, MASK_A, PLAN_1, G, IND, COM, RES, LU_NAMES, GX0, GY1, CELL,
                    T_5186_4326, cell_box, cells_union, tf, write_json)

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

TIERS = ["주간선", "보조간선", "집산"]
SPACING = {"주간선": 1000, "보조간선": 500, "집산": 250}
CROSS = {   # 횡단 구성(m) — 차로 · 분리대 · 정차대 · 자전거 · 보도
    "주간선": {"규모": "대로 1류", "차로": "6차로 × 3.50 = 21.0", "중앙분리대": 2.0, "정차대": 0.0,
             "자전거도로": "2 × 1.5 = 3.0", "보도": "2 × 4.5 = 9.0", "폭": 35.0, "설계속도": "80~60km/h"},
    "보조간선": {"규모": "대로 3류", "차로": "4차로 × 3.25 = 13.0", "중앙분리대": 1.0, "정차대": 0.0,
              "자전거도로": "2 × 1.5 = 3.0", "보도": "2 × 4.0 = 8.0", "폭": 25.0, "설계속도": "60~50km/h"},
    "집산": {"규모": "중로 1류", "차로": "2차로 × 3.25 = 6.5", "중앙분리대": 0.0, "정차대": "2 × 2.0 = 4.0",
           "자전거도로": "2 × 1.5 = 3.0", "보도": "2 × 3.25 = 6.5", "폭": 20.0, "설계속도": "50~40km/h"},
}
STANDARD = {  # 제11조제1항 (이상 ~ 미만, %)
    "주거": {"전체": (15, 30), "간선": (8, 15)},
    "상업·업무": {"전체": (25, 35), "간선": (10, 15)},
    "공업": {"전체": (8, 20), "간선": (4, 10)},
}

site = cells_union(MASK_A)
lu = np.where(MASK_A, PLAN_1, 0)
dev_mask = np.isin(lu, [IND, COM, RES])
dev = cells_union(dev_mask)
dev_zone = dev.buffer(CELL, join_style=2).intersection(site)
minx, miny, maxx, maxy = site.bounds
rr, cc = np.nonzero(dev_mask)
dev_xy = np.column_stack([GX0 + (cc + 0.5) * CELL, GY1 - (rr + 0.5) * CELL])


def lines(ox, oy, spacing, phase):
    """원점(ox, oy)에서 spacing 간격, phase 만큼 밀린 수직·수평선"""
    out = []
    for x in np.arange(ox + phase - 4000, maxx + 1, spacing):
        if minx - 1 < x < maxx + 1:
            out.append(LineString([(x, miny - 1), (x, maxy + 1)]))
    for y in np.arange(oy + phase - 4000, maxy + 1, spacing):
        if miny - 1 < y < maxy + 1:
            out.append(LineString([(minx - 1, y), (maxx + 1, y)]))
    return out


def clip(ls, area, min_len=150):
    out = []
    for l in ls:
        g = l.intersection(area)
        parts = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
        out += [p for p in parts if p.geom_type == "LineString" and p.length >= min_len]
    return out


def network(ox, oy):
    main = clip(lines(ox, oy, 1000, 0), site, min_len=400)      # 통과 간선 — 400m 미만 토막 삭제
    sub = clip(lines(ox, oy, 1000, 500), dev_zone)
    col = clip(lines(ox, oy, 500, 250), dev_zone)     # 250m 격자 = 500m 간격선의 사이
    return {"주간선": main, "보조간선": sub, "집산": col}


def polygons(net):
    """위계 우선순위로 겹침 제거 — 교차부는 상위 위계에 귀속"""
    taken = None
    out = {}
    for t in TIERS:
        geoms = [l.buffer(CROSS[t]["폭"] / 2, cap_style="flat") for l in net[t]]
        g = unary_union(geoms).intersection(site) if geoms else box(0, 0, 0, 0)
        if taken is not None:
            g = g.difference(taken)
        out[t] = g
        taken = g if taken is None else unary_union([taken, g])
    return out


ZONES = {"주거": cells_union(lu == RES), "상업·업무": cells_union(lu == COM), "공업": cells_union(lu == IND)}


def compliance(polys):
    """제11조제1항 기준 충족 개수(용도지역 3 × 전체·간선 2 = 최대 6)"""
    ok = 0
    for z, zg in ZONES.items():
        a = {t: polys[t].intersection(zg).area for t in TIERS}
        tot = 100 * sum(a.values()) / zg.area
        art = 100 * (a["주간선"] + a["보조간선"]) / zg.area
        lo, hi = STANDARD[z]["전체"]
        alo, ahi = STANDARD[z]["간선"]
        ok += (lo <= tot < hi) + (alo <= art < ahi)
    return ok


def score(net):
    allx = [l for t in TIERS for l in net[t]]
    if not allx:
        return 0, 0, 0
    u = unary_union(allx)
    d = shapely.distance(shapely.points(dev_xy), u)
    cover = float((d <= 125).mean())
    polys = polygons(net)
    area = sum(p.area for p in polys.values())
    return cover, compliance(polys), area


best = None
for ox in np.arange(minx, minx + 1000, 30):
    for oy in np.arange(miny, miny + 1000, 30):
        net = network(ox, oy)
        if not net["주간선"]:
            continue
        cov, ok, ar = score(net)
        key = (round(cov, 3), ok, -ar)
        if best is None or key > best[0]:
            best = (key, ox, oy, net)
(_, ox, oy, net) = best
polys = polygons(net)
cover, n_ok, road_area = score(net)
print(f"origin ({ox:.0f}, {oy:.0f}) · 개발 셀 125m 접근 {cover:.1%} · 기준 충족 {n_ok}/6 · 도로 {road_area / 1e4:.2f}ha")

# ── 용도지역별 도로율 ──
zones = {"주거": cells_union(lu == RES), "상업·업무": cells_union(lu == COM),
         "공업": cells_union(lu == IND), "공원·녹지": cells_union(lu == G)}
rows = []
for zname, zg in list(zones.items()) + [("대상지 전체", site)]:
    za = zg.area
    a = {t: polys[t].intersection(zg).area for t in TIERS}
    tot = sum(a.values())
    art = a["주간선"] + a["보조간선"]
    std = STANDARD.get(zname)
    r = {"용도지역": zname, "면적(ha)": round(za / 1e4, 2),
         "주간선(ha)": round(a["주간선"] / 1e4, 2), "보조간선(ha)": round(a["보조간선"] / 1e4, 2),
         "집산(ha)": round(a["집산"] / 1e4, 2), "도로 면적(ha)": round(tot / 1e4, 2),
         "도로율(%)": round(100 * tot / za, 1), "간선도로율(%)": round(100 * art / za, 1)}
    if std:
        lo, hi = std["전체"]
        alo, ahi = std["간선"]
        r["기준 도로율(%)"] = f"{lo}~{hi}"
        r["기준 간선도로율(%)"] = f"{alo}~{ahi}"
        r["도로율 판정"] = "충족" if lo <= r["도로율(%)"] < hi else ("미달" if r["도로율(%)"] < lo else "초과")
        r["간선 판정"] = "충족" if alo <= r["간선도로율(%)"] < ahi else ("미달" if r["간선도로율(%)"] < alo else "초과")
    else:
        r["기준 도로율(%)"] = "—"
        r["기준 간선도로율(%)"] = "—"
        r["도로율 판정"] = "기준 없음(통과 구간)" if zname == "공원·녹지" else "참고"
        r["간선 판정"] = "—"
    rows.append(r)
    print(r)

lengths = {t: round(sum(l.length for l in net[t]), 0) for t in TIERS}
segs = []
for t in TIERS:
    for i, l in enumerate(net[t]):
        segs.append({"위계": t, "구간": f"{t}-{i + 1}", "방향": "남북" if abs(l.coords[0][0] - l.coords[-1][0]) < 1 else "동서",
                     "길이(m)": round(l.length, 0), "폭(m)": CROSS[t]["폭"], "면적(ha)": round(l.length * CROSS[t]["폭"] / 1e4, 2)})

# ── GeoJSON (지도용 · WGS84) ──
feats = []
for t in TIERS:
    for l in net[t]:
        feats.append({"type": "Feature", "geometry": mapping(tf(l, T_5186_4326)), "properties": {"tier": t, "width": CROSS[t]["폭"]}})
    if not polys[t].is_empty:
        feats.append({"type": "Feature", "geometry": mapping(tf(polys[t], T_5186_4326)), "properties": {"tier": t, "kind": "area"}})
lu_feats = []
for code, name in LU_NAMES.items():
    g = cells_union(lu == code)
    if not g.is_empty:
        lu_feats.append({"type": "Feature", "geometry": mapping(tf(g, T_5186_4326)), "properties": {"lu": name}})
write_json(OUT / "roads.geojson", {"type": "FeatureCollection", "features": feats})
write_json(OUT / "plan_landuse.geojson", {"type": "FeatureCollection", "features": lu_feats})
write_json(OUT / "roads.json", {"origin_5186": [ox, oy], "access_125m": cover, "compliance": n_ok, "lengths_m": lengths,
                                "cross": CROSS, "standard": STANDARD, "table": rows, "segments": segs,
                                "spacing": SPACING})

# ── 그림 ──
fig, ax = plt.subplots(figsize=(8.6, 6.4), dpi=150)
colors = {G: "#5f9e57", IND: "#9b7aa0", COM: "#e0603a", RES: "#f2cf5b"}
for code, name in LU_NAMES.items():
    g = cells_union(lu == code)
    for p in getattr(g, "geoms", [g]):
        if not p.is_empty:
            ax.fill(*p.exterior.xy, color=colors[code], lw=0, label=None)
for t, c, w in [("집산", "#555", 1.2), ("보조간선", "#1f4e9c", 2.4), ("주간선", "#c0262d", 3.6)]:
    for l in net[t]:
        ax.plot(*l.xy, color=c, lw=w, solid_capstyle="butt")
for p in getattr(site, "geoms", [site]):
    ax.plot(*p.exterior.xy, color="#111", lw=0.8)
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
ax.legend(handles=[Patch(color=colors[k], label=v) for k, v in LU_NAMES.items()] +
          [Line2D([0], [0], color="#c0262d", lw=3.6, label="주간선 35m"),
           Line2D([0], [0], color="#1f4e9c", lw=2.4, label="보조간선 25m"),
           Line2D([0], [0], color="#555", lw=1.2, label="집산 20m")],
          loc="lower left", fontsize=8, frameon=True)
ax.set_aspect("equal")
ax.set_xticks([]); ax.set_yticks([])
ax.set_title("과제 ① 대안 1안(6주차 대안 C · 절충) — 간선 3단 배치", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "fig_roads.png")
print("saved roads")
