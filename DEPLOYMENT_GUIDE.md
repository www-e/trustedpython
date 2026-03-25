# Production Deployment Guide - Render

## Pre-Deployment Checklist ✅

- [x] All environment variables configured in Render
- [x] Database migration created and tested
- [x] Security best practices implemented
- [x] Health checks configured
- [x] Error handling in place
- [x] Logging configured

## Environment Variables (Configure in Render Dashboard)

```
APP_NAME=Gaming Marketplace
APP_VERSION=0.1.0
DEBUG=false
SECRET_KEY=<generate-strong-random-key>
DATABASE_URL=<your-neon-postgresql-url>
REDIS_URL=<your-upstash-redis-url>
JWT_SECRET_KEY=<generate-random-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=*
```

## Deploy to Render

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Production-ready deployment configuration"
git push origin main
```

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `trustedpython` (or your preferred name)
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: *(leave empty)*
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free (to start) or Starter ($7/mo)

### Step 3: Verify Deployment

1. **Check Build Logs**: Should see `Build successful 🎉`
2. **Check Deploy Logs**: Should see application starting
3. **Test Health Endpoint**:
   ```bash
   curl https://gaming-marketplace.onrender.com/health
   ```
4. **Test API Docs**: Visit `https://gaming-marketplace.onrender.com/docs`
5. **Test Root Endpoint**: Visit `https://gaming-marketplace.onrender.com/`

## Post-Deployment Steps

1. **Run Migrations** (automatic via start.sh)
2. **Verify Database Connection**: Check logs for any database errors
3. **Test Authentication Flow**: Create a test user
4. **Monitor Performance**: Check Render metrics
5. **Set Up Error Tracking**: Consider Sentry for production error tracking

## Troubleshooting

### Build Fails
- Check requirements.txt for all dependencies
- Verify Python version compatibility
- Check build logs for specific errors

### Application Won't Start
- Verify environment variables are set
- Check database connection string
- Verify Redis connection string
- Check application logs

### Database Connection Errors
- Verify DATABASE_URL format
- Check Neon database status
- Verify IP whitelist (if applicable)

### High Memory Usage
- Monitor database connection pool size
- Check for memory leaks
- Consider upgrading Render tier

## Scaling Considerations

### Current Configuration
- **Workers**: 1 (WEB_CONCURRENCY=1)
- **Database**: Neon PostgreSQL (Serverless)
- **Cache**: Upstash Redis

### When to Scale
- **Request rate > 100 req/min**: Upgrade to Standard tier
- **Database connections > 20**: Upgrade Neon plan
- **Response time > 500ms**: Add caching or optimize queries

## Monitoring

### Key Metrics to Watch
- **Response Time**: Should be < 200ms for API calls
- **Error Rate**: Should be < 1%
- **Uptime**: Should be > 99.9%
- **Database Connections**: Monitor pool usage

### Logs
- Application logs: Available in Render dashboard
- Database logs: Available in Neon dashboard
- Redis logs: Available in Upstash dashboard

## Security Notes

- ✅ All secrets stored as environment variables
- ✅ Password hashing with bcrypt
- ✅ JWT authentication
- ✅ CORS configured
- ✅ SQL injection protection (via ORM)
- ✅ Input validation (via Pydantic)

## Backups

- **Database**: Neon handles automatic backups
- **Redis**: Upstash handles persistence
- **Code**: GitHub repository

## Rollback Plan

If deployment fails:
1. Revert to previous commit in GitHub
2. Render will auto-deploy the previous version
3. Run database migration if needed: `alembic downgrade -1`
