.PHONY: check dev-cycle evaluate evaluate-report quality-report test lint

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

test:
	cd backend && python -m pytest

lint:
	cd backend && python -m ruff check app tests
