# 녹지 판독 · 도로 위계 · CCS 결과표 대시보드 — 7주차

스마트도시계획(캡스톤디자인) · 상명대학교 그린스마트시티학과

**대시보드 →** https://sin030327.github.io/ndvi-dashboard/

대상지 2곳 — **동탄 후보지 A**(6주차 장지동 남측 250ha, 대안 1안 = 6주차 1위 대안 C · 절충)와 **상명대학교 천안캠퍼스**(OSM 경계 15.9ha). 상단 버튼으로 바꿉니다.

## 과제 대응

| 과제 | 대시보드 | 결과 |
|---|---|---|
| ① 도로 위계 — 대안 1안에 간선 3단, 도로율 | 「① 도로 위계 · 도로율」 | 주간선 35m · 보조간선 25m · 집산 20m를 1,000 · 500 · 250m 간격으로 배치. 주거 17.8%(간선 11.5) · 상업 25.7%(11.4) · 공업 17.6%(9.1) — 규칙 제11조 6/6 충족 |
| ② i-Tree 500점 판독 | 「② i-Tree」 칸에 판독값 입력 | 경계 shapefile(`files/*_boundary.zip`) 제공. 판독·.itrcnpy·PDF·CSV는 학생이 i-Tree Canopy에서 직접 |
| ③ 지표 ⑦ 카탈로그 | 「③ 지표 ⑦」 · 내보내기 | 실측 NDVI(Sentinel-2 L2A 10m)·LST(Landsat 9 C2 L2 30m), 장면 ID·취득일·경계 안 구름·조회일 병기 |
| ④ CCS 1차 결과표 · 대안 A·B·C | 「④ CCS 1차 결과표」 · 「대안 비교 서식」 | 5개 지표 × 6개 열 + 대안 A 현황 유지 · B 가로수 열식 · C 가로수 + 투수포장, 5점 척도 × 가중치 · 역전점 · 유의성 판정 |
| ⑤ 조감 이미지 | 「⑤ 조감 이미지」 | 대안 C 결정 문장 → 프롬프트 · 'AI 생성' 캡션 · 밝기(130) 확인. 이미지 생성은 학생이 직접 |

## 자료 · 방법

| 단계 | 자료 · 방법 |
|---|---|
| 경계 | 동탄 = 6주차 90m 셀(`data/mask_A.npy`) 합집합 · 천안 = OpenStreetMap way 231288273 |
| NDVI | ESA Sentinel-2 L2A B4·B8 10m, BOA 오프셋(−1000) 보정, SCL 구름·그림자 제외 |
| 지표온도 | USGS Landsat 9 C2 L2 ST_B10 × 0.00341802 + 149.0 − 273.15, QA_PIXEL 구름 제외 |
| 자료 경로 | CDSE·USGS 대신 같은 산출물을 계정 없이 주는 Microsoft Planetary Computer 공개 미러(STAC + Data API, 장면 ID 동일) |
| 장면 선택 | 2026-06-01~09-30 · 경계 안 구름 최소 Sentinel-2 × Landsat 9 쌍 · 날짜 차 ≤ 5일 (사전 고정) |
| 도로 위계 | 규칙 제10조 배치간격 고정, 격자 원점만 탐색(접근 125m 최대 → 제11조 충족 최대 → 도로 면적 최소) |
| 유출계수 | 원본 43번 표 9-11(한국토지공사 2005) × 용도별 면적, 투수포장 0.30 가정 |
| HM | InVEST Urban Cooling User Guide 식 파이썬 재구현(CC 0.6·0.2·0.2 · d_cool 450m), 생물물리 값 가정 |

## 재현

```
pip install requests numpy shapely pyproj matplotlib openpyxl pymupdf
python code/01_sites.py            # 경계 · 캠퍼스 도로 · i-Tree shapefile
python code/02_satellite.py        # 실측 NDVI · LST (Planetary Computer)
python code/03_roads.py            # ① 도로 위계 · 도로율
python code/04_ccs.py              # 유출계수 · HM · 대안 A·B·C
python code/05_export_dashboard.py # data.js
python code/06_submission.py       # 제출/ — xlsx · csv · 보고서 PDF (공개 저장소 제외)
```

i-Tree 판독 후 `data/itree_results.json`에 수목 점 수·판독일을 넣고 `06_submission.py`를 다시 실행하면 결과표와 보고서가 판독값으로 갱신됩니다. 팀원 학번은 `team_private.txt`(저장소 제외)에서 읽습니다.

## 가정 · 한계

- 대안 비교 가중치와 5점 척도 구간은 초안(팀 승인 필요), 가로수·투수포장 단가는 출처 미확인 가정값입니다(`code/04_ccs.py`의 `WEIGHTS` · `UNIT`).
- NDVI·LST는 설계안을 잴 수 없어 대안 A·B·C 모두 같은 장면 값입니다.
- 공업용지 유출계수는 표 9-11에 없어 상업용지 0.80을 준용했습니다.
