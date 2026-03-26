"""Script to check and fix test database schema."""

import asyncio
from sqlalchemy import text
from app.core.deps import get_db


async def check_schema():
    """Check if is_popular column exists."""
    async for db in get_db():
        try:
            # Check if is_popular column exists
            result = await db.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name = 'categories' AND column_name = 'is_popular'")
            )

            has_is_popular = result.rowcount > 0
            print(f"is_popular column exists: {has_is_popular}")

            if not has_is_popular:
                print("Need to apply migration...")
                return False
            else:
                print("Schema is up to date!")
                return True

        except Exception as e:
            print(f"Error checking schema: {e}")
            return False


if __name__ == "__main__":
    asyncio.run(check_schema())
