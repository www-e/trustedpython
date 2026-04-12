# APIs Needed - Master Index

> **Project:** Trusted App - Game Account Marketplace  
> **Backend:** Python (FastAPI recommended)  
> **Database:** PostgreSQL + Redis (caching/sessions/pubsub)  
> **Real-time:** WebSockets for chat & notifications  
> **Status:** Phase 1 Complete (Auth, Chat, Notifications, Buy Flow)

---

## Documents Created ✅

| # | Document | Priority | Status | APIs Count |
|---|----------|----------|--------|------------|
| [00](00_ANALYSIS_SUMMARY.md) | Analysis Summary | - | ✅ Complete | - |
| [01](01_AUTHENTICATION.md) | Authentication APIs | P0 | ✅ Ready | 8 endpoints |
| [02](02_CHAT_MESSAGING.md) | Chat & Messaging APIs | P0 | ✅ Ready | 9 endpoints |
| [03](03_NOTIFICATIONS.md) | Notifications APIs | P1 | ✅ Ready | 9 endpoints |
| [04](04_BUY_FLOW.md) | Buy Flow APIs | P0 | ✅ Ready | 15 endpoints |
| [05](05_USER_PROFILE.md) | User Profile APIs | P0 | ✅ Ready | 13 endpoints |
| [06](06_SELL_LISTINGS.md) | Listings & Sell Flow APIs | P0 | ✅ Ready | 9 endpoints |
| [07](07_HOME_FEED_GAMES.md) | Home Feed & Games APIs | P1 | ✅ Ready | 8 endpoints |
| [08](08_ONBOARDING_SPLASH.md) | Onboarding & Splash APIs | P2 | ✅ Ready | 4 endpoints |
| [09](09_SECURITY_PRIVACY.md) | Security & Privacy APIs | P1 | ✅ Ready | 11 endpoints |
| [10](10_DATABASE_SCHEMA.md) | Database Schema | - | ✅ Complete | 22 tables |
| [11](11_FINAL_VERDICT.md) | Final Verdict & Gap Analysis | - | ✅ Complete | - |
| [12](12_ADMIN_DASHBOARD.md) | Admin Dashboard APIs | P0 | ✅ Ready | 40 endpoints |
| [13](13_MODERATION_TOOLS.md) | Moderation Tools APIs | P1 | ✅ Ready | 11 endpoints |
| [14](14_PUSH_NOTIFICATIONS.md) | Push Notifications APIs | P1 | ✅ Ready | 7 endpoints |

**Total APIs Defined:** 115 endpoints  
**Database Tables:** 22 tables  
**UI Coverage:** 90% of current UI, 95% of full production needs

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Flutter App (Client)                    │
│  ┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────┐ ┌──────────┐ │
│  │ Login   │ │ Signup │ │ Forgot   │ │ Buy  │ │ Chat     │ │
│  │ Screen  │ │ Screen │ │ Password │ │ Flow │ │ Screens  │ │
│  └────┬────┘ └───┬────┘ └────┬─────┘ └──┬───┘ └────┬─────┘ │
│       │          │           │          │          │        │
└───────┼──────────┼───────────┼──────────┼──────────┼────────┘
        │          │           │          │          │
        └──────────┴───────────┴──────────┴──────────┘
                           │
                    HTTP/REST API
                    WebSocket (WS)
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                  Python Backend (FastAPI)                    │
│                                                              │
│  ┌────────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐  │
│  │ Auth       │ │ Chat     │ │ Deals     │ │ Notifs     │  │
│  │ Service    │ │ Service  │ │ Service   │ │ Service    │  │
│  └─────┬──────┘ └────┬─────┘ └─────┬─────┘ └─────┬──────┘  │
│        │             │             │              │          │
│  ┌─────┴─────────────┴─────────────┴──────────────┴─────┐   │
│  │                 Database Layer                         │   │
│  │  PostgreSQL (primary) + Redis (cache/pubsub/sessions)  │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Recommended Python Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | FastAPI | High-performance async API |
| **Database** | PostgreSQL | Primary data store |
| **Cache** | Redis | Session, pubsub, rate limiting |
| **ORM** | SQLAlchemy + Alembic | DB ORM + migrations |
| **Auth** | JWT + bcrypt | Token-based auth |
| **WebSocket** | FastAPI WS + Redis pubsub | Real-time chat/notifs |
| **File Upload** | S3/MinIO | Image storage |
| **Task Queue** | Celery + Redis | Async tasks (emails, notifs) |
| **Validation** | Pydantic | Request/response validation |

---

## API Design Conventions

### Response Format
All API responses follow this structure:
```json
{
  "success": true | false,
  "data": { ... } | null,
  "message": "string | null",
  "error": "string | null",
  "pagination": { ... } | null
}
```

### Error Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {
      "field_name": ["Field-specific errors"]
    }
  }
}
```

### Authentication
All authenticated endpoints require:
```
Authorization: Bearer {access_token}
```

### Pagination
Standard pagination parameters:
- `page` (default: 1)
- `limit` (default: 20, max: 50)

---

## Database Entities (Preliminary)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    users     │     │   accounts   │     │    deals     │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id           │     │ id           │     │ id           │
│ username     │     │ title        │     │ account_id   │
│ email        │     │ game         │     │ buyer_id     │
│ phone        │     │ rank         │     │ seller_id    │
│ password_hash│     │ price        │     │ mediator_id  │
│ display_name │     │ description  │     │ status       │
│ avatar_url   │     │ images       │     │ total_amount │
│ is_verified  │     │ features     │     │ chat_room_id │
│ created_at   │     │ is_verified  │     │ created_at   │
│ updated_at   │     │ seller_id    │     │ updated_at   │
└──────────────┘     │ created_at   │     └──────────────┘
                     └──────────────┘
                           │
                     ┌─────┴─────┐
                     │           │
              ┌────────────┐ ┌────────────┐
              │ mediators  │ │  reviews   │
              ├────────────┤ ├────────────┤
              │ user_id    │ │ id         │
              │ rating     │ │ mediator_id│
              │ tier       │ │ reviewer_id│
              │ badges     │ │ rating     │
              │ bio        │ │ comment    │
              └────────────┘ │ created_at │
                             └────────────┘

┌──────────────────┐     ┌────────────────┐     ┌──────────────────┐
│    chat_rooms    │     │    messages    │     │  notifications   │
├──────────────────┤     ├────────────────┤     ├──────────────────┤
│ id               │     │ id             │     │ id               │
│ name             │     │ room_id        │     │ user_id          │
│ type             │     │ sender_id      │     │ title            │
│ avatar           │     │ content        │     │ description      │
│ created_at       │     │ type           │     │ type             │
│ updated_at       │     │ attachments    │     │ is_read          │
└──────────────────┘     │ created_at     │     │ metadata         │
                         └────────────────┘     │ created_at       │
                                                └──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│ chat_participants│     │    payments      │
├──────────────────┤     ├──────────────────┤
│ room_id          │     │ deal_id          │
│ user_id          │     │ screenshot_url   │
│ role             │     │ status           │
│ joined_at        │     │ submitted_at     │
└──────────────────┘     │ verified_at      │
                         │ rejection_reason │
                         └──────────────────┘
```

---

## Next Steps

1. ✅ Complete analysis of all UI features (Profile, Sell, Home, Games, Onboarding)
2. ✅ Create API documents for all features (8 documents complete)
3. ✅ Create Database Schema document (22 tables)
4. ⏳ Create WebSocket Protocol document
5. ⏳ Create Error Codes Reference document
6. ⏳ Review and validate all API specs

---

## Files Remaining to Read

| Feature | Files | Priority |
|---------|-------|----------|
| Profile | ~16 files | P0 |
| Sell | ~16 files | P0 |
| Home | ~14 files | P1 |
| Games | ~7 files | P2 |
| Onboarding | ~8 files | P2 |
| Splash | ~4 files | P2 |
| Core Widgets | ~28 files | P1 |
| Router/Theme | ~10 files | P1 |
| **Total** | **~103 files** | |

---

*Last Updated: 2026-04-11*
