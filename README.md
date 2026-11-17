# DS Research · Urban Analytics

> 스마트도시 연구 모노레포 — 공간계량모형 · 헤도닉 가격 · DID · GIS · 생존분석
> Smart city research monorepo — spatial econometrics, hedonic pricing, DID, GIS, survival analysis

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PySAL](https://img.shields.io/badge/PySAL-spreg%20%C2%B7%20esda-orange?style=flat-square)](https://pysal.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## 개요

이 저장소는 DongsooJung 계정의 도시·공간 분석 연구 코드를 **단일 모노레포**로 통합한 허브입니다.  
이전에 분리되어 있던 5개 연구 저장소의 소스·노트북·테스트를 `packages/` 아래에서 관리합니다.

| Package | Domain | Methods |
|---------|--------|---------|
| [`urban-spatial-analysis`](packages/urban-spatial-analysis/) | 공간계량경제학 | SLM, SEM, SDM, GWR, Moran's I |
| [`smart-city-gis`](packages/smart-city-gis/) | 스마트도시 GIS | 접근성지수, 보행성, 토지이용 엔트로피 |
| [`airport-infrastructure-analytics`](packages/airport-infrastructure-analytics/) | 군공항 이전 정책 | DID, 공간 헤도닉, 네트워크 분석 |
| [`credit-survival-analysis`](packages/credit-survival-analysis/) | 기업신용 리스크 | Cox PH, Random Survival Forest |
| [`real-estate-molit-api`](packages/real-estate-molit-api/) | 부동산 가격모형 | 헤도닉 가격, MOLIT API, 공간적 자기상관 |

## 구조

```
ds-research-urban-analytics/
├── packages/
│   ├── urban-spatial-analysis/
│   ├── smart-city-gis/
│   ├── airport-infrastructure-analytics/
│   ├── credit-survival-analysis/
│   └── real-estate-molit-api/
└── README.md
```

각 패키지는 독립적인 `requirements.txt`, `src/`, `notebooks/`, `tests/`를 유지합니다.

## 빠른 시작

```bash
git clone https://github.com/DongsooJung/ds-research-urban-analytics.git
cd ds-research-urban-analytics/packages/urban-spatial-analysis
pip install -r requirements.txt
pytest
```

## 이전 저장소

다음 독립 저장소는 본 모노레포로 통합되었습니다:

- `urban-spatial-analysis` → `packages/urban-spatial-analysis/`
- `smart-city-gis` → `packages/smart-city-gis/`
- `airport-infrastructure-analytics` → `packages/airport-infrastructure-analytics/`
- `credit-survival-analysis` → `packages/credit-survival-analysis/`
- `real-estate-molit-api` (구 `real-estate-hedonic`) → `packages/real-estate-molit-api/`

## 라이선스

MIT — 각 패키지의 `LICENSE` 파일을 참고하세요.
