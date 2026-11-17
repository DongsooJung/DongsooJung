# 🏗 Architecture & Methodology

> Airport Infrastructure DID Analytics

---

## 📐 프로젝트 구조

```
airport-infrastructure-analytics/
├── src/airport_di/
│   ├── __init__.py
│   ├── data_loader.py      # 사례별 패널 로드 (수원/광주/대구)
│   ├── did.py              # TWFE/Event Study/CS/Synthetic Control
│   └── visualization.py    # Event plot, SC plot, Placebo
│
├── notebooks/
│   └── 01_suwon_did_analysis.ipynb
│
├── data/                   # MOLIT/SGIS/소음 데이터
├── tests/
└── docs/
```

---

## 📚 5가지 추정기 — 언제 무엇을 쓰나

### 1. Two-way Fixed Effects (TWFE)

$$y_{it} = \alpha_i + \gamma_t + \delta(D_i \cdot \text{Post}_t) + \varepsilon_{it}$$

**용도**: 단일 시점 처리, 평행 추세가 만족될 때 표준.

**한계**: 처리시점이 단위마다 다르면 가중치가 음수가 될 수 있음 (Goodman-Bacon 2021).

---

### 2. Event Study

$$y_{it} = \alpha_i + \gamma_t + \sum_{\tau} \delta_\tau \mathbb{1}[t - T_i = \tau] + \varepsilon_{it}$$

**용도**: 동태적 효과 (사전 추세 + 사후 누적)

**해석**: τ < 0 계수 → 평행 추세 검정. τ ≥ 0 → 시간별 효과 강도.

---

### 3. Goodman-Bacon Decomposition

TWFE의 β를 4가지 비교군의 가중평균으로 분해:
- Treated vs Never-Treated
- Earlier-Treated vs Later-Treated
- Later-Treated vs Earlier-Treated  ← **음수 가중치 발생 가능**
- Pre vs Post within unit

**용도**: 처리시점 이질성이 있을 때 TWFE 신뢰성 진단.

---

### 4. Callaway-Sant'Anna (2021)

각 처리코호트 g에 대해 시점 t별 ATT(g,t) 계산 후 가중평균.

**장점**: 음수 가중치 문제 해결, heterogeneous treatment effects 명시적 추정.

---

### 5. Synthetic Control (Abadie et al. 2010)

$$\hat{Y}_{1t}^N = \sum_{j=2}^{J+1} w_j Y_{jt}, \quad \sum w_j = 1, w_j \geq 0$$

처리집단 1개를 통제집단 가중평균으로 합성.

**용도**: 단일 정책 충격 (예: 광주 군공항 발표 사건).
**장점**: 시각적으로 강력. **단점**: 추론 어려움 (placebo 검정 필요).

---

## 🎯 사례별 차별성

### 🟦 수원 군공항
- **처리시점**: 2025년 이전 발표
- **공간 단위**: 시군구 + 행정동 + 5km 버퍼
- **메커니즘**: 소음 해소 + 재개발 기대감
- **데이터 가용성**: 높음 (MOLIT + 환경부 소음포털)

### 🟧 광주 군공항
- **이전 추진**: 전남 무안
- **이슈**: 무안 주민 반대로 지연
- **분석 시점**: 발표 vs 보류 비교

### 🟨 대구 군공항
- **이전 확정**: 의성·군위
- **선례**: 다른 사례의 사전 가이드라인 제공
- **데이터 길이**: 가장 긴 시계열 확보 가능

### 🟩 김포공항 소음권
- **시점 대신 거리 기반 식별**
- **Dose-Response**: 거리에 따른 가격 함수 추정

---

## 📊 결과 보고 권장 형식

```
| 추정기              | ATT       | SE      | 95% CI            | n_treated | n_periods |
|---------------------|-----------|---------|-------------------|-----------|-----------|
| TWFE                | -0.045    | 0.012   | (-0.069, -0.021)  | 2         | 84        |
| Event Study (sum)   | -0.052    | 0.018   | (-0.087, -0.017)  | 2         | 84        |
| Callaway-Sant'Anna  | -0.041    | 0.014   | (-0.068, -0.014)  | 2         | 84        |
| Synthetic Control   | -0.048    | (RMSPE) | placebo p < 0.05  | 1         | 84        |
```

---

## 📖 주요 참고문헌

1. Card, D., & Krueger, A. B. (1994). Minimum wages and employment. *AER*, 84(4), 772-793.
2. Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic control methods. *JASA*, 105(490), 493-505.
3. Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. *JoE*, 225(2), 254-277.
4. Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple time periods. *JoE*, 225(2), 200-230.
5. Roth, J., Sant'Anna, P. H. C., Bilinski, A., & Poe, J. (2023). What's trending in DID? *JoE*, 235(2), 2218-2244.
