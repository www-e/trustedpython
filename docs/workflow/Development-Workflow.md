# Development Workflow

## 🛠️ Development Environment Setup

### Prerequisites

```bash
# Install Docker Desktop
# https://www.docker.com/products/docker-desktop

# Install Git
# https://git-scm.com/downloads

# Install Python 3.12+
# https://www.python.org/downloads/

# Clone repository
git clone <your-repo-url>
cd marketplace-backend
```

### Local Development with Docker Compose

```bash
# Copy environment template
cp .env.example .env.dev

# Edit .env.dev with your local settings
nano .env.dev

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## 🏗️ Project Structure

### Layer-by-Layer Development Order

```
Phase 1: Foundation (Week 1)
├── Core configuration (settings, security)
├── Database models (User, Listing, Deal, Chat)
├── Base repository pattern
└── Authentication system

Phase 2: Core Features (Week 2-3)
├── User management
├── Listing CRUD
├── Category management
├── Search and filtering

Phase 3: Deal System (Week 3-4)
├── Deal workflow
├── Mediator assignment
├── Chat room creation
└── Real-time messaging

Phase 4: Advanced Features (Week 4-5)
├── File uploads (R2)
├── Push notifications (OneSignal)
├── Mediator tiers
└── Admin dashboard

Phase 5: Testing & Polish (Week 5-6)
├── Integration tests
├── E2E tests
├── Performance optimization
└── Security hardening

Phase 6: Deployment (Week 6-7)
├── Contabo setup
├── CI/CD pipeline
├── Production deployment
└── Monitoring setup
```

---

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── conftest.py              # Pytest fixtures
├── unit/                    # Unit tests (60%)
│   ├── services/
│   │   ├── test_auth_service.py
│   │   ├── test_listing_service.py
│   │   └── test_deal_service.py
│   └── repositories/
│       └── test_listing_repository.py
├── integration/             # Integration tests (30%)
│   ├── api/
│   │   ├── test_auth_endpoints.py
│   │   └── test_listing_endpoints.py
│   └── websocket/
│       └── test_chat_websocket.py
└── e2e/                     # End-to-end tests (10%)
    └── test_deal_flow.py
```

### Running Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest tests/unit/services/test_auth_service.py

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Run only unit tests
docker-compose exec backend pytest tests/unit/

# Run only integration tests
docker-compose exec backend pytest tests/integration/

# Run with verbose output
docker-compose exec backend pytest -v

# Run specific test
docker-compose exec backend pytest tests/unit/services/test_auth_service.py::test_login_success
```

### Fixtures (conftest.py)

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.base import Base
from app.core.security import create_password_hash, create_jwt_token

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Create test client with database override"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user"""
    from app.models.user import User, UserRole

    user = User(
        phone="+201234567890",
        hashed_password=create_password_hash("testpass123"),
        username="testuser",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
def auth_token(test_user: User):
    """Generate auth token for test user"""
    return create_jwt_token({"sub": str(test_user.id), "role": test_user.role})
```

### Test Example

```python
# tests/unit/services/test_auth_service.py

import pytest
from app.services.auth_service import AuthService
from app.core.exceptions import InvalidCredentialsError

@pytest.mark.asyncio
async def test_login_success(db_session, test_user):
    """Test successful login"""
    service = AuthService(db_session)

    result = await service.login(
        phone="+201234567890",
        password="testpass123"
    )

    assert result.access_token is not None
    assert result.refresh_token is not None
    assert result.user_id == test_user.id

@pytest.mark.asyncio
async def test_login_invalid_password(db_session, test_user):
    """Test login with invalid password"""
    service = AuthService(db_session)

    with pytest.raises(InvalidCredentialsError):
        await service.login(
            phone="+201234567890",
            password="wrongpassword"
        )
```

---

## 📝 Code Style & Quality

### Python Code Style

```bash
# Format code with Black
docker-compose exec backend black app/

# Sort imports with isort
docker-compose exec backend isort app/

# Lint with Ruff
docker-compose exec backend ruff check app/

# Type checking with mypy
docker-compose exec backend mypy app/

# Run all quality checks
docker-compose exec backend bash -c "black app/ && isort app/ && ruff check app/ && mypy app/"
```

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.0.272
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic
          - types-redis
```

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 🔄 Git Workflow

### Trunk-Based Development

```bash
# Always work on main branch
git checkout main

# Pull latest changes
git pull origin main

# Create feature branch (for complex features)
git checkout -b feature/listing-management

# Make changes
git add .
git commit -m "feat: add listing CRUD operations"

# Push to feature branch
git push origin feature/listing-management

# Create PR (if needed for review)
# After approval, merge to main
git checkout main
git merge feature/listing-management

# Delete feature branch
git branch -d feature/listing-management
```

### Commit Message Format

```
feat: add user registration endpoint
fix: resolve WebSocket authentication issue
docs: update API documentation
refactor: simplify repository pattern
test: add integration tests for deal flow
chore: upgrade dependencies
perf: optimize database queries
```

### Branch Naming

```
feature/     # New features
bugfix/      # Bug fixes
hotfix/      # Production hotfixes
refactor/    # Code refactoring
test/        # Test updates
docs/        # Documentation updates
```

---

## 🐛 Debugging

### VS Code Configuration

```json
// .vscode/launch.json

{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload"
      ],
      "envFile": "${workspaceFolder}/.env.dev",
      "console": "integratedTerminal"
    }
  ]
}
```

### Debugging Tests

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb (better)
import ipdb; ipdb.set_trace()

# Run tests with debugger
docker-compose exec backend pytest --pdb
```

### Logging

```python
# Use loguru for debugging
from loguru import logger

logger.debug("Detailed debug info")
logger.info("General info")
logger.warning("Warning message")
logger.error("Error occurred")

# View logs in real-time
docker-compose logs -f backend

# Follow specific service
docker-compose logs -f celery_worker
```

---

## 🚀 Feature Development Checklist

### Before Starting

- [ ] Create feature branch (if complex)
- [ ] Read relevant documentation
- [ ] Review existing code patterns
- [ ] Write test cases first (TDD)

### During Development

- [ ] Follow strict SOC (Router → Service → Repository)
- [ ] Write Pydantic schemas for validation
- [ ] Add type hints
- [ ] Write docstrings
- [ ] Test manually with Swagger UI

### Before Committing

- [ ] Run tests: `pytest`
- [ ] Check code quality: `black`, `isort`, `ruff`
- [ ] Update API documentation (if needed)
- [ ] Update migration files (if DB changes)
- [ ] Test with Flutter frontend (if applicable)

### After Merge

- [ ] Deploy to staging/production
- [ ] Monitor logs for errors
- [ ] Verify with frontend team

---

## 📚 Useful Commands

### Database

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Add listings table"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1

# View migration history
docker-compose exec backend alembic history

# Reset database (dev only)
docker-compose exec backend alembic downgrade base
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Docker

```bash
# Build images
docker-compose build

# Rebuild specific service
docker-compose build backend

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Execute command in container
docker-compose exec backend bash

# Restart service
docker-compose restart backend

# Remove volumes (deletes data!)
docker-compose down -v
```

### Redis

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# View all keys
KEYS *

# Get value
GET key_name

# Set value
SET key_name "value"

# Delete key
DEL key_name

# Flush database
FLUSHDB

# Monitor commands
MONITOR
```

---

## 🎯 Development Best Practices

### DO's

✅ Always follow Router → Service → Repository pattern
✅ Write tests for critical business logic
✅ Use type hints everywhere
✅ Add docstrings to services and repositories
✅ Validate input with Pydantic at router layer
✅ Use async/await for I/O operations
✅ Handle exceptions gracefully
✅ Log important events
✅ Keep functions small and focused
✅ Review code before committing

### DON'Ts

❌ Don't put DB logic in routers
❌ Don't skip layers for "simplicity"
❌ Don't hardcode values (use config)
❌ Don't commit secrets or API keys
❌ Don't ignore failing tests
❌ Don't push directly to main without testing
❌ Don't use synchronous code in async functions
❌ Don't swallow exceptions silently
❌ Don't copy-paste code (create utilities)
❌ Don't skip writing documentation

---

## 📚 Related Documentation

- [Architecture Design](../02-Architecture-Design.md) - System architecture patterns
- [API Structure](./API-Structure.md) - API endpoints and contracts
- [Deployment Guide](../deployment/Deployment-Guide.md) - Production deployment

---

**Last Updated**: 2026-03-14
**Version**: 0.1.0
