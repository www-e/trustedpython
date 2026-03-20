# Deployment Guide

## 🚀 Deployment Overview

**Target:** Contabo VPS
**Stack:** Self-hosted (PostgreSQL, Redis, FastAPI, Celery, OneSignal, R2)

**Deployment Strategy:**
- GitHub Actions CI/CD
- Docker containers
- Automated testing and deployment

---

## 🖥️ Contabo VPS Setup

### 1. Initial Server Configuration

```bash
# Connect to your Contabo VPS
ssh root@your-contabo-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create non-root user
adduser marketplace
usermod -aG docker marketplace

# Create project directory
mkdir -p /home/marketplace/app
chown marketplace:marketplace /home/marketplace/app
```

### 2. Firewall Configuration

```bash
# Install UFW
apt install ufw -y

# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow WebSocket (if using separate port)
ufw allow 8001/tcp

# Enable firewall
ufw enable
ufw status
```

### 3. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Obtain certificate
certbot certonly --standalone -d api.marketplace.com

# Certificate location:
# /etc/letsencrypt/live/api.marketplace.com/fullchain.pem
# /etc/letsencrypt/live/api.marketplace.com/privkey.pem
```

---

## 🐳 Production Docker Setup

### docker-compose.prod.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: marketplace_postgres
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - marketplace_network

  redis:
    image: redis:7-alpine
    container_name: marketplace_redis
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - marketplace_network

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: marketplace_backend
    restart: always
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    env_file:
      - .env.prod
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./logs:/app/logs
      - ./certs:/app/certs:ro
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    networks:
      - marketplace_network

  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: marketplace_celery_worker
    restart: always
    command: celery -A app.tasks.celery_app worker --loglevel=info
    env_file:
      - .env.prod
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - marketplace_network

  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: marketplace_celery_beat
    restart: always
    command: celery -A app.tasks.celery_app beat --loglevel=info
    env_file:
      - .env.prod
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - marketplace_network

  nginx:
    image: nginx:alpine
    container_name: marketplace_nginx
    restart: always
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    networks:
      - marketplace_network

volumes:
  postgres_data:
  redis_data:

networks:
  marketplace_network:
    driver: bridge
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application
COPY ./app ./app

# Create logs directory
RUN mkdir -p /app/logs

# Non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔧 Nginx Configuration

### nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name api.marketplace.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.marketplace.com;

        # SSL certificates
        ssl_certificate /etc/letsencrypt/live/api.marketplace.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/api.marketplace.com/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Logging
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        # Client body size limit (for file uploads)
        client_max_body_size 10M;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket endpoint
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 86400;
        }

        # Health check
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
```

---

## 🔐 Environment Configuration

### .env.prod

```bash
# Application
APP_NAME=Gaming Marketplace
APP_ENV=production
DEBUG=false
SECRET_KEY=your-super-secret-key-change-this

# Server
HOST=0.0.0.0
PORT=8000

# Database
DB_USER=marketplace_user
DB_PASSWORD=your-strong-password-here
DB_NAME=marketplace_db
DB_HOST=postgres
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Cloudflare R2
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=marketplace-files
R2_PUBLIC_URL=https://cdn.marketplace.com

# OneSignal
ONESIGNAL_APP_ID=your-onesignal-app-id
ONESIGNAL_API_KEY=your-onesignal-api-key

# CORS
CORS_ORIGINS=https://marketplace.com,https://www.marketplace.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml

name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install pytest pytest-asyncio

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Contabo
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.CONTABO_HOST }}
          username: ${{ secrets.CONTABO_USER }}
          key: ${{ secrets.CONTABO_SSH_KEY }}
          script: |
            cd /home/marketplace/app

            # Pull latest code
            git pull origin main

            # Build and restart containers
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d --build

            # Run migrations
            docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

            # Clean up old images
            docker image prune -af

      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment to production completed!'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
        if: always()
```

---

## 🗄️ Database Setup & Backups

### Initial Setup

```bash
# Connect to running PostgreSQL container
docker exec -it marketplace_postgres psql -U marketplace_user -d marketplace_db

# Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  # For full-text search

# Exit
\q
```

### Automated Backups

```bash
# /home/marketplace/backup.sh

#!/bin/bash

BACKUP_DIR="/home/marketplace/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/marketplace_$DATE.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump database
docker exec marketplace_postgres pg_dump -U marketplace_user marketplace_db | gzip > $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "marketplace_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

### Cron Job

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /home/marketplace/backup.sh >> /home/marketplace/backup.log 2>&1
```

---

## 📊 Monitoring & Logging

### Log Rotation

```bash
# /etc/logrotate.d/marketplace

/home/marketplace/app/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 marketplace marketplace
    sharedscripts
    postrotate
        docker-compose -f /home/marketplace/app/docker-compose.prod.yml exec backend logrotate /etc/logrotate.d/python
    endscript
}
```

### Health Check Endpoint

```python
# api/health.py

@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Health check endpoint"""

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        await redis.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": db_status,
            "redis": redis_status,
        }
    }
```

---

## 🚀 Deployment Steps

### Initial Deployment

```bash
# 1. Clone repository
git clone <your-repo-url> /home/marketplace/app
cd /home/marketplace/app

# 2. Create environment file
cp .env.prod.example .env.prod
nano .env.prod  # Edit with your values

# 3. Create nginx config
cp nginx.conf.example nginx.conf

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Wait for services to start
sleep 10

# 6. Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 7. Create admin user
docker-compose -f docker-compose.prod.yml exec backend python -c "
import asyncio
from app.core.security import create_password_hash
from app.models.user import User, UserRole

async def create_admin():
    from app.database import async_session_maker
    async with async_session_maker() as db:
        admin = User(
            phone='+201234567890',
            hashed_password=create_password_hash('your-admin-password'),
            username='admin',
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        await db.commit()
        print('Admin user created')

asyncio.run(create_admin())
"

# 8. Check status
docker-compose -f docker-compose.prod.yml ps

# 9. View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Updating Production

```bash
# Pull latest code
cd /home/marketplace/app
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Run any new migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Rollback

```bash
# Revert to previous commit
cd /home/marketplace/app
git log --oneline -10  # Find commit hash
git checkout <previous-commit-hash>

# Restart services
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🔍 Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# View logs
docker-compose -f docker-compose.prod.yml logs postgres

# Restart database
docker-compose -f docker-compose.prod.yml restart postgres
```

#### Redis Connection Failed

```bash
# Check Redis
docker ps | grep redis

# Test connection
docker exec -it marketplace_redis redis-cli ping

# Restart Redis
docker-compose -f docker-compose.prod.yml restart redis
```

#### Celery Tasks Not Running

```bash
# Check worker status
docker-compose -f docker-compose.prod.yml logs celery_worker

# Restart worker
docker-compose -f docker-compose.prod.yml restart celery_worker

# Check registered tasks
docker exec marketplace_celery_worker celery -A app.tasks.celery_app inspect registered
```

#### High Memory Usage

```bash
# Check container stats
docker stats

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Clear Redis cache
docker exec marketplace_redis redis-cli FLUSHDB
```

---

## 📚 Related Documentation

- [Architecture Design](../02-Architecture-Design.md) - Overall system architecture
- [API Structure](./API-Structure.md) - API endpoints
- [Development Workflow](../workflow/Development-Workflow.md) - Local development setup

---

**Last Updated**: 2026-03-14
**Version**: 0.1.0
