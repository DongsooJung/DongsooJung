"""Korea Data Hub 통합 대시보드 (Streamlit).

실행:
    python scripts/make_sample.py
    streamlit run dashboard/app.py

탭 구성:
    종합       — KPI·교차 요약
    법원경매   — 물건·할인율·법원별 집계
    공공데이터 — MOLIT 실거래 요약
    환율       — 주요 통화 시계열
    기업정보   — DART 재무 요약
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loader import (  # noqa: E402
    load_companies,
    load_court_auction,
    load_exchange_rates,
    load_public_data,
)

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = ROOT / "data" / "sample"

st.set_page_config(
    page_title="Korea Data Hub",
    page_icon="📡",
    layout="wide",
)

st.title("Korea Data Hub")
st.caption("법원경매 · 공공데이터 · 환율 · 기업정보(DART) 통합 대시보드")

# ----------------------------------------------------------------------
# 사이드바
# ----------------------------------------------------------------------
st.sidebar.header("데이터 소스")
use_sample = st.sidebar.toggle(
    "샘플 데이터 사용",
    value=True,
    help="API 키 없이 데모하려면 켜 두세요. 끄면 .env 키로 실 API를 시도합니다.",
)

if not SAMPLE_DIR.exists() or not any(SAMPLE_DIR.glob("*.csv")):
    st.sidebar.warning("`python scripts/make_sample.py` 로 샘플을 생성하세요.")

st.sidebar.divider()
st.sidebar.header("필터")
sido_filter = st.sidebar.selectbox(
    "경매 시도",
    ["(전체)", "서울특별시", "경기도", "인천광역시", "부산광역시"],
)
region_code = st.sidebar.selectbox(
    "실거래 지역코드",
    [
        ("11680", "강남구"),
        ("11650", "서초구"),
        ("11710", "송파구"),
        ("(전체)", "전체 샘플"),
    ],
    format_func=lambda x: f"{x[1]} ({x[0]})" if x[0] != "(전체)" else x[1],
)
currency_filter = st.sidebar.multiselect(
    "환율 통화",
    ["USD", "EUR", "JPY", "CNY"],
    default=["USD", "EUR"],
)
industry_filter = st.sidebar.selectbox(
    "기업 업종",
    ["(전체)", "반도체", "자동차", "배터리", "IT서비스", "철강", "바이오", "금융", "화장품"],
)

# ----------------------------------------------------------------------
# 데이터 로드
# ----------------------------------------------------------------------
@st.cache_data(show_spinner="데이터 로딩…")
def _court(sido: str | None, sample: bool) -> pd.DataFrame:
    return load_court_auction(sido=sido, use_sample=sample)


@st.cache_data(show_spinner=False)
def _public(code: str, sample: bool) -> pd.DataFrame:
    if code == "(전체)":
        sys.path.insert(0, str(ROOT / "src"))
        from korea_data.public_data import PublicDataClient

        return PublicDataClient()._load_sample(region_code=None, limit=500)
    return load_public_data(region_code=code, use_sample=sample)


@st.cache_data(show_spinner=False)
def _fx(sample: bool) -> pd.DataFrame:
    return load_exchange_rates(use_sample=sample)


@st.cache_data(show_spinner=False)
def _corp(industry: str | None, sample: bool) -> pd.DataFrame:
    return load_companies(industry=industry, use_sample=sample)


sido_arg = None if sido_filter == "(전체)" else sido_filter
ind_arg = None if industry_filter == "(전체)" else industry_filter

df_court = _court(sido_arg, use_sample)
df_public = _public(region_code[0], use_sample)
df_fx = _fx(use_sample)
df_corp = _corp(ind_arg, use_sample)

if currency_filter and not df_fx.empty and "currency" in df_fx.columns:
    df_fx_view = df_fx[df_fx["currency"].isin(currency_filter)].copy()
else:
    df_fx_view = df_fx.copy()

# ----------------------------------------------------------------------
# 탭
# ----------------------------------------------------------------------
tab_overview, tab_auction, tab_public, tab_fx, tab_corp = st.tabs(
    ["종합", "법원경매", "공공데이터", "환율", "기업정보"]
)

# ===== 종합 =====
with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("경매 물건", f"{len(df_court):,}")
    c2.metric("실거래 건수", f"{len(df_public):,}")
    if not df_fx_view.empty and "rate" in df_fx_view.columns:
        usd = df_fx_view[df_fx_view.get("currency", pd.Series(dtype=str)) == "USD"]
        if not usd.empty:
            c3.metric("USD/KRW (최근)", f"{usd['rate'].iloc[-1]:,.1f}")
        else:
            c3.metric("환율 행 수", f"{len(df_fx_view):,}")
    else:
        c3.metric("환율 행 수", "0")
    c4.metric("기업 수", f"{len(df_corp):,}")

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("경매 최저가 할인율 분포")
        if df_court.empty or "discount_rate" not in df_court.columns:
            st.info("경매 데이터가 없습니다. `python scripts/make_sample.py`를 실행하세요.")
        else:
            fig = px.histogram(
                df_court.dropna(subset=["discount_rate"]),
                x="discount_rate",
                nbins=20,
                labels={"discount_rate": "할인율 (1 − 최저가/감정가)"},
            )
            fig.update_layout(yaxis_title="건수", margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("업종별 영업이익률")
        if df_corp.empty or "op_margin" not in df_corp.columns:
            st.info("기업 데이터가 없습니다.")
        else:
            g = (
                df_corp.dropna(subset=["op_margin"])
                .groupby("industry", observed=True)["op_margin"]
                .mean()
                .reset_index()
                .sort_values("op_margin", ascending=False)
            )
            fig = px.bar(
                g,
                x="op_margin",
                y="industry",
                orientation="h",
                labels={"op_margin": "평균 영업이익률", "industry": "업종"},
            )
            fig.update_layout(yaxis_title="", margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("USD 환율 vs ㎡당 단가 (주간 교차)")
    if (
        not df_fx.empty
        and not df_public.empty
        and "date" in df_fx.columns
        and "deal_date" in df_public.columns
        and "price_per_sqm" in df_public.columns
    ):
        usd_ts = (
            df_fx[df_fx["currency"] == "USD"]
            .dropna(subset=["date"])
            .set_index("date")["rate"]
            .resample("W")
            .mean()
            .rename("USD")
        )
        price_ts = (
            df_public.dropna(subset=["deal_date"])
            .set_index("deal_date")["price_per_sqm"]
            .resample("W")
            .mean()
            .rename("㎡당(만원)")
        )
        merged = pd.concat([usd_ts, price_ts], axis=1).dropna(how="all")
        if merged.empty:
            st.caption("기간이 겹치는 주간 데이터가 없습니다.")
        else:
            plot_df = merged.reset_index()
            date_col = plot_df.columns[0]
            fig = px.line(
                plot_df,
                x=date_col,
                y=[c for c in ("USD", "㎡당(만원)") if c in plot_df.columns],
                labels={date_col: ""},
            )
            fig.update_layout(legend_title="", margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("교차 시계열에 필요한 컬럼이 부족합니다.")

# ===== 법원경매 =====
with tab_auction:
    if df_court.empty:
        st.warning("경매 데이터가 없습니다.")
    else:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("물건 수", f"{len(df_court):,}")
        if "appraisal_amount" in df_court.columns:
            k2.metric(
                "평균 감정가",
                f"{df_court['appraisal_amount'].mean() / 1e8:,.1f} 억",
            )
        if "min_bid" in df_court.columns:
            k3.metric(
                "평균 최저가",
                f"{df_court['min_bid'].mean() / 1e8:,.1f} 억",
            )
        if "discount_rate" in df_court.columns:
            k4.metric(
                "평균 할인율",
                f"{df_court['discount_rate'].mean() * 100:,.1f} %",
            )

        a1, a2 = st.columns(2)
        with a1:
            if "court" in df_court.columns:
                by_court = (
                    df_court.groupby("court", observed=True)
                    .size()
                    .rename("건수")
                    .reset_index()
                    .sort_values("건수", ascending=True)
                )
                st.plotly_chart(
                    px.bar(
                        by_court,
                        x="건수",
                        y="court",
                        orientation="h",
                        title="법원별 물건 수",
                    ),
                    use_container_width=True,
                )
        with a2:
            if "property_type" in df_court.columns:
                by_type = (
                    df_court.groupby("property_type", observed=True)
                    .size()
                    .rename("건수")
                    .reset_index()
                )
                st.plotly_chart(
                    px.pie(
                        by_type,
                        names="property_type",
                        values="건수",
                        title="물건 유형",
                    ),
                    use_container_width=True,
                )

        if "auction_date" in df_court.columns and df_court["auction_date"].notna().any():
            ts = (
                df_court.dropna(subset=["auction_date"])
                .set_index("auction_date")
                .groupby(pd.Grouper(freq="W"))
                .size()
                .rename("건수")
                .reset_index()
            )
            st.plotly_chart(
                px.bar(ts, x="auction_date", y="건수", title="주별 경매 일정"),
                use_container_width=True,
            )

        st.dataframe(df_court, use_container_width=True, height=360)
        st.download_button(
            "경매 CSV 다운로드",
            data=df_court.to_csv(index=False).encode("utf-8-sig"),
            file_name="court_auction.csv",
            mime="text/csv",
        )

# ===== 공공데이터 =====
with tab_public:
    if df_public.empty:
        st.warning("실거래 데이터가 없습니다.")
    else:
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("거래 건수", f"{len(df_public):,}")
        if "deal_amount" in df_public.columns:
            p2.metric(
                "평균 거래금액",
                f"{df_public['deal_amount'].mean() / 10000:,.1f} 억",
            )
        if "price_per_sqm" in df_public.columns:
            p3.metric(
                "평균 ㎡당",
                f"{df_public['price_per_sqm'].mean():,.0f} 만원",
            )
        if "apt_name" in df_public.columns:
            p4.metric("단지 수", f"{df_public['apt_name'].nunique():,}")

        q1, q2 = st.columns(2)
        with q1:
            if "legal_dong" in df_public.columns:
                top = (
                    df_public.groupby("legal_dong", observed=True)
                    .size()
                    .rename("건수")
                    .reset_index()
                    .sort_values("건수", ascending=False)
                    .head(12)
                )
                st.plotly_chart(
                    px.bar(top, x="legal_dong", y="건수", title="법정동별 거래건수"),
                    use_container_width=True,
                )
        with q2:
            if {"area", "deal_amount"} <= set(df_public.columns):
                sc = df_public.dropna(subset=["area", "deal_amount"]).copy()
                sc["거래금액(억)"] = sc["deal_amount"] / 10000
                st.plotly_chart(
                    px.scatter(
                        sc,
                        x="area",
                        y="거래금액(억)",
                        color="region_name" if "region_name" in sc.columns else None,
                        title="면적–가격",
                        labels={"area": "전용면적(㎡)"},
                    ),
                    use_container_width=True,
                )

        if "deal_date" in df_public.columns and df_public["deal_date"].notna().any():
            ts = (
                df_public.dropna(subset=["deal_date"])
                .set_index("deal_date")
                .groupby(pd.Grouper(freq="W"))["deal_amount"]
                .mean()
                .div(10000)
                .rename("평균거래(억)")
                .reset_index()
            )
            st.plotly_chart(
                px.line(
                    ts,
                    x="deal_date",
                    y="평균거래(억)",
                    markers=True,
                    title="주별 평균 거래금액",
                ),
                use_container_width=True,
            )

        st.dataframe(df_public, use_container_width=True, height=360)
        st.download_button(
            "실거래 CSV 다운로드",
            data=df_public.to_csv(index=False).encode("utf-8-sig"),
            file_name="public_molit.csv",
            mime="text/csv",
        )

# ===== 환율 =====
with tab_fx:
    if df_fx_view.empty:
        st.warning("환율 데이터가 없습니다.")
    else:
        latest = (
            df_fx_view.sort_values("date")
            .groupby("currency", observed=True)
            .tail(1)
            .set_index("currency")["rate"]
            if "currency" in df_fx_view.columns
            else pd.Series(dtype=float)
        )
        cols = st.columns(max(len(latest), 1))
        for i, (cur, rate) in enumerate(latest.items()):
            cols[i].metric(f"{cur}/KRW", f"{rate:,.2f}")

        if {"date", "currency", "rate"} <= set(df_fx_view.columns):
            st.plotly_chart(
                px.line(
                    df_fx_view.sort_values("date"),
                    x="date",
                    y="rate",
                    color="currency",
                    title="환율 시계열",
                    labels={"date": "", "rate": "KRW", "currency": "통화"},
                ),
                use_container_width=True,
            )
            # 주간 변동률
            pivot = df_fx_view.pivot_table(
                index="date", columns="currency", values="rate", aggfunc="last"
            ).sort_index()
            chg = pivot.pct_change(5).dropna(how="all") * 100
            if not chg.empty:
                melt = chg.reset_index().melt(
                    id_vars=chg.index.name or "date",
                    var_name="currency",
                    value_name="pct",
                )
                date_col = melt.columns[0]
                st.plotly_chart(
                    px.line(
                        melt,
                        x=date_col,
                        y="pct",
                        color="currency",
                        title="5영업일 변동률 (%)",
                        labels={date_col: "", "pct": "%"},
                    ),
                    use_container_width=True,
                )

        st.dataframe(df_fx_view, use_container_width=True, height=320)
        st.download_button(
            "환율 CSV 다운로드",
            data=df_fx_view.to_csv(index=False).encode("utf-8-sig"),
            file_name="exchange_rate.csv",
            mime="text/csv",
        )

# ===== 기업정보 =====
with tab_corp:
    if df_corp.empty:
        st.warning("기업 데이터가 없습니다.")
    else:
        g1, g2, g3 = st.columns(3)
        g1.metric("기업 수", f"{len(df_corp):,}")
        if "revenue" in df_corp.columns:
            g2.metric("평균 매출(억)", f"{df_corp['revenue'].mean():,.0f}")
        if "op_margin" in df_corp.columns:
            g3.metric(
                "평균 영업이익률",
                f"{df_corp['op_margin'].mean() * 100:,.1f} %",
            )

        b1, b2 = st.columns(2)
        with b1:
            if {"corp_name", "revenue"} <= set(df_corp.columns):
                top_rev = df_corp.nlargest(10, "revenue")
                st.plotly_chart(
                    px.bar(
                        top_rev.sort_values("revenue"),
                        x="revenue",
                        y="corp_name",
                        orientation="h",
                        title="매출 상위 기업 (억)",
                        labels={"revenue": "매출(억)", "corp_name": ""},
                    ),
                    use_container_width=True,
                )
        with b2:
            if {"debt_ratio", "op_margin", "corp_name"} <= set(df_corp.columns):
                st.plotly_chart(
                    px.scatter(
                        df_corp,
                        x="debt_ratio",
                        y="op_margin",
                        size="revenue" if "revenue" in df_corp.columns else None,
                        color="industry" if "industry" in df_corp.columns else None,
                        hover_name="corp_name",
                        title="부채비율 vs 영업이익률",
                        labels={
                            "debt_ratio": "부채비율",
                            "op_margin": "영업이익률",
                        },
                    ),
                    use_container_width=True,
                )

        st.dataframe(df_corp, use_container_width=True, height=360)
        st.download_button(
            "기업 CSV 다운로드",
            data=df_corp.to_csv(index=False).encode("utf-8-sig"),
            file_name="companies.csv",
            mime="text/csv",
        )

st.sidebar.divider()
st.sidebar.caption(
    f"패키지 루트: `{ROOT.name}` · 샘플: `{SAMPLE_DIR.relative_to(ROOT) if SAMPLE_DIR.exists() else '없음'}`"
)
