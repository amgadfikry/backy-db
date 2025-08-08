# Makefile
MAKEFLAGS += --no-print-directory

# Declare the targets for the Makefile
.PHONY: help install-dev install-test install-prod start-databases stop-databases test full-test cov lint format clean full-test-cov

# Define the help target to provide usage instructions
help:
	@echo "Usage:"
	@echo "  make install-dev     Install dev dependencies"
	@echo "  make install-test    Install test dependencies"
	@echo "  make install-prod    Install only base deps"
	@echo "  make start-databases Start the databases using docker-compose"
	@echo "  make stop-databases  Stop the databases"
	@echo "  make test            Run tests"
	@echo "  make full-test       Run tests with databases started and stopped automatically"
	@echo "  make full-test-cov   Run tests with coverage and databases started and stopped automatically"
	@echo "  make cov             Run tests with coverage"
	@echo "  make lint            Run ruff for lint checks"
	@echo "  make format          Run black to auto-format code"
	@echo "  make clean           Clean .pyc, __pycache__, .coverage, htmlcov, etc."

# Define commands for installing dependencies
install-dev:
	pip install ".[dev]"

install-prod:
	pip install .

# Define commands for starting and stopping databases using docker-compose
start-databases:
	docker compose -f tests/docker-compose.yml up -d
	@echo "Waiting for all services to become healthy..."
	@containers="$$(docker compose -f tests/docker-compose.yml ps -q)"; \
	for container in $$containers; do \
		name=$$(docker inspect --format '{{.Name}}' $$container | cut -c2-); \
		echo "🕒 Waiting for $$name..."; \
		until [ "$$(docker inspect --format '{{.State.Health.Status}}' $$container 2>/dev/null || echo unknown)" = "healthy" ]; do \
			sleep 2; \
		done; \
		echo "$$name is healthy!"; \
	done
	@echo "✅ All services are healthy."

stop-databases:
	docker compose -f tests/docker-compose.yml down --volumes --remove-orphans

# Define commands for running tests and coverage
test:
	pytest -v tests/ -W ignore::DeprecationWarning \

full-test:
	@make start-databases
	@trap 'make stop-databases' EXIT; make test

cov:
	pytest -v tests/ -W ignore::DeprecationWarning \
		--cov=. \
		--cov-config=.coveragerc \
		--cov-report=term-missing \

full-test-cov:
	@make start-databases
	@trap 'make stop-databases' EXIT; make cov

# Define commands for linting, formatting, and cleaning up
lint:
	ruff check .

format:
	black .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache
