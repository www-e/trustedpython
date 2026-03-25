"""Test with prepared statements disabled."""
import asyncio
from sqlalchemy import text
from app.db import engine

async def test_with_disabled_prepared_statements():
    """Test with prepared statements disabled."""
    # Clean database
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS listing_mediators CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS deals CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listing_images CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listings CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS categories CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS deal_status CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS game_type CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS listing_status CASCADE"))

        # Create ENUMs
        await conn.execute(text("CREATE TYPE game_type AS ENUM ('pubg', 'free_fire', 'call_of_duty', 'fortnite', 'mobile_legends', 'other')"))
        await conn.execute(text("CREATE TYPE listing_status AS ENUM ('draft', 'pending', 'active', 'sold', 'paused', 'archived')"))
        await conn.execute(text("CREATE TYPE deal_status AS ENUM ('pending', 'in_progress', 'awaiting_payment', 'payment_verified', 'credentials_exchanged', 'completed', 'cancelled', 'disputed')"))

        print("ENUMs created successfully")

asyncio.run(test_with_disabled_prepared_statements())
