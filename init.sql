SET TIME ZONE 'UTC';

create table if not exists user
(
    user_id serial primary key,
    created_at timestamp not null default current_timestamp,
    name varchar(255) not null unique
);
comment on table user is '유저 테이블';
comment on column user.user_id is '유저 고유 ID';
comment on column user.created_at is '생성일시';
comment on column user.name is '유저 - 과제용 임시 아이디, 비밀번호 X';

create table if not exists workflow
(
    workflow_id UUID primary key,
    created_at timestamp not null default current_timestamp,
    model varchar(255) not null default 'openai/gpt-4o-mini-2024-07-18',
    user_id integer references user (user_id) default null,
    data_collector_id integer references data_collector (data_collector_id) default null,
    itinerary_builder_id integer references itinerary_builder (itinerary_builder_id) default null,
    budget_manager_id integer references budget_manager (budget_manager_id) default null,
    report_generator_id integer references report_generator (report_generator_id) default null,

    is_error boolean default false
);
comment on table workflow is 'workflow 테이블';
comment on column workflow.id is '워크플로우 고유 ID';
comment on column workflow.created_at is '생성 일시';
comment on column workflow.model is '사용된 모델 이름 (예: openai/gpt-4o)';
comment on column workflow.user_id is 'user 테이블의 외래키 - 해당 에이전트를 생성한 유저 ID';
comment on column workflow.data_collector_id is 'data_collector 테이블의 외래키 - data_collector ID';
comment on column workflow.itinerary_builder_id is 'itinerary_builder 테이블의 외래키 - itinerary_builder ID';
comment on column workflow.budget_manager_id is 'budget_manager 테이블의 외래키 - budget_manager ID';
comment on column workflow.report_generator_id is 'report_generator 테이블의 외래키 - report_generator ID';
comment on column workflow.is_error is '에러 여부 플래그 (true 시 에러 발생)';

create table if not exists data_collector
(
    data_collector_id serial primary key,
    created_at timestamp not null default current_timestamp
);
comment on table data_collector is 'data_collector 테이블';
comment on column data_collector.data_collector_id is '데이터 수집 고유 ID';
comment on column data_collector.created_at is '생성 일시';

create table if not exists itinerary_builder
(
    itinerary_builder_id serial primary key,
    created_at timestamp not null default current_timestamp
);
comment on table itinerary_builder is 'itinerary_builder 테이블';
comment on column itinerary_builder.itinerary_builder_id is '일정 고유 ID';
comment on column itinerary_builder.created_at is '생성 일시';

create table if not exists budget_manager
(
    budget_manager_id serial primary key,
    created_at timestamp not null default current_timestamp
);
comment on table budget_manager is 'budget_manager 테이블';
comment on column budget_manager.budget_manager_id is '예산 고유 ID';
comment on column budget_manager.created_at is '생성 일시';

create table if not exists report_generator
(
    report_generator_id serial primary key,
    created_at timestamp not null default current_timestamp
);
comment on table report_generator is 'report_generator 테이블';
comment on column report_generator.report_generator_id is '리포트 고유 ID';
comment on column report_generator.created_at is '생성 일시';

