"""
헤도닉 가격모형 추정

4가지 모형을 통합 인터페이스로 비교 가능:
    1. OLS           - 공간자기상관 무시 (베이스라인)
    2. SLM (Lag)     - 종속변수의 공간 spillover
    3. SEM (Error)   - 공간적 교란항
    4. SDM (Durbin)  - Lag + Error 통합

이론:
    - Rosen (1974): 헤도닉 가격은 재화의 속성들의 암묵가격 벡터
    - Anselin (1988): 공간계량경제학 입문
    - LeSage & Pace (2009): Introduction to Spatial Econometrics
"""
from __future__ import annotations

import logging
from typing import Literal, Optional
from dataclasses import dataclass

import numpy as np
import pandas as pd
import geopandas as gpd
from libpysal.weights import W
from spreg import OLS, ML_Lag, ML_Error, GM_Lag, GM_Error
import statsmodels.api as sm

logger = logging.getLogger(__name__)

ModelMethod = Literal["OLS", "SLM", "SEM", "SDM"]


# ======================================================================
# 결과 컨테이너
# ======================================================================
@dataclass
class HedonicResults:
    """헤도닉 모형 추정 결과."""

    method: ModelMethod
    coefficients: pd.Series       # 회귀계수
    std_errors: pd.Series         # 표준오차
    p_values: pd.Series           # p-value
    r2: float                     # 결정계수
    adj_r2: Optional[float]       # 수정 결정계수
    log_likelihood: Optional[float]
    aic: Optional[float]
    bic: Optional[float]
    rho: Optional[float] = None   # SLM/SDM의 공간 lag 계수
    lambda_: Optional[float] = None  # SEM의 공간 error 계수
    n: int = 0                    # 표본 수
    k: int = 0                    # 설명변수 수

    def summary(self) -> str:
        """가독성 있는 요약 문자열 반환."""
        raise NotImplementedError(
            "TODO: f'{self.method} | N={self.n}, R²={self.r2:.3f}, ...' "
            "형식으로 멀티라인 테이블 조립"
        )

    def to_dataframe(self) -> pd.DataFrame:
        """계수 테이블 DataFrame 반환 (비교 병합용)."""
        raise NotImplementedError(
            "TODO: pd.DataFrame({'coef': ..., 'std_err': ..., 'p': ...})"
        )


# ======================================================================
# 메인 클래스
# ======================================================================
class SpatialHedonicModel:
    """
    공간 헤도닉 가격모형 통합 인터페이스.

    Example:
        >>> from hedonic import SpatialHedonicModel
        >>> model = SpatialHedonicModel(
        ...     gdf=ads,
        ...     y="log_price",
        ...     X=["log_area", "building_age", "floor"],
        ...     w=w_knn,
        ...     method="SEM",
        ... )
        >>> results = model.fit()
        >>> print(results.summary())
    """

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        y: str,
        X: list[str],
        w: Optional[W] = None,
        method: ModelMethod = "OLS",
    ):
        """
        Args:
            gdf: 분석 데이터셋 GeoDataFrame
            y: 종속변수 컬럼명 (예: 'log_price')
            X: 설명변수 컬럼명 리스트
            w: 공간가중행렬 (OLS에서는 None 허용)
            method: 'OLS' | 'SLM' | 'SEM' | 'SDM'
        """
        self.gdf = gdf
        self.y_col = y
        self.X_cols = X
        self.w = w
        self.method = method

        self._validate()

    # ------------------------------------------------------------------
    def fit(self) -> HedonicResults:
        """모형 추정 실행. method에 따라 해당 estimator 호출."""
        raise NotImplementedError(
            "TODO: match self.method: "
            "'OLS' → self._fit_ols(), "
            "'SLM' → self._fit_slm(), ..."
        )

    # ------------------------------------------------------------------
    # Private fitters
    # ------------------------------------------------------------------
    def _fit_ols(self) -> HedonicResults:
        """OLS (statsmodels 또는 spreg.OLS)."""
        raise NotImplementedError("TODO: sm.OLS(y, sm.add_constant(X)).fit()")

    def _fit_slm(self) -> HedonicResults:
        """Spatial Lag Model (ML 방식)."""
        raise NotImplementedError("TODO: ML_Lag(y, X, w=self.w).fit()")

    def _fit_sem(self) -> HedonicResults:
        """Spatial Error Model (ML 방식)."""
        raise NotImplementedError("TODO: ML_Error(y, X, w=self.w)")

    def _fit_sdm(self) -> HedonicResults:
        """
        Spatial Durbin Model.

        SDM = y = ρWy + Xβ + WXθ + ε
        설명변수의 공간 lag(WX)까지 추가한 확장 모형.
        """
        raise NotImplementedError(
            "TODO: spreg.ML_Lag(y, np.hstack([X, w_sparse @ X]), w=self.w)"
        )

    def _validate(self) -> None:
        """입력 검증: y/X가 gdf에 존재, method≠'OLS'일 때 w 필수."""
        if self.y_col not in self.gdf.columns:
            raise ValueError(f"y='{self.y_col}'가 gdf에 없습니다.")
        missing = [c for c in self.X_cols if c not in self.gdf.columns]
        if missing:
            raise ValueError(f"X 컬럼 누락: {missing}")
        if self.method != "OLS" and self.w is None:
            raise ValueError(f"method='{self.method}'는 공간가중행렬 w가 필요합니다.")


# ======================================================================
# 비교 헬퍼
# ======================================================================
def compare_models(results_list: list[HedonicResults]) -> pd.DataFrame:
    """
    여러 모형의 R²/AIC/BIC를 한 테이블로 비교.

    Args:
        results_list: [ols_result, slm_result, sem_result, sdm_result]

    Returns:
        columns=['method', 'n', 'k', 'r2', 'aic', 'bic', 'rho', 'lambda']
    """
    raise NotImplementedError("TODO: [r.__dict__ for r in results_list] → DataFrame")
