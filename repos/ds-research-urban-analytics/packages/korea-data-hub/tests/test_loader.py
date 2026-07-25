"""dashboard/loader 오프라인 테스트."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_LOADER = ROOT / "dashboard" / "loader.py"
_spec = importlib.util.spec_from_file_location("hub_loader", _LOADER)
loader = importlib.util.module_from_spec(_spec)
sys.modules["hub_loader"] = loader
_spec.loader.exec_module(loader)


@pytest.fixture(scope="module", autouse=True)
def _ensure_sample():
    if not (ROOT / "data" / "sample" / "companies.csv").exists():
        sys.path.insert(0, str(ROOT / "scripts"))
        import make_sample

        make_sample.main()


def test_load_all():
    assert len(loader.load_court_auction(use_sample=True)) > 0
    assert len(loader.load_public_data(use_sample=True)) > 0
    assert len(loader.load_exchange_rates(use_sample=True)) > 0
    assert len(loader.load_companies(use_sample=True)) > 0
