"""
신용 생존데이터 로더

생존분석 표준 형식:
    columns:
        - firm_id: str
        - duration: float (관측 시작부터 사건/검열까지 기간, 일)
        - event: 0/1 (1=부도, 0=관측 종료까지 생존)
        - covariates: 재무비율, 산업, 거시 변수 등
"""
from __future__ import annotations

import logging
from typing import Literal, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

EventType = Literal["default", "downgrade", "delisting"]

# 합성 데이터의 진짜 계수 (검증 기준값)
TRUE_COEF = {"debt_ratio": 0.5, "roa": -0.3}


def load_credit_panel(
    event_type: EventType = "default",
    data_dir: str = "data/processed",
    industries: Optional[list[str]] = None,
    year_range: Optional[tuple[int, int]] = None,
) -> pd.DataFrame:
    """
    신용 생존데이터 로드.

    Args:
        event_type: 'default' | 'downgrade' | 'delisting'
        data_dir: parquet 파일 경로
        industries: KSIC 코드 필터 (예: ['C', 'F'] = 제조·건설)
        year_range: 관측 시작 연도 범위

    Returns:
        long-format 또는 단일행 형식 DataFrame
    """
    import os

    path = os.path.join(data_dir, f"credit_{event_type}.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} 없음. 합성 데이터는 load_synthetic_credit_panel() 사용."
        )

    df = pd.read_parquet(path)
    if industries is not None and "industry_ksic" in df.columns:
        df = df[df["industry_ksic"].isin(industries)]
    if year_range is not None and "obs_year" in df.columns:
        lo, hi = year_range
        df = df[(df["obs_year"] >= lo) & (df["obs_year"] <= hi)]
    return df.reset_index(drop=True)


def load_synthetic_credit_panel(
    n_firms: int = 1000,
    max_duration: int = 365 * 5,
    censoring_rate: float = 0.6,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Cox 모형 검증용 합성 생존 데이터 생성.

    True hazard (비례위험):
        h(t|x) = h₀(t) × exp(0.5·debt_ratio - 0.3·roa)
    Weibull baseline 으로 사건시간을 역변환 샘플링한다.

    Args:
        n_firms: 기업 수
        max_duration: 행정검열 시점(일)
        censoring_rate: 목표 검열 비율(랜덤 dropout으로 근사)
        seed: 난수 시드

    Returns:
        ['firm_id', 'duration', 'event', 'roa', 'debt_ratio', 'industry'] 컬럼
    """
    rng = np.random.default_rng(seed)

    # 표준화된 공변량
    debt_ratio = rng.normal(0.0, 1.0, n_firms)
    roa = rng.normal(0.0, 1.0, n_firms)
    industry = rng.choice(["C", "F", "G", "J"], size=n_firms)

    lp = TRUE_COEF["debt_ratio"] * debt_ratio + TRUE_COEF["roa"] * roa

    # Weibull baseline: shape k, scale 설정. 역변환 샘플링
    #   S(t) = exp(-(lambda * t^k) * exp(lp)),  T = (-ln U / (lambda e^lp))^(1/k)
    k = 1.5
    lam = 1.0 / (max_duration ** k)  # 평균 사건시간이 관측창과 비슷하도록 스케일
    u = rng.uniform(0.0, 1.0, n_firms)
    event_time = (-np.log(u) / (lam * np.exp(lp))) ** (1.0 / k)

    # 랜덤 검열 시간 (지수분포) — censoring_rate 근사
    # 행정검열(max_duration)도 함께 적용
    cens_scale = max_duration * (1.0 - censoring_rate) / max(censoring_rate, 1e-3)
    cens_scale = max(cens_scale, max_duration * 0.1)
    censor_time = rng.exponential(cens_scale, n_firms)
    censor_time = np.minimum(censor_time, max_duration)

    duration = np.minimum(event_time, censor_time)
    event = (event_time <= censor_time).astype(int)

    df = pd.DataFrame({
        "firm_id": [f"F{i:05d}" for i in range(n_firms)],
        "duration": duration,
        "event": event,
        "roa": roa,
        "debt_ratio": debt_ratio,
        "industry": industry,
    })
    logger.info(
        "합성 패널 생성: n=%d, 사건=%d (%.1f%%), 검열=%.1f%%",
        n_firms, event.sum(), 100 * event.mean(), 100 * (1 - event.mean()),
    )
    return df


def to_survival_format(
    transactions: pd.DataFrame,
    firm_id_col: str = "firm_id",
    start_col: str = "obs_start",
    event_col: str = "default_date",
    censor_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Long-format → 생존 표준 (duration, event) 형식 변환.

    각 기업의 관측 시작일과 사건일(있으면)로 duration·event를 계산한다.
    사건일이 없으면 censor_date(기본: 전체 최대 사건일)로 검열 처리.

    Args:
        transactions: 기업별 [firm_id, obs_start, default_date(optional)] 포함
        censor_date: 검열 기준일 (None이면 관측된 사건일의 최댓값)

    Returns:
        ['firm_id', 'duration', 'event'] DataFrame
    """
    df = transactions.copy()
    df[start_col] = pd.to_datetime(df[start_col])
    if event_col in df.columns:
        df[event_col] = pd.to_datetime(df[event_col])

    # 기업별 첫 관측일 / 사건일
    grouped = df.groupby(firm_id_col)
    start = grouped[start_col].min()
    event_date = (
        grouped[event_col].min()
        if event_col in df.columns
        else pd.Series(pd.NaT, index=start.index)
    )

    if censor_date is None:
        valid = event_date.dropna()
        censor_date = valid.max() if len(valid) else start.max()
    censor_date = pd.Timestamp(censor_date)

    end = event_date.where(event_date.notna(), censor_date)
    event = event_date.notna().astype(int)
    duration = (end - start).dt.days.astype(float)

    out = pd.DataFrame({
        "firm_id": start.index,
        "duration": duration.values,
        "event": event.values,
    }).reset_index(drop=True)
    # 음수/0 duration 방지
    out = out[out["duration"] >= 0].reset_index(drop=True)
    return out
