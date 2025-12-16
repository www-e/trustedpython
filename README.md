# TrustedPython Backend

A secure, scalable backend API with role-based authentication for Flutter frontend integration.

## Features

- **Role-based Access Control**: Admin, Mediator, and Regular User roles
- **User Approval Workflow**: Mediators require admin approval
- **JWT Authentication**: Secure token-based authentication
- **User Registration & Login**: Complete auth system
- **Profile Management**: Update user information
- **PostgreSQL Database**: Robust data storage
- **FastAPI Framework**: Modern Python web framework with automatic API documentation
- **Production Ready**: Ready for deployment on Render (dev) and Coolify (prod)

## Architecture

```
app/
├── auth/           # Authentication utilities and routers
│   ├── __init__.py
│   ├── utils.py    # JWT utilities and security helpers
│   └── routers.py  # Authentication endpoints
├── users/          # User management
│   ├── __init__.py
│   └── routers.py  # User management endpoints
├── models/         # Data models
│   ├── __init__.py
│   └── user.py     # User-related models
├── database/       # Database configuration
│   ├── __init__.py
│   └── core.py     # Database engine and session management
├── core/           # Core application utilities
├── utils/          # General utilities
```

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL database
- pip package manager

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd trustedpython
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your specific configuration
```

5. **Run the application**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

The API automatically generates interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Authentication Flow

1. **Registration**: Users register with username, password, and additional info
2. **Auto-approval**: Regular users are auto-approved
3. **Pending approval**: Mediators require admin approval
4. **Login**: Authenticate with credentials to receive JWT tokens
5. **Access**: Use JWT tokens to access protected endpoints

## User Roles

- **Admin**: Full access, can approve/reject users
- **Mediator**: Requires approval before access, specialized permissions
- **Regular User**: Auto-approved, standard permissions

## Environment Variables

Required environment variables in `.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/trustedpython_dev

# JWT Configuration
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Configuration
DEBUG=True
LOG_LEVEL=info
PORT=8000
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Authenticate user
- `POST /auth/token/refresh` - Refresh access token
- `GET /auth/me` - Get current user info

### User Management (Admin Only)
- `GET /users` - Get all users
- `GET /users/{id}` - Get specific user
- `PUT /users/{id}/approve` - Approve/reject user

### Profile
- `PUT /users/profile` - Update profile information

## Documentation

- [Flutter Integration Guide](docs/flutter_integration.md) - Detailed instructions for Flutter frontend integration
- [API Access for Flutter Team](docs/api_access_for_flutter.md) - How to access and use backend API documentation
- [Development Setup](docs/development_setup.md) - Backend development environment setup
- [Deployment Guide](docs/deployment.md) - Instructions for deploying to Render (dev) and Coolify (prod)

## Security Considerations

- Bcrypt password hashing
- JWT token authentication with proper expiration
- Rate limiting to prevent abuse
- Input validation on all endpoints
- SQL injection prevention through ORM
- Secure secret management through environment variables

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8
```

## License

[Specify your license here]