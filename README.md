# Game Account Marketplace API

A secure marketplace for buying and selling gaming accounts, built with FastAPI.

## Features

- **Authentication**: JWT-based auth with email verification, password reset, and session management
- **Buyer Flow**: Browse accounts, create deals, submit payments, select mediators
- **Seller Flow**: Create/manage listings, upload images, track analytics
- **Chat**: Real-time messaging via WebSockets with Redis pub/sub sync
- **Notifications**: Real-time notifications via WebSockets
- **Security**: 2FA (TOTP), trusted devices, login history, account freeze, security scoring
- **Admin Panel**: User management, listing moderation, deal oversight, mediator management, reports, content management
- **Profile Management**: User profiles, listing management, avatar uploads
- **Home Feed**: Personalized feed, featured accounts, search, categories, FAQ, promo banners

## Tech Stack

| Component | Technology |
|---|---|
| **Framework** | FastAPI 0.109.0 |
| **Server** | Uvicorn 0.27.0 |
| **Database** | PostgreSQL 15 (async via asyncpg) |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migrations** | Alembic 1.13 |
| **Cache/Broker** | Redis 7 |
| **Task Queue** | Celery 5.3.6 |
| **Object Storage** | MinIO / S3 |
| **Auth** | python-jose, passlib (bcrypt), pyotp (2FA) |
| **Validation** | Pydantic v2 |

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15
- Redis 7
- MinIO (optional, for file storage)

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your database/redis credentials

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Makefile Commands

```bash
make install     # Install dependencies
make dev         # Run development server
make test        # Run tests with coverage
make lint        # Run linting (flake8, mypy)
make format      # Format code (black, isort)
make clean       # Clean Python cache and build files
```

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /logout` - User logout
- `POST /refresh-token` - Refresh access token
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password
- `POST /verify-email` - Email verification
- `GET /me` - Get current user

### Home Feed (`/api/v1/home`)
- `GET /feed` - Personalized feed
- `GET /featured` - Featured accounts
- `GET /categories` - Category list
- `GET /promo` - Promo banners
- `GET /faq` - FAQ items
- `GET /search` - Search listings
- `GET /games` - Game catalog
- `GET /games/{gameId}/accounts` - Accounts for a game

### Profile (`/api/v1/profile`)
- `GET /me` - Current user profile
- `GET /me/stats` - User statistics
- `GET /me/trade-history` - Trade history
- `PUT /update` - Update profile
- `POST /avatar` - Upload avatar
- `GET /{userId}` - Public profile
- `GET /listings` - User's listings
- `POST /listings` - Create listing
- `GET /listings/{id}` - Listing detail
- `PUT /listings/{id}` - Update listing
- `DELETE /listings/{id}` - Delete listing
- `PUT /listings/{id}/status` - Update listing status

### Security (`/api/v1/security`)
- `POST /enable-2fa` - Enable 2FA
- `POST /verify-2fa` - Verify 2FA code
- `POST /disable-2fa` - Disable 2FA
- `GET /login-history` - Login history
- `GET /score` - Security score
- `GET /settings` - Security settings
- `PUT /settings` - Update security settings
- `POST /change-password` - Change password
- `POST /freeze-account` - Freeze account
- `POST /unfreeze-account` - Unfreeze account
- `POST /logout-all` - Logout all sessions
- `POST /report-suspicious` - Report suspicious activity
- `GET /audit-log` - Audit log

### Sell (`/api/v1/sell`)
- `POST /listings` - Create listing
- `POST /listings/preview` - Preview listing
- `GET /listings/{listing_id}` - Listing detail
- `PUT /listings/{listing_id}` - Update listing
- `POST /listings/{listing_id}/publish` - Publish listing
- `POST /listings/{listing_id}/unpublish` - Unpublish listing
- `GET /categories` - Category list
- `GET /games` - Game list
- `POST /upload-image` - Upload listing image
- `GET /analytics` - Seller analytics

### Buy (`/api/v1/buy`)
- `GET /accounts` - Browse accounts
- `GET /accounts/{id}` - Account detail
- `GET /accounts/{id}/similar` - Similar accounts
- `POST /deals/` - Create deal
- `GET /deals/{id}` - Deal detail
- `PUT /deals/{id}/status` - Update deal status
- `GET /deals/{id}/payment/status` - Payment status
- `POST /deals/{id}/payment` - Submit payment
- `POST /deals/{id}/payment/confirm` - Confirm payment
- `POST /deals/{id}/payment/reject` - Reject payment
- `GET /mediators/` - List mediators
- `GET /mediators/{id}` - Mediator detail
- `GET /mediators/{id}/reviews` - Mediator reviews
- `GET /deals/my` - My deals

### Chat (`/api/v1/chat`)
- `GET /rooms` - List rooms
- `GET /rooms/{id}` - Room detail
- `GET /rooms/{id}/messages` - Room messages
- `POST /rooms/{id}/read` - Mark as read
- `DELETE /rooms/{id}` - Leave room
- `POST /rooms/{id}/messages` - Send message
- `POST /upload` - Upload attachment
- `DELETE /messages/{message_id}` - Delete message
- `GET /unread-count` - Unread count
- `GET /ws` - WebSocket connection

### Notifications (`/api/v1/notifications`)
- `GET /` - List notifications
- `GET /{id}` - Notification detail
- `POST /{id}/read` - Mark as read
- `POST /read-all` - Mark all as read
- `GET /unread-count` - Unread count
- `DELETE /{id}` - Delete notification
- `GET /settings` - Notification settings
- `PUT /settings` - Update settings
- `GET /ws` - WebSocket connection
- `POST /internal/create` - Create notification (internal)

### Admin (`/api/v1/admin`)
- `GET /dashboard/stats` - Dashboard stats
- `GET /dashboard/analytics` - Analytics
- `GET /users` - User list
- `GET /users/search` - Search users
- `GET /users/{id}` - User detail
- `POST /users/{id}/ban` - Ban user
- `POST /users/{id}/verify` - Verify user
- `POST /users/{id}/suspend` - Suspend user
- `POST /users/{id}/unsuspend` - Unsuspend user
- `GET /blocked-users` - Blocked users
- `POST /blocked-users/{id}/unblock` - Unblock user
- `GET /listings/pending` - Pending listings
- `POST /listings/{id}/approve` - Approve listing
- `POST /listings/{id}/reject` - Reject listing
- `DELETE /listings/{id}` - Delete listing
- `GET /deals` - Deals list
- `GET /deals/{id}` - Deal detail
- `POST /deals/{id}/resolve` - Resolve deal
- `POST /deals/{id}/cancel` - Cancel deal
- `GET /mediators` - Mediators list
- `GET /mediators/{id}` - Mediator detail
- `GET /mediators/applications` - Mediator applications
- `POST /mediators/applications/{id}/approve` - Approve application
- `POST /mediators/applications/{id}/reject` - Reject application
- `POST /mediators/{id}/suspend` - Suspend mediator
- `POST /mediators/{id}/verify` - Verify mediator
- `POST /mediators/{id}/update-tier` - Update mediator tier
- `GET /reports` - Reports list
- `GET /reports/{id}` - Report detail
- `POST /reports/{id}/resolve` - Resolve report
- `GET /categories` - Categories
- `POST /categories` - Create category
- `GET /faq` - FAQ list
- `POST /faq` - Create FAQ
- `GET /games` - Games
- `POST /games` - Create game
- `PUT /games/{id}` - Update game
- `GET /promo-banners` - Promo banners
- `POST /promo-banners` - Create promo banner

## Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── api/
│   └── v1/                 # API v1 endpoints
│       ├── auth/           # Authentication routes
│       ├── home/           # Home feed routes
│       ├── profile/        # Profile routes
│       ├── security/       # Security routes
│       ├── sell/           # Seller routes
│       ├── buy/            # Buyer routes
│       ├── chat/           # Chat REST + WebSocket routes
│       ├── notifications/  # Notification REST + WebSocket routes
│       └── admin/          # Admin panel routes
├── core/                   # Core config, database, redis, security
├── models/                 # SQLAlchemy ORM models
├── schemas/                # Pydantic request/response schemas
├── services/               # Business logic layer
├── tasks/                  # Celery background tasks
└── utils/                  # Utility modules
```

## Configuration

All configuration is managed through environment variables or the `.env` file. See `.env.example` for all available options.

Key settings:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key
- `MINIO_ENDPOINT` - MinIO/S3 endpoint
- `SMTP_*` - Email configuration

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```


qwen --resume ec3eb491-4131-4ccf-8ba1-8ad5b0c7aecf