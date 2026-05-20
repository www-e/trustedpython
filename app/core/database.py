"""
Database connection and session management.

Provides async SQLAlchemy engine, session factory, and init/close helpers
for the Game Account Marketplace.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO, future=True)

# Create async session maker
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """
    Initialize database tables.

    Imports all models so they register on the shared Base.metadata,
    then creates all tables if they don't exist.
    """
    try:
        # Import all models to register their metadata on Base
        import app.models  # noqa: F401

        from app.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[OK] Database initialized successfully")
    except Exception as e:
        print(f"[WARNING] Database initialization failed: {e}")
        print("  Continuing without database - some features may not work")


async def close_db() -> None:
    """
    Close database connection.
    """
    await engine.dispose()
