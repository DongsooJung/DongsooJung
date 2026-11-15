#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stargate-blog-hub 작업 트리에 n8n 연동을 적용합니다 (멱등).

사용: python3 patch_blog_hub.py <stargate-blog-hub 경로>
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARK = "# ── n8n 연동 ──"

LOADER = '''
# ───────────────────────────────────────────────────────────────────
''' + MARK + '''
# api/n8n-blog-webhook.js 가 갱신하는 data/n8n-posts.json 을 RSS 결과와 병합
# ───────────────────────────────────────────────────────────────────

N8N_POSTS_PATH = Path(os.environ.get("N8N_POSTS_PATH", BASE_DIR / "data" / "n8n-posts.json"))
N8N_DEFAULT = {"icon": "🤖", "color": "#EA4B71"}


def _norm_link(link: str) -> str:
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    try:
        p = urlsplit(link)
        q = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith("utm_")]
        return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip("/"), urlencode(q), ""))
    except Exception:
        return link


def load_n8n_posts() -> list[dict]:
    if not N8N_POSTS_PATH.exists():
        return []
    try:
        import json
        data = json.loads(N8N_POSTS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        log("WARN", f"n8n 피드 파싱 실패: {exc}")
        return []
    posts = []
    for item in data.get("posts", []):
        link = str(item.get("link") or "")
        title = str(item.get("title") or "").strip()
        if not title or not link.startswith(("http://", "https://")):
            continue
        channel = str(item.get("channel") or "n8n 자동발행")
        meta = FEEDS.get(channel, N8N_DEFAULT)
        date = str(item.get("date") or "")[:10]
        posts.append({
            "channel": channel,
            "icon": meta.get("icon", N8N_DEFAULT["icon"]),
            "color": meta.get("color", N8N_DEFAULT["color"]),
            "title": title,
            "link": link,
            "date": date or "-",
            "sort_key": date or "0000-00-00",
        })
    log("INFO", f"n8n 자동발행: {len(posts)}개 로드")
    return posts


def merge_unique(rss_posts: list[dict], n8n_posts: list[dict]) -> list[dict]:
    """같은 글(정규화 URL 기준)은 RSS 항목을 우선하고 n8n 항목은 RSS 미반영분만 추가."""
    seen = {_norm_link(p["link"]) for p in rss_posts}
    extra = [p for p in n8n_posts if _norm_link(p["link"]) not in seen]
    return rss_posts + extra

'''


def patch_builder(repo: Path) -> None:
    path = repo / "scripts" / "build_hub_index.py"
    text = path.read_text(encoding="utf-8")
    if MARK in text:
        print("build_hub_index.py: 이미 적용됨")
        return
    anchor = "# ───────────────────────────────────────────────────────────────────\n# 렌더링"
    if anchor not in text:
        raise SystemExit("렌더링 섹션 앵커를 찾지 못했습니다 — upstream 변경 확인 필요")
    text = text.replace(anchor, LOADER.lstrip("\n") + "\n" + anchor, 1)
    old = "    all_posts.sort(key=lambda x: x[\"sort_key\"], reverse=True)"
    if old not in text:
        raise SystemExit("정렬 구문을 찾지 못했습니다 — upstream 변경 확인 필요")
    text = text.replace(old, "    all_posts = merge_unique(all_posts, load_n8n_posts())\n" + old, 1)
    path.write_text(text, encoding="utf-8")
    print("build_hub_index.py: n8n 병합 추가")


def patch_workflow(repo: Path) -> None:
    path = repo / ".github" / "workflows" / "허브_RSS_자동갱신.yml"
    text = path.read_text(encoding="utf-8")
    if "data/n8n-posts.json" in text:
        print("허브_RSS_자동갱신.yml: 이미 적용됨")
        return
    old = "      - 'scripts/build_hub_index.py'\n"
    if old not in text:
        raise SystemExit("workflow push.paths 앵커를 찾지 못했습니다")
    text = text.replace(old, old + "      - 'data/n8n-posts.json'\n", 1)
    path.write_text(text, encoding="utf-8")
    print("허브_RSS_자동갱신.yml: data/n8n-posts.json 푸시 트리거 추가")


def copy_files(repo: Path) -> None:
    src = HERE / "files"
    for file in src.rglob("*"):
        if file.is_dir():
            continue
        rel = file.relative_to(src)
        dest = repo / rel
        if rel.as_posix() == "data/n8n-posts.json" and dest.exists():
            continue  # 운영 데이터 보존
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, dest)
        print(f"복사: {rel.as_posix()}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    repo = Path(sys.argv[1]).resolve()
    if not (repo / "scripts" / "build_hub_index.py").exists():
        raise SystemExit(f"stargate-blog-hub 작업 트리가 아닙니다: {repo}")
    copy_files(repo)
    patch_builder(repo)
    patch_workflow(repo)


if __name__ == "__main__":
    main()
