"""DID 추정기 단위 테스트 — TWFE / Event Study / 평행추세.

linearmodels 미설치 환경에서도 statsmodels 기반 구현을 검증한다.
Callaway-Sant'Anna·합성통제는 별도 패키지 필요 → 스킵 처리.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airport_di.did import DIDAnalysis, DIDResult
from airport_di.data_loader import load_synthetic_panel


TRUE_EFFECT = -0.05


@pytest.fixture
def synthetic_panel():
    """treatment_effect=-0.05의 합성 패널."""
    return load_synthetic_panel(
        n_treated=5, n_control=30, pre_periods=60, post_periods=24,
        treatment_effect=TRUE_EFFECT, seed=42,
    )


def make_did(panel):
    return DIDAnalysis(
        panel,
        outcome="outcome",
        unit_col="region_code",
        time_col="period",
        treat_col="treatment",
        post_col="post",
    )


# ----------------------------------------------------------------------
# 합성 패널
# ----------------------------------------------------------------------
class TestSyntheticPanel:
    def test_columns(self, synthetic_panel):
        for c in ["region_code", "period", "treatment", "post", "outcome"]:
            assert c in synthetic_panel.columns

    def test_treatment_binary(self, synthetic_panel):
        assert set(synthetic_panel["treatment"].unique()) <= {0, 1}

    def test_post_only_after_threshold(self, synthetic_panel):
        # post==1 은 period>=60 에서만
        assert (synthetic_panel.loc[synthetic_panel["post"] == 1, "period"] >= 60).all()

    def test_reproducible(self):
        a = load_synthetic_panel(seed=1)
        b = load_synthetic_panel(seed=1)
        pd.testing.assert_frame_equal(a, b)


# ----------------------------------------------------------------------
# TWFE
# ----------------------------------------------------------------------
class TestTWFE:
    def test_recovers_known_effect(self, synthetic_panel):
        """합성 데이터에서 처리효과 -0.05를 ±0.01 오차로 추정."""
        did = make_did(synthetic_panel)
        res = did.run_twfe()
        assert abs(res.att - TRUE_EFFECT) < 0.01
        assert res.p_value < 0.05

    def test_result_structure(self, synthetic_panel):
        did = make_did(synthetic_panel)
        res = did.run_twfe()
        assert isinstance(res, DIDResult)
        assert res.estimator == "twfe"
        assert res.n_treated == 5
        assert res.n_control == 30
        assert res.att_ci[0] <= res.att <= res.att_ci[1]

    def test_summary_runs(self, synthetic_panel):
        did = make_did(synthetic_panel)
        res = did.run_twfe()
        s = res.summary()
        assert "ATT" in s and "twfe" in s

    def test_clustered_se_differs_from_iid(self, synthetic_panel):
        did = make_did(synthetic_panel)
        res_cluster = did.run_twfe(cluster_se=True)
        res_iid = did.run_twfe(cluster_se=False)
        # 두 방식의 점추정은 같고 SE는 다름
        assert res_cluster.att == pytest.approx(res_iid.att, rel=1e-9)
        assert res_cluster.att_se != pytest.approx(res_iid.att_se, rel=1e-6)


# ----------------------------------------------------------------------
# Event Study
# ----------------------------------------------------------------------
class TestEventStudy:
    def test_pre_treatment_coefs_near_zero(self, synthetic_panel):
        """처리 이전(event_time<0) 계수는 0 근처 (평행 추세)."""
        did = make_did(synthetic_panel)
        res = did.run_event_study(leads=4, lags=8)
        es = res.raw_result["event_study"]
        pre = es[es["event_time"] < 0]
        assert pre["coef"].abs().max() < 0.02

    def test_post_treatment_negative(self, synthetic_panel):
        """처리 이후(event_time>=0) 계수는 음수 효과를 반영."""
        did = make_did(synthetic_panel)
        res = did.run_event_study(leads=4, lags=8)
        es = res.raw_result["event_study"]
        post = es[es["event_time"] >= 0]
        assert post["coef"].mean() < 0
        assert abs(res.att - TRUE_EFFECT) < 0.02


# ----------------------------------------------------------------------
# 평행추세 검정
# ----------------------------------------------------------------------
class TestParallelTrends:
    def test_parallel_trends_pass(self, synthetic_panel):
        """평행추세를 만족하는 DGP → 검정 통과 (p>0.05)."""
        did = make_did(synthetic_panel)
        result = did.test_parallel_trends()
        assert "p_value" in result and "pass" in result
        assert result["pass"] is True

    def test_parallel_trends_detects_violation(self):
        """처리집단에 사전 추세를 주입하면 검정이 위반을 감지."""
        panel = load_synthetic_panel(
            n_treated=5, n_control=30, pre_periods=60, post_periods=24,
            treatment_effect=-0.05, seed=42,
        )
        # 처리집단에 사전기간 차등 추세 주입
        mask = panel["treatment"] == 1
        panel.loc[mask, "outcome"] += 0.01 * panel.loc[mask, "period"]
        did = make_did(panel)
        result = did.test_parallel_trends()
        assert result["pass"] is False


# ----------------------------------------------------------------------
# 입력 검증
# ----------------------------------------------------------------------
class TestValidation:
    def test_missing_column_raises(self, synthetic_panel):
        with pytest.raises(ValueError):
            DIDAnalysis(synthetic_panel, outcome="nonexistent")

    def test_non_binary_treatment_raises(self, synthetic_panel):
        bad = synthetic_panel.copy()
        bad["treatment"] = 2
        with pytest.raises(ValueError):
            make_did(bad)


# 별도 패키지 필요
class TestUnavailable:
    def test_callaway_santanna_todo(self, synthetic_panel):
        did = make_did(synthetic_panel)
        with pytest.raises(NotImplementedError):
            did.run_callaway_santanna()

    def test_synthetic_control_todo(self, synthetic_panel):
        did = make_did(synthetic_panel)
        with pytest.raises(NotImplementedError):
            did.run_synthetic_control("T000", ["C001", "C002"])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
