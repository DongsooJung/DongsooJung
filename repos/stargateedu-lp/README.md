# Stargate LP (Landing Page Experiment)

**도메인**: `lp.stargateedu.co.kr` (실험용 서브도메인)
**호스팅**: GitHub Pages (main / root)
**연결**: `DongsooJung/stargate-lp` repo

## 목적

- 공식 쇼핑몰 `www.stargateedu.co.kr` 로 유입을 유도하는 마케팅/랜딩 페이지
- 쇼핑몰(Manus.space + Cloudflare)과 분리된 경량 정적 페이지로 SEO·A/B 실험 가능
- 대치동 KOI/AI 강의 상담권 구매 CTA 제공

## 구조

- `index.html` - 랜딩 페이지(다크 퍼플/골드 테마, 9섹션 구성)
- `CNAME` - `lp.stargateedu.co.kr`
- `robots.txt` - 검색 허용 + Sitemap 지시
- `sitemap.xml` - lp / 쇼핑몰 / 포털 3개 URL

## 섹션 구성

1. Nav (Stargate 로고 + 쇼핑몰 CTA)
2. Hero (뱃지 + 타이틀 + 4-통계 그리드)
3. Programs (KOI / AI / 과고입시 3-카드)
4. Credentials (정동수 9-항 프로필)
5. Process (4-단계 상담→결제→개강)
6. FAQ (6개 details)
7. Final CTA (쇼핑몰 링크)
8. Footer (법적 고지)

## 배포

```
git init -b main
git add -A
git commit -m "init: stargate-lp experimental landing"
git remote add origin https://github.com/DongsooJung/stargate-lp.git
git push -u origin main
gh api -X POST repos/DongsooJung/stargate-lp/pages -F source[branch]=main -F source[path]=/
gh api -X PUT repos/DongsooJung/stargate-lp/pages -f cname=lp.stargateedu.co.kr
```

## DNS (cafe24)

`stargateedu.co.kr` 영역에 CNAME 레코드 추가:

```
이름:   lp
타입:   CNAME
값:     dongsoojung.github.io.
TTL:    3600
```

> apex 도메인(`stargateedu.co.kr`)과 `www` 는 건드리지 말 것. 서브도메인만 추가.

## 주의

- 본 페이지는 **결제 기능 없음**. 모든 결제는 쇼핑몰에서만.
- cafe24 DNS 변경 후 최대 30분 반영, Let's Encrypt 발급 최대 24시간.
- A/B 테스트·구글 애널리틱스 연동 시 Cloudflare 미적용(주의).
