"""API 키 없이 대시보드를 띄우기 위한 샘플 CSV 생성.

실행:
    python scripts/make_sample.py
출력:
    data/sample/{court_auction,public_molit,exchange_rate,companies}.csv
"""
from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sample"
OUT.mkdir(parents=True, exist_ok=True)

random.seed(42)


def make_court_auction() -> pd.DataFrame:
    courts = [
        ("서울중앙지방법원", "서울특별시", "서초구"),
        ("서울동부지방법원", "서울특별시", "송파구"),
        ("수원지방법원", "경기도", "수원시"),
        ("인천지방법원", "인천광역시", "남동구"),
        ("부산지방법원", "부산광역시", "해운대구"),
    ]
    types = ["아파트", "오피스텔", "다세대", "토지", "상가"]
    rows = []
    for i in range(80):
        court, sido, sgg = random.choice(courts)
        appraisal = random.randint(2, 25) * 100_000_000
        round_n = random.choice([1, 2, 3, 4])
        discount = {1: 1.0, 2: 0.8, 3: 0.64, 4: 0.512}[round_n]
        min_bid = int(appraisal * discount)
        month = random.randint(1, 3)
        day = random.randint(1, 28)
        rows.append(
            {
                "case_no": f"2025타경{10000 + i}",
                "court": court,
                "sido": sido,
                "sgg": sgg,
                "address": f"{sido} {sgg} 샘플로 {i + 1}",
                "property_type": random.choice(types),
                "appraisal_amount": appraisal,
                "min_bid": min_bid,
                "auction_round": round_n,
                "auction_date": f"2026-{month:02d}-{day:02d}",
                "status": random.choice(["진행", "진행", "유찰", "매각"]),
            }
        )
    return pd.DataFrame(rows)


def make_public_molit() -> pd.DataFrame:
    districts = {
        "11680": ("강남구", ["개포동", "역삼동", "대치동"], (2600, 3600)),
        "11650": ("서초구", ["반포동", "서초동"], (2400, 3400)),
        "11710": ("송파구", ["잠실동", "문정동"], (1800, 2700)),
    }
    apts = ["래미안", "자이", "힐스테이트", "푸르지오", "아이파크"]
    areas = [59.9, 84.9, 114.5]
    rows = []
    for ym in ("202601", "202602"):
        year, month = int(ym[:4]), int(ym[4:])
        for code, (gu, dongs, ppsm) in districts.items():
            for _ in range(40):
                area = random.choice(areas) + random.uniform(-1, 1)
                amount = int(area * random.uniform(*ppsm))
                rows.append(
                    {
                        "region_code": code,
                        "region_name": gu,
                        "legal_dong": random.choice(dongs),
                        "apt_name": f"{random.choice(apts)}{gu}",
                        "area": round(area, 2),
                        "floor": random.randint(1, 25),
                        "deal_amount": amount,
                        "deal_year": year,
                        "deal_month": month,
                        "deal_day": random.randint(1, 28),
                        "build_year": random.choice([2005, 2012, 2018, 2022]),
                        "deal_type": random.choice(["중개거래", "직거래"]),
                    }
                )
    return pd.DataFrame(rows)


def make_exchange_rate() -> pd.DataFrame:
    # 2026-01-02 ~ 2026-03-31 영업일 근사
    dates = pd.bdate_range("2026-01-02", "2026-03-31")
    bases = {"USD": 1380.0, "EUR": 1500.0, "JPY": 9.2, "CNY": 190.0}
    rows = []
    for cur, base in bases.items():
        level = base
        for d in dates:
            level += random.uniform(-3, 3)
            rows.append(
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "currency": cur,
                    "rate": round(level, 2),
                    "unit": "KRW",
                }
            )
    return pd.DataFrame(rows)


def make_companies() -> pd.DataFrame:
    firms = [
        ("삼성전자", "C26", "반도체", 280_000, 32_000, 25_000, 450_000, 300_000),
        ("SK하이닉스", "C26", "반도체", 55_000, 12_000, 9_000, 110_000, 70_000),
        ("현대자동차", "C30", "자동차", 160_000, 14_000, 11_000, 280_000, 90_000),
        ("기아", "C30", "자동차", 95_000, 10_000, 8_000, 120_000, 55_000),
        ("LG에너지솔루션", "C28", "배터리", 28_000, 2_500, 1_800, 45_000, 20_000),
        ("네이버", "J62", "IT서비스", 10_000, 1_800, 1_200, 30_000, 22_000),
        ("카카오", "J62", "IT서비스", 7_500, 400, 200, 18_000, 10_000),
        ("포스코홀딩스", "C24", "철강", 75_000, 5_000, 3_500, 90_000, 50_000),
        ("셀트리온", "C21", "바이오", 2_800, 900, 700, 8_000, 5_500),
        ("KB금융", "K64", "금융", 18_000, 6_000, 4_500, 700_000, 50_000),
        ("신한지주", "K64", "금융", 16_000, 5_500, 4_000, 650_000, 45_000),
        ("아모레퍼시픽", "C20", "화장품", 4_200, 350, 250, 7_000, 4_000),
    ]
    rows = []
    for i, (name, ksic, industry, rev, op, ni, assets, equity) in enumerate(firms):
        rows.append(
            {
                "corp_code": f"{10000000 + i:08d}",
                "corp_name": name,
                "stock_code": f"{1000 + i * 17:06d}",
                "ksic": ksic,
                "industry": industry,
                "revenue": rev,  # 억원
                "operating_profit": op,
                "net_income": ni,
                "assets": assets,
                "equity": equity,
                "fiscal_year": 2025,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    datasets = {
        "court_auction.csv": make_court_auction(),
        "public_molit.csv": make_public_molit(),
        "exchange_rate.csv": make_exchange_rate(),
        "companies.csv": make_companies(),
    }
    for name, df in datasets.items():
        path = OUT / name
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"wrote {path} ({len(df)} rows)")


if __name__ == "__main__":
    main()
