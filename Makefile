.PHONY: help install dev test lint format security clean docker docker-up docker-down logs

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose
SERVER_DIR := server
VENV := venv

help:
	@echo "=================================="
	@echo "DECO Chat Agent - Makefile"
	@echo "=================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install dependencies"
	@echo "  make install-dev      Install dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Run development server"
	@echo "  make run              Run server (production-like)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-security    Run security tests only"
	@echo "  make coverage         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters (flake8, mypy)"
	@echo "  make format           Auto-format code (black, isort)"
	@echo "  make format-check     Check format without changes"
	@echo ""
	@echo "Security:"
	@echo "  make security         Run all security checks"
	@echo "  make bandit           Run Bandit security scan"
	@echo "  make safety           Check dependencies for vulnerabilities"
	@echo ""
	@echo "Pre-commit:"
	@echo "  make pre-commit-install  Install pre-commit hooks"
	@echo "  make pre-commit-run      Run all pre-commit checks"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker images"
	@echo "  make docker-up        Start containers (docker-compose)"
	@echo "  make docker-down      Stop containers"
	@echo "  make docker-logs      Show container logs"
	@echo "  make docker-rebuild   Rebuild without cache"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate       Run database migrations"
	@echo "  make db-seed          Seed database with sample data"
	@echo ""
	@echo "Clean:"
	@echo "  make clean            Remove build artifacts and cache"
	@echo "  make clean-all        Remove everything (venv, .cache, etc)"
	@echo ""

# ============================================
# SETUP & INSTALLATION
# ============================================

install:
	@echo "Installing dependencies..."
	cd $(SERVER_DIR) && $(PIP) install -r requirements.txt

install-dev:
	@echo "Installing dev dependencies..."
	cd $(SERVER_DIR) && $(PIP) install -r requirements.txt && $(PIP) install -r requirements-dev.txt

venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Run: source venv/bin/activate"

# ============================================
# DEVELOPMENT
# ============================================

dev:
	@echo "Starting development server..."
	cd $(SERVER_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run:
	@echo "Starting server..."
	cd $(SERVER_DIR) && uvicorn app.main:app --host 0.0.0.0 --port 8000

# ============================================
# TESTING
# ============================================

test:
	@echo "Running all tests..."
	cd $(SERVER_DIR) && pytest app/tests/ -v --tb=short

test-unit:
	@echo "Running unit tests..."
	cd $(SERVER_DIR) && pytest app/tests/unit/ -v --tb=short

test-integration:
	@echo "Running integration tests..."
	cd $(SERVER_DIR) && pytest app/tests/integration/ -v --tb=short

test-security:
	@echo "Running security tests..."
	cd $(SERVER_DIR) && pytest app/tests/security/ -v --tb=short

coverage:
	@echo "Running tests with coverage..."
	cd $(SERVER_DIR) && pytest app/tests/ --cov=app --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated: $(SERVER_DIR)/htmlcov/index.html"

# ============================================
# CODE QUALITY
# ============================================

lint:
	@echo "Running linters..."
	cd $(SERVER_DIR) && flake8 app/ --max-line-length=100 --show-source
	cd $(SERVER_DIR) && mypy app/ --ignore-missing-imports || true

format:
	@echo "Auto-formatting code..."
	cd $(SERVER_DIR) && black app/ --line-length=100
	cd $(SERVER_DIR) && isort app/ --profile=black --line-length=100

format-check:
	@echo "Checking code format..."
	cd $(SERVER_DIR) && black --check app/ --line-length=100
	cd $(SERVER_DIR) && isort --check-only app/ --profile=black

# ============================================
# SECURITY
# ============================================

security: bandit safety
	@echo "Security checks completed"

bandit:
	@echo "Running Bandit security scan..."
	cd $(SERVER_DIR) && bandit -r app/ -ll

safety:
	@echo "Checking dependencies for vulnerabilities..."
	cd $(SERVER_DIR) && safety check --json || safety check

# ============================================
# PRE-COMMIT HOOKS
# ============================================

pre-commit-install:
	@echo "Installing pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "Pre-commit hooks installed"

pre-commit-run:
	@echo "Running pre-commit checks on all files..."
	pre-commit run --all-files

pre-commit-update:
	@echo "Updating pre-commit hooks..."
	pre-commit autoupdate

# ============================================
# DOCKER
# ============================================

docker-build:
	@echo "Building Docker images..."
	$(DOCKER_COMPOSE) build

docker-up:
	@echo "Starting containers..."
	$(DOCKER_COMPOSE) up -d
	@echo "Containers started. Check with: docker-compose ps"

docker-down:
	@echo "Stopping containers..."
	$(DOCKER_COMPOSE) down

docker-logs:
	@echo "Showing container logs..."
	$(DOCKER_COMPOSE) logs -f

docker-rebuild:
	@echo "Rebuilding Docker images (no cache)..."
	$(DOCKER_COMPOSE) build --no-cache

docker-ps:
	@echo "Docker container status:"
	docker-compose ps

docker-exec-bash:
	@echo "Opening bash in server container..."
	docker-compose exec server bash

# ============================================
# DATABASE
# ============================================

db-migrate:
	@echo "Running database migrations..."
	cd $(SERVER_DIR) && alembic upgrade head

db-downgrade:
	@echo "Rolling back database migration..."
	cd $(SERVER_DIR) && alembic downgrade -1

db-seed:
	@echo "Seeding database..."
	cd $(SERVER_DIR) && python -m app.scripts.seed_db

db-reset:
	@echo "Resetting database..."
	cd $(SERVER_DIR) && alembic downgrade base && alembic upgrade head

# ============================================
# CLEAN
# ============================================

clean:
	@echo "Cleaning build artifacts..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	find . -type d -name '.mypy_cache' -delete
	find . -type d -name '*.egg-info' -delete
	rm -rf build/ dist/ .coverage htmlcov/
	@echo "Cleaned"

clean-all: clean
	@echo "Removing virtual environment and caches..."
	rm -rf $(VENV)
	rm -rf .env .env.local
	rm -rf .vscode .idea
	@echo "Full clean complete"

# ============================================
# QUICK SHORTCUTS
# ============================================

# Quick test + lint before push
check: format lint test
	@echo "✅ All checks passed!"

# Full CI locally
ci: clean install-dev format lint test coverage security
	@echo "✅ Full CI pipeline completed!"

# Setup dev environment
setup: venv install-dev pre-commit-install
	@echo "✅ Dev environment ready!"

# Status check
status: docker-ps
	@echo ""
	@echo "Server health:"
	@curl -s http://localhost:9000/health | python -m json.tool || echo "Server not running"
