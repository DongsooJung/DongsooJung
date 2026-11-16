-- 로컬 검증용: Supabase auth 스텁 (실제 Supabase 에서는 실행하지 마십시오)
create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls;
create schema auth; create table auth.users(id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true),'')::uuid $$;
grant usage on schema auth, public to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;

-- 001 마이그레이션 적용 후 아래 시나리오를 실행합니다
\set ON_ERROR_STOP 0
\pset footer off
-- 시드 (postgres 권한)
insert into auth.users values ('11111111-1111-1111-1111-111111111111'),('22222222-2222-2222-2222-222222222222'),
 ('33333333-3333-3333-3333-333333333333'),('44444444-4444-4444-4444-444444444444');
insert into public.profiles values
 ('11111111-1111-1111-1111-111111111111','student','학생A(만12세)','2014-03-01',now()),
 ('22222222-2222-2222-2222-222222222222','student','학생B(만16세)','2010-03-01',now()),
 ('33333333-3333-3333-3333-333333333333','guardian','보호자G',null,now()),
 ('44444444-4444-4444-4444-444444444444','teacher','강사T',null,now());
insert into public.guardian_links(guardian_id,student_id) values ('33333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111');
insert into public.classes(id,teacher_id,name) values ('aaaaaaaa-0000-0000-0000-000000000001','44444444-4444-4444-4444-444444444444','KOI 중등반');
insert into public.class_members values ('aaaaaaaa-0000-0000-0000-000000000001','22222222-2222-2222-2222-222222222222');
insert into public.concepts(id,slug,name,subject,level) values ('cccccccc-0000-0000-0000-000000000001','nt/fermat','페르마 소정리','math',3);
insert into public.questions(id,concept_id,kind,body,choices,answer,explanation,status,created_by) values
 ('dddddddd-0000-0000-0000-000000000001','cccccccc-0000-0000-0000-000000000001','mcq','7^222 mod 11','["3","5","7","9"]','5','7^10≡1 이므로 7^2=49≡5','published','44444444-4444-4444-4444-444444444444');

set role authenticated;
\echo '== T1 학생A(동의 전) 제출 → 거부 기대'
set request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
select * from public.submit_attempt('dddddddd-0000-0000-0000-000000000001','3',20000);
reset role; update public.guardian_links set consent='approved', consented_at=now(); set role authenticated;
\echo '== T2 동의 후 오답 제출 → false, 복습 D+1'
select is_correct, mastery_score, next_review::date - now()::date as due_in_days from public.submit_attempt('dddddddd-0000-0000-0000-000000000001','3',20000);
\echo '== T3 정답 2회 → 간격 3일, 7일'
select is_correct, mastery_score, next_review::date - now()::date as due_in_days from public.submit_attempt('dddddddd-0000-0000-0000-000000000001','5',15000);
select is_correct, mastery_score, next_review::date - now()::date as due_in_days from public.submit_attempt('dddddddd-0000-0000-0000-000000000001','5',9000);
\echo '== T4 학생이 정답 컬럼 조회 → 권한 거부 기대'
select answer from public.questions;
\echo '== T5 학생이 attempts 직접 삽입 → 거부 기대'
insert into public.attempts(user_id,question_id,answer,is_correct,elapsed_ms) values ('11111111-1111-1111-1111-111111111111','dddddddd-0000-0000-0000-000000000001','x',true,1);
\echo '== T6 학생이 자기 역할을 admin 으로 변경 → 거부 기대'
update public.profiles set role='admin' where id='11111111-1111-1111-1111-111111111111';
\echo '== T7 학생B 제출 후, 학생A 가 볼 수 있는 attempts 사용자 수 (1 기대)'
set request.jwt.claim.sub = '22222222-2222-2222-2222-222222222222';
select is_correct from public.submit_attempt('dddddddd-0000-0000-0000-000000000001','5',30000);
set request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
select count(distinct user_id) as visible_users from public.attempts;
\echo '== T8 보호자G: 자녀A 기록만 보임'
set request.jwt.claim.sub = '33333333-3333-3333-3333-333333333333';
select p.display_name, count(*) from public.attempts a join public.profiles p on p.id=a.user_id group by 1;
select solved, accuracy_pct from public.weekly_report;
\echo '== T9 강사T: 반 학생B 기록만 보임, 본인 문항 정답 조회 가능'
set request.jwt.claim.sub = '44444444-4444-4444-4444-444444444444';
select p.display_name, count(*) from public.attempts a join public.profiles p on p.id=a.user_id group by 1;
select answer from public.get_answer_key('dddddddd-0000-0000-0000-000000000001');
\echo '== T10 학생A 가 정답 키 RPC 호출 → 0행 기대'
set request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
select count(*) from public.get_answer_key('dddddddd-0000-0000-0000-000000000001');
\echo '== T11 anon 은 문항 조회 불가'
set role anon; select count(*) from public.questions;
\echo '== T12 학생A 가 생년월일 변경 시도 → 거부 기대'
set role authenticated; set request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
update public.profiles set birth_date='2000-01-01' where id='11111111-1111-1111-1111-111111111111';
\echo '== T13 학생A 표시 이름 변경 → 성공 (UPDATE 1)'
update public.profiles set display_name='학생A2' where id='11111111-1111-1111-1111-111111111111';
\echo '== T14 보호자가 consent=approved 로 직접 링크 생성 → 거부 기대'
set request.jwt.claim.sub = '33333333-3333-3333-3333-333333333333';
insert into public.guardian_links(guardian_id,student_id,consent) values ('33333333-3333-3333-3333-333333333333','22222222-2222-2222-2222-222222222222','approved');
\echo '== T15 보호자가 남의 자녀(학생B) 프로필 조회 → 0행 기대'
select count(*) from public.profiles where id='22222222-2222-2222-2222-222222222222';
