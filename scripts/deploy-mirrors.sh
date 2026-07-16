#!/usr/bin/env bash
# 미러 브랜치 → 대상 레포 배포 (로컬 gh/git 인증 사용)
set -euo pipefail

OWNER="DongsooJung"
HUB="DongsooJung"
TOKEN="${GH_TOKEN:-$(gh auth token 2>/dev/null || true)}"

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: GH_TOKEN 또는 gh auth login 필요"
  exit 1
fi

deploy_mirror() {
  local mirror="$1" target="$2" unarchive="${3:-false}"
  echo "━━━ $target ← mirror/$mirror ━━━"
  [[ "$unarchive" == "true" ]] && gh api -X PATCH "repos/$OWNER/$target" -f archived=false 2>/dev/null || true

  local tmp; tmp=$(mktemp -d)
  if ! git clone --branch "mirror/$mirror" \
    "https://x-access-token:${TOKEN}@github.com/$OWNER/$HUB.git" "$tmp"; then
    echo "⚠️  clone failed — skip $target"
    return 0
  fi
  cd "$tmp"
  git remote add target "https://x-access-token:${TOKEN}@github.com/$OWNER/$target.git"
  if git push target HEAD:main --force; then
    echo "✅ $target deployed"
  else
    echo "⚠️  push denied — mirror/$mirror 에 소스 있음"
  fi
  cd - >/dev/null
  rm -rf "$tmp"
}

deploy_mirror ds-research-urban-analytics ds-research-urban-analytics true
deploy_mirror dongsoojung-github-io dongsoojung.github.io
deploy_mirror stargateedu stargateedu
deploy_mirror stargate-main stargate-main
deploy_mirror stargate-blog stargate-blog
deploy_mirror stargate-shop stargate-shop

echo "✅ 배포 완료"
