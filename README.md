# Gaming Marketplace Backend

FastAPI backend for a P2P gaming account marketplace with human-mediated transactions.

## 🎯 What This Is

A secure marketplace where gamers can buy and sell accounts (PUBG, Free Fire, etc.) with the safety of human mediators overseeing each transaction through secure 3-way chat rooms.

## 🚀 Quick Start

```bash
# Clone repository
git clone <your-repo-url>
cd marketplace-backend

# Start development environment
cp .env.example .env.dev
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Access API docs
open http://localhost:8000/docs
```

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.12+
- PostgreSQL 16 (in Docker)
- Redis 7 (in Docker)

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **API** | FastAPI 0.115+ |
| **Language** | Python 3.12+ |
| **Database** | PostgreSQL 16 |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Cache/Messaging** | Redis 7 |
| **Task Queue** | Celery 5 |
| **File Storage** | Cloudflare R2 |
| **Push Notifications** | OneSignal |
| **Testing** | pytest |
| **Documentation** | Swagger UI |

## 📁 Project Structure

```
marketplace-backend/
├── app/                    # Application code
│   ├── api/               # API routers
│   ├── core/              # Configuration, security
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── repositories/      # Data access
│   ├── tasks/             # Celery tasks
│   └── websocket/         # WebSocket handlers
├── tests/                 # Pytest tests
├── migrations/            # Alembic migrations
├── docs/                  # Documentation
└── docker-compose.yml     # Local development
```

## 🔐 Architecture

**Layered Monolith with Strict SOC:**

```
Router (API) → Service (Business Logic) → Repository (Data Access) → Database
```

**Key Principles:**
- Router validates input, checks auth
- Service implements business rules
- Repository handles database queries
- Never skip layers!

## 📚 Documentation

- **[System Overview](./docs/01-System-Overview.md)** - What we're building
- **[Architecture Design](./docs/02-Architecture-Design.md)** - System architecture
- **[API Structure](./docs/api/API-Structure.md)** - API endpoints
- **[Database Schema](./docs/database/Database-Schema.md)** - Data models
- **[Realtime Architecture](./docs/architecture/Realtime-Architecture.md)** - WebSocket implementation
- **[Deployment Guide](./docs/deployment/Deployment-Guide.md)** - Production deployment
- **[Development Workflow](./docs/workflow/Development-Workflow.md)** - How to develop

## 🧪 Testing

```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Run specific tests
docker-compose exec backend pytest tests/unit/services/
```

## 🚀 Deployment

See [Deployment Guide](./docs/deployment/Deployment-Guide.md) for:
- Contabo VPS setup
- Docker configuration
- CI/CD pipeline
- Environment variables
- SSL certificates
- Monitoring

## 🎯 Core Features

- ✅ JWT authentication (access + refresh tokens)
- ✅ Gaming account listings (browse, create, edit)
- ✅ Mediator directory and selection
- ✅ 3-way chat system (group + private rooms)
- ✅ Deal workflow (request → payment → credentials → close)
- ✅ Real-time messaging (WebSockets + Redis pub/sub)
- ✅ File uploads (Cloudflare R2)
- ✅ Push notifications (OneSignal)
- ✅ Role-based access control (User, Mediator, Admin)
- ✅ Mediator tier system
- ✅ Admin dashboard

## 🔒 Security

- JWT-based authentication (15min access token, 7day refresh token)
- Role-based authorization (User, Mediator, Admin)
- Redis-backed rate limiting
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy)
- XSS protection
- CORS configuration

## 📊 Performance

- Target: <200ms API response time (p95)
- Async/await for I/O operations
- Redis caching
- Database connection pooling
- Efficient pagination (cursor-based)

## 🛠️ Development

```bash
# Format code
docker-compose exec backend black app/

# Sort imports
docker-compose exec backend isort app/

# Lint
docker-compose exec backend ruff check app/

# Type check
docker-compose exec backend mypy app/
```

## 📖 API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Flutter Integration

This backend is designed for seamless integration with Flutter apps:

- RESTful API with JSON responses
- WebSocket support for real-time features
- Consistent error handling
- Auto-generated API documentation
- Type-safe Pydantic schemas

## 📝 License

[Your License Here]

## 👥 Team

- **Backend**: Python/FastAPI team
- **Frontend**: Flutter team
- **DevOps**: Infrastructure team

---

**Version**: 0.1.0 (Design Phase)
**Last Updated**: 2026-03-14
claude --resume 7faeb481-83ca-4600-847e-9137c243b554


claude --resume d7a70048-8b39-4056-8d5f-f51af61b8131