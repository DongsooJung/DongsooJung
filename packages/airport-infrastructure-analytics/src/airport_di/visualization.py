"""
DID 분석 전용 시각화."""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

COLORS = {
    "treated": "#e74c3c",      # 빨강 (처리집단)
    "control": "#3498db",      # 파랑 (통제집단)
    "synthetic": "#f39c12",    # 주황 (합성통제)
    "ci": "#bdc3c7",           # 회색 (신뢰구간)
    "treatment_line": "#2c3e50",
}


def plot_outcome_timeseries(
    df: pd.DataFrame,
    outcome: str,
    unit_col: str = "region_code",
    time_col: str = "year_month",
    treat_col: str = "treatment",
    treatment_year: Optional[int] = None,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    처리·통제 집단 outcome 시계열 비교.

    빨간 점선: 처리시점
    빨간 실선: 처리집단 평균
    파란 실선: 통제집단 평균
    """
    raise NotImplementedError(
        "TODO: groupby([time_col, treat_col])[outcome].mean().unstack() → ax.plot()"
    )


def plot_event_study(
    event_coefs: pd.DataFrame,
    ax: Optional[plt.Axes] = None,
    title: str = "Event Study: 동태적 처리효과",
) -> plt.Axes:
    """
    Event Study coefficient plot.

    Args:
        event_coefs: ['event_time', 'coef', 'se'] 컬럼

    x축: event_time (-leads ... 0 ... +lags)
    y축: 계수 + 95% CI 에러바
    수직선: t=0 (처리시점)
    수평선: y=0 (효과 없음)
    """
    raise NotImplementedError(
        "TODO: ax.errorbar(event_time, coef, yerr=1.96*se); "
        "ax.axvline(0, ls='--'); ax.axhline(0, ls=':')"
    )


def plot_synthetic_control(
    treated_path: pd.Series,
    synthetic_path: pd.Series,
    treatment_period: int,
    title: str = "합성통제법 — 실제 vs 합성",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    합성통제 vs 실제 처리집단 outcome 비교.

    처리시점 이후 두 경로의 차이가 처리효과.
    """
    raise NotImplementedError(
        "TODO: ax.plot(treated, color=COLORS['treated']); "
        "ax.plot(synthetic, color=COLORS['synthetic'], linestyle='--')"
    )


def plot_placebo_test(
    placebo_gaps: pd.DataFrame,
    treated_gap: pd.Series,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    합성통제 placebo 검정 — 통제집단 각각을 가짜 처리집단으로 합성한 결과.

    실제 처리집단의 gap이 placebo 분포의 outlier인지 시각적으로 확인.
    """
    raise NotImplementedError(
        "TODO: 회색 placebo lines + 빨간 실제 treated line"
    )


def plot_dose_response(
    df: pd.DataFrame,
    distance_col: str = "dist_to_airport_km",
    outcome: str = "log_price",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    공항까지 거리에 따른 outcome 변화 (dose-response 곡선).

    bins로 거리 그룹핑 후 평균 outcome scatter + LOWESS smooth.
    """
    raise NotImplementedError(
        "TODO: distance bin → groupby mean → scatter + statsmodels.nonparametric.lowess"
    )
