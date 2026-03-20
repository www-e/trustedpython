# Gaming Marketplace - Backend Documentation

**P2P Gaming Account Marketplace with Human-Mediated Transactions**

## 📖 Documentation Index

- **[01-System-Overview](./01-System-Overview.md)** - What we're building, core flows, and tech stack
- **[02-Architecture-Design](./02-Architecture-Design.md)** - System architecture, layer structure, design patterns
- **[03-API-Structure](./api/API-Structure.md)** - API versioning, endpoints, authentication, response formats
- **[04-Database-Schema](./database/Database-Schema.md)** - Data models, relationships, and migrations
- **[05-Realtime-Architecture](./architecture/Realtime-Architecture.md)** - WebSocket implementation, Redis pub/sub, chat system
- **[06-Deployment-Guide](./deployment/Deployment-Guide.md)** - Contabo setup, Docker configuration, CI/CD
- **[07-Development-Workflow](./workflow/Development-Workflow.md)** - Git workflow, testing, local development

## 🚀 Quick Start

```bash
# Clone and start development environment
git clone <repo-url>
cd marketplace-backend
cp .env.example .env.dev
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Access API docs
open http://localhost:8000/docs
```

## 🎯 Project Goals

- **Timeline**: <2 months to full production
- **Scale**: 300 users in first 2 months, 900+ in first year
- **Deployment**: Contabo VPS, self-hosted stack
- **Architecture**: Layered monolith with strict SOC
- **Team**: Small team, parallel frontend (Flutter) + backend development

## 📋 Core Features

✅ User authentication (phone + password, JWT)
✅ Gaming account listings (browse, create, edit)
✅ Mediator selection and assignment
✅ 3-way chat system (private + group rooms)
✅ Deal flow management (request → payment → credentials → close)
✅ Real-time messaging with WebSockets
✅ Push notifications (OneSignal)
✅ File uploads (Cloudflare R2)
✅ Admin dashboard (users, mediators, tiers)
✅ Mediator tier system (badges, limits, assistants)

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI 0.115+ | Async REST API |
| **Language** | Python 3.12+ | Modern async/await |
| **Database** | PostgreSQL 16 | Relational data, ACID |
| **ORM** | SQLAlchemy 2.0 (async) | Database abstraction |
| **Cache/Messaging** | Redis 7 | Pub/sub, rate limiting, caching |
| **Task Queue** | Celery 5 | Background tasks |
| **File Storage** | Cloudflare R2 | Images, proofs |
| **Push Notifications** | OneSignal | Mobile push |
| **Containerization** | Docker Compose | Local dev, production |
| **Migrations** | Alembic | Schema versioning |
| **Testing** | pytest + pytest-asyncio | Test framework |
| **Logging** | loguru | Structured logging |
| **API Docs** | Swagger UI | Auto-generated docs |

## 📁 Project Structure (Planned)

```
marketplace-backend/
├── app/
│   ├── api/              # API v1 routers
│   ├── core/             # Config, security, dependencies
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic layer
│   ├── repositories/     # Data access layer
│   ├── tasks/            # Celery tasks by domain
│   └── websocket/        # WebSocket handlers
├── tests/                # Pytest tests
├── migrations/           # Alembic migrations
├── docs/                 # This documentation
├── .env.example          # Environment template
├── docker-compose.yml    # Local development
├── Dockerfile            # Production image
└── pyproject.toml        # Python dependencies
```

## 🎯 Development Principles

1. **Strict SOC** - Router → Service → Repository → Model (always)
2. **Layer-by-layer** - Build infrastructure first, then features
3. **API-first** - Stable contracts for Flutter integration
4. **Test critical paths** - Full TDD for deals, chat, auth
5. **Version from day one** - `/api/v1/` from the start
6. **Real-time ready** - Redis pub/sub for WebSockets
7. **Self-hosted** - No external dependencies beyond R2 + OneSignal

## 📞 Contact & Support

- **Backend Team**: [Contact info]
- **Flutter Team**: [Contact info]
- **Documentation**: Updated continuously during development

---

**Last Updated**: 2026-03-14
**Version**: 0.1.0 (Design Phase)
