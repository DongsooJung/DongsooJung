-- =====================================================================
-- 한입수학 초기 스키마 + RLS 정책 (Supabase / PostgreSQL 15+)
-- 원칙
--   1) 모든 테이블 RLS 활성화, 기본 거부
--   2) 학생은 정답 컬럼을 읽을 수 없고, 채점은 submit_attempt() RPC로만 수행
--   3) 만 14세 미만은 보호자 동의(개인정보보호법 제22조의2) 승인 전 학습 기록 저장 불가
--   4) 보호자는 연결·동의된 자녀만, 강사는 자기 반 학생만 조회
-- =====================================================================

create extension if not exists pgcrypto;

-- ---------- 열거형 ----------
create type public.user_role      as enum ('student', 'guardian', 'teacher', 'admin');
create type public.consent_status as enum ('pending', 'approved', 'revoked');
create type public.content_status as enum ('draft', 'review', 'published', 'archived');
create type public.question_kind  as enum ('mcq', 'short', 'code');
create type public.error_type     as enum ('concept', 'calculation', 'misread');

-- ---------- 사용자 ----------
create table public.profiles (
  id            uuid primary key references auth.users (id) on delete cascade,
  role          public.user_role not null default 'student',
  display_name  text not null check (char_length(display_name) between 1 and 40),
  birth_date    date,
  created_at    timestamptz not null default now()
);

-- 보호자-자녀 연결 및 법정대리인 동의 기록
create table public.guardian_links (
  guardian_id    uuid not null references public.profiles (id) on delete cascade,
  student_id     uuid not null references public.profiles (id) on delete cascade,
  consent        public.consent_status not null default 'pending',
  consent_method text,                      -- 예: 'phone_verify', 'card_verify'
  consented_at   timestamptz,
  created_at     timestamptz not null default now(),
  primary key (guardian_id, student_id),
  check (guardian_id <> student_id)
);

-- 보호자가 설정하는 사용 제한
create table public.usage_limits (
  student_id     uuid primary key references public.profiles (id) on delete cascade,
  daily_minutes  int  not null default 40 check (daily_minutes between 5 and 600),
  night_lock     boolean not null default true,  -- 22:00~07:00 잠금
  updated_by     uuid references public.profiles (id),
  updated_at     timestamptz not null default now()
);

-- 학원 B2B: 반과 구성원
create table public.classes (
  id          uuid primary key default gen_random_uuid(),
  teacher_id  uuid not null references public.profiles (id) on delete cascade,
  name        text not null,
  created_at  timestamptz not null default now()
);
create table public.class_members (
  class_id    uuid not null references public.classes (id) on delete cascade,
  student_id  uuid not null references public.profiles (id) on delete cascade,
  joined_at   timestamptz not null default now(),
  primary key (class_id, student_id)
);

-- ---------- 콘텐츠 ----------
create table public.concepts (
  id       uuid primary key default gen_random_uuid(),
  slug     text unique not null,             -- 예: 'number-theory/fermat-little'
  name     text not null,                    -- 예: '페르마 소정리'
  subject  text not null,                    -- 'math' | 'informatics'
  level    smallint not null check (level between 1 and 5)
);

-- 선수 관계: from_id 를 익혀야 to_id 가 열림
create table public.concept_edges (
  from_id  uuid not null references public.concepts (id) on delete cascade,
  to_id    uuid not null references public.concepts (id) on delete cascade,
  primary key (from_id, to_id),
  check (from_id <> to_id)
);

create table public.videos (
  id                uuid primary key default gen_random_uuid(),
  creator_id        uuid not null references public.profiles (id),
  concept_id        uuid not null references public.concepts (id),
  title             text not null,
  playback_id       text,                    -- Mux / Cloudflare Stream 재생 ID
  duration_sec      smallint not null check (duration_sec between 5 and 180),
  status            public.content_status not null default 'draft',
  created_at        timestamptz not null default now()
);

create table public.questions (
  id                  uuid primary key default gen_random_uuid(),
  concept_id          uuid not null references public.concepts (id),
  video_id            uuid references public.videos (id) on delete set null,
  parent_question_id  uuid references public.questions (id) on delete set null, -- AI 변형 문제의 원본
  kind                public.question_kind not null,
  body                text not null,
  choices             jsonb,                 -- mcq 보기 배열
  answer              text not null,         -- 학생에게 비공개 (컬럼 권한으로 차단)
  explanation         text,
  difficulty          smallint not null default 2 check (difficulty between 1 and 5),
  ai_generated        boolean not null default false,
  status              public.content_status not null default 'draft',
  created_by          uuid references public.profiles (id),
  created_at          timestamptz not null default now()
);

-- ---------- 학습 기록 ----------
create table public.attempts (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references public.profiles (id) on delete cascade,
  question_id  uuid not null references public.questions (id) on delete cascade,
  answer       text not null,
  is_correct   boolean not null,
  elapsed_ms   int not null check (elapsed_ms >= 0),
  error_type   public.error_type,            -- AI 진단 결과 (오답일 때만)
  created_at   timestamptz not null default now()
);
create index attempts_user_time_idx on public.attempts (user_id, created_at desc);

-- 간격 반복 큐 (SM-2 단순화)
create table public.review_queue (
  user_id       uuid not null references public.profiles (id) on delete cascade,
  question_id   uuid not null references public.questions (id) on delete cascade,
  due_at        timestamptz not null,
  interval_days int not null default 1,
  ease          numeric(4,2) not null default 2.50,
  repetitions   int not null default 0,
  primary key (user_id, question_id)
);
create index review_queue_due_idx on public.review_queue (user_id, due_at);

-- 개념 숙련도 (0~1, 지수가중이동평균)
create table public.mastery (
  user_id     uuid not null references public.profiles (id) on delete cascade,
  concept_id  uuid not null references public.concepts (id) on delete cascade,
  score       numeric(4,3) not null default 0 check (score between 0 and 1),
  attempts    int not null default 0,
  updated_at  timestamptz not null default now(),
  primary key (user_id, concept_id)
);

-- =====================================================================
-- 권한 판정 헬퍼 (security definer: RLS 재귀 방지)
-- =====================================================================
create or replace function public.my_role() returns public.user_role
language sql stable security definer set search_path = public as $$
  select role from public.profiles where id = auth.uid()
$$;

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce(public.my_role() = 'admin', false)
$$;

create or replace function public.is_guardian_of(p_student uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.guardian_links
    where guardian_id = auth.uid() and student_id = p_student and consent <> 'revoked')
$$;

create or replace function public.is_teacher_of(p_student uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.class_members m join public.classes c on c.id = m.class_id
    where c.teacher_id = auth.uid() and m.student_id = p_student)
$$;

-- 만 14세 미만이면 승인된 보호자 동의가 있어야 서비스 이용 가능
create or replace function public.can_use_service(p_user uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select case
    when p.birth_date is null then false
    when p.birth_date > (current_date - interval '14 years') then exists (
      select 1 from public.guardian_links g
      where g.student_id = p.id and g.consent = 'approved')
    else true end
  from public.profiles p where p.id = p_user
$$;

-- =====================================================================
-- RLS
-- =====================================================================
alter table public.profiles       enable row level security;
alter table public.guardian_links enable row level security;
alter table public.usage_limits   enable row level security;
alter table public.classes        enable row level security;
alter table public.class_members  enable row level security;
alter table public.concepts       enable row level security;
alter table public.concept_edges  enable row level security;
alter table public.videos         enable row level security;
alter table public.questions      enable row level security;
alter table public.attempts       enable row level security;
alter table public.review_queue   enable row level security;
alter table public.mastery        enable row level security;

-- profiles: 본인, 연결된 보호자, 담당 강사, 관리자만 조회
create policy profiles_select on public.profiles for select to authenticated
  using (id = auth.uid() or public.is_guardian_of(id) or public.is_teacher_of(id) or public.is_admin());
create policy profiles_insert_self on public.profiles for insert to authenticated
  with check (id = auth.uid() and role in ('student', 'guardian'));   -- teacher/admin 은 관리자가 지정
create policy profiles_update_self on public.profiles for update to authenticated
  using (id = auth.uid()) with check (id = auth.uid()); -- 수정 가능한 컬럼은 display_name 뿐 (아래 컬럼 권한)

-- guardian_links: 보호자가 요청을 만들고, 당사자 둘만 조회
create policy gl_select on public.guardian_links for select to authenticated
  using (guardian_id = auth.uid() or student_id = auth.uid() or public.is_admin());
create policy gl_insert on public.guardian_links for insert to authenticated
  with check (guardian_id = auth.uid() and public.my_role() = 'guardian' and consent = 'pending');
-- 동의 승인/철회는 본인인증 후 서버(Edge Function, service_role)가 처리하므로 update 정책 없음

-- usage_limits: 학생은 읽기만, 보호자만 수정
create policy ul_select on public.usage_limits for select to authenticated
  using (student_id = auth.uid() or public.is_guardian_of(student_id));
create policy ul_write on public.usage_limits for all to authenticated
  using (public.is_guardian_of(student_id))
  with check (public.is_guardian_of(student_id) and updated_by = auth.uid());

-- classes / class_members: 강사 본인 관리, 학생은 소속 반 조회
create policy classes_teacher on public.classes for all to authenticated
  using (teacher_id = auth.uid()) with check (teacher_id = auth.uid() and public.my_role() = 'teacher');
create policy classes_member_read on public.classes for select to authenticated
  using (exists (select 1 from public.class_members m where m.class_id = id and m.student_id = auth.uid()));
create policy cm_teacher on public.class_members for all to authenticated
  using (exists (select 1 from public.classes c where c.id = class_id and c.teacher_id = auth.uid()))
  with check (exists (select 1 from public.classes c where c.id = class_id and c.teacher_id = auth.uid()));
create policy cm_self_read on public.class_members for select to authenticated
  using (student_id = auth.uid());

-- 개념 그래프: 로그인 사용자 모두 읽기, 쓰기는 관리자
create policy concepts_read on public.concepts for select to authenticated using (true);
create policy concepts_admin on public.concepts for all to authenticated using (public.is_admin()) with check (public.is_admin());
create policy edges_read on public.concept_edges for select to authenticated using (true);
create policy edges_admin on public.concept_edges for all to authenticated using (public.is_admin()) with check (public.is_admin());

-- videos: 게시된 것 + 본인 작성분 조회, 강사만 작성, 게시 승인은 관리자
create policy videos_read on public.videos for select to authenticated
  using (status = 'published' or creator_id = auth.uid() or public.is_admin());
create policy videos_insert on public.videos for insert to authenticated
  with check (creator_id = auth.uid() and public.my_role() = 'teacher' and status in ('draft', 'review'));
create policy videos_update on public.videos for update to authenticated
  using (creator_id = auth.uid() or public.is_admin())
  with check (public.is_admin() or (creator_id = auth.uid() and status in ('draft', 'review', 'archived')));

-- questions: 행 단위는 videos 와 동일, 정답 컬럼은 아래 컬럼 권한으로 차단
create policy questions_read on public.questions for select to authenticated
  using (status = 'published' or created_by = auth.uid() or public.is_admin());
create policy questions_insert on public.questions for insert to authenticated
  with check (created_by = auth.uid() and public.my_role() in ('teacher', 'admin'));
create policy questions_update on public.questions for update to authenticated
  using (created_by = auth.uid() or public.is_admin())
  with check (public.is_admin() or (created_by = auth.uid() and status <> 'published'));

-- attempts / review_queue / mastery: 본인, 보호자, 담당 강사만 읽기. 쓰기는 RPC 전용
create policy attempts_read on public.attempts for select to authenticated
  using (user_id = auth.uid() or public.is_guardian_of(user_id) or public.is_teacher_of(user_id));
create policy rq_read on public.review_queue for select to authenticated
  using (user_id = auth.uid());
create policy mastery_read on public.mastery for select to authenticated
  using (user_id = auth.uid() or public.is_guardian_of(user_id) or public.is_teacher_of(user_id));

-- ---------- 테이블·컬럼 권한 ----------
-- Supabase 는 public 스키마 테이블에 anon/authenticated 전체 권한을 기본 부여하므로
-- 먼저 모두 회수한 뒤 필요한 권한만 컬럼 단위로 다시 부여합니다.
revoke all on all tables in schema public from anon, authenticated;

grant select on public.profiles, public.guardian_links, public.usage_limits,
                public.classes, public.class_members, public.concepts, public.concept_edges,
                public.videos, public.attempts, public.review_queue, public.mastery
  to authenticated;

-- profiles: 가입 시 생성, 이후 표시 이름만 수정 가능 (역할·생년월일 변경으로 동의 우회 차단)
grant insert (id, role, display_name, birth_date) on public.profiles to authenticated;
grant update (display_name) on public.profiles to authenticated;

-- guardian_links: 보호자는 연결 요청만 생성 (동의 상태 컬럼은 서버만 변경)
grant insert (guardian_id, student_id) on public.guardian_links to authenticated;

grant insert, update, delete on public.usage_limits, public.classes, public.class_members,
                                public.concepts, public.concept_edges to authenticated;
grant insert, update on public.videos to authenticated;

-- questions: 정답·해설 컬럼은 조회 불가 (강사는 get_answer_key() 로 확인)
grant select (id, concept_id, video_id, parent_question_id, kind, body, choices,
              difficulty, ai_generated, status, created_by, created_at)
  on public.questions to authenticated;
grant insert, update on public.questions to authenticated;

-- attempts / review_queue / mastery 는 쓰기 권한을 주지 않음 (submit_attempt() 로만 기록)

-- 강사·관리자용 정답 조회 (본인 문항 또는 관리자)
create or replace function public.get_answer_key(p_question uuid)
returns table (answer text, explanation text)
language sql stable security definer set search_path = public as $$
  select q.answer, q.explanation from public.questions q
  where q.id = p_question and (q.created_by = auth.uid() or public.is_admin())
$$;

-- =====================================================================
-- 채점 RPC: 정답 확인 → 기록 → 숙련도·복습 큐 갱신
-- =====================================================================
create or replace function public.submit_attempt(
  p_question uuid, p_answer text, p_elapsed_ms int)
returns table (is_correct boolean, explanation text, mastery_score numeric, next_review timestamptz)
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
  q     public.questions%rowtype;
  v_ok  boolean;
  v_m   numeric;
  rq    public.review_queue%rowtype;
  v_due timestamptz;
begin
  if v_uid is null then raise exception '로그인이 필요합니다' using errcode = '28000'; end if;
  if not public.can_use_service(v_uid) then
    raise exception '만 14세 미만은 보호자 동의 후 이용할 수 있습니다' using errcode = '42501';
  end if;

  select * into q from public.questions where id = p_question and status = 'published';
  if not found then raise exception '문항을 찾을 수 없습니다' using errcode = 'P0002'; end if;

  v_ok := lower(btrim(p_answer)) = lower(btrim(q.answer));

  insert into public.attempts (user_id, question_id, answer, is_correct, elapsed_ms)
  values (v_uid, p_question, p_answer, v_ok, greatest(p_elapsed_ms, 0));

  -- 숙련도: EWMA (alpha = 0.3)
  insert into public.mastery as m (user_id, concept_id, score, attempts)
  values (v_uid, q.concept_id, case when v_ok then 0.3 else 0 end, 1)
  on conflict (user_id, concept_id) do update
    set score = round(m.score * 0.7 + (case when v_ok then 0.3 else 0 end), 3),
        attempts = m.attempts + 1, updated_at = now()
  returning score into v_m;

  -- 복습 큐: 정답이면 간격 확대, 오답이면 1일 뒤로 초기화
  select * into rq from public.review_queue where user_id = v_uid and question_id = p_question;
  if not found then
    if v_ok then
      v_due := null;                          -- 처음부터 맞힌 문항은 큐에 넣지 않음
    else
      v_due := now() + interval '1 day';
      insert into public.review_queue (user_id, question_id, due_at) values (v_uid, p_question, v_due);
    end if;
  elsif v_ok then
    rq.repetitions   := rq.repetitions + 1;
    rq.interval_days := case rq.repetitions when 1 then 3 when 2 then 7
                          else ceil(rq.interval_days * rq.ease)::int end;
    v_due := now() + make_interval(days => rq.interval_days);
    update public.review_queue set repetitions = rq.repetitions, interval_days = rq.interval_days,
      due_at = v_due where user_id = v_uid and question_id = p_question;
  else
    v_due := now() + interval '1 day';
    update public.review_queue set repetitions = 0, interval_days = 1,
      ease = greatest(1.30, rq.ease - 0.20), due_at = v_due
      where user_id = v_uid and question_id = p_question;
  end if;

  return query select v_ok, q.explanation, v_m, v_due;
end $$;

-- AI 진단 결과 기록 (Edge Function 이 service_role 로 호출)
create or replace function public.set_error_type(p_attempt bigint, p_type public.error_type)
returns void language sql security definer set search_path = public as $$
  update public.attempts set error_type = p_type where id = p_attempt and is_correct = false
$$;

-- 함수 실행 권한 정리
revoke execute on all functions in schema public from public, anon;
grant execute on function public.submit_attempt(uuid, text, int)      to authenticated;
grant execute on function public.get_answer_key(uuid)                  to authenticated;
grant execute on function public.can_use_service(uuid)                 to authenticated;
grant execute on function public.my_role(), public.is_admin(),
                          public.is_guardian_of(uuid), public.is_teacher_of(uuid) to authenticated;
-- set_error_type 은 service_role 전용 (Supabase 에서 service_role 은 RLS 우회)

-- 보호자 대시보드용 주간 요약 뷰 (호출자 권한으로 RLS 적용)
create view public.weekly_report with (security_invoker = true) as
select a.user_id,
       date_trunc('week', a.created_at)                    as week,
       count(*)                                            as solved,
       round(avg(a.is_correct::int) * 100, 1)              as accuracy_pct,
       round(sum(a.elapsed_ms) / 60000.0, 1)               as solve_minutes
from public.attempts a
group by a.user_id, date_trunc('week', a.created_at);
grant select on public.weekly_report to authenticated;
