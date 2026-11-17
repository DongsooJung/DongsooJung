# 🤝 Contributing Guide

> 이 리포지토리는 정동수(SNU 스마트도시공학 박사 수료)의 연구 포트폴리오입니다.
> 외부 PR보다는 Issue를 통한 토론·피드백을 환영합니다.

---

## 🛠 개발 환경 세팅

```bash
# 1. 클론 및 가상환경 생성
git clone https://github.com/DongsooJung/real-estate-hedonic.git
cd real-estate-hedonic
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt
pip install -e .             # editable 설치 (src 레이아웃)

# 3. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 MOLIT_API_KEY, KAKAO_REST_API_KEY 입력

# 4. 테스트 실행
pytest tests/ -v
```

## 📋 구현 우선순위

현재는 스켈레톤 상태입니다. 다음 순서로 구현을 권장합니다:

### Phase 1 — 데이터 수집 (⭐ 가장 먼저)
- [ ] `molit_api.MolitClient._call_single_page` — XML 파싱
- [ ] `molit_api.MolitClient._normalize_columns` — 한글→영문
- [ ] `molit_api.MolitClient.fetch_transactions` — 페이지 순회
- [ ] `molit_api.MolitClient.fetch_multi_period` — 다지역/다월

### Phase 2 — 지오코딩
- [ ] `geocoding.KakaoGeocoder.geocode` — 단일 주소
- [ ] `geocoding.build_full_address` — 주소 조립
- [ ] `geocoding.KakaoGeocoder.geocode_dataframe` — 일괄 처리

### Phase 3 — 전처리
- [ ] `preprocessing.drop_cancelled`
- [ ] `preprocessing.add_price_per_sqm`
- [ ] `preprocessing.drop_outliers_iqr`
- [ ] `preprocessing.to_geodataframe`

### Phase 4 — 공간계량
- [ ] `weights.build_weights` — KNN 우선
- [ ] `models.SpatialHedonicModel._fit_ols`
- [ ] `models.SpatialHedonicModel._fit_sem`
- [ ] `diagnostics.morans_i`

### Phase 5 — 확장
- [ ] SDM 구현
- [ ] LISA 시각화
- [ ] End-to-end notebook 실행 결과 삽입

## ✅ 코드 스타일

- **PEP 8** 준수 (`black` + `ruff`)
- Type hints 필수
- Docstring: Google 스타일
- 모든 public 함수에 `Args`, `Returns`, `Raises` 기재
- 한글 주석은 의도/설명용만, 변수명·함수명은 영문

## 🧪 테스트 정책

- 새 함수 추가 시 `tests/`에 대응 테스트 추가
- Coverage 목표: 핵심 모듈(`models`, `weights`, `diagnostics`) 80% 이상
- 외부 API 호출은 `pytest-mock`으로 모킹

## 📄 커밋 메시지

[Conventional Commits](https://www.conventionalcommits.org/) 사용:

```
feat(models): implement SpatialHedonicModel._fit_sem
fix(geocoding): handle Kakao API rate limit 429
docs(readme): update installation instructions
test(weights): add KNN edge cases
```

## 📬 연락처

- GitHub Issues: 기술적 질문·버그 리포트
- Email: jds068888@gmail.com (비공개 논의)
