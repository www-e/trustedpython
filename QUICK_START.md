# Quick Start Guide - Game Account Marketplace

## 🚀 Fastest Path to Running

### Option 1: Docker (Recommended)
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Start all services
docker-compose up -d

# 3. Run migrations
docker-compose exec app alembic upgrade head

# 4. Check health
curl http://localhost:8000/health

# Done! API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Option 2: Local Development
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env (update DATABASE_URL to use localhost)

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --reload

# Done! API at http://localhost:8000
```

## 📋 Essential Commands

### Using Make (Unix/Linux/macOS)
```bash
make help          # Show all commands
make dev           # Start development server
make test          # Run tests
make lint          # Check code quality
make format        # Format code
make up            # Start Docker services
make down          # Stop Docker services
make logs          # View logs
make db-upgrade    # Run migrations
```

### Using Docker Compose
```bash
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose restart            # Restart services
docker-compose logs -f app        # View app logs
docker-compose exec app bash      # Shell in app container
docker-compose exec db psql ...   # Database shell
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## 🔧 Configuration Checklist

Before running, update these in `.env`:

### Required (Must Change)
- [ ] `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] `JWT_SECRET_KEY` - Generate with same command
- [ ] `DATABASE_URL` - For Docker use default, for local use `postgresql+asyncpg://postgres:postgres@localhost:5432/game_marketplace`

### Optional (For Production)
- [ ] `MINIO_ACCESS_KEY` & `MINIO_SECRET_KEY` - Change from defaults
- [ ] `STRIPE_SECRET_KEY` - For payment processing
- [ ] `SMTP_*` settings - For email functionality
- [ ] `CORS_ORIGINS` - Add your frontend URL

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run with verbose output
pytest -v
```

## 📊 Monitoring

### Application Health
```bash
curl http://localhost:8000/health
```

### Celery Flower (Task Monitoring)
- URL: http://localhost:5555
- Shows: Active tasks, workers, task history

### MinIO Console (Object Storage)
- URL: http://localhost:9001
- Default credentials: minioadmin / minioadmin

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Permission Issues
```bash
# Fix file permissions on Unix
sudo chown -R $USER:$USER .

# Make setup script executable
chmod +x setup.sh
```

### Container Won't Start
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check logs
docker-compose logs
```

### Import Errors
```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

## 📚 Useful Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- Celery: https://docs.celeryproject.org/

### Project Files
- Full documentation: `README.md`
- Foundation details: `FOUNDATION_SUMMARY.md`
- API structure: `app/api/v1/`

### Environment Reference
- All variables: `.env.example`
- Configuration code: `app/core/config.py`

## 🎯 Development Workflow

1. **Feature Development**
   ```bash
   git checkout -b feature/your-feature
   # Make changes
   make test
   make format
   make lint
   git commit -m "Add feature"
   ```

2. **Database Changes**
   ```bash
   # Edit models in app/models/
   alembic revision --autogenerate -m "Add new table"
   alembic upgrade head
   ```

3. **API Development**
   ```bash
   # Add routes in app/api/v1/
   # Add schemas in app/schemas/
   # Add services in app/services/
   # Test with pytest
   ```

## 🔐 Security Notes

⚠️ **Production Checklist**:
- Change all default passwords
- Use strong SECRET_KEY (32+ chars)
- Enable HTTPS (nginx + Let's Encrypt)
- Set DEBUG=False
- Configure proper CORS origins
- Use production database
- Enable rate limiting
- Set up backups
- Configure firewall rules

## 📞 Support

- Check `README.md` for detailed documentation
- Review `FOUNDATION_SUMMARY.md` for architecture details
- Use `make help` for available commands
- Check logs: `docker-compose logs -f`

## ✨ You're Ready!

The foundation is complete. Start building your features:
- Add models in `app/models/`
- Create API routes in `app/api/v1/`
- Implement business logic in `app/services/`
- Add background tasks in `app/tasks/`

Happy coding! 🎮
