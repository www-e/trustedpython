# Test Suite Documentation

## Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── api/
│   └── v1/
│       ├── test_main_endpoints.py   # Root, health, docs endpoints
│       ├── test_auth_routes.py      # Authentication endpoints
│       ├── test_all_routes.py       # Home, sell, buy, chat, notifications, profile, security, admin
│       ├── test_chat_routes.py      # Chat-specific tests
│       └── test_sell_routes.py      # Sell-specific tests
├── core/
│   └── test_config.py               # Config, security, JWT tests
├── models/
│   └── test_models.py               # All SQLAlchemy model tests
├── schemas/
│   └── test_schemas.py              # All Pydantic schema tests
├── services/
│   └── test_services.py             # Service layer tests
├── utils/
│   └── test_utils.py                # Utility module tests
├── tasks/                           # Celery task tests (future)
├── test_main.py                     # Legacy tests
├── test_buy_flow.py                 # Legacy buy flow tests
└── test_home_feed.py                # Legacy home feed tests
```

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
```

### Run Specific Module
```bash
pytest tests/core/ -v                 # Core tests only
pytest tests/api/v1/test_auth_routes.py -v  # Auth tests only
pytest tests/models/ -v               # Model tests only
```

### Run with Detailed Output
```bash
pytest tests/ -vv --tb=long
```

### Run Tests Matching Pattern
```bash
pytest tests/ -k "test_user" -v       # Tests containing "test_user"
pytest tests/ -k "auth" -v            # Tests containing "auth"
```

## Test Categories

### 1. **Unit Tests** (Fast, Isolated)
- `core/test_config.py` - Settings, password hashing, JWT
- `models/test_models.py` - Model creation, defaults, relationships
- `schemas/test_schemas.py` - Schema validation, serialization

### 2. **Integration Tests** (API Endpoints)
- `api/v1/test_main_endpoints.py` - Root, health, docs
- `api/v1/test_auth_routes.py` - Register, login, logout
- `api/v1/test_all_routes.py` - All other endpoints

### 3. **Service Tests** (Business Logic)
- `services/test_services.py` - Service initialization, methods

### 4. **Utility Tests** (Helper Functions)
- `utils/test_utils.py` - Storage, Redis pub/sub, rate limiting

## Fixtures

### Database Fixtures
- `mock_db_session` - Mock database session
- `patch_get_db` - Override get_db dependency

### Authentication Fixtures
- `mock_user` - Mock user data
- `mock_user_register_data` - Registration payload
- `auth_token` - Valid JWT token
- `auth_headers` - Authorization headers

### Utility Fixtures
- `mock_redis` - Mock Redis client
- `mock_storage` - Mock storage service
- `client` - HTTPX async client

## Coverage Goals

- **Core Modules**: 100% (config, security, database, redis)
- **Models**: 100% (all models, relationships, defaults)
- **Schemas**: 100% (validation, serialization)
- **API Endpoints**: 90%+ (all routes respond correctly)
- **Services**: 80%+ (initialization, key methods)
- **Utilities**: 70%+ (storage, redis, rate limiting)

## Test Principles

1. **Isolation**: Each test is independent and isolated
2. **Mocking**: External dependencies (DB, Redis, Storage) are mocked
3. **Validation**: Tests validate both success and error cases
4. **Coverage**: Tests cover happy paths and edge cases
5. **Naming**: Test names are descriptive (test_what_it_does)

## Writing New Tests

### Example: Testing a New Endpoint
```python
async def test_new_endpoint_returns_200(self, client: AsyncClient):
    """Test new endpoint returns 200."""
    response = await client.get("/api/v1/new-endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### Example: Testing a Service Method
```python
async def test_service_method(self, mock_db_session):
    """Test service method works correctly."""
    service = MyService(mock_db_session)
    result = await service.my_method()
    assert result is not None
```

### Example: Testing a Schema
```python
def test_schema_validation(self):
    """Test schema validates correctly."""
    data = MySchema(field1="value", field2=123)
    assert data.field1 == "value"
    
    with pytest.raises(ValidationError):
        MySchema()  # Missing required fields
```
