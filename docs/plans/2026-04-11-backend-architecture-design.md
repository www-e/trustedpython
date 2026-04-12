# Backend Architecture Design - Game Account Marketplace

> **Date:** 2026-04-11
> **Status:** ✅ Approved
> **Architecture:** Modular Monolith with FastAPI
> **Deployment:** Contabo VPS with Docker Compose

---

## Executive Summary

Design and implementation of a **Python FastAPI backend** for a Game Account Marketplace platform. The backend provides 115 REST/WebSocket endpoints supporting a P2P marketplace with mediator-facilitated transactions.

**Key Business Model:** Social Escrow & Lead Generation - Revenue from mediator subscriptions, not payment processing fees.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Data Models & Database](#4-data-models--database)
5. [API Structure & Schemas](#5-api-structure--schemas)
6. [Services Layer](#6-services-layer)
7. [Real-time Features](#7-real-time-features)
8. [Background Tasks](#8-background-tasks)
9. [File Storage](#9-file-storage)
10. [Security](#10-security)
11. [Testing Strategy](#11-testing-strategy)
12. [Deployment](#12-deployment)
13. [Implementation Phases](#13-implementation-phases)

---

## 1. Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Docker Compose                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Nginx      │  │   FastAPI    │  │   Celery     │      │
│  │  (Reverse    │──│   (App)      │  │   (Worker)   │      │
│  │   Proxy)     │  │   Async      │  │              │      │
│  └──────────────┘  └──────┬───────┘  └──────┬───────┘      │
│                           │                  │              │
│  ┌──────────────┐  ┌──────▼───────┐  ┌──────▼───────┐      │
│  │   MinIO      │  │  PostgreSQL  │  │    Redis     │      │
│  │  (S3 Storage)│  │ (Database)   │  │ (Cache/Queue)│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Pattern: **Modular Monolith**

Single FastAPI application organized into isolated modules. Each business domain (auth, buy, sell, chat) has its own folder with routes, services, models, and schemas.

**Why Modular Monolith?**
- ✅ Simpler deployment (single Docker container)
- ✅ Faster development (no inter-service communication)
- ✅ Easy debugging (single codebase)
- ✅ Perfect for MVP (can split into microservices later)
- ✅ Transactional integrity (single DB transaction)
- ✅ Ideal for solo developer

**When to scale out:** Extract high-traffic modules (chat, marketplace) into separate services when needed.

---

## 2. Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | FastAPI | 0.104+ | High-performance async API |
| **Database** | PostgreSQL | 15+ | Primary data store |
| **Cache/Queue** | Redis | 7+ | Cache, sessions, Celery broker |
| **ORM** | SQLAlchemy | 2.0 (async) | Database async ORM |
| **Migrations** | Alembic | Latest | Database migrations |
| **Auth** | JWT + bcrypt | Latest | Token-based authentication |
| **WebSocket** | FastAPI WebSocket | Native | Real-time chat & notifications |
| **File Storage** | MinIO | Latest | S3-compatible object storage |
| **Task Queue** | Celery | 5.3+ | Background jobs |
| **Validation** | Pydantic | V2 | Request/response validation |
| **Testing** | pytest + pytest-asyncio | Latest | Essential tests only |
| **Docs** | FastAPI auto-Swagger | Built-in | Interactive API docs |
| **Container** | Docker + Docker Compose | Latest | Container orchestration |
| **Reverse Proxy** | Nginx | Latest | Load balancing & static files |

### Python Packages

```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.13.0

# Auth & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Storage & Tasks
celery[redis]==5.3.4
redis==5.0.1
boto3==1.29.0
pillow==10.1.0

# Validation & Utils
pydantic==2.5.0
pydantic-settings==2.1.0
email-validator==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

---

## 3. Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   │
│   ├── api/                        # API Routes (15 modules)
│   │   ├── __init__.py
│   │   ├── deps.py                 # Route dependencies (auth, pagination)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth/               # 8 endpoints
│   │       │   ├── routes.py
│   │       │   ├── schemas.py
│   │       │   └── service.py
│   │       ├── buy/                # 15 endpoints
│   │       │   ├── routes.py
│   │       │   ├── schemas.py
│   │       │   └── service.py
│   │       ├── sell/               # 9 endpoints
│   │       ├── chat/               # 9 endpoints
│   │       ├── profile/            # 13 endpoints
│   │       ├── home/               # 8 endpoints
│   │       ├── notifications/      # 9 endpoints
│   │       ├── admin/              # 40 endpoints
│   │       ├── security/           # 11 endpoints
│   │       └── moderation/         # 11 endpoints
│   │
│   ├── core/                       # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic settings
│   │   ├── security.py             # JWT, password hashing
│   │   ├── exceptions.py           # Custom exceptions
│   │   ├── middleware.py           # Custom middleware
│   │   └── constants.py            # Constants (enums, defaults)
│   │
│   ├── models/                     # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py                 # Base model class
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── deal.py
│   │   ├── chat.py
│   │   ├── notification.py
│   │   ├── mediator.py
│   │   └── ...
│   │
│   ├── schemas/                    # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── common.py               # Common schemas (pagination, etc)
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── deal.py
│   │   ├── chat.py
│   │   └── ...
│   │
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── deal_service.py
│   │   ├── chat_service.py
│   │   ├── notification_service.py
│   │   └── ...
│   │
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── email_tasks.py
│   │   ├── notification_tasks.py
│   │   └── cleanup_tasks.py
│   │
│   ├── utils/                      # Helper functions
│   │   ├── __init__.py
│   │   ├── s3.py                   # MinIO/S3 operations
│   │   ├── image.py                # Image processing
│   │   └── helpers.py
│   │
│   └── db/                         # Database
│       ├── __init__.py
│       ├── session.py              # DB session management
│       └── migrations/             # Alembic migrations
│
├── tests/                          # Essential tests
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_auth/
│   ├── test_buy/
│   ├── test_deals/
│   └── test_chat/
│
├── alembic.ini                     # Alembic config
├── docker-compose.yml              # Docker services
├── Dockerfile                      # App container
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Project metadata
├── .env.example                    # Environment variables template
└── README.md                       # Project documentation
```

### Module Breakdown (115 Endpoints)

| Module | Endpoints | Priority | Complexity |
|--------|-----------|----------|------------|
| Auth | 8 | P0 | Medium |
| Buy Flow | 15 | P0 | High |
| Sell Flow | 9 | P0 | High |
| Chat | 9 | P0 | High (WebSocket) |
| Profile | 13 | P0 | Medium |
| Home Feed | 8 | P1 | Low |
| Notifications | 9 | P1 | Medium |
| Admin | 40 | P1 | High |
| Security | 11 | P1 | Medium |
| Moderation | 11 | P2 | Medium |
| Push Notifications | 7 | P2 | Low |
| **Total** | **~140** | - | - |

---

## 4. Data Models & Database

### Database Strategy

**SQLAlchemy 2.0 Async** with:
- **DeclarativeBase** for models
- **AsyncSession** for database operations
- **select()** construct (not legacy ORM)
- **UUID** primary keys

### Core Models Structure

```python
# app/models/base.py
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import UUID
from datetime import datetime

class Base(DeclarativeBase):
    """Base model for all SQLAlchemy models"""
    pass

class TimestampMixin:
    """Add created_at, updated_at to models"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

### Database Tables (22 Tables)

All tables matching the API docs schema:

1. **users** - Core user authentication
2. **user_profiles** - Extended user info
3. **sessions** - Auth sessions/tokens
4. **accounts** - Game accounts for sale
5. **account_images** - Account images
6. **account_features** - Account features/badges
7. **listings** - User-created listings
8. **deals** - Transactions
9. **payments** - Payment records
10. **mediators** - Mediator profiles
11. **mediator_badges** - Mediator achievements
12. **chat_rooms** - Chat conversations
13. **chat_participants** - Room memberships
14. **messages** - Chat messages
15. **message_attachments** - Message files
16. **notifications** - User notifications
17. **notification_prefs** - User notification settings
18. **games** - Supported games
19. **categories** - Listing categories
20. **reviews** - User reviews
21. **promo_banners** - Marketing banners
22. **faq_items** - FAQ content

### Database Connection

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import async_sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Redis Connection

```python
# app/db/redis.py
import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

async def get_redis() -> redis.Redis:
    """Dependency for Redis client"""
    return redis_client
```

---

## 5. API Structure & Schemas

### Standard Response Format

All API responses follow this structure:

```python
# app/schemas/common.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response format"""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[dict] = None
    pagination: Optional["PaginationSchema"] = None

class PaginationSchema(BaseModel):
    """Pagination metadata"""
    page: int
    limit: int
    total: int
    total_pages: int
```

### Pydantic Schemas

Each module has its own schemas file:

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?\d{10,15}$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    phone: str
    display_name: str | None
    avatar_url: str | None
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

### Route Structure

Each module follows this pattern:

```python
# app/api/v1/auth/routes.py
from fastapi import APIRouter, Depends, status
from app.schemas.user import UserCreate, UserResponse
from app.schemas.common import APIResponse
from app.api.deps import get_current_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends()
) -> APIResponse[UserResponse]:
    """Register new user account"""
    user = await auth_service.register(user_data)
    return APIResponse(success=True, data=user)

@router.post("/login")
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends()
) -> APIResponse[LoginResponse]:
    """Authenticate user and return tokens"""
    tokens = await auth_service.login(credentials)
    return APIResponse(success=True, data=tokens)
```

---

## 6. Services Layer

### Service Architecture

Business logic layer following **Separation of Concerns (SOC)**:

```python
# app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import hash_password, verify_password, create_jwt_token
from app.api.deps import get_db

class AuthService:
    """Authentication business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_data: UserCreate) -> UserResponse:
        # 1. Validate input
        # 2. Check if user exists
        # 3. Hash password
        # 4. Create user
        # 5. Generate tokens
        # 6. Return response
        pass

    async def login(self, credentials: LoginRequest) -> LoginResponse:
        # 1. Find user
        # 2. Verify password
        # 3. Check if active
        # 4. Generate tokens
        # 5. Update last login
        # 6. Return response
        pass
```

### Service Dependencies

```python
# app/api/deps.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.auth_service import AuthService

async def get_auth_service(
    db: AsyncSession = Depends(get_db)
) -> AuthService:
    """Dependency for auth service"""
    return AuthService(db)
```

---

## 7. Real-time Features

### WebSocket Architecture

```python
# app/api/v1/chat/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import json

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    room_id: str
):
    await manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Process message
            await manager.broadcast(room_id, data)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
```

### Redis Pub/Sub for Multi-instance

```python
# app/utils/redis_pubsub.py
import asyncio
import json
from redis.asyncio import Redis

async def redis_message_handler(channel: str, message: dict):
    """Handle Redis pub/sub messages"""
    # Broadcast to WebSocket clients in this instance
    await manager.broadcast(channel, message)

async def subscribe_to_channels():
    """Subscribe to Redis channels for pub/sub"""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("chat:*", "notifications:*")

    async for message in pubsub.listen():
        if message['type'] == 'message':
            channel = message['channel']
            data = json.loads(message['data'])
            await redis_message_handler(channel, data)
```

---

## 8. Background Tasks

### Celery Configuration

```python
# app/tasks/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
)
```

### Background Tasks

```python
# app/tasks/email_tasks.py
from app.tasks.celery_app import celery_app

@celery_app.task
def send_verification_email(email: str, token: str):
    """Send email verification email"""
    # Send email using SendGrid/Mailgun/SES
    pass

@celery_app.task
def send_password_reset_email(email: str, reset_link: str):
    """Send password reset email"""
    pass

# app/tasks/notification_tasks.py
@celery_app.task
def send_push_notification(user_id: str, notification: dict):
    """Send push notification via Firebase/APNS"""
    pass
```

---

## 9. File Storage

### MinIO/S3 Integration

```python
# app/utils/s3.py
import boto3
from app.core.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.MINIO_ENDPOINT,
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
)

async def upload_file(
    file: UploadFile,
    bucket: str,
    key: str
) -> str:
    """Upload file to MinIO"""
    s3_client.upload_fileobj(
        file.file,
        bucket,
        key,
        ExtraArgs={"ContentType": file.content_type}
    )
    return f"{settings.MINIO_ENDPOINT}/{bucket}/{key}"

async def delete_file(bucket: str, key: str):
    """Delete file from MinIO"""
    s3_client.delete_object(Bucket=bucket, Key=key)
```

### Image Processing

```python
# app/utils/image.py
from PIL import Image
import io

def create_thumbnail(image_data: bytes, size: tuple = (300, 300)) -> bytes:
    """Create thumbnail from image"""
    img = Image.open(io.BytesIO(image_data))
    img.thumbnail(size)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()

def validate_image(image_data: bytes) -> bool:
    """Validate image file"""
    try:
        img = Image.open(io.BytesIO(image_data))
        img.verify()
        return True
    except Exception:
        return False
```

---

## 10. Security

### Authentication (JWT)

```python
# app/core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_jwt_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

### Rate Limiting

```python
# app/core/rate_limit.py
from fastapi import Request, HTTPException
from app.db.redis import redis_client

async def rate_limit(
    request: Request,
    key: str,
    max_requests: int = 100,
    window: int = 60
):
    """Rate limit check using Redis"""
    client_ip = request.client.host
    rate_key = f"rate_limit:{key}:{client_ip}"

    current = await redis_client.incr(rate_key)
    if current == 1:
        await redis_client.expire(rate_key, window)

    if current > max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

### CORS Configuration

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 11. Testing Strategy

### Essential Tests Only

Focus on critical paths:
- **Authentication** (register, login, token refresh)
- **Deals** (create, update status, payments)
- **Chat** (WebSocket connection, message sending)

### Pytest Configuration

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.main import app
from app.db.session import get_db

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session():
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")
    async with AsyncSession(engine) as session:
        yield session
```

### Example Tests

```python
# tests/test_auth/test_register.py
pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "phone": "+1234567890",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["username"] == "testuser"
```

---

## 12. Deployment

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/marketplace
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
      - minio

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: marketplace
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

  celery:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations
RUN alembic upgrade head

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://app:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 13. Implementation Phases

### Phase 1: Foundation (Week 1)
- [x] Project setup (Docker, dependencies, structure)
- [x] Database models (all 22 tables)
- [x] Core services (security, config, exceptions)
- [x] Base API structure

### Phase 2: Authentication (Week 1-2)
- [ ] 8 Auth endpoints
- [ ] JWT implementation
- [ ] Password reset flow
- [ ] Email verification

### Phase 3: Core Marketplace (Week 2-3)
- [ ] 15 Buy flow endpoints
- [ ] 9 Sell flow endpoints
- [ ] 13 Profile endpoints
- [ ] Deal management

### Phase 4: Real-time Features (Week 3-4)
- [ ] 9 Chat endpoints
- [ ] WebSocket implementation
- [ ] 9 Notification endpoints
- [ ] Redis pub/sub

### Phase 5: Discovery & Admin (Week 4-5)
- [ ] 8 Home feed endpoints
- [ ] 40 Admin endpoints
- [ ] 11 Security endpoints
- [ ] 11 Moderation endpoints

### Phase 6: Polish & Deploy (Week 5-6)
- [ ] Push notifications (7 endpoints)
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Load testing
- [ ] Deployment to Contabo VPS

---

## Success Criteria

✅ All 115 endpoints implemented with exact response formats
✅ Frontend team can integrate without modifications
✅ WebSocket real-time features working
✅ Celery background tasks processing
✅ Docker deployment to Contabo VPS successful
✅ Essential tests passing for critical paths
✅ Interactive API docs at /docs

---

## Next Steps

1. **Immediate:** Launch parallel agents to start implementation
2. **Use venv** for clean Python environment
3. **Follow YAGNI, DRY, SOC** principles
4. **Track progress** with task list for all 115 endpoints
5. **Ensure type safety** with moderate type hints
6. **Maintain clean code** throughout implementation
