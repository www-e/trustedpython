"""Add is_popular column to categories table."""

import asyncio
from sqlalchemy import text
from app.db import engine


async def add_is_popular_column():
    """Add is_popular column to categories table."""

    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'categories' AND column_name = 'is_popular'")
        )

        if result.rowcount > 0:
            print("is_popular column already exists!")
            return

        print("Adding is_popular column to categories table...")

        # Add the column
        await conn.execute(
            text("ALTER TABLE categories ADD COLUMN IF NOT EXISTS is_popular BOOLEAN DEFAULT FALSE NOT NULL")
        )

        # Create index
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_categories_is_popular ON categories (is_popular)")
        )

        print("SUCCESS! is_popular column added to categories table")


if __name__ == "__main__":
    print("Adding is_popular column...")
    asyncio.run(add_is_popular_column())
