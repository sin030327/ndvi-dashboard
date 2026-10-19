"""공통 — 경로 · 대상지 정의 · 좌표 변환 (7주차)

대상지 2곳
- dongtan : 6주차 후보지 A(장지동 남측, 250ha) — 6주차 90m 격자 mask_A 셀의 합집합
- cheonan : 상명대학교 천안캠퍼스 — OpenStreetMap way 231288273 외곽선
"""
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import box, shape, mapping
from shapely.ops import unary_union
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
OUT = ROOT / "outputs"
SUBMIT = ROOT / "제출"          # 제출용(학번 포함) — .gitignore 로 공개 저장소에서 제외
for p in (OUT, SUBMIT, RAW):
    p.mkdir(parents=True, exist_ok=True)

QUERIED_ON = "2026-10-19"        # 이번 실행의 자료 조회일

SITES = {
    "dongtan": {"name": "동탄 후보지 A · 장지동 남측", "short": "동탄 후보지 A",
                "name_it": "Dongtan, sito candidato A (Jangji-dong sud)"},
    "cheonan": {"name": "상명대학교 천안캠퍼스", "short": "천안캠퍼스",
                "name_it": "Campus di Cheonan, Sangmyung University"},
}

# 6주차 격자(EPSG:5186 중부원점, 90m) — dem90.npz 의 gx0 · gy1 · cell
_g = np.load(DATA / "dem90.npz")
GX0, GY1, CELL = float(_g["gx0"]), float(_g["gy1"]), float(_g["cell"])
MASK_A = np.load(DATA / "mask_A.npy")
PLANS = np.load(DATA / "alt_plans.npz")       # p0 대안 A · p1 대안 B · p2 대안 C (6주차)
PLAN_1 = PLANS["p2"]                          # 과제 ① '대안 1안' = 6주차 1위 대안 C · 절충
G, IND, COM, RES = 1, 2, 3, 4                 # 6주차 코드: 녹지 · 공업 · 상업업무 · 주거
LU_NAMES = {G: "공원·녹지", IND: "공업", COM: "상업·업무", RES: "주거"}

T_5186_4326 = Transformer.from_crs(5186, 4326, always_xy=True)
T_4326_5186 = Transformer.from_crs(4326, 5186, always_xy=True)
T_4326_UTM = Transformer.from_crs(4326, 32652, always_xy=True)
T_UTM_4326 = Transformer.from_crs(32652, 4326, always_xy=True)


def tf(g, t):
    return shapely.transform(g, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])))


def cell_box(r, c):
    x0 = GX0 + c * CELL
    y1 = GY1 - r * CELL
    return box(x0, y1 - CELL, x0 + CELL, y1)


def cells_union(mask):
    rr, cc = np.nonzero(mask)
    return unary_union([cell_box(r, c) for r, c in zip(rr, cc)])


def site_geom(site, crs=4326):
    """대상지 경계 (crs: 4326 · 32652 · 5186)"""
    f = json.loads((DATA / "sites.geojson").read_text(encoding="utf-8"))
    g = shape(next(x for x in f["features"] if x["properties"]["id"] == site)["geometry"])
    if crs == 4326:
        return g
    return tf(g, T_4326_UTM if crs == 32652 else T_4326_5186)


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def area_ha_utm(g):
    return g.area / 1e4
