"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.core.config import settings
from app.schemas.common import ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def cleanup(state: Any, app: FastAPI) -> None:
    """Cleanup function for shutdown."""
    pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """
    Application lifespan events.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up Game Account Marketplace API...")

    # Initialize database connection
    from app.core.database import init_db

    await init_db()
    logger.info("Database initialized")

    # Initialize Redis connection
    from app.core.redis import init_redis

    await init_redis()
    logger.info("Redis initialized")

    # Start Redis pub/sub listener for WebSocket sync
    from app.utils.redis_pubsub import start_redis_listener

    await start_redis_listener()
    logger.info("Redis pub/sub listener started")

    yield

    # Shutdown
    logger.info("Shutting down Game Account Marketplace API...")

    # Stop Redis pub/sub listener
    from app.utils.redis_pubsub import stop_redis_listener

    await stop_redis_listener()
    logger.info("Redis pub/sub listener stopped")

    # Close Redis connection
    from app.core.redis import close_redis

    await close_redis()
    logger.info("Redis connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Game Account Marketplace API - Buy and sell gaming accounts securely",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom middleware for request timing and logging
@app.middleware("http")
async def request_middleware(request: Request, call_next: Any) -> Any:
    """
    Middleware to add custom headers and log requests.
    """
    import time

    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-API-Version"] = "v1"

    # Log request
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )

    return response


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.create(
            error_code=f"HTTP_{exc.status_code}", message=exc.detail
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors.
    """
    # Format validation errors
    details: dict[str, list[str]] = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        if field not in details:
            details[field] = []
        details[field].append(error["msg"])

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.create(
            error_code="VALIDATION_ERROR", message="Request validation failed", details=details
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.create(
            error_code="INTERNAL_ERROR",
            message="An internal error occurred" if not settings.DEBUG else str(exc),
        ).model_dump(),
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    """
    from app.core.database import engine
    from app.core.redis import get_redis

    # Check database
    db_healthy = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_healthy = True
    except Exception:
        db_healthy = False

    # Check Redis
    redis_healthy = False
    try:
        redis_client = await get_redis()
        if redis_client:
            await redis_client.ping()
            redis_healthy = True
    except Exception:
        redis_healthy = False

    is_healthy = db_healthy and redis_healthy

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "database": "ok" if db_healthy else "error",
        "redis": "ok" if redis_healthy else "error",
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
