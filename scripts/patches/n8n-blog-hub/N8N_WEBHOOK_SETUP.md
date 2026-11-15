# n8n 블로그 자동화 → 블로그 허브 연동

n8n 이 네이버·티스토리·워드프레스 등에 글을 발행하면 **즉시** `blog.stargateedu.co.kr` "최신 포스팅"에 반영합니다.
RSS 일일 수집(KST 03:00)을 기다리지 않습니다.

## 데이터 흐름

```
n8n 블로그 자동화 ──(Execute Workflow)──▶ "STARGATE · 블로그 허브 동기화"
   └─ HTTP POST  https://stargate-reading-blog.vercel.app/api/n8n-blog-webhook
        └─ GitHub Contents API → data/n8n-posts.json 커밋 (PAT)
             └─ push 트리거 → "허브 RSS 자동갱신" → index.html 재빌드 → GitHub Pages
```

같은 글이 나중에 RSS 로도 수집되면 URL(utm 파라미터 제거) 기준으로 중복을 제거하며 RSS 항목을 우선합니다.

## 1. Vercel 환경 변수 (`stargate-reading-blog` 프로젝트)

| 변수 | 필수 | 설명 |
|---|---|---|
| `GITHUB_CONTENTS_TOKEN` | 필수 | 기존 Notion 웹훅과 공용. `stargate-blog-hub` 한 저장소 Contents read/write Fine-grained PAT |
| `N8N_WEBHOOK_KEY` | 필수 | 임의의 긴 랜덤 문자열 (`openssl rand -hex 32`) |
| `N8N_WEBHOOK_SECRET` | 선택 | 설정 시 `X-Stargate-Signature: sha256=<HMAC>` 검증 활성화 |
| `N8N_FEED_PATH` | 선택 | 기본 `data/n8n-posts.json` |
| `N8N_MAX_POSTS` | 선택 | 보관 최대 건수, 기본 200 |

> PAT 로 생성된 커밋이어야 push 워크플로가 트리거됩니다. `GITHUB_TOKEN` 커밋은 트리거되지 않습니다.

## 2. n8n 설정

1. `Workflows → Import from File` → `n8n/블로그허브_동기화_워크플로.json`
2. `Credentials → New → Header Auth`
   - Name: `Stargate Hub Webhook Key`
   - Header Name: `X-Stargate-Webhook-Key`
   - Value: Vercel 의 `N8N_WEBHOOK_KEY` 와 동일
3. "허브 웹훅 전송" 노드에서 위 크리덴셜 선택 → 저장 → `수동 테스트` 실행
4. 기존 블로그 자동화 워크플로의 **발행 성공 노드 뒤**에 `Execute Workflow` 노드 추가 → 이 워크플로 선택

### 2-1. 기존 발행 워크플로와 연결 (T43: 네이버·워드프레스 2채널)

| 상위 발행 노드 | 연결 방법 | 필드 변환 |
|---|---|---|
| **WordPress** 노드 (`Post → Create`) | 바로 뒤에 `Execute Workflow` | 불필요. `id`·`link`·`title.rendered`·`excerpt.rendered`·`date_gmt`·`status` 를 그대로 수용 |
| **네이버 블로그** (발행 후 URL 확보 단계) | `Set` 으로 `title`, `url` 두 필드만 만든 뒤 `Execute Workflow` | 채널은 URL 로 판별: `blog.naver.com/stargate8224` → 네이버 개인, `/stargate8225` → 네이버 법인 |
| 티스토리 | 사용하지 않음 | Open API 종료로 자동 발행 불가. 수동 발행 글은 기존 RSS 로 수집 |

WordPress `status` 가 `draft`·`trash`·`private`·`future`·`pending` 이면 허브에서 숨깁니다(공개 해제).

### 2-2. 실패 알림 (Gmail + WF0 오류 로그)

1. `Credentials → New → Gmail OAuth2` 생성 → "실패 메일 알림" 노드에 연결
2. 수신자 기본값은 `stargate8225@gmail.com` 입니다. 노드의 `To` 에서 변경할 수 있습니다.
3. 이 워크플로 `Settings → Error workflow` = **WF0 오류 로그** → 실패 시 Notion 「🧾 n8n 실행 로그」에도 한 줄이 남습니다.

실패 경로: `성공 여부(false)` → `실패 메일 알림`(메일 실패해도 계속 진행) → `실패 알림`(Stop and Error) → WF0 기록.
네트워크 오류도 HTTP 노드의 `On Error: Continue` 설정 덕분에 같은 경로를 탑니다.

## 3. 페이로드 스키마

단건 객체, 배열, `{ "posts": [...] }`, n8n items(`[{ "json": {...} }]`) 모두 허용합니다. 1회 최대 50건.

| 필드 | 별칭 | 필수 | 비고 |
|---|---|---|---|
| `title` | `subject`, `name` | 필수 | 200자 절단 |
| `url` | `link`, `postUrl`, `permalink` | 발행 시 필수 | http/https 만 허용 |
| `channel` | `platform`, `source` | 선택 | 없으면 URL 로 자동 판별. `네이버 개인`·`네이버 법인`·`티스토리`·`워드프레스`·`YouTube 우주인` 이면 기존 아이콘/색상, 그 외 🤖 |
| `publishedAt` | `published_at`, `date_gmt`, `date` | 선택 | ISO 8601, 없으면 수신 시각 |
| `summary`, `tags`, `thumbnail`, `id` | | 선택 | |
| `action` | `status` | 선택 | `publish`(기본) / `unpublish`·`delete`·`draft`·`trash`·`private`·`future`·`pending` → 허브에서 제거 |

## 4. 수동 확인

```bash
curl -X POST https://stargate-reading-blog.vercel.app/api/n8n-blog-webhook \
  -H "content-type: application/json" \
  -H "X-Stargate-Webhook-Key: $N8N_WEBHOOK_KEY" \
  -d '{"title":"연동 테스트","url":"https://dongsoo.tistory.com/","channel":"티스토리"}'
# → {"ok":true,"committed":true,"published":1,"unpublished":0,"count":1}
```

응답 코드: `200` 성공 · `401` 키/서명 불일치 · `422` title/url 누락 또는 50건 초과 · `502` GitHub 커밋 실패.
