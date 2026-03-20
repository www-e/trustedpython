# 🚀 Phase 1 Setup Instructions

## Prerequisites

- Python 3.12+ installed
- Neon PostgreSQL account (https://neon.tech)
- Upstash Redis account (https://upstash.com)

---

## Step 1: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

---

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 3: Configure Environment Variables

1. **Get Neon PostgreSQL connection string:**
   - Go to https://neon.tech
   - Create a free account
   - Create a new project
   - Copy the connection string (use the "Connection string" format)
   - Format: `postgresql+asyncpg://user:pass@ep-xxx.region.aws.neon.tech/dbname`

2. **Get Upstash Redis URL:**
   - Go to https://upstash.com
   - Create a free account
   - Create a new Redis database
   - Copy the REST API URL
   - Format: `rediss://xxx.xxx.upstash.io:6379`

3. **Update `.env` file:**
   ```bash
   # Application
   APP_NAME=Gaming Marketplace
   APP_VERSION=0.1.0
   DEBUG=true
   SECRET_KEY=change-this-to-a-random-secret-key

   # Database (Neon PostgreSQL)
   DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.region.aws.neon.tech/marketplace

   # Redis (Upstash)
   REDIS_URL=rediss://xxx.xxx.upstash.io:6379

   # JWT Configuration
   JWT_SECRET_KEY=change-this-jwt-secret
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # CORS
   CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
   ```

---

## Step 4: Initialize Database

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create initial migration (optional - will do this in Phase 2)
# alembic revision --autogenerate -m "Initial migration"

# Run migrations (when ready)
# alembic upgrade head
```

---

## Step 5: Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_health.py

# Run with coverage (if installed)
# pip install pytest-cov
# pytest --cov=app --cov-report=html
```

---

## Step 6: Start Development Server

```bash
# Run using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run the app module
python -m app.main
```

---

## Step 7: Verify Installation

1. **Check API Documentation:**
   - Open http://localhost:8000/docs
   - You should see Swagger UI

2. **Check Root Endpoint:**
   - Open http://localhost:8000
   - You should see welcome message

3. **Check Health Endpoint:**
   - Open http://localhost:8000/api/v1/health
   - You should see: `{"status": "healthy", "version": "0.1.0"}`

4. **Run Tests:**
   ```bash
   pytest
   ```
   - All tests should pass

---

## What's Next?

**Phase 1 Complete!** ✓

You now have:
- ✅ Project structure with strict SOC pattern
- ✅ Core configuration system
- ✅ Database models (User model)
- ✅ Repository layer (base + user repository)
- ✅ API router structure
- ✅ Pytest infrastructure
- ✅ Alembic setup (ready for migrations)

**Ready for Phase 2:** User Authentication System
- Implement user registration
- Implement login with JWT
- Add user profile endpoints
- Create database migrations

---

## Troubleshooting

**Issue: Module not found errors**
```bash
# Make sure you're in the project directory
cd D:\python\trusted

# Make sure venv is activated
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
```

**Issue: Database connection errors**
- Check your `.env` file has correct DATABASE_URL
- Verify Neon database is active
- Check network connectivity

**Issue: Import errors**
```bash
# Make sure you're running from the project root
# Not from inside the app/ directory
```

---

## Project Structure

```
marketplace-backend/
├── app/
│   ├── api/              # API routers
│   ├── core/             # Config, security, deps
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── repositories/     # Data access layer
│   ├── db.py             # Database session
│   └── main.py           # FastAPI app
├── tests/                # Pytest tests
├── alembic/              # Database migrations
├── .env                  # Environment variables
├── requirements.txt      # Dependencies
└── SETUP.md             # This file
```



claude --resume d7a70048-8b39-4056-8d5f-f51af61b8131