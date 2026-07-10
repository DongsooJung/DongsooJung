"""
공간자기상관 진단 및 모형 선택 테스트

핵심 지표:
    - Moran's I    : 전역 공간자기상관
    - Geary's C    : Moran's I 보완
    - LISA         : 국지적 클러스터 (HH/LL/HL/LH)
    - LM tests     : SLM vs SEM 모형 선택 (Anselin 1996)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from libpysal.weights import W
from esda.moran import Moran, Moran_Local
from esda.geary import Geary

logger = logging.getLogger(__name__)


# ======================================================================
# 전역 공간자기상관
# ======================================================================
@dataclass
class MoranResult:
    statistic: float           # Moran's I
    expected: float            # E[I] under null
    variance: float            # Var[I]
    z_score: float             # 표준화 통계량
    p_value: float             # 단측 p-value
    permutations: int          # 순열검정 반복 수


def morans_i(
    values: np.ndarray,
    w: W,
    permutations: int = 999,
) -> MoranResult:
    """
    전역 Moran's I.

    I > 0: 양의 공간자기상관 (유사한 값이 공간적으로 인접)
    I < 0: 음의 공간자기상관 (상반된 값이 인접)
    I ≈ 0: 공간 랜덤

    Args:
        values: 관심 변수 array (예: 실거래가 잔차)
        w: 공간가중행렬 (row-standardized 권장)
        permutations: Monte Carlo 순열 수

    Returns:
        MoranResult 데이터클래스
    """
    raise NotImplementedError(
        "TODO: m = Moran(values, w, permutations=permutations); "
        "MoranResult(statistic=m.I, expected=m.EI, ...)"
    )


def gearys_c(values: np.ndarray, w: W) -> float:
    """Geary's C 계수 (Moran's I 보완 지표)."""
    raise NotImplementedError("TODO: Geary(values, w).C")


# ======================================================================
# 국지적 LISA
# ======================================================================
def local_moran(
    values: np.ndarray,
    w: W,
    significance_level: float = 0.05,
) -> pd.DataFrame:
    """
    Local Indicators of Spatial Association (LISA).

    각 관측치마다 4가지 분류:
        - HH (High-High): 핫스팟
        - LL (Low-Low):   콜드스팟
        - HL (High-Low):  음의 아웃라이어
        - LH (Low-High):  음의 아웃라이어
        - NS: 유의하지 않음

    Returns:
        columns=['Ii', 'z_Ii', 'p_Ii', 'quadrant', 'significant']
    """
    raise NotImplementedError(
        "TODO: Moran_Local(values, w) 결과를 DataFrame으로 변환, "
        "quadrant 1-4 → HH/LH/LL/HL 매핑"
    )


# ======================================================================
# 모형 선택 검정 (Anselin-Florax-Rey)
# ======================================================================
@dataclass
class LMTestResult:
    """LM 검정 결과. SLM과 SEM 중 어느 모형이 적합한지 결정."""

    lm_lag: float              # LM-Lag statistic
    lm_lag_p: float
    lm_error: float            # LM-Error statistic
    lm_error_p: float
    robust_lm_lag: float       # Robust LM-Lag (Anselin 1996)
    robust_lm_lag_p: float
    robust_lm_error: float     # Robust LM-Error
    robust_lm_error_p: float

    def recommend(self) -> str:
        """
        의사결정 룰 (Anselin & Florax 1995):

        1. LM_lag, LM_error 모두 유의하지 않음 → OLS 사용
        2. 하나만 유의 → 해당 모형 선택
        3. 둘 다 유의 → Robust LM 비교 후 더 유의한 쪽 선택
        """
        raise NotImplementedError(
            "TODO: p-value 비교 로직으로 'OLS'|'SLM'|'SEM' 반환"
        )


def lm_diagnostics(ols_result, w: W) -> LMTestResult:
    """
    OLS 잔차 기반 LM 진단.

    Args:
        ols_result: spreg.OLS 결과 객체 (lm_lag, lm_error 등 속성 포함)
        w: 공간가중행렬

    Returns:
        LMTestResult
    """
    raise NotImplementedError(
        "TODO: spreg OLS는 이미 ols_result.lm_lag 등을 계산함, 그대로 래핑"
    )
