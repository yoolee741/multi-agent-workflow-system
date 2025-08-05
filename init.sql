SET TIME ZONE 'UTC';

create table if not exists users
(
    user_id serial primary key,
    created_at timestamptz not null default current_timestamp,
    name varchar(255) not null unique,
    auth_token varchar(255) not null
);
comment on table users is '유저 테이블';
comment on column users.user_id is '유저 고유 ID';
comment on column users.created_at is '생성일시';
comment on column users.name is '유저 - 과제용 임시 아이디, 비밀번호 X';
comment on column users.auth_token is '권한 확인용 토큰 (유효기간 만료 시 재발급 로직은 반영X)';

-- 워크플로우 상태 Enum 타입 생성
do $$
begin
    if not exists (select 1 from pg_type where typname = 'status_enum') then
        create type status_enum as Enum ('pending', 'running', 'completed', 'failed');
    end if;
end
$$ language plpgsql;

create table if not exists workflow
(
    workflow_id UUID primary key,
    created_at timestamptz not null default current_timestamp,
    model varchar(255) not null default 'openai/gpt-4o-mini-2024-07-18',
    user_id integer references users (user_id) on delete cascade, 
    started_at timestamptz,
    ended_at timestamptz,
    status status_enum not null default 'running'
);
comment on table workflow is 'workflow 테이블';
comment on column workflow.workflow_id is '워크플로우 고유 ID';
comment on column workflow.created_at is '생성 일시';
comment on column workflow.model is '사용된 모델 이름 (예: openai/gpt-4o)';
comment on column workflow.user_id is 'users 테이블의 외래키 - 해당 워크플로우를 생성한 유저 ID';
comment on column workflow.started_at is '시작 시간';
comment on column workflow.ended_at is '종료 시간';
comment on column workflow.status is 'workflow의 상태 - `pending`, `running`, `completed`, `failed`';

create table if not exists data_collector
(
    data_collector_id serial primary key,
    created_at timestamptz not null default current_timestamp,
    workflow_id UUID references workflow (workflow_id) on delete cascade, -- 데이터의 정합성을 위해 cascade를 넣었지만, 데이터 보관 정책에 따라 변경 가능
    started_at timestamptz,
    ended_at timestamptz,
    status status_enum not null default 'pending',
    response jsonb
);
comment on table data_collector is 'data_collector 테이블';
comment on column data_collector.data_collector_id is '데이터 수집 고유 ID';
comment on column data_collector.created_at is '생성 일시';
comment on column data_collector.workflow_id is '워크플로우 ID';
comment on column data_collector.started_at is '시작 시간';
comment on column data_collector.ended_at is '종료 시간';
comment on column data_collector.status is 'data_collector agent의 상태 - `pending`, `running`, `completed`, `failed`';
comment on column data_collector.response is '반환값 - 성공 응답값 || 실패 에러값';

create table if not exists itinerary_builder
(
    itinerary_builder_id serial primary key,
    created_at timestamptz not null default current_timestamp,
    workflow_id UUID references workflow (workflow_id) on delete cascade, -- 데이터의 정합성을 위해 cascade를 넣었지만, 데이터 보관 정책에 따라 변경 가능
    started_at timestamptz,
    ended_at timestamptz,
    status status_enum not null default 'pending',
    response jsonb
);
comment on table itinerary_builder is 'itinerary_builder 테이블';
comment on column itinerary_builder.itinerary_builder_id is '일정 고유 ID';
comment on column itinerary_builder.created_at is '생성 일시';
comment on column itinerary_builder.workflow_id is '워크플로우 ID';
comment on column itinerary_builder.started_at is '시작 시간';
comment on column itinerary_builder.ended_at is '종료 시간';
comment on column itinerary_builder.status is 'itinerary_builder agent의 상태 - `pending`, `running`, `completed`, `failed`';
comment on column itinerary_builder.response is '반환값 - 성공 응답값 || 실패 에러값';

create table if not exists budget_manager
(
    budget_manager_id serial primary key,
    created_at timestamptz not null default current_timestamp,
    workflow_id UUID references workflow (workflow_id) on delete cascade, -- 데이터의 정합성을 위해 cascade를 넣었지만, 데이터 보관 정책에 따라 변경 가능
    started_at timestamptz,
    ended_at timestamptz,
    status status_enum not null default 'pending',
    response jsonb
);
comment on table budget_manager is 'budget_manager 테이블';
comment on column budget_manager.budget_manager_id is '예산 고유 ID';
comment on column budget_manager.created_at is '생성 일시';
comment on column budget_manager.workflow_id is '워크플로우 ID';
comment on column budget_manager.started_at is '시작 시간';
comment on column budget_manager.ended_at is '종료 시간';
comment on column budget_manager.status is 'budget_manager agent의 상태 - `pending`, `running`, `completed`, `failed`';
comment on column budget_manager.response is '반환값 - 성공 응답값 || 실패 에러값';

create table if not exists report_generator
(
    report_generator_id serial primary key,
    created_at timestamptz not null default current_timestamp,
    workflow_id UUID references workflow (workflow_id) on delete cascade, -- 데이터의 정합성을 위해 cascade를 넣었지만, 데이터 보관 정책에 따라 변경 가능
    started_at timestamptz,
    ended_at timestamptz,
    status status_enum not null default 'pending',
    response jsonb
);
comment on table report_generator is 'report_generator 테이블';
comment on column report_generator.report_generator_id is '리포트 고유 ID';
comment on column report_generator.created_at is '생성 일시';
comment on column report_generator.workflow_id is '워크플로우 ID';
comment on column report_generator.started_at is '시작 시간';
comment on column report_generator.ended_at is '종료 시간';
comment on column report_generator.status is 'report_generator agent의 상태 - `pending`, `running`, `completed`, `failed`';
comment on column report_generator.response is '반환값 - 성공 응답값 || 실패 에러값';

insert into users (name, auth_token)
values
    ('user01', 'token01'),
    ('user02', 'token02'),
    ('user03', 'token03'),
    ('user04', 'token04'),
    ('user05', 'token05');