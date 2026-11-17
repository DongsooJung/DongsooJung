"""
이중차분(DID) 추정기

5가지 추정 방식을 통합 인터페이스로 지원:
    1. Two-way Fixed Effects (TWFE)     - 표준 DID
    2. Event Study                       - 처리시점 기준 동태적 효과
    3. Goodman-Bacon Decomposition       - TWFE 가중치 분해
    4. Callaway-Sant'Anna (CS)           - 이질적 처리시점
    5. Synthetic Control                  - 단일 처리집단

이론:
    - Card & Krueger (1994), AER
    - Goodman-Bacon (2021), JoE
    - Callaway & Sant'Anna (2021), JoE
    - Abadie, Diamond & Hainmueller (2010), JASA
"""
from __future__ import annotations

import logging
from typing import Literal, Optional
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

logger = logging.getLogger(__name__)

EstimatorType = Literal["twfe", "event_study", "did_cs", "synthetic_control"]


# ======================================================================
# 결과 컨테이너
# ======================================================================
@dataclass
class DIDResult:
    """DID 추정 결과."""

    estimator: EstimatorType
    att: float                         # 평균 처리효과 (ATT)
    att_se: float                      # 표준오차
    att_ci: tuple[float, float]        # 95% 신뢰구간
    p_value: float
    n_treated: int
    n_control: int
    n_periods: int
    pre_trend_pvalue: Optional[float] = None  # 평행 추세 검정
    raw_result: object = None

    def summary(self) -> str:
        """결과 요약 문자열."""
        lines = [
            f"=== DID 추정 ({self.estimator}) ===",
            f"ATT = {self.att:+.4f}  (SE={self.att_se:.4f}, p={self.p_value:.4f})",
            f"95% CI = [{self.att_ci[0]:+.4f}, {self.att_ci[1]:+.4f}]",
            f"처리={self.n_treated} · 통제={self.n_control} · 기간={self.n_periods}",
        ]
        if self.pre_trend_pvalue is not None:
            verdict = "통과" if self.pre_trend_pvalue > 0.05 else "위반 의심"
            lines.append(
                f"평행추세 검정 p={self.pre_trend_pvalue:.4f} ({verdict})"
            )
        return "\n".join(lines)


# ======================================================================
# 메인 클래스
# ======================================================================
class DIDAnalysis:
    """
    이중차분 분석 통합 인터페이스.

    Example:
        >>> from airport_di import DIDAnalysis, load_panel
        >>> panel = load_panel("suwon")
        >>> did = DIDAnalysis(
        ...     panel,
        ...     outcome="log_price_per_sqm",
        ...     unit_col="region_code",
        ...     time_col="year_month",
        ...     treat_col="treatment",
        ...     post_col="post",
        ... )
        >>> result = did.run_twfe()
        >>> result.summary()
    """

    def __init__(
        self,
        df: pd.DataFrame,
        outcome: str,
        unit_col: str = "region_code",
        time_col: str = "year_month",
        treat_col: str = "treatment",
        post_col: str = "post",
        covariates: Optional[list[str]] = None,
    ):
        self.df = df
        self.outcome = outcome
        self.unit_col = unit_col
        self.time_col = time_col
        self.treat_col = treat_col
        self.post_col = post_col
        self.covariates = covariates or []

        self._validate()

    # ------------------------------------------------------------------
    def run_twfe(self, cluster_se: bool = True) -> DIDResult:
        """
        표준 Two-way Fixed Effects DID.

        모형: y_it = α_i + γ_t + δ·(treat_i × post_t) + X_it β + ε_it

        Args:
            cluster_se: True면 unit 수준 클러스터 표준오차

        Returns:
            DIDResult (att = δ 추정치)
        """
        df = self.df.copy()
        df["_did"] = df[self.treat_col] * df[self.post_col]

        # 엔티티·시간 더미 (TWFE) — statsmodels OLS로 구현 (linearmodels 불필요)
        entity_d = pd.get_dummies(df[self.unit_col], prefix="u", drop_first=True)
        time_d = pd.get_dummies(df[self.time_col], prefix="t", drop_first=True)

        X_parts = [df[["_did"]]]
        if self.covariates:
            X_parts.append(df[self.covariates])
        X_parts.extend([entity_d, time_d])
        X = pd.concat(X_parts, axis=1).astype(float)
        X = sm.add_constant(X, has_constant="add")
        y = df[self.outcome].astype(float)

        if cluster_se:
            groups = df[self.unit_col]
            res = sm.OLS(y, X).fit(
                cov_type="cluster", cov_kwds={"groups": groups}
            )
        else:
            res = sm.OLS(y, X).fit(cov_type="HC1")

        att = float(res.params["_did"])
        se = float(res.bse["_did"])
        p = float(res.pvalues["_did"])
        ci_low, ci_high = res.conf_int().loc["_did"].tolist()

        n_treated = int(df.loc[df[self.treat_col] == 1, self.unit_col].nunique())
        n_control = int(df.loc[df[self.treat_col] == 0, self.unit_col].nunique())
        n_periods = int(df[self.time_col].nunique())

        return DIDResult(
            estimator="twfe",
            att=att,
            att_se=se,
            att_ci=(float(ci_low), float(ci_high)),
            p_value=p,
            n_treated=n_treated,
            n_control=n_control,
            n_periods=n_periods,
            raw_result=res,
        )

    def run_event_study(
        self,
        leads: int = 4,
        lags: int = 8,
    ) -> DIDResult:
        """
        Event Study DID — 처리시점(τ=0) 기준 동태적 효과 추정.

        모형: y_it = α_i + γ_t + Σ_τ δ_τ·1[t-T_i = τ] + ε_it

        Returns:
            DIDResult — raw_result['event_study']에 event_time별 계수/CI DataFrame.
            처리 시점은 post가 처음 1이 되는 시점으로 정의한다.
        """
        df = self.df.copy()

        # 처리시점 T_i: 처리집단에서 post==1 최초 시점
        post_times = (
            df.loc[df[self.post_col] == 1]
            .groupby(self.unit_col)[self.time_col].min()
        )
        global_treat_time = post_times.min() if len(post_times) else None
        if global_treat_time is None:
            raise ValueError("post==1 인 관측이 없어 처리시점을 정의할 수 없습니다.")

        # 시간 정렬 인덱스
        time_vals = np.sort(df[self.time_col].unique())
        time_to_idx = {t: i for i, t in enumerate(time_vals)}
        treat_idx = time_to_idx[global_treat_time]

        df["_event_time"] = df[self.time_col].map(time_to_idx) - treat_idx
        # 처리집단만 이벤트타임 의미 → 통제는 0(기준)으로 묶기 위해 treat와 상호작용
        df["_et_clip"] = df["_event_time"].clip(-leads, lags)

        # 기준 시점 τ=-1 (드롭). 처리집단 × 각 event-time 더미
        et_values = [e for e in range(-leads, lags + 1) if e != -1]
        for e in et_values:
            df[f"_et_{e}"] = ((df["_et_clip"] == e) & (df[self.treat_col] == 1)).astype(float)

        entity_d = pd.get_dummies(df[self.unit_col], prefix="u", drop_first=True)
        time_d = pd.get_dummies(df[self.time_col], prefix="t", drop_first=True)
        et_cols = [f"_et_{e}" for e in et_values]

        X = pd.concat([df[et_cols], entity_d, time_d], axis=1).astype(float)
        X = sm.add_constant(X, has_constant="add")
        y = df[self.outcome].astype(float)
        res = sm.OLS(y, X).fit(
            cov_type="cluster", cov_kwds={"groups": df[self.unit_col]}
        )

        # event-time 계수 정리
        rows = []
        ci = res.conf_int()
        for e in range(-leads, lags + 1):
            if e == -1:
                rows.append({"event_time": e, "coef": 0.0, "ci_low": 0.0, "ci_high": 0.0})
                continue
            col = f"_et_{e}"
            rows.append({
                "event_time": e,
                "coef": float(res.params[col]),
                "ci_low": float(ci.loc[col, 0]),
                "ci_high": float(ci.loc[col, 1]),
            })
        es_df = pd.DataFrame(rows).sort_values("event_time").reset_index(drop=True)

        # 대표 ATT = 사후(post) event-time 계수 평균
        post_coefs = es_df.loc[es_df["event_time"] >= 0, "coef"]
        att = float(post_coefs.mean()) if len(post_coefs) else float("nan")

        n_treated = int(df.loc[df[self.treat_col] == 1, self.unit_col].nunique())
        n_control = int(df.loc[df[self.treat_col] == 0, self.unit_col].nunique())

        return DIDResult(
            estimator="event_study",
            att=att,
            att_se=float("nan"),
            att_ci=(float("nan"), float("nan")),
            p_value=float("nan"),
            n_treated=n_treated,
            n_control=n_control,
            n_periods=int(df[self.time_col].nunique()),
            raw_result={"event_study": es_df, "model": res},
        )

    def run_callaway_santanna(
        self,
        control_group: str = "never_treated",
    ) -> DIDResult:
        """
        Callaway-Sant'Anna (2021) heterogeneous DID.

        처리시점이 시군구별로 다를 때 적합. 각 (g, t) 조합별 ATT 계산 후
        가중평균하여 단일 ATT 산출.

        Args:
            control_group: 'never_treated' | 'not_yet_treated'
        """
        raise NotImplementedError(
            "TODO: differences 패키지 또는 Python 직접 구현. "
            "각 처리코호트 g와 시점 t 조합에 대해 ATT(g,t) 계산"
        )

    def run_synthetic_control(
        self,
        treated_unit: str,
        donor_pool: list[str],
        predictor_vars: Optional[list[str]] = None,
    ) -> DIDResult:
        """
        Abadie-Diamond-Hainmueller (2010) 합성통제법.

        단일 처리집단(예: 수원시)을 통제집단의 가중평균으로 합성하여
        처리시점 이후 차이를 효과로 해석.

        Args:
            treated_unit: 처리 시군구 코드
            donor_pool: 후보 통제 시군구 리스트
            predictor_vars: 매칭에 사용할 사전기간 공변량
        """
        raise NotImplementedError(
            "TODO: from pysyncon import Synth; "
            "synth = Synth(); synth.fit(df, ...); "
            "att = (treated_post - synthetic_post).mean()"
        )

    # ------------------------------------------------------------------
    def test_parallel_trends(self) -> dict:
        """
        평행 추세 가정 검정.

        사전 기간(pre-treatment)에 처리·통제 집단 outcome 추세가
        통계적으로 유사한지 검증.

        Returns:
            {'F_stat': float, 'p_value': float, 'pass': bool}
        """
        df = self.df.copy()
        pre = df[df[self.post_col] == 0].copy()
        if pre[self.treat_col].nunique() < 2:
            raise ValueError("사전 기간에 처리·통제 집단이 모두 필요합니다.")

        # 시간 추세 변수
        time_vals = np.sort(pre[self.time_col].unique())
        time_to_idx = {t: i for i, t in enumerate(time_vals)}
        pre["_trend"] = pre[self.time_col].map(time_to_idx).astype(float)
        pre["_treat_x_trend"] = pre[self.treat_col] * pre["_trend"]

        X = pre[[self.treat_col, "_trend", "_treat_x_trend"]].astype(float)
        X = sm.add_constant(X, has_constant="add")
        y = pre[self.outcome].astype(float)
        res = sm.OLS(y, X).fit(
            cov_type="cluster", cov_kwds={"groups": pre[self.unit_col]}
        )

        # 상호작용 계수 = 0 (추세 평행) 검정
        f_test = res.f_test("_treat_x_trend = 0")
        f_stat = float(np.asarray(f_test.fvalue).ravel()[0])
        p_value = float(f_test.pvalue)

        return {
            "F_stat": f_stat,
            "p_value": p_value,
            "pass": bool(p_value > 0.05),
        }

    def goodman_bacon_decomposition(self) -> pd.DataFrame:
        """
        Goodman-Bacon (2021): TWFE β를 가중평균으로 분해.

        Returns:
            ['comparison_type', 'weight', 'beta'] 컬럼
            comparison_type: 'treated_vs_never', 'early_vs_late', etc.
        """
        raise NotImplementedError(
            "TODO: bacondecomp 패키지 활용 또는 직접 구현"
        )

    # ------------------------------------------------------------------
    def _validate(self) -> None:
        """입력 검증."""
        required = {self.outcome, self.unit_col, self.time_col, 
                    self.treat_col, self.post_col}
        missing = required - set(self.df.columns)
        if missing:
            raise ValueError(f"누락 컬럼: {missing}")
        if not self.df[self.treat_col].isin([0, 1]).all():
            raise ValueError(f"{self.treat_col}는 0/1 더미여야 합니다.")
