# 통합 레포 허브 (Canonical Source)

> **DongsooJung/DongsooJung** 프로필 레포가 통합 후 **단일 소스 오브 트루스**입니다.

## 구조

| 경로 | 내용 | 원본 레포 |
|------|------|----------|
| [`ds-research-urban-analytics/`](ds-research-urban-analytics/) | 5개 연구 패키지 모노레포 | `urban-spatial-analysis` 등 5개 |
| [`dongsoojung-github-io/`](dongsoojung-github-io/) | 메인 포털 (`www.stargateedu.co.kr`) | `dongsoojung.github.io` |
| [`stargateedu-lp/`](stargateedu-lp/) | LP 랜딩 (`lp.stargateedu.co.kr`) | `stargate-lp` |
| [`stargate-main-sites/`](stargate-main-sites/) | blog/shop + shared nav | `stargate-blog`, `stargate-shop` |
| [`stargate-blog-hub/`](stargate-blog-hub/) | 다채널 RSS 스크리닝 허브 (`blog.stargateedu.co.kr`) | `stargate-blog-hub` |

## 미러 브랜치 (배포용)

각 대상 레포 루트에 바로 push 가능한 orphan 브랜치:

| 미러 브랜치 | 대상 레포 |
|------------|----------|
| `mirror/ds-research-urban-analytics` | `ds-research-urban-analytics` |
| `mirror/dongsoojung-github-io` | `dongsoojung.github.io` |
| `mirror/stargateedu` | `stargateedu` |
| `mirror/stargate-main` | `stargate-main` |
| `mirror/stargate-blog` | `stargate-blog` |
| `mirror/stargate-shop` | `stargate-shop` |
| `mirror/stargate-blog-hub` | `stargate-blog-hub` |

```bash
# 로컬에서 한 번에 배포 (gh auth 또는 GH_TOKEN 필요)
./scripts/deploy-mirrors.sh
```

## 자동 동기화

`repos/` 변경 시 GitHub Actions **Sync Mirror Branches** 워크플로가 미러 브랜치를 자동 갱신합니다.
