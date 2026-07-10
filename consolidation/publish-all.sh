#!/usr/bin/env bash
# DongsooJung 레포 통합 배포 스크립트
# 사용법: GH_TOKEN=<personal_access_token> ./publish-all.sh
set -euo pipefail

OWNER="DongsooJung"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUNDLE_DIR="$SCRIPT_DIR/bundles"
STAGING_DIR="$ROOT_DIR/repos"

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "ERROR: GH_TOKEN 환경변수가 필요합니다 (repo 권한 포함 PAT)"
  exit 1
fi

gh auth status >/dev/null 2>&1 || gh auth login --with-token <<<"$GH_TOKEN"

push_bundle() {
  local repo="$1" branch="$2" bundle="$3" unarchive="${4:-false}"
  echo "━━━ $repo ← bundle ━━━"
  [[ "$unarchive" == "true" ]] && gh api -X PATCH "repos/$OWNER/$repo" -f archived=false || true
  local tmpdir; tmpdir=$(mktemp -d)
  git clone "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/$repo.git" "$tmpdir"
  cd "$tmpdir"
  git fetch "$bundle" "refs/heads/$branch"
  git checkout -B "$branch" FETCH_HEAD
  git push -u origin "$branch"
  gh pr create --repo "$OWNER/$repo" --head "$branch" --base main \
    --title "chore: consolidate duplicate repositories" \
    --body "Cursor Cloud Agent 레포 통합." || true
  cd - >/dev/null; rm -rf "$tmpdir"
}

create_pr() {
  local repo="$1" branch="$2"
  gh pr create --repo "$OWNER/$repo" --head "$branch" --base main \
    --title "chore: consolidate duplicate repositories" \
    --body "Cursor Cloud Agent 레포 통합." || true
}

# ── 1. 연구 모노레포 ──
deploy_research() {
  local branch="cursor/merge-research-monorepo-c654"
  echo "━━━ ds-research-urban-analytics ━━━"
  gh api -X PATCH "repos/$OWNER/ds-research-urban-analytics" -f archived=false || true
  local tmpdir; tmpdir=$(mktemp -d)
  git clone "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/ds-research-urban-analytics.git" "$tmpdir"
  cd "$tmpdir" && git checkout -B "$branch"
  if [[ -d "$STAGING_DIR/ds-research-urban-analytics" ]]; then
    cp -r "$STAGING_DIR/ds-research-urban-analytics/." .
  else
    git fetch "$BUNDLE_DIR/ds-research-urban-analytics.bundle" "refs/heads/$branch"
    git checkout -B "$branch" FETCH_HEAD
  fi
  git add -A && git commit -m "feat: merge 5 research repos into packages/ monorepo" || true
  git push -u origin "$branch"
  create_pr "ds-research-urban-analytics" "$branch"
  cd - >/dev/null; rm -rf "$tmpdir"
}

# ── 2. stargateedu + lp/ ──
deploy_stargateedu() {
  local branch="cursor/merge-lp-into-stargateedu-c654"
  echo "━━━ stargateedu ━━━"
  local tmpdir; tmpdir=$(mktemp -d)
  git clone "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/stargateedu.git" "$tmpdir"
  cd "$tmpdir" && git checkout -B "$branch"
  mkdir -p lp
  if [[ -d "$STAGING_DIR/stargateedu-lp" ]]; then
    cp -r "$STAGING_DIR/stargateedu-lp/." lp/
  else
    git fetch "$BUNDLE_DIR/stargateedu-lp-merge.bundle" "refs/heads/$branch"
    git checkout -B "$branch" FETCH_HEAD
  fi
  git add -A && git commit -m "feat: merge stargate-lp into lp/" || true
  git push -u origin "$branch"
  create_pr "stargateedu" "$branch"
  cd - >/dev/null; rm -rf "$tmpdir"
}

# ── 3. stargate-main sites ──
deploy_stargate_main() {
  local branch="cursor/merge-static-sites-c654"
  echo "━━━ stargate-main ━━━"
  local tmpdir; tmpdir=$(mktemp -d)
  git clone "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/stargate-main.git" "$tmpdir"
  cd "$tmpdir" && git checkout -B "$branch"
  if [[ -d "$STAGING_DIR/stargate-main-sites" ]]; then
    cp -r "$STAGING_DIR/stargate-main-sites/sites" .
    cp -r "$STAGING_DIR/stargate-main-sites/shared" .
  else
    git fetch "$BUNDLE_DIR/stargate-main-sites-merge.bundle" "refs/heads/$branch"
    git checkout -B "$branch" FETCH_HEAD
  fi
  git add -A && git commit -m "feat: consolidate blog/shop sites and shared nav" || true
  git push -u origin "$branch"
  create_pr "stargate-main" "$branch"
  cd - >/dev/null; rm -rf "$tmpdir"
}

# ── 4. blog/shop 동기화 ──
sync_site() {
  local site="$1" target="$2"
  [[ -d "$STAGING_DIR/stargate-main-sites/sites/$site" ]] || return 0
  echo "━━━ $target ← sites/$site ━━━"
  local tmpdir; tmpdir=$(mktemp -d)
  git clone "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/$target.git" "$tmpdir"
  cd "$tmpdir" && git checkout -B "cursor/sync-from-main-c654"
  cp -r "$STAGING_DIR/stargate-main-sites/sites/$site/." .
  git add -A && git commit -m "chore: sync from stargate-main sites/$site" || true
  git push -u origin cursor/sync-from-main-c654
  create_pr "$target" "cursor/sync-from-main-c654"
  cd - >/dev/null; rm -rf "$tmpdir"
}

# ── 5. 아카이브 ──
archive_repo() {
  local repo="$1" target="$2"
  echo "━━━ archive $repo ━━━"
  local tmpdir; tmpdir=$(mktemp -d)
  git clone "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/$repo.git" "$tmpdir"
  cd "$tmpdir"
  cat > README.md <<EOF
# ⚠️ 이 저장소는 통합되었습니다

이 프로젝트는 **[$target](https://github.com/$OWNER/$target)** 로 통합되었습니다.

스테이징: [DongsooJung/repos](https://github.com/$OWNER/DongsooJung/tree/main/repos)
EOF
  git checkout -B chore/archived-redirect
  git add README.md && git commit -m "docs: redirect to consolidated repository"
  git push -u origin chore/archived-redirect
  create_pr "$repo" "chore/archived-redirect"
  gh api -X PATCH "repos/$OWNER/$repo" -f archived=true || true
  cd - >/dev/null; rm -rf "$tmpdir"
}

deploy_research
deploy_stargateedu
deploy_stargate_main
sync_site blog stargate-blog
sync_site shop stargate-shop
for src in urban-spatial-analysis smart-city-gis airport-infrastructure-analytics credit-survival-analysis real-estate-molit-api; do
  archive_repo "$src" "ds-research-urban-analytics"
done
archive_repo "stargate-lp" "stargateedu"

echo "✅ 모든 통합 배포 완료"
