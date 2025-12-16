# Deployment Guide

## Development (Render)

1. Push code to GitHub/GitLab
2. Create Render Web Service
3. Set environment variables:
   ```
   DATABASE_URL=your_neon_postgres_connection
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_ORIGINS=*
   ```
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Note**: The application automatically converts standard PostgreSQL URLs to asyncpg format, so Neon connection strings work directly.

## Production (Coolify)

1. Set up Coolify server on Contabo
2. Create application with Git repository
3. Configure environment variables:
   ```
   DATABASE_URL=your_contabo_postgres_connection
   SECRET_KEY=your-secret-key
   DEBUG=False
   ```
4. Use Dockerfile or Python build pack
5. Set health check: `/health`

## Environment Variables

Required:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret (at least 32 random characters)
- `DEBUG`: True for dev, False for prod

CORS Configuration:
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
  - For development: `*` (allows all origins)
  - For production: `http://your-flutter-app.com,https://your-flutter-app.com`

Optional:
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Default 30
- `REFRESH_TOKEN_EXPIRE_DAYS`: Default 7
- `LOG_LEVEL`: Default 'info'