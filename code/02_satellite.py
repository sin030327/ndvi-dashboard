"""02 — 실측 위성값: Sentinel-2 L2A NDVI(10m) · Landsat 9 C2 L2 지표온도(30m)

자료 경로(대체 사유는 보고서에 기록)
  슬라이드 기준 경로는 CDSE(Sentinel-2)·USGS EarthExplorer(Landsat)다. 이번 실행은 계정 없이
  같은 산출물(ESA Sentinel-2 L2A · USGS Landsat Collection 2 Level-2)을 제공하는
  Microsoft Planetary Computer 공개 미러를 썼다. 장면 ID는 원 산출물 ID와 같다.
  - STAC 검색 : https://planetarycomputer.microsoft.com/api/stac/v1/search
  - 화소 추출 : https://planetarycomputer.microsoft.com/api/data/v1/item/bbox/...npy (서버에서 원 격자 그대로 잘라 받음)

장면 선택 규칙(사전 고정)
  기간 2026-06-01 ~ 2026-09-30(잎이 있는 시기) · 경계 안 구름·그림자 비율(장면 전체 구름량이 아님)이
  가장 낮은 Sentinel-2 × Landsat 9 쌍(구름은 QA 기준 · ST_B10 값 없는 화소 비율은 st_gap·coverage로 따로 기록) · 두 장면 날짜 차 ≤ 5일 · 동률이면 8월 1일에 가까운 쌍
"""
import base64
import io
import json
from datetime import date

import numpy as np
import requests
import shapely
from shapely.geometry import Point
from shapely import contains_xy

from common import OUT, SITES, QUERIED_ON, T_4326_UTM, T_UTM_4326, site_geom, write_json

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
DATA_API = "https://planetarycomputer.microsoft.com/api/data/v1/item/bbox"
PERIOD = "2026-06-01/2026-09-30"
MAX_GAP_DAYS = 5
NDVI_TH = 0.3
S = requests.Session()


def stac(collection, bbox, extra=None):
    q = {"collections": [collection], "bbox": bbox, "datetime": PERIOD, "limit": 100}
    if extra:
        q["query"] = extra
    r = S.post(STAC, json=q, timeout=90)
    r.raise_for_status()
    return r.json()["features"]


def crop(collection, item, assets, b, res):
    """UTM 52N 격자에 맞춘 bbox 를 원 해상도로 잘라 받음 → (밴드…, 마스크) 배열"""
    w, h = round((b[2] - b[0]) / res), round((b[3] - b[1]) / res)
    url = f"{DATA_API}/{b[0]},{b[1]},{b[2]},{b[3]}/{w}x{h}.npy"
    params = {"collection": collection, "item": item, "assets": assets,
              "coord_crs": "epsg:32652", "dst_crs": "epsg:32652", "resampling": "nearest"}
    for _ in range(3):
        r = S.get(url, params=params, timeout=180)
        if r.status_code == 200:
            return np.load(io.BytesIO(r.content))
    r.raise_for_status()


def snap(bounds, res, off):
    """격자 원점(off)에 맞춰 bbox 를 바깥쪽으로 정렬 — 원 화소와 정확히 겹치게"""
    minx, miny, maxx, maxy = bounds
    f = lambda v: np.floor((v - off) / res) * res + off
    c = lambda v: np.ceil((v - off) / res) * res + off
    return (float(f(minx - res)), float(f(miny - res)), float(c(maxx + res)), float(c(maxy + res)))


def inside_mask(geom_utm, b, res, shape_hw):
    h, w = shape_hw
    xs = b[0] + res * (np.arange(w) + 0.5)
    ys = b[3] - res * (np.arange(h) + 0.5)
    X, Y = np.meshgrid(xs, ys)
    return contains_xy(geom_utm, X, Y), X, Y


def b64(arr, dtype):
    return base64.b64encode(np.ascontiguousarray(arr, dtype=dtype).tobytes()).decode()


def latlon_grid(geom4326, res_m):
    """지도 표시용 위경도 정렬 격자 — 화소 중심의 위경도 → UTM 좌표"""
    minx, miny, maxx, maxy = geom4326.bounds
    lat0 = (miny + maxy) / 2
    dlat = res_m / 111320
    dlng = res_m / (111320 * np.cos(np.radians(lat0)))
    pad = 2
    north, west = maxy + pad * dlat, minx - pad * dlng
    h = int(np.ceil((maxy - miny) / dlat)) + 2 * pad
    w = int(np.ceil((maxx - minx) / dlng)) + 2 * pad
    lats = north - dlat * (np.arange(h) + 0.5)
    lngs = west + dlng * (np.arange(w) + 0.5)
    LNG, LAT = np.meshgrid(lngs, lats)
    ux, uy = T_4326_UTM.transform(LNG, LAT)
    inside = contains_xy(geom4326, LNG, LAT)
    return dict(north=north, west=west, dlat=dlat, dlng=dlng, w=w, h=h), ux, uy, inside


def sample(native, b, res, ux, uy):
    h, w = native.shape
    ci = np.floor((ux - b[0]) / res).astype(int)
    ri = np.floor((b[3] - uy) / res).astype(int)
    ok = (ci >= 0) & (ci < w) & (ri >= 0) & (ri < h)
    out = np.full(ux.shape, np.nan)
    out[ok] = native[ri[ok], ci[ok]]
    return out


def days(a, b):
    return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)


result = {}
for sid in SITES:
    g4326 = site_geom(sid, 4326)
    gutm = site_geom(sid, 32652)
    bbox_ll = list(g4326.bounds)
    b10 = snap(gutm.bounds, 10, 0)
    b30 = snap(gutm.bounds, 30, 15)

    # ── 후보 장면과 경계 안 구름 비율 ──
    s2c = []
    for f in stac("sentinel-2-l2a", bbox_ll, {"eo:cloud_cover": {"lt": 70}}):
        a = crop("sentinel-2-l2a", f["id"], ["SCL"], b10, 10)
        ins, _, _ = inside_mask(gutm, b10, 10, a.shape[1:])
        scl = a[0][ins]
        bad = np.isin(scl, [0, 1, 3, 8, 9, 10]) | (a[-1][ins] == 0)
        s2c.append({"id": f["id"], "date": f["properties"]["datetime"][:10],
                    "scene_cloud": round(f["properties"]["eo:cloud_cover"], 2),
                    "local_cloud": round(100 * bad.mean(), 2),
                    "baseline": f["properties"].get("s2:processing_baseline", ""),
                    "tile": f["properties"].get("s2:mgrs_tile", "")})
    l9c = []
    for f in stac("landsat-c2-l2", bbox_ll, {"platform": {"eq": "landsat-9"}, "eo:cloud_cover": {"lt": 70}}):
        a = crop("landsat-c2-l2", f["id"], ["lwir11", "qa_pixel"], b30, 30)
        ins, _, _ = inside_mask(gutm, b30, 30, a.shape[1:])
        qa = a[1][ins].astype(np.uint16)
        bad = ((qa & 0b11111) != 0)                            # fill · 확장 구름 · 권운 · 구름 · 그림자(QA)
        st_gap = (a[0][ins] == 0)                              # QA가 맑아도 ST_B10 값이 없는 화소 — 따로 기록
        l9c.append({"id": f["id"], "date": f["properties"]["datetime"][:10],
                    "time_utc": f["properties"]["datetime"][11:16],
                    "scene_cloud": round(f["properties"]["eo:cloud_cover"], 2),
                    "local_cloud": round(100 * bad.mean(), 2), "st_gap": round(100 * st_gap.mean(), 2)})
    pairs = [(max(s["local_cloud"], l["local_cloud"]), days(s["date"], "2026-08-01"), s, l)
             for s in s2c for l in l9c if days(s["date"], l["date"]) <= MAX_GAP_DAYS]
    pairs.sort(key=lambda p: (p[0], p[1]))
    _, _, s2, l9 = pairs[0]
    print(sid, "S2", s2["id"], s2["local_cloud"], "| L9", l9["id"], l9["local_cloud"])

    # ── NDVI (10m) ──
    a = crop("sentinel-2-l2a", s2["id"], ["B04", "B08", "SCL"], b10, 10)
    off = -1000 if s2["baseline"] and float(s2["baseline"]) >= 4.0 else 0   # BOA_ADD_OFFSET(처리 기준 04.00 이상)
    red = (a[0].astype(float) + off) / 10000
    nir = (a[1].astype(float) + off) / 10000
    valid = ~np.isin(a[2], [0, 1, 3, 8, 9, 10]) & (a[-1] > 0) & ((red + nir) > 0)
    ndvi = np.where(valid, (nir - red) / np.where(valid, nir + red, 1), np.nan)
    ins10, X10, Y10 = inside_mask(gutm, b10, 10, ndvi.shape)
    v = ndvi[ins10 & valid]
    nd_stats = dict(mean=float(v.mean()), sd=float(v.std()), median=float(np.median(v)),
                    p10=float(np.percentile(v, 10)), p90=float(np.percentile(v, 90)),
                    n=int(v.size), n_total=int(ins10.sum()), green_ratio=float((v >= NDVI_TH).mean()),
                    red_mean=float(red[ins10 & valid].mean()), nir_mean=float(nir[ins10 & valid].mean()))

    # ── 지표온도 (30m) ──
    a = crop("landsat-c2-l2", l9["id"], ["lwir11", "qa_pixel"], b30, 30)
    qa = a[1].astype(np.uint16)
    lvalid = ((qa & 0b11111) == 0) & (a[-1] > 0) & (a[0] > 0)
    lst = np.where(lvalid, a[0] * 0.00341802 + 149.0 - 273.15, np.nan)
    ins30, X30, Y30 = inside_mask(gutm, b30, 30, lst.shape)
    lv = lst[ins30 & lvalid]
    lst_stats = dict(mean=float(lv.mean()), sd=float(lv.std()), min=float(lv.min()), max=float(lv.max()),
                     n=int(lv.size), n_total=int(ins30.sum()), coverage=float(lv.size / ins30.sum()))

    # NDVI ↔ LST 산점: 30m 셀 안의 10m 화소 중심(3×3) 평균
    pairs_nl = []
    rr, cc = np.nonzero(ins30 & lvalid)
    for r, c in zip(rr, cc):
        x0 = b30[0] + 30 * c
        y1 = b30[3] - 30 * r
        sel = (X10 >= x0) & (X10 < x0 + 30) & (Y10 <= y1) & (Y10 > y1 - 30) & valid
        if sel.sum() >= 5:
            pairs_nl.append([round(float(np.nanmean(ndvi[sel])), 3), round(float(lst[r, c]), 2)])
    pn = np.array(pairs_nl)
    r_nl = float(np.corrcoef(pn[:, 0], pn[:, 1])[0, 1]) if len(pn) > 3 else float("nan")

    # ── 지도 표시용 위경도 격자 ──
    grid10, ux, uy, gin = latlon_grid(g4326, 10)
    disp = sample(ndvi, b10, 10, ux, uy)
    q = np.where(np.isnan(disp), 255, np.clip(np.round((disp + 1) * 100), 0, 200)).astype(np.uint8)
    grid30, ux3, uy3, gin3 = latlon_grid(g4326, 30)
    dl = sample(lst, b30, 30, ux3, uy3)
    ql = np.where(np.isnan(dl), 65535, np.clip(np.round(dl * 100), 0, 65534)).astype(np.uint16)

    np.savez_compressed(OUT / f"sat_{sid}.npz", ndvi=ndvi, ins10=ins10, valid10=valid, b10=b10,
                        lst=lst, ins30=ins30, valid30=lvalid, b30=b30)
    result[sid] = {
        "s2": s2, "l9": l9, "s2_candidates": sorted(s2c, key=lambda x: x["date"]),
        "l9_candidates": sorted(l9c, key=lambda x: x["date"]),
        "ndvi": nd_stats, "lst": lst_stats, "ndvi_lst_r": r_nl, "ndvi_lst_pairs": pairs_nl,
        "ndvi_native_b64": b64(np.clip(np.round((v + 1) * 100), 0, 200), np.uint8),
        "grid10": {**grid10, "ndvi_b64": b64(q, np.uint8), "inside_b64": b64(gin, np.uint8)},
        "grid30": {**grid30, "lst_b64": b64(ql, np.uint16), "inside_b64": b64(gin3, np.uint8)},
        "queried_on": QUERIED_ON,
    }
    print(f"  NDVI {nd_stats['mean']:.3f} ± {nd_stats['sd']:.3f} (n={nd_stats['n']}) · "
          f"LST {lst_stats['mean']:.2f}°C (n={lst_stats['n']}) · r={r_nl:.2f}")

write_json(OUT / "satellite.json", result)
