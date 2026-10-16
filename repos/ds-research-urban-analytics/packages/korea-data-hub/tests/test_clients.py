"""korea_data 클라이언트·정규화 테스트 (오프라인, 샘플 CSV)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from korea_data.court_auction import CourtAuctionClient
from korea_data.dart_client import DartClient
from korea_data.exchange_rate import ExchangeRateClient
from korea_data.public_data import PublicDataClient


@pytest.fixture(scope="module", autouse=True)
def _ensure_sample():
    sample_dir = ROOT / "data" / "sample"
    if not (sample_dir / "court_auction.csv").exists():
        sys.path.insert(0, str(ROOT / "scripts"))
        import make_sample

        make_sample.main()


class TestCourtAuction:
    def test_sample_load(self):
        df = CourtAuctionClient().fetch_listings(use_sample=True)
        assert len(df) > 0
        assert "case_no" in df.columns
        assert "discount_rate" in df.columns

    def test_sido_filter(self):
        df = CourtAuctionClient().fetch_listings(sido="서울특별시", use_sample=True)
        assert len(df) > 0
        assert (df["sido"] == "서울특별시").all()


class TestPublicData:
    def test_sample_load(self):
        df = PublicDataClient().fetch_apt_trades(use_sample=True)
        assert len(df) > 0
        assert "deal_amount" in df.columns
        assert "price_per_sqm" in df.columns

    def test_region_filter(self):
        df = PublicDataClient().fetch_apt_trades(
            region_code="11680", use_sample=True
        )
        assert (df["region_code"].astype(str) == "11680").all()


class TestExchangeRate:
    def test_sample_load(self):
        df = ExchangeRateClient().fetch_rates(use_sample=True)
        assert len(df) > 0
        assert set(df["currency"].unique()) >= {"USD", "EUR"}

    def test_currency_filter(self):
        df = ExchangeRateClient().fetch_rates(currency="USD", use_sample=True)
        assert (df["currency"] == "USD").all()
        assert df["date"].is_monotonic_increasing or len(df) > 1


class TestDart:
    def test_sample_load(self):
        df = DartClient().fetch_companies(use_sample=True)
        assert len(df) >= 5
        assert "op_margin" in df.columns
        assert "debt_ratio" in df.columns

    def test_industry_filter(self):
        df = DartClient().fetch_companies(industry="반도체", use_sample=True)
        assert len(df) >= 1
        assert (df["industry"] == "반도체").all()

    def test_query_filter(self):
        df = DartClient().fetch_companies(query="삼성", use_sample=True)
        assert len(df) >= 1
        assert df["corp_name"].str.contains("삼성").any()


class TestNormalizeEmpty:
    def test_empty_frames(self):
        assert CourtAuctionClient._normalize(pd.DataFrame()).empty
        assert PublicDataClient._normalize(pd.DataFrame()).empty
        assert ExchangeRateClient._normalize(pd.DataFrame()).empty
        assert DartClient._normalize(pd.DataFrame()).empty
