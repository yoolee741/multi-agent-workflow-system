
## 📦 프로젝트 설정 및 실행 가이드

이 프로젝트를 시작하기 전에 아래 안내에 따라 환경 설정을 진행해주세요.
✅ 시작하기 전 체크리스트
- `.env` 파일 생성
- `API_KEY` 설정
- `make help`로 사용 가능한 명령어 확인 (Makefile이 설치된 경우)

---

### 🔧 환경 변수 설정

먼저 `.env` 파일을 생성해야 합니다:

```bash
    cp .env.template .env
```
`.env` 파일에서 API_KEY 값을 반드시 입력해주세요.

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
로컬 환경에서 애플리케이션을 실행합니다.


❗ Makefile이 설치되어 있지 않은 경우  
Makefile을 사용하지 않으실 경우, 아래와 같은 명령어를 직접 터미널에 입력해 주세요.

```bash
# 도커 및 도커 컴포즈 설치 확인
docker --version
docker compose version

# 로컬 환경에서 애플리케이션 실행
docker compose --env-file .env up -d
docker compose logs -f
---

📦 프로젝트 테스트

---

🗂️ DB ERD
DB ERD는 아래의 링크를 참고해주세요.
🔗 https://drawsql.app/teams/mnl/diagrams/multi-agent-workflow-system

