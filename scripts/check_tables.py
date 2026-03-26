"""Check what tables exist in the database."""

import asyncio
from sqlalchemy import text
from app.db import engine


async def check_tables():
    """Check what tables exist."""

    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        )
        tables = result.fetchall()
        print(f"Tables in database: {[t[0] for t in tables]}")


if __name__ == "__main__":
    print("Checking database tables...")
    asyncio.run(check_tables())
