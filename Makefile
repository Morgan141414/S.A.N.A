.PHONY: check dev-cycle evaluate evaluate-report evaluate-readiness llm-smoke quality-report test lint

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

test:
	cd backend && python -m pytest

lint:
	cd backend && python -m ruff check app tests
