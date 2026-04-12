# Backend Deployment Guide - Getting This Project Fully Operational

**Project:** Game Account Marketplace API  
**Framework:** FastAPI + SQLAlchemy (async) + PostgreSQL + Redis + MinIO  
**Status:** Code is 100% complete and verified. Infrastructure is all that's missing.

---

## What You Need (Prerequisites)

| Component | Purpose | Why It's Required |
|---|---|---|
| **PostgreSQL 15+** | Primary database | All data: users, listings, deals, chats, notifications |
| **Redis 7+** | Cache + sessions + WebSocket sync | Token storage, caching, real-time messaging |
| **MinIO or S3** | File storage | Image uploads (avatars, listing photos, payment proofs) |
| **SMTP Server** | Email delivery | Email verification, password reset emails |
| **Python 3.11+** | Runtime | Already installed ✅ |
| **Docker (optional)** | Run everything in containers | Easiest way to get all services running |

---

## Step 1: Install Docker (Easiest Path)

If you don't have Docker installed:

### Windows
```powershell
# Download Docker Desktop
# Visit: https://www.docker.com/products/docker-desktop/
# Install and restart your computer

# Verify installation
docker --version
docker-compose --version
```

### Or Install Services Individually (No Docker)
```powershell
# PostgreSQL
# Download: https://www.postgresql.org/download/windows/
# Install, remember your postgres password

# Redis
# Download: https://github.com/microsoftarchive/redis/releases
# Or use WSL: sudo apt install redis-server

# MinIO
# Download: https://min.io/download
# Run: minio.exe server C:\minio-data --console-address ":9001"
```

---

## Step 2: Configure the .env File

Your `.env` file exists but needs real values. Here's what to change:

```bash
# Open your .env file
notepad .env
```

### Critical Values to Set

```env
# =====================
# 1. DATABASE (PostgreSQL)
# =====================

# If using Docker Compose (services run as containers):
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/game_marketplace

# If running PostgreSQL locally on your machine:
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/gamemarket

# =====================
# 2. REDIS
# =====================

# If using Docker Compose:
REDIS_URL=redis://redis:6379/0

# If running Redis locally:
REDIS_URL=redis://localhost:6379/0

# =====================
# 3. JWT SECRET (Generate a real one)
# =====================

# Generate a secure random key:
# Python one-liner: python -c "import secrets; print(secrets.token_hex(64))"
# Then paste it here:
JWT_SECRET_KEY=<paste-your-generated-key-here>

# =====================
# 4. SECRET KEY (Generate a real one)
# =====================

SECRET_KEY=<paste-another-generated-key-here>

# =====================
# 5. MINIO / S3 STORAGE
# =====================

# If using Docker Compose (MinIO container):
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=game-marketplace
MINIO_SECURE=False

# If using AWS S3:
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_ACCESS_KEY=<your-aws-access-key>
MINIO_SECRET_KEY=<your-aws-secret-key>
MINIO_BUCKET=your-bucket-name
MINIO_SECURE=True

# If using local MinIO:
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=game-marketplace
MINIO_SECURE=False

# =====================
# 6. SMTP EMAIL (For verification & password reset)
# =====================

# Using Gmail (requires App Password):
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
EMAIL_FROM=noreply@gamemarketplace.com
EMAIL_FROM_NAME=Game Account Marketplace

# Using SendGrid (recommended for production):
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<your-sendgrid-api-key>

# =====================
# 7. CORS (Add your frontend URL)
# =====================

# Development:
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Production (add your Flutter web URL if applicable):
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]

# =====================
# 8. ENVIRONMENT
# =====================

# Development:
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Production:
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## Step 3: Start Infrastructure

### Option A: Docker Compose (Recommended - All in One Command)

```powershell
# Navigate to project directory
cd D:\pythontrusted

# Start all services (PostgreSQL, Redis, MinIO, Celery, Flower)
docker-compose up -d

# Wait 30 seconds for PostgreSQL to initialize
timeout /t 30

# Check all services are healthy
docker-compose ps

# You should see:
# game_marketplace_app     - running
# game_marketplace_db      - running (healthy)
# game_marketplace_redis   - running (healthy)
# game_marketplace_minio   - running (healthy)
# game_marketplace_celery_worker - running
# game_marketplace_celery_beat   - running
# game_marketplace_flower        - running
```

### Option B: Manual Setup (Without Docker)

```powershell
# 1. Start PostgreSQL
# (It should auto-start after installation)
# Verify:
psql -U postgres -c "SELECT version();"

# 2. Create the database
psql -U postgres -c "CREATE DATABASE gamemarket;"

# 3. Start Redis
# If installed as Windows service:
redis-server --service-start
# Or if using WSL:
wsl sudo systemctl start redis-server

# Verify Redis:
redis-cli ping
# Should return: PONG

# 4. Start MinIO
# Download minio.exe from https://min.io/download
minio.exe server C:\minio-data --console-address ":9001"

# Open browser: http://localhost:9001
# Login: minioadmin / minioadmin
# Create bucket named: game-marketplace
```

---

## Step 4: Initialize the Database

### Option A: Automatic (Docker Compose handles this)

```powershell
# The Docker CMD already runs: alembic upgrade head
# So tables are created automatically on first start
```

### Option B: Manual Migration

```powershell
# Activate your virtual environment
.\venv\Scripts\activate

# Run database migrations
alembic upgrade head

# You should see:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transaction.
# INFO  [alembic.runtime.migration] Running upgrade -> xxxxx, ...

# If you get "no revision files found", you need to create the first migration:
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

---

## Step 5: Start the Application

### Development Mode (With Auto-Reload)

```powershell
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO:     Will watch for changes in these directories: ['D:\\pythontrusted']
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Application startup complete.
```

### Production Mode (No Reload, Multiple Workers)

```powershell
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Step 6: Verify Everything Works

### Test 1: Health Check

```powershell
# Open browser or use curl:
curl http://localhost:8000/health

# Expected response (ALL should say "ok" / "healthy"):
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok"
}
```

### Test 2: API Documentation

```
Open browser: http://localhost:8000/docs

You should see the Swagger UI with all 130+ endpoints listed.
Click any endpoint → Try it out → Execute to test.
```

### Test 3: Register a User

```powershell
curl -X POST http://localhost:8000/api/v1/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"testuser\",\"email\":\"test@example.com\",\"phone\":\"+1234567890\",\"password\":\"TestPass123!\"}"

# Expected response (201 Created):
{
  "error_code": null,
  "message": "User registered successfully",
  "data": {
    "user": { ... },
    "access_token": "eyJ...",
    "refresh_token": "eyJ..."
  }
}
```

### Test 4: Login

```powershell
curl -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"testuser\",\"password\":\"TestPass123!\"}"

# Expected response (200 OK) with access_token and refresh_token
```

### Test 5: Browse Accounts (Requires DB data)

```powershell
curl http://localhost:8000/api/v1/buy/accounts

# Expected: {"data": {"accounts": [], "total": 0}} (empty, no data yet)
```

---

## Step 7: Create Admin User

```powershell
# Connect to PostgreSQL
psql -U postgres -d gamemarket

# Insert admin user (adjust password hash)
# First, generate a password hash using Python:
python -c "from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(ctx.hash('YourAdminPassword123!'))"

# Copy the hash output and use it in this SQL:
INSERT INTO users (id, username, email, phone, password_hash, is_email_verified, is_active, is_suspended, two_factor_enabled, login_notifications, is_frozen)
VALUES (
  gen_random_uuid(),
  'admin',
  'admin@gamemarketplace.com',
  '+0000000000',
  '$2b$12$<paste-your-hash-here>',
  true, true, false, false, true, false
);

# Verify:
SELECT username, email, is_active FROM users WHERE username = 'admin';
```

---

## Step 8: Seed Initial Data (Optional but Recommended)

### Create Initial Categories

```python
# Create a seed script: seed.py
import asyncio
from app.core.database import async_session_maker
from app.models.content import Category, Game

async def seed():
    async with async_session_maker() as db:
        # Add categories
        categories = [
            Category(name="Premium Accounts", slug="premium", icon="⭐"),
            Category(name="Starter Accounts", slug="starter", icon="🎮"),
            Category(name="Ranked Accounts", slug="ranked", icon="🏆"),
            Category(name="Smurf Accounts", slug="smurf", icon="🎭"),
        ]
        db.add_all(categories)

        # Add games
        games = [
            Game(name="Fortnite", slug="fortnite", icon_url=""),
            Game(name="Valorant", slug="valorant", icon_url=""),
            Game(name="League of Legends", slug="lol", icon_url=""),
            Game(name="Genshin Impact", slug="genshin", icon_url=""),
            Game(name="Apex Legends", slug="apex", icon_url=""),
            Game(name="Call of Duty", slug="cod", icon_url=""),
            Game(name="Overwatch 2", slug="overwatch", icon_url=""),
            Game(name="Counter-Strike 2", slug="cs2", icon_url=""),
        ]
        db.add_all(games)

        await db.commit()
        print("✅ Seed data created!")

asyncio.run(seed())
```

```powershell
# Run the seed script
python seed.py
```

---

## Step 9: Configure MinIO Bucket

```powershell
# Open MinIO Console: http://localhost:9001
# Login: minioadmin / minioadmin

# 1. Create Bucket
#    - Click "Buckets" → "Create Bucket"
#    - Name: game-marketplace
#    - Click "Create"

# 2. Set Bucket Policy (Public Read)
#    - Click the bucket → "Access Rules" → "Add Access Rule"
#    - Prefix: *
#    - Access: Read-Only
#    - Click "Save"

# 3. Verify Upload Works
#    - Open Swagger UI: http://localhost:8000/docs
#    - POST /api/v1/sell/upload-image
#    - Upload a test image
#    - Should return a real URL like: http://localhost:9000/game-marketplace/listings/...
```

---

## Step 10: Set Up Celery (Background Tasks)

Celery handles async tasks like sending emails, processing images, etc.

### If Using Docker Compose

```powershell
# Already running! Check status:
docker-compose ps celery_worker
docker-compose ps celery_beat
docker-compose ps flower

# Open Flower (Celery Monitoring Dashboard):
# http://localhost:5555
```

### If Running Manually

```powershell
# Terminal 1: Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4

# Terminal 2: Celery Beat (Scheduled Tasks)
celery -A app.tasks.celery_app beat --loglevel=info

# Terminal 3: Flower (Monitoring - Optional)
celery -A app.tasks.celery_app flower --port=5555
```

---

## Complete Architecture (How It All Connects)

```
┌─────────────────────────────────────────────────────────┐
│                    Flutter App / Web                     │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / WebSocket
                         ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI (Uvicorn) - Port 8000               │
│  ┌──────────┐  ┌─────────┐  ┌────────┐  ┌────────────┐ │
│  │   Auth   │  │  Home   │  │  Chat  │  │   Admin    │ │
│  └──────────┘  └─────────┘  └────────┘  └────────────┘ │
│  ┌──────────┐  ┌─────────┐  ┌────────┐  ┌────────────┐ │
│  │   Buy    │  │  Sell   │  │Profile │  │  Security  │ │
│  └──────────┘  └─────────┘  └────────┘  └────────────┘ │
└───────┬─────────────┬──────────────┬───────────────────┘
        │             │              │
        ▼             ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  PostgreSQL  │ │  Redis   │ │  MinIO / S3  │
│  (Port 5432) │ │(Port 6379)│ │ (Port 9000)  │
│              │ │          │ │              │
│ • Users      │ │ • Cache  │ │ • Avatars    │
│ • Listings   │ │ • Sessions│ │ • Photos    │
│ • Deals      │ │ • Pub/Sub│ │ • Payment   │
│ • Messages   │ │ • Celery │ │   Proofs     │
│ • Notifs     │ │   Broker │ │              │
└──────────────┘ └────┬─────┘ └──────────────┘
                      │
                      ▼
              ┌──────────────┐
              │    Celery    │
              │   Workers    │
              │              │
              │ • Send Email │
              │ • Process    │
              │   Images     │
              │ • Cleanup    │
              └──────────────┘
```

---

## Checklist: Before Going Live

- [ ] PostgreSQL running and database created
- [ ] Redis running and responding to ping
- [ ] MinIO bucket created and policy set to public read
- [ ] `.env` file configured with real values
- [ ] JWT_SECRET_KEY and SECRET_KEY are secure random strings (not defaults)
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Admin user created in database
- [ ] Categories and games seeded
- [ ] CORS origins configured with production URLs
- [ ] DEBUG=False in production
- [ ] SMTP configured for email delivery
- [ ] Health endpoint returns `"status": "healthy"`
- [ ] Swagger UI accessible at `/docs`
- [ ] Register endpoint creates real users
- [ ] Login endpoint returns real JWT tokens
- [ ] File upload returns real URLs (not mock)

---

## Troubleshooting

### "password authentication failed for user postgres"
```powershell
# Your DATABASE_URL password doesn't match PostgreSQL
# Fix: Update DATABASE_URL in .env with correct password
# Or reset PostgreSQL password:
psql -U postgres
ALTER USER postgres PASSWORD 'new_password';
```

### "Connection refused" on Redis
```powershell
# Redis isn't running
# Docker: docker-compose up -d redis
# Manual: redis-server
# Verify: redis-cli ping → should return PONG
```

### "Bucket not found" on upload
```powershell
# MinIO bucket doesn't exist
# Create it: http://localhost:9001 → Buckets → Create → game-marketplace
```

### "No module named 'xyz'"
```powershell
# Missing dependency
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Tables don't exist in database
```powershell
# Migrations haven't been run
.\venv\Scripts\activate
alembic upgrade head
```

### Server starts but returns 500 on every endpoint
```powershell
# Check health endpoint first
curl http://localhost:8000/health

# If database or redis shows "error":
# - Check .env DATABASE_URL and REDIS_URL are correct
# - Ensure services are actually running
# - Check Docker logs: docker-compose logs db redis
```

---

## Quick Start Commands (Copy-Paste Ready)

### Full Setup with Docker (Recommended)

```powershell
# 1. Clone / navigate to project
cd D:\pythontrusted

# 2. Activate environment
.\venv\Scripts\activate

# 3. Start all services
docker-compose up -d

# 4. Wait for database
timeout /t 30

# 5. Run migrations (if not auto-run)
alembic upgrade head

# 6. Verify health
curl http://localhost:8000/health

# 7. Open Swagger
start http://localhost:8000/docs

# 8. Done! 🎉
```

### Full Setup Without Docker

```powershell
# 1. Start PostgreSQL (should auto-start)
# 2. Start Redis: redis-server
# 3. Start MinIO: minio.exe server C:\minio-data --console-address ":9001"
# 4. Create bucket in MinIO console: http://localhost:9001
# 5. Activate environment: .\venv\Scripts\activate
# 6. Run migrations: alembic upgrade head
# 7. Start server: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 8. Open Swagger: start http://localhost:8000/docs
# 9. Done! 🎉
```

---

## Services Ports Summary

| Service | Port | URL |
|---|---|---|
| FastAPI App | 8000 | http://localhost:8000 |
| API Docs (Swagger) | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | postgresql://localhost:5432 |
| Redis | 6379 | redis://localhost:6379 |
| MinIO API | 9000 | http://localhost:9000 |
| MinIO Console | 9001 | http://localhost:9001 |
| Flower (Celery) | 5555 | http://localhost:5555 |
