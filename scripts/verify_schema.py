"""Verify database schema is correct."""

import asyncio
from sqlalchemy import text
from app.db import engine


async def verify_schema():
    """Verify all columns exist."""

    async with engine.begin() as conn:
        # Check is_popular column
        result = await conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'categories' AND column_name = 'is_popular'")
        )
        has_is_popular = result.rowcount > 0
        print(f"is_popular column exists: {has_is_popular}")

        # Check is_featured column
        result = await conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'listings' AND column_name = 'is_featured'")
        )
        has_is_featured = result.rowcount > 0
        print(f"is_featured column exists: {has_is_featured}")

        # Check exclusive_cards table
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_name = 'exclusive_cards'")
        )
        has_exclusive_cards = result.rowcount > 0
        print(f"exclusive_cards table exists: {has_exclusive_cards}")

        return has_is_popular and has_is_featured and has_exclusive_cards


if __name__ == "__main__":
    print("Verifying database schema...")
    result = asyncio.run(verify_schema())
    if result:
        print("\nSUCCESS! Database schema is correct.")
    else:
        print("\nERROR! Database schema is incomplete.")
