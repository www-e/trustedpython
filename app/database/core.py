from sqlmodel import create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from typing import AsyncGenerator
from app.models.user import SQLModel
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://username:password@localhost:5432/trustedpython_dev")

# Check if DATABASE_URL uses the asyncpg driver, and fix if needed
if DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    # Replace the protocol to use asyncpg
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Handle asyncpg-specific URL parameters (remove incompatible ones like channel_binding)
parsed = urlparse(DATABASE_URL)
query_params = parse_qs(parsed.query)

# Remove parameters that asyncpg doesn't support
unsupported_params = ['channel_binding']
for param in unsupported_params:
    query_params.pop(param, None)

# Reconstruct the URL without unsupported parameters
new_query = urlencode(query_params, doseq=True)
DATABASE_URL = urlunparse((
    parsed.scheme,
    parsed.netloc,
    parsed.path,
    parsed.params,
    new_query,
    parsed.fragment
))

# Create async engine
engine = create_async_engine(DATABASE_URL)

async def create_db_and_tables():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection"""
    async with AsyncSession(engine) as session:
        yield session