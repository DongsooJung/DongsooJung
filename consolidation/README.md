# DongsooJung 레포 통합 계획

Cursor Cloud Agent가 준비한 중복 레포 통합 작업입니다.

## 통합 요약

| 그룹 | 대상 (통합 후) | 소스 (아카이브 예정) |
|------|---------------|---------------------|
| **연구** | `ds-research-urban-analytics` | `urban-spatial-analysis`, `smart-city-gis`, `airport-infrastructure-analytics`, `credit-survival-analysis`, `real-estate-molit-api` |
| **교육 LP** | `stargateedu/lp/` | `stargate-lp` |
| **STARGATE 정적사이트** | `stargate-main` (`sites/`, `shared/`) | `stargate-blog`, `stargate-shop` 소스 통합 (배포는 별도 유지) |
| **프로필** | `DongsooJung` README | `real-estate-hedonic` 링크 → 모노레포로 정리 |

## 준비된 Git 번들

```
consolidation/bundles/
├── ds-research-urban-analytics.bundle   # 5개 연구 레포 → packages/
├── stargateedu-lp-merge.bundle          # stargate-lp → lp/
└── stargate-main-sites-merge.bundle     # blog/shop → sites/
```

## 배포 방법

### 옵션 A: 스크립트 (권장)

```bash
cd consolidation
GH_TOKEN=<repo권한_PAT> chmod +x publish-all.sh && ./publish-all.sh
```

### 옵션 B: 수동 번들 적용

```bash
git clone https://github.com/DongsooJung/ds-research-urban-analytics.git
cd ds-research-urban-analytics
git pull ../path/to/ds-research-urban-analytics.bundle cursor/merge-research-monorepo-c654
git push origin cursor/merge-research-monorepo-c654
```

### 옵션 C: GitHub Actions

`Actions → Consolidate Repositories → Run workflow`  
(리포지토리 Secrets에 `GH_PAT` 등록 필요)

## 연구 모노레포 구조

```
ds-research-urban-analytics/
├── packages/
│   ├── urban-spatial-analysis/
│   ├── smart-city-gis/
│   ├── airport-infrastructure-analytics/
│   ├── credit-survival-analysis/
│   └── real-estate-molit-api/
└── README.md
```

## 주의사항

- `ds-research-urban-analytics`는 현재 **archived** 상태 → 배포 전 아카이브 해제 필요
- `stargate-blog`, `stargate-shop`은 GitHub Pages CNAME 때문에 **별도 배포 레포 유지** (소스만 `stargate-main`에서 관리)
- `real-estate-hedonic`은 이미 `real-estate-molit-api`로 이름 변경됨
