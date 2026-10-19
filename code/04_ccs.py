"""04 — 과제 ③·④: 지표 ⑦ 카탈로그 · CCS 1차 결과표 · 대안 비교 서식(대안 A·B·C)

7주차 대안(슬라이드 49~51) — 같은 배분에서 '시설 조합'만 다르게
  대안 A · 현황 유지        시설 없음
  대안 B · 가로수 열식      간선(주간선·보조간선) 양쪽 1열씩 2열, 수관폭 8m
  대안 C · 가로수 + 투수포장 B + 집산도로 포장의 30%를 투수포장(유출계수 0.30)으로 전환
  (캠퍼스는 OSM 캠퍼스 도로 양쪽 2열 · 캠퍼스 도로 포장의 30% 투수포장)

값의 성격
  NDVI · 지표온도 — 실측(02_satellite). 설계안은 위성으로 잴 수 없어 대안 A·B·C 모두 같은 장면 값(변화 없음)
  캐노피          — i-Tree 500점 판독값(학생 판독 후 입력). 대안 B·C = 판독값 + 가로수 수관 면적 비율(계산)
  유출계수        — 원본 43번 표 9-11(한국토지공사 2005) × 용도별 면적
  HM              — InVEST Urban Cooling 식(User Guide)을 파이썬으로 재구현. 생물물리 값은 가정
  조성비·유지관리 — 물량(계산) × 가정 단가(출처 확인 필요)
"""
import json

import numpy as np
import shapely
from shapely.geometry import shape, LineString
from shapely.ops import unary_union

from common import (OUT, DATA, SITES, QUERIED_ON, MASK_A, PLAN_1, G, IND, COM, RES, GX0, GY1, CELL,
                    T_4326_UTM, cells_union, site_geom, tf, write_json)

SAT = json.loads((OUT / "satellite.json").read_text(encoding="utf-8"))
ROADS = json.loads((OUT / "roads.json").read_text(encoding="utf-8"))
N_ITREE = 500

# ── 사전 고정값 ─────────────────────────────────────────────────────────
RUNOFF = {"근린공원": 0.30, "공동주택": 0.65, "상업용지": 0.80, "도로": 0.85, "학교": 0.40, "투수포장": 0.30}
RUNOFF_NOTE = "원본 43번 표 9-11 — 한국토지공사(2005) 《생태환경도시개발편람》 245쪽 · 공업은 표에 없어 상업용지 0.80 준용(가정) · 투수포장 0.30은 가정"
PERM_SHARE = 0.30          # 대안 C 투수포장 전환 비율
PERM_RANGE = (0.20, 0.45)  # 투수포장 유출계수 가정 폭(막힘·동결 — 슬라이드 49 위험)
CROWN = 8.0                # 가로수 수관폭(m) — 슬라이드 50 가정
TREE_SPACING = 8.0         # 가로수 식재 간격(m) — 가정
CAMPUS_ROAD_W = 6.0        # 캠퍼스 OSM service 도로 폭(m) — 가정
D_COOL = 450.0             # InVEST 최대 냉각거리 기본값
W_CC = (0.6, 0.2, 0.2)     # shade · albedo · ETI 기본 가중치
# 생물물리 표(가정) — shade · kc · albedo · green_area
BIO = {
    "공원·녹지": (0.50, 0.90, 0.16, 1), "주거": (0.15, 0.30, 0.15, 0), "상업·업무": (0.05, 0.15, 0.12, 0),
    "공업": (0.05, 0.10, 0.15, 0), "도로": (0.00, 0.05, 0.10, 0), "가로수": (0.80, 0.90, 0.15, 1),
    "투수포장": (0.00, 0.20, 0.15, 0), "수목(NDVI≥0.5)": (0.80, 1.00, 0.15, 1),
    "초지(0.3~0.5)": (0.10, 0.75, 0.20, 1), "건물·포장(<0.3)": (0.10, 0.20, 0.15, 0),
}
CLASSES = list(BIO)
# 가정 단가(출처 확인 필요 — 학생이 실제 단가로 바꿔 넣을 것)
UNIT = {"가로수 식재(원/주)": 500_000, "가로수 유지관리(원/주·년)": 30_000,
        "투수포장 추가 조성(원/㎡, 일반 포장 대비)": 40_000, "투수포장 유지관리(원/㎡·년)": 2_000}
UNIT_NOTE = "가정 단가 — 출처 미확인. 조달청 표준시장단가 등 실제 단가로 교체 필요"

# 대안 비교 서식 — 5점 척도 구간 · 가중치(사전 고정, 팀 승인 필요)
SCALE = {
    "캐노피 피복률(%)": ("↑", [10, 20, 30, 40]),
    "NDVI 평균": ("↑", [0.2, 0.35, 0.5, 0.65]),
    "지표온도(℃)": ("↓", [40, 36, 32, 28]),
    "가중 유출계수": ("↓", [0.7, 0.6, 0.5, 0.4]),
    "조성비(백만원/ha)": ("↓", [30, 15, 5, 0.0001]),
    "유지관리비(백만원/ha·년)": ("↓", [3, 1.5, 0.5, 0.0001]),
}
WEIGHTS = {"캐노피 피복률(%)": 0.25, "NDVI 평균": 0.10, "지표온도(℃)": 0.15,
           "가중 유출계수": 0.20, "조성비(백만원/ha)": 0.15, "유지관리비(백만원/ha·년)": 0.15}
ALTS = ["대안 A · 현황 유지", "대안 B · 가로수 열식", "대안 C · 가로수 + 투수포장"]


def score(name, v):
    d, cuts = SCALE[name]
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if d == "↑":
        return 1 + sum(v >= c for c in cuts)
    return 1 + sum(v < c for c in cuts) if name.startswith(("조성비", "유지관리")) else 1 + sum(v < c for c in cuts)


def fft_conv(a, k):
    s = (a.shape[0] + k.shape[0] - 1, a.shape[1] + k.shape[1] - 1)
    r = np.fft.irfft2(np.fft.rfft2(a, s) * np.fft.rfft2(k, s), s)
    oy, ox = k.shape[0] // 2, k.shape[1] // 2
    return r[oy:oy + a.shape[0], ox:ox + a.shape[1]]


def hm_model(lulc, valid, res, weights=W_CC, d_cool=D_COOL):
    """InVEST Urban Cooling — CC = w1·shade + w2·albedo + w3·ETI (ET0 균일 → ETI = Kc)
    큰 녹지(반경 d_cool 안 녹지 > 2ha) 영향권: CC_park = Σ g·CC·e^(−d/d_cool) 가중 평균, HM = max(CC, CC_park)"""
    sh = np.zeros(lulc.shape); kc = np.zeros(lulc.shape); al = np.zeros(lulc.shape); g = np.zeros(lulc.shape)
    for i, c in enumerate(CLASSES):
        m = lulc == i
        sh[m], kc[m], al[m], g[m] = BIO[c]
    cc = weights[0] * sh + weights[1] * al + weights[2] * kc
    r = int(d_cool // res)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1] * res
    d = np.hypot(xx, yy)
    disk = d <= d_cool
    kern = np.where(disk, np.exp(-d / d_cool), 0)
    v = valid.astype(float)
    num = fft_conv(cc * g * v, kern)
    den = fft_conv(v, kern)
    cc_park = np.where(den > 0, num / np.maximum(den, 1e-9), 0)
    ga = fft_conv(g * v, disk.astype(float)) * res * res / 1e4      # ha
    hm = np.where((ga > 2) & (cc_park > cc), cc_park, cc)
    return hm, cc


def raster_grid(bounds, res):
    minx, miny, maxx, maxy = bounds
    w = int(np.ceil((maxx - minx) / res)); h = int(np.ceil((maxy - miny) / res))
    xs = minx + res * (np.arange(w) + 0.5); ys = maxy - res * (np.arange(h) + 0.5)
    return np.meshgrid(xs, ys)


def cin(g, X, Y):
    return shapely.contains_xy(g, X, Y) if not g.is_empty else np.zeros(X.shape, bool)


# ════════════════════════════ 동탄 후보지 A ════════════════════════════
def dongtan():
    site = cells_union(MASK_A)
    lu = np.where(MASK_A, PLAN_1, 0)
    rd = shape  # noqa
    road_feats = json.loads((OUT / "roads.geojson").read_text(encoding="utf-8"))["features"]
    from common import T_4326_5186
    lines = {t: [tf(shape(f["geometry"]), T_4326_5186) for f in road_feats
                 if f["properties"]["tier"] == t and f["properties"].get("kind") != "area"]
             for t in ("주간선", "보조간선", "집산")}
    W = {t: ROADS["cross"][t]["폭"] for t in lines}
    road_poly = {}
    taken = None
    for t in ("주간선", "보조간선", "집산"):
        g = unary_union([l.buffer(W[t] / 2, cap_style="flat") for l in lines[t]]).intersection(site)
        if taken is not None:
            g = g.difference(taken)
        road_poly[t] = g
        taken = g if taken is None else unary_union([taken, g])
    roads_all = taken
    # 가로수 — 간선 양쪽 가장자리 수관폭 8m 띠(보도 위)
    strips = []
    for t in ("주간선", "보조간선"):
        for l in lines[t]:
            strips.append(l.buffer(W[t] / 2, cap_style="flat").difference(l.buffer(W[t] / 2 - CROWN, cap_style="flat")))
    trees = unary_union(strips).intersection(site)
    tree_len = sum(l.length for t in ("주간선", "보조간선") for l in lines[t])
    n_trees = int(round(2 * tree_len / TREE_SPACING))
    perm_area = PERM_SHARE * road_poly["집산"].area

    zone = {"공원·녹지": cells_union(lu == G), "주거": cells_union(lu == RES),
            "상업·업무": cells_union(lu == COM), "공업": cells_union(lu == IND)}
    coef_of = {"공원·녹지": RUNOFF["근린공원"], "주거": RUNOFF["공동주택"], "상업·업무": RUNOFF["상업용지"], "공업": RUNOFF["상업용지"]}
    A = site.area
    base_sum = sum((zg.difference(roads_all).area) * coef_of[z] for z, zg in zone.items()) + roads_all.area * RUNOFF["도로"]
    runoff = {
        "A": base_sum / A, "B": base_sum / A,
        "C": (base_sum - perm_area * (RUNOFF["도로"] - RUNOFF["투수포장"])) / A,
    }
    runoff_C_range = [(base_sum - perm_area * (RUNOFF["도로"] - p)) / A for p in PERM_RANGE[::-1]]

    # HM — 10m 격자 래스터화(EPSG:5186)
    res = 10.0
    X, Y = raster_grid(site.bounds, res)
    valid = cin(site, X, Y)
    base = np.full(X.shape, CLASSES.index("공원·녹지"))
    for z, zg in zone.items():
        base[cin(zg, X, Y)] = CLASSES.index(z)
    base[cin(roads_all, X, Y)] = CLASSES.index("도로")
    lb = base.copy(); lb[cin(trees, X, Y) & valid] = CLASSES.index("가로수")
    lc = lb.copy()
    # 집산도로 포장 30% — 집산 띠의 바깥쪽 30% 폭(보도·정차대)을 투수포장으로
    col_perm = unary_union([l.buffer(W["집산"] / 2, cap_style="flat").difference(
        l.buffer(W["집산"] / 2 * (1 - PERM_SHARE), cap_style="flat")) for l in lines["집산"]]).intersection(road_poly["집산"])
    lc[cin(col_perm, X, Y) & (lc == CLASSES.index("도로"))] = CLASSES.index("투수포장")
    hm, hm_rng = {}, {}
    for k, l in (("A", base), ("B", lb), ("C", lc)):
        h, _ = hm_model(l, valid, res)
        hm[k] = float(h[valid].mean())
        vals = []
        for ws in ((0.5, 0.25, 0.25), (0.7, 0.15, 0.15)):
            vals.append(float(hm_model(l, valid, res, ws)[0][valid].mean()))
        hm_rng[k] = (min(vals), max(vals))
    d_canopy = trees.difference(zone["공원·녹지"]).area / A      # 기존 녹지 위 가로수는 증가분에서 제외
    qty = {"가로수(주)": n_trees, "가로수 연장(km)": round(tree_len / 1000, 2), "가로수 수관 면적(ha)": round(trees.area / 1e4, 2),
           "투수포장(㎡)": round(perm_area), "집산도로 포장(㎡)": round(road_poly["집산"].area)}
    return dict(area_ha=A / 1e4, runoff=runoff, runoff_C_range=runoff_C_range, hm=hm, hm_range=hm_rng,
                d_canopy=d_canopy, qty=qty, n_trees=n_trees, perm_area=perm_area,
                runoff_basis="1안 배분(공원·녹지 근린공원 0.30 · 주거 공동주택 0.65 · 상업·공업 0.80) + ① 도로망 0.85",
                lulc_basis="1안 배분 90m 셀 + ① 도로망을 10m 격자로 래스터화")


# ════════════════════════════ 천안캠퍼스 ════════════════════════════
def cheonan():
    site = site_geom("cheonan", 32652)
    A = site.area
    z = np.load(OUT / "sat_cheonan.npz")
    ndvi, b10 = z["ndvi"], z["b10"]
    res = 10.0
    h, w = ndvi.shape
    X, Y = np.meshgrid(b10[0] + res * (np.arange(w) + 0.5), b10[3] - res * (np.arange(h) + 0.5))
    valid = np.isfinite(ndvi)
    feats = json.loads((DATA / "campus_roads.geojson").read_text(encoding="utf-8"))["features"]
    lines = []
    for f in feats:
        g = tf(shape(f["geometry"]), T_4326_UTM)
        lines += [g] if g.geom_type == "LineString" else list(g.geoms)
    road = unary_union([l.buffer(CAMPUS_ROAD_W / 2, cap_style="flat") for l in lines]).intersection(site)
    trees = unary_union([l.buffer(CAMPUS_ROAD_W / 2 + CROWN, cap_style="flat").difference(
        l.buffer(CAMPUS_ROAD_W / 2, cap_style="flat")) for l in lines]).intersection(site)
    tree_len = sum(l.intersection(site).length for l in lines)
    n_trees = int(round(2 * tree_len / TREE_SPACING))
    perm_area = PERM_SHARE * road.area
    base_sum = (A - road.area) * RUNOFF["학교"] + road.area * RUNOFF["도로"]
    runoff = {"A": base_sum / A, "B": base_sum / A,
              "C": (base_sum - perm_area * (RUNOFF["도로"] - RUNOFF["투수포장"])) / A}
    runoff_C_range = [(base_sum - perm_area * (RUNOFF["도로"] - p)) / A for p in PERM_RANGE[::-1]]

    base = np.where(ndvi >= 0.5, CLASSES.index("수목(NDVI≥0.5)"),
                    np.where(ndvi >= 0.3, CLASSES.index("초지(0.3~0.5)"), CLASSES.index("건물·포장(<0.3)")))
    base[cin(road, X, Y)] = CLASSES.index("도로")
    inside = cin(site, X, Y)
    lb = base.copy()
    tm = cin(trees, X, Y) & (base != CLASSES.index("수목(NDVI≥0.5)"))
    lb[tm] = CLASSES.index("가로수")
    lc = lb.copy()
    rp = cin(road, X, Y)
    # 도로 화소의 30%를 투수포장으로(격자 위 균등 배분)
    idx = np.flatnonzero(rp & (lc == CLASSES.index("도로")))
    lc.flat[idx[::max(1, round(1 / PERM_SHARE))]] = CLASSES.index("투수포장")
    hm, hm_rng = {}, {}
    for k, l in (("A", base), ("B", lb), ("C", lc)):
        hh, _ = hm_model(l, valid, res)
        hm[k] = float(hh[inside & valid].mean())
        vals = [float(hm_model(l, valid, res, ws)[0][inside & valid].mean()) for ws in ((0.5, 0.25, 0.25), (0.7, 0.15, 0.15))]
        hm_rng[k] = (min(vals), max(vals))
    # 수관 증가분 — 이미 수목(NDVI≥0.5)인 화소 위 가로수는 제외
    d_canopy = float((tm & inside).sum() * res * res / A)
    qty = {"가로수(주)": n_trees, "가로수 연장(km)": round(tree_len / 1000, 2), "가로수 수관 면적(ha)": round(trees.area / 1e4, 2),
           "투수포장(㎡)": round(perm_area), "캠퍼스 도로 포장(㎡)": round(road.area)}
    return dict(area_ha=A / 1e4, runoff=runoff, runoff_C_range=runoff_C_range, hm=hm, hm_range=hm_rng,
                d_canopy=d_canopy, qty=qty, n_trees=n_trees, perm_area=perm_area,
                runoff_basis=f"캠퍼스 = 학교 0.40, OSM 캠퍼스 도로(폭 {CAMPUS_ROAD_W:.0f}m 가정) = 도로 0.85",
                lulc_basis="Sentinel-2 NDVI 3분류(≥0.5 수목 · 0.3~0.5 초지 · <0.3 건물·포장) + OSM 캠퍼스 도로")


def se(p, n=N_ITREE):
    return float(np.sqrt(p * (1 - p) / n))


def build(sid, m):
    sat = SAT[sid]
    s2, l9 = sat["s2"], sat["l9"]
    area = m["area_ha"]
    costs = {}
    for k in ("A", "B", "C"):
        trees = m["n_trees"] if k in ("B", "C") else 0
        perm = m["perm_area"] if k == "C" else 0
        build_c = trees * UNIT["가로수 식재(원/주)"] + perm * UNIT["투수포장 추가 조성(원/㎡, 일반 포장 대비)"]
        keep_c = trees * UNIT["가로수 유지관리(원/주·년)"] + perm * UNIT["투수포장 유지관리(원/㎡·년)"]
        costs[k] = (build_c / 1e6 / area, keep_c / 1e6 / area, build_c, keep_c)

    ndvi_txt = f"Sentinel-2 L2A {s2['id']} · 취득 {s2['date']} · 경계 안 구름 {s2['local_cloud']:.1f}%(장면 {s2['scene_cloud']:.1f}%)"
    lst_txt = f"Landsat 9 C2 L2 ST_B10 {l9['id']} · 취득 {l9['date']} {l9['time_utc']} UTC · 경계 안 구름 {l9['local_cloud']:.1f}%"
    ccs = [
        {"지표": "캐노피 피복률", "값": None, "오차·가정 폭": "± SE = √(p(1−p)/500)", "해상도": "500점 판독",
         "출처·취득일": "i-Tree Canopy · 판독일 기입", "조회일": "판독일 기입",
         "비고": "빈칸 사유: i-Tree 500점 판독 대기(학생 판독 후 입력)",
         "대안": {"A": "판독값 p", "B": f"p + {100 * m['d_canopy']:.1f}%p(가로수 수관)", "C": f"p + {100 * m['d_canopy']:.1f}%p(가로수 수관)"}},
        {"지표": "NDVI 평균", "값": round(sat["ndvi"]["mean"], 3), "오차·가정 폭": f"화소 표준편차 {sat['ndvi']['sd']:.3f} (n = {sat['ndvi']['n']:,})",
         "해상도": "10m 화소", "출처·취득일": ndvi_txt, "조회일": QUERIED_ON, "비고": "Planetary Computer 공개 미러(CDSE 대체)",
         "대안": {k: f"{sat['ndvi']['mean']:.3f}(동일 장면)" for k in "ABC"}},
        {"지표": "지표온도", "값": round(sat["lst"]["mean"], 1), "오차·가정 폭": f"화소 표준편차 {sat['lst']['sd']:.1f}℃ · 취득 시각 1회분",
         "해상도": "30m 격자", "출처·취득일": lst_txt, "조회일": QUERIED_ON, "비고": "LST ≠ 기온 · Planetary Computer 공개 미러(USGS 대체)",
         "대안": {k: f"{sat['lst']['mean']:.1f}℃(동일 장면)" for k in "ABC"}},
        {"지표": "가중 유출계수", "값": round(m["runoff"]["A"], 3),
         "오차·가정 폭": f"투수포장 0.30 가정(대안 C {m['runoff_C_range'][0]:.3f}~{m['runoff_C_range'][1]:.3f})",
         "해상도": "용도별 면적", "출처·취득일": RUNOFF_NOTE, "조회일": QUERIED_ON, "비고": m["runoff_basis"],
         "대안": {k: f"{m['runoff'][k]:.3f}" for k in "ABC"}},
        {"지표": "냉각 지수 HM", "값": round(m["hm"]["A"], 3),
         "오차·가정 폭": f"그늘 가중치 0.6 ± 0.1 → {m['hm_range']['A'][0]:.3f}~{m['hm_range']['A'][1]:.3f}",
         "해상도": "10m 화소", "출처·취득일": "InVEST 3.20.2 User Guide 식 파이썬 재구현 · CC 0.6·0.2·0.2 · d_cool 450m · 생물물리 값 가정",
         "조회일": QUERIED_ON, "비고": m["lulc_basis"] + " · natcap.invest 미실행(Python 3.14 휠 없음)",
         "대안": {k: f"{m['hm'][k]:.3f}" for k in "ABC"}},
    ]
    # 대안 비교 서식(6행) — 캐노피는 판독값 입력 전까지 빈칸
    rows = {
        "캐노피 피복률(%)": {"기준선": None, "A": None, "B": None, "C": None, "unc": "± 2·SE", "src": "i-Tree 500점(판독 대기) + 가로수 수관 계산"},
        "NDVI 평균": {"기준선": sat["ndvi"]["mean"], **{k: sat["ndvi"]["mean"] for k in "ABC"}, "unc": "동일 장면", "src": f"S2 L2A 10m · {s2['date']}"},
        "지표온도(℃)": {"기준선": sat["lst"]["mean"], **{k: sat["lst"]["mean"] for k in "ABC"}, "unc": "동일 장면", "src": f"Landsat 9 ST 30m · {l9['date']}"},
        "가중 유출계수": {"기준선": m["runoff"]["A"], **{k: m["runoff"][k] for k in "ABC"},
                    "unc": f"C {m['runoff_C_range'][0]:.3f}~{m['runoff_C_range'][1]:.3f}", "src": "표 9-11 · 투수포장 0.30 가정"},
        "조성비(백만원/ha)": {"기준선": 0.0, **{k: costs[k][0] for k in "ABC"}, "unc": "가정 단가", "src": UNIT_NOTE},
        "유지관리비(백만원/ha·년)": {"기준선": 0.0, **{k: costs[k][1] for k in "ABC"}, "unc": "가정 단가", "src": UNIT_NOTE},
    }
    return {"ccs": ccs, "matrix_rows": rows, "model": m, "costs": costs}


out = {"weights": WEIGHTS, "scale": SCALE, "alts": ALTS, "unit": UNIT, "unit_note": UNIT_NOTE, "bio": BIO,
       "runoff_table": RUNOFF, "perm_share": PERM_SHARE, "perm_range": PERM_RANGE, "crown": CROWN,
       "tree_spacing": TREE_SPACING, "n_itree": N_ITREE, "sites": {}}
for sid, fn in (("dongtan", dongtan), ("cheonan", cheonan)):
    m = fn()
    out["sites"][sid] = build(sid, m)
    print(sid, {k: round(v, 3) for k, v in m["runoff"].items()}, {k: round(v, 3) for k, v in m["hm"].items()},
          f"Δcanopy {100 * m['d_canopy']:.2f}%p", m["qty"])
write_json(OUT / "ccs.json", out)
