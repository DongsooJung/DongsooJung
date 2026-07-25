# Korea Data Hub · 통합 데이터 대시보드

> 법원 경매 · 공공데이터포털(MOLIT) · 환율 · 기업정보(DART)를 한 Streamlit 대시보드로 조회

## 빠른 시작

```bash
cd packages/korea-data-hub
pip install -r requirements.txt
python scripts/make_sample.py
streamlit run dashboard/app.py
```

API 키 없이 **샘플 데이터**로 바로 실행됩니다. 실 API를 쓰려면:

```bash
cp .env.example .env
# DATA_GO_KR_KEY / MOLIT_API_KEY / DART_API_KEY / BOK_ECOS_KEY 입력
```

사이드바에서 **샘플 데이터 사용** 토글을 끄면 `.env` 키로 실호출을 시도하고, 실패 시 샘플로 폴백합니다.

## 탭 구성

| 탭 | 내용 |
|----|------|
| **종합** | KPI, 경매 할인율, 업종 영업이익률, USD×㎡당 교차 시계열 |
| **법원경매** | 법원·유형별 집계, 주별 일정, CSV 다운로드 |
| **공공데이터** | MOLIT 실거래 KPI·법정동·면적–가격·주별 추이 |
| **환율** | 통화별 최근값·시계열·5영업일 변동률 |
| **기업정보** | 매출 상위, 부채비율×영업이익률 스캐터 |

## 패키지 구조

```
korea-data-hub/
├── src/korea_data/
│   ├── court_auction.py    # 법원 경매
│   ├── public_data.py      # 공공데이터 / MOLIT
│   ├── exchange_rate.py    # 환율 (ECOS)
│   └── dart_client.py      # DART 기업정보
├── dashboard/
│   ├── app.py              # Streamlit 통합 대시보드
│   └── loader.py
├── scripts/make_sample.py
├── data/sample/
├── tests/
├── .env.example
└── requirements.txt
```

## Cursor / Claude 연동

1. `.env`에 API 키 설정
2. (선택) `.cursor/mcp.json`에 MCP 서버로 클라이언트 래핑
3. Agent에게 "강남 경매 물건 요약해줘" / "USD 환율 추이 차트 수정" 등 요청

## 테스트

```bash
pytest tests/ -q
```
