# Production Readiness - Fix Plan

**Created:** April 12, 2026  
**Priority:** Critical → Low  
**Estimated Effort:** 2-3 sprints

---

## Phase 1: Critical - Remove Mock Data (P0) - THIS SESSION

### Fix 1: sell_service.py - Image Upload
**File:** `app/services/sell_service.py`  
**Lines:** 231-259  
**Current:** Returns hardcoded CDN URLs with fake dimensions  
**Fix:** Use `app.utils.storage.upload_file_to_storage` + PIL for dimensions

```python
# Current (BAD):
url = f"https://cdn.gamemarket.com/listings/{image_id}.jpg"
width, height = 1920, 1080  # Placeholder

# Fixed (GOOD):
from app.utils.storage import upload_file_to_storage
from PIL import Image
import io

# Upload file to storage
upload_file = UploadFile(filename=filename, file=io.BytesIO(file_data))
url = await upload_file_to_storage(upload_file, folder=f"listings/{listing_id}")

# Get real dimensions
img = Image.open(io.BytesIO(file_data))
width, height = img.size
```

**Files to fix:**
1. `app/services/sell_service.py` (lines 231-259, 551)
2. `app/services/profile_service.py` (lines 256-257, 421)
3. `app/services/profile/management_service.py` (lines 267-268)
4. `app/services/profile/listing_management_service.py` (lines 172, 322-323)
5. `app/api/v1/buy/payment_routes.py` (lines 65-66)

---

## Phase 2: High Priority - Business Logic (P1) - NEXT SESSION

### Fix 2: Email Verification Flow
**Files:** `app/services/auth_service.py`  
**Lines:** 124, 210-213, 287-290

**Current:** No email sent, verification doesn't update DB  
**Fix:**
1. Integrate with email service (SMTP or AWS SES)
2. Generate and store verification tokens
3. Update `user.is_email_verified = True` on verification
4. Set `user.email_verified_at = datetime.utcnow()`

**Dependencies:**
- SMTP credentials configured in `.env`
- Email templates created
- Token storage strategy (DB or Redis)

### Fix 3: Logout Token Blacklisting
**File:** `app/services/auth_service.py`  
**Lines:** 305-307

**Current:** Logout doesn't invalidate tokens  
**Fix:**
1. Store revoked tokens in Redis with TTL matching token expiry
2. Check token blacklist in `get_current_user` dependency
3. Set `session.revoked_at` in database

**Dependencies:**
- Redis connection
- Session model properly configured

### Fix 4: Admin Reports & Audit
**Files:**
- `app/services/admin/report_service.py` (lines 55-101)
- `app/services/admin/audit_service.py` (lines 69-120)

**Current:** All methods return empty data  
**Fix:**
1. Implement actual database queries for reports
2. Create audit log table if missing
3. Wire up event logging on admin actions

**Dependencies:**
- Database tables for reports/audit logs
- Event tracking infrastructure

### Fix 5: Mediator Verification
**Files:**
- `app/api/v1/buy/deal_routes.py` (line 129)
- `app/api/v1/buy/payment_routes.py` (lines 106, 143)

**Current:** No verification that user is mediator  
**Fix:**
1. Check `current_user.id == deal.mediator_id` before allowing mediator actions
2. Return 403 if user is not the assigned mediator

---

## Phase 3: Medium - Stub Modules (P2)

### Fix 6: Return 501 for Unimplemented Modules
**Files:**
- `app/api/v1/accounts/__init__.py`
- `app/api/v1/analytics/__init__.py`
- `app/api/v1/games/__init__.py`
- `app/api/v1/orders/__init__.py`
- `app/api/v1/payments/__init__.py`
- `app/api/v1/users/__init__.py`

**Current:** Empty routers return 200 with empty response  
**Fix:** Return 501 Not Implemented

```python
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def not_implemented():
    raise HTTPException(
        status_code=501,
        detail="This endpoint is not yet implemented"
    )
```

---

## Phase 4: Cleanup (P3)

### Fix 7: Remove Stale Comments
**Files:** All files with TODO comments  
**Action:** Remove or update comments that are no longer relevant

Examples:
- `core/database.py` line 4: "This is a placeholder module" → Implementation is complete, remove comment
- All "TODO: Implement" comments for features that are now implemented
- All "For now, return mock data" comments after fixing mock data issues

---

## Impact Assessment

### What Flutter Team Can Do NOW
```
✅ Test authentication flow (register, login)
✅ Browse the API structure via /docs
✅ Set up API client with all 113 endpoints
✅ Implement request/response models
✅ Test error handling (401, 422, 500)
```

### What Requires Infrastructure
```
⏳ PostgreSQL - All data queries
⏳ Redis - Caching, sessions, WebSocket sync
⏳ MinIO/S3 - Image uploads (6 endpoints affected)
⏳ SMTP - Email verification, password reset
```

### What Requires Code Changes (This Plan)
```
🔧 Phase 1: 6 files - Remove mock data (2-3 hours)
🔧 Phase 2: 8 files - Implement business logic (1-2 days)
🔧 Phase 3: 6 files - Update stub modules (1 hour)
🔧 Phase 4: 15 files - Clean up comments (30 min)
```

---

## Recommendation

**For Flutter Team:**
1. **Start integration NOW** using the `/docs` endpoint
2. **Use mock data** from your Flutter side for UI development
3. **Wait for Phase 1 completion** before testing image uploads
4. **Wait for Phase 2 completion** before testing email/verification flows
5. **Full integration testing** requires PostgreSQL + Redis + MinIO running

**For Backend Team:**
1. Complete Phase 1 in current session (critical mock data fixes)
2. Schedule Phase 2 for next sprint (business logic)
3. Phase 3-4 can be done in parallel with Flutter development
4. Infrastructure setup (PostgreSQL, Redis, MinIO) should happen ASAP

---

## Quick Win: What I Can Fix RIGHT NOW

I can fix all **Phase 1 (P0) issues** immediately:
- Replace mock URLs with proper storage utility calls
- Remove hardcoded dimensions
- Ensure image_urls are properly populated
- Fix payment screenshot placeholder

This will make all image/file upload endpoints production-ready (pending MinIO/S3 configuration).

**Should I proceed with Phase 1 fixes now?**
