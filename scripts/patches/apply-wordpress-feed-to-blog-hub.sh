#!/usr/bin/env bash
# stargate-blog-hub 에 WordPress RSS 피드를 직접 반영합니다.
# 필요: gh auth login 또는 GH_TOKEN (stargate-blog-hub write 권한)
set -euo pipefail

OWNER="${OWNER:-DongsooJung}"
REPO="${REPO:-stargate-blog-hub}"
BRANCH="${BRANCH:-cursor/add-wordpress-feed-6e85}"
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

python3 << 'PY'
from pathlib import Path

path = Path('scripts/build_hub_index.py')
text = path.read_text(encoding='utf-8')
if 'stargate815.wordpress.com/feed/' in text:
    print('이미 WordPress 피드가 있습니다.')
    raise SystemExit(0)

text = text.replace(
    '1) FEEDS 에 정의된 4개(+옵션) 채널의 RSS 를 수집',
    '1) FEEDS 에 정의된 5개(+옵션) 채널의 RSS 를 수집',
)
old = '''    "티스토리": {
        "url": "https://dongsoo.tistory.com/rss",
        "icon": "✍️",
        "color": "#FF5900",
    },
    "YouTube 우주인": {'''
new = '''    "티스토리": {
        "url": "https://dongsoo.tistory.com/rss",
        "icon": "✍️",
        "color": "#FF5900",
    },
    "워드프레스": {
        "url": "https://stargate815.wordpress.com/feed/",
        "icon": "📝",
        "color": "#21759B",
    },
    "YouTube 우주인": {'''
if old not in text:
    raise SystemExit('FEEDS block not found — upstream changed')
path.write_text(text.replace(old, new), encoding='utf-8')

tpl = Path('templates/허브_템플릿.html')
tt = tpl.read_text(encoding='utf-8')
needle = '''      <article class="channel"><div class="icon">✍️</div><h3>별로 향하는 문</h3><div class="meta">티스토리 · AI/테크</div><p>AI 자동화, 프롬프트 엔지니어링, 개발 실전 노트.</p><a class="text-link" href="https://dongsoo.tistory.com/" target="_blank" rel="noopener">바로가기 →</a></article>
      <article class="channel"><div class="icon">🪐</div><h3>Notion Archive</h3>'''
insert = '''      <article class="channel"><div class="icon">✍️</div><h3>별로 향하는 문</h3><div class="meta">티스토리 · AI/테크</div><p>AI 자동화, 프롬프트 엔지니어링, 개발 실전 노트.</p><a class="text-link" href="https://dongsoo.tistory.com/" target="_blank" rel="noopener">바로가기 →</a></article>
      <article class="channel"><div class="icon">📝</div><h3>워드프레스</h3><div class="meta">WordPress · stargate815</div><p>스타게이트 워드프레스 최신 글과 공지를 모읍니다.</p><a class="text-link" href="https://stargate815.wordpress.com/" target="_blank" rel="noopener">바로가기 →</a></article>
      <article class="channel"><div class="icon">🪐</div><h3>Notion Archive</h3>'''
if needle not in tt:
    raise SystemExit('template needle not found')
tpl.write_text(tt.replace(needle, insert), encoding='utf-8')
print('source updated')
PY

python3 -m pip install -q -r scripts/requirements.txt
python3 scripts/build_hub_index.py

git add scripts/build_hub_index.py templates/허브_템플릿.html index.html
git commit -m "feat(hub): WordPress(stargate815) RSS를 최신 글 스크리닝에 추가"
git push -u origin "$BRANCH"
gh pr create --repo "${OWNER}/${REPO}" --base main --head "$BRANCH" \
  --title "feat: WordPress(stargate815) 최신 글을 허브 스크리닝에 추가" \
  --body "stargate815.wordpress.com RSS를 FEEDS에 추가하고 채널 카드·index.html을 갱신합니다."

echo "✅ PR 생성 완료. 머지 후 blog.stargateedu.co.kr 에 반영됩니다."
