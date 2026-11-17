"""
주소 → 위경도 지오코딩

Kakao Local API를 사용하여 MOLIT 실거래 주소(법정동 + 지번)를
WGS84 좌표(EPSG:4326)로 변환한다.

Kakao API: https://developers.kakao.com/docs/latest/ko/local/dev-guide
Rate limit: 300,000 requests/day (개인 무료 계정 기준)
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional
from functools import lru_cache

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class KakaoGeocoder:
    """
    Kakao Local API 지오코딩 래퍼.

    Features:
        - 메모리 캐시 (동일 주소 중복 호출 방지)
        - 자동 rate limit 준수 (10 req/sec)
        - 실패 주소 별도 로깅

    Example:
        >>> geo = KakaoGeocoder()
        >>> lon, lat = geo.geocode("서울시 강남구 대치동 890")
        (127.0523, 37.4956)
    """

    ENDPOINT = "https://dapi.kakao.com/v2/local/search/address.json"
    RATE_LIMIT_SLEEP = 0.1  # 10 req/sec

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("KAKAO_REST_API_KEY")
        if not self.api_key:
            raise ValueError("KAKAO_REST_API_KEY가 설정되지 않았습니다.")
        self.headers = {"Authorization": f"KakaoAK {self.api_key}"}
        self.failed_addresses: list[str] = []

    # ------------------------------------------------------------------
    @lru_cache(maxsize=10_000)
    def geocode(self, address: str) -> Optional[tuple[float, float]]:
        """
        단일 주소 → (경도, 위도) 변환.

        Returns:
            (longitude, latitude) or None (실패 시)

        Note:
            - 실패한 주소는 self.failed_addresses에 기록
            - 같은 주소 재호출 시 캐시에서 즉시 반환
        """
        raise NotImplementedError(
            "TODO: requests.get(ENDPOINT, params={'query': address})"
            " → response.json()['documents'][0]['x','y']"
        )

    def geocode_dataframe(
        self,
        df: pd.DataFrame,
        address_col: str = "full_address",
        lon_col: str = "longitude",
        lat_col: str = "latitude",
    ) -> pd.DataFrame:
        """
        DataFrame의 주소 컬럼을 일괄 지오코딩.

        Args:
            df: 입력 DataFrame
            address_col: 주소 컬럼명
            lon_col, lat_col: 출력 좌표 컬럼명

        Returns:
            lon_col, lat_col이 추가된 DataFrame (원본 복사)
        """
        raise NotImplementedError(
            "TODO: df[address_col].progress_apply(self.geocode) 후 "
            "[longitude, latitude] 컬럼 분리"
        )

    # ------------------------------------------------------------------
    def save_failed_log(self, path: str = "data/interim/geocode_failed.txt") -> None:
        """지오코딩 실패한 주소 목록을 파일로 저장."""
        raise NotImplementedError("TODO: Path(path).write_text('\\n'.join(...))")


# ----------------------------------------------------------------------
# 주소 정규화 헬퍼
# ----------------------------------------------------------------------
def build_full_address(row: pd.Series) -> str:
    """
    MOLIT 실거래 행에서 지오코딩용 전체 주소 생성.

    Format: '{시도} {시군구} {legal_dong} {jibun}'

    Args:
        row: {'legal_dong', 'jibun'} 등을 포함한 Series

    Returns:
        정규화된 전체 주소 문자열
    """
    raise NotImplementedError(
        "TODO: region_code → 시도/시군구 매핑 + legal_dong + jibun 연결"
    )
