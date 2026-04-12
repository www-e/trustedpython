"""
Database Session Management

Provides async database session management using SQLAlchemy 2.0 async patterns.
All database operations should use the get_session() dependency.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

# Base class for all models
Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields database sessions.

    Usage in FastAPI routes:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(User))
            return result.scalars().all()

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database connection and create tables.
    This should be called on application startup.
    """
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered with Base
        # from app.models import *  # noqa
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    This should be called on application shutdown.
    """
    await engine.dispose()
