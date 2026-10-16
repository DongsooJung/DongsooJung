"""공공데이터포털 공통 래퍼 + MOLIT 실거래 요약.

MOLIT 키(MOLIT_API_KEY)가 있으면 실거래 API를 호출하고,
없으면 샘플 CSV를 사용한다.
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

SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "sample" / "public_molit.csv"


class PublicDataClient:
    """공공데이터포털 / MOLIT 실거래 요약 클라이언트."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("MOLIT_API_KEY") or os.getenv("DATA_GO_KR_KEY")
        self.base_url = base_url or os.getenv(
            "MOLIT_API_BASE",
            "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade",
        )
        self.timeout = timeout
        self.endpoint = f"{self.base_url.rstrip('/')}/getRTMSDataSvcAptTrade"

    def fetch_apt_trades(
        self,
        region_code: str = "11680",
        year_month: str = "202601",
        limit: int = 200,
        use_sample: bool = False,
    ) -> pd.DataFrame:
        """아파트 매매 실거래 요약 DataFrame."""
        if use_sample or not self.api_key:
            logger.info("공공데이터: 샘플 데이터 사용")
            return self._load_sample(region_code=region_code, limit=limit)

        try:
            return self._fetch_api(region_code, year_month, limit)
        except Exception as exc:  # noqa: BLE001
            logger.warning("MOLIT API 실패, 샘플로 폴백: %s", exc)
            return self._load_sample(region_code=region_code, limit=limit)

    def _fetch_api(
        self, region_code: str, year_month: str, limit: int
    ) -> pd.DataFrame:
        params = {
            "serviceKey": self.api_key,
            "LAWD_CD": region_code,
            "DEAL_YMD": year_month,
            "pageNo": 1,
            "numOfRows": min(limit, 1000),
        }
        resp = requests.get(self.endpoint, params=params, timeout=self.timeout)
        resp.raise_for_status()
        # XML 응답 — 간단 파싱 대신 샘플 폴백을 우선 (풀 파서는 molit_api 참고)
        text = resp.text
        if "<item>" not in text:
            raise ValueError("MOLIT 응답에 item이 없습니다")
        # 최소 XML 파싱
        import xml.etree.ElementTree as ET

        root = ET.fromstring(text)
        rows = []
        for item in root.iter("item"):
            rows.append({child.tag: (child.text or "") for child in item})
        if not rows:
            raise ValueError("파싱된 거래가 없습니다")
        df = pd.DataFrame(rows)
        return self._normalize(df, region_code=region_code).head(limit)

    def _load_sample(
        self, region_code: Optional[str] = None, limit: int = 200
    ) -> pd.DataFrame:
        if not SAMPLE_PATH.exists():
            return pd.DataFrame()
        df = pd.read_csv(SAMPLE_PATH)
        df = self._normalize(df)
        if region_code and "region_code" in df.columns:
            df = df[df["region_code"].astype(str) == str(region_code)]
        return df.head(limit).reset_index(drop=True)

    @staticmethod
    def _normalize(
        df: pd.DataFrame, region_code: Optional[str] = None
    ) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        rename = {
            "거래금액": "deal_amount",
            "아파트": "apt_name",
            "법정동": "legal_dong",
            "전용면적": "area",
            "층": "floor",
            "년": "deal_year",
            "월": "deal_month",
            "일": "deal_day",
            "건축년도": "build_year",
            "거래유형": "deal_type",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        if "deal_amount" in df.columns:
            df["deal_amount"] = (
                df["deal_amount"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .pipe(pd.to_numeric, errors="coerce")
            )
        for col in ("area", "floor", "deal_year", "deal_month", "deal_day", "build_year"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if region_code and "region_code" not in df.columns:
            df["region_code"] = region_code
        if {"deal_year", "deal_month", "deal_day"} <= set(df.columns):
            ymd = (
                df["deal_year"].astype("Int64").astype("string")
                + "-"
                + df["deal_month"].astype("Int64").astype("string").str.zfill(2)
                + "-"
                + df["deal_day"].astype("Int64").astype("string").str.zfill(2)
            )
            df["deal_date"] = pd.to_datetime(ymd, format="%Y-%m-%d", errors="coerce")
        if {"deal_amount", "area"} <= set(df.columns):
            df["price_per_sqm"] = df["deal_amount"] / df["area"]
        return df
