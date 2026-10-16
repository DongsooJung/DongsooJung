# Architecture — Korea Data Hub

```
.env / sample CSV
       │
       ▼
┌──────────────────┐
│  korea_data/*    │  CourtAuction / PublicData / ExchangeRate / Dart
│  Clients         │  API 실패 시 sample CSV 폴백
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ dashboard/loader │  Streamlit용 thin wrapper
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ dashboard/app.py │  5탭 Streamlit + Plotly
└──────────────────┘
```

## 설계 원칙

1. **오프라인 우선** — `make_sample.py`만으로 대시보드 기동
2. **키 선택적** — API 키 없으면 샘플, 있으면 실호출 후 실패 시 폴백
3. **가벼운 의존성** — pandas + requests + streamlit + plotly (공간계량 스택 비의존)
4. **기존 모노레포 패턴** — `real-estate-molit-api/dashboard`와 동일한 레이아웃
