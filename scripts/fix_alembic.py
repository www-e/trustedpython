"""Check and fix alembic version - fixed transaction handling."""

import asyncio
from sqlalchemy import text
from app.db import engine


async def check_alembic():
    """Check alembic version and fix if needed."""
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            versions = result.fetchall()
            print(f"Alembic versions: {versions}")
        except Exception as e:
            error_msg = str(e)
            if "alembic_version" in error_msg and "does not exist" in error_msg:
                print("No alembic_version table found, creating it...")
                # Need to create outside the failed transaction
                pass
            else:
                print(f"Error checking alembic: {e}")
                raise

async def fix_alembic():
    """Fix alembic version table outside transaction."""
    async with engine.begin() as conn:
        # Create table and set base version
        await conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"))
        # Check if version exists
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        if result.rowcount == 0:
            print("Setting base version...")
            await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('44ec30f3a4a6')"))
            print("Base version set!")
        else:
            print(f"Current version: {result.scalar()}")


if __name__ == "__main__":
    print("Checking alembic status...")
    asyncio.run(check_alembic())
    print("\nFixing alembic if needed...")
    asyncio.run(fix_alembic())
