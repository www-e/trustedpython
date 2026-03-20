# Quick Commands Reference

## Setup (One Time)
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate


# Install dependencies
pip install -r requirements.txt
```

## Development
```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/test_health.py
```

## Database (Alembic)
```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

## URLs
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Root: http://localhost:8000
- Health: http://localhost:8000/api/v1/health

## Environment Setup
1. Sign up for Neon (PostgreSQL): https://neon.tech
2. Sign up for Upstash (Redis): https://upstash.com
3. Update `.env` with your credentials
