# System Overview

## 🎯 What We're Building

A **secure Peer-to-Peer marketplace for gaming accounts** (PUBG, Free Fire, etc.) where safety is enforced by **human Mediators** rather than automated payment holds.

The platform acts as a matchmaker between Buyers, Sellers, and Mediators. All fund transfers and credential handoffs happen **manually in heavily monitored 3-way chat rooms**, after which the Mediator finalizes the digital handshake.

---

## 👥 Role Definitions

### 1. User (Buyer/Seller)
**Acquisition**: Self-registration

**Permissions**:
- Browse and search listings
- Create and manage listings
- Initiate buy requests
- Choose Mediators
- Upload payment proofs in private chat
- Receive credentials via Mediator
- View transaction history

### 2. Mediator
**Acquisition**: Created only by Admin

**Permissions**:
- Accept/decline deal requests
- Manage 3-way chat rooms
- Verify payment proofs
- Verify account credentials
- Transfer credentials to Buyer
- Close deals (make chats read-only)
- Limited by **Tier** (max concurrent chats, assistant count, reopen ability)

### 3. Admin
**Acquisition**: System default

**Permissions**:
- Full CRUD access
- Create/delete Mediator accounts
- Assign and manage Mediator Tiers
- Ban users and Mediators
- View all transactions and chats
- Manage platform configuration

---

## 🔄 End-to-End Transaction Flow

### Phase 1: Initiation
1. **Buyer** browses feed → finds account → clicks "Request to Buy"
2. **System** shows Mediator Selection screen (ranked by Tier, trust score, online status)
3. **Buyer** selects Mediator

### Phase 2: Notification & Chat Creation
4. **System** fires push notifications to Seller and Mediator
5. **System** creates 3 distinct chat rooms:
   - **Private**: Buyer ↔ Mediator (for payment proofs)
   - **Private**: Seller ↔ Mediator (for credential delivery)
   - **Group**: Buyer ↔ Seller ↔ Mediator (for coordination)

### Phase 3: Execution
6. **Buyer** pays Seller via external method (Vodafone Cash, Crypto, Bank Transfer)
7. **Buyer** uploads payment screenshot to private chat with Mediator
8. **Seller** provides account credentials to Mediator in private chat
9. **Mediator** verifies:
   - ✅ Payment proof is legitimate
   - ✅ Account credentials work

### Phase 4: Resolution
10. **Mediator** transfers credentials to Buyer
11. **Mediator** clicks **"Close Deal"**

### Phase 5: Closure
12. **All 3 chats** become read-only
13. **Listing status** changes to "Sold"
14. **Listing** moved to Sold Page
15. **Transaction** added to all participants' history

---

## 🏗️ System Architecture

### Pattern: Layered Monolith

```
┌─────────────────────────────────────────────┐
│           Flutter Mobile App                │
└─────────────────────────────────────────────┘
                    ↓ HTTPS/WSS
┌─────────────────────────────────────────────┐
│          API Gateway / Load Balancer        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│           FastAPI Application               │
│  ┌───────────────────────────────────────┐  │
│  │  Router Layer (API endpoints)         │  │
│  ├───────────────────────────────────────┤  │
│  │  Service Layer (Business Logic)       │  │
│  ├───────────────────────────────────────┤  │
│  │  Repository Layer (Data Access)       │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
          ↓        ↓           ↓
    ┌────────┐  ┌──────┐  ┌──────────┐
    │  PG    │  │Redis │  │  R2      │
    │  16    │  │  7   │  │  Storage  │
    └────────┘  └──────┘  └──────────┘
         ↓
    ┌──────────┐
    │ Celery   │
    │ Worker   │
    └──────────┘
         ↓
    ┌──────────┐
    │OneSignal │
    │  Push    │
    └──────────┘
```

### Flow Rule: Always Downward

**Router** → **Service** → **Repository** → **Model**

- ✅ **Router** validates input, calls service
- ✅ **Service** implements business logic, calls repository
- ✅ **Repository** accesses database, returns models
- ✅ **Model** represents data structures

**Never**:
- ❌ Put DB logic in routers
- ❌ Put business logic in repositories
- ❌ Skip layers

---

## 🎨 Tech Stack & Rationale

### Core Framework
- **FastAPI 0.115+** - Modern async framework, automatic validation, OpenAPI docs
- **Python 3.12+** - Latest async/await, type hints, performance improvements

### Data Layer
- **PostgreSQL 16** - ACID transactions for deal consistency, relational data
- **SQLAlchemy 2.0 (async)** - Mature ORM, async support, type-safe queries
- **Alembic** - Database migrations, version control, rollback support

### Real-time & Caching
- **Redis 7** - Pub/sub for WebSockets, Celery broker, rate limiting, caching
- **FastAPI WebSockets** - Native WebSocket support, connection management

### Background Tasks
- **Celery 5** - Async task queue, scheduled tasks, retry logic
- **Celery Beat** - Scheduled tasks (deal reminders, cleanup jobs)

### External Services
- **Cloudflare R2** - S3-compatible storage, cheaper than AWS, no egress fees
- **OneSignal** - Push notifications, no Firebase costs, better delivery

### Development & Deployment
- **Docker Compose** - Local dev consistency, easy onboarding
- **GitHub Actions** - CI/CD, automated testing and deployment
- **Contabo VPS** - Cost-effective hosting, full control

### Developer Experience
- **Pydantic V2** - Request/response validation, auto-generated schemas
- **Swagger UI + ReDoc** - Interactive API docs at `/docs`
- **pytest + pytest-asyncio** - Async test support, fixtures
- **loguru** - Structured logging, rotation, better than stdlib logging

---

## 📊 Scale & Performance Expectations

### User Growth
- **Month 1-2**: 300 users (50 Mediators, 250 Buyers/Sellers)
- **Month 3-6**: 600 users
- **Year 1**: 900+ users
- **Concurrent users**: ~50-100 during peak hours

### Expected Load
- **API requests**: 10-50 req/sec average, 200+ peak
- **WebSocket connections**: 50-100 concurrent
- **Chat messages**: 5-20 msg/sec during active deals
- **Database queries**: 100-500 q/sec
- **File uploads**: 20-100 per day (screenshots, proofs)

### Performance Targets
- **API response time**: <200ms p95
- **WebSocket latency**: <100ms for message delivery
- **Database query time**: <50ms for indexed queries
- **File upload**: Complete within 10 seconds
- **Push notification**: Delivered within 5 seconds

---

## 🔒 Security & Compliance

### Authentication
- **JWT Access Token**: 15-minute expiration
- **Refresh Token**: 7-day expiration
- **Token storage**: HttpOnly cookies (web) / Secure storage (mobile)
- **No email/OTP** in MVP (phone + password only)

### Authorization
- **Role-based access control** (User, Mediator, Admin)
- **FastAPI Dependencies** for route protection
- **Granular permissions** by tier for Mediators

### Data Protection
- **Payment proofs** stored securely, mediator-only access
- **Account credentials** never stored permanently
- **User data isolation** by user ID paths in storage
- **GDPR-ready** with account deletion workflows

### Rate Limiting
- **Redis-backed** distributed rate limiting
- **Per-IP and per-user** limits
- **Endpoint-specific** limits (chat > browsing > auth)

### Input Validation
- **Pydantic strict validation** at API boundary
- **SQLAlchemy** for database constraint validation
- **Custom validators** for business rules

---

## 🎯 Success Criteria

### MVP Must-Haves (Month 2)
✅ Complete user authentication flow
✅ Listing creation and browsing
✅ Mediator directory and selection
✅ 3-way chat system (all 3 rooms)
✅ Deal flow (request → close)
✅ File uploads (screenshots, proofs)
✅ Push notifications
✅ Admin dashboard (basic)
✅ Deployment to Contabo

### Growth Features (Month 3-6)
🔄 Mediator tier system implementation
🔄 Assistant sub-accounts for Mediators
🔄 Advanced analytics dashboard
🔄 Performance optimization
🔄 Enhanced search and filtering

### Scale Features (Month 6-12)
🔄 Multi-region deployment
🔄 Advanced caching strategies
🔄 Database sharding preparation
🔄 AI-powered fraud detection

---

## 📚 Related Documentation

- [Architecture Design](./02-Architecture-Design.md) - Deep dive into system architecture
- [API Structure](./api/API-Structure.md) - API endpoints and contracts
- [Database Schema](./database/Database-Schema.md) - Data models and relationships
- [Realtime Architecture](./architecture/Realtime-Architecture.md) - WebSocket implementation
- [Deployment Guide](./deployment/Deployment-Guide.md) - Contabo setup and deployment

---

**Last Updated**: 2026-03-14
**Version**: 0.1.0
