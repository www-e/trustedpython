# Backend Development Setup (Windows)

## Prerequisites
- Python 3.8+ installed (verify: `python --version`)
- Git for Windows
- PostgreSQL for Windows

## Quick Start (Windows)

```cmd
# Clone repository
git clone <repository-url>
cd trustedpython

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env from example
copy .env.example .env

# Edit .env with your values (especially SECRET_KEY and DATABASE_URL)
notepad .env

# Run development server
uvicorn main:app --reload --port 8000
```

API available at: http://localhost:8000
Interactive docs: http://localhost:8000/docs

## Development Commands (Windows)

```cmd
# Activate environment
.\venv\Scripts\activate

# Install new dependencies
pip install package-name
pip freeze > requirements.txt

# Run development server
uvicorn main:app --reload

# Run with custom port
uvicorn main:app --reload --port 8001
```

## Environment Configuration
- Edit `.env` file with your database connection and secret key
- For local development, set `DEBUG=True`
- For CORS with Flutter: `ALLOWED_ORIGINS=*` (allows any Flutter port)
- Use PostgreSQL connection string: `postgresql+asyncpg://username:password@localhost:5432/dbname`

## API Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/token/refresh` - Refresh token
- `GET /auth/me` - Get current user
- `GET /users` - Get all users (admin only)
- `PUT /users/{id}/approve` - Approve user (admin only)
- `PUT /users/profile` - Update profile