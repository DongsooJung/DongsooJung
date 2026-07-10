# 통합 레포 스테이징

Cursor Cloud Agent가 준비한 **병합 완료 소스**입니다.  
`cursor[bot]` 권한 제한으로 대상 레포에 직접 push하지 못해, 프로필 레포에 스테이징합니다.

| 디렉터리 | 통합 대상 레포 | 내용 |
|----------|---------------|------|
| [`ds-research-urban-analytics/`](ds-research-urban-analytics/) | `DongsooJung/ds-research-urban-analytics` | 5개 연구 레포 → `packages/` |
| [`stargateedu-lp/`](stargateedu-lp/) | `DongsooJung/stargateedu` (`lp/`) | `stargate-lp` 랜딩 통합 |
| [`stargate-main-sites/`](stargate-main-sites/) | `DongsooJung/stargate-main` | blog/shop + shared nav |

## 배포

```bash
cd consolidation
GH_TOKEN=<repo권한_PAT> ./publish-all.sh
```

`publish-all.sh`는 `repos/` 스테이징 또는 `bundles/`에서 대상 레포로 push합니다.
