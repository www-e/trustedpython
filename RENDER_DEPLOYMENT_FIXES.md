# Render Deployment Fixes - March 25, 2026

## Problem Identified

Render was deploying with **Python 3.14.3**, which has breaking changes in the `typing` module that cause SQLAlchemy 2.0.36 to fail with:

```
TypeError: descriptor '__getitem__' requires a 'typing.Union' object but received a 'tuple'
```

This error occurs when using `Mapped[str | None]` syntax in SQLAlchemy models.

## Fixes Applied

### 1. Removed Unnecessary Files
- ❌ **Deleted `Procfile`** - Not needed for Render (uses Start Command directly)
- ❌ **Deleted `start.sh`** - Causing timeout issues; migrations should run separately

### 2. Fixed Python Version Specification
- ✅ **Updated `runtime.txt`** to use correct format:
  ```
  3.12.0
  ```
  
  Note: Use format `3.X.X` not `python-3.X.X`

### 3. Updated Dependencies
- ✅ **Updated `requirements.txt`** - Changed SQLAlchemy to use version `>=2.0.37` for better Python 3.14 compatibility:
  ```txt
  sqlalchemy[asyncio]>=2.0.37
  ```

### 4. Created render.yaml (Infrastructure as Code)
- ✅ **Added `render.yaml`** - Auto-configures your service on Render
- Includes: web service config, environment variables, health checks, auto-deploy

## Correct Render Configuration

### Option A: Using render.yaml (Recommended - One Click!)

1. Push all changes to GitHub
2. Go to https://render.com
3. Click **"New +"** → **"Blueprint"**
4. Connect your repository: `trustedpython`
5. Render auto-detects `render.yaml` and configures everything
6. In Dashboard, verify/set these secrets:
   - `SECRET_KEY` (auto-generated)
   - `JWT_SECRET_KEY` (auto-generated)
   - `DATABASE_URL` (add your Neon URL)
   - `REDIS_URL` (add your Upstash URL)

**Done!** Auto-deploy is now enabled. Every push to `main` triggers a deploy.

### Option B: Manual Configuration

When deploying on Render manually, use these exact settings:

| Field | Value |
|-------|-------|
| **Name** | `trustedpython` |
| **Branch** | `main` |
| **Region** | `oregon` |
| **Root Directory** | *(leave empty)* |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free (to start) or Starter ($7/mo) |
| **Auto-Deploy** | On (commits to `main`) |
| **Health Check** | `/health` |

## Environment Variables

Add these in Render Dashboard:

```
APP_NAME=Gaming Marketplace
APP_VERSION=0.1.0
DEBUG=false
SECRET_KEY=<generate-random-32-characters>
DATABASE_URL=<your-neon-postgresql-url>
REDIS_URL=<your-upstash-redis-url>
JWT_SECRET_KEY=<generate-random-32-characters>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=*
```

## Deployment Steps

### 1. Commit and Push Fixes
```bash
git add .
git commit -m "Fix Render deployment: Python version, render.yaml, and SQLAlchemy compatibility"
git push origin main
```

### 2. Deploy on Render

**Option A: Using render.yaml (Recommended)**
1. Go to https://render.com
2. Click **"New +"** → **"Blueprint"**
3. Connect your repository: `trustedpython`
4. Render auto-configures everything from `render.yaml`
5. In Dashboard, set these secrets:
   - `DATABASE_URL` (your Neon PostgreSQL URL)
   - `REDIS_URL` (your Upstash Redis URL)

**Option B: Manual Configuration**
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: `trustedpython`
4. Configure with settings in table above
5. Add environment variables manually

### 3. Run Database Migrations

After first deployment, run migrations manually:

**Option A: Render Dashboard**
- Go to your service → "Shell" tab
- Run: `alembic upgrade head`

**Option B: Add preDeployCommand to render.yaml**
The `render.yaml` can include a preDeployCommand for auto-migrations (coming in next update).

## Verification

After deployment:

1. ✅ Check logs: Should see "🚀 Gaming Marketplace v0.1.0 starting..."
2. ✅ Test health: `https://trustedpython.onrender.com/health`
3. ✅ Test API docs: `https://trustedpython.onrender.com/docs`
4. ✅ Test root: `https://trustedpython.onrender.com/`

## Troubleshooting

### If Python 3.14 is still being used:

1. **Clear Build Cache** in Render dashboard
2. **Redeploy** after clearing cache
3. If still failing, upgrade SQLAlchemy further: `sqlalchemy>=2.0.40`

### Alternative: Fix Models for Python 3.14 Compatibility

If the Python version fix doesn't work, update models to use `Optional` instead of `|`:

**Before (causes error in Python 3.14):**
```python
username: Mapped[str | None] = mapped_column(String(50))
```

**After (compatible with all versions):**
```python
from typing import Optional
username: Mapped[Optional[str]] = mapped_column(String(50))
```

Files that may need updates:
- `app/models/user.py`
- `app/models/listing.py`
- `app/models/deal.py`

## Files Changed

| File | Action | Reason |
|------|--------|--------|
| `Procfile` | Deleted | Not needed for Render |
| `start.sh` | Deleted | Causing timeouts, migrations run separately |
| `runtime.txt` | Updated | Fixed Python version format (`3.12.0`) |
| `requirements.txt` | Updated | SQLAlchemy version for compatibility (`>=2.0.37`) |
| `render.yaml` | Created | Infrastructure as Code for auto-deploy |
| `RENDER_DEPLOYMENT_FIXES.md` | Created | This documentation file |

## Next Steps

1. Push all changes to GitHub
2. Deploy on Render with correct configuration
3. Run migrations manually via Shell
4. Test all endpoints
5. Monitor logs for any issues
