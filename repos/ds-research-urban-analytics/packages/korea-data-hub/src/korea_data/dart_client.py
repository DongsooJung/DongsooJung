"""DART(전자공시) 기업 정보 API 클라이언트.

DART_API_KEY가 없으면 샘플 CSV를 사용한다.
문서: https://opendart.fss.or.kr
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

SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "sample" / "companies.csv"


class DartClient:
    """DART 기업 개요·재무 요약 클라이언트."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("DART_API_KEY")
        self.base_url = base_url or os.getenv(
            "DART_API_BASE",
            "https://opendart.fss.or.kr/api",
        )
        self.timeout = timeout

    def fetch_companies(
        self,
        query: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 100,
        use_sample: bool = False,
    ) -> pd.DataFrame:
        """기업 목록/개요 DataFrame.

        Args:
            query: 기업명 부분 검색
            industry: 업종 필터
            limit: 최대 행 수
            use_sample: True면 API 건너뛰고 샘플 사용
        """
        if use_sample or not self.api_key:
            logger.info("DART: 샘플 데이터 사용")
            return self._load_sample(query=query, industry=industry, limit=limit)

        try:
            return self._fetch_api(query=query, limit=limit)
        except Exception as exc:  # noqa: BLE001
            logger.warning("DART API 실패, 샘플로 폴백: %s", exc)
            return self._load_sample(query=query, industry=industry, limit=limit)

    def _fetch_api(self, query: Optional[str], limit: int) -> pd.DataFrame:
        # corpCode.xml 전체 다운로드는 무거우므로, 샘플 폴백을 기본으로 두고
        # 키가 있을 때 company.json 단건 조회를 시도하는 최소 구현
        params = {"crtfc_key": self.api_key, "corp_code": query or "00126380"}
        url = f"{self.base_url.rstrip('/')}/company.json"
        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") not in (None, "000"):
            raise ValueError(payload.get("message", "DART 오류"))
        row = {
            "corp_code": payload.get("corp_code"),
            "corp_name": payload.get("corp_name"),
            "stock_code": payload.get("stock_code"),
            "industry": payload.get("induty_code"),
            "ceo": payload.get("ceo_nm"),
            "address": payload.get("adres"),
            "established": payload.get("est_dt"),
        }
        df = pd.DataFrame([row])
        return self._normalize(df).head(limit)

    def _load_sample(
        self,
        query: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        if not SAMPLE_PATH.exists():
            return pd.DataFrame()
        df = pd.read_csv(SAMPLE_PATH)
        df = self._normalize(df)
        if query and "corp_name" in df.columns:
            df = df[df["corp_name"].astype(str).str.contains(query, case=False, na=False)]
        if industry and "industry" in df.columns:
            df = df[df["industry"] == industry]
        return df.head(limit).reset_index(drop=True)

    @staticmethod
    def _normalize(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        for col in ("revenue", "operating_profit", "net_income", "assets", "equity"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if {"revenue", "operating_profit"} <= set(df.columns):
            df["op_margin"] = (
                df["operating_profit"] / df["revenue"]
            ).where(df["revenue"] > 0)
        if {"assets", "equity"} <= set(df.columns):
            df["debt_ratio"] = (
                (df["assets"] - df["equity"]) / df["equity"]
            ).where(df["equity"] > 0)
        return df
