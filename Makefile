.PHONY: help install dev test lint format clean build up down restart logs db-migrate db-upgrade db-downgrade

# Default target
help:
	@echo "Game Account Marketplace - Available Commands:"
	@echo "================================================"
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install dependencies in venv"
	@echo "  make dev         - Run development server"
	@echo "  make test        - Run tests with coverage"
	@echo "  make lint        - Run linting (flake8, mypy)"
	@echo "  make format      - Format code (black, isort)"
	@echo ""
	@echo "Docker:"
	@echo "  make build       - Build Docker containers"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make logs-app    - View app logs only"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate  - Create new migration"
	@echo "  make db-upgrade  - Apply database migrations"
	@echo "  make db-downgrade - Rollback last migration"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean       - Clean Python cache and build files"
	@echo "  make shell       - Open shell in app container"
	@echo "  make db-shell    - Open PostgreSQL shell"

# Installation
install:
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt

# Development server
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Testing
test:
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# Linting
lint:
	@echo "Running flake8..."
	flake8 app/ tests/
	@echo "Running mypy..."
	mypy app/

# Formatting
format:
	@echo "Running black..."
	black app/ tests/
	@echo "Running isort..."
	isort app/ tests/

# Clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-app:
	docker-compose logs -f app

# Database migrations
db-migrate:
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

# Docker database migrations
docker-db-upgrade:
	docker-compose exec app alembic upgrade head

docker-db-downgrade:
	docker-compose exec app alembic downgrade -1

# Shell access
shell:
	docker-compose exec app bash

db-shell:
	docker-compose exec db psql -U postgres -d game_marketplace

# Flower (Celery monitoring)
flower:
	celery -A app.tasks.celery_app flower --port=5555

# Celery worker
celery-worker:
	celery -A app.tasks.celery_app worker --loglevel=info

# Celery beat
celery-beat:
	celery -A app.tasks.celery_app beat --loglevel=info
