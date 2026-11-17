# Corporate Credit Survival Analysis · 기업 신용 생존분석

> 한국 기업 신용위험 평가를 위한 생존모형과 머신러닝
> Survival models and machine learning for Korean corporate credit risk assessment

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![scikit-survival](https://img.shields.io/badge/scikit--survival-0.22+-orange?style=flat-square)](https://scikit-survival.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## 개요 · Overview

전통적 신용평가(로지스틱 회귀)는 부도를 이진 결과로만 다뤄 **사건까지의 시간(time-to-event)** 동학을 무시합니다. 국내 중소기업은 산업 경기·지역 경제·대기업 공급망 의존도에 따라 뚜렷한 생존 패턴을 보입니다. 본 저장소는 검열(censoring)을 적절히 처리하는 생존분석과 생존 ML을 결합한 신용위험 프레임워크를 제공합니다.

Traditional credit scoring (logistic regression) treats default as a binary outcome, ignoring **time-to-event dynamics**. Korean SMEs show distinct survival patterns driven by industry cycles, regional conditions, and supply-chain dependencies. This repository combines survival analysis (with proper censoring) and survival ML into a credit-risk framework.

## 문제와 접근 · Problem & Approach

1. **Kaplan-Meier** — 산업·지역별 비모수 생존곡선 추정
2. **Cox 비례위험 / Cox Proportional Hazards** — 시변 공변량 포함 (`models.py`)
3. **랜덤 생존 포레스트 / Random Survival Forests** — 비선형 위험요인 상호작용
4. **공간 frailty / Spatial Frailty** — 지역 경제 이질성 반영

## 기술 스택 · Tech Stack

- **생존모형 / Survival:** lifelines, scikit-survival, PySAL (공간 frailty)
- **ML Pipeline:** scikit-learn, XGBoost, LightGBM
- **Data:** DART(전자공시), NICE/KCB 신용데이터, KOSIS 지역지표
- **Visualization:** Matplotlib, Plotly (생존곡선·위험함수)

## 평가지표 · Evaluation Metrics

C-index(일치도), Brier Score(보정), 시점별 AUC(1·3년) 로 모형을 비교합니다.
Models are compared with C-index, Brier score, and time-dependent AUC (1yr, 3yr).

## 프로젝트 구조 · Repository Structure

```
credit-survival-analysis/
├── src/credit_surv/
│   ├── data_loader.py          # DART API · 신용데이터 커넥터, 재무비율 생성
│   └── models.py               # KM, Cox PH, RSF, 공간 frailty, 평가지표
├── notebooks/
│   └── 01_credit_survival.ipynb   # EDA → KM → Cox → 생존 ML 비교
├── data/README.md
├── docs/ARCHITECTURE.md
├── tests/test_models.py
├── requirements.txt
└── LICENSE
```

## 빠른 시작 · Quick Start

```bash
git clone https://github.com/DongsooJung/credit-survival-analysis.git
cd credit-survival-analysis
pip install -r requirements.txt
jupyter notebook notebooks/01_credit_survival.ipynb
```

## 참고문헌 · References

- Hosmer, D.W., Lemeshow, S., & May, S. (2008). *Applied Survival Analysis*. Wiley.
- Ishwaran, H. et al. (2008). Random Survival Forests. *Annals of Applied Statistics*.

## 라이선스 · License

MIT License

## 저자 · Author

**정동수 (Dongsoo Jung)** — 서울대학교 박사과정 · 공간계량 & 금융위험
