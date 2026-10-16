"""환율 정보 API 클라이언트.

한국은행 ECOS 또는 공공데이터 환율 API를 호출한다.
키가 없으면 샘플 CSV를 사용한다.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "sample" / "exchange_rate.csv"


class ExchangeRateClient:
    """주요 통화 환율 시계열 클라이언트."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        self.api_key = (
            api_key
            or os.getenv("EXCHANGE_RATE_KEY")
            or os.getenv("BOK_ECOS_KEY")
        )
        self.base_url = base_url or os.getenv(
            "EXCHANGE_RATE_BASE",
            "https://ecos.bok.or.kr/api/StatisticSearch",
        )
        self.timeout = timeout

    def fetch_rates(
        self,
        currency: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        use_sample: bool = False,
    ) -> pd.DataFrame:
        """환율 시계열 DataFrame.

        Args:
            currency: 'USD', 'EUR', 'JPY', 'CNY' 등. None이면 전체.
            start/end: 'YYYY-MM-DD'
            use_sample: True면 API 건너뛰고 샘플 사용
        """
        if use_sample or not self.api_key:
            logger.info("환율: 샘플 데이터 사용")
            return self._load_sample(currency=currency, start=start, end=end)

        try:
            return self._fetch_api(currency=currency, start=start, end=end)
        except Exception as exc:  # noqa: BLE001
            logger.warning("환율 API 실패, 샘플로 폴백: %s", exc)
            return self._load_sample(currency=currency, start=start, end=end)

    def _fetch_api(
        self,
        currency: Optional[str],
        start: Optional[str],
        end: Optional[str],
    ) -> pd.DataFrame:
        # ECOS StatisticSearch 경로 예시 (키·통계코드는 환경에 맞게 조정)
        start_ymd = (start or "20260101").replace("-", "")
        end_ymd = (end or "20261231").replace("-", "")
        url = (
            f"{self.base_url.rstrip('/')}/{self.api_key}/json/kr/1/1000/"
            f"731Y001/D/{start_ymd}/{end_ymd}"
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        rows = payload.get("StatisticSearch", {}).get("row", [])
        if not rows:
            raise ValueError("ECOS 응답에 행이 없습니다")
        df = pd.DataFrame(rows)
        df = self._normalize(df)
        if currency and "currency" in df.columns:
            df = df[df["currency"] == currency]
        return df.reset_index(drop=True)

    def _load_sample(
        self,
        currency: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        if not SAMPLE_PATH.exists():
            return pd.DataFrame()
        df = pd.read_csv(SAMPLE_PATH)
        df = self._normalize(df)
        if currency and "currency" in df.columns:
            df = df[df["currency"] == currency]
        if start and "date" in df.columns:
            df = df[df["date"] >= pd.Timestamp(start)]
        if end and "date" in df.columns:
            df = df[df["date"] <= pd.Timestamp(end)]
        return df.reset_index(drop=True)

    @staticmethod
    def _normalize(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        rename = {
            "TIME": "date",
            "DATA_VALUE": "rate",
            "ITEM_NAME1": "currency",
            "UNIT_NAME": "unit",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "rate" in df.columns:
            df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
        return df
