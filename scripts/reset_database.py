"""Reset database and apply migrations from scratch."""

import asyncio
from sqlalchemy import text
from app.db import engine


async def reset_database():
    """Drop all tables and reset alembic version."""

    async with engine.begin() as conn:
        # Drop all tables in correct order (respecting foreign keys)
        print("Dropping all tables...")

        # Drop tables manually to avoid FK constraints issues
        await conn.execute(text("DROP TABLE IF EXISTS listing_mediators CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listing_images CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS deals CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listings CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS categories CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS exclusive_cards CASCADE"))

        # Drop alembic version table
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))

        # Drop custom ENUM types
        await conn.execute(text("DROP TYPE IF EXISTS game_type CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS listing_status CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS deal_status CASCADE"))

        print("All tables dropped successfully!")


if __name__ == "__main__":
    print("Resetting database...")
    asyncio.run(reset_database())
    print("\nNow run: alembic upgrade head")
