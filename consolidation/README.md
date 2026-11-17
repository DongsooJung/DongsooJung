# 레포 통합 작업 기록

> **Historical plan — 재검증 전 실행 금지**
>
> 이 디렉터리는 Cursor Cloud Agent가 준비한 과거 통합 작업 기록입니다. 2026-11-17 확인 결과, 이 문서의 일부 `archived`·완료 표현은 실제 GitHub 저장소 상태와 다릅니다. `publish-all.sh`와 포함된 번들은 최신 운영 원본과 Git 이력을 다시 검증하기 전까지 실행하지 않습니다.

## 과거 통합 구상

| 그룹 | 통합 대상 | 검토 대상 소스 |
|------|-----------|---------------|
| 연구 | `ds-research-urban-analytics/packages/` | `urban-spatial-analysis`, `smart-city-gis`, `airport-infrastructure-analytics`, `credit-survival-analysis`, `real-estate-molit-api` |
| 교육 LP | `stargateedu/lp/` | `stargate-lp` |
| STARGATE 정적사이트 | `stargate-main` 참고 스냅숏 | `stargate-blog`, `stargate-shop` |

## 2026-11-17 현재 상태

- `ds-research-urban-analytics`는 **아카이브되어 있지 않습니다.**
- 위 검토 대상 소스 저장소들도 모두 아카이브되어 있지 않습니다.
- `dongsoojung.github.io`, `stargate-main`, `stargate-blog-hub`, `stargate-shop-redirect`는 각 운영 도메인의 공식 원본입니다.
- `stargateedu-shop`은 현재 운영 원본이 아니라 향후 이전을 위한 준비 저장소입니다.
- `repos/*`와 `mirror/*`는 참고 스냅숏이며 프로덕션 배포 원본이 아닙니다.

## 재개 전 필수 검증

1. 번들 브랜치와 현재 각 저장소 `main`의 커밋·파일 차이를 비교합니다.
2. 통합 결과에 최신 운영 변경과 Git 이력이 빠짐없이 반영됐는지 확인합니다.
3. 열린 이슈·PR, Pages, CNAME, Actions, Secrets, 외부 자동화의 이전 계획을 작성합니다.
4. 테스트와 배포 검증을 통과한 뒤에만 소스 저장소의 아카이브를 검토합니다.
5. 실제 상태 변경 후 `ARCHIVED_REPOS.md`, `DOMAIN_SOURCES.md`, `repos/README.md`를 같은 변경 창에서 갱신합니다.

운영 기준은 [DOMAIN_SOURCES.md](../DOMAIN_SOURCES.md)가 우선합니다.
