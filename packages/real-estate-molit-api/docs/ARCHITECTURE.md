# 🏗 Architecture & Design Decisions

> Real Estate Hedonic Price Model — 설계 문서

---

## 📐 프로젝트 구조

```
real-estate-hedonic/
├── src/hedonic/              # 핵심 패키지
│   ├── __init__.py           # 공개 API 정의
│   ├── molit_api.py          # 🌐 데이터 수집 계층
│   ├── geocoding.py          # 🗺 좌표 변환
│   ├── preprocessing.py      # 🧹 정제·파생변수
│   ├── weights.py            # 🕸 공간가중행렬
│   ├── models.py             # 📊 헤도닉 모형 (OLS/SLM/SEM/SDM)
│   ├── diagnostics.py        # 🔍 공간자기상관 진단
│   └── visualization.py      # 📈 시각화
│
├── notebooks/
│   └── 01_end_to_end_pipeline.ipynb
│
├── data/
│   ├── raw/                  # MOLIT 원본 (gitignored)
│   ├── interim/              # 지오코딩 중간 산출물
│   └── processed/            # 분석 데이터셋(ADS)
│
├── tests/                    # pytest
├── scripts/                  # CLI 실행 스크립트
├── docs/                     # 설계 문서
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🎯 설계 원칙

### 1. 계층 분리 (Layered Architecture)

| Layer | 책임 | 의존성 |
|-------|------|--------|
| **Collection** | MOLIT/Kakao/V-World API 호출 | `requests`, `os.environ` |
| **Transformation** | 정제·파생변수·공간조인 | `pandas`, `geopandas` |
| **Modeling** | 헤도닉 추정 | `spreg`, `statsmodels` |
| **Diagnostics** | 공간자기상관 검정 | `esda` |
| **Presentation** | 시각화 | `matplotlib`, `folium` |

각 layer는 **상위 layer의 입출력만 의존**하며, 교차 참조를 금지합니다.

### 2. API 키 관리

- 모든 API 키는 **환경변수** (`.env`)로 분리
- `.env`는 `.gitignore`에 포함 → 커밋 금지
- `.env.example` 템플릿만 리포에 포함
- 런타임에 `python-dotenv`가 로드

### 3. 좌표계 정책

| 단계 | CRS | 용도 |
|------|-----|------|
| 지오코딩 결과 | EPSG:4326 (WGS84) | 경위도, Kakao API 표준 |
| 거리 계산 | EPSG:5186 (Korea 2000 Central TM) | 미터 단위, 공간가중행렬 |
| 시각화 | EPSG:4326 또는 3857 | 웹맵 호환 |

### 4. 이상치 처리

- **거래 해제**: `cancel_flag='O'` 행 삭제 (MOLIT API 기본 정책)
- **가격 이상치**: `price_per_sqm` 기준 IQR × 1.5 fence
- **건물 연령**: `building_age < 0` 또는 `> 60` 검토 대상
- **전용면적**: `area < 20㎡` 또는 `> 300㎡` 분리 플래그

---

## 📊 모형 선택 Flowchart

```
          ┌──────────────────┐
          │  OLS 베이스라인  │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  Moran's I 검정  │
          │  (OLS 잔차 기반) │
          └────────┬─────────┘
                   │
          p < 0.05 │ p ≥ 0.05
          ┌───────┴───────┐
          ▼               ▼
     LM 진단         OLS 채택
          │
          ▼
  ┌───────────────┐
  │  LM-Lag vs    │
  │  LM-Error 비교│
  └───┬───────┬───┘
      │       │
      ▼       ▼
     SLM     SEM
      │       │
      └───┬───┘
          ▼
    SDM 비교 (옵션)
    AIC/BIC 최소 선택
```

---

## 🔬 계량경제학적 고려사항

### 공간 스필오버의 의미

- **SLM (Spatial Lag)**: 이웃 가격이 본인 가격에 직접 영향
  - 예: 옆 단지가 비싸면 우리 단지도 프리미엄 형성
- **SEM (Spatial Error)**: 관측되지 않은 공간적 공통 요인
  - 예: 학군, 재개발 기대감 등 동 단위 비관측 요인
- **SDM (Spatial Durbin)**: 설명변수의 공간 spillover까지 모형화
  - 예: 이웃 단지의 면적·층도 본인 가격에 영향

### 해석 주의점

SLM/SDM의 경우 **계수는 직접 해석 불가** — `spreg.diagnostics_sp`로
**Direct / Indirect / Total Effect** 분해 필요.

```python
# 예시 (향후 구현)
from spreg.diagnostics_sp import MoranRes
slm.total_effect      # 단위 증가 총 효과
slm.direct_effect     # 본인에게 미치는 효과
slm.indirect_effect   # 이웃으로의 spillover
```

---

## 🔄 데이터 흐름 (End-to-End)

```
MOLIT API
  │ region_code, year_month
  ▼
[MolitClient.fetch_multi_period]
  │ 24 columns × N rows
  ▼
[preprocessing.drop_cancelled]
[preprocessing.drop_outliers_iqr]
  │
  ▼
[KakaoGeocoder.geocode_dataframe]
  │ + longitude, latitude
  ▼
[preprocessing.to_geodataframe]
[preprocessing.spatial_join_dong]
  │ + dong_code, dong_name, geometry
  ▼
[preprocessing.add_price_per_sqm]
[preprocessing.add_building_age]
[preprocessing.add_log_transforms]
  │ Analysis Dataset (ADS)
  ▼
[weights.build_weights(method='knn')]
  │ W matrix
  ▼
[SpatialHedonicModel.fit(method='SEM')]
  │ HedonicResults
  ▼
[diagnostics.morans_i on residuals]
[diagnostics.lm_diagnostics]
  │
  ▼
[visualization.*]
  │ PNG/HTML
  ▼
  results/
```

---

## 🚧 향후 확장 계획

- [ ] **시계열 헤도닉**: 월별 가격지수(Case-Shiller) 산출
- [ ] **Multilevel 모형**: 동-시군구 2단계 hierarchical (R `lme4` 포팅)
- [ ] **ML 비선형**: XGBoost + SHAP 기반 해석
- [ ] **Dashboard**: Streamlit 또는 Dash 시각화 앱
- [ ] **CI/CD**: GitHub Actions로 월 1회 자동 재학습
