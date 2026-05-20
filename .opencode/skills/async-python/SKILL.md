---
name: async-python
description: Use this skill when implementing async Python patterns, SQLAlchemy 2.0 async queries, Celery task flows, Redis pub/sub, or WebSocket handling. Covers asyncio best practices specific to the Game Account Marketplace.
---

# Async Python Skill

## SQLAlchemy 2.0 Async Queries

### Session Management
Sessions come from `get_db()` dependency — never create manually:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 20):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()
```

### Common Query Patterns

| Pattern | Code |
|---------|------|
| Get by ID | `await db.execute(select(Model).where(Model.id == id)).scalar_one_or_none()` |
| Get all | `await db.execute(select(Model)).scalars().all()` |
| Count | `await db.execute(select(func.count()).select_from(Model)).scalar()` |
| Filter + paginate | `q = select(Model).where(Model.field == val).offset(skip).limit(limit)` |
| Join | `select(ModelA).join(ModelB).where(ModelB.field == val)` |
| Exists check | `await db.execute(select(Model.id).where(...).limit(1)).first() is not None` |

### Bulk Operations
```python
# Bulk insert
db.add_all([Model(**data) for data in items])
await db.commit()

# Bulk update via execute
await db.execute(update(Model).where(Model.id.in_(ids)).values(status="active"))
await db.commit()
```

### N+1 Prevention
Always eager-load relationships when accessing them outside the query:
```python
from sqlalchemy.orm import selectinload

# ❌ N+1 — each item triggers a separate query
result = await db.execute(select(Listing))
listings = result.scalars().all()
for listing in listings:
    print(listing.user.name)  # triggers query per item

# ✅ Eager load
result = await db.execute(
    select(Listing).options(selectinload(Listing.user))
)
listings = result.scalars().all()
for listing in listings:
    print(listing.user.name)  # no extra query
```

## Transaction Safety

### Auto-commit pattern (single operation)
```python
db.add(new_record)
await db.commit()
await db.refresh(new_record)
```

### Explicit transaction for multi-step operations
```python
async def transfer_funds(db: AsyncSession, from_id: int, to_id: int, amount: float):
    try:
        from_wallet = await db.execute(
            select(Wallet).where(Wallet.user_id == from_id).with_for_update()
        ).scalar_one()
        to_wallet = await db.execute(
            select(Wallet).where(Wallet.user_id == to_id).with_for_update()
        ).scalar_one()

        from_wallet.balance -= amount
        to_wallet.balance += amount
        await db.commit()
    except Exception:
        await db.rollback()
        raise
```

## Celery Task Patterns

### Defining tasks
```python
from app.tasks.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, to_email: str, subject: str, body: str):
    try:
        # actual email sending logic
        pass
    except Exception as exc:
        raise self.retry(exc=exc)
```

### Calling from services
```python
from app.tasks.send_email_task import send_email_task

# Fire-and-forget
send_email_task.delay(user.email, "Welcome!", "Body")

# With countdown (schedule future)
send_email_task.apply_async(args=[email, subj, body], countdown=300)
```

## Redis Patterns

### Caching
```python
from app.core.redis import get_redis

redis = await get_redis()
if redis:
    # Set with 1hr TTL
    await redis.setex(f"cache:items:{item_id}", 3600, json.dumps(data))
    # Get
    cached = await redis.get(f"cache:items:{item_id}")
```

### Rate Limiting
```python
key = f"ratelimit:{action}:{user_id}"
count = await redis.incr(key)
if count == 1:
    await redis.expire(key, 60)  # 60s window
if count > 60:
    raise RateLimitException(detail="Too many requests")
```

## WebSocket + Redis Pub/Sub

### Chat WebSocket pattern (multi-instance sync)
```python
# On message send: publish to Redis channel
from app.utils.redis_pubsub import publish_message

await publish_message("chat:room:123", {
    "type": "new_message",
    "data": message_dict,
})

# Consumer picks it up and broadcasts to local WebSocket connections
```

## asyncio Best Practices

### Lifespan events (`app/main.py`)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await init_redis()
    await start_redis_listener()
    yield
    # Shutdown
    await stop_redis_listener()
    await close_redis()
```

### Never block the event loop
```python
# ❌ Blocking — freezes all requests
time.sleep(5)

# ✅ Non-blocking
await asyncio.sleep(5)

# ❌ Blocking HTTP call
requests.get("https://api.example.com")

# ✅ Async HTTP
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
```

### Proper cleanup
- Always use `async with` for resources
- Always call `await db.commit()` or `await db.rollback()` — sessions don't auto-close
- WebSocket connections: wrap handler in try/finally to close on disconnect
