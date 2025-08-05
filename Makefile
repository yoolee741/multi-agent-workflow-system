# Makefile
include: .env
.PHONY: help check-docker local-run clean rebuild

help: ## Make 설명
	@IFS=$$'\n' ; \
	help_lines=(`fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//'`); \
	for help_line in $${help_lines[@]}; do \
		IFS=$$'#' ; \
		help_split=($$help_line) ; \
		help_command=`echo $${help_split[0]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		help_info=`echo $${help_split[2]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		printf "%-30s %s\n" $$help_command $$help_info ; \
	done

check-docker: ## 도커 체크
	docker --version && docker compose version

local-run: ## 로컬 서버 실행
	docker compose --env-file .env up -d && docker compose logs -f

clean: ## 도커 종료
	docker compose down

rebuild: ## 도커 재빌드
	docker compose build