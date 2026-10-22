.PHONY: help install dev test lint typecheck format clean docker-up docker-down logs

# Help target
help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies with uv"
	@echo "  dev        - Start development environment with docker-compose"
	@echo "  test       - Run pytest"
	@echo "  lint       - Run ruff check"
	@echo "  typecheck  - Run mypy"
	@echo "  format     - Format code with ruff"
	@echo "  clean      - Remove temporary files"
	@echo "  docker-up  - Start Docker containers"
	@echo "  docker-down- Stop Docker containers"
	@echo "  logs       - Follow Docker container logs"

# Install dependencies
install:
	uv sync

# Start development environment (PostgreSQL + services)
dev: docker-up
	@echo "Development environment started. Check containers with 'docker ps'"

# Run tests
test:
	uv run pytest

# Lint code
lint:
	uv run ruff check .

# Type check
typecheck:
	uv run mypy .

# Format code
format:
	uv run ruff check --fix .
	uv run ruff format .

# Clean temporary files
clean:
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__
	rm -rf .coverage htmlcov .ruff_cache .mypy_cache
	docker-compose down -v 2>/dev/null || true

# Docker compose targets
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

logs:
	docker-compose logs -f

# Default target
default: help