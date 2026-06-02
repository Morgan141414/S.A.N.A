.PHONY: check dev-cycle evaluate evaluate-report evaluate-readiness llm-smoke llm-smoke-ollama-local llm-smoke-ollama-expanded ollama-pull-model ollama-serve-user ollama-user-install quality-report test lint

check:
	./scripts/check.sh

dev-cycle:
	./scripts/dev_cycle.sh

quality-report:
	./scripts/quality_report.sh

evaluate:
	./scripts/evaluate.sh

evaluate-report:
	./scripts/evaluate_report.sh

evaluate-readiness:
	./scripts/evaluate_readiness.sh

llm-smoke:
	./scripts/llm_smoke.sh

llm-smoke-ollama-local:
	./scripts/llm_smoke_ollama_local.sh

llm-smoke-ollama-expanded:
	./scripts/llm_smoke_ollama_expanded.sh

ollama-user-install:
	./scripts/ollama_user_install.sh

ollama-serve-user:
	./scripts/ollama_user_serve.sh

ollama-pull-model:
	./scripts/ollama_pull_model.sh

test:
	cd backend && python -m pytest

lint:
	cd backend && python -m ruff check app tests
