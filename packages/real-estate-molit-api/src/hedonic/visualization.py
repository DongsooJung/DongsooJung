"""
시각화 모듈

부동산 공간분석을 위한 시각화 패턴:
    1. 가격 히트맵 (choropleth)
    2. LISA 클러스터 맵
    3. 잔차 공간 패턴
    4. 계수 비교 차트 (4모형)
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


# 브랜드 컬러 (Stargate Navy/Gold)
COLORS = {
    "navy": "#1B3A5C",
    "gold": "#D4AF37",
    "mint": "#4ecca3",
    "red": "#e74c3c",
    "gray": "#7f8c8d",
}


def plot_price_choropleth(
    gdf: gpd.GeoDataFrame,
    value_col: str = "price_per_sqm",
    cmap: str = "YlOrRd",
    title: str = "㎡당 거래가격",
    ax=None,
) -> plt.Axes:
    """행정동별 평균가격 choropleth."""
    raise NotImplementedError(
        "TODO: gdf.dissolve('dong_code', aggfunc='mean').plot(column, cmap, legend=True)"
    )


def plot_lisa_cluster(
    gdf: gpd.GeoDataFrame,
    lisa_df: pd.DataFrame,
    ax=None,
) -> plt.Axes:
    """
    LISA 클러스터 맵.

    색상:
        HH → 빨간색 (핫스팟)
        LL → 파란색 (콜드스팟)
        HL → 주황색
        LH → 하늘색
        NS → 회색 (비유의)
    """
    raise NotImplementedError(
        "TODO: gdf.merge(lisa_df).plot(column='quadrant', categorical=True, cmap=...)"
    )


def plot_residual_map(
    gdf: gpd.GeoDataFrame,
    residuals: np.ndarray,
    title: str = "모형 잔차 공간 분포",
    ax=None,
) -> plt.Axes:
    """OLS 잔차의 공간 패턴 시각화. 공간자기상관이 보이면 SEM 필요 신호."""
    raise NotImplementedError(
        "TODO: gdf.assign(resid=residuals).plot(column='resid', cmap='RdBu_r', legend=True)"
    )


def plot_coefficient_comparison(
    results_list: list,
    coef_name: str,
    title: Optional[str] = None,
) -> plt.Figure:
    """
    4개 모형(OLS/SLM/SEM/SDM)의 동일 계수 비교 forest plot.

    Args:
        results_list: HedonicResults 리스트
        coef_name: 비교할 계수명 (예: 'log_area')

    Returns:
        matplotlib Figure (에러바 + 점추정치)
    """
    raise NotImplementedError(
        "TODO: method별 coef ± 1.96*se 에러바, seaborn catplot"
    )


def plot_model_fit_comparison(comparison_df: pd.DataFrame) -> plt.Figure:
    """4개 모형의 R²/AIC/BIC 비교 막대그래프 3-panel."""
    raise NotImplementedError(
        "TODO: fig, axes = plt.subplots(1, 3), axes[0].bar('method', 'r2'), ..."
    )
