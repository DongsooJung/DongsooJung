"""
Real Estate Hedonic Price Model (Korea)

공간자기상관을 보정한 한국 아파트 헤도닉 가격모형 파이썬 패키지.

주요 모듈:
    molit_api      : 국토교통부 실거래가 OpenAPI 클라이언트
    geocoding      : Kakao Local API 기반 주소→좌표 변환
    preprocessing  : 결측·이상치 처리, 파생변수 생성, 공간조인
    weights        : 공간가중행렬 생성 (Queen/Rook/KNN/Distance)
    models         : OLS/SLM/SEM/SDM 추정 및 비교
    diagnostics    : Moran's I, LM test, AIC/BIC 비교
    visualization  : 가격 히트맵, LISA 클러스터, 잔차 공간패턴

사용 예:
    >>> from hedonic import MolitClient, SpatialHedonicModel
    >>> client = MolitClient()
    >>> df = client.fetch_transactions(region_code="11680", year_month="202601")
    >>> model = SpatialHedonicModel(df, method="SEM")
    >>> results = model.fit()
    >>> results.summary()
"""

__version__ = "0.1.0"
__author__ = "Dongsoo Jung"
__email__ = "jds068888@gmail.com"

# Public API
from hedonic.molit_api import MolitClient  # noqa: F401
from hedonic.models import SpatialHedonicModel  # noqa: F401

__all__ = ["MolitClient", "SpatialHedonicModel"]
