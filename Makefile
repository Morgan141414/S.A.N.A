.PHONY: check dev-cycle quality-report test lint

check:
	./scripts/check.sh

dev-cycle:
	./scripts/dev_cycle.sh

quality-report:
	./scripts/quality_report.sh

test:
	cd backend && python -m pytest

lint:
	cd backend && python -m ruff check app tests
