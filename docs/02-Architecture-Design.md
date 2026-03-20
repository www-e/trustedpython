# Architecture Design

## 🏗️ Overall Architecture Pattern

### Layered Monolith with Strict Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│                    (FastAPI Routers)                        │
│  - Request validation (Pydantic)                            │
│  - Authentication/Authorization checks                      │
│  - Response formatting                                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                    │
│                      (Services)                             │
│  - Orchestrate workflows                                    │
│  - Implement business rules                                 │
│  - Coordinate multiple repositories                         │
│  - Transaction boundaries                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Access Layer                      │
│                    (Repositories)                           │
│  - Database queries                                         │
│  - External API calls                                       │
│  - Cache interactions                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         Data Layer                          │
│              (PostgreSQL, Redis, External APIs)             │
└─────────────────────────────────────────────────────────────┘
```

### Golden Rule: Always Downward Flow

**Router → Service → Repository → Data**

#### Router Layer Responsibilities
```python
# ✅ CORRECT
@router.post("/listings")
async def create_listing(
    data: ListingCreate,
    current_user: User = Depends(require_auth),
    service: ListingService = Depends()
):
    """Validate request, check auth, delegate to service"""
    listing = await service.create_listing(data, current_user.id)
    return listing

# ❌ WRONG - Business logic in router
@router.post("/listings")
async def create_listing(data: ListingCreate):
    """Never query DB or implement rules in router"""
    if data.price <= 0:
        raise ValueError("Invalid price")  # Should be in service
    listing = await db.insert(Listing, data)  # Should be in repository
```

#### Service Layer Responsibilities
```python
# ✅ CORRECT
class ListingService:
    async def create_listing(self, data: ListingCreate, user_id: int):
        """Business logic, orchestrate repos, manage transactions"""
        # Business rules
        if data.price < MIN_PRICE:
            raise ValueError("Price too low")

        # Coordinate repositories
        user = await self.user_repo.get(user_id)
        category = await self.category_repo.get(data.category_id)

        # Create and return
        listing = await self.listing_repo.create(data, user_id)
        return listing

# ❌ WRONG - DB queries in service
class ListingService:
    async def create_listing(self, data: ListingCreate, user_id: int):
        # Never access db directly - use repository
        listing = await self.db.execute(
            insert(Listing).values(**data.dict())
        )
```

#### Repository Layer Responsibilities
```python
# ✅ CORRECT
class ListingRepository:
    async def create(self, data: ListingCreate, user_id: int) -> Listing:
        """Data access only - no business logic"""
        query = insert(Listing).values(
            title=data.title,
            price=data.price,
            user_id=user_id,
            **data.dict(exclude={'title', 'price'})
        )
        listing = await self.session.execute(query)
        return listing.scalar_one()

# ❌ WRONG - Business rules in repository
class ListingRepository:
    async def create(self, data: ListingCreate, user_id: int):
        # Never validate business rules here
        if data.price < MIN_PRICE:  # Wrong - service's job
            raise ValueError("Price too low")
```

---

## 📁 Project Directory Structure

```
marketplace-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   │
│   ├── api/                         # API v1 Routers
│   │   ├── __init__.py
│   │   ├── deps.py                  # Router dependencies
│   │   ├── auth.py                  # Authentication endpoints
│   │   ├── users.py                 # User management
│   │   ├── listings.py              # Listing CRUD
│   │   ├── deals.py                 # Deal transactions
│   │   ├── chats.py                 # Chat messaging
│   │   ├── mediators.py             # Mediator management
│   │   └── admin.py                 # Admin endpoints
│   │
│   ├── core/                        # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py                # Settings from env
│   │   ├── security.py              # JWT, password hashing
│   │   ├── deps.py                  # Service/Repo deps
│   │   └── middleware.py            # Custom middleware
│   │
│   ├── models/                      # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── base.py                  # Base model class
│   │   ├── user.py                  # User model
│   │   ├── listing.py               # Listing model
│   │   ├── deal.py                  # Deal model
│   │   ├── chat.py                  # Chat models
│   │   ├── mediator.py              # Mediator model
│   │   └── tier.py                  # Tier model
│   │
│   ├── schemas/                     # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── user.py                  # User DTOs
│   │   ├── listing.py               # Listing DTOs
│   │   ├── deal.py                  # Deal DTOs
│   │   ├── chat.py                  # Chat DTOs
│   │   ├── mediator.py              # Mediator DTOs
│   │   └── common.py                # Common schemas (pagination, etc)
│   │
│   ├── services/                    # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Authentication logic
│   │   ├── user_service.py          # User management
│   │   ├── listing_service.py       # Listing logic
│   │   ├── deal_service.py          # Deal orchestration
│   │   ├── chat_service.py          # Chat logic
│   │   └── mediator_service.py      # Mediator management
│   │
│   ├── repositories/                # Data Access Layer
│   │   ├── __init__.py
│   │   ├── base.py                  # Base repository
│   │   ├── user_repository.py
│   │   ├── listing_repository.py
│   │   ├── deal_repository.py
│   │   ├── chat_repository.py
│   │   └── mediator_repository.py
│   │
│   ├── tasks/                       # Celery Tasks
│   │   ├── __init__.py
│   │   ├── notifications.py         # OneSignal push
│   │   ├── listings.py              # Listing cleanup
│   │   └── deals.py                 # Deal reminders
│   │
│   ├── websocket/                   # WebSocket Handlers
│   │   ├── __init__.py
│   │   ├── manager.py               # Connection manager
│   │   ├── chat.py                  # Chat endpoints
│   │   └── auth.py                  # WebSocket auth
│   │
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── s3.py                    # Cloudflare R2 client
│       ├── onesignal.py             # OneSignal client
│       ├── pagination.py            # Pagination helpers
│       └── validators.py            # Custom validators
│
├── tests/                           # Pytest Tests
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/                        # Unit tests
│   │   ├── services/
│   │   └── repositories/
│   ├── integration/                 # Integration tests
│   │   ├── api/
│   │   └── websocket/
│   └── e2e/                         # End-to-end tests
│
├── migrations/                      # Alembic Migrations
│   └── versions/
│
├── docs/                            # Documentation
│   ├── 00-README.md
│   ├── 01-System-Overview.md
│   ├── 02-Architecture-Design.md
│   └── ...
│
├── .env.example                     # Environment template
├── .env.dev                         # Development config
├── .env.test                        # Test config
├── .env.prod                        # Production template
├── docker-compose.yml               # Local development
├── Dockerfile                       # Production image
├── pyproject.toml                   # Python dependencies
├── alembic.ini                      # Alembic config
└── README.md                        # Project README
```

---

## 🔄 Request Flow Example

### Example: Creating a Listing

```
1. HTTP Request
   POST /api/v1/listings
   Headers: Authorization: Bearer <JWT>
   Body: { "title": "PUBG Account", "price": 50 }

2. Router Layer (api/listings.py)
   ├─ Parse JWT token → Extract user_id
   ├─ Validate request body with Pydantic
   └─ Call listing_service.create()

3. Service Layer (services/listing_service.py)
   ├─ Validate business rules (price > 0, category exists)
   ├─ Call user_repo.get() to verify user
   ├─ Call category_repo.get() to verify category
   ├─ Call listing_repo.create() to save listing
   ├─ Call task_service.notify_new_listing() (Celery)
   └─ Return listing model

4. Repository Layer (repositories/listing_repository.py)
   ├─ Execute SQL INSERT via SQLAlchemy
   ├─ Return Listing model instance

5. Database (PostgreSQL)
   └─ Persist listing data

6. Response
   ├─ Service returns model to router
   ├─ Router converts to Pydantic schema
   └─ Return JSON response + 201 Created
```

### Code Implementation

```python
# api/listings.py (Router Layer)
@router.post("/listings", response_model=ListingResponse, status_code=201)
async def create_listing(
    data: ListingCreate,
    current_user: User = Depends(get_current_user),
    service: ListingService = Depends()
):
    """Create a new gaming account listing"""
    listing = await service.create_listing(data, current_user.id)
    return listing

# services/listing_service.py (Service Layer)
class ListingService:
    def __init__(
        self,
        listing_repo: ListingRepository,
        user_repo: UserRepository,
        category_repo: CategoryRepository
    ):
        self.listing_repo = listing_repo
        self.user_repo = user_repo
        self.category_repo = category_repo

    async def create_listing(
        self,
        data: ListingCreate,
        user_id: int
    ) -> Listing:
        # Business rule validation
        if data.price < MIN_LISTING_PRICE:
            raise ValueError(f"Price must be at least {MIN_LISTING_PRICE}")

        # Verify entities exist
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        category = await self.category_repo.get(data.category_id)
        if not category:
            raise NotFoundError("Category not found")

        # Create listing
        listing = await self.listing_repo.create(data, user_id)

        # Background task
        notify_new_listing.delay(listing.id)

        return listing

# repositories/listing_repository.py (Repository Layer)
class ListingRepository(BaseRepository):
    async def create(
        self,
        data: ListingCreate,
        user_id: int
    ) -> Listing:
        listing = Listing(
            title=data.title,
            description=data.description,
            price=data.price,
            category_id=data.category_id,
            user_id=user_id,
            status=ListingStatus.ACTIVE
        )
        self.session.add(listing)
        await self.session.commit()
        await self.session.refresh(listing)
        return listing
```

---

## 🎯 Design Patterns Used

### 1. Dependency Injection
```python
# Services injected into routers via FastAPI Depends()
@router.get("/listings")
async def get_listings(
    service: ListingService = Depends()  # Auto-injected
):
    return await service.get_listings()

# Repositories injected into services
class ListingService:
    def __init__(
        self,
        listing_repo: ListingRepository = Depends()  # Auto-injected
    ):
        self.listing_repo = listing_repo
```

### 2. Repository Pattern
```python
# Abstract base repository
class BaseRepository(Generic[Model]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int) -> Optional[Model]:
        result = await self.session.get(self.model, id)
        return result

    async def create(self, **kwargs) -> Model:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

# Concrete repository
class ListingRepository(BaseRepository[Listing]):
    model = Listing
```

### 3. Service Layer Pattern
```python
# Services contain business logic
# Services orchestrate multiple repositories
# Services manage transaction boundaries
class DealService:
    @async_transaction
    async def create_deal(self, data: DealCreate):
        # Multi-step workflow
        listing = await self.listing_repo.get(data.listing_id)
        mediator = await self.mediator_repo.get(data.mediator_id)

        # Create deal
        deal = await self.deal_repo.create(data)

        # Create 3 chat rooms
        chats = await self.chat_service.create_deal_chats(deal)

        # Send notifications
        notify_deal_created.delay(deal.id, chats)

        return deal
```

### 4. Factory Pattern (for WebSocket connections)
```python
class WebSocketFactory:
    @staticmethod
    def create_chat_websocket(chat_id: int, user: User):
        return ChatWebSocket(
            chat_id=chat_id,
            user_id=user.id,
            redis_pubsub=get_redis_pubsub()
        )
```

### 5. Strategy Pattern (for payment proof verification)
```python
class ProofVerificationStrategy(ABC):
    @abstractmethod
    async def verify(self, proof: ProofUpload) -> bool:
        pass

class VodafoneCashVerification(ProofVerificationStrategy):
    async def verify(self, proof: ProofUpload) -> bool:
        # Vodafone Cash specific verification
        pass

class CryptoVerification(ProofVerificationStrategy):
    async def verify(self, proof: ProofUpload) -> bool:
        # Crypto-specific verification
        pass
```

---

## 🔐 Security Architecture

### Authentication Flow
```
1. User sends phone + password → POST /api/v1/auth/login
2. Service verifies credentials → generate JWT
3. Return access_token (15min) + refresh_token (7days)
4. Client includes token in Authorization header
5. Each request validates JWT → extracts user_id
6. FastAPI dependency injects current_user
```

### Authorization Flow
```
1. Request hits protected endpoint
2. Depends(require_role) checks user.role
3. If role insufficient → 403 Forbidden
4. If role sufficient → proceed to handler
```

### Rate Limiting Flow
```
1. Request received
2. Rate limiter checks Redis for user/IP count
3. If limit exceeded → 429 Too Many Requests
4. If under limit → increment counter, proceed
5. Counter expires after window (60s, 1hr, etc)
```

---

## 📊 Caching Strategy

### Cache-Aside Pattern
```python
# Get user profile
async def get_user(user_id: int) -> User:
    # Try cache first
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return User.parse_raw(cached)

    # Cache miss - query DB
    user = await self.user_repo.get(user_id)

    # Populate cache (5 minute TTL)
    await redis.setex(
        f"user:{user_id}",
        300,
        user.json()
    )

    return user
```

### Cache Invalidation
```python
# Update user → invalidate cache
async def update_user(user_id: int, data: UserUpdate):
    user = await self.user_repo.update(user_id, data)

    # Invalidate cache
    await redis.delete(f"user:{user_id}")

    return user
```

### Cached Data Types
- **User profiles** (5 min TTL)
- **Mediator stats** (1 min TTL)
- **Listing counts** (5 min TTL)
- **Category lists** (1 hour TTL)

---

## 🧪 Testing Architecture

### Test Pyramid
```
        /\        E2E Tests (10%)
       /  \       - Critical user journeys
      /____\      - Full stack integration
     /      \
    /        \    Integration Tests (30%)
   /          \   - API endpoint tests
  /            \  - WebSocket tests
 /______________\
                 Unit Tests (60%)
                 - Service logic
                 - Repository queries
                 - Utilities
```

### Test Organization
```
tests/
├── unit/
│   ├── services/
│   │   ├── test_auth_service.py
│   │   ├── test_deal_service.py
│   │   └── test_listing_service.py
│   └── repositories/
│       └── test_listing_repository.py
├── integration/
│   ├── api/
│   │   ├── test_auth_endpoints.py
│   │   └── test_listing_endpoints.py
│   └── websocket/
│       └── test_chat_websocket.py
└── e2e/
    └── test_deal_flow.py
```

---

## 📚 Related Documentation

- [API Structure](./api/API-Structure.md) - Endpoint specifications
- [Database Schema](./database/Database-Schema.md) - Data models
- [Realtime Architecture](./architecture/Realtime-Architecture.md) - WebSocket implementation
- [Development Workflow](./workflow/Development-Workflow.md) - How we work

---

**Last Updated**: 2026-03-14
**Version**: 0.1.0
