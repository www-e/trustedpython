# Game Account Marketplace - AI Agent Steering Guide

> **Purpose**: This file steers AI agents working on this codebase — a FastAPI-based marketplace for buying and selling gaming accounts with a Flutter frontend. It focuses on principles, patterns, and verification, not implementation details.
> **MANDATORY**: You MUST follow the Auto Agent Detection & Parallel Execution Protocol below on EVERY task.

---

## Auto Agent Detection & Parallel Execution Protocol [MANDATORY]

> **These rules are NOT optional. They are the default mode of operation for every task.**

### 1. Automatic Agent Detection
**You MUST automatically detect and delegate to the correct specialized agent for the task.** Do NOT ask the user which agent to use. Analyze the task and pick the best fit immediately.

**Detection Rules:**
- Database schema changes, SQLAlchemy models, Alembic migrations, indexing → `database-architect`
- Auth flows (JWT, 2FA, OAuth), security reviews, vulnerability scanning → `security-auditor`
- Performance issues, slow API responses, database query optimization → `performance-engineer`
- API endpoints, FastAPI route design, Pydantic schemas, validation → `api-designer`
- Backend business logic, services layer, Celery tasks → `backend-developer`
- Full end-to-end features (DB models + API + services + Celery) → `fullstack-developer`
- Testing (pytest, pytest-asyncio, integration, E2E) → `testing-qa-expert`
- Docker, CI/CD pipelines, Docker Compose, cloud deployment → `devops-engineer`
- Code quality, Black, isort, flake8, mypy, refactoring → `code-quality-enforcer`
- Complex task planning and architecture → `dev-planner`
- Post-implementation code review → `superpowers-code-reviewer`
- Async Python patterns, asyncio, asyncpg → `python-pro` (via plugin)
- Database query optimization (SQLAlchemy, raw SQL) → `database-optimizer` or `sql-pro`
- WebSocket real-time features → `websocket-engineer` (via plugin)
- Security audits with OWASP Top 10 focus → `security-reviewer` (via plugin)

### 2. Automatic Skill Loading
**You MUST automatically load relevant skills BEFORE starting work.** Do NOT ask the user if they want to load a skill. Match the task to skills and load them immediately.

**Auto-Load Mapping:**
- Schema changes → `skill database-design`
- Auth/security work → `skill security-hardening` + `skill auth-security`
- Performance work → `skill performance-optimization`
- API/endpoint work → `skill api-design`
- Testing → `skill testing-strategy`
- Error handling → `skill error-handling`
- Code review → `skill code-review`
- Notifications/WebSocket → `skill notification-system`
- Payment features → `skill payment-integration`
- Async patterns, asyncio, FastAPI internals → `skill python-pro` (from fullstack-dev-skills)
- Complex SQL/high-performance queries → `skill sql-pro` (from fullstack-dev-skills)

### 3. Parallel Execution is DEFAULT
**You MUST use parallel execution for multi-step tasks.** Do NOT work sequentially unless there is a strict dependency chain. Launch multiple agents/tools in parallel whenever possible.

**Parallel Patterns:**
- **Research + Implementation**: Fire explore agents for context while planning implementation
- **Multi-file changes**: Edit independent files in parallel (e.g., route + service + schema)
- **Subagent delegation**: Launch multiple subagents for different aspects of the same task
- **Verification**: Run lint + type-check + tests in parallel after changes

**Example:**
```text
User: "Add a new listing analytics endpoint with seller stats"
Agent Response:
1. skill api-design
2. skill database-design
3. Launch parallel tasks:
   - database-architect: Design query/view for analytics
   - api-designer: Create FastAPI route + Pydantic schema
   - backend-developer: Build business logic service
4. Merge results and implement
5. Run verification in parallel (flake8 + mypy + pytest)
```

### 4. Visual & Organized Output
**You MUST organize ALL output for the user in a clear, visual format.** Never dump raw text or unorganized code blocks.

**Output Formatting Rules:**
- Use **Markdown tables** for comparisons, agent assignments, and status tracking
- Use **emoji indicators** for status: 🟢 Complete / 🟡 In Progress / 🔴 Blocked / ✅ Verified
- Provide a **Task Summary** at the end with: what was done, files changed, agents used, verification status

**Required Output Structure:**
```markdown
## Task Summary
| Agent | Role | Status |
|-------|------|--------|
| database-architect | Schema design | 🟢 Done |
| api-designer | Route creation | 🟢 Done |
| backend-developer | Business logic | 🟡 In Progress |

## Changes Made
- `app/models/analytics.py` - Added SellerAnalytics model
- `app/api/v1/admin/dashboard_routes.py` - Analytics endpoints
- `app/schemas/admin.py` - Analytics response schemas

## Verification
- [x] `make lint` passed
- [x] `make test` passed
- [ ] Docker build pending
```

---

## Core Principles

### 1. Verify First, Assume Nothing
- **Always verify** the current state before making changes
- **Don't recreate** work that's already done — always check if a route/service/schema exists
- **Read before writing** — understand the codebase before modifying it
- **Never hallucinate git state** — run `rtk git status` and read the output

### 2. Clean Architecture & Structure
- Follow existing patterns and conventions — this project uses **layered architecture**:
  - Routes (thin) → Services (business logic) → Models/DB (data)
- Maintain **Separation of Concerns (SOC)** — keep routes, services, models, and schemas separate
- Apply **YAGNI** — don't add functionality until it's actually needed
- Apply **DRY** — extract reusable patterns into shared modules (`app/core/`, `app/utils/`)

### 3. Auto Agent Detection & Smart Skills
- **Automatically detect** the correct agent type for the task
- **Use specialized skills** from available plugins when they match the domain
- **Delegate to subagents** for parallel work when appropriate
- Load skills with `skill <name>` before starting relevant work

### 4. Planning & Understanding
1. **Understand** the task and context first
2. **Plan** the approach before coding
3. **Verify** assumptions about the codebase
4. **Execute** with minimal, focused changes
5. **Test** to ensure correctness
6. **Verify** — run linters, type checks, and tests

---

## Project Architecture

### Tech Stack
| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI 0.109.0 (async Python 3.11+) |
| **Database** | PostgreSQL 15 + SQLAlchemy 2.0 async + asyncpg |
| **Migrations** | Alembic 1.13 |
| **Validation** | Pydantic v2 (request/response schemas) |
| **Auth** | JWT (python-jose + passlib/bcrypt) + TOTP 2FA (pyotp) |
| **Cache** | Redis 7 (caching, session store, pub/sub) |
| **Queue** | Celery 5.3.6 (background tasks, email, notifications) |
| **Storage** | MinIO / S3-compatible (file uploads, avatars, listing images) |
| **Async** | Python asyncio + asyncpg + SQLAlchemy async |
| **WebSocket** | FastAPI native WebSocket for chat & notifications |
| **Frontend** | Flutter (external, consumes REST API via JSON) |
| **HTTP Client** | httpx (async HTTP client) |
| **Logging** | loguru with structured JSON format |

### Directory Structure
```text
app/
├── main.py                 # FastAPI app entry with lifespan events
├── api/
│   ├── deps.py             # Shared deps (DB, Redis, auth, pagination)
│   └── v1/                 # API v1 routes (organized by domain)
│       ├── auth/           # Registration, login, email verify, reset password
│       ├── home/           # Feed, featured, categories, search, FAQ, promo
│       ├── profile/        # User profile CRUD, avatars, listings mgmt
│       ├── security/       # 2FA, login history, security score, freeze
│       ├── sell/           # Listing creation, publishing, analytics
│       ├── buy/            # Browsing, deals, payments, mediators
│       ├── chat/           # REST + WebSocket real-time messaging
│       ├── notifications/  # REST + WebSocket real-time notifications
│       └── admin/          # Dashboard, users, listings, mediators, reports
├── core/
│   ├── config.py           # Pydantic Settings (env-based config)
│   ├── database.py         # SQLAlchemy async engine + session factory
│   ├── security.py         # Password hashing (bcrypt) + JWT create/decode
│   ├── redis.py            # Redis async client
│   └── exceptions.py       # Typed exception classes
├── models/                 # SQLAlchemy 2.0 ORM models
│   ├── base.py             # DeclarativeBase + TimestampMixin
│   ├── user.py, account.py, listing.py, deal.py
│   ├── chat.py, notification.py, mediator.py, review.py
│   └── content.py          # FAQ, promo banners, categories, games
├── schemas/                # Pydantic v2 request/response schemas
│   └── common.py           # ErrorResponse, PaginatedResponse, PaginationMeta
├── services/               # Business logic (organized by domain)
│   ├── auth_service.py
│   ├── home/ (feed_service, content_service, search_service)
│   ├── profile/ (profile_management, listing_management)
│   ├── security/ (two_factor, login_history, security_score, etc.)
│   ├── buy/ (deal, payment, mediator, account_browsing)
│   ├── chat/ (room, message, participant, attachment, unread)
│   ├── notifications/ (crud, preferences)
│   └── admin/ (user, listing, deal, mediator, dashboard, etc.)
├── tasks/                  # Celery background tasks
│   └── celery_app.py       # Celery app configuration
└── utils/                  # Utilities
    ├── storage.py          # MinIO/S3 file storage
    ├── rate_limit.py       # Rate limiting
    └── redis_pubsub.py     # Redis pub/sub for WebSocket sync
```

---

## Key Patterns

### Route Registration (FastAPI)
- **All routes** registered in `app/api/v1/__init__.py` via `api_router.include_router()`
- **Domain modules** follow: `app/api/v1/{domain}/routes.py` or `{domain}_routes.py`
- **Tags** assigned in `include_router(tags=[...])` for OpenAPI grouping
- **Prefixes** applied in `include_router(prefix="/{domain}", ...)` for URL organization

### Dependencies (FastAPI Depends)
All shared dependencies come from `app/api/deps.py`:
- `get_db()` → async SQLAlchemy session (`AsyncSession`)
- `get_redis()` → async Redis client (`Redis | None`)
- `get_current_user()` → authenticated `User` from JWT Bearer token
- `get_current_active_user()` → active user (checks `is_active`)
- `get_optional_user()` → user if authenticated, else `None`
- `paginate()` → `PaginationParams(page, limit)` with validation
- `PaginationMeta.create(page, limit, total)` → pagination metadata

### Service Layer Patterns
- Services are **stateless**, receive db/redis sessions as parameters
- Services raise typed exceptions from `app/core/exceptions.py`:
  - `NotFoundException`, `UnauthorizedException`, `ForbiddenException`
  - `ValidationException`, `ConflictException`, `RateLimitException`
  - `PaymentRequiredException`, `ServiceUnavailableException`
- Routes catch exceptions via FastAPI exception handlers in `app/main.py`
- Async services use `async with` for session management

### Database Patterns (SQLAlchemy 2.0 Async)
- **Model style**: `class Model(Base, TimestampMixin):` with `Mapped[...]` type annotations
- **Base model**: `app/models/base.py` — `DeclarativeBase` + `TimestampMixin` (created_at, updated_at)
- **Session management**: `async_session_maker()` in `app/core/database.py` — never create manually
- **Query pattern**: `await db.execute(select(Model).where(Model.id == id)).scalar_one_or_none()`
- **Migrations**: Edit model → `alembic revision --autogenerate -m "desc"` → review → `alembic upgrade head`
- **Relationships**: SQLAlchemy `relationship()` for ORM, `ForeignKey` for FK columns

### Auth Patterns
- **JWT dual-token system**: Access token (30min) + Refresh token (7 days)
- **Password hashing**: bcrypt via passlib (`app/core/security.py`)
- **Token verification**: `decode_token()` + `verify_token()` with type checking
- **2FA**: TOTP via pyotp (`app/services/security/two_factor_service.py`)
- **Security scoring**: Points-based system (`app/services/security/security_score_service.py`)
- **Account freeze**: Emergency freeze/unfreeze (`app/services/security/account_freeze_service.py`)

### WebSocket Patterns (FastAPI WebSocket)
- **Chat**: `app/api/v1/chat/websocket.py` — Redis pub/sub for multi-instance message sync
- **Notifications**: `app/api/v1/notifications/websocket.py` — real-time notification delivery
- **Redis pub/sub**: `app/utils/redis_pubsub.py` — lifecycle managed in app lifespan events
- **Authentication**: WebSocket connections verify JWT token on connect

### Error Handling
- **Typed exceptions** in `app/core/exceptions.py` — each with error_code, message, status_code
- **Global handlers** in `app/main.py` — map exceptions to consistent `ErrorResponse` JSON
- **Validation errors** caught by `RequestValidationError` handler with field-level detail collection
- **Debug mode**: Full exception traces in `DEBUG=True`, sanitized in production

### Celery Tasks
- **App config**: `app/tasks/celery_app.py` — broker=Redis, result_backend=Redis
- **Tasks**: Defined in `app/tasks/` — used for email sending, notification delivery, cleanup jobs
- **Workers**: `celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4`
- **Monitoring**: Flower dashboard at port 5555
- **Scheduler**: Celery Beat for periodic tasks (`celery_beat` service in docker-compose)

### Logging & Middleware
- **CORS**: `CORSMiddleware` in `app/main.py` — update `CORS_ORIGINS` for Flutter dev domains
- **Request timing**: Custom middleware logs method, path, status, duration on every request
- **Structured logging**: loguru configured for JSON output in production
- **Headers**: Response includes `X-Process-Time` and `X-API-Version`

### Flutter Frontend Integration
- **REST API contract**: Flutter consumes JSON APIs at `/api/v1/*` — all responses use Pydantic v2 schemas
- **Authentication**: Bearer JWT token in `Authorization` header — access + refresh token flow
- **WebSocket**: Flutter connects to `/api/v1/chat/ws` and `/api/v1/notifications/ws`
- **CORS**: Add Flutter dev domains to `CORS_ORIGINS` in `.env` or `app/core/config.py`
- **API docs**: Swagger UI at `/docs`, ReDoc at `/redoc` — available when `DEBUG=True`
- **Pagination**: All list endpoints return `PaginationMeta` — Flutter handles page/limit params
- **Error format**: All errors return `ErrorResponse` with `error_code`, `message`, optional `details`
- **File upload**: MinIO/S3 for images — Flutter sends multipart/form-data to upload endpoints

### Import Patterns
- **Absolute imports** from project root: `from app.xxx import yyy`
- **Never use** relative imports like `from ..core import config`

---

## Feature Flag Patterns

When adding new features or modifying existing ones:
1. **Create a checklist** of all files that need changes (models, schemas, services, routes, tests)
2. **Check for existing patterns** — look at similar features for style consistency
3. **Implement bottom-up**: models → schemas → services → routes → tests
4. **Verify each layer** before moving to the next
5. **Run the full verification suite** at the end

---

## CRITICAL: Git State Awareness Protocol [MANDATORY]

### The Golden Rule of Git Operations
**Before ANY git command, verify the current state. Never assume.**

### Mandatory Checks Before Git Commands
Run ALL of these in parallel before touching git:
```bash
rtk git status --short                # What's modified/staged/untracked?
rtk git log --oneline -5              # Where is HEAD?
rtk git log --oneline origin/main..HEAD  # Commits ahead of origin?
rtk git stash list                    # Anything stashed?
rtk git diff --cached --name-only     # Staged files?
```

### Forbidden Patterns (NEVER Do These)
1. **NEVER claim "I didn't commit anything" without running `git log`**
2. **NEVER run `git reset` without first confirming HEAD vs origin/main**
3. **NEVER assume unstaged files are the only changes** — check commits ahead of origin
4. **NEVER ignore `git stash list` — stashed work is invisible in status**
5. **NEVER run destructive commands (`reset --hard`, `clean -fd`) without user explicit confirmation**

### The Reset Trap
`git reset --mixed` is safe for content, but it changes commit history pointers. **Always tell the user exactly what commits are being undone before resetting.**

---

## CRITICAL: Checklist-Before-Action Protocol [MANDATORY]

### The Pattern
When a task involves multiple similar items (files, endpoints, components):

1. **Create the checklist BEFORE touching any code**
2. **Work through it item by item — do not skip**
3. **Mark each item complete immediately after finishing**
4. **Never say "done" for the batch until every item is verified**

### Verification Per Item
Each checklist item must have its own verification step. Do not batch-verify at the end.

---

## CRITICAL: Anti-Hallucination Rules [MANDATORY]

### Definition
**Hallucination** = Making a confident claim about system state without evidence, or acting on an assumption you haven't verified.

### Forbidden Hallucinations
| Hallucination | Example | Correct Action |
|---------------|---------|----------------|
| "I didn't commit anything" | Claiming no commits | Run `git log --oneline -5` |
| "Those files are unstaged" | Assuming changes in working tree | Check commits ahead of origin |
| "The build passes" | Claiming without running | Run `make lint` or `pytest` |
| "That file exists at X" | Assuming path without checking | Use `glob` or `read` to verify |
| "The route is registered" | Assuming router inclusion | Check `app/api/v1/__init__.py` |
| "The migration works" | Not running it | Run `alembic upgrade head` in test env |

### Verification Commands (Run Before Claiming)
- **File exists?** → `glob` or `read`
- **Lint passes?** → `make lint`
- **Tests pass?** → `make test`
- **No commits made?** → `git log --oneline -5`
- **All files accounted for?** → `git diff --name-only origin/main..HEAD`
- **Type-safe?** → `mypy app/`
- **Route registered?** → check `app/api/v1/__init__.py`

### The Rule of Evidence
**Every claim about system state must be backed by a tool call you just made.** If you didn't run the command, you don't know. Say "Let me check" instead of guessing.

---

## Essential Commands

### Development
```bash
make dev              # Start FastAPI dev server (uvicorn --reload)
make test             # Run pytest with coverage
make lint             # Run flake8 + mypy
make format           # Run black + isort
make install          # Install dependencies (venv + pip)
```

### Docker
```bash
make build            # Build Docker images
make up               # Start all services (docker-compose up -d)
make down             # Stop all services
make restart          # Restart all services
make logs             # View all logs
make logs-app         # View app logs only
```

### Database (Alembic)
```bash
make db-migrate       # Create new Alembic migration
make db-upgrade       # Apply migrations
make db-downgrade     # Rollback last migration
```

### Celery
```bash
make celery-worker    # Start Celery worker
make celery-beat      # Start Celery beat scheduler
make flower           # Start Celery monitoring (port 5555)
```

### Direct Python Commands
```bash
pytest tests/ -v --cov=app --cov-report=term-missing
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

---

## Multi-State File Scenarios

When a user says "I have files everywhere" or "my numbers don't match", files may exist in **four places simultaneously**:

| State | Command to Check | Included in `git status`? |
|-------|------------------|---------------------------|
| **Unpushed commits** | `git log origin/main..HEAD` | ❌ No |
| **Staged** | `git diff --cached --name-only` | ✅ Yes (green) |
| **Unstaged** | `git diff --name-only` | ✅ Yes (red) |
| **Stashed** | `git stash show --name-only "stash@{0}"` | ❌ No |

**Always check all four states** before concluding where files are.

---

## Agent & Skill Reference

### Primary Agents (`.opencode/agent/`)

| Agent | Description | When to Use |
|-------|-------------|-------------|
| `backend-developer` | FastAPI services, business logic, Celery tasks | Building APIs, services, background jobs |
| `fullstack-developer` | Complete features: models → services → routes → Celery | End-to-end feature development |
| `database-architect` | SQLAlchemy models, Alembic migrations, indexing | Schema changes, migrations, optimization |
| `api-designer` | FastAPI routes, Pydantic schemas, validation | API design, request/response schemas |
| `security-auditor` | JWT auth, 2FA (TOTP), input validation, OWASP | Security features, vulnerability scanning |
| `performance-engineer` | Query optimization, caching, async patterns | Performance analysis, optimization |
| `testing-qa-expert` | pytest, pytest-asyncio, integration tests | Test writing, coverage improvement |
| `devops-engineer` | Docker, Docker Compose, CI/CD, deployment | Infrastructure, deployment, pipelines |
| `code-quality-enforcer` | Black, isort, flake8, mypy, clean code | Code quality, refactoring, standards |

### Subagents (`.opencode/agent/subagent/`)

| Subagent | Description | When to Use |
|----------|-------------|-------------|
| `dev-planner` | Task planning and architecture | Breaking down complex tasks |
| `superpowers-code-reviewer` | Post-implementation code review | Reviewing completed work |
| `security-scanner` | Focused vulnerability scanning | Scanning specific files/features |
| `perf-analyzer` | Component/endpoint-level profiling | Profiling specific endpoints/services |
| `prisma-optimizer` | Query-level optimization | Specific slow SQLAlchemy queries, N+1 fixes |

### Plugin Skills (via `skill <name>` in fullstack-dev-skills)

| Plugin Skill | Load When |
|--------------|-----------|
| `python-pro` | Async Python, asyncio, type hints, Pydantic |
| `fastapi-expert` | FastAPI patterns, dependencies, middleware, WebSockets |
| `sql-pro` | Complex SQL queries, EXPLAIN ANALYZE, window functions |
| `database-optimizer` | PostgreSQL/SQLAlchemy query performance |
| `test-master` | Test architecture, coverage strategies, mocking |
| `debugging-wizard` | Troubleshooting async errors, tracing failures |
| `secure-code-guardian` | Security hardening, input validation, JWT patterns |
| `devops-engineer` | Docker, CI/CD, deployment infrastructure |
| `monitoring-expert` | Logging, metrics, alerting setup |
| `websocket-engineer` | Real-time WebSocket features, pub/sub patterns |
| `code-reviewer` | Structured code review with severity ratings |

---

## Working with This Codebase

### Before You Start
1. **Load relevant skills** automatically per the Auto-Load Mapping above
2. **Detect and delegate** to the correct specialized agent
3. **Verify the task hasn't been done** — check for existing routes, services, models
4. **Understand** the existing patterns — look at similar files for style consistency
5. **Plan your changes**
6. **Check git state** — run the Mandatory Git Checks above before making any changes

### While Working
1. Follow existing code style — match the project's Python conventions
2. Keep changes minimal and focused — surgical changes, not rewrites
3. Maintain separation of concerns — routes are thin, services contain logic
4. Don't add what you don't need (YAGNI)
5. **Execute in parallel** whenever there are independent sub-tasks
6. **Use checklists** for multi-item tasks — create the list first, then work through it
7. **Verify each item individually** — don't batch-verify at the end

### Verification Flow [MANDATORY]
After ANY change, run the verification ladder:

| Tier | Scope | Requirements |
|------|-------|-------------|
| **V1** | Single file, cosmetic | `flake8` on changed file |
| **V2** | Single domain, ≤3 files | `make lint` + `pytest tests/related/test_file.py` |
| **V3** | Multi-file, cross-cutting | `make lint` + `make test` + verify all routes registered |

**Never claim "works" without running the relevant verification.**

### When Done
1. Run `make lint` to verify code quality
2. Run `make test` to ensure tests pass
3. Ensure no duplication (DRY)
4. Verify logic is in the right layer (SOC)
5. Confirm the final result matches existing architectural patterns
6. **Present results in the Visual Output Format defined above**
7. **Verify git state** — know exactly what's committed, staged, unstaged, or stashed

---

## External References

- `README.md` — Full project documentation with all API endpoints listed
- `.env.example` — All environment variables with descriptions
- `docker-compose.yml` — Infrastructure definition (6 services)
- `Makefile` — All development commands documented
- `pyproject.toml` — Project metadata + tool configs (Black, isort, mypy, pytest)

---

## Agent Startup Reminder

At the start of a task:
1. Read this file first
2. **Load relevant skills** automatically per the Auto-Load Mapping
3. **Auto-detect the correct agent** — do NOT ask the user, pick it immediately
4. Verify the current code before proposing changes
5. **Plan parallel execution** for multi-step tasks
6. Delegate to specialized subagents for complex sub-tasks
7. **Format output visually** with tables, checklists, and status indicators
8. Finish with focused verification, not assumptions