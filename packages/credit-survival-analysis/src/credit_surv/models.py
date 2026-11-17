"""
생존분석 모형 5종 통합 인터페이스

설치 의존성에 따른 구현 범위:
    - KaplanMeier : 순수 numpy 구현 (의존성 없음)
    - CoxModel    : scipy 기반 Breslow 부분우도 직접 구현 (lifelines 불필요)
    - AFTModel    : lifelines 필요 → 미설치 시 안내
    - RSFModel    : scikit-survival 필요 → 미설치 시 안내
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal, Optional, Any

import numpy as np
import pandas as pd
from scipy import optimize

logger = logging.getLogger(__name__)

ModelType = Literal["KM", "Cox", "AFT", "RSF", "DeepSurv"]


# ======================================================================
# 유틸 — Harrell's concordance index
# ======================================================================
def concordance_index(
    durations: np.ndarray,
    events: np.ndarray,
    risk_scores: np.ndarray,
) -> float:
    """Harrell's C-index.

    위험점수(risk_scores)가 높을수록 빨리 사건이 발생해야 일치(concordant).

    Args:
        durations: 관측기간
        events: 1=사건, 0=검열
        risk_scores: 선형예측자 등 위험 점수 (높을수록 고위험)

    Returns:
        0~1 (0.5=무작위). 비교가능 쌍이 없으면 0.5.
    """
    durations = np.asarray(durations, dtype=float)
    events = np.asarray(events, dtype=int)
    risk = np.asarray(risk_scores, dtype=float)
    n = len(durations)

    concordant = 0.0
    permissible = 0.0
    for i in range(n):
        if events[i] != 1:
            continue
        for j in range(n):
            if durations[j] <= durations[i]:
                # j가 i보다 먼저 또는 동시에 사건/검열 → 비교 조건 확인
                if durations[j] == durations[i] and events[j] == 1:
                    # 동시간 두 사건: tie 처리
                    if j <= i:
                        continue
                else:
                    continue
            # 여기서 durations[j] > durations[i] (i가 먼저 사건)
            permissible += 1.0
            if risk[i] > risk[j]:
                concordant += 1.0
            elif risk[i] == risk[j]:
                concordant += 0.5

    if permissible == 0:
        return 0.5
    return concordant / permissible


# ======================================================================
# 결과 컨테이너
# ======================================================================
@dataclass
class SurvivalResult:
    """생존모형 추정 결과 표준 컨테이너."""

    model_type: ModelType
    coefficients: Optional[pd.Series] = None  # Cox/AFT
    hazard_ratios: Optional[pd.Series] = None  # exp(coef)
    p_values: Optional[pd.Series] = None
    concordance_index: float = 0.0           # C-index (랭킹 지표)
    log_likelihood: Optional[float] = None
    aic: Optional[float] = None
    bic: Optional[float] = None
    feature_importance: Optional[pd.Series] = None  # RSF/DeepSurv
    n_obs: int = 0
    n_events: int = 0
    raw_model: Any = None

    def summary(self) -> str:
        lines = [
            f"=== {self.model_type} Survival Model ===",
            f"관측수: {self.n_obs}, 사건수: {self.n_events}",
            f"C-index: {self.concordance_index:.4f}",
        ]
        if self.log_likelihood is not None:
            lines.append(f"Log-likelihood: {self.log_likelihood:.2f}")
        if self.aic is not None:
            lines.append(f"AIC: {self.aic:.2f}")
        if self.coefficients is not None:
            lines.append("\n계수 (coef / HR / p):")
            for name in self.coefficients.index:
                coef = self.coefficients[name]
                hr = self.hazard_ratios[name] if self.hazard_ratios is not None else np.exp(coef)
                p = self.p_values[name] if self.p_values is not None else float("nan")
                lines.append(f"  {name:16} {coef:+.4f}  HR={hr:.3f}  p={p:.4f}")
        return "\n".join(lines)


# ======================================================================
# Kaplan-Meier (비모수) — 순수 numpy
# ======================================================================
class KaplanMeier:
    """비모수 생존함수 추정."""

    def __init__(self):
        self.timeline_: Optional[np.ndarray] = None
        self.survival_: Optional[np.ndarray] = None
        self.label_: str = "all"

    def fit(self, durations, events, label: str = "all") -> "KaplanMeier":
        durations = np.asarray(durations, dtype=float)
        events = np.asarray(events, dtype=int)
        self.label_ = label

        # 고유 사건시간 오름차순
        uniq_times = np.unique(durations)
        surv = []
        s = 1.0
        timeline = []
        for t in uniq_times:
            at_risk = np.sum(durations >= t)
            d = np.sum((durations == t) & (events == 1))
            if at_risk > 0:
                s *= (1.0 - d / at_risk)
            timeline.append(t)
            surv.append(s)

        self.timeline_ = np.array(timeline)
        self.survival_ = np.array(surv)
        return self

    def survival_function(self) -> pd.DataFrame:
        if self.survival_ is None:
            raise RuntimeError("fit()을 먼저 호출하세요.")
        return pd.DataFrame(
            {self.label_: self.survival_},
            index=pd.Index(self.timeline_, name="timeline"),
        )

    def median_survival_time(self) -> float:
        if self.survival_ is None:
            raise RuntimeError("fit()을 먼저 호출하세요.")
        below = np.where(self.survival_ <= 0.5)[0]
        if len(below) == 0:
            return float("inf")  # 중앙생존시간 미도달
        return float(self.timeline_[below[0]])


# ======================================================================
# Cox PH (준모수) — scipy Breslow 부분우도
# ======================================================================
class CoxModel:
    """
    Cox Proportional Hazards Model.

    h(t|x) = h₀(t) × exp(x'β)

    Breslow 부분우도를 scipy로 직접 최적화한다 (lifelines 불필요).

    Example:
        >>> cox = CoxModel(duration_col="duration", event_col="event")
        >>> result = cox.fit(df, covariates=["roa", "debt_ratio"])
        >>> print(result.summary())
    """

    def __init__(
        self,
        duration_col: str = "duration",
        event_col: str = "event",
        penalizer: float = 0.0,
    ):
        self.duration_col = duration_col
        self.event_col = event_col
        self.penalizer = penalizer
        self.fitted_ = None
        self.covariates_: Optional[list[str]] = None
        self.beta_: Optional[np.ndarray] = None
        self.means_: Optional[np.ndarray] = None

    # --- 내부: 음의 로그 부분우도 + 그래디언트 (Breslow) ---
    def _neg_log_partial_likelihood(self, beta, X, durations, events):
        lp = X @ beta
        # 위험집합: t_j >= t_i. 시간 내림차순 정렬로 누적합 활용
        order = np.argsort(-durations)  # 큰 시간부터
        lp_sorted = lp[order]
        dur_sorted = durations[order]
        ev_sorted = events[order]
        X_sorted = X[order]

        exp_lp = np.exp(lp_sorted)
        # 누적합 (위험집합 = 현재 시점 이상)
        cum_exp = np.cumsum(exp_lp)
        cum_x = np.cumsum(X_sorted * exp_lp[:, None], axis=0)

        # 동일시간 ties 처리: 같은 시간대는 같은 위험집합 사용
        # 각 위치에서 직전까지의 누적(>= t_i)을 구하려면 시간 그룹 경계 보정
        nll = 0.0
        grad = np.zeros_like(beta)
        i = 0
        n = len(dur_sorted)
        while i < n:
            j = i
            while j < n and dur_sorted[j] == dur_sorted[i]:
                j += 1
            # 그룹 [i, j) 는 동일 시간; 위험집합 누적값 = cum_exp[j-1]
            risk_sum = cum_exp[j - 1]
            risk_x = cum_x[j - 1]
            for k in range(i, j):
                if ev_sorted[k] == 1:
                    nll -= (lp_sorted[k] - np.log(risk_sum))
                    grad -= (X_sorted[k] - risk_x / risk_sum)
            i = j

        if self.penalizer > 0:
            nll += 0.5 * self.penalizer * np.sum(beta ** 2)
            grad += self.penalizer * beta
        return nll, grad

    def fit(self, df: pd.DataFrame, covariates: list[str]) -> SurvivalResult:
        self.covariates_ = list(covariates)
        durations = df[self.duration_col].to_numpy(dtype=float)
        events = df[self.event_col].to_numpy(dtype=int)
        X = df[covariates].to_numpy(dtype=float)

        # 중심화 (수치 안정)
        self.means_ = X.mean(axis=0)
        Xc = X - self.means_

        beta0 = np.zeros(X.shape[1])

        def obj(b):
            return self._neg_log_partial_likelihood(b, Xc, durations, events)

        res = optimize.minimize(
            obj, beta0, jac=True, method="BFGS",
            options={"gtol": 1e-6, "maxiter": 500},
        )
        beta = res.x
        self.beta_ = beta
        self.fitted_ = res

        # 표준오차: 헤시안 역행렬 (BFGS 근사 hess_inv 사용)
        try:
            cov = res.hess_inv
            se = np.sqrt(np.diag(cov))
        except Exception:
            se = np.full_like(beta, np.nan)

        from scipy.stats import norm
        z = beta / se
        p_values = 2 * (1 - norm.cdf(np.abs(z)))

        nll = res.fun
        loglik = -nll
        n_params = len(beta)
        aic = 2 * n_params - 2 * loglik

        risk_scores = Xc @ beta
        c_index = concordance_index(durations, events, risk_scores)

        coef = pd.Series(beta, index=covariates)
        result = SurvivalResult(
            model_type="Cox",
            coefficients=coef,
            hazard_ratios=np.exp(coef),
            p_values=pd.Series(p_values, index=covariates),
            concordance_index=c_index,
            log_likelihood=loglik,
            aic=aic,
            n_obs=len(df),
            n_events=int(events.sum()),
            raw_model=self,
        )
        return result

    def predict_partial_hazard(self, X: pd.DataFrame) -> np.ndarray:
        """exp(x'β) 부분위험 반환."""
        if self.beta_ is None:
            raise RuntimeError("fit()을 먼저 호출하세요.")
        Xc = X[self.covariates_].to_numpy(dtype=float) - self.means_
        return np.exp(Xc @ self.beta_)

    def check_proportional_hazards(self) -> pd.DataFrame:
        """비례위험 가정 검정 (Schoenfeld residuals) — lifelines 필요."""
        raise NotImplementedError(
            "Schoenfeld 잔차 검정은 lifelines 설치 후 지원됩니다."
        )


# ======================================================================
# AFT (모수) — lifelines 필요
# ======================================================================
class AFTModel:
    """Accelerated Failure Time (Weibull, Log-Normal)."""

    def __init__(self, distribution: str = "weibull"):
        self.distribution = distribution

    def fit(self, df, covariates) -> SurvivalResult:
        raise NotImplementedError(
            "AFTModel은 lifelines 설치가 필요합니다 "
            "(pip install lifelines). WeibullAFTFitter/LogNormalAFTFitter 사용."
        )


# ======================================================================
# Random Survival Forest (ML) — scikit-survival 필요
# ======================================================================
class RSFModel:
    """Random Survival Forest (Ishwaran et al. 2008)."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 5,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state

    def fit(self, X: pd.DataFrame, y) -> SurvivalResult:
        raise NotImplementedError(
            "RSFModel은 scikit-survival 설치가 필요합니다 "
            "(pip install scikit-survival)."
        )

    def feature_importance(self) -> pd.Series:
        raise NotImplementedError("scikit-survival 설치 후 지원됩니다.")

    def explain(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError("shap 설치 후 지원됩니다.")


# ======================================================================
# 모형 비교
# ======================================================================
def compare_survival_models(
    results: list[SurvivalResult],
) -> pd.DataFrame:
    """C-index, AIC, BIC 한 테이블 비교."""
    rows = []
    for r in results:
        rows.append({
            "model": r.model_type,
            "c_index": r.concordance_index,
            "log_likelihood": r.log_likelihood,
            "aic": r.aic,
            "bic": r.bic,
            "n_obs": r.n_obs,
            "n_events": r.n_events,
        })
    return pd.DataFrame(rows)
