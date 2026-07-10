"""
Credit Survival Analysis

한국 기업의 신용위험을 생존분석(Survival Analysis)으로 모형화한다.

타깃 사건(Event):
    - 부도(default): 회생/파산/대출원리금 90일 이상 연체
    - 신용등급 하락: BBB- → BB+ 등 투기등급 진입
    - 폐업/청산

추정 방법:
    1. Kaplan-Meier        - 비모수 생존함수
    2. Cox Proportional Hazards - 준모수 회귀
    3. AFT (Accelerated Failure Time) - 모수 모형 (Weibull, log-normal)
    4. Random Survival Forest (RSF) - ML 기반
    5. DeepSurv/DeepHit    - 딥러닝 기반 (PyTorch)

데이터 소스:
    - DART 재무제표
    - 한국기업데이터(KED) 신용평가
    - KIS-Value
    - 통계청 기업통계

이론:
    - Cox (1972): Regression models and life-tables
    - Ishwaran et al. (2008): Random Survival Forest
    - Katzman et al. (2018): DeepSurv
"""

__version__ = "0.1.0"
__author__ = "Dongsoo Jung"
__email__ = "jds068888@gmail.com"

from credit_surv.models import CoxModel, RSFModel  # noqa: F401
from credit_surv.data_loader import load_credit_panel  # noqa: F401

__all__ = ["CoxModel", "RSFModel", "load_credit_panel"]
