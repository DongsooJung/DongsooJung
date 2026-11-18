"""대시보드용 데이터 로더.

korea_data 클라이언트를 통해 샘플/API 데이터를 로드한다.
Streamlit이 hedonic/geopandas 등 무거운 스택 없이도 동작하도록
패키지 경로만 sys.path에 추가한다.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from korea_data.court_auction import CourtAuctionClient  # noqa: E402
from korea_data.dart_client import DartClient  # noqa: E402
from korea_data.exchange_rate import ExchangeRateClient  # noqa: E402
from korea_data.public_data import PublicDataClient  # noqa: E402


def load_court_auction(
    sido: Optional[str] = None,
    use_sample: bool = True,
    limit: int = 500,
) -> pd.DataFrame:
    return CourtAuctionClient().fetch_listings(
        sido=sido, limit=limit, use_sample=use_sample
    )


def load_public_data(
    region_code: str = "11680",
    year_month: str = "202601",
    use_sample: bool = True,
    limit: int = 500,
) -> pd.DataFrame:
    return PublicDataClient().fetch_apt_trades(
        region_code=region_code,
        year_month=year_month,
        limit=limit,
        use_sample=use_sample,
    )


def load_exchange_rates(
    currency: Optional[str] = None,
    use_sample: bool = True,
) -> pd.DataFrame:
    return ExchangeRateClient().fetch_rates(
        currency=currency, use_sample=use_sample
    )


def load_companies(
    query: Optional[str] = None,
    industry: Optional[str] = None,
    use_sample: bool = True,
    limit: int = 200,
) -> pd.DataFrame:
    return DartClient().fetch_companies(
        query=query, industry=industry, limit=limit, use_sample=use_sample
    )
