#!/usr/bin/env bash
# stargate-blog-hub 에 n8n 블로그 자동화 연동을 적용하고 브랜치를 푸시합니다.
# 필요: gh auth login 또는 GH_TOKEN (stargate-blog-hub write 권한)
set -euo pipefail

OWNER="${OWNER:-DongsooJung}"
REPO="${REPO:-stargate-blog-hub}"
BRANCH="${BRANCH:-feat/n8n-blog-integration}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

TOKEN="${GH_TOKEN:-$(gh auth token 2>/dev/null || true)}"
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: GH_TOKEN 또는 gh auth login 필요"
  exit 1
fi

git clone --depth=1 "https://x-access-token:${TOKEN}@github.com/${OWNER}/${REPO}.git" "$TMP/repo"
cd "$TMP/repo"
git checkout -b "$BRANCH"

python3 "$HERE/n8n-blog-hub/patch_blog_hub.py" "$TMP/repo"
cp "$HERE/n8n-blog-hub/N8N_WEBHOOK_SETUP.md" N8N_WEBHOOK_SETUP.md

node tests/n8n-blog-webhook.test.js
node tests/notion-reading-webhook.test.js

git add -A
if git diff --cached --quiet; then
  echo "변경 사항 없음 — 이미 적용되어 있습니다."
  exit 0
fi
git -c user.name="stargate-hub-bot" -c user.email="bot@stargate11.com" \
  commit -m "feat(n8n): 블로그 자동화 웹훅 연동 및 허브 병합"
git push -u origin "$BRANCH"
echo "완료: https://github.com/${OWNER}/${REPO}/compare/${BRANCH}?expand=1"
