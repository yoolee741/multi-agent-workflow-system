
## 📦 프로젝트 설정 및 실행 가이드

이 프로젝트를 시작하기 전에 아래 안내에 따라 환경 설정을 진행해주세요. 
<br>
<br>
✅ 시작하기 전 체크리스트
- `.env` 파일 생성
- `API_KEY` 설정
- `make help`로 사용 가능한 명령어 확인 (Makefile이 설치된 경우)
<br>

### 🔧 환경 변수 설정

먼저 `.env` 파일을 생성해야 합니다:

```bash
    cp .env.template .env
```
`.env` 파일에서 API_KEY 값을 반드시 입력해주세요.

<br>

### 🛠️ Makefile 사용법

이 프로젝트는 Makefile을 통해 주요 명령어를 간편하게 실행할 수 있습니다.
도움말은 아래 명령어로 확인할 수 있습니다.
```bash
    make help
```

✅ make check-docker
도커 및 도커 컴포즈가 제대로 설치되어 있는지 확인합니다.

- 만약 Docker Compose가 구버전(docker-compose)인 경우, Makefile 내 명령어를 docker compose → docker-compose로 수정해주세요.

✅ make local-run
로컬 환경에서 애플리케이션을 실행합니다. <br>

** ❗DB 셋팅 및 스키마 생성 완료 후 서버가 켜지도록 로직을 구현하였습니다. DB가 완전히 준비되면 자동으로 연결되고 서버가 시작될 것입니다. 

<br>

### ❗Makefile이 설치되어 있지 않은 경우  
Makefile을 사용하지 않으실 경우, 아래와 같은 명령어를 직접 터미널에 입력해 주세요.

```bash
# 도커 및 도커 컴포즈 설치 확인
docker --version
docker compose version

# 로컬 환경에서 애플리케이션 실행
docker compose --env-file .env up -d
docker compose logs -f
```
<br>

## 📦 프로젝트 테스트
테스트에 사용할 수 있는 사용자 계정과 인증 토큰 목록입니다.
<br>

API 요청 시, 아래의 user_name과 auth_token 값을 참고하여 사용하세요.<br>

```bash
    user_name, auth_token
    ('user01', 'token01'),
    ('user02', 'token02'),
    ('user03', 'token03'),
    ('user04', 'token04'),
    ('user05', 'token05');

```
## 🚀 테스트 방법
1. 워크플로우 시작 API 호출
* Swagger UI에서 쉽게 호출할 수 있습니다. (URL: http://0.0.0.0:8000/docs)

* POST /workflow/start 엔드포인트를 사용해 user_name으로 워크플로우를 시작하세요.
<br>
2. WebSocket 테스트

워크플로우 실행 중 클라이언트가 WebSocket으로 접속 시도할 때 정상적으로 초기 상태를 받을 수 있습니다. <br>

* 진행 중인 워크플로우 접속 화면 예시:
<br>
<img width="1105" height="668" alt="스크린샷 2025-08-06 오전 9 32 19" src="https://github.com/user-attachments/assets/87bca1f6-0941-45a5-9ee7-2bbaafdb3e06" />


워크플로우 종료 후 접속한 경우 초기 상태만 받고 이후 업데이트가 없습니다.

* 종료 후 접속 화면 예시:
<img width="1156" height="674" alt="스크린샷 2025-08-06 오전 8 17 01" src="https://github.com/user-attachments/assets/63ad3471-c3af-4b75-b826-9b150aaa3155" />

3. Postman 사용법
* Postman에서 WebSocket 연결을 테스트할 수 있습니다.

* WebSocket URL 예시: ws://0.0.0.0:8000/ws/{workflow_id}?auth_token={token}

* workflow_id와 auth_token은 워크플로우 시작 시 받은 값을 사용하세요.

### ❗DB GUI 툴(ex. DBeaver etc.)을 사용하여 연결하는 경우, 아래의 정보를 사용하여 연결하세요.<br>
* host=localhost<br>
* port=5433
<br>

## 🗂️ DB ERD
DB ERD는 아래의 링크를 참고해주세요.
<br>

🔗 https://drawsql.app/teams/mnl/diagrams/multi-agent-workflow-system

<br>

## 📁 프로젝트 구조
```bash
MULTI-AGENT-WORKFLOW-SYSTEM
├── app
│ ├── agents # 각 에이전트별 로직 구현
│ │ ├── init.py # agents 패키지 초기화
│ │ ├── base.py # 에이전트 공통 베이스 클래스
│ │ ├── budget_manager.py # 예산 관리 에이전트
│ │ ├── data_collector.py # 데이터 수집 에이전트
│ │ ├── itinerary_builder.py # 여행 일정 구성 에이전트
│ │ ├── report_generator.py # 보고서 생성 에이전트
│ │ └── utils.py # 에이전트 관련 유틸 함수들
│ ├── api # Rest API 및 WebSocket 핸들러
│ │ ├── init.py # api 패키지 초기화
│ │ ├── websocket.py # WebSocket 연결 및 관리 함수
│ │ └── workflow.py # 워크플로우 관련 REST API 함수
│ ├── db # 데이터베이스 연결 및 유틸
│ │ ├── database.py # 데이터베이스 커넥션 풀 관리 함수 및 각 기능에 필요한 DB 작업 함수
│ │ ├── utils.py # DB 관련 유틸 함수들
│ │ └── main.py # 진입점
├── .env.template # 환경변수 템플릿 파일
├── .gitignore # Git 무시할 파일 및 폴더 설정
├── docker-compose.yaml # Docker Compose 설정 파일
├── Dockerfile # Docker 이미지 빌드 설정
├── init.sql # DB 초기화 SQL 스크립트
├── Makefile # 자주 쓰는 명령어 모음
├── readme.md # 프로젝트 설명 및 문서
└── requirements.txt # Python 의존성 목록
```
