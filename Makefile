.PHONY: check test lint

check:
	./scripts/check.sh

test:
	cd backend && python -m pytest

lint:
	cd backend && python -m ruff check app tests

