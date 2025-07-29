# Makefile

.PHONY: help install-dev install-test install-prod test cov clean

help:
	@echo "Usage:"
	@echo "  make install-dev     Install dev dependencies"
	@echo "  make install-test    Install test dependencies"
	@echo "  make install-prod    Install only base deps"
	@echo "  make test            Run tests"
	@echo "  make cov             Run tests with coverage"
	@echo "  make lint            Run ruff for lint checks"
	@echo "  make format          Run black to auto-format code"
	@echo "  make clean           Clean .pyc, __pycache__, .coverage, htmlcov, etc."

install-dev:
	pip install ".[dev]"

install-test:
	pip install ".[test]"

install-prod:
	pip install .

test:
	pytest -v tests/ -W ignore::UserWarning

cov:
	pytest -v -W ignore::UserWarning \
		--cov=utils \
		--cov=storage \
		--cov=schema \
		--cov=security \

lint:
	ruff check .

format:
	black --check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache
