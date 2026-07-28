#!/usr/bin/env bash
# 미러 orphan 브랜치 생성 — /tmp 에서 안전하게 빌드 후 origin push
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="/tmp/mirror-work-$$"
TOKEN="${GH_TOKEN:-$(python3 -c "import yaml; print(yaml.safe_load(open('$HOME/.config/gh/hosts.yml'))['github.com']['oauth_token'])" 2>/dev/null || true)}"
TOKEN="${TOKEN:-$(git -C "$ROOT" remote get-url origin | sed -n 's/.*x-access-token:\([^@]*\)@.*/\1/p')}"
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: GitHub token not found"
  exit 1
fi

cleanup() { rm -rf "$WORK" "$STAGING"; }
trap cleanup EXIT

STAGING="$WORK/staging"
mkdir -p "$STAGING"

# 소스 준비
cp -r "$ROOT/repos/ds-research-urban-analytics" "$STAGING/ds-research"
cp -r "$ROOT/repos/dongsoojung-github-io" "$STAGING/dongsoojung-github-io"

mkdir -p "$STAGING/stargateedu/lp"
TOKEN_URL="https://x-access-token:${TOKEN}@github.com/DongsooJung"
if git clone --depth=1 "${TOKEN_URL}/stargateedu.git" "$STAGING/stargateedu-base" 2>/dev/null; then
  cp -r "$STAGING/stargateedu-base/." "$STAGING/stargateedu/"
  rm -rf "$STAGING/stargateedu-base"
fi
cp -r "$ROOT/repos/stargateedu-lp/." "$STAGING/stargateedu/lp/"

mkdir -p "$STAGING/stargate-main"
if git clone --depth=1 "${TOKEN_URL}/stargate-main.git" "$STAGING/stargate-main-base" 2>/dev/null; then
  cp -r "$STAGING/stargate-main-base/." "$STAGING/stargate-main/"
  rm -rf "$STAGING/stargate-main-base"
fi
cp -r "$ROOT/repos/stargate-main-sites/sites" "$STAGING/stargate-main/"
cp -r "$ROOT/repos/stargate-main-sites/shared" "$STAGING/stargate-main/"
cp "$STAGING/stargate-main/shared/"* "$STAGING/stargate-main/" 2>/dev/null || true

cp -r "$ROOT/repos/stargate-main-sites/sites/blog" "$STAGING/stargate-blog"
cp -r "$ROOT/repos/stargate-main-sites/sites/shop" "$STAGING/stargate-shop"
cp -r "$ROOT/repos/stargate-blog-hub" "$STAGING/stargate-blog-hub"

# 작업 클론
git clone "https://x-access-token:${TOKEN}@github.com/DongsooJung/DongsooJung.git" "$WORK/repo"
cd "$WORK/repo"
git remote set-url origin "https://x-access-token:${TOKEN}@github.com/DongsooJung/DongsooJung.git"

build_mirror() {
  local branch="$1" src="$2" msg="$3"
  echo "▶ mirror/$branch"
  git branch -D "mirror/$branch" 2>/dev/null || true
  git checkout --orphan "mirror/$branch"
  git rm -rf . 2>/dev/null || true
  (cd "$src" && tar --exclude='.git' -cf - .) | tar -xf -
  printf 'mirror/%s\nfrom DongsooJung/DongsooJung main\n' "$branch" > .mirror-source
  git add -A
  git commit -m "$msg"
}

build_mirror "ds-research-urban-analytics" "$STAGING/ds-research" \
  "mirror: ds-research-urban-analytics monorepo"
build_mirror "dongsoojung-github-io" "$STAGING/dongsoojung-github-io" \
  "mirror: dongsoojung.github.io portal (www.stargateedu.co.kr)"
build_mirror "stargateedu" "$STAGING/stargateedu" \
  "mirror: stargateedu + lp/"
build_mirror "stargate-main" "$STAGING/stargate-main" \
  "mirror: stargate-main + sites/ + shared/"
build_mirror "stargate-blog" "$STAGING/stargate-blog" \
  "mirror: stargate-blog"
build_mirror "stargate-shop" "$STAGING/stargate-shop" \
  "mirror: stargate-shop"
build_mirror "stargate-blog-hub" "$STAGING/stargate-blog-hub" \
  "mirror: stargate-blog-hub (blog.stargateedu.co.kr)"

git checkout main

MIRRORS=(
  mirror/ds-research-urban-analytics
  mirror/dongsoojung-github-io
  mirror/stargateedu
  mirror/stargate-main
  mirror/stargate-blog
  mirror/stargate-shop
  mirror/stargate-blog-hub
)

PUSH_FAILED=0
HUB_FAILED=0
for ref in "${MIRRORS[@]}"; do
  echo "▶ pushing $ref"
  if git push origin "$ref" --force; then
    echo "✅ $ref pushed"
  else
    echo "⚠️  $ref push failed (continuing)"
    PUSH_FAILED=1
    if [[ "$ref" == "mirror/stargate-blog-hub" ]]; then
      HUB_FAILED=1
    fi
  fi
done

if [[ "$HUB_FAILED" -ne 0 ]]; then
  echo "❌ mirror/stargate-blog-hub push failed"
  exit 1
fi

if [[ "$PUSH_FAILED" -ne 0 ]]; then
  echo "⚠️  some mirror pushes failed (blog-hub OK)"
else
  echo "✅ all mirror branches pushed"
fi
