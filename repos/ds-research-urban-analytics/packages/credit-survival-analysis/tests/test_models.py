"""생존모형 단위 테스트 — Cox/KM/C-index/합성데이터.

lifelines·scikit-survival 미설치 환경에서도 동작하도록, scipy 기반으로
직접 구현된 Cox PH 와 numpy KaplanMeier 를 검증한다.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from credit_surv.data_loader import (
    load_synthetic_credit_panel,
    to_survival_format,
    TRUE_COEF,
)
from credit_surv.models import (
    KaplanMeier,
    CoxModel,
    concordance_index,
    compare_survival_models,
    SurvivalResult,
)


@pytest.fixture
def synthetic_panel():
    return load_synthetic_credit_panel(n_firms=2000, seed=42)


# ----------------------------------------------------------------------
# 합성 데이터
# ----------------------------------------------------------------------
class TestSyntheticData:
    def test_has_required_columns(self, synthetic_panel):
        for col in ["firm_id", "duration", "event", "roa", "debt_ratio"]:
            assert col in synthetic_panel.columns

    def test_event_is_binary(self, synthetic_panel):
        assert set(synthetic_panel["event"].unique()) <= {0, 1}

    def test_durations_positive(self, synthetic_panel):
        assert (synthetic_panel["duration"] > 0).all()

    def test_has_both_events_and_censoring(self, synthetic_panel):
        assert synthetic_panel["event"].sum() > 0
        assert (synthetic_panel["event"] == 0).sum() > 0

    def test_reproducible(self):
        a = load_synthetic_credit_panel(n_firms=100, seed=7)
        b = load_synthetic_credit_panel(n_firms=100, seed=7)
        pd.testing.assert_frame_equal(a, b)


# ----------------------------------------------------------------------
# concordance_index
# ----------------------------------------------------------------------
class TestConcordance:
    def test_perfect_concordance(self):
        # 위험 높을수록 빨리 사건 → C=1
        durations = np.array([1, 2, 3, 4])
        events = np.array([1, 1, 1, 1])
        risk = np.array([4, 3, 2, 1])  # 짧은 생존 = 높은 위험
        assert concordance_index(durations, events, risk) == pytest.approx(1.0)

    def test_anti_concordance(self):
        durations = np.array([1, 2, 3, 4])
        events = np.array([1, 1, 1, 1])
        risk = np.array([1, 2, 3, 4])  # 완전 반대
        assert concordance_index(durations, events, risk) == pytest.approx(0.0)

    def test_random_near_half(self):
        rng = np.random.default_rng(0)
        n = 500
        durations = rng.exponential(10, n)
        events = np.ones(n, dtype=int)
        risk = rng.normal(0, 1, n)
        c = concordance_index(durations, events, risk)
        assert 0.4 < c < 0.6


# ----------------------------------------------------------------------
# Kaplan-Meier
# ----------------------------------------------------------------------
class TestKM:
    def test_monotone_decreasing(self, synthetic_panel):
        km = KaplanMeier().fit(
            synthetic_panel["duration"], synthetic_panel["event"]
        )
        surv = km.survival_function().iloc[:, 0].to_numpy()
        assert np.all(np.diff(surv) <= 1e-12)

    def test_starts_at_or_below_one(self, synthetic_panel):
        km = KaplanMeier().fit(
            synthetic_panel["duration"], synthetic_panel["event"]
        )
        surv = km.survival_function().iloc[:, 0].to_numpy()
        assert surv[0] <= 1.0
        assert surv[-1] >= 0.0

    def test_no_events_survival_stays_one(self):
        km = KaplanMeier().fit([1, 2, 3, 4], [0, 0, 0, 0])
        surv = km.survival_function().iloc[:, 0].to_numpy()
        assert np.allclose(surv, 1.0)

    def test_all_events_reaches_zero(self):
        km = KaplanMeier().fit([1, 2, 3], [1, 1, 1])
        surv = km.survival_function().iloc[:, 0].to_numpy()
        assert surv[-1] == pytest.approx(0.0)


# ----------------------------------------------------------------------
# Cox PH
# ----------------------------------------------------------------------
class TestCoxModel:
    def test_recovers_known_coefficients(self, synthetic_panel):
        """진짜 계수 debt_ratio=0.5, roa=-0.3 을 ±0.1 내로 복원."""
        cox = CoxModel()
        result = cox.fit(synthetic_panel, covariates=["debt_ratio", "roa"])
        assert result.coefficients["debt_ratio"] == pytest.approx(
            TRUE_COEF["debt_ratio"], abs=0.1
        )
        assert result.coefficients["roa"] == pytest.approx(
            TRUE_COEF["roa"], abs=0.1
        )

    def test_hazard_ratio_known(self, synthetic_panel):
        """HR(debt_ratio) ≈ exp(0.5) = 1.65 ± 0.15."""
        cox = CoxModel()
        result = cox.fit(synthetic_panel, covariates=["debt_ratio", "roa"])
        assert result.hazard_ratios["debt_ratio"] == pytest.approx(
            np.exp(0.5), abs=0.15
        )

    def test_concordance_above_chance(self, synthetic_panel):
        cox = CoxModel()
        result = cox.fit(synthetic_panel, covariates=["debt_ratio", "roa"])
        assert result.concordance_index >= 0.55

    def test_significant_pvalues(self, synthetic_panel):
        cox = CoxModel()
        result = cox.fit(synthetic_panel, covariates=["debt_ratio", "roa"])
        # 강한 신호 → p < 0.05
        assert result.p_values["debt_ratio"] < 0.05

    def test_summary_runs(self, synthetic_panel):
        cox = CoxModel()
        result = cox.fit(synthetic_panel, covariates=["debt_ratio", "roa"])
        s = result.summary()
        assert "Cox" in s and "C-index" in s

    def test_predict_partial_hazard(self, synthetic_panel):
        cox = CoxModel()
        cox.fit(synthetic_panel, covariates=["debt_ratio", "roa"])
        ph = cox.predict_partial_hazard(synthetic_panel.head(5))
        assert len(ph) == 5
        assert (ph > 0).all()


# ----------------------------------------------------------------------
# to_survival_format
# ----------------------------------------------------------------------
class TestToSurvivalFormat:
    def test_basic_conversion(self):
        df = pd.DataFrame({
            "firm_id": ["A", "B", "C"],
            "obs_start": ["2020-01-01", "2020-01-01", "2020-01-01"],
            "default_date": ["2020-12-31", None, None],
        })
        out = to_survival_format(df, censor_date=pd.Timestamp("2021-12-31"))
        assert set(out.columns) == {"firm_id", "duration", "event"}
        # A는 부도(event=1), B·C는 검열(event=0)
        a = out[out["firm_id"] == "A"].iloc[0]
        assert a["event"] == 1
        assert a["duration"] == pytest.approx(365, abs=1)
        b = out[out["firm_id"] == "B"].iloc[0]
        assert b["event"] == 0


# ----------------------------------------------------------------------
# compare_survival_models
# ----------------------------------------------------------------------
class TestCompare:
    def test_compare_table(self, synthetic_panel):
        cox = CoxModel()
        r = cox.fit(synthetic_panel, covariates=["debt_ratio", "roa"])
        km_dummy = SurvivalResult(model_type="KM", n_obs=100, n_events=40)
        table = compare_survival_models([r, km_dummy])
        assert len(table) == 2
        assert "c_index" in table.columns
        assert "model" in table.columns


# 미설치 라이브러리 의존 모형
class TestUnavailableModels:
    def test_aft_requires_lifelines(self, synthetic_panel):
        from credit_surv.models import AFTModel
        with pytest.raises(NotImplementedError):
            AFTModel().fit(synthetic_panel, ["debt_ratio"])

    def test_rsf_requires_sksurv(self, synthetic_panel):
        from credit_surv.models import RSFModel
        with pytest.raises(NotImplementedError):
            RSFModel().fit(synthetic_panel[["debt_ratio"]], None)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
