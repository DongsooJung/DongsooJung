// n8n 블로그 자동화 → blog.stargateedu.co.kr 허브 연동 웹훅
//
// n8n 워크플로가 네이버/티스토리/워드프레스 등에 글을 발행한 직후
// 이 엔드포인트로 POST 하면 data/n8n-posts.json 이 GitHub Contents API 로 갱신되고,
// 해당 커밋이 "허브 RSS 자동갱신" 워크플로를 트리거하여 index.html 이 즉시 재빌드됩니다.
//
// 인증: 헤더 X-Stargate-Webhook-Key == N8N_WEBHOOK_KEY (timing-safe 비교)
// 선택: 헤더 X-Stargate-Signature == "sha256=" + HMAC-SHA256(N8N_WEBHOOK_SECRET, rawBody)

const crypto = require("node:crypto");

const REPOSITORY = process.env.GITHUB_REPOSITORY || "DongsooJung/stargate-blog-hub";
const FEED_PATH = process.env.N8N_FEED_PATH || "data/n8n-posts.json";
const BRANCH = process.env.GITHUB_BRANCH || "main";
const MAX_POSTS = Number(process.env.N8N_MAX_POSTS || 200);
const MAX_BATCH = 50;

function send(res, status, body) {
  res.status(status).setHeader("content-type", "application/json; charset=utf-8");
  res.setHeader("cache-control", "no-store");
  res.end(JSON.stringify(body));
}

function safeEqual(left, right) {
  const a = Buffer.from(String(left || ""));
  const b = Buffer.from(String(right || ""));
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

// WordPress REST 응답의 { rendered } / { raw } 객체와 HTML 태그·엔티티를 평문으로 변환
function plain(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    value = value.rendered ?? value.raw ?? value.value ?? "";
  }
  return String(value ?? "")
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#0?39;|&#8217;|&#8216;/g, "'")
    .replace(/&#8220;|&#8221;/g, '"')
    .replace(/&#8211;/g, "–")
    .replace(/&#8212;/g, "—")
    .replace(/&#8230;|\[&hellip;\]|&hellip;/g, "…");
}

// URL 호스트로 허브 채널명 판별 (build_hub_index.py FEEDS 키와 동일)
function inferChannel(link) {
  try {
    const url = new URL(link);
    const host = url.hostname.replace(/^m\./, "");
    if (host === "blog.naver.com") {
      if (/^\/stargate8225(\/|$)/.test(url.pathname)) return "네이버 법인";
      if (/^\/stargate8224(\/|$)/.test(url.pathname)) return "네이버 개인";
      return "네이버 블로그";
    }
    if (host.endsWith(".tistory.com")) return "티스토리";
    if (host.endsWith(".wordpress.com") || host.endsWith(".wordpress.org")) return "워드프레스";
    if (host.endsWith("youtube.com") || host === "youtu.be") return "YouTube 우주인";
  } catch {}
  return "";
}

function text(value, max) {
  if (value == null) return "";
  const out = (Array.isArray(value) ? value.map(plain).join(", ") : plain(value))
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return out.length > max ? `${out.slice(0, max - 1)}…` : out;
}

function httpUrl(value) {
  try {
    const url = new URL(String(value || "").trim());
    return ["http:", "https:"].includes(url.protocol) ? url.toString() : "";
  } catch {
    return "";
  }
}

function normalizeLink(link) {
  try {
    const url = new URL(link);
    url.hash = "";
    for (const key of [...url.searchParams.keys()]) {
      if (/^utm_|^fbclid$|^gclid$/i.test(key)) url.searchParams.delete(key);
    }
    return url.toString().replace(/\/$/, "");
  } catch {
    return link;
  }
}

function isoDate(value) {
  const parsed = value ? new Date(value) : new Date();
  return Number.isNaN(parsed.getTime()) ? new Date().toISOString() : parsed.toISOString();
}

// n8n 에서 오는 다양한 필드명을 하나의 스키마로 정규화
// (n8n WordPress 노드 응답: id·link·title.rendered·excerpt.rendered·date_gmt·status 그대로 수용)
const HIDE_STATUSES = ["unpublish", "delete", "deleted", "remove", "draft", "trash", "private", "future", "pending"];

function toPost(raw) {
  const item = raw && typeof raw === "object" && raw.json && typeof raw.json === "object" ? raw.json : raw || {};
  const link = httpUrl(item.url || item.link || item.postUrl || item.permalink);
  const title = text(item.title || item.subject || item.name, 200);
  const action = String(item.action || item.status || "publish").toLowerCase();
  const rawTags = Array.isArray(item.tags) ? item.tags : text(item.tags, 300).split(",");
  // WordPress 응답의 숫자 태그 ID 는 제외
  const tags = rawTags.map((tag) => text(tag, 30)).filter((tag) => tag && !/^\d+$/.test(tag)).slice(0, 10);
  const channel = text(item.channel || item.platform || item.source, 40) || inferChannel(link) || "n8n 자동발행";
  const sourceId = text(item.postId || item.id, 100);
  const id = sourceId
    ? `${channel}:${sourceId}`
    : crypto.createHash("sha256").update(normalizeLink(link) || title).digest("hex").slice(0, 32);
  return {
    id,
    title,
    link,
    channel,
    date: isoDate(item.publishedAt || item.published_at || (item.date_gmt ? `${item.date_gmt}Z` : "") || item.date || item.createdAt),
    summary: text(item.summary || item.excerpt || item.description, 300),
    thumbnail: httpUrl(item.thumbnail || item.image || item.imageUrl || item.jetpack_featured_media_url),
    tags,
    workflow: text(item.workflow || item.workflowName, 80),
    unpublish: HIDE_STATUSES.includes(action),
  };
}

async function github(path, options = {}) {
  const token = process.env.GITHUB_CONTENTS_TOKEN;
  if (!token) throw new Error("GITHUB_CONTENTS_TOKEN is not configured");
  const response = await fetch(`https://api.github.com/repos/${REPOSITORY}/${path}`, {
    ...options,
    headers: {
      accept: "application/vnd.github+json",
      authorization: `Bearer ${token}`,
      "x-github-api-version": "2022-11-28",
      "user-agent": "stargate-n8n-webhook/1.0",
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(`GitHub API ${response.status}: ${data.message || "request failed"}`);
    error.status = response.status;
    throw error;
  }
  return data;
}

function merge(existing, incoming) {
  let posts = Array.isArray(existing) ? existing.slice() : [];
  const result = { published: 0, unpublished: 0 };
  for (const post of incoming) {
    const key = normalizeLink(post.link);
    const same = (item) => item.id === post.id || (key && normalizeLink(item.link) === key);
    const before = posts.length;
    posts = posts.filter((item) => !same(item));
    if (post.unpublish) {
      if (posts.length < before) result.unpublished += 1;
      continue;
    }
    const { unpublish, ...stored } = post;
    posts.unshift(stored);
    result.published += 1;
  }
  posts.sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")));
  return { posts: posts.slice(0, MAX_POSTS), ...result };
}

async function updateFeed(incoming, attempt = 0) {
  const encodedPath = FEED_PATH.split("/").map(encodeURIComponent).join("/");
  let current = null;
  let feed = { posts: [] };
  try {
    current = await github(`contents/${encodedPath}?ref=${encodeURIComponent(BRANCH)}`);
    feed = JSON.parse(Buffer.from(current.content.replace(/\n/g, ""), "base64").toString("utf8"));
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  const next = merge(feed.posts, incoming);
  if (next.published === 0 && next.unpublished === 0) return { ...next, committed: false };
  const label = incoming.length === 1 ? incoming[0].title : `${incoming.length}건`;
  const body = {
    message: `chore(n8n): ${label} ${next.published ? "발행" : "공개 해제"} 동기화`,
    content: Buffer.from(JSON.stringify({
      generatedAt: new Date().toISOString(),
      source: "n8n webhook · 블로그 자동화",
      posts: next.posts,
    }, null, 2) + "\n").toString("base64"),
    branch: BRANCH,
    ...(current ? { sha: current.sha } : {}),
  };
  try {
    await github(`contents/${encodedPath}`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (error) {
    // 동시 발행 시 sha 충돌(409/422) → 최신본 재조회 후 1회 재시도
    if ([409, 422].includes(error.status) && attempt < 2) return updateFeed(incoming, attempt + 1);
    throw error;
  }
  return { ...next, committed: true };
}

function rawBody(req) {
  if (typeof req.body === "string") return req.body;
  if (Buffer.isBuffer(req.body)) return req.body.toString("utf8");
  return req.body ? JSON.stringify(req.body) : "";
}

module.exports = async function handler(req, res) {
  if (req.method === "GET") return send(res, 200, { ok: true, service: "stargate-n8n-blog-webhook" });
  if (req.method !== "POST") return send(res, 405, { ok: false, error: "method_not_allowed" });

  const expected = process.env.N8N_WEBHOOK_KEY;
  if (!expected || !safeEqual(req.headers["x-stargate-webhook-key"], expected)) {
    return send(res, 401, { ok: false, error: "unauthorized" });
  }

  const body = rawBody(req);
  const secret = process.env.N8N_WEBHOOK_SECRET;
  if (secret) {
    const digest = `sha256=${crypto.createHmac("sha256", secret).update(body).digest("hex")}`;
    if (!safeEqual(req.headers["x-stargate-signature"], digest)) {
      return send(res, 401, { ok: false, error: "bad_signature" });
    }
  }

  let payload;
  try {
    payload = typeof req.body === "object" && req.body && !Buffer.isBuffer(req.body) ? req.body : JSON.parse(body || "{}");
  } catch {
    return send(res, 400, { ok: false, error: "invalid_json" });
  }

  // 단건 객체, 배열, { posts: [...] }, n8n items([{ json }]) 모두 허용
  const list = Array.isArray(payload) ? payload : Array.isArray(payload.posts) ? payload.posts : [payload];
  if (list.length === 0 || list.length > MAX_BATCH) {
    return send(res, 422, { ok: false, error: "batch_size", max: MAX_BATCH });
  }
  const posts = list.map(toPost);
  const invalid = posts
    .map((post, index) => (!post.title || (!post.link && !post.unpublish) ? index : -1))
    .filter((index) => index >= 0);
  if (invalid.length) return send(res, 422, { ok: false, error: "missing_title_or_url", invalid });

  try {
    const result = await updateFeed(posts);
    return send(res, 200, {
      ok: true,
      committed: result.committed,
      published: result.published,
      unpublished: result.unpublished,
      count: result.posts.length,
    });
  } catch (error) {
    console.error(error);
    return send(res, 502, { ok: false, error: "sync_failed" });
  }
};

module.exports._internal = { toPost, merge, normalizeLink, inferChannel };
