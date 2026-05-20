---
name: fastapi-patterns
description: Use this skill when building FastAPI routes, Pydantic schemas, dependency injection, or API layers for the Game Account Marketplace. Covers layered architecture, response patterns, error handling, and Flutter API contracts.
---

# FastAPI Patterns Skill

## Layered Architecture

All features follow this strict layering — routes are thin, services hold logic, models own data:

```
Route (schema in/out) → Service (business logic) → Model (SQLAlchemy ORM)
```

### Route Layer (thin)
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_user
from app.schemas.common import APIResponse

router = APIRouter()

@router.get("/items/{item_id}", response_model=APIResponse[ItemResponse])
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await item_service.get_item(db, item_id, current_user.id)
    return APIResponse.success_response(data=ItemResponse.model_validate(result))
```

### Service Layer (stateless)
```python
from app.core.exceptions import NotFoundException, ForbiddenException

async def get_item(db: AsyncSession, item_id: int, user_id: int) -> Item:
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException(detail="Item not found")
    if item.user_id != user_id:
        raise ForbiddenException(detail="Not your item")
    return item
```

## Dependencies (`app/api/deps.py`)

Always use these shared deps — never re-implement:

| Dep | What it gives you |
|-----|-------------------|
| `get_db` | Async SQLAlchemy session |
| `get_redis` | Async Redis client (or None) |
| `get_current_user` | `User` from JWT Bearer token |
| `get_current_active_user` | User + checks `is_active` |
| `get_optional_user` | User if authenticated, else None |
| `PaginationParams` | Validated `page` and `limit` query params |

```python
from app.api.deps import get_db, get_current_active_user, PaginationParams
```

## Response Patterns

### Success with data
```python
return APIResponse.success_response(data=ItemResponse.model_validate(item))
```

### Success with pagination
```python
return APIResponse.success_response(
    data=[ItemResponse.model_validate(i) for i in items],
    pagination=PaginationSchema.create(page, limit, total),
)
```

### Error cases — raise typed exceptions, never raw HTTPException
```python
from app.core.exceptions import (
    NotFoundException,       # 404
    UnauthorizedException,   # 401
    ForbiddenException,      # 403
    ValidationException,     # 422
    ConflictException,       # 409
    RateLimitException,      # 429
    PaymentRequiredException,# 402
)
```

## Pydantic v2 Schemas

### Request schemas — standard BaseModel with Field
```python
from pydantic import BaseModel, Field, EmailStr

class CreateItemRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Item title")
    price: float = Field(..., gt=0, description="Price in USD")
```

### Response schemas — use `from_attributes=True` for ORM mapping
```python
class ItemResponse(BaseModel):
    id: int
    title: str
    price: float
    created_at: datetime

    model_config = {"from_attributes": True}
```

Use `model_validate()` (not `from_orm`) for Pydantic v2:
```python
ItemResponse.model_validate(db_item)  # ✅ correct
# ItemResponse.from_orm(db_item)      # ❌ removed in v2
```

## Route Registration

Every domain module registers in `app/api/v1/__init__.py`:
```python
api_router.include_router(my_module.router, prefix="/my-module", tags=["My Module"])
```

## Flutter API Contract

- All responses wrapped in `APIResponse` (`success`, `data`, `error`, `pagination`, `message`)
- All errors return `ErrorResponse` (`error_code`, `message`, `details`)
- List endpoints accept `?page=1&limit=20` and return `PaginationSchema`
- Auth via `Authorization: Bearer <token>` header
- File upload via `multipart/form-data`
- WebSocket auth via `?token=<jwt>` query parameter
