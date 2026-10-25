"""06 — 제출 파일 만들기 (제출/ — 학번 포함, 공개 저장소 제외)

입력  data/itree_results.json  — i-Tree 판독 후 직접 채움 {"dongtan": {"n": 500, "tree": 123, "date": "2026-10-2x"}, ...}
산출  제출/7주차_보고서_도로위계_CCS결과표.pdf
      제출/7주차_결과표.xlsx · 제출/csv/*.csv
      제출/조감이미지_프롬프트_캡션.txt · 제출/i-Tree_작업안내.txt · 제출/제출_체크리스트.md
"""
import base64
import io
import csv
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from common import ROOT, OUT, DATA, SUBMIT, SITES, QUERIED_ON, site_geom

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
_tp = ROOT / "team_private.txt"   # 팀원 학번 — 공개 저장소 제외(.gitignore)
TEAM = _tp.read_text(encoding="utf-8").strip() if _tp.exists() else "(team_private.txt 에 팀원 · 학번 기입)"

SAT = json.loads((OUT / "satellite.json").read_text(encoding="utf-8"))
CCS = json.loads((OUT / "ccs.json").read_text(encoding="utf-8"))
RD = json.loads((OUT / "roads.json").read_text(encoding="utf-8"))
ITP = DATA / "itree_results.json"
if not ITP.exists():
    ITP.write_text(json.dumps({s: {"n": 500, "tree": None, "date": None} for s in SITES}, ensure_ascii=False, indent=1), encoding="utf-8")
ITREE = json.loads(ITP.read_text(encoding="utf-8"))
ALT = ["A", "B", "C"]
CSVDIR = SUBMIT / "csv"
CSVDIR.mkdir(exist_ok=True)


AIP = DATA / "canopy_ai_reading.json"   # i-Tree 대신 AI가 판독한 무작위 500점(공개 표기) — 07_ai_canopy_points.py
AIR = json.loads(AIP.read_text(encoding="utf-8")) if AIP.exists() else {}


def itree(sid):
    """캐노피 판독값 — i-Tree 결과가 있으면 우선, 없으면 AI 대체 판독(출처를 따로 표기)"""
    v = ITREE.get(sid) or {}
    if v.get("tree") is not None and v.get("n"):
        n, k = int(v["n"]), int(v["tree"])
        src, src_txt, res_txt, note = "itree", f"i-Tree Canopy · 판독 {v.get('date') or ''}", "500점 판독", ""
        date = v.get("date") or ""
    elif sid in AIR:
        a = AIR[sid]
        n, k, date = int(a["n"]), int(a["tree"]), a["read_on"]
        src = "ai"
        src_txt = f"AI 대체 판독(i-Tree 아님) · {a['imagery']} · 판독 {date}"
        res_txt = "무작위 500점(AI 판독)"
        note = "i-Tree 원본(.itrcnpy) 없음 — 같은 방식의 대체 판독, 판독자 AI(Claude)"
    else:
        return None
    p = k / n
    return {"n": n, "k": k, "p": p, "se": math.sqrt(p * (1 - p) / n), "date": date,
            "src": src, "src_txt": src_txt, "res_txt": res_txt, "note": note}


def sc(name, v):
    d, cuts = CCS["scale"][name]
    if v is None:
        return None
    return 1 + sum((v >= c) if d == "↑" else (v < c) for c in cuts)


def matrix(sid):
    s = CCS["sites"][sid]
    it = itree(sid)
    dcan = s["model"]["d_canopy"]
    rows = []
    for name, w in CCS["weights"].items():
        mr = s["matrix_rows"][name]
        r = {"name": name, "w": w, "v": {}, "s": {}, "j": {}, "unc": mr["unc"], "src": mr["src"], "pending": False}
        if name.startswith("캐노피"):
            if it:
                pB = min(1, it["p"] + dcan)
                seB = math.sqrt(pB * (1 - pB) / it["n"])
                r["v"] = {"기준선": 100 * it["p"], "A": 100 * it["p"], "B": 100 * pB, "C": 100 * pB}
                same = abs(pB - it["p"]) < 2 * max(it["se"], seB)
                r["s"]["기준선"] = r["s"]["A"] = sc(name, 100 * it["p"])
                r["s"]["B"] = r["s"]["C"] = r["s"]["A"] if same else sc(name, 100 * pB)
                r["j"] = {"B": "차이 없음" if same else "유의", "C": "차이 없음" if same else "유의"}
                r["unc"] = f"± {100 * it['se']:.1f} / {100 * seB:.1f}%p"
            else:
                r["pending"] = True
                r["v"] = {k: None for k in ["기준선"] + ALT}
        else:
            for k in ["기준선"] + ALT:
                r["v"][k] = mr[k]
                r["s"][k] = sc(name, mr[k])
            if name == "가중 유출계수":
                lo, hi = s["model"]["runoff_C_range"]
                if abs(r["v"]["C"] - r["v"]["기준선"]) < abs(hi - lo):
                    r["s"]["C"] = r["s"]["기준선"]
                    r["j"]["C"] = "가정 의존"
                else:
                    r["j"]["C"] = "가정 폭 초과"
            if name.startswith(("NDVI", "지표온도")):
                r["j"] = {k: "동일 장면" for k in ALT}
        rows.append(r)
    used = [r for r in rows if not r["pending"]]
    ws = sum(r["w"] for r in used)
    for r in used:
        r["wn"] = r["w"] / ws
    total = {k: sum(r["wn"] * r["s"][k] for r in used) for k in ALT}
    rank = sorted(ALT, key=lambda k: -total[k])
    rev = []
    for r in used:
        top = rank[0]
        others = [o for o in used if o is not r]
        T0 = lambda k: sum(o["wn"] / (1 - r["wn"]) * o["s"][k] for o in others)
        best = None
        for k in ALT:
            if k == top or r["s"][top] == r["s"][k]:
                continue
            a = T0(top) - T0(k)
            b = (r["s"][top] - r["s"][k]) - a
            if abs(b) < 1e-12:
                continue
            t = -a / b
            if 0 <= t <= 1 and abs(t - r["wn"]) > 1e-9 and (best is None or abs(t - r["wn"]) < abs(best[0] - r["wn"])):
                best = (t, k)
        rev.append((r["name"], r["wn"], best))
    return rows, total, rank, rev, it is None


def ccs_rows(sid):
    s = CCS["sites"][sid]
    it = itree(sid)
    out = []
    for i, r in enumerate(s["ccs"]):
        r = {**r, "대안": dict(r["대안"])}
        if i == 0 and it:
            dcan = s["model"]["d_canopy"]
            pB = min(1, it["p"] + dcan)
            seB = math.sqrt(pB * (1 - pB) / it["n"])
            sig = "유의" if abs(pB - it["p"]) >= 2 * max(it["se"], seB) else "차이 없음"
            r.update({"값": f"{100 * it['p']:.1f}%", "오차·가정 폭": f"± {100 * it['se']:.2f}%p (SE, N = {it['n']})",
                      "해상도": it["res_txt"], "출처·취득일": it["src_txt"], "조회일": it["date"],
                      "비고": f"{it['k']}/{it['n']}점 수목" + (f" · {it['note']}" if it["note"] else "")})
            r["대안"] = {"A": f"{100 * it['p']:.1f} ± {100 * it['se']:.1f}",
                        "B": f"{100 * pB:.1f} ± {100 * seB:.1f} ({sig})", "C": f"{100 * pB:.1f} ± {100 * seB:.1f} ({sig})"}
        elif i == 0 and sid == "cheonan":
            r["비고"] = "빈칸 사유: 판독 미실시 — 과제 대상지는 동탄 후보지 A, 천안캠퍼스는 추가 비교"
        out.append(r)
    return out


ALTN = {k: v for k, v in zip(ALT, CCS["alts"])}

# ── 그림 ─────────────────────────────────────────────────────────────
cmap = LinearSegmentedColormap.from_list("ndvi", [(0, "#785a46"), (0.5, "#c8be a0".replace(" ", "")), (0.6, "#ebe196"),
                                                 (0.7, "#96c864"), (0.8, "#3c9646"), (1, "#0a5028")])
figs = {}
for sid in SITES:
    z = np.load(OUT / f"sat_{sid}.npz")
    g = site_geom(sid, 32652)
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.9), dpi=140, gridspec_kw={"width_ratios": [1, 1, 1.05]})
    b10, b30 = z["b10"], z["b30"]
    im = axs[0].imshow(z["ndvi"], cmap=cmap, vmin=-1, vmax=1, extent=[b10[0], b10[2], b10[1], b10[3]], interpolation="nearest")
    im2 = axs[1].imshow(z["lst"], cmap="inferno", extent=[b30[0], b30[2], b30[1], b30[3]], interpolation="nearest")
    for ax, t in ((axs[0], "NDVI (Sentinel-2 L2A 10m)"), (axs[1], "지표온도 ℃ (Landsat 9 ST 30m)")):
        for p in getattr(g, "geoms", [g]):
            ax.plot(*p.exterior.xy, color="#ff2a1a", lw=1.4)
        ax.set_title(t, fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
        minx, miny, maxx, maxy = g.bounds
        ax.set_xlim(minx - 60, maxx + 60); ax.set_ylim(miny - 60, maxy + 60)
    fig.colorbar(im, ax=axs[0], fraction=0.046, pad=0.02)
    fig.colorbar(im2, ax=axs[1], fraction=0.046, pad=0.02)
    pr = np.array(SAT[sid]["ndvi_lst_pairs"])
    axs[2].scatter(pr[:, 0], pr[:, 1], s=6, c="#e8642c", alpha=.7)
    axs[2].set_xlabel("NDVI (30m 셀 평균)"); axs[2].set_ylabel("LST ℃")
    axs[2].set_title(f"NDVI–LST  r = {SAT[sid]['ndvi_lst_r']:.2f}  (셀 {len(pr)}개)", fontsize=9)
    axs[2].grid(alpha=.3)
    fig.suptitle(SITES[sid]["name"], fontsize=11)
    fig.tight_layout()
    fp = OUT / f"fig_sat_{sid}.png"
    fig.savefig(fp)
    plt.close(fig)
    figs[sid] = fp


def img64(p, jpeg=False, maxw=1600):
    if not jpeg:
        return "data:image/png;base64," + base64.b64encode(Path(p).read_bytes()).decode()
    from PIL import Image
    im = Image.open(p).convert("RGB")
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


# ── CSV · xlsx ───────────────────────────────────────────────────────
def write_csv(name, rows):
    with open(CSVDIR / name, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(rows)


wb = Workbook()
HDR = PatternFill("solid", fgColor="1F2A5C")


def sheet(title, rows, widths=None, first=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = title[:31]
    for r in rows:
        ws.append([("" if v is None else v) for v in r])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HDR
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for i, col in enumerate(ws.columns, 1):
        w = (widths or {}).get(i) or min(60, max(10, max(len(str(c.value or "")) for c in col) * 1.15))
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    return ws


# ① 도로율
keys = list(RD["table"][0].keys())
road_rows = [keys] + [[r[k] for k in keys] for r in RD["table"]]
sheet("①도로율_대안1안", road_rows, first=True)
write_csv("1_도로율_대안1안.csv", road_rows)
seg_rows = [list(RD["segments"][0].keys())] + [list(s.values()) for s in RD["segments"]]
sheet("①도로_구간", seg_rows)
write_csv("1_도로_구간.csv", seg_rows)
cross_keys = ["규모", "폭", "차로", "중앙분리대", "정차대", "자전거도로", "보도", "설계속도"]
cross_rows = [["위계", "배치간격(m)"] + cross_keys] + [[t, RD["spacing"][t]] + [RD["cross"][t][k] for k in cross_keys] for t in RD["cross"]]
sheet("①횡단구성", cross_rows)
write_csv("1_횡단구성.csv", cross_rows)

# ③ 지표 ⑦ 카탈로그
cat = [["대상", "지표", "값", "오차", "해상도", "출처", "장면 ID", "취득일", "경계 안 구름(%)", "조회일", "비고"]]
for sid in SITES:
    s, it = SAT[sid], itree(sid)
    cat.append([SITES[sid]["name"], "캐노피 피복률(%)", round(100 * it["p"], 2) if it else None,
                f"± {100 * it['se']:.2f}%p SE" if it else "", it["res_txt"] if it else "500점 판독", it["src_txt"] if it else "i-Tree Canopy", "", it["date"] if it else "",
                "", it["date"] if it else "", it["note"] if it else ("빈칸 — 판독 미실시(과제 대상지는 동탄 후보지 A, 천안캠퍼스는 추가 비교)" if sid == "cheonan" else "빈칸 — i-Tree 판독 대기")])
    cat.append([SITES[sid]["name"], "NDVI 평균", round(s["ndvi"]["mean"], 4), f"화소 SD {s['ndvi']['sd']:.4f} · n {s['ndvi']['n']}", "10m",
                "Sentinel-2 L2A (Planetary Computer 공개 미러)", s["s2"]["id"], s["s2"]["date"], s["s2"]["local_cloud"], QUERIED_ON,
                f"임계값 0.3 이상 화소 {100 * s['ndvi']['green_ratio']:.1f}%"])
    cat.append([SITES[sid]["name"], "지표온도(℃)", round(s["lst"]["mean"], 2), f"화소 SD {s['lst']['sd']:.2f} · n {s['lst']['n']}", "30m",
                "Landsat 9 C2 L2 ST_B10 (Planetary Computer 공개 미러)", s["l9"]["id"], f"{s['l9']['date']} {s['l9']['time_utc']} UTC",
                s["l9"]["local_cloud"], QUERIED_ON, "LST ≠ 기온" + (f" · ST 산출 화소 {100 * s['lst']['coverage']:.0f}%만(나머지 ST_B10 값 없음, 원인 미확인) — 경계 일부 대표" if s["lst"]["coverage"] < 0.99 else "")])
sheet("③지표7_카탈로그", cat)
write_csv("3_지표7_카탈로그.csv", cat)

# ④ CCS 결과표 · 대안 비교
mx_out = {}
for sid in SITES:
    short = SITES[sid]["short"].replace(" ", "")
    rows = [["지표", "값", "오차·가정 폭", "해상도", "출처·취득일", "조회일", "대안 A · 현황 유지", "대안 B · 가로수 열식", "대안 C · 가로수 + 투수포장", "비고"]]
    for r in ccs_rows(sid):
        rows.append([r["지표"], r["값"], r["오차·가정 폭"], r["해상도"], r["출처·취득일"], r["조회일"], r["대안"]["A"], r["대안"]["B"], r["대안"]["C"], r.get("비고", "")])
    sheet(f"④CCS결과표_{short}", rows)
    write_csv(f"4_CCS_1차결과표_{short}.csv", rows)
    M = matrix(sid)
    mx_out[sid] = M
    mrows, total, rank, rev, prov = M
    mx = [["지표", "방향", "가중치(사전 고정)", "적용 가중치", "기준선 값", "기준선 점수", "대안 A 값", "A 점수", "대안 B 값", "B 점수", "B 판정",
           "대안 C 값", "C 점수", "C 판정", "오차·가정", "출처"]]
    for r in mrows:
        v = lambda k: None if r["v"][k] is None else round(r["v"][k], 4)
        mx.append([r["name"], CCS["scale"][r["name"]][0], r["w"], "제외(판독 대기)" if r["pending"] else round(r["wn"], 3),
                   v("기준선"), r["s"].get("기준선"), v("A"), r["s"].get("A"), v("B"), r["s"].get("B"), r["j"].get("B", ""),
                   v("C"), r["s"].get("C"), r["j"].get("C", ""), r["unc"], r["src"]])
    mx.append(["가중 합계", "", 1.0, "", "", "", "", round(total["A"], 3), "", round(total["B"], 3), "", "", round(total["C"], 3), "",
               "잠정(캐노피 제외)" if prov else "확정", "순위: " + " > ".join(ALTN[k] for k in rank)])
    mx.append([])
    mx.append(["역전점 — 지표", "현재 가중치", "역전 가중치", "역전 후 1위", "여유폭(%p)"])
    for name, wn, best in rev:
        mx.append([name, round(wn, 3), round(best[0], 3) if best else "0~1 범위 역전 없음", ALTN[best[1]] if best else "", round(100 * abs(best[0] - wn), 1) if best else ""])
    mx.append([])
    mx.append(["5점 척도 구간(사전 고정)", "방향", "1|2|3|4|5 경계값"])
    for name, (d, cuts) in CCS["scale"].items():
        mx.append([name, d, " | ".join(str(c) for c in cuts)])
    sheet(f"④대안비교_{short}", mx)
    write_csv(f"4_대안비교서식_{short}.csv", mx)

# 유의성
sig = [["N", "p = 0.2 SE(%p)", "p = 0.3 SE(%p)", "p = 0.5 SE(%p)", "SE × 2 (p = 0.3)"]]
for n in (100, 250, 500, 1000, 2000):
    sig.append([n] + [round(100 * math.sqrt(p * (1 - p) / n), 2) for p in (0.2, 0.3, 0.5)] + [round(200 * math.sqrt(0.21 / n), 2)])
p1, p2, n = 0.20, 0.23, 500
se1, se2 = math.sqrt(p1 * (1 - p1) / n), math.sqrt(p2 * (1 - p2) / n)
z = (p2 - p1) / math.sqrt(se1 ** 2 + se2 ** 2)
sig += [[], ["준비 질문 — 500점 · 캐노피 20% 대 23%(차이 3%p)"],
        ["대안 1", f"{100 * p1:.1f} ± {100 * se1:.2f}%"], ["대안 2", f"{100 * p2:.1f} ± {100 * se2:.2f}%"],
        ["차이", "3.0%p"], ["SE × 2(큰 쪽)", f"{200 * max(se1, se2):.2f}%p"], ["판정", "차이 없음(3.0 < 3.76)"],
        ["두 표본 z", f"{z:.2f} (< 1.96, 95% 유의 아님)"],
        ["필요 표본(3%p를 유의로)", f"약 {math.ceil(4 * p2 * (1 - p2) / 0.03 ** 2):,}점"]]
sheet("유의성_준비질문", sig)
write_csv("유의성_준비질문.csv", sig)

# 가정·출처
assume = [["항목", "값", "근거·비고"],
          ["대안 1안", "6주차 대안 C · 절충", "6주차 매트릭스 1위(3.35)"],
          ["배치간격", "주간선 1,000 · 보조간선 500 · 집산 250m", "규칙 제10조제3호"],
          ["횡단 폭", "35 · 25 · 20m", "제10조제7호 — 보도·자전거·분리대·정차대 포함(구성은 표)"],
          ["도로율 기준", "주거 15~30(간선 8~15) · 상업 25~35(10~15) · 공업 8~20(4~10)%", "제11조제1항, 상한 '미만'"],
          ["장면 선택", "2026-06-01~09-30, 경계 안 구름 최소 쌍, 날짜 차 ≤ 5일", "사전 고정"],
          ["자료 경로 대체", "Microsoft Planetary Computer 공개 미러", "CDSE·USGS 계정 없이 같은 산출물(장면 ID 동일)"],
          ["가로수", f"간선 양쪽 2열 · 수관폭 {CCS['crown']:.0f}m · 간격 {CCS['tree_spacing']:.0f}m", "슬라이드 50 가정"],
          ["투수포장", f"집산(캠퍼스) 도로 포장의 {100 * CCS['perm_share']:.0f}% · 유출계수 0.30 (가정 폭 {CCS['perm_range'][0]}~{CCS['perm_range'][1]})", "슬라이드 49·50"],
          ["유출계수 표", json.dumps(CCS["runoff_table"], ensure_ascii=False), "원본 43번 표 9-11 · 공업은 상업 0.80 준용(가정)"],
          ["InVEST", "CC 0.6·0.2·0.2 · d_cool 450m · ET0 균일", "User Guide 식 재구현(natcap.invest 미실행)"],
          ["생물물리 표", json.dumps(CCS["bio"], ensure_ascii=False), "shade · kc · albedo · green_area — 가정"],
          ["단가", json.dumps(CCS["unit"], ensure_ascii=False), CCS["unit_note"]],
          ["가중치", json.dumps(CCS["weights"], ensure_ascii=False), "대안 기입 전 고정 — 팀 승인 필요"]]
sheet("가정·출처", assume)
write_csv("가정_출처.csv", assume)
xlsx = SUBMIT / "7주차_결과표.xlsx"
wb.save(xlsx)
print("saved", xlsx)

# ── 조감 이미지 · 안내 문서 ─────────────────────────────────────────
q = CCS["sites"]["dongtan"]["model"]["qty"]
decision = (f"대안 C — 주간선·보조간선 {q['가로수 연장(km)']}km 양쪽 가로수 2열(약 {q['가로수(주)']:,}주, 수관폭 8m), "
            f"집산도로 포장 {q['투수포장(㎡)']:,}㎡(30%) 투수포장 전환, 저지대 하천변 갈대 저류지 배치.")
prompt = ("Bright midday bird's-eye view (45-degree aerial) of a new low-rise and mid-rise residential district on gently rolling farmland "
          "in Dongtan, Hwaseong, South Korea. A 35 m arterial boulevard and 25 m secondary arterials lined on both sides with two continuous "
          "rows of mature street trees (crown about 8 m), 20 m collector streets with light-grey permeable paving on sidewalks and parking lanes, "
          "a reed retention pond in the low ground beside a small stream, green park corridor kept between neighbourhoods. Clear blue sky, "
          "soft natural daylight, high brightness, realistic urban planning visualisation, no text, no logos, no people close-up.")
caption = ("AI 생성 이미지(도구명 · 생성일 기입) — 동탄 후보지 A 대안 C(가로수 2열 · 투수포장 · 저류지)의 개념 시각화이며 실사가 아님. "
           "이미지 속 수목 수·면적은 값이 아님 — 수치는 CCS 1차 결과표 참조.")
(SUBMIT / "조감이미지_프롬프트_캡션.txt").write_text(
    f"[결정 문장]\n{decision}\n\n[프롬프트 — 영문]\n{prompt}\n\n[캡션]\n{caption}\n\n"
    "[생성 규칙 — 슬라이드 55]\n- 밝은 주광 장면(평균 밝기 130 이상), 어두우면 다시 생성\n- 생성 도구·날짜·크레딧을 카탈로그에 기록\n"
    "- 완성 이미지를 제출/조감이미지.png(또는 .jpg)로 저장하면 보고서에 자동으로 들어갑니다(06_submission.py 재실행)\n", encoding="utf-8")
(SUBMIT / "i-Tree_작업안내.txt").write_text("""i-Tree Canopy 500점 판독 — 대상지 2곳(동탄 후보지 A · 천안캠퍼스)

1. https://canopy.itreetools.org 접속 → Get Started
2. 경계: 'Load Shapefile Boundary' → 제출/i-Tree_경계/dongtan_boundary.zip (천안은 cheonan_boundary.zip) 업로드
   (좌표계 WGS84, 경계 = 통계 모집단 — 대시보드·결과표와 같은 경계)
3. 피복 분류: 단순모드 Tree / Non-Tree (토지이용모드를 쓰면 Tree 항목 수를 그대로 기록)
4. 지역·단위: Asia › South Korea(없으면 가장 가까운 지역) · 통화 KRW · 미터법
5. 점 판독: + 로 점 생성 → 노란 십자 자리 피복 선택 → Save & Create New … 500점까지
6. 저장: Project › Save → .itrcnpy  /  Report › Print → PDF  /  Report › Export to CSV
   파일 이름 예: 7주차_iTree_동탄A.itrcnpy · 7주차_iTree_동탄A.pdf · 7주차_iTree_동탄A.csv → 제출/ 폴더에 넣기
7. 결과 입력: data/itree_results.json 의 tree(수목 점 수)·date(판독일) 채우기
     {"dongtan": {"n": 500, "tree": 123, "date": "2026-10-22"}, "cheonan": {...}}
   그다음  python code/06_submission.py  → 결과표 xlsx·csv·보고서 PDF가 판독값으로 다시 만들어짐
   (대시보드에서는 '② i-Tree 500점 판독 결과' 칸에 같은 값을 넣으면 화면이 바로 바뀜)
8. 점검(슬라이드 54): 2인이 50점을 중복 판독해 일치율 기록 권장
""", encoding="utf-8")

# ── 보고서 HTML → PDF ────────────────────────────────────────────────
def table(rows, cls=""):
    h = "".join(f"<th>{c}</th>" for c in rows[0])
    b = "".join("<tr>" + "".join(f"<td>{'' if c is None else c}</td>" for c in r) + "</tr>" for r in rows[1:])
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


aerial = next((p for p in [SUBMIT / "조감이미지.png", SUBMIT / "조감이미지.jpg", SUBMIT / "조감이미지.jpeg"] if p.exists()), None)
if aerial:
    aerial_html = f'<img class="fig" src="{img64(aerial, jpeg=True)}"><p class="cap">{caption}</p>'
else:
    aerial_html = '<div class="todo">이미지 미첨부 — 아래 프롬프트로 밝은 장면 1장을 생성해 제출/조감이미지.png로 저장한 뒤 06_submission.py를 다시 실행하면 이 자리에 들어갑니다.</div>'

# AI 대체 판독 근거 — 판독 조각 20장 · 점별 분류 CSV
ai_html = ""
if "dongtan" in AIR:
    import shutil
    ev = SUBMIT / "캐노피_대체판독_동탄"
    ev.mkdir(exist_ok=True)
    for f in (OUT / "canopy_sheets").glob("sheet_*.png"):
        shutil.copy(f, ev / f.name)
    a = AIR["dongtan"]
    with open(ev / "판독점_500_분류.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "lat", "lon", "class"])
        for q in a["points"]:
            w.writerow([q["id"], q["lat"], q["lon"], q["class"]])
    ai_html = (f"<div class='box'><b>대체 판독 방법(공개 표기)</b> — {a['method']}. 판독자 {a['reader']}. 영상 {a['imagery']}. "
               f"무작위 점 시드 {a['seed']}(재현 가능). 판정 규칙: {a['rule']}. 점별 분류와 판독 조각 20장은 제출/캐노피_대체판독_동탄/에 있다. "
               "잎 없는 시기 영상이라 낙엽수 수관은 갈색 질감으로 판독했고, 그림자 속 점은 주변 질감으로 판단해 판독자 오차가 있을 수 있다.</div>"
               f"<img class='fig' src='{img64(OUT / 'canopy_sheets' / 'sheet_01.png', jpeg=True, maxw=930)}' style='width:62%'>"
               "<p class='cap'>판독 조각 예시(1~25번) — 중앙 십자 = 판독 위치, 한 조각 약 60m.</p>")

sec_ccs = ""
for sid in SITES:
    rows = [["지표", "값", "오차·가정 폭", "해상도", "출처·취득일", "조회일", "대안 A", "대안 B", "대안 C"]]
    for r in ccs_rows(sid):
        rows.append([f"<b>{r['지표']}</b><div class='s'>{r.get('비고', '')}</div>", r["값"] if r["값"] is not None else "<span class='blank'>빈칸</span>",
                     r["오차·가정 폭"], r["해상도"], f"<span class='s'>{r['출처·취득일']}</span>", r["조회일"], r["대안"]["A"], r["대안"]["B"], r["대안"]["C"]])
    mrows, total, rank, rev, prov = mx_out[sid]
    mx = [["지표", "가중치", "기준선", "대안 A", "대안 B", "대안 C", "오차·출처"]]
    for r in mrows:
        def cell(k):
            if r["pending"]:
                return "판독 대기"
            v = r["v"][k]
            fv = f"{v:.3f}" if r["name"].startswith("NDVI") or r["name"] == "가중 유출계수" else f"{v:.2f}" if r["name"].startswith(("조성", "유지")) else f"{v:.1f}"
            return f"<b>{r['s'][k]}</b> <span class='s'>({fv}){' · ' + r['j'][k] if r['j'].get(k) else ''}</span>"
        mx.append([r["name"], "제외" if r["pending"] else f"{r['wn']:.2f}", cell("기준선"), cell("A"), cell("B"), cell("C"), f"<span class='s'>{r['unc']} · {r['src']}</span>"])
    mx.append(["<b>가중 합계</b>", "1.00", "—"] + [f"<b>{total[k]:.2f}</b> ({rank.index(k) + 1}위)" for k in ALT] + ["잠정(캐노피 제외)" if prov else "확정"])
    rv = [["지표", "현재 가중치", "역전 가중치", "역전 후 1위", "여유폭"]] + [
        [n_, f"{w:.3f}", f"{b[0]:.3f}" if b else "0~1 범위 역전 없음", ALTN[b[1]] if b else "", f"{100 * abs(b[0] - w):.1f}%p" if b else ""] for n_, w, b in rev]
    m = CCS["sites"][sid]["model"]
    sec_ccs += f"""
<h3>{SITES[sid]['name']}</h3>
{table(rows, 'small')}
<p class="s">대안 A 현황 유지 · B 가로수 열식(간선 양쪽 2열, 수관폭 8m · 가로수 {m['qty']['가로수(주)']:,}주) · C 가로수 + 투수포장({m['qty']['투수포장(㎡)']:,}㎡).
캐노피 증가분은 가로수 수관 면적 비율 {100 * m['d_canopy']:.1f}%p(기존 녹지·수목 위 수관 제외). NDVI·지표온도는 설계안을 위성으로 잴 수 없어 같은 장면 값.</p>
<h4>대안 비교 서식 — {'잠정 순위(캐노피 판독 대기, 나머지 가중치 재정규화)' if prov else '순위 확정'}: {' > '.join(ALTN[k] for k in rank)}</h4>
{table(mx, 'small')}
{table(rv, 'small')}
"""

it_txt = []
for sid in SITES:
    it = itree(sid)
    it_txt.append(f"<li><b>{SITES[sid]['name']}</b> — " + (f"{'<b>AI 대체 판독(i-Tree 아님)</b> — ' if it['src'] == 'ai' else ''}수목 {it['k']}/{it['n']}점 = <b>{100 * it['p']:.1f} ± {100 * it['se']:.2f}%</b> (판독 {it['date']}), "
                  f"캐노피 면적 {SAT and CCS['sites'][sid]['model']['area_ha'] * it['p']:.2f} ± {CCS['sites'][sid]['model']['area_ha'] * it['se']:.2f}ha" if it
                  else "<span class='blank'>판독 미실시</span> — 과제 대상지는 동탄 후보지 A이고 천안캠퍼스는 추가 비교라 캐노피 칸을 사유와 함께 비워 둠.") + "</li>")

s2rows = [["대상", "Sentinel-2 L2A 장면", "취득일", "경계 안 구름", "Landsat 9 C2 L2 장면", "취득일·시각", "경계 안 구름"]] + [
    [SITES[s]["short"], SAT[s]["s2"]["id"], SAT[s]["s2"]["date"], f"{SAT[s]['s2']['local_cloud']}%", SAT[s]["l9"]["id"],
     f"{SAT[s]['l9']['date']} {SAT[s]['l9']['time_utc']}UTC", f"{SAT[s]['l9']['local_cloud']}%"] for s in SITES]
res = {r["용도지역"]: r for r in RD["table"]}
html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>7주차 과제</title><style>
@page{{size:A4;margin:16mm 14mm}}
body{{font-family:'Malgun Gothic',sans-serif;font-size:10pt;color:#1b2033;line-height:1.55}}
h1{{font-size:18pt;margin:0 0 4px}} h2{{font-size:13pt;border-left:5px solid #e8642c;padding-left:8px;margin:20px 0 8px;page-break-after:avoid}}
h3{{font-size:11pt;margin:14px 0 6px}} h4{{font-size:10pt;margin:10px 0 4px}}
table{{border-collapse:collapse;width:100%;margin:6px 0 10px;font-size:8.6pt;page-break-inside:auto}}
th{{background:#1f2a5c;color:#fff;font-weight:600;padding:4px 5px;text-align:left}} td{{border-bottom:1px solid #d9dce5;padding:4px 5px;vertical-align:top}}
table.small{{font-size:7.8pt}} .s{{font-size:7.6pt;color:#555}} .blank{{background:#fff0e6;color:#b4461a;padding:0 4px;border-radius:3px}}
.cover td{{border:0;padding:2px 8px 2px 0}} .fig{{width:100%;margin:6px 0}} .cap{{font-size:8.5pt;color:#555}}
.todo{{border:1.5px dashed #e8642c;padding:10px;color:#b4461a;border-radius:6px}} .box{{background:#f4f5f9;padding:8px 10px;border-radius:6px}}
</style></head><body>
<h1>도로 위계 · 그린인프라 정량화 · CCS 1차 결과표</h1>
<div>스마트도시계획(캡스톤디자인) · 7주차 과제</div>
<table class="cover"><tr><td>소속</td><td>상명대학교 그린스마트시티학과</td></tr><tr><td>팀원</td><td>{TEAM}</td></tr>
<tr><td>교수자</td><td>김태한 교수</td></tr><tr><td>대상지</td><td>① 동탄 후보지 A(장지동 남측, {CCS['sites']['dongtan']['model']['area_ha']:.1f}ha — 6주차 대안 1안) · ② 상명대학교 천안캠퍼스({CCS['sites']['cheonan']['model']['area_ha']:.1f}ha)</td></tr>
<tr><td>작성일</td><td>{QUERIED_ON} · 자료 조회일 {QUERIED_ON}</td></tr><tr><td>대시보드</td><td>https://sin030327.github.io/ndvi-dashboard/</td></tr>
<tr><td>제출</td><td>LMS 7주차 과제 · PDF + 결과표(xlsx·csv) + i-Tree 원본(.itrcnpy) · 기한 2026.10.25. 23:59</td></tr></table>

<h2>0. 요약</h2>
<ul>
<li><b>① 도로 위계</b> — 6주차 1위 대안 C에 주간선 35m·보조간선 25m·집산 20m를 1,000·500·250m 간격으로 배치했다. 도로율은 주거 {res['주거']['도로율(%)']}%(간선 {res['주거']['간선도로율(%)']}%) · 상업 {res['상업·업무']['도로율(%)']}%({res['상업·업무']['간선도로율(%)']}%) · 공업 {res['공업']['도로율(%)']}%({res['공업']['간선도로율(%)']}%)로 제11조 기준 {RD['compliance']}/6을 충족한다.</li>
<li><b>③ 지표 ⑦</b> — 동탄 NDVI {SAT['dongtan']['ndvi']['mean']:.3f} · LST {SAT['dongtan']['lst']['mean']:.1f}℃({SAT['dongtan']['s2']['date']}), 천안캠퍼스 NDVI {SAT['cheonan']['ndvi']['mean']:.3f} · LST {SAT['cheonan']['lst']['mean']:.1f}℃({SAT['cheonan']['s2']['date']}/{SAT['cheonan']['l9']['date']}). 모두 경계 안 구름 0% 장면의 실측값이다.</li>
<li><b>② 캐노피 판독</b> — {('동탄 후보지 A: i-Tree와 같은 무작위 500점 방식의 <b>AI 대체 판독(i-Tree 아님)</b>, ' + f"{100 * itree('dongtan')['p']:.1f} ± {100 * itree('dongtan')['se']:.2f}%. .itrcnpy 원본은 없음") if itree('dongtan') and itree('dongtan')['src'] == 'ai' else ('i-Tree 판독값 입력' if itree('dongtan') else '판독 대기')}. 천안캠퍼스는 판독 미실시(사유 기록).</li>
<li><b>④ 대안 비교</b> — 동탄 {' > '.join(ALTN[k] for k in mx_out['dongtan'][2])}, 천안 {' > '.join(ALTN[k] for k in mx_out['cheonan'][2])}{' (잠정)' if any(mx_out[s][4] for s in SITES) else ''}.</li>
<li><b>준비 질문</b> — 500점에서 캐노피 20% 대 23%는 SE × 2 = 3.76%p보다 차이(3.0%p)가 작아 '차이 없음'. 값 옆에 ± SE를 남기고 판정어를 함께 적는다.</li>
</ul>

<h2>1. 자료 · 방법</h2>
{table(s2rows, 'small')}
<p class="s">자료 경로 대체 — 슬라이드 기준 경로는 CDSE(Sentinel-2)·USGS EarthExplorer(Landsat)다. 학생 계정 개설 전이라 같은 산출물(ESA Sentinel-2 L2A · USGS Landsat Collection 2 Level-2)을 계정 없이 제공하는 Microsoft Planetary Computer 공개 미러를 썼고, 장면 ID는 원 산출물과 같다. 장면은 '2026-06-01~09-30, 경계 안 구름·그림자 최소 쌍, 날짜 차 5일 이내' 규칙(사전 고정)으로 골랐다. NDVI는 BOA 오프셋(−1000)을 보정한 B4·B8 10m 원 화소, LST는 ST_B10 × 0.00341802 + 149.0 − 273.15다. 동탄 경계는 6주차 90m 셀 합집합, 천안캠퍼스 경계는 OpenStreetMap way 231288273이다.</p>

<h2>2. 과제 ① 도로 위계 — 대안 1안 간선 3단 배치 · 도로율</h2>
<img class="fig" src="{img64(OUT / 'fig_roads.png')}">
<p class="s">배치 규칙: 간격은 제10조제3호로 고정하고 격자 원점만 30m 단위로 탐색했다 — ① 개발 셀 중심이 도로에서 125m 안인 비율 최대({100 * RD['access_125m']:.0f}%) → ② 제11조 기준 충족 개수 최대 → ③ 도로 면적 최소. 주간선은 대상지를 지나는 통과 간선(400m 미만 토막 삭제), 보조간선·집산은 개발용지 + 90m 안에만 둔다. 교차부 면적은 상위 위계에 귀속.</p>
{table(cross_rows, 'small')}
{table(road_rows, 'small')}
<p class="s">간선도로율 = 주간선 + 보조간선. 국지도로는 배치하지 않았으므로 지구단위계획 단계에서 국지도로를 더하면 도로율이 올라간다(주거 상한 30% 미만 여유 {30 - res['주거']['도로율(%)']:.1f}%p). 6주차 수용인구 산식의 '도로·기반시설 20%' 가정과 비교하면 주거 간선 3단만으로 {res['주거']['도로율(%)']}%를 차지한다.</p>

<h2>3. 과제 ② i-Tree Canopy 500점 판독</h2>
<ul>{''.join(it_txt)}</ul>
{ai_html}
<p class="s">경계 shapefile(WGS84)은 제출/i-Tree_경계/에 있다. 단순모드(Tree/Non-Tree) 500점, SE = √(p(1−p)/N), 면적 = 경계 면적 × p ± 경계 면적 × SE. 원본 .itrcnpy · Report PDF · CSV를 함께 제출한다.</p>

<h2>4. 과제 ③ 지표 ⑦ 카탈로그 — 캐노피 · NDVI · 지표온도</h2>
{table(cat, 'small')}
<img class="fig" src="{img64(figs['dongtan'])}">
<img class="fig" src="{img64(figs['cheonan'])}">

<h2>5. 과제 ④ CCS 1차 결과표 · 대안 비교 서식</h2>
<p class="s">6개 열(지표 · 값 · 오차 · 해상도 · 출처·취득일 · 조회일)이 모두 채워진 행만 대안 비교로 옮긴다. 대안 비교는 5점 척도 × 가중치(합 1.00, 대안 기입 전 고정 — 팀 승인 필요), 차이가 오차 안이면 기준선과 같은 점수. 조성비·유지관리비는 물량 × 가정 단가({CCS['unit_note']}).</p>
{sec_ccs}
<h3>준비 질문 — 표본 500점 기준 두 대안의 캐노피 차이 3%p</h3>
{table(sig, 'small')}

<h2>6. 과제 ⑤ 조감 이미지</h2>
{aerial_html}
<div class="box"><b>결정 문장</b> {decision}<br><b>프롬프트</b> <span class="s">{prompt}</span><br><b>캡션</b> {caption}</div>

<h2>7. 가정 · 한계</h2>
{table(assume, 'small')}
<ul class="s">
<li>NDVI·LST는 각 대상지 장면 1회분이다. 같은 날짜대 비교 규약에 따라 대안 간 차이는 위성값으로 판정하지 않았다.</li>
<li>HM은 InVEST User Guide 식의 재구현이며 생물물리 값·ET0 균일은 가정이다. 그늘 가중치 ±0.1 변동 폭을 값 옆에 적었다.</li>
<li>Landsat 열적외 원 해상도는 100m(30m 재배열)이라 가로수 1열 규모의 변화는 잡히지 않는다.</li>
<li><b>동탄 지표온도는 경계의 {100 * SAT['dongtan']['lst']['coverage']:.0f}%({SAT['dongtan']['lst']['n']:,}/{SAT['dongtan']['lst']['n_total']:,}셀)만 대표한다.</b> QA_PIXEL은 맑음인데 ST_B10 값이 없는 화소가 6~9월 Landsat 9 장면 모두에서 76% 이상 나타났다(경로 115·116 공통, 원인 미확인). USGS EarthExplorer 원본으로 교차 확인이 필요하다.</li>
<li>공업용지 유출계수는 표 9-11에 없어 상업용지 값을 준용했다. 단가는 출처 확인 전 가정값이다.</li>
</ul>
<h2>참고문헌</h2>
<p class="s">김철수. (2017). 《현대도시계획》. 기문당. · 대한국토·도시계획학회. (2015). 《토지이용계획론》. 보성각. · 한국토지공사. (2005). 《생태환경도시개발편람》. ·
「도시·군계획시설의 결정·구조 및 설치기준에 관한 규칙」(시행 2025-10-31) 제10조·제11조·제12조·제30조. · ESA Sentinel-2 L2A · USGS Landsat Collection 2 Level-2 — Microsoft Planetary Computer STAC/Data API(조회 {QUERIED_ON}). ·
Natural Capital Project. InVEST User Guide — Urban Cooling Model. · i-Tree Canopy. · OpenStreetMap contributors(ODbL). · 김태한. (2026). 스마트도시계획(캡스톤디자인) 7주차 주간 슬라이드.</p>
</body></html>"""
out_html = OUT / "report.html"
out_html.write_text(html, encoding="utf-8")
pdf = SUBMIT / "7주차_보고서_도로위계_CCS결과표.pdf"
subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", out_html.as_uri()], check=True, timeout=180)
print("saved", pdf, pdf.stat().st_size)

# ── 체크리스트 ───────────────────────────────────────────────────────
done = lambda b: "✅" if b else "⬜"
its = {s: itree(s) for s in SITES}
files = {p.name for p in SUBMIT.iterdir()}
has = lambda ext: any(f.lower().endswith(ext) for f in files)
(SUBMIT / "제출_체크리스트.md").write_text(f"""# 7주차 과제 제출 체크리스트 (기한 2026.10.25. 23:59 · LMS 7주차)

| 과제 | 상태 | 파일 |
|---|---|---|
| ① 도로 위계 — 대안 1안 간선 3단 · 도로율 | {done(True)} 기준 {RD['compliance']}/6 충족 | 보고서 2장 · 7주차_결과표.xlsx「①…」 · csv/1_*.csv |
| ② i-Tree 500점 판독 | {done(its['dongtan'] is not None and its['dongtan']['src'] == 'itree')} {'동탄: AI 대체 판독(i-Tree 아님, .itrcnpy 없음)' if its['dongtan'] and its['dongtan']['src'] == 'ai' else ('입력됨' if its['dongtan'] else '직접 판독 필요')} · 천안: 미실시 | {'.itrcnpy ' + done(has('.itrcnpy'))} · i-Tree PDF · i-Tree CSV → 이 폴더에 추가 |
| ③ 지표 ⑦ 카탈로그 | {done(its['dongtan'] is not None)} NDVI·LST 실측 완료, 동탄 캐노피 {'AI 대체 판독값' if its['dongtan'] and its['dongtan']['src'] == 'ai' else ('입력됨' if its['dongtan'] else '대기')} | xlsx「③지표7_카탈로그」 · csv/3_지표7_카탈로그.csv |
| ④ CCS 1차 결과표 · 대안 A·B·C | {done(its['dongtan'] is not None)} 동탄 {'확정' if its['dongtan'] else '잠정'} · 천안 잠정(캐노피 미실시 — 사유 기록) | xlsx「④…」 · csv/4_*.csv · 보고서 5장 |
| ⑤ 조감 이미지 · 'AI 생성' 캡션 | {done(aerial is not None)} {'첨부됨' if aerial else '이미지 생성 필요'} | 조감이미지_프롬프트_캡션.txt → 제출/조감이미지.png |

## 직접 할 일
1. **i-Tree 판독** — `i-Tree_작업안내.txt` 순서대로 두 경계를 각각 500점 판독 → `.itrcnpy`·PDF·CSV를 이 폴더에 저장
2. **값 입력** — `data/itree_results.json`에 수목 점 수(tree)·판독일(date) 입력
3. **조감 이미지** — 프롬프트로 밝은 장면 1장 생성 → `제출/조감이미지.png`로 저장
4. **다시 만들기** — `python code/06_submission.py` → 보고서 PDF·xlsx·csv가 판독값·이미지로 갱신
5. **팀 확인** — 대안 비교 가중치(초안)·단가(가정) 승인 또는 수정 → `code/04_ccs.py`의 WEIGHTS·UNIT 수정 후 04 → 05 → 06 재실행

## LMS에 올릴 것
- `7주차_보고서_도로위계_CCS결과표.pdf`
- `7주차_결과표.xlsx` (또는 csv 폴더)
- i-Tree 원본 `.itrcnpy` (+ i-Tree 보고서 PDF·CSV)
""", encoding="utf-8")
print("checklist ok")
