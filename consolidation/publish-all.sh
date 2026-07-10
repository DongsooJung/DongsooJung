#!/usr/bin/env bash
# DongsooJung 레포 통합 배포 스크립트
# 사용법: GH_TOKEN=<personal_access_token> ./publish-all.sh
set -euo pipefail

OWNER="DongsooJung"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_DIR="$SCRIPT_DIR/bundles"

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "ERROR: GH_TOKEN 환경변수가 필요합니다 (repo 권한 포함 PAT)"
  exit 1
fi

gh auth status >/dev/null 2>&1 || gh auth login --with-token <<<"$GH_TOKEN"

push_bundle() {
  local repo="$1" branch="$2" bundle="$3" unarchive="${4:-false}"
  echo "━━━ $repo ← $bundle ━━━"

  if [[ "$unarchive" == "true" ]]; then
    gh api -X PATCH "repos/$OWNER/$repo" -f archived=false || true
  fi

  local tmpdir
  tmpdir=$(mktemp -d)
  git clone "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/$repo.git" "$tmpdir"
  cd "$tmpdir"
  git fetch "$bundle" "refs/heads/$branch"
  git checkout -B "$branch" FETCH_HEAD
  git push -u origin "$branch"
  gh pr create --repo "$OWNER/$repo" \
    --head "$branch" --base main \
    --title "chore: consolidate duplicate repositories" \
    --body "Cursor Cloud Agent가 준비한 레포 통합 변경입니다. consolidation/ README를 참고하세요." \
    || echo "(PR may already exist)"
  cd - >/dev/null
  rm -rf "$tmpdir"
}

# 1. 연구 모노레포 (ds-research-urban-analytics — 아카이브 해제 필요)
push_bundle "ds-research-urban-analytics" \
  "cursor/merge-research-monorepo-c654" \
  "$BUNDLE_DIR/ds-research-urban-analytics.bundle" \
  true

# 2. stargate-lp → stargateedu
push_bundle "stargateedu" \
  "cursor/merge-lp-into-stargateedu-c654" \
  "$BUNDLE_DIR/stargateedu-lp-merge.bundle"

# 3. stargate blog/shop → stargate-main 모노레포
push_bundle "stargate-main" \
  "cursor/merge-static-sites-c654" \
  "$BUNDLE_DIR/stargate-main-sites-merge.bundle"

# 4. 소스 레포 아카이브 + 리다이렉트 README
archive_repo() {
  local repo="$1" target="$2"
  echo "━━━ Archive $repo → $target ━━━"
  local tmpdir
  tmpdir=$(mktemp -d)
  git clone "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/$repo.git" "$tmpdir"
  cd "$tmpdir"
  cat > README.md <<EOF
# ⚠️ 이 저장소는 통합되었습니다

이 프로젝트는 **[$target](https://github.com/$OWNER/$target)** 로 통합되었습니다.

새 위치에서 계속 개발해 주세요.
EOF
  git checkout -b "chore/archived-redirect"
  git add README.md
  git commit -m "docs: redirect to consolidated repository"
  git push -u origin chore/archived-redirect
  gh pr create --repo "$OWNER/$repo" \
    --head chore/archived-redirect --base main \
    --title "docs: mark repo as consolidated" \
    --body "Redirect README before archiving." || true
  gh api -X PATCH "repos/$OWNER/$repo" -f archived=true || true
  cd - >/dev/null
  rm -rf "$tmpdir"
}

for src in urban-spatial-analysis smart-city-gis airport-infrastructure-analytics credit-survival-analysis real-estate-molit-api; do
  archive_repo "$src" "ds-research-urban-analytics"
done

archive_repo "stargate-lp" "stargateedu"

echo "✅ 모든 통합 배포 완료"
