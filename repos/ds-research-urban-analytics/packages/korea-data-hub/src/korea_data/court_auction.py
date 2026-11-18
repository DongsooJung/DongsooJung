"""법원 경매 정보 API 클라이언트.

공공데이터포털 법원경매 OpenAPI 또는 샘플 데이터로
경매 물건 목록을 DataFrame으로 반환한다.

API 키(COURT_AUCTION_KEY / DATA_GO_KR_KEY)가 없으면 샘플 데이터를 사용한다.
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

SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "sample" / "court_auction.csv"


class CourtAuctionClient:
    """법원 경매 물건 조회 클라이언트."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        self.api_key = (
            api_key
            or os.getenv("COURT_AUCTION_KEY")
            or os.getenv("DATA_GO_KR_KEY")
        )
        self.base_url = base_url or os.getenv(
            "COURT_AUCTION_BASE",
            "https://apis.data.go.kr/Courtauction",
        )
        self.timeout = timeout

    def fetch_listings(
        self,
        sido: Optional[str] = None,
        limit: int = 100,
        use_sample: bool = False,
    ) -> pd.DataFrame:
        """경매 물건 목록을 DataFrame으로 반환.

        Args:
            sido: 시도 필터 (예: '서울특별시'). None이면 전체.
            limit: 최대 행 수
            use_sample: True면 API를 건너뛰고 샘플 CSV 사용
        """
        if use_sample or not self.api_key:
            logger.info("법원경매: 샘플 데이터 사용 (API 키 없음 또는 use_sample=True)")
            return self._load_sample(sido=sido, limit=limit)

        try:
            return self._fetch_api(sido=sido, limit=limit)
        except Exception as exc:  # noqa: BLE001 — 대시보드 폴백
            logger.warning("법원경매 API 실패, 샘플로 폴백: %s", exc)
            return self._load_sample(sido=sido, limit=limit)

    def _fetch_api(self, sido: Optional[str], limit: int) -> pd.DataFrame:
        """공공데이터포털 법원경매 API 호출 (엔드포인트는 환경에 맞게 조정)."""
        params = {
            "serviceKey": self.api_key,
            "pageNo": 1,
            "numOfRows": min(limit, 1000),
            "type": "json",
        }
        if sido:
            params["sido"] = sido
        resp = requests.get(self.base_url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        items = (
            payload.get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        )
        if isinstance(items, dict):
            items = [items]
        if not items:
            raise ValueError("API 응답에 경매 물건이 없습니다")
        df = pd.DataFrame(items)
        return self._normalize(df).head(limit)

    def _load_sample(
        self, sido: Optional[str] = None, limit: int = 100
    ) -> pd.DataFrame:
        if not SAMPLE_PATH.exists():
            return pd.DataFrame()
        df = pd.read_csv(SAMPLE_PATH)
        df = self._normalize(df)
        if sido and "sido" in df.columns:
            df = df[df["sido"].astype(str) == sido]
        return df.head(limit).reset_index(drop=True)

    @staticmethod
    def _normalize(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        rename = {
            "caseNo": "case_no",
            "courtNm": "court",
            "addr": "address",
            "aprslAmt": "appraisal_amount",
            "minSaleAmt": "min_bid",
            "bidDate": "auction_date",
            "objctNm": "property_type",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        for col in ("appraisal_amount", "min_bid"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "auction_date" in df.columns:
            df["auction_date"] = pd.to_datetime(df["auction_date"], errors="coerce")
        if {"appraisal_amount", "min_bid"} <= set(df.columns):
            df["discount_rate"] = (
                1 - df["min_bid"] / df["appraisal_amount"]
            ).where(df["appraisal_amount"] > 0)
        return df
