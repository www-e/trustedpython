"""Clear all data from test database."""

import asyncio
from sqlalchemy import text
from app.db import engine


async def clear_data():
    """Delete all data from tables."""

    async with engine.begin() as conn:
        # Delete from tables in correct order (respecting foreign keys)
        await conn.execute(text("DELETE FROM listing_mediators"))
        await conn.execute(text("DELETE FROM deals"))
        await conn.execute(text("DELETE FROM listing_images"))
        await conn.execute(text("DELETE FROM listings"))
        await conn.execute(text("DELETE FROM categories"))
        await conn.execute(text("DELETE FROM users"))
        await conn.execute(text("DELETE FROM exclusive_cards"))

        # Reset sequences
        await conn.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
        await conn.execute(text("ALTER SEQUENCE categories_id_seq RESTART WITH 1"))
        await conn.execute(text("ALTER SEQUENCE listings_id_seq RESTART WITH 1"))
        await conn.execute(text("ALTER SEQUENCE listing_images_id_seq RESTART WITH 1"))
        await conn.execute(text("ALTER SEQUENCE deals_id_seq RESTART WITH 1"))
        await conn.execute(text("ALTER SEQUENCE listing_mediators_id_seq RESTART WITH 1"))
        await conn.execute(text("ALTER SEQUENCE exclusive_cards_id_seq RESTART WITH 1"))

    print("All test data cleared!")


if __name__ == "__main__":
    print("Clearing test data...")
    asyncio.run(clear_data())
