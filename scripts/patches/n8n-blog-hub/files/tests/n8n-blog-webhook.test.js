const assert = require("node:assert/strict");
const crypto = require("node:crypto");

process.env.N8N_WEBHOOK_KEY = "test-n8n-key";
process.env.GITHUB_CONTENTS_TOKEN = "test-github-token";

let stored = null; // null → 파일 없음(404)
let writes = 0;
let conflictOnce = false;

global.fetch = async (_url, options = {}) => {
  if (!options.method || options.method === "GET") {
    if (!stored) return { ok: false, status: 404, json: async () => ({ message: "Not Found" }) };
    return {
      ok: true,
      status: 200,
      json: async () => ({ sha: `sha-${writes}`, content: Buffer.from(JSON.stringify(stored)).toString("base64") }),
    };
  }
  if (conflictOnce) {
    conflictOnce = false;
    return { ok: false, status: 409, json: async () => ({ message: "sha conflict" }) };
  }
  const body = JSON.parse(options.body);
  stored = JSON.parse(Buffer.from(body.content, "base64").toString("utf8"));
  writes += 1;
  return { ok: true, status: 200, json: async () => ({ content: { sha: `sha-${writes}` } }) };
};

const handler = require("../api/n8n-blog-webhook");

function response() {
  return {
    statusCode: 0,
    headers: {},
    status(code) { this.statusCode = code; return this; },
    setHeader(name, value) { this.headers[name] = value; },
    end(body) { this.body = JSON.parse(body); },
  };
}

async function call(body, headers = { "x-stargate-webhook-key": "test-n8n-key" }) {
  const res = response();
  await handler({ method: "POST", headers, body }, res);
  return res;
}

(async () => {
  // 1) 인증 실패
  let res = await call({ title: "x", url: "https://a.example/1" }, { "x-stargate-webhook-key": "wrong" });
  assert.equal(res.statusCode, 401);

  // 2) 필수 필드 누락
  res = await call({ title: "", url: "" });
  assert.equal(res.statusCode, 422);

  // 3) 파일 없음(404) 상태에서 단건 발행 → 새 파일 생성
  res = await call({
    title: "KOI 2차 대비 DP 정리",
    url: "https://blog.naver.com/stargate8224/1?utm_source=n8n",
    channel: "네이버 개인",
    publishedAt: "2026-11-14T09:00:00+09:00",
    tags: ["KOI", "DP"],
  });
  assert.equal(res.statusCode, 200);
  assert.equal(res.body.published, 1);
  assert.equal(stored.posts.length, 1);
  assert.equal(stored.posts[0].channel, "네이버 개인");
  assert.equal(stored.posts[0].date, "2026-11-14T00:00:00.000Z");

  // 4) n8n items 배열([{ json }]) 일괄 발행 + 동일 URL(utm 제거) 중복 제거 + sha 충돌 재시도
  conflictOnce = true;
  res = await call([
    { json: { title: "KOI 2차 대비 DP 정리 (수정)", link: "https://blog.naver.com/stargate8224/1", platform: "네이버 개인", date: "2026-11-14" } },
    { json: { title: "GraphRAG 실습", link: "https://dongsoo.tistory.com/99", platform: "티스토리", date: "2026-11-15" } },
  ]);
  assert.equal(res.statusCode, 200);
  assert.equal(res.body.published, 2);
  assert.equal(stored.posts.length, 2);
  assert.equal(stored.posts[0].title, "GraphRAG 실습");
  assert.equal(stored.posts[1].title, "KOI 2차 대비 DP 정리 (수정)");

  // 5) 공개 해제
  res = await call({ action: "unpublish", url: "https://dongsoo.tistory.com/99", title: "GraphRAG 실습" });
  assert.equal(res.statusCode, 200);
  assert.equal(res.body.unpublished, 1);
  assert.equal(stored.posts.length, 1);

  // 6) 변경 없음 → 커밋 생략
  const before = writes;
  res = await call({ action: "unpublish", url: "https://nothing.example/0", title: "없음" });
  assert.equal(res.body.committed, false);
  assert.equal(writes, before);

  // 7) HMAC 서명 검증
  process.env.N8N_WEBHOOK_SECRET = "hmac-secret";
  const payload = { title: "서명 테스트", url: "https://stargate815.wordpress.com/p/1", channel: "워드프레스" };
  res = await call(payload, { "x-stargate-webhook-key": "test-n8n-key", "x-stargate-signature": "sha256=bad" });
  assert.equal(res.statusCode, 401);
  const sig = `sha256=${crypto.createHmac("sha256", "hmac-secret").update(JSON.stringify(payload)).digest("hex")}`;
  res = await call(payload, { "x-stargate-webhook-key": "test-n8n-key", "x-stargate-signature": sig });
  assert.equal(res.statusCode, 200);
  delete process.env.N8N_WEBHOOK_SECRET;

  // 8) javascript: 스킴 차단
  res = await call({ title: "XSS", url: "javascript:alert(1)" });
  assert.equal(res.statusCode, 422);

  console.log("n8n-blog-webhook: ok");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
