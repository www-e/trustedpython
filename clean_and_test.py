"""Clean database and force Neon to clear cache."""
import asyncio
from sqlalchemy import text
from app.db import engine

async def clean():
    """Completely clean the database and disconnect."""
    async with engine.begin() as conn:
        # Drop everything
        await conn.execute(text("DROP TABLE IF EXISTS listing_mediators CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS deals CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listing_images CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listings CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS categories CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS deal_status CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS game_type CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS listing_status CASCADE"))
        print("Database completely cleaned")

    # Dispose all connections to force Neon to clear cache
    await engine.dispose()
    print("Engine disposed - Neon cache should be cleared")

asyncio.run(clean())
