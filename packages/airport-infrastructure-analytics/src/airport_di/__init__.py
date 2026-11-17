"""
Airport Infrastructure Difference-in-Differences Analytics

군공항 이전·종전부지 재개발의 인근 부동산·경제 효과 분석을
이중차분법(DID) + 합성통제법(Synthetic Control) + 공간 DID로 추정한다.

핵심 사례:
    - 수원 군공항 (이전 추진 → 화성 화옹지구)
    - 광주 군공항 (전남 무안 이전 추진)
    - 대구 군공항 (의성·군위 이전 확정)
    - 김포공항 인근 (소음 영향권 vs 비영향권)

이론:
    - Card & Krueger (1994): DID 표준 설정
    - Abadie, Diamond & Hainmueller (2010): 합성통제법
    - Goodman-Bacon (2021): Two-way FE 분해
    - Callaway & Sant'Anna (2021): Heterogeneous DID

사용 예:
    >>> from airport_di import DIDAnalysis, load_panel
    >>> panel = load_panel("suwon")
    >>> did = DIDAnalysis(panel, treatment_year=2025)
    >>> result = did.run_twfe(outcome="log_apt_price")
    >>> result.summary()
"""

__version__ = "0.1.0"
__author__ = "Dongsoo Jung"
__email__ = "jds068888.gmail.com"

from airport_di.did import DIDAnalysis  # noqa: F401
from airport_di.data_loader import load_panel  # noqa: F401

__all__ = ["DIDAnalysis", "load_panel"]
