#!/usr/bin/env bash
# Snapshot branch deployment helper.
# Production domain repositories are protected from this script.
set -euo pipefail

OWNER="DongsooJung"
HUB="DongsooJung"
TOKEN="${GH_TOKEN:-$(gh auth token 2>/dev/null || true)}"

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: GH_TOKEN or gh auth login is required"
  exit 1
fi

is_protected_target() {
  case "$1" in
    dongsoojung.github.io|stargate-main|stargate-blog-hub|stargateedu-shop)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

deploy_snapshot() {
  local mirror="$1" target="$2"

  if is_protected_target "$target"; then
    echo "ERROR: $target is a production source of truth and cannot be overwritten by a snapshot."
    exit 2
  fi

  local tmp
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' RETURN

  git clone --branch "mirror/$mirror"     "https://x-access-token:${TOKEN}@github.com/$OWNER/$HUB.git" "$tmp"

  git -C "$tmp" remote add target     "https://x-access-token:${TOKEN}@github.com/$OWNER/$target.git"
  git -C "$tmp" push target HEAD:main
}

# Non-production package mirrors only.
deploy_snapshot ds-research-urban-analytics ds-research-urban-analytics
deploy_snapshot stargateedu stargateedu

echo "Snapshot deployment complete. Production domain repositories were not modified."
