# 저장소 통합·아카이브 상태

> 2026-11-17 GitHub 저장소 메타데이터 기준으로 **현재 아카이브된 저장소는 없습니다.** 이 문서는 과거 통합 구상과 실제 저장소 상태를 구분합니다.

## 현재 상태와 후속 검토

| 저장소 | 현재 상태 | 후속 조치 |
|---|---|---|
| `urban-spatial-analysis` | 활성·아카이브 아님 | 연구 모노레포 반영 내용과 Git 이력 비교 후 결정 |
| `smart-city-gis` | 활성·아카이브 아님 | 연구 모노레포 반영 내용과 Git 이력 비교 후 결정 |
| `airport-infrastructure-analytics` | 활성·아카이브 아님 | 연구 모노레포 반영 내용과 Git 이력 비교 후 결정 |
| `credit-survival-analysis` | 활성·아카이브 아님 | 연구 모노레포 반영 내용과 Git 이력 비교 후 결정 |
| `real-estate-molit-api` | 활성·아카이브 아님 | 연구 모노레포 반영 내용과 Git 이력 비교 후 결정 |
| `stargate-lp` | 활성·아카이브 아님 | `stargateedu`와의 중복 및 배포 연결 확인 후 결정 |
| `stargate-blog` | 활성·아카이브 아님 | 운영 원본은 `stargate-blog-hub`; Pages·CNAME 확인 후 legacy 전환 검토 |
| `stargate-shop` | 활성·아카이브 아님 | 현재 운영 원본은 `stargate-shop-redirect`; 배포 연결 확인 후 legacy 전환 검토 |
| `dongsoojung.github.io` | **운영 원본** | `www.stargateedu.co.kr` 및 apex를 제공하므로 아카이브 대상 아님 |

## 스냅숏과 미러의 역할

- `repos/*` 스냅숏과 `mirror/*` 브랜치는 비교·복구 참고용입니다.
- 스냅숏 또는 미러를 운영 저장소의 `main`에 덮어쓰거나 프로덕션에 배포하지 않습니다.
- 실제 통합을 완료하기 전에는 소스 저장소를 아카이브 완료로 기록하지 않습니다.
- 아카이브와 삭제는 별도 승인 후 진행하며, 삭제 전에는 배포·외부 연동·이슈·PR·Git 이력의 보존 필요성을 확인합니다.

**운영 원본 기준:** [DOMAIN_SOURCES.md](DOMAIN_SOURCES.md)
