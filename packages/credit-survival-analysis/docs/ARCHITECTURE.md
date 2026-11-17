# 🏗 Architecture & Methodology

> Korean Corporate Credit Survival Analysis

---

## 📐 프로젝트 구조

```
credit-survival-analysis/
├── src/credit_surv/
│   ├── __init__.py
│   ├── data_loader.py    # DART/KED 데이터 로드 + 합성 생존데이터
│   └── models.py          # KM/Cox/AFT/RSF/DeepSurv
├── notebooks/
│   └── 01_credit_survival.ipynb
├── data/
├── tests/
└── docs/
```

---

## 📚 5가지 모형 비교

| 모형 | 형태 | 가정 | 장점 | 단점 |
|------|------|------|------|------|
| **Kaplan-Meier** | 비모수 | 없음 | 시각적, 그룹 비교 | 공변량 ✗ |
| **Cox PH** | 준모수 | 비례위험 | 해석력 ↑, HR 직관적 | 비선형 ✗ |
| **AFT (Weibull)** | 모수 | 분포 가정 | 외삽 가능 | 분포 오설정 시 편향 |
| **RSF** | ML | 없음 | 비선형, 자동 상호작용 | 해석 어려움 (SHAP 필요) |
| **DeepSurv** | DL | 없음 | 고차원 데이터, 표현학습 | 데이터 多 필요, 블랙박스 |

---

## 🔍 Cox PH 핵심 수식

$$h(t|x) = h_0(t) \cdot \exp(\beta_1 x_1 + \beta_2 x_2 + \cdots + \beta_p x_p)$$

- $h_0(t)$: baseline hazard (비특정)
- $\exp(\beta_k)$: **Hazard Ratio (HR)** — 공변량 $x_k$가 1단위 증가할 때 위험 배수
- $\text{HR} > 1$: 위험 증가, $\text{HR} < 1$: 위험 감소

**해석 예시**:
- HR(부채비율) = 1.65 → 부채비율 1단위 ↑ = 부도 위험 65% ↑
- HR(ROA) = 0.72 → ROA 1단위 ↑ = 부도 위험 28% ↓

---

## 📊 평가 지표

### Concordance Index (C-index)

$$C = \frac{\#\{(i,j) : T_i < T_j, \hat{S}_i(T_i) < \hat{S}_j(T_i)\}}{\#\{(i,j) : T_i < T_j\}}$$

- 0.5: 무작위 예측
- 0.7+: 양호
- 0.8+: 매우 우수

생존 데이터의 ROC-AUC와 유사한 역할.

---

## 🚧 향후 확장

- [ ] Time-varying covariates (재무비율의 시계열 변화 반영)
- [ ] Competing risks (부도 vs 합병 vs 청산)
- [ ] Multi-state models (정상 → BBB → 부도 단계 모형화)
- [ ] Macro 변수 통합 (GDP, KOSPI 등)

---

## 📖 주요 참고문헌

1. Cox, D. R. (1972). Regression models and life-tables. *JRSS-B*, 34(2), 187-202.
2. Ishwaran, H., et al. (2008). Random survival forests. *Annals of Applied Statistics*, 2(3), 841-860.
3. Katzman, J. L., et al. (2018). DeepSurv: personalized treatment recommender system using a Cox proportional hazards deep neural network. *BMC Medical Research Methodology*, 18(1).
4. Lin, D. Y. (1994). Cox regression analysis of multivariate failure time data. *Statistics in Medicine*, 13(21), 2233-2247.
