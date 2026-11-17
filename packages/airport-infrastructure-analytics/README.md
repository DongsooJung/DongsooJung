# Airport Infrastructure Analytics · 공항 인프라 분석

> 군 공항 이전과 종전부지 재개발 전략의 데이터 기반 분석
> Data-driven analysis of military airport relocation and former-site redevelopment

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## 개요 · Overview

국내 군 공항 이전은 대규모 도시개발 기회를 만듭니다(종전부지가 100만㎡를 넘기도 함). 현행 계획은 주변 부동산 가치·교통망·토지이용에 대한 공간적 파급효과를 과소평가합니다. 본 저장소는 이중차분(DID)·헤도닉·네트워크 분석·시나리오 시뮬레이션을 결합한 정량 프레임워크를 제공합니다.

Military airport relocations in South Korea create large urban development opportunities (former sites often exceed 1M㎡). Current planning underestimates spatial spillover effects on property values, transport networks, and land use. This repository provides a quantitative framework combining DID, hedonic modeling, network analysis, and scenario simulation.

## 문제와 접근 · Problem & Approach

1. **이중차분 / Difference-in-Differences (DID)** — 부동산 가치 영향 추정 (`did.py`)
2. **헤도닉 / Hedonic Model** — 공간 시차로 소음노출 가치평가
3. **네트워크 분석 / Network Analysis** — 이전 후 접근성 변화
4. **시나리오 / Scenario Simulation** — 종전부지 최적 토지이용 혼합

## 연구 배경 · Research Background

서울공항 활주로 재포장·격납고 PM을 수행한 **공군 시설장교** 실무 경험과 도시 공간경제 박사 연구를 결합해 개발되었습니다.

Developed from direct experience as a ROKAF Civil Engineering Officer (runway repaving and hangar PM at Seoul Air Base), combined with doctoral research on urban spatial economics.

## 방법 · Methods

```
처치군 Treatment: 공항 경계 5km 버퍼 내 부동산
대조군 Control:   소음 등고선 밖 비교가능 부동산
시점 Time:        발표 전 → 이전 결정 후 → 완공 후

DID 추정량: δ = (Ȳ_처치,후 − Ȳ_처치,전) − (Ȳ_대조,후 − Ȳ_대조,전)
공간 DID:   파급효과 반영을 위해 공간 가중행렬 결합
```

## 프로젝트 구조 · Repository Structure

```
airport-infrastructure-analytics/
├── src/airport_di/
│   ├── data_loader.py          # 실거래·소음·경계 데이터 로더
│   ├── did.py                  # 공간 확장 DID 추정량
│   └── visualization.py        # 소음 등고선·가격 변화 시각화
├── notebooks/
│   └── 01_suwon_did_analysis.ipynb   # 수원 공군기지 DID 사례
├── data/README.md
├── docs/ARCHITECTURE.md
├── tests/test_did.py
├── requirements.txt
└── LICENSE
```

## 빠른 시작 · Quick Start

```bash
git clone https://github.com/DongsooJung/airport-infrastructure-analytics.git
cd airport-infrastructure-analytics
pip install -r requirements.txt
jupyter notebook notebooks/01_suwon_did_analysis.ipynb
```

## 참고문헌 · References

- Nelson, J.P. (2004). Meta-analysis of airport noise and hedonic property values.
- Pope, D.G. & Pope, J.C. (2015). When Walmart comes to town: Always low housing prices?
- 국방부. 군 시설 이전 계획.

## 라이선스 · License

MIT License

## 저자 · Author

**정동수 (Dongsoo Jung)** — 공군 시설장교(예) · 서울대학교 박사과정 · 스마트도시공학
